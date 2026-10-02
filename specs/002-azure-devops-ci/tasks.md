---

description: "Task list template for feature implementation"
---

# Tasks: Azure DevOps CI 品質檢查流程

**Input**: Design documents from `/specs/002-azure-devops-ci/`

**Prerequisites**: plan.md、spec.md、research.md、data-model.md、contracts/、quickstart.md（皆已存在）

**Tests**: 本功能未要求產生自動化測試（spec.md 範圍外明確排除覆蓋率報告；pipeline 本身無法在本機
執行），故不包含獨立的測試任務；驗證改以 Polish 階段的靜態檢查 + 使用者實際推送驗收取代。

**Organization**: 任務依 spec.md 的三個 User Story（P1～P3）分組；全部任務集中編輯兩個檔案
（`azure-pipelines.yml`、`sonar-project.properties`），同一檔案內的任務依序執行（無 `[P]`）。

**⚠️ 硬性限制**（對應 plan.md Constraints、research.md D8、quickstart.md 重要提醒）：
本功能的 YAML 無法在本機執行；**AI 執行這些任務時 MUST NOT 執行 `git push`**，
正式驗收只能由使用者推送後在 Azure DevOps 觀察。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可平行執行（不同檔案、無相依）
- **[Story]**: 對應的 User Story（US1、US2、US3）

## Path Conventions

單一專案；本功能僅新增儲存庫根目錄的兩個設定檔：`azure-pipelines.yml`、`sonar-project.properties`。
不涉及 `src/`、`tests/`（FR-010）。

---

## Phase 1: Setup

**Purpose**: 建立本功能唯一的 pipeline 檔案骨架

- [X] T001 建立 `azure-pipelines.yml`（儲存庫根目錄）：設定 pipeline 名稱、單一 job、
      `pool: vmImage: 'ubuntu-24.04'`（**固定版本號，不得使用 `ubuntu-latest`**，
      理由見 research.md D2：該標籤將於 2026/10/19 改指向 Ubuntu 26）、空的 `steps: []`。
      此為後續所有任務共同編輯的唯一檔案。對應：plan.md Project Structure、research.md D2。

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 本功能依賴的外部（非 repo 內）前置條件；三個 User Story 的實際驗收皆依賴這些條件成立

**⚠️ CRITICAL**: 以下為人工／Azure DevOps 介面設定，不在本次 repo 變更範圍內，但必須在推送驗收前
備妥，否則即使 YAML 正確也無法觀察到預期行為

- [X] T002 [P] 確認下列 Azure DevOps／SonarQube Cloud 前置條件已就緒（人工檢查，對應
      `specs/002-azure-devops-ci/quickstart.md` 的「前置條件」小節，非程式碼變更）：
      (a) 此 Git 儲存庫已連結一個 Azure DevOps 專案，且已從 `azure-pipelines.yml` 建立 Pipeline；
      (b) 該組織已安裝支援 v4 任務的「SonarQube Cloud」Marketplace 延伸模組；
      (c) SonarQube Cloud 組織 `john19960810` 與專案 `john19960810_guess_number_game_113403522`
      已事先建立（spec.md Assumptions）；
      (d) 已建立型別為「SonarQube Cloud」、名稱為 `sonarcloud-113403522` 的 Service Connection，
      且其中已設定有效 token（**不得** 以任何形式寫入 repo，對應 FR-008）。

      **完成**（使用者於 Azure DevOps／SonarQube Cloud 實際確認，2026-10-02）：
      SonarQube Cloud 延伸模組、Service Connection `sonarcloud-113403522`、
      SonarQube Cloud 專案 `john19960810_guess_number_game_113403522` 皆已就緒。

**Checkpoint**：T001、T002 完成後，才能開始驗證任何一個 User Story 的實際行為。

---

## Phase 3: User Story 1 - 自動觸發 CI (Priority: P1) 🎯 MVP

**Goal**: 推送 commit 到 main 分支時，Azure DevOps 在無人工操作下自動開始執行 pipeline；
推送到其他分支或開 PR 皆不觸發。

**Independent Test**: 推送一個 commit 到 `main`，觀察 Azure DevOps 是否自動開始執行 pipeline
（此時 pipeline 內容可以只是一個無實質作用的步驟，不需包含測試或掃描）。

### Implementation for User Story 1

- [X] T003 [US1] 在 `azure-pipelines.yml` 新增頂層 `trigger` 與 `pr` 設定：
      `trigger: branches: include: [main]`、`pr: none`
      （對應 FR-001、FR-002、FR-011、AC-01；research.md D1；
      contracts/azure-pipeline-contract.md 觸發契約）。
