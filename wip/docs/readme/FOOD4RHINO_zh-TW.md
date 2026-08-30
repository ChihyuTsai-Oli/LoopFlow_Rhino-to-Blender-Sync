# Food4Rhino 中文（已送審，待審核通過後再補頁面網址）

LoopFlow Rhino to Blender Sync 把 Rhino 8 的模型、相機與燈光點位，單向同步到 Blender。匯出乾淨模型、寫出視角與點位，以及 Blender 端的更新。

主要流程：在 Rhino 裡照原本方式建模，按需要發布模型、選取物件、相機或燈光；Blender 讀取同一專案資料夾裡的交換檔。模型更新時，已調好的同名材質可以留下。各通道彼此獨立，不必一次做完。

目標是保留 Rhino 的設計自由，同時減少改完模型後在渲染場景裡重做一遍的重複工作。

請用 Rhino 的 Package Manager 安裝（搜尋 **loopflow Rhino to Blender Sync**）。Blender 端用該套件拷到「文件\LoopFlow」的 zip，以 Add-ons → Install from Disk 安裝。

不要把舊版 2.x 的工具列、套件或 Blender add-on 與本版混在同一專案。

系統需求：Rhino 8（Windows 10/11）、Blender 5.2.1（開發環境）。介面：English。說明文件：English / Traditional Chinese。
