# 怎麼認識 tensor （一）
date: 2023/03/08
category: math
thumbnail: https://imgcdn.austint.in/f7CxY-ikjHKrdIDe_RYwtAFDK1c=/fit-in/760x560/filters:format(webp)/understanding-tensor/spider-man-1.jpeg
excerpt: 以前覺得張量這個名字很酷，但各種介紹文章在一開始都看不懂，希望可以寫一系列的文章給跟當時的我一樣的人。
---

> 矩陣就是表格。

在高中對矩陣的數學意義有一點基本認識的我，第一次聽到高中數學老師這樣介紹矩陣的時候心中實在有點生氣，體、向量空間、基底、線性變換全部都沒說，就這樣一句介紹矩陣？

後來當然課綱該教的內容有教完，只不過沒有想到兩三年後成為資工小白，在第一次要理解張量（tensor）的場合，看得懂定義和符號但看不懂為什麼那樣定義和那種表示法有什麼用，於是最後只能先接受在機器學習領域常看到、也和高中數學老師不謀而合的說法：

> 張量就是有$` n_1\times n_2\times n_3 \times ... \times n_k `$個格子的多維數字陣列（可以像矩陣一樣乘他ㄛ）。

標題說的東西這樣就算說完了，畢竟在 C 裡宣告一個 `float A[2][3][4][5][6];` 之後要對他做什麼都可以，跟數學無關的也行。但如果對體、向量空間、基底、線性變換有一點認識的話，應該就可以看我後來覺得怎麼認識 tensor 比較簡單的。

## 多線性變換 和 multilinear form

張量是一種多線性變換（multilinear map），算是線性變換的擴充。最基本的特例除了 linear transformation 之外就是雙線性變換（bilinear map）：給定一個 field $`K`$和$`K`$上的向量空間$`V, W, X`$，函數$`B:V\times W\rightarrow X`$是雙線性變換的意思是$`B`$對$`V,W`$中的向量「分別」是線性的，也就是：

```math
\begin{align*}
B(av+b, w) &= aB(v, w) + B(b, w) \\
B(v, aw+c) &= aB(v, w) + B(v, c) \\
\end{align*}
\\
a\in K\quad v, b\in V\quad w, c\in W
```

第一眼看到會和$`V\times W\rightarrow X`$的線性變換搞混，他們的差別就在「分別」線性的性質，假設$`A:V\times W\rightarrow X`$是線性變換而$`B:V\times W\rightarrow X`$是雙線性變換的話，將$`V, W`$中的元素$`v, w`$乘以一個常數代入$`A, B`$中就能觀察到：

```math
\begin{align*}
A\begin{pmatrix}2v\\2w\end{pmatrix} &= 2A\begin{pmatrix}v\\w\end{pmatrix} \\
B(2v,2w) &= 2B(v, 2w) = 4B(v, w)
\end{align*}
```

當$`V=W`$而且$`X`$就是原本的 field $`K`$的時候，這樣的 bilinear map 就會稱為 bilinear form

以此類推，對多個向量空間映射到一個向量空間的函數如果對每個變數都是單獨線性的，我們便稱之為多線性變換，又定義域如果又是同一個向量空間的笛卡爾積且對應域也是原本的 field $`K`$，也就是$`A: V^k \rightarrow K`$的話，這個多線性變換就會稱為 multilinear form ，也會稱為一個$`k`$-tensor ，這裡就先把$`k`$稱作精簡版的「階」（order）。終於在這裡看到名字有 tensor 的東西了，雖然不太準確，但下面的說法就比較感受得到張量和數學的關聯了：

> 張量就是將 field $`K`$上的向量空間$`V`$中的多個變數以分別線性的方式映射到$`K`$的函數。

## 為什麼是挑映射到$`K`$的函數？

剛開始學線性代數應該會很常看到 linear operator 的定義是$`T: V\rightarrow V`$，又一開始看到張量的介紹的時候會看到「純量可以是一種張量、向量是張量、$`n\times n`$矩陣也是張量」，又看到 linear operator 給定基底後可以表示為矩陣（而且是方陣），所以看到張量的定義明明是$`T: V^k\rightarrow K`$長得不一樣就會感到疑惑。透過觀察讓純量、向量和矩陣符合張量定義的過程和構造新張量的方法，應該可以解答標題和這個段落產生的疑惑。

### Scalar as tensor

Field $`K`$本身可以作為一個向量空間，對$`a\in K`$我們可以定義$`T_a: K\rightarrow K, x\mapsto ax`$，按照上面的定義，我們好像可以將用$`a`$定義的$`T_a`$視為一個$`1`$-tensor 了？但用同樣的方法我們也可以將$`x\mapsto a x_1 x_2 ... x_k`$這樣的函數當成$`k`$-tensor ，也就是純量 $`a`$ 是沒辦法透過上面的定義 well defined 的，為了~~世界的和平~~張量運算規則的方便性，我們把純量就這樣定義成 $`0`$-tensor 。