- [X] T004 [US1] 在 `azure-pipelines.yml` 的 `steps:` 中加入一個最小可觀察步驟（例如
      `- script: echo "CI pipeline triggered"`），取代 T001 的空 `steps: []`，
      使 pipeline 觸發後有實際可見的執行紀錄，供本故事獨立驗證（之後會在 US2、US3 被
      真正的步驟取代／擴充，不需要另外刪除）。

**Checkpoint**：此時獨立推送到 main 應可觀察到 pipeline 自動執行；推送到其他分支或開 PR
不應觸發（quickstart.md 手動驗證情境 #1；#2、#3 本次標註不執行，見 quickstart.md 說明）。

---

## Phase 4: User Story 2 - 執行既有單元測試 (Priority: P2)

**Goal**: Pipeline 以專案既有方式執行全部 pytest 測試；任一測試失敗即讓 pipeline 失敗。

**Independent Test**: 在既有測試全數通過的狀態下觸發 pipeline，確認全部 pytest 測試被執行且
pipeline 標示成功；（本次驗收範圍不含「刻意讓測試失敗」的情境，見 quickstart.md 說明）。

### Implementation for User Story 2

- [X] T005 [US2] 在 `azure-pipelines.yml` 中，將 T004 的佔位步驟替換為環境建置步驟：
      加入 `UsePythonVersion@0` 任務，`versionSpec: '3.12'`（與本機 `.venv` 一致，
      對應 plan.md Technical Context、research.md D2）。
- [X] T006 [US2] 緊接著 T005，在 `azure-pipelines.yml` 新增一個 script 步驟，依序執行
      `python -m pip install --upgrade pip pytest` 與 `python -m pytest`
      （專案既有執行方式，依賴既有 `pyproject.toml` 的 `pythonpath=["src"]`、
      `testpaths=["tests"]`；不加任何 `--cov` 參數）。
      任一測試失敗時 `pytest` 回傳非零結束碼，Azure DevOps 任務自動標示失敗並中止後續步驟
      （對應 FR-003、FR-004、FR-005、AC-02；research.md D3）。

**Checkpoint**：此時獨立觸發 pipeline 應可觀察到：完整執行 `tests/unit`、`tests/integration`
全部既有測試，全數通過則 pipeline 成功（quickstart.md 手動驗證情境 #5；#6「刻意讓測試失敗」
本次標註不執行）。

---

## Phase 5: User Story 3 - 程式碼品質掃描 (Priority: P3)

**Goal**: 測試通過後，以 SonarQube Cloud v4 任務掃描程式碼、上傳結果，並在 pipeline 摘要顯示
Quality Gate 結果（僅資訊呈現，不影響 pipeline 成敗）。

**Independent Test**: 在測試已通過的 pipeline 執行中，確認掃描結果上傳至 SonarQube Cloud 專案，
且可在 pipeline 執行摘要看到 Quality Gate 結果，無需另外登入 SonarQube Cloud。

### Implementation for User Story 3

- [X] T007 [P] [US3] 建立 `sonar-project.properties`（儲存庫根目錄），內容為：

      ```properties
      sonar.projectKey=john19960810_guess_number_game_113403522
      sonar.organization=john19960810
      sonar.sources=src
      sonar.tests=tests
      sonar.python.version=3.12
      sonar.exclusions=.specify/**,specs/**
      ```

      MUST NOT 包含任何 token／密碼／其他機密值；MUST NOT 設定任何 coverage 相關欄位
      （對應 FR-006、FR-008、FR-009；data-model.md SonarQube Cloud 掃描設定；
      contracts/sonar-config-contract.md）。與 T001～T006 為不同檔案，可平行進行。
- [X] T008 [US3] 在 `azure-pipelines.yml` 的 `steps:` **最前面**（即在 T005 的
      `UsePythonVersion@0` 之前）插入 `checkout: self`，並設定 `fetchDepth: 0`
      （取得完整 git 歷史，供 SonarQube Cloud 分析使用；對應 research.md D2；
      依賴 T001 已存在的 `steps:` 區塊）。
- [X] T009 [US3] 緊接在 T008 的 checkout 之後、T005 的 `UsePythonVersion@0` 之前，
      新增 `SonarCloudPrepare@4` 任務：

      ```yaml
      - task: SonarCloudPrepare@4
        inputs:
          SonarCloud: 'sonarcloud-113403522'
          organization: 'john19960810'
          scannerMode: 'cli'
          configMode: 'file'
          configFile: 'sonar-project.properties'
      ```

      欄位名稱已依官方文件核實：服務連線欄位為 `SonarCloud`（非 `SonarQube`，兩者分屬不同
      Marketplace 延伸模組，見 research.md D4）。`configMode: 'file'` 時不設定 `cliProjectKey`，
      專案金鑰一律由 T007 的 `sonar-project.properties` 提供。依賴 T007、T008。
      （注意：Prepare 必須排在建置／測試步驟之前是 SonarQube Cloud 任務的既定順序要求，
      此步驟僅寫入掃描設定、尚未執行實際分析，故不違反 FR-005「測試通過後才執行品質掃描」的
      意圖——真正的分析與上傳在 T010、T011。）
