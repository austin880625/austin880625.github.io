# 使用 Thumbor + Nextcloud 架設自己的網頁圖床 (2): Nextcloud 安裝與自己開發 Plugin
date: 2022/07/16
category: server
thumbnail: https://imgcdn.austint.in/-TfQgliVsEl09tzAu7mbg18K-eo=/fit-in/760x560/filters:format(webp)/thumbor-sample/thumbor-nextcloud.png

excerpt: Thumbor 可以透過 file loader 存取 Nextcloud 的檔案。本文介紹 Nextcloud 的安裝並整合 Thumbor 使其可以快速取得 Thumbor url 的過程

---
架設完 Thumbor 伺服器之後，把網站圖片放在伺服器的固定位置就能使用 file loader 滿足圖片伺服器需求。但在第一篇文章也提到，傳輸圖片到 server 需要使用 scp 類型的工具，如果是在手機上拍照，把圖片上傳的流程會是把手機照片傳輸到電腦 -> 用電腦 scp 檔案到伺服器 -> 手動用 script 產生 Thumbor 圖片 url ，其實不是很方便。其實會希望有手機或電腦有客戶端可以直接上傳檔案的雲端硬碟，然後直接在界面上拿到圖片的 url 。因為本來有在用 Nextcloud ，所以來試著在 Nextcloud 上實作產生 url 的機制。

## Nextcloud 安裝

雖然本來就有裝好的 Nextcloud ，但為了文章完整度還是重新架一個，順便拿來當 Plugin 開發的測試環境。

安裝 Nextcloud 預設環境需要一個能夠執行 PHP 的網頁伺服器和資料庫，官方文件有不同網頁伺服器和資料庫的設定方法，我自己習慣的是 Nginx+MariaDB+phpFPM 的組合，目前使用的 Linux 發行版是 Alpine Linux 。安裝過程如下：

### 套件

```
# 改設定檔的工具
apk add vim
# server 軟體和有用的 client
apk add nginx mariadb mariadb-client php8-fpm
# php 所需要的 extension
apk add php8-ctype php8-curl php8-dom php8-gd php8-xml php8-xmlreader php8-xmlwriter php8-simplexml php8-mbstring php8-openssl php8-posix php8-session php8-zip php8-pdo_mysql php8-fileinfo php8-bz2 php8-intl
rc-service nginx start
rc-service php-fpm8 start
```

### 資料庫初始設定

```
# 初始化資料庫
/etc/init.d/mariadb setup
rc-service mariadb start
mysql_secure_installation
# 接著照著提示一個一個選是否需要

# 建立資料庫與使用者
mysql -u root -h localhost -p
CREATE USER 'nc' IDENTIFIED BY 'password';
CREATE DATABASE nextcloud_01;
use nextcloud_01
GRANT ALL PRIVILEGES ON nextcloud_01.* TO 'nc';
```

### 設定檔

建立 php-fpm 專用的 user

```
adduser php -G www-data
```

php-fpm 的設定

`/etc/php8/php-fpm.d/www.conf`

```
; 執行使用者
; Unix user/group of processes
; Note: The user is mandatory. If the group is not set, the default user's group
;       will be used.
user = php
group = www-data

; 這是預設值，喜歡的話可以改成 unix socket
listen = 127.0.0.1:9000
```

