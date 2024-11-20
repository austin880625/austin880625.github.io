# 從 Link Register 看函式呼叫的前世今生
category: embedded
date: 2024/10/15
excerpt: 在開發嵌入式系統的程式時，通常使用的處理器都和桌機/筆電的 x86 不同，因此會注意到有不同的 register ，其中會用 link register 來記錄函式返回的位置。因為功能看起來和 call stack 重複，因此去尋找了 call stack 的一點歷史紀錄。
thumbnail: https://imgcdn.austint.in/dvoTM-C7Srgh6ZmuONraJPHoMpw=/fit-in/760x560/filters:format(webp)/from-link-register-to-function-call/title-2.png
---

大學的時候修計算機組織的時候主要介紹的是 MIPS 處理器，後來偶爾玩一些 ARM 開發板也會看到一些組語，在這兩種處理器上都會看到在一些函式呼叫的流程會用到幾種指令和暫存器：

- `jal`(MIPS) 或 `bl`(ARM) 指令
- `jr`(MIPS) 或 `bx`(ARM) 指令
- `ra`(MIPS) 或 `lr`(ARM) 暫存器

這幾個指令和暫存器的功能是在程式跳轉的時候把跳轉前的 program counter 位址記錄在所謂的 link register 中，在函式執行結束後再跳轉回 link register 記錄的位址。因為 link register 通常只能記錄一個記憶體位址，在這些處理器上的函式如果會再呼叫其他函式或遞迴呼叫，就需要把 link register 的內容進一步存到記憶體的 stack 中，這個 stack 就是一般提到的 call stack 。這裡以 ARM 為例寫一個由 caller 呼叫 callee 簡化的函式呼叫流程：

```
callee:
  ; the leaf callee
  mov r1, 3
  mov r2, 4
  sub r0, r1, r2

  bx lr

caller:
  ; The function that would calls other
  push {r11, lr}  ; r11 是 frame pointer 也要一併紀錄
  bl callee
  mov r1, r0      ; take the return value

  pop {r11, lr}
  bx lr
```

其中的 `caller` 就是會再呼叫其他函式的函式，在使用 `bl` 指令的時候會把 `lr` register 裡面的內容複寫掉，所以在使用之前要用 push 把 `lr` 的內容存進 stack 裡。

以前看到這個流程的感覺是能用就好，但久了腦袋就浮現了幾個疑問。首先是感覺這種流程沒有那麼方便，不知道為什麼不要只 push program counter 就好了，還要再規劃多一個 link register ，或是為什麼這段 link register -> stack 的資料轉移過程不是自動的而是要自己 push 。再來是假如是因為效能考量，看到其他架構的處理器也不一定有這種 link register 的設計，或是也沒有因此多設計更多 link register 似乎也不太合理。以為自己是不是被 ARM 荼毒太多或是被 x86 的 call 系列語法寵壞了，直到最近找了幾篇文章才大概了解這幾種實作的演進。

## 最早的 Call Stack ： ACE

對現代寫程式從 function 階層開始寫的人來說， call stack 算是刻在腦袋裡的概念，看到一段 code 就會想這段會從哪裡呼叫進來，接著會呼叫什麼其他函式或回到什麼地方。但對電腦正要被發明的時代來說，這個概念還不是很多人能輕易想像的：程式主要是打孔紙帶、記憶體是循序存取的 delay line 且非常貴等等。

即使如此，還是有人在 1945 年就設計出能夠用 LIFO 的資料結構儲存指令執行位置的機制，這個人就是大名鼎鼎的 Alan Turing ，他當時設計的電腦被稱為 Automatic Computing Engine (ACE)。他在設計 ACE 的文件中提到用 "note" 紀錄發生切換指令的位置，並且把這些 note 以 "list" 的形式放在 delay line memory （當時使用的記憶體）裡面， Alan Turing 把對這個 list 增加和移除 note 的指令稱作 `BURY` 和 `UNBURY` ，其實除了 "register" 這個名稱之外，已經算是很完整的 call stack 機制了。

不過比較熟悉電腦史的人就會知道， ACE 這部機器最後沒有成功被建造出來，簡化版的 Pilot ACE 也一直到 1950 年才完成。在 1945 年到 1950 年間也還是有如 EDVAC, EDSAC 等電腦被建造出來。這段時間的電腦要執行副程式（subroutine）的方式大部分是打出一樣的打孔紙帶和前面的程式連在一起，而另一個有真正實作 subroutine call 的方案在 EDSAC 這台電腦上，使用的則是被稱為 Wheeler Jump 的機制。

## 現實中其他電腦的方案： Wheeler Jump

Wheeler jump 的名字來自於他的發明人 David John Wheeler ，在 1945-1950 年間的電腦除了 Alan Turing 想到的 ACE 沒有建造出來之外， Call stack 還不是很普及的概念，當時電腦的暫存器也是很珍貴的資源，所以 Wheeler jump 這個技巧雖然看起來有點迂迴，但也在當時成為比較流行的 subroutine call 做法之一。

