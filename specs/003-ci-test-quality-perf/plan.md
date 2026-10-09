# Implementation Plan: CI 測試品質與效能量測擴充

**Branch**: `003-ci-test-quality-perf` | **Date**: 2026-10-09 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-ci-test-quality-perf/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

擴充既有的 Azure Pipelines CI（`azure-pipelines.yml`）與 `sonar-project.properties`，在不觸發
重新定義觸發方式或 SonarQube Cloud 設定的前提下：(1) 讓 pytest 同時產出 JUnit 測試結果與
Cobertura 覆蓋率報告，並透過 `PublishTestResults@2`／`PublishCodeCoverageResults@2` 呈現在
pipeline 摘要，同時讓 SonarQube Cloud 讀到同一份覆蓋率；(2) 新增一組只依賴標準函式庫的
`benchmarks/` 腳本，透過既有遊戲介面 `cli.run()` 的 `engine`／`input_fn` 注入點（固定種子
+ 預先算好的猜測序列），完成 10 次決定性、可重現的猜數字遊戲完整執行，量測並平均 CPU
時間、記憶體峰值與回應時間，寫成 `benchmark_summary.md` 並透過
`##vso[task.uploadsummary]` 顯示於 pipeline 的 Extensions 分頁；效能量測步驟以
`continueOnError: true` 確保數值或例外都不會讓 pipeline 整體失敗。技術決策與其理由見
`research.md`。

## Technical Context

**Language/Version**: Python 3.12（沿用 `UsePythonVersion@0` 既有設定；專案憲章要求 3.11+）

**Primary Dependencies**: `pytest`、`pytest-cov`（開發／CI 限定，憲章 v1.1.0 已核准）；
`benchmarks/` 腳本僅使用標準函式庫（`subprocess`、`resource`、`time`、`statistics`、`json`、
`random`）；Azure Pipelines 任務 `PublishTestResults@2`、`PublishCodeCoverageResults@2`
（YAML 設定，非 Python 相依）

**Storage**: N/A（無持久化儲存；產出的報告檔為單次 CI 執行的暫存產物，不提交進版本控制）

**Testing**: 既有 `pytest` 測試套件不變；本功能不要求為 `benchmarks/` 腳本新增 pytest 單元
測試（CI 設定與量測工具，非遊戲核心邏輯，見下方 Constitution Check 說明）；本機與線上驗證
流程見 `quickstart.md`

**Target Platform**: Azure Pipelines，Microsoft-hosted agent，`pool.vmImage: 'ubuntu-24.04'`
（沿用既有設定）

**Project Type**: 單一 Python CLI 專案（`src/guessing_game/`）+ CI pipeline 設定 +
獨立的標準函式庫量測腳本（`benchmarks/`，非套件、不被 `src/` 匯入）

**Performance Goals**: 無數值門檻（spec 003 明確排除效能門檻；僅作趨勢追蹤用的資訊呈現）

**Constraints**:

- 效能量測工具 MUST 僅使用標準函式庫（憲章原則 I）。
- 任何步驟 MUST NOT 修改 `src/` 下任何檔案（FR-011）。
- 任何密碼／token MUST NOT 以明文寫入 repo（FR-012，沿用既有 Azure DevOps 安全機制）。
- 效能量測步驟 MUST NOT 讓 pipeline 整體失敗，無論量測數值或該步驟本身是否發生例外
  （FR-010、FR-015）。

**Scale/Scope**: 單一 pipeline 檔案 + 單一 SonarQube 設定檔的局部修改；新增 3 個
`benchmarks/` 腳本；每次 pipeline 執行固定量測 10 次樣本。

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 檢查 | 結論 |
|---|---|---|
| I. 技術棧限制 | `benchmarks/` 僅匯入標準函式庫，以及既有的 `guessing_game.engine`／`guessing_game.cli`（兩者本身亦僅用標準函式庫）；`pytest-cov` 僅用於 CI，憲章 v1.1.0 已明確允許；效能量測工具（`time`、`resource`、`subprocess`、`statistics`）皆為標準函式庫。 | **PASS** |
| II. 風格／型別／文件規範 | `benchmarks/` 新增函式皆須有完整 type hints 與 Google 風格 docstring（留給 `/speckit-tasks`／`/speckit-implement` 落實，非設計階段違反）。 | **PASS（留待實作落實）** |
| III. 邏輯與 I/O 分離（NON-NEGOTIABLE） | 不修改 `src/`，此原則規範的是遊戲核心邏輯與其 I/O 層，與本功能新增的 CI 量測工具無關；量測工具本身亦未在 `src/` 內新增違反此原則的程式碼。 | **PASS** |
| IV. 核心邏輯單元測試 | 不新增、不修改遊戲核心邏輯，既有核心邏輯測試不受影響；`benchmarks/` 屬 CI 工具而非核心邏輯，未強制要求以 pytest 覆蓋（憲章原則 IV 之範圍為遊戲核心邏輯）。 | **PASS** |
| V. 日誌規範 | 本原則規範的是「遊戲」執行期的 logging 行為；`benchmarks/` 腳本的 stdout（`measure_once.py` 的單行 JSON、`run_benchmarks.py` 的 `##vso` 摘要指令）屬 CI 工具與 Azure Pipelines 之間的資料／控制介面，非遊戲日誌，不在此原則規範範圍內。 | **PASS（範圍外，非違反）** |

**結論**：Constitution Check 全數通過，無需 Complexity Tracking 中記錄任何例外或取捨。

## Project Structure

### Documentation (this feature)

```text
specs/003-ci-test-quality-perf/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── benchmark-ipc.md       # measure_once.py → run_benchmarks.py 的 JSON 契約
│   └── pipeline-steps.md      # azure-pipelines.yml / sonar-project.properties 目標狀態
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
# 既有結構（不變）
src/
└── guessing_game/
    ├── __init__.py
    ├── __main__.py
    ├── cli.py
    └── engine.py

tests/
└── ...（既有 pytest 測試，不修改）

# 本功能新增
benchmarks/
├── bench_driver.py      # 被量測的負載：以固定種子預先算出猜測序列，透過 cli.run(engine=, input_fn=) 驅動既有遊戲介面完成一局
├── measure_once.py      # 量測包裝行程：執行一次 bench_driver.py，回報 CPU/記憶體/時間
└── run_benchmarks.py    # 協調者：呼叫 measure_once.py 10 次、彙總平均、寫 benchmark_summary.md

# 本功能修改（既有檔案，局部調整）
azure-pipelines.yml          # 新增測試結果/覆蓋率發布步驟與效能量測步驟（見 contracts/pipeline-steps.md）
sonar-project.properties     # 新增 sonar.python.coverage.reportPaths=coverage.xml
.gitignore                   # 新增 test-results.xml / coverage.xml / benchmark_summary.md
```

**Structure Decision**: 延續現有「單一專案」結構（`src/` + `tests/`），不引入新的頂層應用程式
或服務邊界。CI 量測工具以獨立的 `benchmarks/` 目錄存放（非 Python package、不被 `src/` 匯入），
與 `src/`／`tests/` 的既有分層（邏輯層／I/O 層／測試）保持正交，避免混入遊戲程式碼或測試套件。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

無違反項目，本節不適用。
