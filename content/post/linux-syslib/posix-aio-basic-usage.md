# 能對普通檔案做 async IO 嗎？跨平台 POSIX AIO 介紹與基本使用
date: 2022/08/01
category: programming

excerpt: 在普通檔案的讀寫中，一般在網路程式裡會使用到的非同步 IO 通常都是沒辦法直接使用的， POSIX AIO 提供基本的非同步 API 讓一個 process 可以一次發出多個檔案讀寫請求

---

## IO 事件 API 有什麼問題

在普通檔案的讀寫中，一般在網路程式裡會使用到的非同步 IO 通常都是沒辦法直接使用的，例如使用 poll 的話會永遠回傳普通檔案 fd 是 ready 的狀態，在 Linux 上用 `epoll_ctl` 加入普通檔案的 fd 的話則會回傳 `EPERM` 錯誤。

這個設計的考量是普通檔案發生 block 的意義和網路/FIFO 發生 block 的意義不太一樣。普通檔案的操作如 `open`, `read`, `write` 的結果都是一翻兩瞪眼，要不有檔案有資料，要不就是檔案不存在、無法寫入或內容讀完了，操作都是在呼叫的時刻就能進行，不管操作的時間多久，操作結束（可以說系統忙完）就能知道結果。而 socket 和 FIFO 發生的 block 則是在「等待事件發生」例如等待 socket 有 client 連線、或是 FIFO 的 write end 有人寫入。可以說 `epoll` 類型的 API 是為了節省 process 等待「事件可被處理」的時間，而不是「處理事件」的時間。

為什麼 `epoll` 沒有等待普通檔案讀寫的通知機制呢？我沒有再去特別查證了，但我猜是為了減少對讀寫操作的假設。`epoll` 減少等待的是 CPU 沒有處理任務的閒置時間，但讀寫操作只有在系統可以操作獨立的讀寫裝置（如硬碟、網路卡）的時候 CPU 才可能空閒下來，如果檔案對應的裝置只需要 CPU 運算（如 ramdisk），那麼 CPU 只是進入 kernel space 做必要的計算而已，並不會發生空閒的狀態。所以就算作業系統馬上返回到 process ，也沒辦法提高 CPU 的利用率。

## 跨平台讀寫操作的 Asynchronous API

`epoll` API 沒有普通檔案讀寫功能不代表 Linux 沒有提供普通檔案讀寫的非同步 API ， POSIX 有定義一系列稱為 AIO 的 API ，在 glibc 中有最基本的實作，可以達到「讀寫時不阻塞 process ，並在完成時讓 process 處理結果」的基本要求。使用方式是把想要執行的讀寫操作包裝到 `struct aiocb` 的結構裡作為請求，這個結構有以下需要自己填的欄位：

```
struct aiocb {
    /* The order of these fields is implementation-dependent */

    int             aio_fildes;     /* File descriptor */
    off_t           aio_offset;     /* 檔案的讀寫位置 */
    volatile void  *aio_buf;        /* 寫入內容/讀取結果的 buffer */
    size_t          aio_nbytes;     /* buffer 的長度 */
    int             aio_reqprio;    /* Request 的優先級，越大表示優先級越低 */
    struct sigevent aio_sigevent;   /* 完成或失敗時通知 process 的方式 */
    int             aio_lio_opcode; /* 批次處理參數 */

    /* Various implementation-internal fields not shown */
};
```

因為這個 struct 還有其他欄位，所以使用這個 struct 前應該要先用 memset 把他歸零或是直接使用 designated initializer。

其中 `aio_sigevent` 欄位需要設定讀寫操作完成後要如何通知呼叫的 process ，這個 struct 的內容長這樣：

```
union sigval {            /* 收到 signal 時附帶的資料 */
    int     sival_int;
    void   *sival_ptr;
};

struct sigevent {
    int    sigev_notify;  /* 通知的方式 */
    int    sigev_signo;   /* 通知 process 使用的 signal */
    union sigval sigev_value;
                            /* Signal 的附帶資料 */
    void (*sigev_notify_function)(union sigval);
                            /* sigev_notify 是 SIGEV_THREAD 時要啟動的 function */
    void  *sigev_notify_attributes;
                            /* sigev_notify 是 SIGEV_THREAD 時的其他屬性 */
    pid_t  sigev_notify_thread_id;
                            /* ID of thread to signal
                            (SIGEV_THREAD_ID); Linux-specific */
};
```

`sigev_notify` 欄位的值決定剩下的欄位要怎麼填，POSIX AIO 有這幾種值可以用：

- `SIGEV_NONE`：操作結束後不做任何事，不需要填上其他欄位
- `SIGEV_SIGNAL`：操作結束後對呼叫的 process 傳送 signal ，需要填上 `sigev_signo` 指定傳送的 signal number
- `SIGEV_THREAD`：操作結束後啟動 `sigev_notify_function` 指定的函式，呼叫方式依照實作不同可能會啟動新的 thread。還需要填上 `sigev_notify_attribuets` ，這個指標的內容是 `pthread_attr_t` 物件，可以透過 `pthread_attr_init` 來初始化