nginx 放一個 virtual host ，這段設定是修改自[官網](https://docs.nextcloud.com/server/stable/admin_manual/installation/nginx.html)的，我們主要先設定成 80 port 就可以連線，底下有很多跟 Nextcloud 實作有關的 rewrite ，自己寫實在不太好寫。

`/etc/nginx/http.d/nextcloud.conf`

```
upstream php-handler {
    server 127.0.0.1:9000;
    #server unix:/var/run/php/php7.4-fpm.sock;
}

# Set the `immutable` cache control options only for assets with a cache busting `v` argument
map $arg_v $asset_immutable {
    "" "";
    default "immutable";
}

server {
    #listen 443      ssl http2;
    #listen [::]:443 ssl http2;
    listen 80;
    listen [::]:80;
    # 改成會用來連線的主機名稱，例如 localhost, blog.austint.in 等
    server_name 10.1.2.103;

    # Path to the root of your installation
    root /var/www/nextcloud;

    # Use Mozilla's guidelines for SSL/TLS settings
    # https://mozilla.github.io/server-side-tls/ssl-config-generator/
    #ssl_certificate     /etc/ssl/nginx/cloud.example.com.crt;
    #ssl_certificate_key /etc/ssl/nginx/cloud.example.com.key;

    # Prevent nginx HTTP Server Detection
    server_tokens off;

    # HSTS settings
    # WARNING: Only add the preload option once you read about
    # the consequences in https://hstspreload.org/. This option
    # will add the domain to a hardcoded list that is shipped
    # in all major browsers and getting removed from this list
    # could take several months.
    #add_header Strict-Transport-Security "max-age=15768000; includeSubDomains; preload;" always;

    # set max upload size and increase upload timeout:
    client_max_body_size 512M;
    client_body_timeout 300s;
    fastcgi_buffers 64 4K;

    # Enable gzip but do not remove ETag headers
    gzip on;
    gzip_vary on;
    gzip_comp_level 4;
    gzip_min_length 256;
    gzip_proxied expired no-cache no-store private no_last_modified no_etag auth;
    gzip_types application/atom+xml application/javascript application/json application/ld+json application/manifest+json application/rss+xml application/vnd.geo+json application/vnd.ms-fontobject application/wasm application/x-font-ttf application/x-web-app-manifest+json application/xhtml+xml application/xml font/opentype image/bmp image/svg+xml image/x-icon text/cache-manifest text/css text/plain text/vcard text/vnd.rim.location.xloc text/vtt text/x-component text/x-cross-domain-policy;

    # Pagespeed is not supported by Nextcloud, so if your server is built
    # with the `ngx_pagespeed` module, uncomment this line to disable it.
    #pagespeed off;

    # HTTP response headers borrowed from Nextcloud `.htaccess`
    add_header Referrer-Policy                      "no-referrer"   always;
    add_header X-Content-Type-Options               "nosniff"       always;
    add_header X-Download-Options                   "noopen"        always;
    add_header X-Frame-Options                      "SAMEORIGIN"    always;
    add_header X-Permitted-Cross-Domain-Policies    "none"          always;
    add_header X-Robots-Tag                         "none"          always;
    add_header X-XSS-Protection                     "1; mode=block" always;

    # Remove X-Powered-By, which is an information leak
    fastcgi_hide_header X-Powered-By;

    # Specify how to handle directories -- specifying `/index.php$request_uri`
    # here as the fallback means that Nginx always exhibits the desired behaviour
    # when a client requests a path that corresponds to a directory that exists
    # on the server. In particular, if that directory contains an index.php file,
    # that file is correctly served; if it doesn't, then the request is passed to
    # the front-end controller. This consistent behaviour means that we don't need
    # to specify custom rules for certain paths (e.g. images and other assets,
    # `/updater`, `/ocm-provider`, `/ocs-provider`), and thus
    # `try_files $uri $uri/ /index.php$request_uri`
    # always provides the desired behaviour.
    index index.php index.html /index.php$request_uri;

    # Rule borrowed from `.htaccess` to handle Microsoft DAV clients
    location = / {
        if ( $http_user_agent ~ ^DavClnt ) {
            return 302 /remote.php/webdav/$is_args$args;
        }
    }

    location = /robots.txt {
        allow all;
        log_not_found off;
        access_log off;
    }

    # Make a regex exception for `/.well-known` so that clients can still
    # access it despite the existence of the regex rule
    # `location ~ /(\.|autotest|...)` which would otherwise handle requests
    # for `/.well-known`.
    location ^~ /.well-known {
        # The rules in this block are an adaptation of the rules
        # in `.htaccess` that concern `/.well-known`.

        location = /.well-known/carddav { return 301 /remote.php/dav/; }
        location = /.well-known/caldav  { return 301 /remote.php/dav/; }

        location /.well-known/acme-challenge    { try_files $uri $uri/ =404; }
        location /.well-known/pki-validation    { try_files $uri $uri/ =404; }

        # Let Nextcloud's API for `/.well-known` URIs handle all other
        # requests by passing them to the front-end controller.
        return 301 /index.php$request_uri;
    }

    # Rules borrowed from `.htaccess` to hide certain paths from clients
    location ~ ^/(?:build|tests|config|lib|3rdparty|templates|data)(?:$|/)  { return 404; }
    location ~ ^/(?:\.|autotest|occ|issue|indie|db_|console)                { return 404; }

    # Ensure this block, which passes PHP files to the PHP process, is above the blocks
    # which handle static assets (as seen below). If this block is not declared first,
    # then Nginx will encounter an infinite rewriting loop when it prepends `/index.php`
    # to the URI, resulting in a HTTP 500 error response.
    location ~ \.php(?:$|/) {
        # Required for legacy support
        rewrite ^/(?!index|remote|public|cron|core\/ajax\/update|status|ocs\/v[12]|updater\/.+|oc[ms]-provider\/.+|.+\/richdocumentscode\/proxy) /index.php$request_uri;

        fastcgi_split_path_info ^(.+?\.php)(/.*)$;
        set $path_info $fastcgi_path_info;

        try_files $fastcgi_script_name =404;

        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param PATH_INFO $path_info;
        fastcgi_param HTTPS on;

        fastcgi_param modHeadersAvailable true;         # Avoid sending the security headers twice
        fastcgi_param front_controller_active true;     # Enable pretty urls
        fastcgi_pass php-handler;

        fastcgi_intercept_errors on;
        fastcgi_request_buffering off;

        fastcgi_max_temp_file_size 0;
    }

    location ~ \.(?:css|js|svg|gif|png|jpg|ico|wasm|tflite|map)$ {
        try_files $uri /index.php$request_uri;
        add_header Cache-Control "public, max-age=15778463, $asset_immutable";
        access_log off;     # Optional: Don't log access to assets

        location ~ \.wasm$ {
            default_type application/wasm;
        }
    }

    location ~ \.woff2?$ {
        try_files $uri /index.php$request_uri;
        expires 7d;         # Cache-Control policy borrowed from `.htaccess`
        access_log off;     # Optional: Don't log access to assets
    }

    # Rule borrowed from `.htaccess`
    location /remote {
        return 301 /remote.php$request_uri;
    }

    location / {
        try_files $uri $uri/ /index.php$request_uri;
    }
}
```

重新載入服務

```
rc-service php-fpm8 reload
rc-service nginx reload
```

### Nextcloud 主程式

```
wget https://download.nextcloud.com/server/releases/latest.zip
unzip -d /var/www/ latest.zip
chown -R php:www-data /var/www/nextcloud
```

接著打開瀏覽器輸入 http://主機名稱 (如 http://localhost) 應該就能看到安裝畫面，填入需要的資訊後按安裝。

![Nextcloud 主程式安裝畫面](https://imgcdn.austint.in/hRyg-u_FlvBqb9ACli1mfY4bnvQ=/1000x0/thumbor-sample/nc-install.png)

如果是在 http server 上安裝的話，安裝完成的重新導向會導向 https 的網址，可以在 `/var/www/nextcloud/config/config.php` 修改增加這些設定：

```
// 把 https 改成 http
  'overwrite.cli.url' => 'http://10.1.2.103',
  'overwriteprotocol' => 'http',
```

接著就能回到瀏覽器用 http 的網址重新連線。安裝精靈會提示是否要安裝一些 Nextcloud App ，看喜好決定後安裝完成就能進到主畫面了。

![Nextcloud 24.0.2.1 主畫面](https://imgcdn.austint.in/P6XEqfswA-MHWoghDvD035FzK34=/1000x0/thumbor-sample/nc-dashboard.png)

## Thumbor 設定

接著要設定 Thumbor 可以存取 Nextcloud 中的檔案，其實很簡單，只要用 file loader 並把 `thumbor.conf` 中的 `FILE_LOADER_ROOT_PATH` 改成 Nextcloud 的使用者資料目錄，接著就能用相對位置當作 url 存取上傳到 Nextcloud 的圖片了。

```
# 只有一個使用者的話也可以指定成使用者目錄底下的特定位置
FILE_LOADER_ROOT_PATH = '/var/www/nextcloud/data/austin/files/
```

如果 Thumbor 和 Nextcloud 架在不同機器的話，我想到的做法是用 WebDAV 的 url 搭配 Nextcloud 的 app password 存取，不過需要在 http request 中加入驗證 header ，可能需要改 http loader 的實作。

## Nextcloud App 開發

這段應該才是寫這篇文章真正的動機，希望在 Nextcloud 上傳圖片的當下就能在頁面上得到 Thumbor 附帶 HMAC 的網址，我的想像是在檔案的下拉選單有一個 Get thumbor url 的選項，按下去之後出現圖片的 unsafe url 以及 HMAC url ，修改 unsafe url 上的濾鏡參數之後 HMAC url 跟著改變並且可以一鍵複製。

Nextcloud 提供了自訂 App 的開發 API ，所以想達成的效果應該是可行的，只是說明文件有點過時（加上不太有用和錯亂）。過去 Nextcloud 的 javascript API 是在全域變數裡的，似乎是從 OwnCloud 帶進來的，較新版的 Nextcloud 則開始使用 webpack 打包 javascript 套件，官方文件上也推薦使用新版套件管理的開發流程。但也只有推薦，幾乎沒有文件、沒有範例、沒有 code 。 ㄛ對，有些 API 看起來就是舊版的文件被刪了，新版的 code 還沒用到新的 API 。

於是整個開發過程就是看一些原始碼、從瀏覽器 console 倒一些變數猜函式怎麼用、從 Nextcloud 原始碼塞 `echo` 看哪裡新舊版載入行為不一樣（裝 XDebug 對我還是有點麻煩），看說明文件花的時間反而最少 orz。整個開發體驗和 Wordpress plugin 差有點多。

總之花了一個禮拜先做出了一個能用的版本，打包好的 zip 檔案在解壓縮之後就能放在 Nextcloud 的 `apps` 目錄（通常在 `/var/www/nextcloud/apps` 下），在 app 管理頁面就能看到 Thumbor Url 的啟用選項。

![Nextcloud 安裝完 Thumbor Url apps 後的啟用選項](https://imgcdn.austint.in/fXSHaDgF5jZkKRU_I7PTabN1x_E=/800x0/thumbor-sample/thumborurl-enable.png)

啟用後就能在個人設定的分享頁面中看到 Thumbor Url 需要的設定。

![Nextcloud 中 Thumbor Url 設定畫面](https://imgcdn.austint.in/eQwKjUFKgKyKyQltplyKd5zvCXU=/800x0/thumbor-sample/thumborurl-settings.png)

三個設定的意義如下：

- Thumbor server base url ： Thumbor 伺服器位置
- Thumbor server base dir ： Thumbor 的 **file loader 圖片根目錄**相對 Nextcloud 中**使用者根目錄**的位置。例如使用者名稱是 `austin` ，在 Nextcloud 把要分享的圖片放在 `img/for-thumbor` 目錄下，這個時候 base dir 就會設定為 `/img/for-thumbor` 而 Thumbor 的 `FILE_LOADER_ROOT_PATH` 設定就會像 `/var/www/nextcloud/data/austin/files/img/for-thumbor`
- Thumbor server security key ： Thumbor 用來對 url 做 HMAC 簽章的 security key

設定完成後在 Nextcloud 檔案瀏覽畫面中圖片的檔案下拉選單就會出現 Get Thumbor Url 的選項。其實只有在 base dir 底下的圖片這個選項才是有作用的，只是我的 app 沒有特別過濾所以到處都會出現。

![檔案下拉選單新增的 Get Thumbor Url 選項](https://imgcdn.austint.in/DpSLIfYdhSCull-Cpv0AXOKhzXw=/800x0/thumbor-sample/thumborurl-menu.png)

點下去之後會出現輸入圖片處理選項的彈出視窗，可以在這一步輸入 Thumbor url 格式的縮放、濾鏡、裁切選項。

![輸入 Thumbor 圖片處理選項](https://imgcdn.austint.in/1Uaq5CDZmVm7KB1gpQaGjPMLJZo=/800x0/thumbor-sample/thumborurl-enter-filter.png)

最後就會獲得有 HMAC hash 的圖片 url ，Nextcloud 有 https 的話也會直接複製進剪貼簿，不需要有本地 script 才能得到 url hash 了。

![帶有 HMAC hash 的圖片 url](https://imgcdn.austint.in/p7WrYlm_FmH2MKJHJWw2LIbjZQs=/800x0/thumbor-sample/thumborurl-signed-url.png)

## Downloads

最後這是寫出來的 Nextcloud App 的 repository ，應該是沒有要把他推上 Nextcloud AppStore 的計劃，因為文件實在太難讀，日後維護感覺會很痛苦。不過有什麼簡單的建議應該也是可以再討論。

[https://github.com/austin880625/nextcloud-thumbor-url](https://github.com/austin880625/nextcloud-thumbor-url)

## References

[https://github.com/nextcloud/files_rightclick](https://github.com/nextcloud/files_rightclick)

[https://docs.nextcloud.com/server/stable/admin_manual/installation/source_installation.html](https://docs.nextcloud.com/server/stable/admin_manual/installation/source_installation.html)

[https://download.bitgrid.net/nextcloud/jsdocs/core_js_oc-dialogs.js.html](https://download.bitgrid.net/nextcloud/jsdocs/core_js_oc-dialogs.js.html)

[https://docs.nextcloud.com/server/20/developer_manual/prologue/index.html](https://docs.nextcloud.com/server/20/developer_manual/prologue/index.html)