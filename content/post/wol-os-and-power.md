title: Wake on LAN 需要的設定選項與代表的意義
date: 2020/10/01
category: computer-tips
---
Wake on LAN(WoL) 可以讓電腦在睡眠或關機時由區域網路中的其他主機喚醒，為了啟用這項功能， BIOS 和作業系統中的設定選項都需要設定成正確的值。每個設定選項看起來都差不多，所以第一次設定會以爲意義也都差不多，但其實不是。 WoL 的喚醒訊號基本上會經過網路卡、網路卡與主機板的界面再到主機板的電源管理模組。所以不同設定其實是在控制這些元件在遇到喚醒訊號時各自的行為，因此這些設定才會缺一不可。底下列出幾項設定 WoL 需要的選項以及他們各自代表的實際意義。

## BIOS 裡的設定

### Wake on LAN/Wake on PCI

設定值：開

這個選項最直白，他的意義是主機板在收到來自 NIC 或 PCI 的喚醒訊號時要不要進行喚醒。

如果網卡是內建的而不是插在 PCI 介面上那可能不一定需要選 Wake on PCI (看內建網卡設計上是不是佔一個 PCI address) ，如果網路卡是經過 USB 介面的外接網卡，那可能需要選的就是 Wake on USB 而不是 Wake on PCI 。

### EuP/ErP mode

設定值：關

有些主機板不把這個關掉 WoL 的選項就不會出現，有些不管有沒有關掉 WoL 的選項都在，因此成為最大的雷。

這個選項的意義是使電腦符合歐盟 ErP 的能源消耗標準，符合這個標準的電腦會有大家都認得的 CE 標章。這個標準的一項要求是電腦在關機和睡眠時（精確來說是 S3 以下的電源狀態）耗電不能超過 0.5 瓦，有些電腦為了符合這個標準，在開啓這個選項的狀態下就會把網卡供電切斷，如此網卡就沒辦法處理喚醒封包。邏輯上這個行爲和主機板收到網卡的喚醒訊號要不要喚醒是獨立的，那些在把這個選項打開時卻不把 WoL 的選項隱藏的考量可能是在此。

### Deep Sleep Control

設定值：關閉

這個選項跟上面那個類似，但我只有在 Dell 的個人電腦上看過，它的意義是在遇到來自作業系統的關機或睡眠指令時要讓電源狀態進到 S3 還是 S4/S5 ，進到 S5 也跟上面的選項一樣會讓網卡斷電。這個設定的另一個行爲是進到 S4 後收到喚醒封包即使機器會喚醒，在載入 Windows 系統時 Windows 一樣會再把自己關回 S4 ，原因是 Windows 設計上把 S4/S5 認定爲「使用者不希望電腦會被動喚醒的狀態」，這個行爲在其他作業系統上是不是也有就不確定。

## 作業系統中的設定

雖然開機的流程是和作業系統無關的，但 BIOS 只能調整主機板自己的行為，對於裝置自己對協定特定的控制行爲就只能用驅動程式和裝置溝通，而對於作業系統面對來自不同裝置喚醒的反應也是由作業系統決定。這些行為需要透過作業系統中的網卡設定來達成。

在 Linux 中，依照發行版有點差異，但大致都是用類似 ethtool 類的工具將網卡的 wol 選項開啟。

在 Windows 中則是在裝置管理員中選取網卡右鍵點內容，在進階分頁中有 Wake on LAN 的選項，將選項開啟。如果 Wake on LAN 選項沒有出現，那可能是需要安裝網卡的原廠驅動程式而不是微軟的版本。

在兩種作業系統中，這個選項的意義是透過驅動程式告訴網卡「如果收到喚醒封包，要對主機板送出喚醒訊號」。也就是這個選項關閉的話，雖然主機板收到喚醒訊號會開機，但網卡根本不會送出喚醒訊號。

在 Windows 中，網卡內容還有另一個選項是電源分頁中的「允許此裝置喚醒電腦」，這個選項是指定收到喚醒訊號的行為，但到底是作業系統透過驅動程式告訴主機板的晶片組還是作業系統在喚醒後被載入後做的判斷則不是很確定。

## References

[Does wake-on LAN/WOL depend on hardware or the operating system?](https://serverfault.com/questions/191854/does-wake-on-lan-wol-depend-on-hardware-or-the-operating-system)

[Newer Dell system models will not Wake-On-LAN with Deep Sleep Control set to S5 in the Windows](https://www.dell.com/support/article/zh-tw/sln307243/newer-dell-system-models-will-not-wake-on-lan-with-deep-sleep-control-set-to-s5-in-the-windows?lang=en)

[Energy-related Products - Wikipedia](https://en.wikipedia.org/wiki/Energy-related_products)