- [X] T010 [US3] 在 `azure-pipelines.yml` 的 T006 pytest 步驟**之後**，新增
      `SonarCloudAnalyze@4` 任務（不需要任何輸入欄位）。依賴 T006、T009。
- [X] T011 [US3] 緊接在 T010 之後，新增 `SonarCloudPublish@4` 任務：

      ```yaml
      - task: SonarCloudPublish@4
        inputs:
          pollingTimeoutSec: '300'
      ```

      **不** 設定任何「依 Quality Gate 結果讓任務失敗」的選項——`SonarCloudPublish@4`
      本身並未提供此輸入欄位，預設行為即是只把 Quality Gate 結果寫入 pipeline 執行摘要、
      不影響任務／pipeline 的成敗（對應 FR-006、FR-007、FR-007a；research.md D4、D5；
      Clarifications 2026-10-02 第 1 題）。依賴 T010。

**Checkpoint**：此時完整 pipeline 依序為 checkout(fetchDepth:0) → SonarCloudPrepare@4 →
UsePythonVersion(3.12) → pip install + pytest → SonarCloudAnalyze@4 → SonarCloudPublish@4；
推送到 main 且測試通過後，pipeline 摘要應顯示 Quality Gate 結果，且分析範圍不含 `.specify/`、
`specs/`（quickstart.md 手動驗證情境 #4、#5、#7、#9、#10、#11；#8「刻意觸發 Quality Gate
FAILED」本次標註不執行）。

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 推送前的本機靜態檢查，以及正式驗收的交接

- [X] T012 [P] 執行 `specs/002-azure-devops-ci/quickstart.md`「設定檔驗證」小節列出的全部
      `grep` 檢查（觸發設定、`vmImage` 釘選、SonarCloud 任務版本為 `@4`、
      `sonar-project.properties` 無機密關鍵字、`sonar.exclusions` 已排除 spec-kit 目錄），
      確認針對 `azure-pipelines.yml`、`sonar-project.properties` 全數通過。
      **不得** 安裝或使用 PyYAML 等第三方套件做 YAML 語法驗證（違反憲章原則 I）。
- [X] T013 [P] 執行 `.venv/bin/python -m pytest`，確認既有全部測試（`tests/unit`、
      `tests/integration`）維持原本通過狀態（對應 Constitution Check 原則 IV 未被破壞；
      quickstart.md「既有測試仍需通過」）。
- [X] T014 檢視本次變更的 `git diff`，確認僅新增／修改 `azure-pipelines.yml`、
      `sonar-project.properties` 兩個檔案，`src/`、`tests/`、`pyproject.toml` 未被觸碰
      （對應 FR-010）。
- [X] T015 將以上變更交付使用者本人推送到 `main`（**AI MUST NOT 執行 `git push`**，
      對應 plan.md Constraints、research.md D8）；使用者推送後，依
      `specs/002-azure-devops-ci/quickstart.md`「手動驗證情境」表中標註「執行」的項目
      （#1、#4、#5、#7、#9、#10、#11）在 Azure DevOps 實際觀察驗收結果。

      **驗收結果**（使用者於 Azure DevOps／SonarQube Cloud 實際執行，2026-10-02）：

      - **#1 自動觸發**：run #20261002.2、.3、.4 皆為 Individual CI，push 到 `main` 後
        無人工介入自動執行，全部成功（FR-001、AC-01、SC-001）。
      - **#4 fetchDepth**：SonarQube Cloud 的 issue 能顯示作者與日期（git blame 資訊），
        代表 `fetchDepth: 0` 確實取得完整 git 歷史（research.md D2）。
      - **#5 測試通過後才執行掃描**：pipeline 各步驟依序成功，`pytest` 通過後才執行
        `SonarCloudAnalyze@4` 與 `SonarCloudPublish@4`（FR-003～FR-005、AC-02）。
      - **#7 摘要顯示 Quality Gate**：pipeline 的 Extensions 分頁出現「SonarQube Cloud
        Analysis Report」，但結果為 **`none`（Not computed）**——**已知問題**，非本功能實作
        缺陷：原因是 SonarQube Cloud 專案由分析自動建立，缺少 New Code definition，
        而預設的 Sonar way Quality Gate 條件全部針對「新程式碼」，無新程式碼定義時無法計算，
        因此顯示 Not computed。修正方式需由 SonarQube Cloud 管理員在該專案設定
        New Code definition，屬於 repo 外、SonarQube Cloud 專案層級的設定，不在本功能
        （`azure-pipelines.yml`／`sonar-project.properties`）變更範圍內；已回報給專案管理員
        （學長）後續處理。FR-007（摘要顯示 Quality Gate 結果）本身的「顯示機制」已驗證運作
        正常，僅計算結果因外部專案設定而為 `none`。
      - **#9 排除範圍**：SonarQube Cloud 顯示 144 Lines of Code，語言僅 Python，
        `.specify/`、`specs/` 未被掃描（使用者第 6 點、research.md D7）。
      - **#10 耗時**：每次執行約 1 分 10 秒至 1 分 23 秒，遠低於 10 分鐘門檻（SC-004）。
      - **#11 未修改程式碼**：`src/`、`tests/`、`pyproject.toml` 皆未變動（FR-010）。

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**：無相依，立即可開始（T001）。
- **Foundational (Phase 2)**：T002 為人工確認項目，可與 T001 平行處理，但 MUST 在任何一個
  User Story 的「實際驗收」之前完成（不阻擋 repo 內的檔案編輯工作）。
