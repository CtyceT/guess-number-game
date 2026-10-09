# Contract: Azure Pipelines / SonarQube Cloud 設定異動

這份文件是 `/speckit-tasks` 與 `/speckit-implement` 要落地的目標狀態（target state），而非
此刻就套用的變更——`/speckit-plan` 只產出設計文件，不修改 repo 中的實際設定檔。

## `azure-pipelines.yml` 目標狀態

沿用既有 `trigger`、`pr`、`pool`、`checkout`、`SonarCloudPrepare@4`、`UsePythonVersion@0`
區塊不變（對應 research.md D1、D4）。變動範圍如下：

1. **既有的 pytest 步驟**（`displayName: 'Install pytest and run existing test suite'`）：

   ```yaml
   - script: |
       python -m pip install --upgrade pip pytest pytest-cov
       python -m pytest --junitxml=test-results.xml --cov=src --cov-report=xml
     displayName: 'Install pytest/pytest-cov and run test suite with coverage'
   ```

2. **在上述步驟之後、`SonarCloudAnalyze@4` 之前，新增兩個發布步驟**：

   ```yaml
   - task: PublishTestResults@2
     condition: succeededOrFailed()
     inputs:
       testResultsFormat: 'JUnit'
       testResultsFiles: 'test-results.xml'
       testRunTitle: '猜數字遊戲 pytest 結果'

   - task: PublishCodeCoverageResults@2
     condition: succeededOrFailed()
     inputs:
       summaryFileLocation: 'coverage.xml'
       pathToSources: 'src'
   ```

   `condition: succeededOrFailed()` 確保即使測試失敗，Tests 分頁仍能呈現逐案例結果
   （對應 FR-002／FR-003；pipeline 整體失敗與否仍由既有的 pytest 結束碼決定，不受此
   condition 影響）。

3. **`SonarCloudAnalyze@4` 與 `SonarCloudPublish@4` 維持不變**（此時 `coverage.xml` 已存在，
   且 `sonar-project.properties` 已指向它，見下方）。

4. **在 `SonarCloudPublish@4` 之後，新增效能量測步驟**：

   ```yaml
   - script: |
       python benchmarks/run_benchmarks.py
     displayName: 'Run guessing game performance benchmark (10 runs, stdlib only)'
     continueOnError: true
   ```

   `continueOnError: true` 是落實 FR-010／FR-015「效能數字不設門檻，量測步驟不得讓
   pipeline 失敗」的 YAML 層保險（對應 research.md D8）。

## `sonar-project.properties` 目標狀態

在既有內容後新增一行，其餘不變：

```properties
sonar.python.coverage.reportPaths=coverage.xml
```

## 新增檔案一覽（`benchmarks/`）

| 檔案 | 角色 |
|---|---|
| `benchmarks/bench_driver.py` | 被量測的負載：以固定種子預先算出猜測序列，透過 `cli.run(engine=, input_fn=)` 驅動既有遊戲介面完成一局 |
| `benchmarks/measure_once.py` | 量測包裝行程：執行一次 `bench_driver.py`，回報 CPU/記憶體/時間（見 `benchmark-ipc.md`） |
| `benchmarks/run_benchmarks.py` | 協調者：呼叫 `measure_once.py` 10 次、彙總平均、寫出 `benchmark_summary.md`、印出 `##vso[task.uploadsummary]` |

`benchmark_summary.md`、`test-results.xml`、`coverage.xml` 皆為 CI 執行時產生的報告檔，不應
提交進版本控制（`/speckit-tasks` 應包含將其加入 `.gitignore` 的任務）。

## 驗收方式

本功能的驗收是「推送後在 Azure DevOps 實際執行一次 pipeline」，核對：

- Tests 分頁：逐案例通過/失敗 + 整體成功率（US1 / FR-002 / FR-003）。
- Code Coverage 分頁：整體覆蓋率百分比（US2 / FR-004）。
- SonarQube Cloud 專案頁面：覆蓋率與未覆蓋程式碼位置（US2 / FR-005）。
- 執行摘要 Extensions 分頁：`benchmark_summary.md` 內容，含 10 次樣本平均的 CPU 時間、
  記憶體用量、回應時間（US3 / FR-007–FR-009）。
- 無論效能數值為何，pipeline 整體結果（成功/失敗）不受影響（US3 / FR-010）。

Claude 不會自行執行 `git push`；驗收所需的實際 CI 執行由使用者推送後觀察。
