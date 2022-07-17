# 在 Wordpress 2022 佈景主題加入 Google Analytics 標籤的方法
date: 2022/07/02
category: web-dev/wordpress
thumbnail: https://img.austint.in/yy_O-vL9tKSknaOhdIecPZck3D8=/fit-in/760x560/filters:format(webp)/wp-add-ga-tag-with-2022-theme/theme-edit.png
---

在一兩年前 Wordpress 預設使用的佈景主題是 Twenty Twenty-One ，這之前的佈景主題檔案都還能看到 `<head>` 標籤在 `header.php` 裡面，所以如果有像是 Google Analytics 的線上服務需要內嵌腳本，可以直接在更改佈景主題檔案的功能中把 `<script>` 標籤加到 `<head>` 標籤內。

## 為什麼 head 標籤不能直接用了？

在 2018 年起， Wordpress 發布了新版的 Gutenberg 編輯器，相較於舊版編輯器開發了區塊編輯器的概念用來取代 shortcode，將區塊作為以 ReactJS 爲基礎的統一界面，讓 plugin 的開發者能夠在文章編輯器中建立所見即所得的自訂內容區塊。而在這個編輯器發布後不久， Wordpress 開發社群就開始把目標設定為把這個編輯器從單純的文章編輯延伸到整個網站的佈景都可以透過區塊編輯。

幾天前裝了一個 Wordpress 網站起來，用最新的 Twenty Twenty-Two 佈景主題發現整個佈景主題設定已經變成所見即所得的界面，佈景主題檔案內也沒有原本所見的 `header.php` 檔案，而是大部分都變成了帶有 Wordpress block 註解的 HTML 檔案，也不包含 HTML 檔案最開始的 `<head>`, `<body>` 等標籤，從 `index.php` 的說明看起來，佈景主題也不會再有包含這些標籤的檔案，都會由 Wordpress 自動生成。

![Wordpress 的 Twenty Twenty-Two 佈景找不到 head 標籤](https://img.austint.in/dqxWTvt2S6N4aKsg4c_9FVkA9VU=/960x0/wp-add-ga-tag-with-2022-theme/theme-edit.png)

## 新的 GA 標籤要放哪裡？

以佈景主題的設計來說，更換佈景主題的時候是希望能夠不用影響到網站功能的，而網站的額外功能應該要由 plugin 來提供，所以原本就使用 plugin 的人應該不會被這個版本的佈景主題更新影響。但我自己不太想要只是因為一段複製貼上的 code 就裝一個 plugin ，就把插入 `<script>` 標籤在新版 Wordpress(5.7+) 的寫法寫到 Wordpress 預設安裝的範例 Hello Dolly plugin 裡面。做法如下：

假設在 Google Analytics 管理介面拿到的 GA 標籤程式碼是這樣， `G-XXXXXXXXXX` 是 GA 的 ID

```
<!-- Global site tag (gtag.js) - Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-XXXXXXXXXX');
</script>
```

先在 Plugin 頁面把 Hello Dolly 關閉，接著要找到 Hello Dolly plugin 的程式碼，開啟 Tools -> Plugin File Editor 後，在右上角可以看到選擇 plugin 的選取框，選擇 Hello Dolly 後按 Select 

![編輯 Plugin 程式碼的步驟](https://img.austint.in/Uoj5IMhW4iIuk5eF0EDpjVbufAo=/960x0/wp-add-ga-tag-with-2022-theme/plugin-edit.png)

在編輯區塊上面的其他程式碼可以自己決定要不要刪掉，最開始的註解不要刪就可以了，那是 Wordpress 的 Plugin 宣告。然後在最底下加入

```
function dolly_enqueue_google_analytics() {
	wp_print_script_tag(
		array(
			'src' => esc_url('https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX'),
			'async' => true,
		)
	);
	wp_print_inline_script_tag("
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-XXXXXXXXXX');
	");
}

add_action('wp_head', dolly_enqueue_google_analytics);
```

接著按 Update File 後再到 Plugin 的頁面啟用 Dolly ，接著就可以到網站首頁用開發者工具檢查標籤是不是載入成功了。

## References

[https://core.trac.wordpress.org/ticket/54272](https://core.trac.wordpress.org/ticket/54272)

[https://make.wordpress.org/core/2021/02/23/introducing-script-attributes-related-functions-in-wordpress-5-7/](https://make.wordpress.org/core/2021/02/23/introducing-script-attributes-related-functions-in-wordpress-5-7/)

[https://developer.wordpress.org/reference/functions/wp_head/](https://developer.wordpress.org/reference/functions/wp_head/)