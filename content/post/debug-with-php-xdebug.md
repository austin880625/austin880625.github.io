# 使用 Xdebug 偵錯伺服器上的 PHP 程式
category: web-dev
date: 2022/08/28

excerpt: 有天發現自己的 Nextcloud 界面沒辦法登入了，伺服器的 log 內容又太簡潔找不到原因，除了用 echo 大法二分尋找可能的錯誤點或變數內容之外，使用 Xdebug 可以用來對本地或伺服器上的 PHP 程式進行單步執行的偵錯

---
有天發現自己的 Nextcloud 界面沒辦法登入了，帳號密碼不管怎麼輸入都是直接跳回登入頁面的迴圈。在 Nextcloud, php-fpm 到 nginx 上的 log 都沒有什麼有用的資訊，只有顯示未登入。從 log 上找到對應錯誤訊息的程式碼，都是讀取 session 中的 user ，沒辦法看出驗證帳號密碼和寫入 session 的過程出了什麼問題。

Nextcloud 的程式碼很多又很亂，沒辦法很快看出帳號密碼驗證的程式碼從哪裡執行，過去我會用在小型 PHP script 的 echo 大法印出變數猜測放 echo 的地方是錯誤發生前還是發生後。因為原始程式常常邏輯判斷完就跟著印出內容，所以還算是容易除錯。

但現代 PHP 應用程式常常採用 MVC 或 REST + 前端 架構，很多處理邏輯都是在 header 回傳前完成的，使用 echo 大法除了很難把內容印在固定的地方之外還會額外製造一堆 header already sent 的錯誤。這時候就會希望有可以單步執行的除錯程式釐清真正被執行到的程式碼和錯誤關鍵的發生點。這樣的功能就可以透過 Xdebug 來達成。

## 安裝

在主流 Linux 發行版上安裝 Xdebug 現在算是相對簡單，只要一行指令就能完成，在以前還需要處理 pecl 安裝的一些麻煩，以我使用的 Alpine Linux 來說的話變成這樣：

```
sudo apk add php7-pecl-xdebug
# 或是
# sudo apk add php8-pecl-xdebug
```

其他的發行版可以參考官網的安裝流程，換個套件管理器而已。

安裝後要去修改 PHP 的設定檔載入 Xdebug 的 extension ，如果是使用套件管理器安裝的話，除了 `php.ini` 檔案以外應該可以額外找到 PHP 設定檔的目錄下有給 Xdebug 使用的檔案（也可以自己建立），例如 `/etc/php7/conf.d/50_xdebug.ini` 。在這個檔案加入以下的內容：

```
; 在 Alpine Linux 上 xdebug.so 的路徑是在 /usr/lib/php7/modules/xdebug.so ，如果有沒辦法順利載入的狀況可能要看看 so 檔案是不是在正確的位置。
zend_extension=xdebug.so
```

接著重啟 web server 或 php-fpm 後就可以驗證安裝，在 PHP 網頁的目錄建立一個測試網頁，內容如下：

```
<?php
xdebug_info();
?>
```

瀏覽伺服器上這個網頁應該就會看到 Xdebug 的版本和設定資訊。

