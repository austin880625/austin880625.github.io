# 在 shell 上快速架設 HTTP server 的方法：Python, nc, socat
date: 2024/01/21
category: server
excerpt: 架設測試用的 HTTP server 有幾種方法，直接裝標準的 HTTP server 軟體需要寫設定檔，用 Python 或 Golang 直接套框架寫對一些簡單的需求也太慢了。 HTTP 也是標準的網路協定，因此一些設計來在 shell 上使用的網路測試工具就剛好可以用來架簡單的 HTTP server 。這篇文章整理了幾種我自己會使用的方法和情境。
---

在寫網頁應用程式的時候，除了取得網頁本身的 HTTP request 之外，也常有其他會發送 HTTP request 的元件或流程。例如網頁前端會有 javascript 另外發送的 API request ，也有來自其他服務的 webhook 。有時候想快速測試一下這類型的 request 內容就需要事先架好一個 HTTP server ，也要能回傳簡單的回應。

以前架這種 HTTP server 都是用 Python 的 `SimpleHttpServer` 來寫，但這種方法主要是用來顯示目錄下的檔案，如果有要測試 header 或依照 request 回傳不同內容的時候還是要寫一個實際的 server 。寫久了就覺得 unix 上常用的網路工具應該還是有機會達到手寫自訂 response 的目標。但到最近才開始真的自己實驗。總結過後快速架設 HTTP server 主要有下面幾種方法。

## Python 的 `http.server` 

就是上面說的要快速展示當下目錄的 HTML 或圖片的時候用的。

```
python3 -m http.server <port>
```

## netcat

一開始說的發送 API request 的情境在 python 的 `http.server` 上不是請求檔案內容，想要回傳 json 內容的話使用沒有那麼方便。假如熟悉 HTTP 協定的回應結構的話，能夠直接打出純文字在 socket 上傳送資料應該和寫 code 的工作量差不多，因為在 json 回覆裡該設定的 header 和欄位都一樣需要設定。如果是 client 端通常是用 telnet 來達成， server 端的話則是可以用 netcat ，安裝好之後是叫做 `nc` 指令。使用 `nc -l <port>` 就可以開始 listen 在指定的 port 上。

```
nc -l 8000
```

這時候用瀏覽器或 curl 訪問 http://127.0.0.1:8000 就可以在終端機上看到 request 被印出來：

```
austin@fedora:~/Documents/labs$ nc -l 8000
GET / HTTP/1.1
Host: 127.0.0.1:8000
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate, br
Connection: keep-alive
Upgrade-Insecure-Requests: 1
Sec-Fetch-Dest: document
Sec-Fetch-Mode: navigate
Sec-Fetch-Site: none
Sec-Fetch-User: ?1

```

可以直接按照 HTTP response 的格式打上回傳內容：

```
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 21

{"status": "success"}

```

接著就可以看到瀏覽器順利認定連線已經結束（接收的內容長度和 Content-Length 相符）並且顯示我們的回傳內容。

## socat

socat 被視為功能進階的 netcat ，當然 netcat 已經有很多我還沒完全活用的功能了，不過 socat 對我的感覺是操作上比較 high level 一些。使用以下指令就可以開始聽指定的 port ，然後就可以跟上面 netcat 的操作方式一樣直接在 stdin 打上回傳內容。

```
socat TCP-LISTEN:8000,crlf,fork -
```

需要的時候甚至也可以讓 socat 處理 HTTPS 連線，可以看[這篇教學](https://fabianlee.org/2022/10/26/linux-socat-used-as-secure-https-web-server/)。

## 結論

nc 和 socat 都是功能滿多的工具，nc 的主要用途就是用來掃 port 和發送自訂封包， socat 的主要用途是把不同 socket 和 IO 的資料接起來。因為 HTTP 是純文字的協定，所以在 HTTP 伺服器需要回傳 HTML 或多媒體檔案以外的內容就會比較方便，在需要的回傳內容足夠簡單的情況下也不會比直接套框架寫 API 慢太多。

## References

[Coding起來 — Python — 一行指令就能輕鬆建立網頁伺服器 — SimpleHTTPServer套件 — http.server使用教學](https://chwang12341.medium.com/coding%E8%B5%B7%E4%BE%86-python-%E4%B8%80%E8%A1%8C%E6%8C%87%E4%BB%A4%E5%B0%B1%E8%83%BD%E8%BC%95%E9%AC%86%E5%BB%BA%E7%AB%8B%E7%B6%B2%E9%A0%81%E4%BC%BA%E6%9C%8D%E5%99%A8-simplehttpserver%E5%A5%97%E4%BB%B6-http-server%E4%BD%BF%E7%94%A8%E6%95%99%E5%AD%B8-34c30b81c26)

[How to Use Netcat Commands: Examples and Cheat Sheets](https://www.varonis.com/blog/netcat-commands)

[Linux: socat used as secure HTTPS web server](https://fabianlee.org/2022/10/26/linux-socat-used-as-secure-https-web-server/)

