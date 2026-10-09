# Phase 1 Data Model: CI 測試品質與效能量測擴充

本功能不涉及應用程式資料庫或持久化模型；以下為 CI 流程中流動的資料結構，對應
`spec.md` 的 Key Entities，供 `/speckit-tasks` 與 `/speckit-implement` 參照。

## 測試執行結果（Test Run Result）

由 pytest 透過 `--junitxml=test-results.xml` 產生，`PublishTestResults@2` 消費；不由本功能
自訂程式碼產生或解析。

| 欄位 | 說明 |
|---|---|
| test case name | 單一測試案例的識別名稱（含模組/類別/函式） |
| status | `passed` / `failed` / `error` / `skipped` |
| duration | 該測試案例執行耗時（秒） |
| （彙總）total / passed / failed | Azure DevOps Tests 摘要畫面自動彙總，對應 FR-003 的整體成功率 |

## 覆蓋率報告（Coverage Report）

由 `pytest-cov` 透過 `--cov=src --cov-report=xml` 產生 `coverage.xml`（Cobertura 格式），
`PublishCodeCoverageResults@2` 與 SonarQube Cloud（經 `sonar.python.coverage.reportPaths`）
各自消費同一份檔案。

| 欄位 | 說明 |
|---|---|
| line-rate / branch-rate | 整體覆蓋率百分比（對應 FR-004 的 pipeline 摘要呈現） |
| per-file covered/missed lines | SonarQube Cloud 介面用以標示未覆蓋的程式碼位置（對應 FR-005、SC-003） |

## 效能量測樣本（Performance Sample）

由 `benchmarks/measure_once.py` 針對單次 `bench_driver.py` 執行產生，以一行 JSON 印至
stdout，供 `benchmarks/run_benchmarks.py` 解析（詳細 JSON schema見 `contracts/`）。

| 欄位 | 型別 | 說明 |
|---|---|---|
| `run_index` | int | 第幾次執行（1–10），由協調者賦予，不由 `measure_once.py` 自行決定 |
| `response_time_s` | float | 該次 `bench_driver.py` 執行的 wall-clock 總時間（秒），`time.perf_counter()` 量得 |
| `cpu_time_s` | float | 該次執行的 CPU 時間（秒），`ru_utime + ru_stime`（`RUSAGE_CHILDREN`） |
| `max_rss_kb` | int | 該次執行的峰值記憶體用量（KB），`ru_maxrss`（`RUSAGE_CHILDREN`） |
| `ok` | bool | 該次執行是否成功完成一局（`bench_driver.py` 結束碼為 0） |
| `error` | str \| null | 失敗時的簡短錯誤訊息；成功時為 `null` |

**驗證規則**：

- 10 筆樣本的 `run_index` MUST 為 1 到 10 的不重複整數。
- 平均值計算（見 Performance Summary）MUST 只採計 `ok == true` 的樣本；若全部樣本皆失敗，
  平均值欄位 MUST 標示為無法計算（例如 `null`），而非以 0 代表「表現良好」。

## 效能量測摘要（Performance Summary）

由 `run_benchmarks.py` 彙總 10 筆 Performance Sample 而得，寫入 `benchmark_summary.md`。

| 欄位 | 型別 | 說明 |
|---|---|---|
| `sample_count` | int | 嘗試執行的樣本數（固定為 10） |
| `ok_count` | int | 成功完成一局的樣本數 |
| `avg_response_time_s` | float \| null | 成功樣本的平均回應時間 |
| `avg_cpu_time_s` | float \| null | 成功樣本的平均 CPU 時間 |
| `avg_max_rss_kb` | float \| null | 成功樣本的平均峰值記憶體用量 |
| `samples` | list[Performance Sample] | 供摘要表格逐列呈現，亦利於除錯 |

此摘要不設任何通過／失敗門檻（對應 FR-010）；`run_benchmarks.py` 與其所在的 pipeline 步驟
皆不得因樣本數值或個別樣本失敗而使 pipeline 整體標示為失敗（對應 FR-015，實作方式見
`research.md` D8）。