- **User Stories (Phase 3–5)**：皆依賴 T001（`azure-pipelines.yml` 必須已存在）。
  三個故事在檔案內容上是累加關係（US2 擴充 US1 的檔案、US3 再擴充 US2 的檔案），
  因此 **MUST 依優先序（US1 → US2 → US3）循序完成**，不可平行進行 repo 編輯；
  但每個故事完成後都可獨立觀察、獨立驗收（見各自 Checkpoint）。
- **Polish (Phase 6)**：依賴 US1、US2、US3 皆完成。

### Within Each User Story

- US1：T003 → T004（同檔案，依序）。
- US2：T005 → T006（同檔案，依序；且依賴 US1 的 T004 已存在，以便被替換）。
- US3：T007 與 T008 可平行（不同檔案）；T008 → T009 → （US2 的 T006）→ T010 → T011
  （同檔案 `azure-pipelines.yml` 內依序插入；T009 依賴 T007 的設定檔已存在）。

### Parallel Opportunities

- T002（人工確認前置條件）可與 T001（建立檔案骨架）平行進行。
- T007（建立 `sonar-project.properties`）可與 T008（編輯 `azure-pipelines.yml` 插入 checkout）
  平行進行，兩者是不同檔案。
- T012、T013（Polish 階段的兩種本機檢查）可平行執行。
- 除上述外，其餘任務皆集中編輯同一個 `azure-pipelines.yml`，依序執行，不標記 `[P]`。

---

## Parallel Example: User Story 3

```bash
# T007 與 T008 可同時進行（不同檔案）：
Task: "建立 sonar-project.properties（projectKey、organization、sources、tests、
       python.version、exclusions）"
Task: "在 azure-pipelines.yml 最前面插入 checkout: self（fetchDepth: 0）"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. 完成 Phase 1（T001）與 Phase 2（T002，人工確認前置條件）。
2. 完成 Phase 3（US1：T003、T004）。
3. **交給使用者推送並在 Azure DevOps 觀察**：確認 push 到 main 會自動觸發 pipeline
   （quickstart.md 情境 #1）。此即可作為第一個可驗收的 MVP 增量。

### Incremental Delivery

1. Setup + Foundational → US1（自動觸發，MVP）→ 使用者推送驗收。
2. 加入 US2（pytest 執行與失敗判定）→ 使用者推送驗收。
3. 加入 US3（SonarQube Cloud 掃描與 Quality Gate 顯示）→ 使用者推送驗收。
4. 每次增量都疊加在同一份 `azure-pipelines.yml` 上，不破壞前一個故事已驗證的行為。

---

## Notes

- 本功能只有兩個檔案（`azure-pipelines.yml`、`sonar-project.properties`），多數任務必須
  依序編輯同一檔案，`[P]` 標記僅出現在真正跨檔案、無相依的任務（T002、T007/T008、T012/T013）。
- 三個 User Story 在「檔案內容」上是累加關係，但各自的 Checkpoint 仍可獨立觀察與驗收，
  符合 spec.md 對每個 User Story「獨立可測試」的要求。
- **AI 執行本任務清單時，MUST NOT 執行 `git push`**；T015 的推送動作必須交回使用者本人。
- 本機無法「執行」`azure-pipelines.yml`；T012、T013 僅為推送前的靜態／既有測試檢查，
  不等同於正式驗收（正式驗收見 T015）。
