# 記憶體錯誤檢查工具 Address Sanitizer 介紹
date: 2024/02/16
category: programming/cxx
thumbnail: https://imgcdn.austint.in/m3R2auZJ4eIQPnIbsN1tCoOZ7sg=/fit-in/760x560/filters:format(webp)/address-sanitizer-intro/program-in-c.png
excerpt: 在 C/C++ 程式中，存取越界或 use-after-free 類型的記憶體錯誤是很常見的 bug ，除了透過良好的習慣跟 design pattern 可以手工避免之外，也有一些工具在編譯過程或執行時期進行自動化的檢查。最近看到了 Google 在 2012 年發表 Address Sanitizor （簡稱 ASAN）的論文，整理一下使用方法還有論文裡面介紹 的 ASAN 實作。

---

在 C/C++ 程式中，存取越界或 use-after-free 類型的記憶體錯誤是很常見的 bug ，除了透過良好的習慣跟 design pattern 可以手工避免之外，也有一些工具在編譯過程或執行時期進行自動化的檢查。最近看到了 Google 在 2012 年發表 Address Sanitizor （簡稱 ASAN）的論文，宣稱打趴了當時既有的工具，現在也整合進了各大主流 compiler 和 Linux kernel 。在這篇文章整理一下使用方法還有論文裡面介紹 的 ASAN 實作。

## 編譯器選項

ASAN 一開始開發時是 LLVM 的一個 pass ，所以我們就用 LLVM toolchain 的 clang 來做實驗。先寫好一隻有明顯記憶體錯誤的小程式。

```
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main() {
	int *a = (int *)malloc(3 * sizeof(int));
	scanf("%d%d", &a[0], &a[1]);
	a[2] = a[0] + a[1];
	// wrong place to free!
	free(a);
	printf("%d\n", a[2]);
	// correct
	//free(a);
	return 0; 
}

```

編譯完執行可以看出沒有輸出正常的加法結果。試著用 ASAN 抓出錯誤，要使用的編譯選項是 `fsanitize=address` ，加上一般的 `-O1` 以上的優化會省略部份 frame pointer 的操作，所以會希望加上 `-fno-omit-frame-pointer` 保留，讓錯誤發生時的 stack trace 可以完整一點。所以要使用 ASAN 的編譯指令會長這樣：

```
clang -O1 -fsanitize=address -fno-omit-frame-pointer a.c
```

如果以前沒有用過相關的環境，會出現這樣的錯誤：

```
/usr/bin/ld: cannot find /usr/bin/../lib/clang/17/lib/linux/libclang_rt.asan_static-x86_64.a: No such file or directory
/usr/bin/ld: cannot find /usr/bin/../lib/clang/17/lib/linux/libclang_rt.asan-x86_64.a: No such file or directory
/usr/bin/ld: cannot find /usr/bin/../lib/clang/17/lib/linux/libclang_rt.asan_cxx-x86_64.a: No such file or directory
clang++: error: linker command failed with exit code 1 (use -v to see invocation)
```

需要安裝 LLVM 的 compiler-rt 才能 link 到 ASAN 在執行時期需要的函式。

```
sudo dnf install compiler-rt
# 或是 Ubuntu/Debian 用
sudo apt-get install libclang-rt-17-dev
```

## 錯誤輸出內容

安裝過後應該就能順利編譯，執行並輸入兩個數字後就可以看到 ASAN 噴出來的錯誤。我們分段來做說明。

```
=================================================================
==2772484==ERROR: AddressSanitizer: heap-use-after-free on address 0x502000000018 at pc 0x0000003425a7 bp 0x7ffd6b494c40 sp 0x7ffd6b494c38
READ of size 4 at 0x502000000018 thread T0
    #0 0x3425a6 in main (/home/austin/Documents/labs/a.out+0x3425a6) (BuildId: f4d841ec4dad0298)
    #1 0x7ff518314149 in __libc_start_call_main (/lib64/libc.so.6+0x28149) (BuildId: 788cdd41a15985bf8e0a48d213a46e07d58822df)
    #2 0x7ff51831420a in __libc_start_main@GLIBC_2.2.5 (/lib64/libc.so.6+0x2820a) (BuildId: 788cdd41a15985bf8e0a48d213a46e07d58822df)
    #3 0x266314 in _start (/home/austin/Documents/labs/a.out+0x266314) (BuildId: f4d841ec4dad0298)
```

上面顯示的是 ASAN 偵測到一個 heap-use-after-free 的錯誤，也就是有 malloc 出來的記憶體在 free 過後又被存取了，並且列出存取的種類和執行到這個存取指令的 stack trace 。如果一開始編譯的時候有加上 `-g` 選項加入 debug symbol 的話， stack trace 標示程式執行位址的地方都會變成標示檔案和行數。

