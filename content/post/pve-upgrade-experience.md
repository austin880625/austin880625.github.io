# Proxmox VE 6.x -> 8.1 驚險升級過程紀錄
date: 2023/11/27
category: server
excerpt: PVE 太久沒升級，一升上去就作死手殘好幾步差點掉一堆資料。沒有技術內容的分析，純粹作為以後警惕。
---

上個月初搬回台灣定居，回家中的各種好處之中，其中一項就是比較不用擔心平常實驗用的 server 斷線了，也比較有時間回家做一些小升級。兩個禮拜前在回家前就找了預計升級的 CPU ，準備回去也把現有的 CPU 連著以前堆積的一些零件順便拼成一台完整的電腦。也順便看了 Proxmox VE 的升級流程，覺得如果是 6.x 升級到 8.1 最新版的話，似乎走備份後重灌的流程比較容易。所以就準備好了安裝碟想說一次升級。

## 硬體準備

從新北到高雄來回一趟的成本說低不低，所以希望一次完成越多事情越好。規劃帶過去和回家路上買的東西有這些：

* 要升級的 CPU： Ryzen 5800X3D 。太晚想到要升級， 5950X 已經有點難找且大多是有點盤的價錢了。
* 臨時備份用硬碟： server 上所有資料看起來只有 200 多 G ，整個 array 也只有 2
T 左右，後來自己買的 4T 外接硬碟就帶著感覺綽綽有餘。
* 一台簡單的筆電：修一些網路問題接 switch 用，**如果筆電沒 RJ-45 記得帶 type-C 網卡**。
* PVE 安裝碟：載好安裝 iso 檔直接 dd 進隨身碟就可以。

要帶回來新北的東西有這些：

* 換下來的 CPU ： Ryzen 3100 ，人窮的時候一台文書機也會當成 server 。
* 和 CPU 一起買的主機板、記憶體、散熱膏和 SSD ：主機板是合購價要搭配的 B550 的板子，我的 server 主機板嚴格來說應該算是有 10G 網卡和 IPMI 的 x570 ，所以 5800X3D 搭這張、 3100 換下來搭合購的板子應該比較適合。也發現 SSD 原來已經降到 500 以下了所以多買了一顆。
* server 很久以前用的機殼：總之就是個 M-ATX 的殼。
* 很久以前抽獎抽到的基礎水冷套件：剛好 5800X3D 已經不附風扇了直接拿來用，很久以前以為是給 Intel 的腳位用的後來發現裡面的轉接架全部都可以用。
* HDMI 之類的線材。

## VM 、 containers 備份

我的機器是純粹給自己用的可以容許有 downtime 。所以就很乾脆的把所有 VM 和 container 關起來，接上外接硬碟後按照官方文件備份：

```
# 備份所有 VM 和 containers
vzdump --mode [stop|suspend|snapshot] --all --dump-dir /mnt/path-to-mounted-disk
```

## 設定檔備份

官方的說明沒有直接提到，但社群的慣例是會把 `/etc` 複製一份。沒有提的原因可能是升級系統版本本來就有可能改到這裡面的檔案，還是複製一份的原因是時間久了會有些連自己都忘記有的 config 寫法或 cronjob 類型的自動化流程，大小不大但要用的時候可以省很多重寫的時間。

## 安裝前檢查、休息、和動腦！！

因為完整的重灌完成後會很難回頭，所以這一步想得越慢越好，順便讓備份確實的慢慢跑完，這裡沒有做完最多就是下次再升級而已不會掉資料，所以千萬不要急。從剛開始到這一步我實際上作死的步驟有這些：

* 忘記帶網卡：螢幕沒畫面想接 switch 看 server 的網路有沒有通的半夜才發現。還好有 24 小時營業的小北。
* 沒有備份 `/etc` ：灌完才想到我的網路和 storage 的架構都設定得比較特別，沒了設定檔只能從頭重新摸。
* 亂挑 image 備份 ：以為重灌只會動到系統碟， VM 的資料都在獨立的 RAID 上，所以就挑掉了幾個容量最大的 disk image ，只備份那些可以很快做完的，明明外接硬碟容量就很夠卻讓自己多了一堆不必要的麻煩。

