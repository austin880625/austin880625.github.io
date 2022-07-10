title: 用 Python 實作一個 200 行內的 Static Site Generator
date: 2020/02/09
category: programming/python
---
Static Site Generator 在網路上有很多介紹，有幾個相當知名的工具如 Hexo, Hugo, Jekyll 等，其主要的運作流程是從網站內容的目錄讀出文章的 markdown 文件，再從使用者選取的佈景主題中讀出模板檔案，最後使用 template engine 將最終的網頁內容生成 HTML 檔案。完整的 SSG 會包含更模組化或更高自訂性的功能，例如 i18n 、 plugin 的 API 或是自訂 permalink 或 route 的規則等，但如果只是完成前面講到的基本功能，在已經有現成的 template engine 和 markdown parser 的情況下，似乎不會是很難的一件事。也因此我也想過自己實作一個 SSG 的想法，在思考程式的架構時因為 overdesign 的老毛病和喜歡亂試不同語言卡了一段時間，最後用 Python 搭配 python-markdown 和 jinja2 寫了一個最小可行版本，也不刻意遵守程式語言的 packaging convention 等規範（也就是只當成放在網站內容目錄下的一個自動化 script），不含佈景模板在兩百行內就能完成。

## 功能設計

### 網站目錄結構

一個用 SSG 維護的網站目錄下通常有放置文章 markdown 檔案的目錄、佈景主題目錄、和用來放置輸出完成的網站目錄。因為我們沒有要將程式碼打包成獨立套件，所以原始碼和這個目錄的內容變混在一起變成下面這樣：

```
├── content
├── content_type
├── public
├── site-gen.py
└── theme
    └── default
```

其中 site-gen.py 就是我們要完成的主程式， content_type 放置跟內容類型有關的原始碼， content 是網站內容的 markdown 目錄， theme 是佈景主題目錄， public 則是最終輸出的網站目錄。

### 文章元資料（Metadata）

因為 SSG 並不維護資料庫，文章內容以外的資料（如分類、標題、作者、日期等）最好的存放位置就是在文章的檔案裡面和文章本身的內容用特定格式區分開來。在常見的 SSG 中，這些資料都在 markdown 檔案的開頭以類似下面的格式呈現：

```markdown
title: Hello World
author: XXX
tags: newcomer, blog
---
```

這段內容在 SSG （事實上是資訊管理領域）的術語叫做 front matter ，在部分 markdown 的規範中會納入這段稱作 meta 的語法。總之，對我們來說，這個區塊的內容不需要太複雜，我自己目前只有規劃 title 和 path （permalink 用的路徑）而已。

### 內容類型

一般的 SSG 的內容類型都有分成文章和頁面，頁面擁有專屬於自己的路徑，並且在模板的語法中會在和文章不同的 loop 中輸出。我們已經將內容的路徑直接變成 meta 中的 path 欄位讓使用者自己規劃了，這樣文章和頁面就變得沒什麼差異，但我們可以貪心一點，假設未來會有使用者定義有特定欄位的內容，將文章、頁面規劃成繼承「內容」的類別（`Content`），`Content` 類別只解析 metadata 的部分，往後其他內容也同樣繼承這個類別後再自己定義欄位和文章解析的方式即可。這個想法是來自很多 CMS 會有 post type 或 content type 的設計來符合不同於部落格的網站內容需求

在目錄結構規劃上， content 目錄中可以多出 post 子目錄表示 post 這個內容類別的 markdown 檔案由 content_type 中的 post.py 來解析文章內容和 metadata。

因為 `Content` 類別會解析 metadata ，我們將全網站的設定如標題副標和 url 等資訊也存放在 content 目錄中的 site.md 裡。

### 靜態內容

像圖片、 css 和 js 檔案這類的靜態內容分為供佈景使用和供網站內容使用，為避免撞名，將兩者分別複製到 static 目錄的兩個分開的目錄底下。

## Show me the code

依照前面所講的 SSG 運作流程，主程式就分成三個步驟：

```python
        site = collect_site_content()
        theme = process_theme(site)
        generate_site(site, theme)
```

分別是尋找並處理 markdown 檔案、尋找並編譯佈景主題模板和產生最後的網站內容。

`collect_site_content()`：

```python
def collect_site_content():
    site = {
        "config": {
            "title": "",
            "subtitle": "",
            "theme": "default",
            "url": "http://127.0.0.1:8000/",
            "staticurl": "/static/theme"
        },
        "content_type": [],
        "content": {}
    }
    for type_name in os.listdir("content"):
        ent = os.path.join("content", type_name)
        if type_name == "static":
            dst = os.path.join("public", "static", "content")
            Path(os.path.join("public", "static")).mkdir(parents=True, exist_ok=True)
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(ent, dst)
        elif type_name == "site.md":
            content = Content(ent)
            site["config"].update(content.meta)
        elif os.path.isdir(ent):
            content_class = \
                getattr(\
                    importlib.import_module("content_type." + type_name),\
                    type_name.capitalize()\
                )
            site["content_type"].append(type_name)
            site["content"][type_name] = []
            for root, dirs, files in os.walk(ent):
                for name in files:
                    post = content_class(os.path.join(root, name))
                    site["content"][type_name].append(post)
            
    return site
```

最主要工作的是將名稱是 static 和 site.md 以外的資料夾名稱視為內容類型並加入存放內容的 Python Dict 中，處理特定內容類型的方法是在 content_type 目錄下尋找對應的 module 並用該 module 中的 class 存放屬於該內容類型的資料。例如 Post 這個內容類型需要找出 title 和用 markdown 處理 metadata 以外的內容：

