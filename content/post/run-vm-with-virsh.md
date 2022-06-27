title: 文字介面的 VM 工具 virsh 使用筆記
category: os/vm
date: 2020/04/11
---

對於個人使用的 VM 環境來說，除了圖形化介面的 VirtualBox 或 VMWare 之外，在 Linux 上可以使用的虛擬化技術還有 KVM, QEMU, Xen 等，他們各自可以擁有很多不同的操作介面，可能是文字、圖形或網頁。對這些虛擬化技術如果能有統一的 API ，不同類型的操作介面就可以只用這套 API 控制不同虛擬化技術的 VM ， libvirt 就是提供這種 API 的一套函式庫，而 virsh 則是使用這個函式庫的一種文字介面管理程式。

## 安裝套件

* `qemu-kvm`： QEMU 是一套包含各種架構模擬器的總稱， kvm 是 linux 操作不同處理器的虛擬化指令集的 kernel module ， qemu-kvm 則是利用 kvm module 建立虛擬機的模擬器。
* `libvirt`： 一套以 C 語言撰寫的 library ，提供一套統一的界面來操作不同虛擬化技術的 VM。這裡用 libvirt 操作的虛擬化技術是 KVM。
* `libvirt-client`： 操作 libvirt 的 client 端程式，包含文字介面工具 virsh。
* `virt-install`：方便使用 libvirt 建立 VM 的文字介面工具。

## 權限設定

非 root 的使用者需要在 kvm 這個 group 中才能建立/控制 VM。

## 使用 virt-install 建立 VM

以安裝 Archlinux 為例，在 archlinux 的 iso 檔所在目錄中，底下的指令可以快速的建立一臺 VM 並開機

```
virt-install \
    --name=<vm_name> \
    --vcpus=1 --memory=1024 \
    --cdrom=archlinux-2020.04.01-x86_64.iso \
    --disk size=20,format=vmdk \
    --os-variant=archlinux \
    --graphics=vnc,port=5900,listen=0.0.0.0 \
    --noautoconsole
```

在文字介面中使用 --graphics=vnc 參數可以將畫面輸出到 vnc 協定上，並且可以指定 port 及 bind address 。如此就可以從遠端連入該虛擬機器的畫面進行操作，由於可以指定 port ，使用前務必檢查防火牆有沒有擋下所使用的 port 。

## virsh 常見指令

### `virsh list [--all]`

列出正在運行的（加上 --all 是全部） VM 。

### `virsh start <vm_name>`

啟動指定的 VM 。

### `virsh destroy <name>`

強制關閉指定的 VM 。

### `virsh shutdown <name>`

對指定的 VM 送出關機指令。

### `virsh undefine <name> [--remove-all-storage] [--wipe-storage]`

刪除指定的 VM ，並指定是否刪除相關磁碟映像檔。