```
0x502000000018 is located 8 bytes inside of 12-byte region [0x502000000010,0x50200000001c)
freed by thread T0 here:
    #0 0x30456a in free (/home/austin/Documents/labs/a.out+0x30456a) (BuildId: f4d841ec4dad0298)
    #1 0x34252d in main (/home/austin/Documents/labs/a.out+0x34252d) (BuildId: f4d841ec4dad0298)
    #2 0x7ff518314149 in __libc_start_call_main (/lib64/libc.so.6+0x28149) (BuildId: 788cdd41a15985bf8e0a48d213a46e07d58822df)
    #3 0x7ff51831420a in __libc_start_main@GLIBC_2.2.5 (/lib64/libc.so.6+0x2820a) (BuildId: 788cdd41a15985bf8e0a48d213a46e07d58822df)
    #4 0x266314 in _start (/home/austin/Documents/labs/a.out+0x266314) (BuildId: f4d841ec4dad0298)
previously allocated by thread T0 here:
    #0 0x304812 in malloc (/home/austin/Documents/labs/a.out+0x304812) (BuildId: f4d841ec4dad0298)
    #1 0x3424c3 in main (/home/austin/Documents/labs/a.out+0x3424c3) (BuildId: f4d841ec4dad0298)
    #2 0x7ff518314149 in __libc_start_call_main (/lib64/libc.so.6+0x28149) (BuildId: 788cdd41a15985bf8e0a48d213a46e07d58822df)
    #3 0x7ff51831420a in __libc_start_main@GLIBC_2.2.5 (/lib64/libc.so.6+0x2820a) (BuildId: 788cdd41a15985bf8e0a48d213a46e07d58822df)
    #4 0x266314 in _start (/home/austin/Documents/labs/a.out+0x266314) (BuildId: f4d841ec4dad0298)
```

以上是列出被存取的記憶體在被 free 掉之前所在的區塊，還有分配這段記憶體的 malloc 和 free 被呼叫的位置。

```
SUMMARY: AddressSanitizer: heap-use-after-free (/home/austin/Documents/labs/a.out+0x3425a6) (BuildId: f4d841ec4dad0298) in main
Shadow bytes around the buggy address:
  0x501ffffffd80: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
  0x501ffffffe00: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
  0x501ffffffe80: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
  0x501fffffff00: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
  0x501fffffff80: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
=>0x502000000000: fa fa fd[fd]fa fa fa fa fa fa fa fa fa fa fa fa
  0x502000000080: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x502000000100: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x502000000180: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x502000000200: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x502000000280: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
Shadow byte legend (one shadow byte represents 8 application bytes):
  Addressable:           00
  Partially addressable: 01 02 03 04 05 06 07 
  Heap left redzone:       fa
  Freed heap region:       fd
  Stack left redzone:      f1
  Stack mid redzone:       f2
  Stack right redzone:     f3
  Stack after return:      f5
  Stack use after scope:   f8
  Global redzone:          f9
  Global init order:       f6
  Poisoned by user:        f7
  Container overflow:      fc
  Array cookie:            ac
  Intra object redzone:    bb
  ASan internal:           fe
  Left alloca redzone:     ca
  Right alloca redzone:    cb
==2772484==ABORTING
```

最後這段算是 ASAN 為記憶體分配（或定址 addressable ，就是記憶體位置在 page table 上是否有對應的物理位址）狀態建立的 metadata ，存在一段被稱為 shadow memory 的區塊。每個 byte 用來表示一段 8 bytes 的 application memory 的分配狀態。 `01-07` 的值表示這 8 個 byte 的前 1~7 個 byte 是已經被分配為可存取的， `00` 表示 8 個 byte 都是已分配為可存取。其他的值都表示這個 8 bytes 的區塊不應該被存取，不同的數值表示不同的類型。每一列左邊的記憶體位置是右邊每個shadow memory byte 的數值所對應的 application memory ，方括號表示那個 byte 對應的就是被存取的那段 application memory 。一開始的程式做的 use-after-free 對應的 shadow memory byte 數值是 `fd` ，按照上面的對應表上表示的是 Freed heap region ，也就是在記憶體釋放過後的存取。如果把程式改成越界的錯誤，把 `free()` 換到正確的位置，再把輸出的 `a[2]` 改成 `a[3]` ，錯誤訊息的 shadow memory 會像下面這樣：

```
Shadow bytes around the buggy address:
  0x501ffffffd80: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
  0x501ffffffe00: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
  0x501ffffffe80: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
  0x501fffffff00: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
  0x501fffffff80: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
=>0x502000000000: fa fa 00[04]fa fa fa fa fa fa fa fa fa fa fa fa
  0x502000000080: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x502000000100: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x502000000180: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x502000000200: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x502000000280: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
```

這時候被存取到的記憶體對應的 shadow memory 數值就是 `04` ，前一段記憶體的是 `00` 。整個陣列被分配了 4x3 = 12 bytes 的空間，所以 `a[3]` 存取到了 8 bytes 的後段，超過了第四個 byte 因此回傳了錯誤。

## 實作原理

在 ASAN 之前有一些類似的記憶體錯誤檢測工具， ASAN 算是把其中幾種技術做了一些改良之後整合在一起。在紀錄記憶體分配狀態使用了 shadow memory ，在追蹤記憶體存取的方面依賴 compiler instrumentation ，管理 shadow memory 和錯誤回報機制則是用 runtime library 完成。