以上這些就都剛剛好是在我按下 PVE 的確認安裝去吃飯的路上想到的，所以後面的東西就幾乎都在冒冷汗中完成......

## 儲存空間注意事項

除了 VM, containers 都要完整備份之外，真的要挑 image 的時候一定要注意自己存 VM 的裝置是不是完全獨立的。像以下的配置就不是：

* 用 mdadm 而不是 PVE 預設的 zfs 建立 RAID 。
* SSD 前面數個小分區作為 root FS 系統碟，後面剩的空間當作 RAID 陣列的 bcache cache device。

這樣配置的話，系統碟在重裝被洗掉的時候後面的 cache 也很有可能被洗掉。這時候在 cache 裡的資料究竟有沒有被寫回 RAID 陣列裡就沒有人能保證了。而 PVE 剛裝好的時候沒有 mdadm 也沒有 bcache-tools ，所以也會呈現什麼 RAID 陣列都讀不到只剩四顆乾淨硬碟的恐怖景象。

裝回來又經過一兩次重開機後就發現我的 RAID 陣列和原本建立的 LVM 突然讀得出來了，把他們補進 storage.cfg 之後就回復原本操作 PVE storage 的方式。

更簡單的解決方式或許是再買一顆獨立的系統碟就可以和 cache 分開了。

## 網路設定注意事項

為了讓 server 裡的 VM 能夠連接到不同的內網網段和對小烏龜做 PPPoE 的連線，也為了善用珍貴的網路孔，我在一個 port 上設定了 VLAN 的 trunk port ，主要的連外網路也是在這個 trunk port 上的其中一個 VLAN 。 PVE 在安裝的時候只有 DHCP 和 static IP 兩種選項，所以裝完維持原本接線的話網路自然是不會通的。架構畫圖很麻煩而且我現在也很疑惑為什麼我要自己搞那麼複雜，就把比較關鍵的 interfaces config 放上來比較不怕忘記。

```
# /etc/network/interfaces
auto lo
iface lo inet loopback

iface enp36s0f0 inet manual

# put vlan tag on physical NIC
iface enp36s0f0.4 inet manual
iface enp36s0f0.2 inet manual
iface enp36s0f0.3 inet manual

# put separate virtual bridge device on each VLAN interface
auto vmbr0
auto vmbr1
auto vmbr2
iface vmbr0 inet manual
        address 10.1.1.3/24
        bridge-ports enp36s0f0.2
        bridge-stp off
        bridge-fd 0

iface vmbr1 inet manual
        address 192.168.1.103/24
        bridge-ports enp36s0f0.4
        bridge-stp off
        bridge-fd 0

iface vmbr2 inet manual
        address 10.1.2.3/24
        gateway 10.1.2.253
        bridge-ports enp36s0f0.3
        bridge-stp off
        bridge-fd 0
```

主要是理論上會覺得寫 `vmbr0.xxx` 各自放 IP 設定應該會和在 `vmbr0, 1, 2` 上面分別寫 `enp0s1.xxx` 的效果一樣加上 VLAN tag ，但現實就是打臉，只有後者會起作用。過程也要記得善用 `ifreload -a` `ifup` `ifdown` 和**重開機治百病**，有些像是網卡驅動直接找不到網卡的問題也是莫名其妙就慢慢解掉了。

## 還原 VM, containers

這裡就按照官方文件還原外接硬碟裡的備份檔

```
# 還原 VM
qmrestore /mnt/path-to-mounted-disk/101-backup.vma 100 --storage cached-vol0

# 還原 containers
pct restore 104 /mnt/path-to-mounted-disk/104-2023_11_18-16_52_09.tar --storage cached-pool0
```

## References

[pct(1)](https://pve.proxmox.com/pve-docs/pct.1.html)

[qmrestore(1)](https://pve.proxmox.com/pve-docs/qmrestore.1.html)

[Upgrade from 6.x to 7.0](https://pve.proxmox.com/wiki/Upgrade_from_6.x_to_7.0)
