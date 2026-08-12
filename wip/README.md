# LoopFlow R2B WIP

此資料夾是 R2B 3.0 的 Git 追蹤工作區；穩定 2.x 與 release payload 仍留在原位置。

```text
wip/
  docs/           # 重構 SSOT、資料契約、roadmap、progress
  src/            # 後續建立的 3.0 原始碼
  tests/          # 自動與契約測試
  fixtures/       # 可提交、輕量且不含私人資料的測試資料
```

大型 Rhino／Blender 工作檔、人工測試輸出與可由 Dropbox 同步的素材不放進 repo。其本機根目錄由環境變數 `LOOPFLOW_R2B_WORKFILES_ROOT` 指定，電腦對照與設定方式見工作區根目錄 `工作檔路徑.md`。

Rhino 與 Blender 產生／讀取的即時交換 JSON 放在 `%LOOPFLOW_R2B_WORKFILES_ROOT%\exchange\`，不提交 Git。
