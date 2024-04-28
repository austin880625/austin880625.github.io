# Linux 中普通檔案的 async IO API：Linux AIO 基本使用
date: 2022/08/24
category: programming
excerpt: 先前介紹的 POSIX AIO 只有做到執行讀寫操作的 process 不會在讀寫時阻塞，如果要讓 kernel 在完成後通知 process 的話，還是需要核心的協助。本文介紹 Linux 提供的 AIO 界面來達成這項任務

---

[之前的文章](/post/2022/08/01/posix-aio-basic-usage.html)提到 POSIX 版的 async IO 界面其實只是啟動新的 thread 進行普通的 blocking IO ，如果程式本身已經是在多個 thread 中進行平行的 IO 操作，那麼使用這個 API 其實不會獲得任何效能上的好處。

我們希望的 async IO 應該還是像 epoll 那樣，發送讀寫請求之後讓 process 繼續執行，讀寫任務完成後可以讓 process 把結果撿起來用。這就會需要系統核心的協助，要有介面來讓 process 「發送」要求和在完成時收到通知以「獲得」結果。

## Linux AIO 

Linux AIO 就對這種類型的 IO 提供部分的支援，主要透過 `io_setup`, `io_submit` 和 `io_getevents` 三個 system call 來達成初始化、發送 request 和取得結果的工作。需要先引入相關的 header 檔案

```
#include <fcntl.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <linux/aio_abi.h>
#include <linux/ioprio.h>
```

`io_setup` 用來建立 async io 的 context ，也就是在 kernel 所需的資料結構，接收兩個參數 `nr_events` 和 `ctx_idp` ，分別表示 io queue 裡最大的請求數量和存放 context 的指標。所以初始化的過程如下：

```
        int nr_event = 4;
        aio_context_t ctx;
        // We don't assume the typing of aio_context_t here
        // but it's actually integer alike
        memset(&ctx, 0, sizeof(aio_context_t));
        long err = syscall(SYS_io_setup, nr_event, &ctx);
```

### 建立請求 

接著要準備要發送的 IO 操作請求，這個請求是透過 `iocb` 這個結構來定義的，底下介紹裡面需要填入的欄位。

`aio_rw_flags` 的作用相當於使用 `open` 時設定的 flag ，可以使用的值有：

- `RWF_APPEND`
- `RWF_SYNC`
- `RWF_DSYNC`
- `RWF_HIPRI`
- `RWF_NOWAIT`

`aio_lio_opcode` 用來指定要執行的檔案操作，可以使用的值的名稱和原始的 blocking system call 直接對應：

- `IOCB_CMD_PREAD`
- `IOCB_CMD_PWRITE`
- `IOCB_CMD_FSYNC`
- `IOCB_CMD_FDSYNC`
- `IOCB_CMD_POLL`
- `IOCB_CMD_NOOP`
- `IOCB_CMD_PREADV`
- `IOCB_CMD_PWRITEV`

`aio_flags` 指定了 IO request 的一些屬性，這裡我只會 `IOCB_FLAG_IOPRIO` ，表示這個 aio request 會使用到 `aio_reqprio` 欄位來指定優先級

`aio_reqprio` 表示這個 IO request 的優先級，數字越大表示優先級越低。在 `aio_flags` 的值是 `IOCB_FLAG_IOPRIO` 的時候使用 `IOPRIO_PRIO_VALUE` 這個 macro 來定義。這個 macro 接收兩個參數 `class` 和 `data` ，分別表示 IO 排程器的種類和優先級， `data` 可以是 0-7 的值，有一個中間值常數 `IOPRIO_NORM=4`， `class` 可以使用的值則有以下三種：

- `IOPRIO_CLASS_RT`: Realtime 的排程，會排在最高優先級，此時 `data` 表示的是 IO request 應該完成的時間區間，但其實在系統中沒有辦法自己指定具體的 deadline。
- `IOPRIO_CLASS_BE`: 和系統的 BFQ 排程器一起排程，由 kernel 依照 `data` 分配 IO 裝置的頻寬用量。值為 0 的時候優先級最高， 7 的時候優先級最低。
- `IOPRIO_CLASS_IDLE`: 只有磁碟閒置時才會處理請求，這時 `data` 的值沒有作用。

