title: USB Specification 簡介
path: 2020/02/14
date: 2020/02/14
---
如果要寫 USB 裝置的 driver 或應用程式，對 USB 規範的基本認識是必須的，在 [USB 開發者論壇（USB-IF）的網站](https://www.usb.org/document-library/usb-20-specification)上可以下載到 USB 規範本文，雖然 USB 3.0 規範已經釋出許久，但其設計是向後相容的，且 USB 3.0 的規範依然需要對 USB 2.0 有了解，因此在這裡只對 USB 2.0 規範對軟體開發較相關的內容做一些整理。

## Spec 內容安排

USB 規範下載下來是一個 zip 檔，規範的本文是 usb_20.pdf 這個檔案，規範定義了 USB 從裝置類型、硬體尺寸、電氣特性、訊號格式到協定的架構的所有內容，對軟體開發來說，訊號格式（Electrical 章節的一部分）可以略讀，而協定架構以及不同裝置類型在協定中如何傳送資訊則是比較需要瞭解的。

## USB 系統的物理架構

一個有不同裝置互相連接的 USB 系統中，會有一個 host 及一至多個 device ， device 在規範中分為 hub 及 function ， hub 可以繼續連接更多 USB 裝置（最多七層）， function 則是提供裝置本身的功能，這些裝置在物理上連接的樹狀結構稱為 bus topology，如下圖（來源：Universal Serial Bus Specification）：

![Bus Topology](/static/content/usb/bus_topo.png)

物理上的樹狀結構在 host 是需要被維護的（為了處理整個 hub 的熱插拔），但在操作裝置時 host 並不需要處理樹狀結構的資訊，而是如同所有 device 都直接接在 host 上來操作，由 hub 自己依照規範將訊號轉送到對應的裝置。

在任兩個 USB device 之間連接的 USB cable 物理上是四條導線： VCC, GND, D+ 和 D- ，訊號在 D+ 和 D- 上以 NRZI（None Return to Zero Inverted） 的編碼傳送在 USB protocol layer 的封包。各個裝置的 controller 都會有一個稱作 SIE（Serial Interface Engine） 的單元負責在 USB 抽象的資料流模型和封包的 bitstream 之間作轉換。

## USB 資料流模型（Data Flow Model）

在 protocol layer 之上所抽象出來的 USB 資料流模型定義在規範中的第五章，章節的開頭說到無論是軟體還是硬體的 USB 開發者都應該閱讀，這章的內容除了更詳細的說明 USB 的基本概念，也定位了 USB 的各項實作細節在資料傳輸中扮演什麼角色，分層的模型也進一部劃分了軟硬體上的分工，所以相當重要。

USB 以裝置的位置和 endpoint 的號碼及輸入輸出唯一決定資料傳輸的目標，所以我們會說「對某個 address 上的 device 的 endpoint x 傳送/接收資料」。一個 USB device 可以有很多 endpoint ，也可以包裝多個 endpoint 成為一個 interface 用以和 host 上控制該裝置的軟體溝通。這些 address, endpoint 及 interface 的資訊會在 host 進行 bus enumeration 的程序中透過 endpoint 0 傳送/被指定。

在 protocol layer 以上的分層邏輯應該是以 host 的軟體架構來劃分的，在 host 上有兩種軟體會與 USB 裝置通訊，分別是管理 host 上 USB 裝置的 system software 以及控制特定 USB 裝置的 client software 。 system software 會和所有 USB 裝置通訊，一般只透過裝置的 endpoint 0 取得裝置的資訊；而 client software 只會和其支援的裝置通訊，會依照該裝置提供的 interface 和該 interface 所包含的 endpoint 溝通。這兩種軟體在 spec 中並不直接代表 host 上的 driver 或應用程式，因為 host 不一定代表一臺電腦，電腦上也不一定有管理 driver/應用程式的 OS （例如印表機列印隨身碟檔案的功能），所以應該以程式通訊的對象和負責的工作來判斷。

![USB data flow](/static/content/usb/data_flow.png)

## Endpoint Transfer Type

為了讓不同類型的資料都能在 USB 上傳輸，以及提高傳輸通道的 utilization ， USB 定義了四種 endpoint 傳輸的方式，分別是 Control transfer, Bulk transfer, Interrupt transfer 和 Isochronous transfer 。 transfer type 規範的是一部分的資料格式、封包的大小限制、資料傳輸的延遲及資料傳輸方向等。除了 control transfer 之外的 transfer type 都是單向的，因此若要做到雙向傳輸就需要用到兩個 endpoint

### Control Transfer

所有的 USB 裝置都至少有這個 endpoint

### Bulk Transfer

### Interrupt Transfer

### Isochronus Transfer