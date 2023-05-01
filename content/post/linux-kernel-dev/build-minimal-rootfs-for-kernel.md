title: 最小的 Root Filesystem 需要哪些東西
date: 2023/03/11
category: os/linux
excerpt: 編譯完 Linux kernel 在 QEMU 中跑起來之後，完整啟動後遇到的第一個錯誤應該會是 Unable to mount root fs ，從解決這個錯誤到進入一個可以執行的 shell 其實不會太遠，接下來就建立一個可以讓 QEMU 上的 Linux 執行 shell 的磁碟 image
---

編譯完 Linux kernel 在 QEMU 中跑起來之後，完整啟動後遇到的第一個錯誤應該會是 `Unable to mount root fs` ，從解決這個錯誤到進入一個可以執行的 shell 其實不會太遠，接下來就建立一個可以讓 QEMU 上的 Linux 執行 shell 的磁碟 image 。

在沒有 root 權限的環境沒辦法掛載檔案系統，方法會比較不一樣，我們先以有 root 權限的環境進行。

## 建立 image 和格式化

```
dd if=/dev/zero of=a.img bs=1M count=128
mkfs.ext3 a.img
```

## 準備 init 程式

現在 a.img 裡面已經有一個 ext3 的檔案系統了，如果直接用這個 image 當作開機碟的話， kernel 會給出 `No working init found` 的錯誤訊息。接下來就需要掛載他然後寫需要的檔案進去，我們利用 `mknod` 和 `losetup` 建立 loop device 並掛載：

```
sudo losetup -f a.img
mkdir mnt
#這裡的 loop8 改成 losetup 建立的 loop device 名稱，可以用 losetup -l 查詢
sudo mount /dev/loop8 ./mnt
```

`No working init found` 錯誤訊息的意義是找不到第一個 user space 的程式 init ， Linux kernel 會嘗試在 root FS 裡找 /sbin/init 這個執行檔。在大部分桌面電腦使用的 Linux distribution 中會是 systemd 或 openRC 這類系統服務管理器。目前的目標是建立能跑的最小 root FS ，所以我們使用一個二進位檔就能運作的 busybox ，下載已經編譯好的版本把他移到剛剛掛載的目錄裡：

```
wget https://busybox.net/downloads/binaries/1.35.0-x86_64-linux-musl/busybox
sudo chmod +x busybox
sudo mkdir mnt/{sbin,bin}
sudo cp busybox mnt/
sudo ln -s /busybox mnt/sbin/init
```

接著卸載這個 root FS 就可以再啟動一次 Linux kernel ：

```
umount mnt
qemu-system-x86_64 -kernel arch/x86/boot/bzImage -nographic -append "console=ttyS0 nokaslr root=/dev/sda rw" -drive format=raw,file=../rootfs/a.img
```

這裡可能出現的小疑惑是 root 還沒掛載前 kernel 怎麼知道 /dev/sda 在哪裡？這個猜測沒錯，所以 Linux kernel 中實際上會把 `/dev/XXYN` 這樣格式的路徑直接轉換為不同介面的磁碟對應的 major number 和 minor number ，不會再從 VFS 嘗試尋找路徑。

這次執行的 QEMU 應該能看到 `Please press Enter to activate this console.` 的提示，再按一次 enter 就可以看到 shell 了，可以用 `/busybox XX` 的方式執行 busybox 支援的指令了。

```
/ # /busybox ls /
bin         busybox     dev         lost+found  sbin
/ # /busybox mkdir /proc
/ # /busybox mkdir /dev/pts
/ # /busybox mount proc /proc -t proc
/ # /busybox mount devpts /dev/pts -t devpts
```

## References

[losetup(8): set up/control loop devices - Linux man page](https://linux.die.net/man/8/losetup)

[How to add more /dev/loop* devices on Fedora 19](https://unix.stackexchange.com/questions/98742/how-to-add-more-dev-loop-devices-on-fedora-19)

[How does a kernel mount the root partition?](https://unix.stackexchange.com/questions/9944/how-does-a-kernel-mount-the-root-partition)

[bootparam(7) — Linux manual page](https://man7.org/linux/man-pages/man7/bootparam.7.html)

[Creating Initramfs](https://medium.com/@kiky.tokamuro/creating-initramfs-5cca9b524b5a)

[name_to_dev_t](https://elixir.bootlin.com/linux/latest/source/init/do_mounts.c#L277)