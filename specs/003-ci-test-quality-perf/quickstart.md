# Quickstart: 驗證 CI 測試品質與效能量測擴充

## 本機驗證（實作後，推送前）

### 1. 測試成功率 + 覆蓋率報告（US1、US2）

```bash
python -m pip install --upgrade pip pytest pytest-cov
python -m pytest --junitxml=test-results.xml --cov=src --cov-report=xml
```

**預期結果**：

- 指令結束後，repo 根目錄出現 `test-results.xml`（JUnit 格式）與 `coverage.xml`
  （Cobertura 格式）。
- 若全部測試通過，指令結束碼為 0；手動讓任一測試失敗可驗證結束碼變為非 0
  （對應 FR-003 的「整體成功率」在 Azure DevOps 端會呈現為低於 100%）。

### 2. 效能量測腳本（US3）

```bash
python benchmarks/run_benchmarks.py
```

**預期結果**：

- repo 根目錄出現 `benchmark_summary.md`，內容包含 10 筆樣本（或失敗記錄）與平均的
  CPU 時間、記憶體用量（KB）、回應時間（秒）。
- 標準輸出最後一行為 `##vso[task.uploadsummary]<benchmark_summary.md 的絕對路徑>`
  （在本機執行時這行只是純文字，Azure Pipelines 執行時才會被解讀為 logging command）。
- 連續執行兩次，`benchmark_summary.md` 中的平均 CPU 時間／回應時間在同一台機器上應相近
  （因為每次都用相同的固定種子預先算出同一份猜測序列，透過 `cli.run()` 驅動完整的遊戲
  介面完成一局，詳見 `research.md` D5）；記憶體峰值
  （`max_rss_kb`）在多次執行間也應落在合理相近的範圍內，而不是單調遞增或明顯被先前執行
  的峰值污染（驗證 `research.md` D6 的量測方式正確）。
- 故意讓 `bench_driver.py` 失敗（例如暫時改一個會拋例外的分支，驗證完後還原），確認
  `run_benchmarks.py` 仍會正常結束（結束碼 0）並在摘要中標示該筆樣本失敗，而不是讓整個
  腳本中止。

### 3. 確認未修改 `src/`

```bash
git status --short src/
```

**預期結果**：無任何輸出（`src/` 底下沒有被修改的檔案），對應 FR-011 / SC-006。

## Azure DevOps 驗證（推送後）

> Claude 不會自行執行 `git push`；以下步驟由使用者推送後在 Azure DevOps 介面核對。

1. 推送到 `main` 分支，確認 pipeline 自動觸發（沿用既有行為，不在本功能驗證範圍內重複
   贅述）。
2. 開啟該次 pipeline 執行的 **Tests** 分頁：確認可看到逐案例通過/失敗狀態與整體成功率
   （US1）。
3. 開啟 **Code Coverage** 分頁：確認可看到整體覆蓋率百分比（US2）。
4. 開啟對應的 SonarQube Cloud 專案頁面：確認覆蓋率數據已上傳，且可識別未被覆蓋的程式碼
   位置（US2 / FR-005）。
5. 開啟該次執行的 **Extensions**／摘要分頁：確認可看到 `benchmark_summary.md` 的內容
   （10 次樣本的平均 CPU 時間、記憶體用量、回應時間）（US3）。
6. 確認無論效能數字為何，pipeline 整體執行結果（成功/失敗）仍只由建置與測試步驟決定
   （FR-010）；可對照「效能量測」步驟本身的狀態（即使該步驟顯示警告或失敗，整體 pipeline
   不受影響，因為該步驟設有 `continueOnError: true`）。