### Shadow Memory

紀錄記憶體分配狀態本來就需要額外空間，這段空間通常不應該被 application 直接存取，而是讓這些記憶體錯誤檢測工具來管理，這些空間被稱為 shadow memory ，因此 shadow memory 的使用量和查詢效率就會是各種工具間比較的重點。過去的其他工具有的實作是在 application 的每個 byte 都對應到 shadow memory 的一個 byte 來紀錄分配狀態，這樣的空間使用量就會是原始記憶體使用量的兩倍。有的則是額外實作了查詢用的資料結構，在每次記憶體的 load/store 或是 malloc/free 都去查詢修改這個結構，可能效率不會太好。

ASAN 的論文中提到一個觀察：在大部分系統中，由 malloc 分配出來的記憶體都是以 8 個 byte 為單位對齊的。也就是每段 8 bytes 長的區域的分配狀態只會是前 `k` bytes 可以定址而後面 `8-k` 個 bytes 不行， `k` 從 0 到 8 就是 9 種狀態， ASAN 再把 8 個 bytes 全部不可定址的狀態分成 heap, stack 等情況把 8 個 bytes 分配的狀態編碼成一個 byte 可以容納的數值，就是上面錯誤訊息裡的 shadow byte legend。這樣理論上 ASAN 會佔用的記憶體就會是 application 使用量的 8 分之 1 。

ASAN 對 shadow memory 中的查詢也力求節省計算以及額外的記憶體操作。對一個記憶體位址 `addr` ，對應的 shadow memory byte 的位址就是 `(addr >> scale) + offset` ，其中 scale 和 offset 是事先決定好的倍率和起始位址，會依照系統中 malloc 對齊單位的大小和對 process 起始的 address space 決定， scale 在上面的 8 bytes 對齊來說就會設定為 3 。offset 在 32bit Linux 會設定成 `0x20000000` 、在 64bit 則會設定成 `0x0000100000000000` 等。

### Compiler Instrumentation

記憶體存取的 bug 需要在每次存取記憶體的時候檢查分配的狀態，也就是每次遇到 load/store 的指令都需要進入檢查的流程。因為 load/store 是 CPU 層級的指令（不是 call function 或 system call）所以要找出所有的 load/store 比較直接的方法就是在 compiler 輸出的流程找。 ASAN 把這個過程寫成 LLVM 的一個 pass ，會排在所有優化完成之後執行，在所有的 load/store 指令前面插進這樣的流程：

```
ShadowAddr = (Addr >> 3) + Offset;
k = *ShadowAddr;
if (k != 0 && ((Addr & 7) + AccessSize > k))
  ReportAndCrash(Addr);
```

也就是很直白的檢查要存取的記憶體區段在 shadow memory 中的狀態是不是可以存取的，如果不行就噴錯結束整個程式。

在編譯時期 ASAN 也會對 stack variable 做處理，在區域變數的前後各增加一段稱為 redzone 的記憶體，實際上就是多兩個 char 陣列，這兩個區域的 shadow memory 就標記為 redzone 不可存取的數值，這樣也能夠檢測在 stack 上的存取越界。

### Runtime Library

從前面的內容就可以看到整個 ASAN 的正確性依賴在 shadow memory 內容上，而這些內容就需要在執行時有專門的流程來維護。 ASAN 主要實作了自訂的 malloc/free ，在被呼叫的時候修改對應的 shadow memory 內容。除了被分配的區域依照 shadow memory 的規則設定為 `00-07` 的數值、釋放時修改成稱作 quarantine 的狀態外，分配的區域前後也要標記為不可存取，而 ASAN 也會把這些區域拿來利用，存放一些 malloc/free 呼叫時的 stack trace 。

## 心得

ASAN 在後來有幾個我覺得比較重要的發展，其中一個是實作了在 Linux kernel 中的版本叫 KASAN ，另一個是硬體的支援可以減少 binary 的大小和對 instruction cache 的影響，還有整合了一些 memory leak 的檢查類型。我覺得在寫各種情境的 C/C++ 程式都可以拿來檢查看看。

雖然整個 ASAN 發表時是一篇 paper ，整個實作內容看起來算是簡單，看下來反而會覺得好像直覺上就應該這樣設計，有點想像不到以前所謂比較不理想的實作長什麼樣子。感覺也是一個理念簡單暴力，但實作完整所以能夠推廣進各個生態系的成功案例。

## References

[封面圖取自改編歌曲 Program in C](https://www.youtube.com/watch?v=tas0O586t80)

[AddressSanitizer: A Fast Address Sanity Checker | USENIX (影片)](https://www.usenix.org/conference/atc12/technical-sessions/presentation/serebryany)

[AddressSanitizer: A Fast Address Sanity Checker (論文)](https://www.usenix.org/system/files/conference/atc12/atc12-final39.pdf)

[AddressSanitizer — Clang 19.0.0git documentation](https://clang.llvm.org/docs/AddressSanitizer.html)

