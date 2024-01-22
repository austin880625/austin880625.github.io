title: Linux 5.18 核心正式版發布，有哪些重要更新
date: 2022/05/28
path: 2022/05/28
---

5/22 Linus Torvalds 在 LKML 上公告了 Linux 5.18 的正式發布， Linus 在公告信中表達這次的發布「沒有發生太多意外」，並且鼓勵大家下載來測試。裡面提到的主要更新有驅動程式、網路實作和測試工具。

## 驅動程式

在驅動程式中受到特別關注的有 Intel 的 Software Defined Silicon(SDSi) 機制，可以讓使用者透過購買授權來啟用晶片中預設關閉的功能， Intel 在近期一直很活躍的發布有關這個機制的 patch 和文件，主要是在系統中模擬一個可以接收授權後簽章的 PCIe 介面，但還沒有說明會用這個機制來限制未來 CPU 的什麼功能。還有特斯拉的 Full Self Driving(FSD) 自動駕駛系統的驅動程式。大廠的硬體被整合進 Linux kernel 應該不算是什麼新聞，不過前者挑戰了「自由軟體要讓使用者能夠完全控制自己的硬體」的哲學，後者應該是讓大家發現 Linux 又多了一項在未來的應用而受到注意。

## 檔案系統

在 kernel 編譯選項中正式把 ReiserFS 標記為 deprecated 。這是 Linux kernel 收錄的第一個日誌型檔案系統，因為原開發者 Hans Reiser 因謀殺案被判刑入獄而沒辦法再維護也讓很多人不願意使用， Linux 社群計畫在 2025 年前將 ReiserFS 完全自 kernel 程式碼內移除。

## C 語言標準

在 5.18 版 Linux 開始升級到 C11 標準，等於從 C89 跳過 C99 一次跳了 33 年，不過仍然繼續使用一些 gcc 的擴充語法(使用的 flag 是 `-std=gnu11`)。驅使這項轉變的是 Linux kernel 常用的一項遍歷 double link list 的 macro ：`list_for_each_entry` ，這個 macro 需要一個事先宣告的 iterator 變數，由於 Linux 裡的 link list 是設計成環狀的，這個 macro 只用 iterator 是否到達列表起點判斷是否走訪完畢，這個 macro 中的 for 迴圈結束後事先宣告的 iterator 指標仍然可以被存取，但有可能在列表起點，造成 for loop 結束後指標指向型別不同的物件而非 list 中的其中一個物件。

這段討論一開始被認為是 speculative execution 的安全性問題(因為 for loop 的 branch prediction 失敗時 loop body 可能會作用在 list 起點上)，後來 Linus 提出 iterator 在 for loop 外面就夠難搞了，所以便決定改為升級 C11 標準讓 iterator 可以宣告在 for loop 內部。

## 其他東西

都是我不會的東西，在網路實作的部分主要是在 bridge interface 上支援了 Multiple Spanning Tree(MSTP) 協定，還有 user event 可以使 userspace 的 process 發送可供 perf 類工具監聽的事件。

## References

[https://lkml.org/lkml/2022/5/22/274](https://lkml.org/lkml/2022/5/22/274)

[https://www.zdnet.com/article/linux-kernel-5-18-arrives-heres-whats-new/](https://www.zdnet.com/article/linux-kernel-5-18-arrives-heres-whats-new/)

[https://kernelnewbies.org/Linux_5.18](https://kernelnewbies.org/Linux_5.18)

[https://lwn.net/Articles/888736/](https://lwn.net/Articles/888736/)

[https://lwn.net/Articles/889266/](https://lwn.net/Articles/889266/)

[https://lwn.net/Articles/884876/](https://lwn.net/Articles/884876/)

[https://segmentfault.com/a/1190000041470767/en](https://segmentfault.com/a/1190000041470767/en)

[https://lwn.net/ml/linux-kernel/20220217184829.1991035-1-jakobkoschel@gmail.com/](https://lwn.net/ml/linux-kernel/20220217184829.1991035-1-jakobkoschel@gmail.com/)

[https://lwn.net/ml/linux-kernel/86C4CE7D-6D93-456B-AA82-F8ADEACA40B7@gmail.com/](https://lwn.net/ml/linux-kernel/86C4CE7D-6D93-456B-AA82-F8ADEACA40B7@gmail.com/)