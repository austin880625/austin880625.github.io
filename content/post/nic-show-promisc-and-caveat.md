title: Linux 上查詢網卡 Promiscuous Mode 狀態的方法和問題
category: os/linux
date: 2021/05/08
thumbnail: https://img.austint.in/pZYK25bR5gQkdyEkZ-LcCby2gTU=/fit-in/760x560/filters:format(webp)/promisc.png

excerpt: 我們可以用 ip 和 ifconfig 獲得網卡的 promisc 模式狀態，但顯示的狀態似乎和應用時的預期有差距，探索 Linux kernel 的原始碼找出真正原因

---
## 起點： VM 網路的黑魔法

在常見的 VM 軟體中，網路設定都會有一種模式叫做 bridge mode ，使用這種模式可以將 VM 的網卡和 host 的實體網卡連接在同一個網路中。這個功能第一個想想不太對勁的地方是實體網卡都會有自己的 MAC 位址，網卡的驅動程式理論上不會有 bridge 上其他網卡的 MAC 位址資訊，那網卡在第二層聽到目標不是自己的 data frame 的時候，怎麼知道要不要把這個 frame 收下來呢？除了 VM 之外，在網路監聽這類的應用上，都會開啟網卡的一種叫做 promiscuous mode 的模式，在這個模式中，網卡會將所有的流量全部接收送進系統，由作業系統對收到的資料再做進一步處理。這個模式原理上相當自然，但在使用的過程中，又會發現另一個越想越不對勁的地方。

## 檢查 Promiscuous Mode 狀態的方法？

就算沒有要拿網卡做什麼事，我們還是可以用 `ip` 或 `ifconfig` 指令開啟網卡的 promiscuous mode ，開啟後在兩個指令的網卡 flags 欄位都會出現 `PROMISC` 標誌。如下：

```
> ip link set [interface] promisc on
> ip a
...
3: virbr0: <NO-CARRIER,BROADCAST,MULTICAST,PROMISC,UP> mtu 1500 qdisc noqueue state DOWN group default qlen 1000
    link/ether 52:54:00:bb:1a:1b brd ff:ff:ff:ff:ff:ff
    inet 192.168.122.1/24 brd 192.168.122.255 scope global virbr0
       valid_lft forever preferred_lft forever
...
>
```

或是使用 `ifconfig` 的版本：

```
> ifconfig [interface] promisc
> ifconfig
...
virbr0: flags=4355<UP,BROADCAST,PROMISC,MULTICAST>  mtu 1500
        inet 192.168.122.1  netmask 255.255.255.0  broadcast 192.168.122.255
        ether 52:54:00:bb:1a:1b  txqueuelen 1000  (Ethernet)
        RX packets 0  bytes 0 (0.0 B)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 0  bytes 0 (0.0 B)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
...
>
```

正當我們以為 `ip` 指令顯示的 `PROMISC` 標誌就表示網卡是否在 promiscuous mode 時，奇怪的事情發生了。

試著執行一些理論上應該會開啟網卡 promiscuous mode 的程式，例如 `tcpdump` 或將網卡加入 linux bridge 中，接著執行 `ip` 指令檢查，發現網卡上面並沒有顯示 PROMISC 標籤，難道這些程式其實不一定要開啟 promiscuous mode ？還是 `ip`/`ifconfig` 只在特定情況顯示網卡的 PROMISC 標籤？

## 確認裝置目前 flags 的方式

### Sysfs