### Column vector as tensor

對 over $`K`$的 n 維向量空間$`V`$（好的先當作有限維），取標準基底$`\mathbf{e} = \{e_1, e_2,...,e_n\}`$和一個由 field $`K`$的元素組成的行(column)向量$`v = \begin{bmatrix}a_1\\a_2\\\vdots\\a_n\end{bmatrix}`$。我們可以定義$`T_v: V\rightarrow K`$ 為 $`w\mapsto \begin{bmatrix}w\end{bmatrix}_{\mathbf{e}}^T v,\quad w\in K^n`$，這樣的話按照定義我們就可以說$`T_v`$是一個 $`1`$-tensor 。

### Square matrix as tensor

用上面一段的向量空間$`V`$和標準基底$`\mathbf{e}`$，可以取一個方陣$`A\in M_{n\times n}(K)`$，則對於$`V`$中同樣基底的行向量$`u,v`$可以將$`T_A: V\times V\rightarrow K`$定義為$`T_A(u, v)=u^T Av`$，這樣就能將兩個向量變為實數，所以也符合了$`2`$-tensor 的定義。我們也能從這裡看到把矩陣當作張量來用和當作線性變換來用的用法是有一點不一樣的，算是解答了本節一開始的疑惑。

我們接著就能注意到，把上一段的$`T_A(u,v)`$的$`Av`$算出來變成行向量之後其實也等於上上一段的$`T_{Av}(u)`$，也就是$`k`$-tensor代入其中一個$`V`$中的變數之後會變成$`(k-1)`$-tensor 。這個概念其實就像 functional programming 的 currying：多個變數的函數可以帶入其中一個變數成為另一個單獨的函數，這種概念下的$`T_{Av}`$其實就可以寫成$`T_A(\cdot,v)`$，要產生函數值就把變數帶入其中的點記號。

### Tensors produced by product

取一個$`k`$-tensor $`T_1`$和一個$`l`$-tensor $`T_2`$，因為兩者都是映射到$`K`$的函數，所以可以利用$`K`$上的乘法定義下面新的函數：

```math
T_1\otimes T_2:V^k\times V^l\rightarrow K\\
T_1\otimes T_2(u_1, ...,u_k,v_1,...,v_l) = T_1(u_1,...,u_k)T_2(v_1,...,v_l)
```
因為$`T_1,T_2`$對各個變數是分別線性的，可以很容易驗證$`T_1\otimes T_2`$對各個變數也都是分別線性的，所以我們就這樣構造出了一個$`(k+l)`$-tensor ，並且將這個$`\otimes`$符號的運算稱作 tensor product。

### 阿所以為什麼啊

說了這麽多，「為什麼這樣定義XXX」這類問題的回答通常就是「好用」，但上面的例子不需要實際上理論的應用，就大概展示到了把張量定義為映射到$`K`$的函數有下面這些好處：

1. **$`K`$不依賴基底的選擇**：也就是依照張量定義，對張量輸入多個向量，只要向量一樣，不論張量和向量本身的數值表示法選取什麼基底，產生的純量依然是相同的。
2. **可以將純量、向量、和矩陣都視為張量的表示法**：如果定義張量的方式是映射到$`V`$或$`\mathcal{L}(V)`$的函數，就會讓純量或向量變成特例，而且高階張量的階也會變得不太直覺（例如三維陣列實際上代表二階張量之類的）。
3. **可以用低階張量構造高階張量**：像 2. 一樣，如果定義張量的方式不是映射到$`K`$，因為向量和矩陣要不沒辦法任意做乘法，要不就是通常乘法不可交換，我們就比較不容易用$`K`$的乘法簡單的 well-define 新的高階張量。

接下來要說一件殘忍的事實：「上面對張量的定義其實不完整」，但因為篇幅感覺爆量了又感覺後面不知道怎麼自圓其說，就先發出來，剩下的以後再說。


## References

Linear Algebra 4e, Stephen H. Friedberg

An Introduction to Manifolds, Loring Tu

[Tensor - Wikipedia](https://en.wikipedia.org/wiki/Tensor)

[Currying - Wikipedia](https://en.wikipedia.org/wiki/Currying)


[Bilinear Form - Wikipedia](https://en.wikipedia.org/wiki/Bilinear_form)

[Lorentz Transformation - Wikipedia](https://en.wikipedia.org/wiki/Lorentz_transformation)

[How is a (0,0) rank tensor a number? - Mathematics Stack Exchange](https://math.stackexchange.com/questions/2887219/how-is-a-0-0-rank-tensor-a-number)