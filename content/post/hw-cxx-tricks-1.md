title: 寫作業用到的一些好玩的 C++ 語法 (1)
date: 2020/10/16
path: 2020/10/16
---

寫作業剛好感覺 spec 很適合用來練習一些 C++ 專屬的寫法，主要進行的是 Tensor 的運算，所以用到了一些記憶體管理和 template 的功能。因為語法看起來都滿容易忘記的，所以把他們的意思和語法記下來。先放一些，這個主題之後應該可以繼續放其他的內容。

## Lambda Basics

基本的 lambda function 會長這樣：

```
auto f = [](int x) { return x; };
```

前面方括號的意思是 capture ，可以用來「抓」在目前 scope 裡的 symbol 。預設的 capture 是by value ，也就是會 copy ，在 symbol 前面加 `&` 就會是 capture by reference 。除了顯式的指定要 capture 的符號外，也可以使用 default capture ，會自動 capture 所有「沒有 capture 但有在 function body 中使用」的 symbol 。 default capture 的語法長這樣：

```
void f(int y) {
    int x = 10;
    auto g = [=]() { return x+y; } // capture by value
    auto h = [&]() { return x++; } // capture by reference
}
```

## Lambda for Function Composition

在 template 中拿到 function 的參數 type 的方法沒有那麼好想，所以要寫一個函數的合成的 callable type 也不太容易，要偷懶就用 lambda 讓他全部自己推。

```
// F, G 是 callable 的 type
template<typename F, typename G>
auto compose(F&& fn, G&& gn) {
    return [=](auto&& x) {
        return fn(gn(x));
    };  
}

int main() {
    auto f = [](int x) { return x+1; };
    auto g = [](int x) { return x+2; };
    std::cout << compose(f, g)(10) << std::endl;
}
```

## `using` aliases

typedef 只能對 instantiated type 做定義，我們有時候希望這個定義能夠幫我們對 template 傳遞需要的 template 參數，這時候可以對 `using` 關鍵字使用 template 。

```
template<class T>
using Point = tuple<T, T, T>;

int main() {
    Point<float> p;
    return 0;
}
```

## Templates Parameter Pack

C++ template 的參數可以是不定長度的，在參數列表中會在最後一個參數以 `...` 表示，因為這些參數的使用都是在 compile time 就完成的，所以不會有像 va_list 那樣可以在執行時期使用的資料結構，也因此把參數 unpack 過後使用他的方法要不就是把它原封不動傳給其他人，要不就是用 template 寫遞迴把參數一個一個拿出來。底下是一個使用遞迴定義多維陣列 `Tensor` 的例子：

```
// using 本身不能遞迴，所以用 struct 遞迴定出每一層的 type

template<typename T, int r, int... Args>
struct Tensor_ {
    // 拿出第一個參數，剩下用 Args... 展開往下傳
    // 使用 typename 是因為 Tensor_<T, Args...> 是 non-instantiated type ， compiler 還不知道成員 ::t 是什麼
    using t = std::array<typename Tensor_<T, Args...>::t, r>;
};

// Base case
template<typename T, int r>
struct Tensor_<T, r> {
    using t = std::array<T, r>;
};

template<typename T, int r, int... Args>
using Tensor = typename Tensor_<T, r, Args...>::t;

// 使用
Tensor<3, 4, 5> T;
```

## References

[Do c++11 lambdas capture variables they don't use?](https://stackoverflow.com/questions/6181464/do-c11-lambdas-capture-variables-they-dont-use)

[Is there any difference betwen [=] and [&] in lambda functions?](https://stackoverflow.com/questions/21105169/is-there-any-difference-betwen-and-in-lambda-functions)

[Generic Lambdas and the compose Function](https://yongweiwu.wordpress.com/2015/01/03/generic-lambdas-and-the-compose-function/)

[C++: Why is the recursive templated alias forbidden?](https://stackoverflow.com/questions/46595520/c-why-is-the-recursive-templated-alias-forbidden)