Linux 的 sysfs 中會列出系統中的硬體及核心運作資訊，在 `/sys/class/net/<iface>/flags` 這個檔案可以看到網卡的 flags ， flags 是個 16 進位顯示的數字，各個 bit 的對應可以看[這個 enum 定義](https://elixir.bootlin.com/linux/v5.11.15/source/include/uapi/linux/if.h#L82)。

在剛剛提到網卡使用 promiscuous mode 的情境中，可以發現代表 promiscuous mode 的 bit 都有被設定成 1 。

### Netlink

對 `ip` 及 `ifconfig` 指令使用 `strace` 會發現他們分別使用了 netlink 和 ioctl 取得網卡資訊，為此我們稍微看了一些 netlink 的文件，寫一個小程式簡單的把網卡的名稱和 flag 撈出來。

```
#include <stdio.h>
#include <string.h>
#include <asm/types.h>
#include <sys/socket.h>
#include <linux/netlink.h>
#include <linux/rtnetlink.h>
#include <net/if.h>

char recvbuf[8192];

int main() {
	int netlink_socket;
	int ret;
	struct sockaddr_nl addr = {
		.nl_family = AF_NETLINK,
		.nl_pad = 0,
		.nl_pid = 0,
		.nl_groups = 0
	};
	struct {
		struct nlmsghdr nh;
		struct ifinfomsg msg;
		char attrbuf[512];
	} req;
	struct rtattr *rta;
	netlink_socket = socket(AF_NETLINK, SOCK_DGRAM, NETLINK_ROUTE);

	// whole message structure:
	// [netlink header]
	// [netlink route message]
	//   (for RTM_NEWLINK, RTM_DELLINK, RTM_GETLINK)
	//   [ifinfomsg structure]
	//   [a series of rtattr structures]

	// message type: RTM_GETLINK
	memset(&req, 0, sizeof(req));
	req.nh.nlmsg_len = NLMSG_LENGTH(sizeof(req.msg));
	req.nh.nlmsg_flags = NLM_F_REQUEST | NLM_F_DUMP;
	req.nh.nlmsg_type = RTM_GETLINK;

	req.msg.ifi_family = AF_UNSPEC;
	req.msg.ifi_index = 0;
	req.msg.ifi_change = 0xFFFFFFFF;
	printf("Index: %u\n", req.msg.ifi_index);

	ssize_t len = send(netlink_socket, &req, req.nh.nlmsg_len, 0);
	printf("Sent %d\n", len);

	len = recv(netlink_socket, recvbuf, 8192, 0);
	printf("Recv %d\n", len);
	struct nlmsghdr *nh;
	for(nh = (struct nlmsghdr *)recvbuf; NLMSG_OK(nh, len); nh = NLMSG_NEXT(nh, len)) {
		if(nh->nlmsg_type == RTM_NEWLINK) {
			printf("NEWLINK\n");
			struct ifinfomsg *ifi = (struct ifinfomsg *) NLMSG_DATA(nh);
			printf("Index: %u\n", ifi->ifi_index);
			printf("Flags: %u\n", ifi->ifi_flags);
			ssize_t attr_len = nh->nlmsg_len - NLMSG_LENGTH(sizeof(struct ifinfomsg));
			for(rta = IFLA_RTA(ifi); RTA_OK(rta, attr_len); rta = RTA_NEXT(rta, attr_len)) {
				if(rta->rta_type == IFLA_IFNAME) {
					char *name = RTA_DATA(rta);
					printf("Name: %s\n", name);
				}
			}
		} else if(nh->nlmsg_type == RTM_GETLINK) {
			printf("GETLINK\n");
		} else if(nh->nlmsg_type == RTM_DELLINK) {
			printf("DELLINK\n");
		} else {
			printf("Unrecognized message\n");
		}
	}
	return 0;
}
```

初步比對發現得到的 flags 和 ip 指令標籤上有的 flags 基本上是一致的，也就是 netlink 獲得的網卡 flags 資訊會和 sysfs 中的 flags 不同。差不多是時候直接追 Linux kernel 的 code 了。

## Netlink 取得 Flags 的方式

追了一下 netlink 的 code 最後確認取得 flags 的地方是[這段 code](https://elixir.bootlin.com/linux/v5.11.15/source/net/core/dev.c#L8428) ，在 `dev_get_flags` 函式中可以看見包含 `IFF_PROMISC` 在內的幾個 flags 都被 mask 掉了。到這裡我們確定了為什麼兩種方式取得的 flags 會不一樣。從 git log 來看，這個行為好像從設計出來就是這麼寫的。

用這個函式的名稱搜尋發現了幾篇 mail archive 和討論，發現也有人 trace 到這段程式過。這樣做的原因大致是因為 `ip` 及 `ifconfig` 指令所做的啟動/關閉 promiscuous mode並不完全是直接控制網卡這個模式的開關。網卡可能在多種情況下由系統的不同元件（包含 user space 和 kernel space ）啟用 promiscuous mode，除了使用者直接透過指令啟用外，還有上面提到的 bridge 、封包紀錄和部分的 multicast 實作等。因此 kernel 需要以一個 counter 的形式紀錄有多少次啟用 promiscuous mode的請求，一個元件關閉 promiscuous mode的實際操作是將 counter 減 1 ，當這個 counter 下降到 0 時才會真正關閉網卡上的 promiscuous mode。而 `ip` 指令顯示的 `PROMISC` 標誌應該是指是否有從 user space 直接開啟 promiscuous mode 的請求。

這樣想起來上面關於 bridge 及 `tcpdump` 的實驗就變得算是合理，因為除了 `ip` 指令是直接用 `netlink` 存取網卡資訊外， bridge 是操作 Linux kernel 的 bridge module ， `tcpdump` 則是使用 EBPF 。所以因為這些應用程式產生的 promiscuous mode 請求其實應該是由 kernel module 觸發，才沒有讓 `ip` 指令中的網卡顯示 `PROMISC` 標誌。

而[這篇 StackOverflow](https://unix.stackexchange.com/questions/561102/what-determines-an-interfaces-promiscuity-the-interface-flags-or-properties) 更是直接把我們在上面寫的事情從頭解釋一遍。也提到若要顯示網卡啟用 promiscuous 需求的次數，可以在 `ip` 指令中加上 `-d` 參數，就可以看到 promiscuity 欄位上的數字。這個數字對於 user space 來說就成為 read only ，而不是可以被直接設定的值了。

## Reference
[Linux NIC Flags](https://elixir.bootlin.com/linux/v5.11.15/source/include/uapi/linux/if.h#L82)

[IFF_PROMISC again](http://lkml.iu.edu/hypermail/linux/net/0705.0/0001.html)

[flags & IFF_PROMISC -- rtnetlink and sysfs](https://marc.info/?l=linux-net&m=119557466131972&w=2)

[What determines an interface's promiscuity, the interface flags or properties?](https://unix.stackexchange.com/questions/561102/what-determines-an-interfaces-promiscuity-the-interface-flags-or-properties)