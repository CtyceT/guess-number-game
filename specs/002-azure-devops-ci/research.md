# Research: Azure DevOps CI 品質檢查流程

Technical Context 中沒有 `NEEDS CLARIFICATION`；以下記錄各項設計決策與理由，供實作與審查對照。

**版本說明**：本文件已依使用者於 2026-10-02 提供的 8 項技術決策全面更新（vmImage 改為固定
`ubuntu-24.04`、Python 版本改為 3.12、SonarQube Cloud 任務由 v3 升級為 v4、新增 `fetchDepth: 0`
checkout 設定、SonarQube Cloud 具體連線資訊、排除 spec-kit 目錄）。舊版決策若與本版衝突，
一律以本版為準。

## D1. 觸發設定（對應 FR-001、FR-002、FR-011、AC-01）

- **Decision**: `azure-pipelines.yml` 使用 `trigger: branches: include: [main]` 僅於 main 分支的
  push 觸發 CI，並明確加上 `pr: none` 關閉 Pull Request 觸發。
- **Rationale**: Azure DevOps YAML pipeline 預設行為是「所有分支的 push 與所有 PR 皆觸發」，
  若不顯式設定會同時違反 FR-002（非 main 分支不得觸發）與 FR-011（不得對 PR 分析）。
  顯式列出 `include: [main]` 比僅依賴預設更不容易因分支改名、新增分支而意外跑錯行為。
- **Alternatives considered**: 僅設定 `trigger: - main`（簡寫）——效果相同但省略 `pr: none`
  時仍會對 PR 觸發獨立的 PR 驗證建置，違反 FR-011，故兩者都需要明確寫出。

## D2. 執行環境、Python 版本與 Checkout 設定（對應 Technical Context）

- **Decision**:
  - `pool: vmImage: 'ubuntu-24.04'`（Microsoft 代管代理，**固定版本號，不用 `ubuntu-latest`**）。
  - 第一個步驟明確使用 `checkout: self` 並設定 `fetchDepth: 0`（取得完整 git 歷史，而非預設的
    淺層 clone）。
  - `UsePythonVersion@0` 任務固定 `versionSpec: '3.12'`。
- **Rationale**:
  - **vmImage 釘選**：`ubuntu-latest` 是會隨時間改指向不同 Ubuntu 版本的「浮動標籤」；
    依使用者提供的資訊，該標籤將於 2026/10/19 改指向 Ubuntu 26。若沿用 `ubuntu-latest`，
    pipeline 行為可能在未經測試的情況下因代理作業系統版本跳動而改變（例如預裝套件版本、
    glibc 版本），釘選為目前驗證過的 `ubuntu-24.04` 可避免此風險；日後需要升級時，
    可在明確評估後主動修改版本號，而不是被動被 Microsoft 的標籤重新導向。
  - **`fetchDepth: 0`**：SonarQube Cloud 的分析（例如新程式碼判定、blame 資訊、歷史趨勢）
    需要完整的 git 歷史；Azure DevOps 預設 checkout 只抓最新一次 commit（淺層 clone），
    會導致 Sonar 分析時出現歷史不完整的警告或新程式碼判定失準，故明確設定 `fetchDepth: 0`。
  - **Python 3.12**：與專案現有的本機開發環境（`.venv`，`python --version` 為 3.12.14）一致，
    避免「本機可過但 CI 版本不同導致行為差異」的落差；3.12 仍滿足憲章原則 I 的
    「Python 3.11 或更新版本」。
- **Alternatives considered**:
  - 沿用 `ubuntu-latest`——省去日後手動升級的動作，但犧牲了可預測性，與使用者明確提出的風險
    疑慮相牴觸，故不採用。
  - 自架 self-hosted agent——對本練習專案而言是不必要的維運負擔，不符合「維持精簡」。
  - 維持 Python 3.11（憲章最低需求）——與本機 `.venv`（3.12）不一致，可能遺漏僅在 3.12
    出現的行為差異，故改採與本機一致的 3.12。

