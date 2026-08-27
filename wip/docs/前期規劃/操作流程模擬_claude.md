# R2B 3.0 — 操作流程模擬（Claude 版）

> 與 [`操作流程模擬_cursor_grok.md`](操作流程模擬_cursor_grok.md) 同源、不同視角，兩份並存互相對照，**都不改寫對方**。
> 依據：[`資料生態決策表_合併.md`](資料生態決策表_合併.md) 的已決欄、[`現況與工作鏈藍圖.md`](現況與工作鏈藍圖.md)、`_R2B_重構計畫.md`，以及現行 2.x 程式（Rhino 端 5 支 Python、Blender 端 `import_3dm` fork 與 Toolkit）。
> 這是 **3.0 目標行為**的驗收腳本草案，不是 2.x 現在會發生的事。指令名見 [`../rhino指令.md`](../rhino指令.md)。

本版維持三個獨有視角，這也是它和 grok 版的分工：

1. **磁碟上實際長什麼樣** — 每一步之後 `loopflow_R2B/` 裡多了什麼、少了什麼。
2. **失敗、取消、中斷時停在哪裡** — 包含 R2B 特有的一種：Rhino **停在別的檔案裡**。
3. **哪些現在就必須有、哪些可以晚點補** — 第一次實機測試不需要整條鏈都做完。

---

## 讀之前：六處裁決文字對不上，我在模擬裡採用的讀法

多數決自動填入時，有幾列的「你的決定」與同列建議方向或其他已採用原則對不上。我沒有改動決策表，只在這裡說明本模擬採用哪一種讀法，**這六列請你回頭確認**。

| ID | 決定欄目前寫的 | 為什麼對不上 | 本模擬採用 |
|---|---|---|---|
| `R2B-ND-09` | 「採 **B**；先 A」 | 同一格裡先說 B（設定檔 exclusive lock）又說「先 A」（不鎖）。合併表自己也標了「選項字母有差」 | **A（不鎖）**。`XF-ECO-02` 把即時檔移到工作檔旁之後，不同專案自然分開，多開 Rhino 已不會互蓋；真的撞到再加鎖 |
| `R2B-ED-01` | （只有一段引述 `_SelAll` 的現況，沒有選定模式） | 這一列問的是「最終選取規則」，決定欄沒回答 | **三種互斥模式：全部／指定圖層／目前選取**，執行前顯示物件數與範圍，只把上次成功的模式記成預設。**這是本模擬的假設，不是你的裁決** |
| `R2B-ED-02` | 採 B（預設開 watcher，可關） | B 的前提是「現況有自動 watcher」。但 `LiveLink_R2B_Camera.py:72、80` 用的是 Python 2 的 `sc.sticky.has_key(...)`，在 Rhino 8 的 CPython 下很可能一按就 `AttributeError` | 照 B 寫，但把「watcher 現在到底能不能跑」列為**實機第一項要確認的事** |
| `XF-ED-02` | 不升級，新舊版不可混用 | 與 `R2B-ED-12`（設定檔欄位對照表必做）語氣相反 | 兩者其實可並存：**不做自動轉換**，只產生一份唯讀清單告訴你「舊設定的值長怎樣、你要自己重設哪些」 |
| `R2B-ND-04` | 小寫＋角色清楚（建議名含 `model_lastgood.3dm`） | `XF-ND-01`＝A 要求兩產品同型命名，而 R2O 那邊的 last-good 是不帶後綴的 `models.usdz` | **`model.3dm` 是 last-good、`model_pending.3dm` 是發布中**，與 R2O 同型。不用 `_lastgood` 後綴 |
| `R2B-ND-05` | 採 A（凍結 2.x 數學） | 「凍結現況」＝凍結「完全不做單位與軸向轉換」。若不寫明，之後很容易有人以為 payload 是公尺 | 照 A 凍結數值，但契約必須明寫 **payload 是 Rhino 原生單位與原生軸向**，並加上 `unit_system`／`meters_per_unit` 等純描述欄位（不改變數值） |

另外有八列的決定欄只是把建議文字截斷貼上、沒有寫出選項字母（`R2B-ECO-05`、`ECO-06`、`ED-03`、`ED-07`、`ED-08`、`ED-12`、`ND-07`、`ND-08`）。這些我照同列整合建議的方向讀。

---

## 示範專案

