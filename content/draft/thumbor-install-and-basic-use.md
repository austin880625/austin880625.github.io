
我在 Alpine linux 上嘗試直接用 `pip3 install` 安裝，但永遠有一些 extension 沒辦法被 import ，在那個目錄只看到 `.c` 檔，表示那些檔案沒有被編譯到，也許是套件的自動編譯 config 寫錯了，所以使用了下載原始碼手動編譯的方式。

```
# Pillow 編譯的 dependency ，只有安裝時會用到
apk add --virtual  build-deps gcc python3-dev musl-dev
apk add gcc python3-dev jpeg-dev zlib-dev
apk add curl-dev
pip3 install pycurl
wget https://github.com/thumbor/thumbor/archive/refs/tags/7.0.10.zip
unzip 7.0.10.zip
cd thumbor-7.0.10
python3 setup.py install --user
# 安裝後就可以刪除
apk del build-deps
```

```
thumbor-url -l key '20220703_180520.jpg'
```