因此一個 `aio_reqprio` 的值可以寫成 `IOPRIO_PRIO_VALUE(IOPRIO_CLASS_BE, IOPRIO_NORM)` 。

剩下的欄位就比較像原始 IO system call 裡會有的參數 `aio_fildes` 表示要執行 IO request 的 file descriptor ， `aio_buf`, `aio_nbytes`, `aio_offset` 表示資料要在記憶體存放的位址、讀寫操作的資料長度和位移。

### 發送請求和獲取結果

填完這些參數（真的有夠多）就能夠發送 AIO 請求了。發送請求使用的是 `io_submit` system call ，帶有三個參數 `ctx_id`, `nr`, `iocbpp` ，分別是一開始建立的 context 、 IO request 的數量和一個由指向 `iocb` 結構的指標組成的陣列或指標（a pointer to the pointer to `iocb`）

```
        struct iocb *cbpp[] = { &cb };
        syscall(SYS_io_submit, ctx, 1, cbpp);
```

發送請求之後可以用 `io_getevents` 獲得結果

```
        struct io_event events[MAX_NR];
        syscall(SYS_io_getevents, ctx, min_nr, nr, &events, &timeout);
```

`nr` 表示要在 `events` 存放完成事件的最多數量。 這個 system call 會 block 直到 io context 中完成的 request 數量達到至少 `min_nr` 或是以 `timespec` 結構定義的 timeout 時間超過為止。收到結果後的 `io_event` 有這些欄位：

```
 struct io_event {
    __u64       data;       /* the data field from the iocb */
    __u64       obj;        /* what iocb this event came from */
    __s64       res;        /* result code for this event */
    __s64       res2;       /* secondary result */
};
```

`res2` 的內容我不知道，但 `res` 是在 `iocb` 結構的 `aio_lio_opcode` 指定的 IO 操作回傳的結果。`data` 則是 `aio_buf` 的資料。這些欄位不知道為什麼都用整數型別而不是指標。可能是為了統一結構大小做的一些小優化，但總之自己轉換型別後就能得到資料。

### 資源釋放

`io_destroy` 應該最簡單，就是釋放在 kernel 中佔用的資料結構：

```
        syscall(SYS_io_destroy, ctx);
```

## libaio 函式庫

使用 `syscall` 會需要依照不同處理器稍微注意不同 ABI 參數記憶體對齊的問題，這系列的 system call 其實要設定的欄位也算是偏多。因此在 userspace 有人另外寫了 `libaio` 這個 wrapper 函式庫。基本上大部分函式意思都和名稱對應的 system call 差不多，只是有些參數做了簡化，~~我好想先發文就不再特別研究他的參數怎麼填了~~。

## 限制

雖然 Linux AIO 從取名和開發過程就是為了達成對檔案真正的 asynchronous IO 。但其實到現在還是有滿多限制，特定的情境下這個 API 依然會造成阻塞，通常和 kernel 內的 lock 或排程或記憶體管理類的問題有關。這個 API 只有對普通檔案開啟 `O_DIRECT` 屬性的讀寫操作才會最接近理想 async IO 的行為。

## References

[https://man7.org/linux/man-pages/man2/io_setup.2.html](https://man7.org/linux/man-pages/man2/io_setup.2.html)

[https://docs.huihoo.com/doxygen/linux/kernel/3.7/aio__abi_8h_source.html](https://docs.huihoo.com/doxygen/linux/kernel/3.7/aio__abi_8h_source.html)

[https://elixir.bootlin.com/linux/v5.19/source/include/uapi/linux/ioprio.h](https://elixir.bootlin.com/linux/v5.19/source/include/uapi/linux/ioprio.h)

[https://hackmd.io/@sysprog/iouring](https://hackmd.io/@sysprog/iouring)

[https://stackoverflow.com/questions/34572559/asynchronous-io-io-submit-latency-in-ubuntu-linux](https://stackoverflow.com/questions/34572559/asynchronous-io-io-submit-latency-in-ubuntu-linux)

[https://oxnz.github.io/2016/10/13/linux-aio/](https://oxnz.github.io/2016/10/13/linux-aio/)