## D3. 測試執行與失敗判定（對應 FR-003、FR-004、FR-005、AC-02）

- **Decision**: 單一 Script 任務：`python -m pip install --upgrade pip pytest`，
  接著以專案既有的執行方式 `python -m pytest`（依賴既有 `pyproject.toml` 的
  `pythonpath = ["src"]`、`testpaths = ["tests"]`，不需額外參數）。不加入 `--cov` 或任何 coverage
  外掛，呼應 FR-009。不另外發布 JUnit XML 測試結果（不加入 `PublishTestResults@2`）。
- **Rationale**: `pytest` 在任一測試失敗時以非零結束碼結束，Azure DevOps 的任務即自動標示為失敗，
  進而讓整個 job／pipeline 標示為失敗並停止後續步驟（預設 `continueOnError: false`），
  已自然滿足 FR-004／FR-005，不需要額外的「失敗判定」邏輯。
  省略 JUnit 發布步驟可維持 pipeline 精簡（呼應憲章「維持精簡，避免預先設計與不必要的抽象」）；
  spec 的 AC-02 僅要求「任一測試失敗則 pipeline 失敗」，未要求逐筆測試結果呈現於 Tests 分頁。
- **Alternatives considered**: 加入 `pytest --junitxml=...` + `PublishTestResults@2`——可提供更細緻的
  逐筆測試檢視，但屬於本次 spec 未要求的加值功能，先不加入以避免範圍蔓延；
  若未來需要，可在不影響本次契約的情況下另行新增。

## D4. SonarQube Cloud 整合方式與版本（對應 FR-006、FR-007、FR-008、AC-03）

- **Decision**: 使用 Azure DevOps Marketplace 的官方延伸模組「SonarQube Cloud」
  （發行者：SonarSource）之 **v4** 系列任務（v3 已棄用，不得使用）。Pipeline 依序呼叫：

  ```yaml
  - task: SonarCloudPrepare@4
    inputs:
      SonarCloud: 'sonarcloud-113403522'
      organization: 'john19960810'
      scannerMode: 'cli'
      configMode: 'file'
      configFile: 'sonar-project.properties'

  # ...（環境建置、pytest 任務，見 D2／D3）...

  - task: SonarCloudAnalyze@4

  - task: SonarCloudPublish@4
    inputs:
      pollingTimeoutSec: '300'
  ```

  其中 `SonarCloud` 輸入欄位對應的 Service Connection 名稱為 `sonarcloud-113403522`；
  `organization` 為 `john19960810`；`scannerMode` 為 `cli`（獨立 scanner，而非 MSBuild／
  Maven／Gradle 整合模式，因本專案是純 Python 專案）；`configMode` 為 `file`，
  實際掃描參數（含 `sonar.projectKey`）改放在 `sonar-project.properties`（見 D7），
  故 `SonarCloudPrepare@4` 不需要也不設定 `cliProjectKey`。
- **欄位名稱核實**（對應使用者要求第 7 點，核對官方文件「List of SonarQube tasks」）：
  - 服務連線的輸入欄位名稱是 **`SonarCloud`**（SonarQube Cloud 延伸模組專屬），
    **不是** `SonarQube`（那是給另一套「SonarQube」延伸模組／自架 SonarQube Server 用的
    `SonarQubePrepare@N` 系列任務的欄位名稱，兩者是 SonarSource 發布的不同 Marketplace
    延伸模組，任務名稱與輸入欄位皆不通用，不可混用）。
  - `configMode: 'file'` 時，`configFile` 預設值本就是 `'sonar-project.properties'`，
    此處明確寫出以利閱讀，但非必要。
  - `cliProjectKey` 只有在 `scannerMode: 'cli'` 且 `configMode: 'manual'` 時才需要
    （用來取代設定檔）；本設計採 `configMode: 'file'`，專案金鑰一律由
    `sonar-project.properties` 的 `sonar.projectKey` 提供，`SonarCloudPrepare@4`
    因此不設定 `cliProjectKey`，避免同一份資訊在兩處重複維護。
  - `SonarCloudAnalyze@4` 不需要任何輸入（直接沿用 Prepare 階段寫入的環境變數設定）。
  - `SonarCloudPublish@4` 只有 `pollingTimeoutSec` 這個輸入需要關心；它不提供「Quality Gate
    失敗就讓任務失敗」的輸入欄位，任務本身的預設行為就是只把 Quality Gate 結果寫入
    pipeline 執行摘要、不影響任務的成功／失敗狀態（見 D5）。
