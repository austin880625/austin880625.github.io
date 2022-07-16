# 使用 Thumbor + Nextcloud 架設自己的網頁圖床 (1): Thumbor 伺服器安裝
date: 2022/07/11
category: server
thumbnail: https://img.austint.in/YjnRls77eA_l7IgeZMum1B0eSpg=/thumbor-sample/thumbor-nextcloud.png

excerpt: 使用 GitHub Page 寫部落格開始有加圖片的需求，可以架設 Thumbor 作為自動裁切縮放以及快取圖片的服務。本文介紹 Thumbor 服務的安裝以及基本的安全性設定

---
原本部落格的文章只有文章和 code ，所以東西全部放在 GitHub Page 上輕鬆自在，最近想寫生活廢文開始有加圖片的需求，感覺到圖片和相片直接放 GitHub Page 很快就會讓 repository 接近 1GB 的容量上限，而且也會拖慢 git 操作的速度。

自己是有可以放圖片的空間，直接架一個 nginx 提供靜態檔案是可行的，但會有三個問題。第一個是照片或圖片原檔通常都很大，直接在網頁使用會降低載入速度和花費太多網路流量，通常需要進行壓縮或縮放，手動做也不太方便。第二個是常常需要對圖片做簡單的旋轉或裁切，要自己開軟體是一回事，而不管在手機或電腦上如果要保存原始檔案都還需要做額外的管理。第三個是上傳檔案需要用 scp 類的工具，從手機上要把照片上傳也沒有那麼方便。

而 Thumbor 是一個開源圖片處理伺服器軟體，預設支援從伺服器的檔案系統和透過 HTTP(S) 獲取圖片，也可以使用社群或自己開發的 loader 從其他來源抓取圖片。使用者只要透過 url 指定圖片的尺寸、裁切範圍及套用的濾鏡就能讓 Thumbor 回傳需要的圖片， Thumbor 也會自己維護處理過的圖片快取，在網頁上的圖片只要是固定的就不會有太多次重複處理。

## 安裝 Thumbor

安裝 Thumbor 需要有 Python 3.7 以上的版本，依照 Linux 發行版有幾種不同的安裝方式，如果你是使用 Ubuntu/Debian 的話官方有提供套件的 PPA 可以用以下指令安裝：

```
sudo add-apt-repository ppa:thumbor/ppa
sudo aptitude update
sudo aptitude install thumbor
```

這個方式安裝的設定檔會自動產生，只要再到 `/etc/default/thumbor` 檔案下把 `enabled` 的值改為 `1` 接著就能使用 `service thumbor start force=1` 指令啟動。日後要修改設定的話可以再修改 `/etc/thumbor.conf` 檔案的內容。

其他 Linux 發行版可以用 `pip install` 安裝。我是使用檔案系統 loader ，在系統中新增了另一個專用的 unix user 並把圖片目錄對這個使用者的群組的權限設定為只讀（755）。不過我在 Alpine linux 上嘗試直接安裝完的時候永遠有一些 extension 沒辦法被 import ，在那個目錄只看到 `.c` 檔，表示那些檔案沒有被編譯到，也許是套件的自動編譯 config 寫錯了，所以使用了下載原始碼手動編譯的方式。

```
# Pillow 編譯的 dependency ，只有安裝時會用到
apk add --virtual  build-deps gcc python3-dev musl-dev
apk add gcc python3-dev jpeg-dev zlib-dev
apk add curl-dev
pip3 install pycurl
wget https://github.com/thumbor/thumbor/archive/refs/tags/7.0.10.zip
unzip 7.0.10.zip
cd thumbor-7.0.10
# 我也不知道為什麼這樣就能安裝成功
python3 setup.py install --user
# 安裝後就可以刪除編譯 dependency
apk del build-deps
```

安裝完畢後 Thumbor 的執行檔會在 `~/.local/bin/thumbor` ，設定 `.local/bin` 的環境變數後就能使用 Thumbor 相關的指令，但啟動之前要先有設定檔，先用以下的指令產生預設的設定檔後再啟動：

```
thumbor-config > thumbor.conf
thumbor -c thumbor.conf
```

也可以安裝 supervisor 這類執行檔管理工具使用像下面的設定檔，之後就能用 `supervisorctl start thumbor` 的指令啟動 Thumbor server :

```
[program:thumbor]
command=/home/thumbor/.local/bin/thumbor -c /home/thumbor/thumbor.conf
```

啟動後就能透過 `http://localhost:8888` 存取 Thumbor 伺服器的功能。

## 設定 Loader

Loader 是 Thumbor 用來抓取圖片的界面，全新安裝的 Thumbor 內建兩種 Loader: file 和 HTTP ，其他是 HTTPS 或是 HTTP loader 加上 file loader 的 fallback ，假如是 file loader 的話，在 thumbor.conf 裡面修改以下幾項設定：

