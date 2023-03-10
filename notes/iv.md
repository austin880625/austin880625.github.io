# 知識點

slab: 固定大小的記憶體區塊（較大塊）
buddy system: 將可用空間（2^k）不斷對半分割直到 fit 最小的區塊

thread 和 process 在 linux kernel 中都是使用 task_struct ，thread 是 scheduling 的最小單位，process 是擁有獨立 address space 的最小單位，所以多個 thread 會共用 `mm` (或 `active_mm`)field

cache coloring
direct mapping cache
associative set cache
https://stackoverflow.com/questions/23448528/how-is-an-lru-cache-implemented-in-a-cpu

linux kernel 的 hash function 是將數字乘上黃金比例的小數部分再左移取高位
multiqueue 和普通 LRU 的差別: LRU 只有維護 cache data 存取時間的關係，multiqueue 的多個 LRU 之間 promote/demote 的基準是存取的頻率，所以透過維護 hit count 這類資訊就能近似帶有 aging 機制的 LFU 的理想狀態。
https://www.usenix.org/conference/2001-usenix-annual-technical-conference/multi-queue-replacement-algorithm-second-level

TinyLFU: 帶 counter 的 bloom filter 取最小的

static function in C: scope is in the same file
static function in C++: can only access static members in the class

diff btween class and struct: the members are default to be private/public

concurrency model

kobjects
lock types
memory allocation
maple tree
mm_struct, vm_struct, vm_area_struct

raid 0
raid 1

# 自我介紹

陽明交通大學畢業
    在學期間
        ACM
        系計中助教
        課程助教

    專案
        專題
        UART-IAP
        FreeRTOS

    自架網站
        PVE
        硬碟、網路架構
        reverse proxy
        NAS
        密碼管理器
        gitea
蝦皮工作