- **Rationale**: 官方延伸模組原生支援「上傳分析結果到 SonarQube Cloud 專案」與「在 pipeline
  執行摘要自動產生 Quality Gate 結果區塊」兩項需求（FR-006、FR-007），不需要自行呼叫
  SonarQube Cloud Web API 或手刻摘要格式化邏輯。`pollingTimeoutSec` 設為 300 秒，
  讓分析與等待 Quality Gate 計算的時間落在 SC-004 的 10 分鐘預算內，同時避免無限等待。
  v3 已被 SonarSource 標示為棄用版本，新建立的 pipeline 應直接採用 v4，避免上線後立刻面臨
  棄用警告或功能缺口。
- **Alternatives considered**:
  - 直接使用 `sonar-scanner` CLI 搭配自行撰寫腳本呼叫 SonarQube Cloud Web API
    取得 Quality Gate 狀態並寫入摘要——需要自行處理驗證、輪詢與摘要格式，
    複雜度遠高於官方延伸模組已提供的能力，故不採用。
  - 繼續使用 v3 任務——已棄用，使用者明確排除此選項。
  - `configMode: 'manual'` + `cliProjectKey`——會讓專案金鑰同時出現在 YAML 與
    `sonar-project.properties`（若兩者都存在）兩處，增加不一致的風險，故不採用。

## D5. Quality Gate 失敗不得讓 pipeline 失敗（對應 FR-007a、Clarifications 2026-10-02 第 1 題）

- **Decision**: 依 D4 的欄位核實結果，`SonarCloudPublish@4` 本來就不提供「Quality Gate 失敗讓任務
  失敗」的輸入選項，維持任務預設設定（僅 `pollingTimeoutSec`）即可同時滿足 FR-007 與 FR-007a，
  不需要額外程式邏輯去「事後忽略」失敗狀態；pipeline 中也不額外加入任何以 Quality Gate 狀態為
  條件的失敗／中止步驟。
- **Rationale**: 使用者在 Clarifications 中明確選擇「Quality Gate 結果僅作資訊呈現，不影響
  pipeline 整體成功／失敗」。`SonarCloudPublish` 任務預設即會把 Quality Gate 結果寫入
  pipeline 執行摘要（滿足 FR-007），且其任務本身的成功／失敗只取決於「分析結果是否成功送達並
  處理完成」，與 Quality Gate 判定結果（PASSED／FAILED）無關，因此天然符合 FR-007a，
  不需要刻意關閉任何選項。
- **Alternatives considered**: 另外呼叫 SonarQube Cloud Web API 查詢 Quality Gate 狀態、
  再以條件式步驟覆寫 pipeline 結果——這會讓 pipeline 更複雜，且與官方延伸模組的既有行為
  重複，不如直接沿用任務預設來得精簡可靠。

## D6. 機密管理（對應 FR-008、限制：任何密碼／token 都不得寫入 repo）

- **Decision**: 在 Azure DevOps 專案設定中使用一個既有的「SonarQube Cloud」類型 Service
  Connection，名稱為 `sonarcloud-113403522`，SonarQube Cloud 的驗證 token 僅存放於該
  Service Connection 的加密欄位。`azure-pipelines.yml` 僅以名稱參照該 Service Connection
  （`SonarCloud: 'sonarcloud-113403522'`），不在任何 YAML 或設定檔中出現 token 明文。
