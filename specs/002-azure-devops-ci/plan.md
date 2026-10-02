# Implementation Plan: Azure DevOps CI 品質檢查流程

**Branch**: `002-azure-devops-ci`（僅為功能識別名稱；實際在 `main` 上作業）| **Date**: 2026-10-02 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-azure-devops-ci/spec.md`

**Note**: 本版 plan 依使用者提供的 8 項技術決策覆寫先前版本；差異見各節內文與 research.md 的
決策更新記錄。

## Summary

為猜數字遊戲新增 Azure DevOps CI pipeline，不修改任何遊戲程式碼。Pipeline 僅由 main 分支的 push
觸發（不觸發於其他分支、不分析 Pull Request），依序執行：以 `fetchDepth: 0` checkout 完整 git
歷史 → 安裝 Python 3.12（與本機 `.venv` 一致）→ 執行全部既有 pytest 單元測試（任一失敗即讓
pipeline 失敗並中止）→ 測試通過後，以 SonarQube Cloud（SonarSource）Azure DevOps 延伸模組 v4
系列任務掃描程式碼、上傳結果至指定的 SonarQube Cloud 專案，並在 pipeline 執行摘要顯示 Quality
Gate 結果（通過／失敗皆為資訊呈現，不會讓 pipeline 本身失敗，依據 Clarifications 的決議）。
所有機密（SonarQube Cloud token）皆透過名為 `sonarcloud-113403522` 的 Azure DevOps Service
Connection 提供，不寫入 repo。

技術方法：單一 YAML pipeline 檔（`azure-pipelines.yml`，置於儲存庫根目錄）+ 一個 Sonar 掃描設定檔
（`sonar-project.properties`，明確排除 `.specify/`、`specs/` 等 spec-kit 文件目錄）。不新增任何
`src/`／`tests/` 下的程式碼或相依套件。此 YAML 無法在本機執行驗證；驗收方式是推送後於 Azure DevOps
實際執行一次 pipeline（見 quickstart.md）。**本功能的實作階段不得由 AI 自行執行 `git push`**，
push 由使用者本人操作。

## Technical Context

**Language/Version**: Python 3.12（固定版本，與本機 `.venv` 一致，而非泛用的「3.11+」；
仍滿足憲章原則 I 的「3.11 或更新版本」）；pipeline 以 `UsePythonVersion@0` 的
`versionSpec: '3.12'` 設定

**Primary Dependencies**: 無新增專案相依；CI 執行環境僅安裝 `pytest`（唯一允許的第三方相依，
沿用憲章，以專案既有的執行方式跑全部測試，不額外安裝其他套件）；SonarQube Cloud 分析透過 Azure
DevOps Marketplace 延伸模組「SonarQube Cloud」（SonarSource 發行）提供的 **v4** 系列任務
（`SonarCloudPrepare@4`、`SonarCloudAnalyze@4`、`SonarCloudPublish@4`；v3 已棄用，不得使用），
而非專案程式碼相依

**Storage**: N/A（CI 設定與分析結果皆由 Azure DevOps／SonarQube Cloud 託管，本功能不新增任何儲存）

**Testing**: pytest（執行專案既有的 `tests/unit`、`tests/integration` 全部測試，以專案既有方式
執行 `python -m pytest`，不新增測試案例、不產生 coverage 報告）

**Target Platform**: Azure DevOps Pipelines（YAML），Microsoft 代管代理，`pool.vmImage`
**固定為 `'ubuntu-24.04'`**（刻意不用 `'ubuntu-latest'`：該標籤將於 2026/10/19 改指向
Ubuntu 26，為避免代理版本在未經測試的情況下被動升級而影響 pipeline 穩定性，明確釘選版本號）

**Project Type**: CI/CD 設定（單一專案；本功能純粹新增儲存庫根目錄的設定檔，不影響
`src/guessing_game/` 的既有結構）

**Performance Goals**: SC-004：從 commit 推送到 pipeline 摘要出現 Quality Gate 結果，總時間
MUST 在 10 分鐘以內

**Constraints**:
- 任何密碼／token MUST NOT 寫入 repo（經名為 `sonarcloud-113403522` 的 Service Connection 提供）
- MUST NOT 修改任何遊戲程式碼
- MUST NOT 產生測試覆蓋率報告
- MUST NOT 對 Pull Request 觸發分析
- Quality Gate 失敗 MUST NOT 讓 pipeline 整體失敗（FR-007a）
- `sonar-project.properties` MUST 將 `.specify/`、`specs/` 等 spec-kit 文件目錄排除在掃描範圍外
- 此 YAML MUST NOT 在本機執行驗證（Azure DevOps 專屬語法，本機無對應執行環境）；
  實作階段 MUST NOT 由 AI 自行 `git push`，驗收需使用者推送後在 Azure DevOps 實際觀察執行結果

**Scale/Scope**: 單一 pipeline 檔 + 單一 Sonar 設定檔；五個循序步驟（checkout、SonarQube Cloud
掃描前置設定、環境建置、pytest、SonarQube Cloud 掃描與發布）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

本功能為 CI 設定，不觸及猜數字遊戲的執行期程式碼，故憲章中關於程式碼本身的原則（I／II／III／V）
以「是否被本功能破壞」檢視，而非新增實作：

| 原則 | 檢查結果 | 依據 |
|------|----------|------|
| I. Python 3.11+、僅標準函式庫、pytest | ✅ 通過 | Pipeline 固定 Python 3.12（滿足「3.11 或更新版本」）僅安裝 `pytest` 執行既有測試；不為 `src/guessing_game` 新增任何第三方執行期相依；SonarQube Cloud 任務是 Azure DevOps 延伸模組（宿主環境層級），非專案 Python 相依 |
| II. Google Style、type hints、docstring | ✅ 通過 | 本功能不新增或修改任何 `.py` 檔案 |
| III. 邏輯與 I/O 分離 | ✅ 通過 | 不修改 `engine.py`／`cli.py`，既有分離維持不變 |
| IV. 核心邏輯單元測試 | ✅ 通過 | Pipeline 以專案既有方式執行全部 pytest 測試且全數必須通過，不降低既有測試把關 |
| V. 日誌規範 | ✅ 通過 | 不修改任何 logging 設定 |
| 工作流程：SDD、可追溯 | ✅ 通過 | 每項設計對應 spec 的 FR／SC（見 data-model.md 與 contracts/） |

**Gate 結果**：無違規，Complexity Tracking 免填。

**Phase 1 設計後重新檢查**：設計僅新增 `azure-pipelines.yml` 與 `sonar-project.properties` 兩個
設定檔，未新增程式碼、未新增專案相依、未變更既有測試；全部原則仍通過。

## Project Structure

### Documentation (this feature)

```text
specs/002-azure-devops-ci/
├── plan.md                        # This file (/speckit-plan command output)
├── research.md                    # Phase 0 output (/speckit-plan command)
├── data-model.md                  # Phase 1 output (/speckit-plan command)
├── quickstart.md                  # Phase 1 output (/speckit-plan command)
├── contracts/                     # Phase 1 output (/speckit-plan command)
│   ├── azure-pipeline-contract.md #   azure-pipelines.yml 的觸發、階段與任務結構
│   └── sonar-config-contract.md   #   sonar-project.properties 的必要欄位
└── tasks.md                       # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
azure-pipelines.yml          # Pipeline 定義：trigger（main-only、pr: none）、
                              # checkout（fetchDepth: 0）、安裝 Python 3.12、pytest、
                              # SonarQube Cloud v4 三個任務（vmImage: ubuntu-24.04）
sonar-project.properties     # SonarQube Cloud 掃描設定（projectKey、organization、
                              # sources=src、tests=tests、python.version=3.12、
                              # 排除 .specify/、specs/）

src/guessing_game/            # 既有程式碼，本功能不修改
tests/                        # 既有測試，本功能不修改、不新增測試
```

**Structure Decision**: 採單一專案、最精簡結構（呼應憲章「維持精簡」）。本功能只在儲存庫根目錄新增
兩個設定檔（`azure-pipelines.yml`、`sonar-project.properties`），不建立額外的 `ci/`、`.azure/` 等
目錄，也不改動 `src/`、`tests/`、`pyproject.toml`。Sonar 掃描設定以獨立的
`sonar-project.properties` 檔表達（而非把所有參數內嵌於 YAML 的 `extraProperties`），
讓 pipeline 任務本身維持精簡、掃描設定可獨立於 pipeline 工具被其他介面（例如本機 `sonar-scanner`）
讀取與驗證；同一份設定檔也是「排除 `.specify/`、`specs/`」這項限制的唯一落地位置。

## Complexity Tracking

無憲章違規，無需填寫。