這裡用 `SIGEV_SIGNAL` 做為例子，除了設定 `sigev_signo` 之外，也要使用 `sigaction` 來指定要執行的 signal handler

```
void read_handler(int sig, siginfo_t *info, void *ucontext) {                   
    ...                        
}

int main() {
    ...
    struct sigaction act = {                                                
            .sa_sigaction = read_handler,                                   
            .sa_mask = 0,                                                   
            .sa_flags = SA_RESTART | SA_SIGINFO                             
    };                                                                      
    sigemptyset(&act.sa_mask);
    sigaction(SIGIO, &act, NULL);
    ...
}
```

Signal handler 需要接受三個參數 `sig` 表示收到的 signal number ， `info` 表示 signal 附帶的資料，使用時也需要在 `sa_flags` 加上 `SA_SIGINFO` 屬性。 `ucontext` 則是一般不使用。

相關的結構都設定完成之後，就能傳入最開始介紹的 `aiocb` 結構的指標呼叫 `aio_read`, `aio_write` 等 API 了，也需要注意在呼叫過後檔案的讀取位址是沒有規定的，所以如果要接著使用傳統 `read`/`write` API 的話要記得再使用 `seek` 類的 API 重設一次檔案讀寫位址。

## 運作機制

這組 API 並沒有使用 Linux kernel 的 IO 事件機制，用 debugger 來執行他會發現 `aio_read` 實際上是用建立 thread 的方式來執行讀寫操作和通知原始 thread

```
Breakpoint 1, main (argc=2, argv=0x7fffffffdae8) at posix_aio.c:55
55		aio_read(&cb);
(gdb) n
[New Thread 0x7ffff7fbf740 (LWP 2546026)]
56		cnt = 0;
(gdb)
```

也就是發出一個 IO request 等於會開新的 thread ，用這種 API 與其說是 asynchronous IO ，其實比較像方便平行化處理 IO 的函式庫。

## Sample Code

整理起來以下就是簡單的執行 `aio_read` 的 sample code：

```
// compile: gcc -lrt posix_aio.c
#include <stdio.h>
#include <fcntl.h>
#include <aio.h>
#include <signal.h>

sig_atomic_t cnt;

void read_handler(int sig, siginfo_t *info, void *ucontext) {
	printf("read finished\n");
	printf("the count of loop waited: %d\n", cnt);
	printf("%d %d\n", sig, SIGIO);
	printf("%d %d\n", info->si_code, SI_ASYNCIO);
	struct aiocb *cb = info->si_value.sival_ptr;
	if(cb == NULL || sig != SIGIO || info->si_code != SI_ASYNCIO) return ;
	ssize_t size = aio_return(cb);
	printf("%d\n", size);
	volatile char *buf = cb->aio_buf;
	for(int i=0; i<size; i++) {
		printf("%c", buf[i]);
	}
}

int main(int argc, char *argv[]) {
	if(argc < 2) {
		printf("no file specified\n");
		return 0;
	}
	const unsigned int buf_size = 4096;
	int fd1 = open(argv[1], 0, O_RDONLY);
	char buf1[buf_size];
	struct sigaction act = {
		.sa_sigaction = read_handler,
		.sa_mask = 0,
		.sa_flags = SA_RESTART | SA_SIGINFO
	};
	sigemptyset(&act.sa_mask);
	struct sigevent event = {
		.sigev_notify = SIGEV_SIGNAL,
		.sigev_signo = SIGIO,
	};
	struct aiocb cb = {
		.aio_fildes = fd1,
		.aio_offset = (off_t)0,
		.aio_buf = buf1,
		.aio_nbytes = buf_size,
		.aio_reqprio = 0,
		.aio_sigevent = event,
		.aio_lio_opcode = 0
	};
	cb.aio_sigevent.sigev_value.sival_ptr = &cb;
	sigaction(SIGIO, &act, NULL);
	aio_read(&cb);
	cnt = 0;
	while(1) {
		cnt++;
		int status = aio_error(&cb);
		if(status == 0) {
			break;
		}
	}
	return 0;
}

```

## References

[https://stackoverflow.com/questions/8057892/epoll-on-regular-files](https://stackoverflow.com/questions/8057892/epoll-on-regular-files)

[https://stackoverflow.com/questions/60958406/why-poll-returns-immediately-on-regular-files-and-blocks-on-fifo](https://stackoverflow.com/questions/8057892/epoll-on-regular-files)

[https://stackoverflow.com/questions/8768083/difference-between-posix-aio-and-libaio-on-linux](https://stackoverflow.com/questions/8768083/difference-between-posix-aio-and-libaio-on-linux)

[https://programmer.ink/think/just-one-thing-about-linux-asynchronous-i-o-aio.html](https://programmer.ink/think/just-one-thing-about-linux-asynchronous-i-o-aio.html)

[https://man7.org/linux/man-pages/man7/aio.7.html](https://man7.org/linux/man-pages/man7/aio.7.html)

[https://man7.org/linux/man-pages/man7/sigevent.7.html](https://man7.org/linux/man-pages/man7/sigevent.7.html)

[https://man7.org/linux/man-pages/man2/sigaction.2.html](https://man7.org/linux/man-pages/man2/sigaction.2.html)