![Xdebug 版本資訊頁面](https://imgcdn.austint.in/XFUnurUccg7ZdtAF-0tYu3CNSBE=/fit-in/760x560/filters:format(webp)/debug-with-php-xdebug/xdebug-info.png)

## 設定除錯模式和觸發條件

以我想要進行單步執行的情境的話，就要在 `50_xdebug.ini` 檔案繼續加入以下的內容：

```
xdebug.mode=debug
xdebug.start_with_request=yes
```

`xdebug.mode` 指的是 Xdebug 除錯的模式，除了代表單步執行的 `debug` 以外，還有以下的模式

- `off`: 關閉 Xdebug
- `develop`: 在 PHP 程式中開啟資訊較詳細的 `var_dump` 以及錯誤發生時的 stack trace
- `coverage`: 計算程式執行時控制流程的覆蓋率，通常搭配 phpunit 使用
- `gcstats`: 計算 garbage collection 的使用資訊
- `profile`: 計算執行效能的數據
- `trace`: 紀錄 PHP 程式執行過程中函式呼叫的所有參數

多個模式也可以用 `xdebug.mode=develop,debug` 這樣的形式同時啟用。

`xdebug.start_with_request` 則是決定要在什麼時候觸發 debug session ，這個值設定為 `yes` 就會在每個 request 都開始在 PHP 執行的時候執行 `xdebug.mode` 指定的功能。如果設定成 `trigger` ，會在環境變數或 GET/POST parameters 有 `XDEBUG_TRIGGER` 這個 key 的時候才會觸發。 

## 設定 IDE 和偵錯主機

Xdebug 的觸發機制是讓執行 PHP 的主機對進行 debug 的主機建立連線，所以如果執行 PHP 程式的機器在遠端的話， debug 主機就需要有對外接收連線的 port ，也需要有在遠端主機執行的程式碼。這個接收連線的程式就是 Xdebug 官網上說的 debug client （在連線上其實是 server），通常是 IDE 。 Xdebug 官網也有提供一個簡易版的 command line debug client ，但他的指令實在是太長了，所以我後來還是在 VSCode 上設定。

### 偵錯主機設定

我們繼續修改遠端主機的 `50_xdebug.ini` 檔案內容，加入以下內容設定 debug client 的主機位址和 port ：

```
xdebug.client_host=192.168.1.107
; port 需要和 IDE 中設定的一致
xdebug.client_port=9003
```

修改完成記得再重新啟動一次 web server 或 php-fpm

### IDE 設定

到要進行除錯的開發機。在 VSCode 上使用 Xdebug 需要安裝 `PHP Debug` 這個 extension ，接著需要打開要進行 debug 的程式碼目錄（和遠端主機執行的要一樣，不一樣的話也是可以執行，只是斷點上的 code 不是實際在執行的 code 而已）。

![VSCode 上的 PHP Debug extension ，認明藍勾勾標章](https://imgcdn.austint.in/lQbB5NgHx-AtkgGja9yCB4WEDgE=/fit-in/760x560/filters:format(webp)/debug-with-php-xdebug/vscode-php-debug.png)

然後可以在左側 `Run and Debug` 的分頁底下按 `create a launch.json file` 建立 VSCode 的 debug 選項設定檔， `Listen for Xdebug` 的選項就是用來接收遠端 Xdebug 連線的，可以改成下面的樣子：

```
{
    "name": "Listen for Xdebug",
    "type": "php",
    "request": "launch",
    "port": 9003,
    "stopOnEntry": true,
    "pathMappings": {
        "/var/www/nextcloud": "${workspaceFolder}"
    }
},
```

以遠端 debug 來說， `pathMappings` 大概是最重要的，作用就是把遠端主機上 PHP 程式碼所在的目錄對應到本地的目錄，在這裡就是要對應到 `${workspaceFolder}` 上。

`stopOnEntry` ，可以在不知道整個網頁程式的進入點在哪裡的時候（比如被進行很複雜的 path rewrite）設成 `true`，就會在最開始執行的 PHP script 就觸發中斷點。

## 開始除錯

都設定完成之後就可以開始除錯了，在 VSCode 上的 `Run and Debug` 分頁啟動 `Listen for Xdebug` 選項，接著用瀏覽器或 Postman 類的工具對遠端主機發出 HTTP request ，沒有發生意外的話，就會看到程式被停在最開始執行的位置上，這時候就可以開始加其他想要的斷點或開始單步執行和查看相關的變數。

![開始 debug 的畫面](https://imgcdn.austint.in/_OFXvyDwc5RmEfc2m8_jN-rYxUo=/fit-in/760x560/filters:format(webp)/debug-with-php-xdebug/vscode-xdebug-running.png)

最後有找到實際發生錯誤的原因了，是因為 PHP 的 `session_save_path` 目錄沒有建立好，沒辦法建立 session 導致 CSRF 怎麼驗證都會失敗，應該是某個我不記得的日子動到 PHP config 造成的。

## References

[https://xdebug.org/docs/](https://xdebug.org/docs/)

[https://marketplace.visualstudio.com/items?itemName=xdebug.php-debug](https://marketplace.visualstudio.com/items?itemName=xdebug.php-debug)