在 Wheeler jump 中副程式的 caller 準備呼叫的時候會先把當下指令的位址（也就是 program counter）存在 accumulator 上， accumulator 是一種暫存器，但一般作用是用來計算，只要執行任何計算指令它的數值就會被覆蓋掉，選擇 accumulator 就是為了避免使用其他 register 或是電腦上根本沒有多餘的 register 。存好 program counter 之後就是一個 `JUMP TO X` 跳轉到副程式所在的位址。

在副程式的最後一步是另一個 `JUMP TO Y` 形式的指令， Y 在進入副程式時可能是任意數字。在副程式的一開始會做兩件事，第一步是計算 caller 返回的位址，也就是把在 accumulator 中的值加上「JUMP 指令的長度」，通常就是依照不同電腦上的指令架構加 1~3 的固定數值，第二步就是把這個計算出來的值用 `STORE` 指令存放在副程式最後一個指令 `JUMP TO Y` 的 Y 的位址，這個位置需要程式設計者事先知道副程式的位置和長度直接計算出來寫死。這樣在副程式執行結束的時候就會跳轉到原本計算好的 program counter 的位置。這個過程好處是不需要額外的暫存器，並且可以處理一定程度的 nested call ，每一層 nested call 的返回位址會在每個被呼叫的副程式最後一個指令裡。但沒辦法處理遞迴，而且也等於是直接修改執行的 code 本身，一旦寫錯位置或有其他的 bug 會非常難除錯，在現代的程式也會因為 segmentation 的設計沒辦法直接實作這種技巧。具體的程式碼也可以看維基百科中 Wheeler jump 的範例。

## Link Register 的出現

Wheeler jump 與其說是一個實用的方法，不如說是提醒了當時的電腦設計者需要的暫存器，有一個單獨的暫存器可以專門用來存返回位址的話，就根本不需要那些偽裝成計算的存地址和修改自身程式碼的操作了。於是後來的電腦就開始加入這些暫存器，並且一路保留到今天的許多 RISC 架構上。

## Stack linkage 的時代

1970 年代後一個重要的事件是 C 語言被發明了， C 語言的 function call 在語法上沒有限制遞迴呼叫，也不需要額外的宣告。為了標準化 compiler 對不同處理器中處理 function call 的方式，貝爾實驗室也在 1981 年發布了 The C Language Calling Standard ，定義 function call 對參數以及 program counter 的具體處理方式和順序，也就成為標準化的做法。在有 link register 的處理器中如果涉及多層的函數呼叫或遞迴，也會採用這套流程，也就是最近的 return address 放在 link register 中，而其他 return address 和參數就放在 stack 裡。

因為位在 stack 最頂層的幾個位置幾乎都會被 CPU 自己的 cache 保留，所以即使 call 指令看起來會做 memory access 速度也不會太慢。

## 現代電腦設計 link register 的 trade off

Link register 最明顯的優勢就是程式碼中每個 function call 都有機會減少一次記憶體操作，還有在 RISC 上不需要 branch 以外的流程控制指令。但這個方法實作 function call 所節省的記憶體操作主要在 leaf call 上，也就是能夠節省多少時間其實要視整個程式 leaf call 的數量而定。另一個缺點是相對於 stack linkage 的實作，在 function call 時的記憶體操作通常需要自己使用 push/pop 指令，在 code size 會有些許的膨脹。

Stack linkage 所帶來的優缺點可以說是相對的，因為有實作 call 指令，可以減少 code size ，寫 function call 的指令也不需要特別考慮函式是不是 leaf call ，在 CISC 上也可以用 microcode 做到在 call 指令整合額外的記憶體操作（例如 push pc 以外的 register）。

## References

[Wheeler Jump - Wikipedia](https://en.wikipedia.org/wiki/Wheeler_Jump)

[Link register - Wikipedia](https://en.wikipedia.org/wiki/Link_register)

[What are the pros and cons of CPUs using link registers for return address?](https://qr.ae/pslY9h)

[Who invented the call stack?](https://www.quora.com/Who-invented-the-call-stack?top_ans=661084)

[Proposed Electronic Computer, Alan Turing](https://www.alanturing.net/turing_archive/archive/p/p01/p01.php) 第 11 頁起說明了 Automatic Computing Engine 執行 subroutine 的方式

[Subroutine and procedure call support](https://people.computing.clemson.edu/~mark/subroutines.html)

[The C Language Calling Standard](https://www.bell-labs.com/usr/dmr/www/clcs.pdf)

Computer Organization And Design: The Hardware/Software Interface, David A. Patterson, John L. Hennessy

封面圖是 stack 在德文裡老一輩說法， Kellerspeicher 這個字是從「地下室」 der keller 來的，某種程度上 stack 在記憶體上往下長的行為似乎比 stack 更精確一些。