```python
class Post(Content):
    def __init__(self, name):
        Content.__init__(self, name)
        self.permalink += ".html"
        self.title = self.meta.get("title")
        self.content = ""
        if self.file_type == ".md":
            self.content = markdown.markdown(self.raw_content, extensions=['extra'])
    def get_content(self):
        return self.content
```

`Content` 類別則是處理檔案前面的 metadata 資料，目前假設每個項目只有一行，不夠的話其實用 python-markdown 套件的 Meta extension 就好了：

```python
class Content:
    def __init__(self, name):
        self.meta = {
            "path": ""
        }
        self.filename = os.path.basename(name)
        self.raw_content = ""
        with open(name) as f:
            lines = f.readlines()
            for (i, line) in enumerate(lines):
                if line.strip() == "---":
                    self.raw_content = "".join(lines[i+1:])
                    break
                else:
                    kv = line.split(":")
                    key = kv[0]
                    self.meta[key] = ""
                    if len(kv) < 2:
                        continue
                    value = kv[1].strip()
                    self.meta[key] = value
                    print(key, ":", value)
        name_ext = os.path.splitext(self.filename)
        self.path = self.meta.get("path")
        self.permalink = "/" + self.meta.get("path") + "/" + name_ext[0]
        self.file_type = name_ext[-1]
    def get_content(self):
        return self.raw_content
```

文章的 permalink 是用文章 meta 的 path 欄位加上檔名決定的，會這樣寫是因為很多 SSG 預設用日期產生 permalink ，直接用 path 的話寫出 `2020/02/09` 這樣的內容就能有類似的結果。

接下來的東西都比較簡單，用 jinja 讀取每種內容類型的模板（`process_theme()`）之後以存放內容的 site 變數 render 模板，將內容寫入到正確位置的檔案（`generate_site()`）就可以了：

`process_theme()`：

```python
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
def process_theme(site):
    theme_path = os.path.join("theme", site.theme)
    if os.path.exists(os.path.join(theme_path, "static")):
            dst = os.path.join("public", "static", "theme")
            Path(os.path.join("public", "static")).mkdir(parents=True, exist_ok=True)
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(os.path.join(theme_path, "static"), dst)
    env = Environment(
        loader=FileSystemLoader(theme_path)
    )
    theme = {
        "index": env.get_template("index.html"),
        "single": {}
    }
    for content_type in site.content_type:
        theme["single"][content_type] = env.get_template("%s.html" % content_type)
    return theme
```

`generate_site()`：

```python
def generate_site(site, theme):
    print("writing index.html")
    with open(os.path.join("public", "index.html"), "w") as f:
        f.write(theme["index"].render(site))
    for content_type in site["content_type"]:
        for post in site["content"][content_type]:
            print('writing', content_type, "with name", post.filename, "into", post.permalink)
            Path("public/" + post.path).mkdir(parents=True, exist_ok=True)
            with open(Path("public" + post.permalink), "w") as f:
                f.write(theme["single"][content_type].render({
                    "config": site["config"],
                    "content_type": site["content_type"],
                    "content": site["content"],
                    content_type: post
                }))
```

因為有些連結使用的是相對 url ，我們可以準備一個簡易的 http server 來顯示生成的網頁，在主程式中用 serve 這個 subcommand 啟動：

```python
if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "serve":
            PORT = 8000
            web_dir = os.path.join(os.path.dirname(__file__), 'public')
            os.chdir(web_dir)

            Handler = http.server.SimpleHTTPRequestHandler
            socketserver.TCPServer.allow_reuse_address = True
            httpd = socketserver.TCPServer(("", PORT), Handler)
            print("serving at port", PORT)
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                httpd.shutdown()
                httpd.server_close()
    else:
        site = collect_site_content()
        theme = process_theme(site)
        generate_site(site, theme)
```

## 使用

這樣就算是完成了，在 content 目錄下新增 site.md 存放網站設定： 

```markdown
title: Hello World
subtitle: Hello Parallel World
theme: default
---
```

接著在 content/post 目錄下新增一篇文章：

```markdown
title: Hello World
path: 2020/02/09
---
# Hello World!

這是一篇測試文章
![Alt Text](/static/content/nest/abc.jpg)
```

再來就是用 jinja 模板語言寫佈景主題（其實就只是模板）：

base.html ：

```html
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <link rel="stylesheet" href="{{config.staticurl}}/style.css">
        <title>{{config.title}}</title>
    </head>
    <body>
        <header>
            <h1 class="header-title">{{config.title}}</h1>
            <h2 class="header-subtitle">{{config.subtitle}}</h2>
            <nav>
                <div class="nav-links">
                    <ul>
                        <li><a href="/">首頁</a></li>
                    </ul>
                </div>
            </nav>
        </header>
        <div class="container">
            {% block site_content %}{% endblock %}
        </div>
    </body>
</html>
```

index.html ：

```html
{% extends "base.html" %}

{% block site_content %}
<ul>
    {% for post in content["post"] %}
    <li><a href="{{post.permalink}}">{{post.title}}</a></li>
    {% endfor %}
</ul>
{% endblock %}
```

post.html ：

```html
{% extends "base.html" %}

{% block site_content %}
<h1>{{ post.title }}</h1>
<div class="post-content">
    {{ post.content }}
</div>
{% endblock %}
```

完成以後用 `python3 site-gen.py` 指令會將網站輸出到 public 目錄內，用 `python3 site-gen.py serve` 指令會 在 8000 port 上開啟 http server 提供 public 目錄的內容（也就是完成的網站）。

## 結語

基本上普通的功夫寫出來的東西就只能當玩具，還有很多功能可以實作，就當作是複習 python 了（也沒複習到多深）。