| 項目 | 本模擬用的值 |
|---|---|
| 工作檔 | `…\WIP_R2B\source\Demo_Apt.3dm`（已存檔） |
| 設定根 | `…\WIP_R2B\source\_LoopFlow_Config\loopflow_R2B\`（`XF-ECO-02`） |
| Blender 檔 | `…\WIP_R2B\source\Demo_Apt.blend` |
| Blender 如何找到設定根 | AppData 指標檔為預設，`rhino_json_dir` 可手動覆寫；手動優先（`XF-ED-04`＝C） |
| 介面語言 | 全英文（`XF-ED-01`＝A）——下面引號內的訊息就是使用者實際會看到的字 |
| 設定檔格式 | JSON（`R2B-ND-03`＝B） |

圖層與 Blender 端對應：

| 用途 | Rhino 示範 | 誰讀它 | Blender 端 |
|---|---|---|---|
| 建築／家具幾何 | `R2B::MDL::Architecture`、`R2B::MDL::Furniture` | `R2B_Models` | 匯入／更新模型 |
| 燈光對齊點 | `R2B_LT_Points::Downlight`（Point 物件） | `R2B_Light` | `RH_*` empty，靠 `rhino_guid` 對齊 |
| 燈具樣板 | （不在 Rhino） | — | Fixtures collection，複製成 `INST_*` 子物件 |

燈的亮度、顏色、IES 全部在 Blender 樣板上調（`ED-06`＝A）。Rhino 端讀的是幾何點，本來就沒有這些值可讀。

---

## 磁碟：跑完一整輪之後，設定根應該長這樣

```text
Demo_Apt.3dm
Demo_Apt.blend
_LoopFlow_Config/
  loopflow_R2B/
    config.json              ← 取代 R2B_Path.txt（ND-03＝B）
    r2b.log                  ← 現在完全不存在，見下
    live/                    ← 高頻小檔
      camera.json            last-good
      camera_pending.json    只在發布中的瞬間存在
      light.json             last-good
      light_pending.json
    models/                  ← 低頻大檔
      model.3dm              last-good
      model_pending.3dm
```

分成 `live/` 與 `models/` 是因為工作檔在 Dropbox 裡（見工作區 `工作檔路徑.md`）。R2B Camera 目前是**每次視角變動就寫一次、完全沒有節流**（`LiveLink_R2B_Camera.py:39-64`；R2O 至少有 0.2 秒節流），放在雲端同步資料夾裡會一直觸發上傳，也比較容易出現「衝突複本」讓 Blender 讀到錯的檔。**3.0 應該替 R2B Camera 補上與 R2O 相同的節流規則**，這件事決策表沒有明列。

`r2b.log` 值得單獨講：`LiveLink_R2B__Config.py:37` 定義了 debug log 的路徑，但**整個 repo 沒有一支程式寫入它**。R2B 現在是零 log，所以任何「失敗了但我不知道為什麼」都無從查起。

---

## 階段 0｜開案與 Health

**`R2B_Open`** → 從目前 `.3dm` 推出設定根 → 讀 `config.json` → 更新 AppData 指標檔 → 印出實際生效值與三個通道的 last-good 時間。

`ED-05`＝A：Open 與 Config 不分開，設定只有 8 個欄位，其中至少 3 個在 3.0 會消失（`DataPath`、`ModelDir`、`BoxMapSize`），拆兩個指令不划算。
`ED-04`＝B：Health 就在 `R2B_Open` 裡，不另立指令。

Health 至少要回答三件事，因為這三件是雙機作業最常出錯的地方：

```text
Project     : Demo_Apt.3dm
Config      : ...\_LoopFlow_Config\loopflow_R2B\
Pointer     : updated (AppData\...\current_project.json)
Last good   : model.3dm    2026-08-27 14:02
              camera.json  2026-08-27 14:05
              light.json   (none)