- **Rationale**: Service Connection 是 Azure DevOps 原生的機密管理機制，權限可獨立授予／撤銷，
  且其值不會出現在 pipeline 執行紀錄或 repo 歷史中，直接滿足 FR-008 與使用者的限制。
- **Alternatives considered**: 使用 Pipeline 的 secret variable 直接存放 token 並手動傳給
  `sonar-scanner`——可行但需要自行處理參數傳遞與遮罩，而官方延伸模組已原生支援
  Service Connection 整合，選用延伸模組原生機制更不容易出錯。

## D7. Sonar 掃描設定的存放位置與排除範圍（對應 Project Structure、使用者第 6 點）

- **Decision**: 以獨立的 `sonar-project.properties` 檔（置於儲存庫根目錄）宣告：

  ```properties
  sonar.projectKey=john19960810_guess_number_game_113403522
  sonar.organization=john19960810
  sonar.sources=src
  sonar.tests=tests
  sonar.python.version=3.12
  sonar.exclusions=.specify/**,specs/**
  ```

  並搭配 `SonarCloudPrepare@4` 的 `configMode: 'file'`（見 D4）。
- **Rationale**:
  - 把掃描設定與 pipeline 任務參數分離，使設定檔可被其他工具（例如開發者本機執行
    `sonar-scanner` 預檢）直接讀取，也讓 `azure-pipelines.yml` 保持精簡。
  - `sonar.sources=src`、`sonar.tests=tests` 已將掃描範圍限定在這兩個目錄，`.specify/`、
    `specs/` 等 spec-kit 文件目錄本就不在掃描範圍內；額外加上 `sonar.exclusions` 是
    防禦性寫法——即使日後有人誤將 `sonar.sources` 改為倉庫根目錄（`.`），這條排除規則
    仍能確保 spec-kit 文件不會被當成程式碼掃描，符合使用者的明確要求。
  - `sonar.python.version=3.12` 對齊 D2 的 Python 版本決策，確保 Sonar 的 Python
    分析規則套用正確的語言版本行為。
- **Alternatives considered**: 全部參數內嵌於 `SonarCloudPrepare@4` 的 `extraProperties` 字串——
  省去一個檔案，但會讓 YAML 任務參數變長且不易本機驗證，故不採用。
  僅靠 `sonar.sources`／`sonar.tests` 隱含排除、不另寫 `sonar.exclusions`——較精簡，
  但防禦性較弱，使用者明確要求「不掃描 .specify、specs 等檔案」，故選擇顯式排除以降低
  日後設定漂移的風險。

## D8. 驗收方式（對應使用者第 8 點）

- **Decision**: 此 pipeline YAML 無法在本機以一般 `pytest`／`python` 指令執行驗證
  （`azure-pipelines.yml` 的語法與任務僅由 Azure DevOps 執行期解讀）。驗收方式是：
  由使用者本人將變更推送到連結此儲存庫的 Azure DevOps 專案，觀察一次實際的 pipeline 執行
  （見 quickstart.md 的手動驗證情境）。**本功能的實作階段（`/speckit-implement`）不得由 AI
  自行執行 `git push`**；AI 僅負責在本機建立／修改 `azure-pipelines.yml` 與
  `sonar-project.properties`，並完成語法層級的靜態檢查（例如 YAML 可被解析、
  設定檔內無明文機密關鍵字），實際推送與線上驗證由使用者操作。
- **Rationale**: 避免 AI 代為推送造成非預期的實際 CI 執行（例如消耗 Azure DevOps 的建置分鐘數、
  觸發 SonarQube Cloud 分析配額），且推送通常涉及使用者對遠端分支策略、PR 流程的掌控權，
  屬於應由人工確認的動作。
- **Alternatives considered**: AI 推送後自行用 `az pipelines` CLI 查詢執行結果——需要額外的
  Azure DevOps 認證與 CLI 設定，且仍與使用者「不要自行 git push」的明確指示牴觸，故不採用。
