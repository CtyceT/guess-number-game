# Contract: azure-pipelines.yml

此文件定義 `azure-pipelines.yml`（儲存庫根目錄）對 Azure DevOps 呈現的「契約」：
觸發條件、階段順序、以及每個階段對外可觀察的行為。實作須符合本契約；
調整任務版本號在同一大版本內的 patch（例如內部 build 號）不視為破壞契約，
但改變觸發範圍、階段順序、失敗語意，或更換 `SonarCloudPrepare`/`SonarCloudAnalyze`/
`SonarCloudPublish` 的主版本號（v4），則視為破壞契約，須回頭更新本文件與 spec。

**版本說明**：已依 2026-10-02 的技術決策更新（vmImage 固定、checkout fetchDepth、Python 3.12、
SonarQube Cloud v4 任務與具體連線資訊）。

## 觸發契約（對應 FR-001、FR-002、FR-011）

| 項目 | 必要設定 | 可觀察行為 |
|------|----------|------------|
| Push 觸發範圍 | `trigger.branches.include: [main]` | 推送至 `main` 自動啟動一次 pipeline 執行；推送至任何其他分支不啟動 |
| PR 觸發 | `pr: none` | 開啟或更新任何 Pull Request 皆不啟動本 pipeline 的分析 |

## 執行環境契約

| 項目 | 必要設定 | 說明 |
|------|----------|------|
| 代理映像 | `pool.vmImage: 'ubuntu-24.04'` | **固定版本號**，不得使用浮動標籤 `ubuntu-latest`（2026/10/19 起該標籤將改指向 Ubuntu 26，見 research.md D2） |

## 階段契約（循序，前一階段失敗則後續階段不執行；階段 1 的「掃描前置設定」例外說明見下）

### 階段 0：原始碼取得

- **設定**：`checkout: self`，`fetchDepth: 0`
- **成功輸出**：工作目錄具備完整 git 歷史（非淺層 clone）
- **失敗語意**：checkout 失敗 → pipeline 執行結果為 Failed，不進入階段 1
- **理由**：SonarQube Cloud 分析（新程式碼判定、blame 等）需要完整歷史，見 research.md D2

### 階段 1：掃描前置設定（對應 US3，但先於單元測試執行）

- **輸入**：階段 0 完成後的工作目錄；`sonar-project.properties`
  （見 [sonar-config-contract.md](./sonar-config-contract.md)）；
  名為 `sonarcloud-113403522` 的 Service Connection
- **任務**（**v4** 系列，v3 已棄用不得使用）：

  ```yaml
  - task: SonarCloudPrepare@4
    inputs:
      SonarCloud: 'sonarcloud-113403522'
      organization: 'john19960810'
      scannerMode: 'cli'
      configMode: 'file'
      configFile: 'sonar-project.properties'
  ```

- **成功輸出**：掃描設定（scanner 環境變數）已就緒，供階段 4 的 `SonarCloudAnalyze@4` 使用
- **失敗語意**：Prepare 任務失敗 → pipeline 執行結果為 Failed，不進入階段 2
- **重要說明（對應 FR-005 的範圍界定）**：本階段依 SonarQube Cloud 官方任務的既定順序要求，
  **必須**排在建置／測試步驟之前執行；它只負責寫入掃描設定，**不** 執行實際的程式碼分析或
  結果上傳。因此本階段 **不** 視為 FR-005／Edge Case 所稱的「品質掃描步驟」本身——
  真正受「僅在測試通過後才執行」規範約束的是階段 4（`SonarCloudAnalyze@4`／
  `SonarCloudPublish@4`）。此範圍界定已記錄於 spec.md 的 Assumptions。

### 階段 2：環境建置

- **輸入**：階段 1 完成後的工作目錄；pipeline 執行環境（`ubuntu-24.04`）
- **任務**：`UsePythonVersion@0`（`versionSpec: '3.12'`）、安裝 `pytest`
- **成功輸出**：環境具備 Python 3.12 與 `pytest` 可執行
- **失敗語意**：任一安裝步驟失敗 → pipeline 執行結果為 Failed，不進入階段 3

### 階段 3：單元測試（對應 US2、AC-02）

- **輸入**：階段 2 的環境；專案既有 `tests/unit`、`tests/integration`
- **任務**：`python -m pytest`（專案既有執行方式，依賴 `pyproject.toml` 的
  `pythonpath`／`testpaths` 設定）
- **成功輸出**：全部既有 pytest 測試通過（結束碼 0）
- **失敗語意**：任一測試失敗或測試執行本身出錯（結束碼非 0）→ pipeline 執行結果為 Failed，
  不進入階段 4
- **明確排除**：不產生、不發布測試覆蓋率報告（FR-009）

### 階段 4：品質掃描與發布（對應 US3、AC-03）

- **輸入**：階段 3 成功後的原始碼（即 `src/`、`tests/` 內容，未被本功能修改）；
  階段 1 已準備好的掃描設定
- **任務**（**v4** 系列，v3 已棄用不得使用）：

  ```yaml
  - task: SonarCloudAnalyze@4

  - task: SonarCloudPublish@4
    inputs:
      pollingTimeoutSec: '300'
  ```

- **成功輸出**：
  - 分析結果上傳至 SonarQube Cloud 專案 `john19960810_guess_number_game_113403522`（FR-006）
  - Pipeline 執行摘要出現 Quality Gate 結果（`PASSED` 或 `FAILED`）（FR-007）
- **失敗語意**：僅當掃描／上傳本身無法完成（連線失敗、逾時超過 300 秒等）時，
  pipeline 執行結果為 Failed；Quality Gate 結果為 `FAILED` **不** 構成 pipeline 失敗（FR-007a，
  `SonarCloudPublish@4` 本無「依 Quality Gate 結果讓任務失敗」的輸入選項，見 research.md D4/D5）

## 整體契約（對應 SC-004）

從 push 到 main，到 pipeline 執行摘要顯示 Quality Gate 結果，總耗時 MUST 落在 10 分鐘以內
（五個階段的加總執行時間，在既有的小型程式碼庫規模下）。

## 機密契約（對應 FR-008）

`azure-pipelines.yml` 與 `sonar-project.properties` 中 MUST NOT 出現任何密碼或 token 明文；
SonarQube Cloud 驗證資訊僅透過名為 `sonarcloud-113403522` 的 Azure DevOps Service Connection
（型別：SonarQube Cloud／SonarCloud）提供。

## 驗收方式契約（對應使用者第 8 點、research.md D8）

本檔案為 Azure DevOps 專屬 YAML，MUST NOT 嘗試在本機以一般指令「執行」此檔案本身
（可做的是語法層級檢查，見 quickstart.md）。驗收 MUST 以實際推送後、在 Azure DevOps
觀察一次真實 pipeline 執行為準；`git push` 的動作 MUST 由使用者本人執行，不得由 AI 代為執行。
