# LoopFlow R2B WIP

此資料夾是 R2B 3.0 的 Git 追蹤工作區；穩定 2.x 與 release payload 仍留在原位置。

```text
wip/
  docs/           # 重構 SSOT、資料契約、roadmap、progress
  src/            # 後續建立的 3.0 原始碼
  tests/          # 自動與契約測試
  fixtures/       # 可提交、輕量且不含私人資料的測試資料
```

大型 Rhino／Blender 工作檔、人工測試輸出與可由 Dropbox 同步的素材不放進 repo。測檔／素材根目錄由環境變數 `LOOPFLOW_R2B_WORKFILES_ROOT` 指定，電腦對照見工作區根目錄 `工作檔路徑.md`。

3.0 執行時的設定與即時 JSON 寫在目前工作檔旁的 `_LoopFlow_Config/loopflow_R2B/`，不提交 Git。已發布 2.x 仍用 AppData。