Blender     : sync folder matches (checked via pointer)
```

> **使用者介入**：只在路徑或設定有問題時。
>
> **停在哪裡**：文件未存檔 → `Save the file first.` 後停止，不建立任何資料夾（`XF-ECO-01`＝B）。

---

## 階段 1｜Models（3DM）

**`R2B_Models`** → 選範圍（三種模式之一，見上方矛盾表）→ **顯示物件數與範圍讓你確認** → 收集明確物件 ID → 在**暫存文件／暫存資料**上做清理（炸開 Block、刪除輔助物件、建立材質、Box Mapping、Purge）→ 匯出 `models/model_pending.3dm` → 驗證（至少要能被 importer 讀開）→ atomic 換成 `model.3dm`。

在 Blender：更新／匯入 last-good 模型。重複同步時保留你已指定的材質與 Blender-owned 屬性（`ED-08`）。

> **使用者介入**：選範圍；在 Blender 按更新。
>
> **停在哪裡**：
> - 範圍是空的 → 阻擋，不發布，`model.3dm` 不動（`ED-07`）。
> - 匯出或清理失敗 → `model.3dm` 是上一版；**Rhino 仍停在你原本的工作檔**。
> - 中途取消 → 來源 `.3dm` 的物件、圖層、選取、可見／鎖定狀態與 `doc.Modified` 全部與執行前相同（`XF-ECO-03`）。

**與 2.x 的差別，這一階段最多，而且有一個會吃掉你的東西**：

1. **現在的圖層選單其實不影響匯出範圍。** 程式先依你選的圖層挑物件（`LiveLink_R2B_Models.py:107-110`），下一行卻執行 `_SelAll`（`:113`）把整份文件全選再匯出。所以 `LastModelLayer` 從來沒有真的限制過輸出——你現在熟悉的「選圖層」行為，可能和實際結果無關。
2. **現在會在沒有提示的情況下吃掉未存的修改。** 為了避開存檔提示，程式先 `rs.DocumentModified(False)` 再 `_-Open` 中繼檔（`:130-131`），最後又 `DocumentModified(False)` ＋ `_-Open` 原檔（`:199-201`）。如果你在按 Models 之前有還沒存的修改，它們會安靜消失。
3. **現在取消或當掉會停在別的檔案裡。** 清理是在「開啟中繼檔」的狀態下做的，中途中斷，你的 Rhino 就停在 `R2B.3dm` 而不是 `Demo_Apt.3dm`。這是 `ECO-05`（可取消）現在唯一真正的例外。
4. **現在失敗也會說成功。** `finally` 無條件印出 `Export complete`（`:203-205`），前面失敗與否完全不影響。
5. **現在先刪後匯。** `os.remove` 舊 3DM 再匯出（`:115-119`），失敗時 last-good 已經先沒了。
6. **材質名可能撞名。** 材質名取自圖層路徑的**最後兩段**（`:170-171`），不同父層但後兩段相同的圖層會產生同名材質。

---

## 階段 2｜Camera（JSON）

**`R2B_Camera`** → 開／關 watcher（`ED-02`＝B，預設開、可關、可手動推一次）→ 視角變動時寫 `live/camera_pending.json` → validate → atomic → `live/camera.json`。

payload 凍結 2.x 數值（`ND-05`＝A）：Rhino 原生座標、原生單位、`Camera35mmLensLength` 原值，**不做任何換算**。換算全部在 Blender 端一處完成（現況是 `rhino_cam_scale` 與 `rhino_cam_lens_mult` 兩個使用者可調欄位，`LoopFlow_import_3dm/__init__.py:148-149、165-167`）。契約要明寫這件事，並附上 `unit_system`／`meters_per_unit` 等描述欄位供 Blender 端自動帶入預設值。

在 Blender：timer 讀檔 → parse → apply → **成功之後**才更新「已套用」狀態（`XF-ECO-05`）。

> **使用者介入**：切到你要的視角；決定 watcher 開或關。
>
> **停在哪裡**：
> - 沒有有效相機 → 警告，不覆寫 `camera.json`（`ED-07`）。
> - Blender 讀到寫到一半的檔 → 這一輪失敗，**但下一輪必須重試**。
> - Blender apply 失敗 → 不更新已套用狀態，訊息要說出是哪一段失敗（`ED-03`）。

**與 2.x 的差別**：現在 Blender 端是**先記 mtime 再 parse**——`LoopFlow_import_3dm/__init__.py:160` 先把 `livelink_last_mtime` 設成新值，`:162-163` 才開始 parse，而整段包在 `except Exception: pass` 裡（`:194-195`）。所以只要讀到一個寫到一半的 JSON，這一輪會安靜失敗，而且因為 mtime 已經記起來了，**在檔案下次被寫入之前不會再重試**。配上 Rhino 端非 atomic 的 `open(..., 'w')`＋`json.dump`（`LiveLink_R2B_Camera.py:63-64`），這就是「相機偶爾跟丟、重開才好」的成因，全程沒有任何訊息。修法只有一行的位置差別：mtime 移到 apply 成功之後。

---

## 階段 3｜Light（JSON）

**`R2B_Light`** → 掃 `LightLayer` 底下的 Point → 每一項帶位置與 `source_guid` → 寫 `live/light_pending.json` → validate → atomic。

在 Blender：依 `rhino_guid` 對齊既有 empty；沒有的就新建 `RH_<type>_<guid 前 5 碼>`，並從 Fixtures 樣板複製 `INST_*` 子物件（`LoopFlow_import_3dm/__init__.py:275-307`）。你在樣板上調的燈參數會被保留，因為那本來就由 Blender 管。

`ECO-06`：Light 通道是 R2B／R2O 兩個產品裡**唯一做對身分**的地方——它送的是 Rhino 物件 GUID，Blender 以自訂屬性 `rhino_guid` 對齊（`LiveLink_R2B_Light.py:66`、`__init__.py:245、257`）。3.0 應該把它當範本，而不是重新設計。

> **使用者介入**：把點放對圖層。
>
> **停在哪裡**：
> - **找不到 `LightLayer`、或該圖層底下沒有點 → 阻擋，不得發布空清單**（`ED-07`）。若你真的要清空，必須是一個明確的「發布空集合」動作並再確認一次。
> - 單點資料異常 → 整批停止並列出，不部分套用。

**與 2.x 的差別，這一項是我在 R2B 找到唯一會造成可見損失又完全沒有提示的路徑**：現況沒有任何點符合條件時，程式仍然無條件寫出 `{"points": []}`（`LiveLink_R2B_Light.py:52-76`）。Blender 端讀到空清單後，`active_guids` 是空的，於是把 collection 內**所有**帶 `rhino_guid` 的 empty 全部刪掉、連同底下的 `INST_*` 子物件一起移除（`__init__.py:317-342`），最後回報 `Light sync complete! Processed 0 point(s).`——看起來像成功。也就是說：`LightLayer` 打錯一個字，和「真的沒有燈」，現在是同一個結果，而且會直接毀掉你在 Blender 排好的整組燈具。

順帶一提，現行比對是 `layer_full.startswith("R2B_LT_Points")`，**沒有加 `::`**（`:48、58`），所以 `R2B_LT_Points_舊` 這種圖層也會被一起吃進來。R2O 的同一段有加 `::`。3.0 應比照修正（`ND-08` 需要你確認的兩欄之一）。

另外有一個設計得不錯、值得寫進契約的行為：某個點在 Rhino 被刪掉時，掛在它底下的**非** `INST_*` 物件不會被刪，而是解除父子關係並標記 `recovered_rhino_guid`，下次那個 GUID 回來時會自動接回去（`__init__.py:263-273、329-337`）。

---

## 第二輪：改東西之後

| 你改了什麼 | 要重跑什麼 | 不該被影響的 |
|---|---|---|
| 建築幾何 | `R2B_Models` → Blender 更新模型 | `camera.json`、`light.json` 不該被 Models 指令碰到；Blender 端已指定的材質要留著（`ED-08`） |
| 視角 | watcher 開著就不必按；關著就手動推一次 | 模型與燈光 |
| 移動／增刪燈光點 | `R2B_Light` → Blender 對齊 | 樣板上的燈參數；你手動掛在 empty 底下的非 `INST_*` 物件 |

三個通道可獨立執行、驗證、取消與復原（`ECO-05`）。

---

## 中斷、取消與失敗停在哪裡

這張表是我認為最該拿去當驗收清單的一張。

| 情境 | Rhino 來源文件 | 設定根磁碟 | Blender 場景 | 使用者看到 |
|---|---|---|---|---|
| 文件未存檔就按發布指令 | 不變 | 完全不建立 | 不變 | `Save the file first.` |
| Models 清理中按 Esc | 物件／圖層／選取／`doc.Modified` 全部與執行前相同，**且 Rhino 仍停在原工作檔** | `model.3dm` 是上一版 | 不變 | `Cancelled at stage: cleanup.` |
| Models 匯出失敗 | 同上 | `model.3dm` 是上一版；pending 保留供診斷 | 不變 | `Failed at stage: export.` ＋可開 log |
| 範圍是空的 | 不變 | 不動 | 不變 | `Nothing to export in the selected range.` |
| `LightLayer` 打錯字 | 不變 | `light.json` **維持上一版** | **燈具全部留著** | `Light layer '<name>' not found.` |
| Camera 寫檔時 Dropbox 鎖住檔案 | 不變 | `camera.json` 是上一版 | 停在上一個位置 | 寫進 log；不跳視窗打斷建模 |
| Blender 讀到寫到一半的 JSON | 不變 | 不變 | 不變，**且下一輪會重試** | 靜默重試；連續失敗才提示 |
| Rhino 當掉 | 你自己未存的修改仍在（指令不得先清 `doc.Modified`） | 最多留下一個 `*_pending` 檔 | 不變 | — |

倒數第二列和最後一列是 3.0 相對 2.x 最重要的兩個行為改變。

---

## 第一階段最小可用範圍

第一次實機測試不需要整條鏈。我建議的順序是：

1. **確認 Camera watcher 現在到底能不能跑**（`sc.sticky.has_key`）。這只要按一次按鈕就知道，卻會決定 `ED-02` 的前提是否成立。**排第一是因為它最便宜。**
2. **設定根＋指標檔＋Health**（階段 0）。沒有這個，後面每一步都無法確認 Blender 讀的是不是同一個資料夾。
3. **log**。R2B 現在零 log；在補上之前，任何失敗都只能靠猜。這是所有後續驗證的前提。
4. **Light 端到端**。它是三個通道裡唯一身分已經做對的，改動最小、最快能跑通，而且順便修掉 `ED-07` 那條會清空燈具的路徑。
5. **Camera**：atomic publisher ＋ 節流 ＋ consumer 的 mtime 位置。三件事一起改才有意義。
6. **Models**：範圍模式 → 暫存文件清理 → pending → validate → atomic。這是最大的一塊，也是唯一需要重新設計流程（不能再用開關檔）的一塊。
7. **Blender 端拆分**（`ECO-01`）：把同步引擎、面板、operator 從 `import_3dm` fork 的 `__init__.py` 搬出去，並換掉 `import_3dm.*` operator namespace（`ND-02`）。

第 7 項可以和 4-6 並行，因為它完全不影響 Rhino 端。可以晚點補的：Toolkit 分包（`ED-11`）、Extension 發行形態（`ED-10`）、`import_3dm` 的 patch 允許清單（`ND-07`，但要等第 7 項做完才有意義——現在 fork 裡 850 行有一大半是第一方程式碼，無法回答「哪些算 patch」）。

---

## 這條流程還沒回答的問題

1. **`R2B-ED-01` 沒有真正的答案。** 決定欄只引述了 `_SelAll` 的現況。在你實機確認「你要的到底是整份文件還是指定圖層」之前，Models 的範圍規則無法凍結——而範圍規則決定了 `LastModelLayer` 這個設定欄要不要留（`ND-08`）。
2. **Blender 端的路徑升級沒有偵測機制。** Auto-Detect 現在把 Sync Folder 寫死成 AppData（`__init__.py:550-555`）、模型路徑寫死 `//R2B.3dm`（`:548`，相對 `.blend`）。新版路徑是 `_LoopFlow_Config/loopflow_R2B/models/model.3dm`，既有 `.blend` 會安靜地讀不到新檔。建議 add-on 主動比對並提示「這個路徑看起來是舊版位置」，而不是只在文件寫一句。
3. **`BoxMapSize` 要不要留沒定。** `ND-08` 標的兩欄之一。它現在是固定 500 的全域值（`LiveLink_R2B_Models.py:186`），但 Box Mapping 的合適尺寸其實跟案子尺度有關。留、改成每次可選、或直接移除，三種都合理，需要你決定。
4. **「必須保留」清單只列了一半。** `ED-08` 要求列出清單，現況可以直接抄的有：材質指派、`rhino_guid`／`rhino_type` 自訂屬性、`INST_*` 相對位置、`recovered_rhino_guid` 重掛機制。還沒被保護的至少有兩項：你對 `RH_*` empty 的手動改名，以及你自己用 `INST_` 開頭命名的手工物件（會被當成同步產物刪掉）。

---

## 與 cursor grok 版的主要差異

兩份都依同一張決策表，結論方向一致。差別在於：

| | grok 版 | 本版 |
|---|---|---|
| 形式 | 一條連續編號的操作清單（31 步） | 分階段，每階段附磁碟狀態與停點 |
| 對矛盾裁決的處理 | 直接採用建議方向 | 開頭獨立一節列出六處落差與本模擬採用的讀法，請你回頭確認 |
| 失敗行為 | 分散在各步驟的但書 | 集中成一張中斷矩陣，可直接當驗收表 |
| 與 2.x 的對照 | 「你應該感覺到的安全差異」四點 | 每階段末尾附具體 `檔名:行號`；Models 那段列了六項 |
| 實作順序 | 未涵蓋 | 「第一階段最小可用範圍」七步，第一步是一個只要按一次按鈕的檢查 |
| 未決事項 | 未涵蓋 | 「還沒回答的問題」四項 |

建議兩份一起看：grok 版適合照著點一遍確認流程順不順，本版適合在寫程式前確認每一步的失敗行為與磁碟狀態。
