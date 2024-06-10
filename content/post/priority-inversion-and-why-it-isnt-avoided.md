title: Priority Inversion 是什麼？作業系統應該避免嗎？
date: 2024/06/11
category: os
thumbnail: https://img.austint.in/UN0o2vP91OI_YMCDkQ2BdAxwxQo=/fit-in/760x560/filters:format(webp)/priority-inversion-and-why-it-isnt-avoided/unbounded_priority_inversion.drawio.png
excerpt: 在作業系統課程中，會提到一種叫做 priority inversion 的現象，這個現象通常是不希望發生的，通常也會順帶介紹幾種解決方式。但有些作業系統沒有把這些 protocol 通常沒有包含在預設的 scheduling policy 中。本文從一些文件和歷史 mailing list 來推測可能的原因。
---

在作業系統課程中，會提到一種叫做 priority inversion 的現象，我記得當初對這個問題有看沒有懂，其中一個疑問是「這個行為看起來很對啊哪裡有問題」。感覺是沒有聽到這個問題的 context 。通常課堂也會順帶介紹幾種解決方式，但幾種普遍的作業系統（Linux, FreeRTOS）中，這些 protocol 通常沒有包含在預設的 scheduling policy 中。畢業很久想到專題做過的東西來複習就想到應該來找一下這個問題的原因，順便找到了當時一題期中考題困惑已久的答案。

## Priority Inversion

先介紹幾個重要的名詞：

1. Preemptive & Cooperative kernel: Cooperative kernel 表示這個 kernel 上運作的 task 是透過主動放棄 CPU 資源或 system call 有阻塞(block)來觸發 kernel 進行排程。 preemptive kernel 則是系統會通過中斷機制停止 task 並視 kernel 的需要觸發排程。
2. Priority scheduling: 系統依照對 task 指定的優先級選擇排程觸發時要執行的 task 所以排程器透過中斷觸發時，會選擇可執行的任務中優先級最高的 task 執行，比較高優先級的任務比其他低優先級任務先被選中的過程稱作搶佔 (Preemption)。
3. Mutex & Semaphore 的差別: mutex 確保任何時候只有一個 task 「持有」（有所屬 owner），所以所有task 都在獲得 mutex 後再操作 critical section 的資料就能確保同時只有一個 task 寫入或讀取。 Semaphore 邏輯上是一個整數，透過 signal() 和 wait() 介面來增減值，所有 task 都可以對其增減值，所以沒有 ownership 的概念。

接著就能介紹主角，就如名字所表示的， priority inversion 讓優先級低的任務比優先級高的任務先分配到 CPU 時間。 Priority inversion 分為兩種，一種是 bounded 一種是 unbounded 。 Bounded priority inversion 發生在有一個高優先級的 task （稱為 A）和一個低優先級的 task （稱為 B）利用 mutex 共享資源的時候。當 task B 先取得 mutex ，在持有鎖的期間被 preempt 輪到高優先級的 A 執行，在 A 嘗試獲得 mutex 的時候就會被 block 住，造成優先級高的 A 需要等待優先級低的 B 釋放 mutex 才能繼續執行，也就是優先級低的 task 反而能先獲得 CPU 資源，因此稱作 priority inversion 。而稱作 bounded 的原因主要是共享資源的兩個 task 是程式設計者事先已知的，所以這段影響的時間是可以被開發者控制和預測的，所以 bounded priority inversion 通常不被視為一個問題。

