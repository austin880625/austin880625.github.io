title: 用 gdb debug 在 QEMU 上跑的 Linux Kernel
date: 2022/01/16
category: os/linux
---

## 安裝環境

```
apt-get install qemu-system build-essential flex bison libelf-dev libssl-dev
wget https://cdn.kernel.org/pub/linux/kernel/v5.x/linux-5.15.12.tar.xz
tar -xvf linux-5.15.12.tar.xz
cd linux-5.15.12
```

## 編譯 kernel

幾個比較常用到的 Linux kernel makefile target

- `menuconfig`: 啟動 CLI 介面選擇和設定核心功能
- `tinyconfig`: 編譯出可以在處理器中執行的最小核心(連輸出字元的 driver 都不會有)
- `vmlinux`: 按照可執行檔案格式(如 ELF, COFF)包裝的 kernel，如果有選擇 debug 功能的話 symbol table 會在這個檔案裡
- `zImage`: 包含 boot sector 可以直接載入記憶體中開機的 kernel 映象檔案以 gzip 壓縮，如果核心太大(超過 512KB)會編譯失敗
- `bzImage`: 字面意思是比較大的 zImage ，和 bzip 壓縮沒有關係。較大的核心會使用的映像檔案格式，boot sector 會將 kernel 載入到處理器支援的較大的記憶體區段之後再跳轉執行。

```
make menuconfig
# 確定 DEBUG_INFO 和 GDB_SCRIPTS 的選項為 y
# 直接 make 會連 module 一起編很久，這邊就編 vmlinux 和給 VM 開機用的 bzImage
make -j4 vmlinux
make -j4 bzImage
```

編譯需要一些時間，如果有跳錯通常是缺函式庫，如果不是可能要 google 一下錯誤訊息，我自己遇到的不是因為缺函式庫的錯誤只有下面這個

`no rule to make target 'debian/canonical-certs.pem'`

編輯 .config 把 `CONFIG_SYSTEM_TRUSTED_KEYS` 的值改成 `""`
以及把 `CONFIG_SYSTEM_REVOCATION_KEYS` 的值也改成 `""`

## 在 QEMU 中啟動 Linux kernel

執行以下指令
```
qemu-system-x86_64 -kernel arch/x86/boot/bzImage -nographic -append "console=ttyS0"
```
基本的意思就是啟動一台 x86_64 架構處理器的 VM ，以 bzImage 映像檔作為 kernel ，關閉圖形並將文字輸出到 ttyS0 裝置上

沒有特別的狀況的話， kernel 會開始啟動，直到處理器使用率被跑滿，畫面會停在這一句
```
[    8.088348] ---[ end Kernel panic - not syncing: VFS: Unable to mount root fs on unknown-block(0,0) ]---
```

表示 kernel 找不到可以掛載的 root fs ，沒辦法啟動應該在裡面的 init process

這時可以按鍵盤的 Ctrl+a 接著按 x 中止 VM

## 啟動 gdb

linux kernel 有提供一些 linux debug 用的 gdb 指令，可以修改 gdb 的設定檔讓 gdb 啟動時自動載入加入這些指令的 script

```shell
echo "add-auto-load-safe-path `pwd`/scripts/gdb/vmlinux-gdb.py" >> ~/.gdbinit
```

現在用以下指令啟動 QEMU
```
qemu-system-x86_64 -kernel arch/x86/boot/bzImage -nographic -append "console=ttyS0 nokaslr" -S -s
```

`-S` 參數是讓 QEMU 將 VM 啟動時就將 VM 停住等待 gdb 的指令，`-s` 參數則是讓 QEMU 會監聽 port 1234 的連線。 `nokaslr` 的核心參數是停用隨機分配 kernel 運作位址的功能。接著在另一個 terminal 上啟動 gdb 連線

```
user@user-VirtualBox:~/os/linux-5.15.12$ gdb vmlinux 
GNU gdb (Ubuntu 9.2-0ubuntu1~20.04) 9.2
Copyright (C) 2020 Free Software Foundation, Inc.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
Type "show copying" and "show warranty" for details.
This GDB was configured as "x86_64-linux-gnu".
Type "show configuration" for configuration details.
For bug reporting instructions, please see:
<http://www.gnu.org/software/gdb/bugs/>.
Find the GDB manual and other documentation resources online at:
    <http://www.gnu.org/software/gdb/documentation/>.

For help, type "help".
Type "apropos word" to search for commands related to "word"...
Reading symbols from vmlinux...
(gdb) target remote :1234
Remote debugging using :1234
0x000000000000fff0 in exception_stacks ()
(gdb) b start_kernel
Breakpoint 1 at 0xffffffff831c0fb5: file init/main.c, line 934.
(gdb) c
Continuing.

Breakpoint 1, start_kernel () at init/main.c:934
934	{
(gdb)
```

`start_kernel` 是 Linux 核心在完成處理器架構相關的初始化之後的進入點，到達這個 breakpoint 之後就可以用 gdb 讓 kernel 進行單步執行或檢查記憶體、處理器等 debug 工作

Linux 提供的 gdb 指令都是 `lx-` 開頭，可以用 `apropos` 列出相關的指令

```
(gdb) apropos lx-
lx-clk-summary -- Print clk tree summary
lx-cmdline --  Report the Linux Commandline used in the current kernel.
lx-configdump -- Output kernel config to the filename specified as the command
lx-cpus -- List CPU status arrays
lx-device-list-bus -- Print devices on a bus (or all buses if not specified)
lx-device-list-class -- Print devices in a class (or all classes if not specified)
lx-device-list-tree -- Print a device and its children recursively
lx-dmesg -- Print Linux kernel log buffer.
lx-fdtdump -- Output Flattened Device Tree header and dump FDT blob to the filename
lx-genpd-summary -- Print genpd summary
lx-iomem -- Identify the IO memory resource locations defined by the kernel
lx-ioports -- Identify the IO port resource locations defined by the kernel
lx-list-check -- Verify a list consistency
lx-lsmod -- List currently loaded modules.
lx-mounts -- Report the VFS mounts of the current process namespace.
lx-ps -- Dump Linux tasks.
lx-symbols -- (Re-)load symbols of Linux kernel and currently loaded modules.
lx-timerlist -- Print /proc/timer_list
lx-version --  Report the Linux Version of the current kernel.
(gdb) 
```

## Reference

http://nickdesaulniers.github.io/blog/2018/10/24/booting-a-custom-linux-kernel-in-qemu-and-debugging-it-with-gdb/