```
LOADER = 'thumbor.loaders.file_loader'
FILE_LOADER_ROOT_PATH = '/path/to/圖片根目錄'
```

HTTP loader 的話，可以改的設定滿多的，重要的就是改這一個，其他的應該需要用到的都會自己知道是什麼意思。

```
LOADER = 'thumbor.loaders.http_loader'
```

## 圖片 url 格式

一個存取 Thumbor 圖片的 url 格式會像這樣：

```
http://localhost:8888/unsafe/400x300/thumbor-sample/usb.jpg
```

得到的圖片：

![基本 Thumbor url 回傳的圖片](https://img.austint.in/KSlIxb9kb8HvQFj1DGSL9zT8BhY=/400x300/thumbor-sample/usb.jpg)

url 中的 `400x300` 就是寬x高的裁切大小， Thumbor 會自己取圖片的中間區域，如果，如果在之前加上 `fit-in` 就變成縮放到指定大小，最後的 `thumbor-sample/usb.jpg` 則是圖片的路徑，我是使用 file loader 所以是相對於設定檔中圖片根目錄的圖片位置，假如是 http loader 的話就是 url encoded 過的圖片網址，像是 `https%3A%2F%2Fgithub.com%2Fthumbor%2Fthumbor%2Fraw%2Fmaster%2Fexample.jpg`。也可以加上手動指定的裁切範圍和加上一些其他濾鏡：

```
http://localhost:8888/unsafe/50x10:2000x3000/fit-in/800x600/filters:rotate(-90):grayscale()/thumbor-sample/usb.jpg
```

![加上濾鏡](https://img.austint.in/riTn97y4CGGky5KqMm_1RDMByFQ=/50x10:2000x3000/fit-in/800x600/filters:rotate(-90):grayscale()/thumbor-sample/usb.jpg)

還可以加上很多如翻轉、背景填色等參數，更詳細的 url 格式可以參考[官方文件說明](https://thumbor.readthedocs.io/en/latest/usage.html)。

## 設定 Security Url

用 url 指定輸出格式的方式很方便，但因為 url 所有人都能存取，顯然會有安全性問題，攻擊者只要指定大量不同的圖片尺寸就能夠消耗伺服器的計算資源。

對於這點目前 Thumbor 使用 HMAC 來驗證圖片的存取，將需求的 url 以設定中的 secret key 做 HMAC 的 hash ，使用者發出 request 時要在 url 的第一段加上這段 hash Thumbor 才會做處理。也就是只有擁有 secret key 的人才能產生可供所有人存取的 Thumbor url 。

Secret key 的設定在 thumbor config 的 `SECURITY_KEY` 中，可以是任意的隨機字串。要強制使用 security url 的話就把 `ALLOW_UNSAFE_URL` 改成 `False` ，從此要存取圖片就要將 url 中的 unsafe 換成那個 url 使用 secret key 的 hash ，如下面 url 中的 `KSlIxb9kb8HvQFj1DGSL9zT8BhY=`：

```
https://img.austint.in/KSlIxb9kb8HvQFj1DGSL9zT8BhY=/400x300/thumbor-sample/usb.jpg
```

那要用什麼方式獲得 url 的 hash 呢？ Thumbor 安裝的時候有內建 `thumbor-url` 指令，把 secret key 存在文字檔內就可以用來產生 url

```
# 注意相對路徑的開頭不包含斜線！
thumbor-url -l key.txt 'thumbor-sample/usb.jpg'
```

在其他不想為了產生 url 裝 thumbor 的地方，可以安裝給各個程式語言使用的 library ，在 python 中可以安裝 `libthumbor` 套件，然後就可以寫像下面的 script ：

```
#!/usr/bin/python3
import sys
from libthumbor import CryptoURL

arg_url = sys.argv[1]
crypto = CryptoURL(key="XXXXXX")
url = crypto.generate(image_url=arg_url)
print(url)
```
```
# 使用
> script.py '50x10:2000x3000/fit-in/800x600/filters:rotate(-90):grayscale()/thumbor-sample/usb.jpg'
/riTn97y4CGGky5KqMm_1RDMByFQ=/50x10:2000x3000/fit-in/800x600/filters:rotate(-90):grayscale()/thumbor-sample/usb.jpg
```

## References

[https://stackoverflow.com/questions/57787424/django-docker-python-unable-to-install-pillow-on-python-alpine](https://stackoverflow.com/questions/57787424/django-docker-python-unable-to-install-pillow-on-python-alpine)

[https://web.dev/use-thumbor/](https://web.dev/use-thumbor/)

[https://thumbor.readthedocs.io/en/latest/index.html](https://thumbor.readthedocs.io/en/latest/index.html)