![Bounded priority inversion](https://img.austint.in/D7zRSwNbFGdeQr7cHMA4l9bar90=/fit-in/760x560/filters:format(webp)/priority-inversion-and-why-it-isnt-avoided/bounded_priority_inversion.drawio.png)

Unbounded priority 就有點不一樣，它的情境是有三個高、中、低優先級的 task （我們分別稱作 A, B, C）， A 和 C 用一個 mutex 共享資源。一開始 C 先拿到 mutex ，在持有期間 A 嘗試獲得 mutex 就會被 block 。這個時候 B 開始執行，不出意外的話就要出意外了， B 因為優先級在 A, C 之間會 preempt C ，接下來 C 就只能等到 B 釋放 CPU 時間才有機會執行到，假如除了 B 還有其他 D, E, F... task 的優先級都在 A, C 之間，接下來的時間 scheduler 都不會選擇 C ，最後就會導致 task A 被無止境的卡住。

![Unbounded priority inversion](https://img.austint.in/UN0o2vP91OI_YMCDkQ2BdAxwxQo=/fit-in/760x560/filters:format(webp)/priority-inversion-and-why-it-isnt-avoided/unbounded_priority_inversion.drawio.png)

## 作業系統避免 Unbounded Priority Inversion 的方法

想要解決 priority inversion 的人認為其發生的原因是能夠釋放 lock 的 task 沒有機會執行到，所以在作業系統層面避免 priority inversion 的方法都是「讓持有 lock 的 task 盡快執行並結束 critical section 」。其中一種最直接的方法就是關掉中斷避免發生 context switch ，這也是最原始的 critical section 實作方法。第一次看到的人可能覺得這個方法太白爛了，但其實下面幾種主流的方法我看了其實也覺得有點白爛。我們繼續用上面 task A, B, C 的例子介紹這幾種方法。

### Priority Inheritance

基本操作很簡單，就是在 task A 嘗試持有 lock 的時候將持有 lock 的 task C 的優先級提高到和 A 一樣，如此 task A 被 block 住的時候， task C 就不會被 task B preempt 了。

### Priority Ceiling Protocol(PCP)

這個方法是將每個 lock 都指定一個 priority ceiling ，設定為會使用這個 lock 的 task 中最大的 priority ， task C 在一開始持有 lock 的時候 priority 就會被提高到這個 ceiling 。也就是在持有 lock 的期間就讓這個 task 比所有可能請求這個 lock 的 task 的 priority 還高。

### Random Boosting

根據微軟的文件， Windows 就是採用這種方法。 scheduler 會對所有 ready state 的 task 隨機提升 priority ，這樣持有 lock 的 task 就永遠有機會被執行並釋放 lock 。算是一種比較消極解決的方法。

## 作業系統不鼓勵這些實作的原因

上面的方法都很簡單，實際上也能解決問題。不過對我來說這些方法很白爛的原因就是看起來都很像先射箭再畫靶。想要避免被 preempt ？那就提高優先級就不會囉～在 general purpose 的作業系統中，沒有直接使用這些機制的原因也是認為 lock 和 task 的優先級管理應該是程式開發者的責任，不應該被作業系統介入。作業系統介入解決表面上可以減少應用程式設計者使用 lock 的負擔，但在 task 或 lock 上額外加上的資訊（例如提高優先級之前原始的優先級或 lock 的最高優先級）卻依然讓程式設計者需要知道這些機制的運作才能知道自己 task 設定好的優先級會怎麼樣被「破壞」，所以並沒有減少應用程式設計的認知負擔。而比較正常的實作以 unbounded priority inversion 的情境來說，應該是避免不同優先級的 task 競爭相同的資源，較低優先級的 task 透過 IPC 向管理資源的較高優先級的 task 做出相關的請求達成使用相關資源的目的。

## 那個神秘的期中考問題

當時遇到的題目似乎是比較開放式的問答，大意是 mutex 和 semaphore 不一樣的地方可能讓 semaphore 在 priority scheduling 遇到什麼問題。當時我是沒什麼頭緒的把這題放掉的，後來有聽說關鍵字是 priority inversion ，但也一直沒感覺是不是 semaphore 對 priority inversion 有什麼影響，該被 block 到的 task 還是會 block 。

後來看了一篇 StackOverflow 問答才感覺應該是答案。問題應該是在問解決過程中遇到的問題而不是 priority inversion 的過程的問題。上面的 priority inheritance 和 priority ceiling 都需要操作 lock 持有者的優先級，所以需要 owner 的資訊，而 semaphore 沒有持有者的概念，所以發生 priority inversion 的時候就沒辦法套用這兩種方法。從這個方面來看反而是 random boosting 獲勝了（？

## References

Operating System Concepts 恐龍本

[Preemptive Process Scheduling 的觀念](https://www.jollen.org/blog/2006/11/_scheduler_running_process.html)

[Semaphore priority inversion](https://stackoverflow.com/questions/15755080/semaphore-priority-inversion)

[Priority inversion in mutex vs semaphore](https://stackoverflow.com/questions/17777807/priority-inversion-in-mutex-vs-semaphore)

[What is bounded and unbounded priority inversion? Also explain how it is solved using priority inheritance and priority ceiling.](https://www.ques10.com/p/54411/what-is-bounded-and-unbounded-priority-inversion-a/#:~:text=Bounded%20priority%20inversion%3A,of%20higher%20priority%20task%20begins.)

[Re: [PATCH 1/19] MUTEX: Introduce simple mutex implementation](https://lkml.org/lkml/2005/12/16/265)

[Priority Inversion - Win32 apps | Microsoft Learn](https://learn.microsoft.com/en-us/windows/win32/procthread/priority-inversion)

[Recursive Lock (Mutex) vs Non-Recursive Lock (Mutex)](https://stackoverflow.com/questions/187761/recursive-lock-mutex-vs-non-recursive-lock-mutex)

[Priority Ceiling Protocol - GeeksforGeeks](https://www.geeksforgeeks.org/priority-ceiling-protocol/)