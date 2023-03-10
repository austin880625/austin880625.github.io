title: Cache Prefetching 及在 Linux Kernel 中的使用
category: os/linux
date: 2020/03/14
---
因為在研究某個 cache 使用情境時自己想到一種可能的最佳化策略，查查資料和翻書發現原來已經（一部分）被提到過了，以前上課果然不夠認真...

## Cache Prefetching

在計算機組織或作業系統的課程中， cache 是幾乎一定被提到的主題，除了~~各種 cache policy 和 miss rate 很好考之外~~，他算是一種以工程方法面對理論模型的經典例子（數學上的電腦模型只負責到認定記憶體為 sequential access 或 random access），在白算盤（Computer Organization and Design）介紹 memory hierarchy 的章節中，除了 cache replacement policy 之外，也在結尾提到幾種增進 cache 效率的方法，其中一種便是 prefetching。

cache 有用的原因是來自空間（spatial）和空間（temporal）的局部性（locality），將記憶體中被存取的資料附近的資料一併帶到距離 CPU 更近的儲存空間中，並把短期內沒有被使用的資料從這樣的空間移除，這樣大大的增加了同樣資料或附近的資料再次被存取時的效能。但 cache replacement policy 只負責在資料被存取時新增/移除資料，如果能在資料被存取前就先把資料帶到 cache ，是不是就連第一次存取時的 cache miss 都省了？

Prefetching 就是這種策略的實現。想法上是直接將資料帶到 cache ，但設計上把這套機制和 cache 分開或許比較不會影響 cache replacement policy 本身。因此在硬體上其中一個較著名的實作是在 cache 之外使用 stream buffer ，在發生 cache miss 時將存取的位址附近連續幾個位址上的資料移動到 buffer 中，如果接下來存取的地址剛好是連續的，那麼 buffer 就會把最前面的資料移入 cache 中，把剩下的資料繼續往前 shift 。

在軟體方面， x86 指令集中，其實本來就有一系列的 cache 操作指令供軟體控制 cache 的行為，讓程式或編譯器對 cache 作最佳化，比如一段程式進行的記憶體操作如果是對連續一個區塊寫入而不讀取的話，就可以控制這段區塊的記憶體內容不要進入 cache ，從而省下讀取記憶體的 memory request 的時間。而 prefetch 也是這些指令的其中一員，使用情境通常是記憶體存取的位置相對難預測時，可以透過 prefetch 指令讓記憶體存取提早進入 pipeline 中。

到這裡事情看起來很美好，但這件事顯然不是多多益善，找了一下發現了一個在作業系統這種對速度斤斤計較的情境中的使用案例。

## Linux Kernel 曾經的 Prefetching

在 linux kernel 的 API 中提供了一個叫 `prefetch()` 的界面，可以用來產生不同處理器上專用的 prefetch 指令，在 kernel 中的資料會講求減少 cache miss ，又假如資料結構的性質會在記憶體上產生「跳來跳去」的存取對 cache 相當不友善，於是某個叫做 link list 的資料結構就被拿來開刀了。所以在 linux kernel 中（以及網路上衆多對 prefetch 的介紹文章）曾經有過下面這一段程式碼：

```C
#define list_for_each(pos, head) \
for (pos = (head)->next; prefetch(pos->next), pos != (head); \
        pos = pos->next)
```

這是遍歷一個 link list 的 for 迴圈， 在每次檢查 loop condition 時 prefetch 下一個節點，在 loop body 跑完之後，下一個節點的內容應該就會在 catch 中， 執行到 `pos = pos->next` 時便不會發生 cache miss 。

這在當時被認為是個合理的最佳化手段，在一些過去的處理器（據 mailing list 來看是 AMD K7 系列的處理器）中確實也起到改善效能的作用，直到一位叫 Andi Kleen 的 kernel contributor 做了將大部分 prefetch 移除的 patch ，後續幾位 linux contributor 包含 Linus 本人也對這份 patch 進行一些測試，發現這樣的「最佳化」反而讓程式變慢了。

在相關的討論中提到了速度變慢的幾個原因，包含 CPU 已經會使用自己的預測策略進行 prefetch 了，額外使用 prefetch 指令反而會增加 prefetch unit 的負擔、 kernel 運行時使用的 link list 太短以至於太常對 `NULL` 做 prefetch 、 prefetch 指令會消耗額外的 register 等。因此對 list 的 prefetch 從 kernel 版本 3.0 以後便被移除。

## 結論

作業系統是和硬體合作相當密切的軟體，因此系統的效能瓶頸往往不會是只看程式邏輯或是計時就能確定，還需要確認處理器對這些程式執行的行為。而一個最佳化的手段是否有效也會不斷被硬體的更新影響。

## 參考資料

[Cache Prefetching 維基百科](https://en.wikipedia.org/wiki/Cache_prefetching)

[https://stackoverflow.com/questions/20697215/when-should-we-use-prefetch](https://stackoverflow.com/questions/20697215/when-should-we-use-prefetch)

[The Problem With Prefetch](https://lwn.net/Articles/444336/)

[Remove implicit list prefetches for most cases](https://lwn.net/Articles/404033/)