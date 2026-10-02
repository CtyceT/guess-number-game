# Quickstart: 驗證 Azure DevOps CI 品質檢查流程

此文件為執行與驗證指南；pipeline 結構細節見 [contracts/](./contracts/)，
各步驟之間的狀態轉換見 [data-model.md](./data-model.md)。

**版本說明**：已依 2026-10-02 的技術決策更新（vmImage、Python 版本、SonarQube Cloud v4 任務與
具體連線資訊）；並加入「不得由 AI 自行 `git push`」的明確提醒。後續再依驗收範圍修正
（移除 PyYAML 依賴、改用 `.venv` 執行 pytest、標註本次不執行的驗證情境）。

## 重要提醒：驗收方式

`azure-pipelines.yml` 是 Azure DevOps 專屬 YAML，**無法在本機執行**（沒有對應的本機執行環境）。
正式驗收 MUST 透過「推送到連結此儲存庫的 Azure DevOps 專案，觀察一次實際 pipeline 執行」完成。
**`git push` 這個動作 MUST 由使用者本人操作，AI 不得自行推送**；AI 在實作階段僅負責建立／修改
`azure-pipelines.yml`、`sonar-project.properties`，並完成下方「設定檔驗證」中的本機靜態檢查。

## 前置條件

- 一個已連結此 Git 儲存庫的 Azure DevOps 專案，且已從既有的 `azure-pipelines.yml`
  建立一個 Pipeline（Azure DevOps → Pipelines → New pipeline → 選擇現有 YAML 檔）。
- 已在 Azure DevOps 組織安裝 Marketplace 延伸模組「SonarQube Cloud」（發行者：SonarSource），
  且其版本支援 v4 系列任務（`SonarCloudPrepare@4`／`SonarCloudAnalyze@4`／`SonarCloudPublish@4`）。
- 已有 SonarQube Cloud 組織 `john19960810` 與專案 `john19960810_guess_number_game_113403522`
  （對應 spec.md 的 Assumptions：專案已事先建立）。
- 已在 Azure DevOps 專案設定建立一個型別為「SonarQube Cloud」的 Service Connection，
  命名為 `sonarcloud-113403522`，其中存放 SonarQube Cloud 的驗證 token
  （**不** 寫入任何 repo 檔案，對應 FR-008）。

## 手動驗證情境（需使用者推送後於 Azure DevOps 觀察）

本次驗收範圍僅限「不需修改任何程式碼或測試、不需額外推送非 main 分支或開 Pull Request」即可
觀察到的行為；需要修改 `src/`／`tests/` 或刻意推送非 main 分支／開 PR 的情境，
標註為「本次不執行」，見下表備註與後方的排除說明。

| # | 步驟 | 預期結果 | 對應需求 | 本次是否執行 |
|---|------|----------|----------|--------------|
| 1 | 使用者推送一個 commit 到 `main` | Azure DevOps 在無人工操作下自動開始一次 pipeline 執行 | FR-001、AC-01、SC-001 | 執行 |
| 2 | 使用者推送一個 commit 到 `main` 以外的分支（例如 `feature/x`） | 不會有任何 pipeline 執行被觸發 | FR-002 | **本次不執行** |
| 3 | 使用者對 `main` 開一個 Pull Request | 不會觸發本 pipeline 的分析 | FR-011 | **本次不執行** |
| 4 | 查看階段 0（原始碼取得）的執行紀錄 | 確認使用 `fetchDepth: 0`，取得完整 git 歷史而非淺層 clone | research.md D2 | 執行 |
| 5 | 在全部既有測試通過的狀態下推送 commit | 階段 2（單元測試）顯示成功；階段 3（品質掃描）接著執行 | FR-003、AC-02 | 執行 |
| 6 | 暫時讓某個既有 pytest 測試失敗後推送 commit | Pipeline 於階段 2 標示為失敗；階段 3（品質掃描）未執行 | FR-004、FR-005、AC-02 | **本次不執行** |
| 7 | 查看步驟 1 或 5 的 pipeline 執行摘要畫面 | 可直接看到 SonarQube Cloud 的 Quality Gate 結果（PASSED／FAILED），不需另外登入 SonarQube Cloud | FR-007、AC-03、SC-003 | 執行 |
| 8 | 刻意讓本次分析觸發 Quality Gate `FAILED`（例如新增明顯的程式碼異味） | 摘要顯示 `FAILED`，但 pipeline 整體執行結果仍為成功（不因 Quality Gate 失敗而被標示為 Failed） | FR-007a | **本次不執行** |
| 9 | 於 SonarQube Cloud 專案頁面檢視本次分析涵蓋的檔案範圍 | `.specify/`、`specs/` 底下的檔案未出現在掃描結果中 | 使用者第 6 點、D7 | 執行 |
| 10 | 記錄從步驟 1 commit 推送時間到摘要出現 Quality Gate 結果的時間差 | 總耗時在 10 分鐘以內 | SC-004 | 執行 |
| 11 | 檢視本次變更的 diff | `src/guessing_game/`、`tests/` 內容未被修改 | FR-010 | 執行 |

**標註「本次不執行」的理由**（#2、#3、#6、#8）：

- 這四項都需要暫時修改 `src/`／`tests/` 下的程式碼（讓測試失敗、刻意加入程式碼異味），
  或額外推送非 main 分支、開啟 Pull Request 才能觀察。
- 修改既有遊戲程式碼或測試違反 FR-010（本功能 MUST NOT 修改任何猜數字遊戲既有的程式碼），
  也違反本次實驗規定「不得手動修改程式碼」來驗證 CI 行為。
- 額外的分支推送與 PR 會多觸發（或嘗試觸發）pipeline／分析，消耗 Azure DevOps 建置分鐘數與
  SonarQube Cloud 的分析額度，在非必要情況下應避免。
- 這些情境的正確性已由 contracts/azure-pipeline-contract.md 的「觸發契約」「階段契約」
  以書面契約描述並可供審查，不需要以實際推送重現才能驗收。

## 設定檔驗證（本機可執行的靜態檢查，非正式驗收）

本機不得以 PyYAML（或任何第三方 YAML 套件）解析 `azure-pipelines.yml` 來「驗證語法」——
安裝 PyYAML 屬於為此功能新增第三方相依，違反憲章原則 I（執行期／驗證工具僅允許標準函式庫與
`pytest`）。以下改用純文字層級的 `grep` 檢查，確認關鍵設定確實存在於檔案中；
YAML 語法本身的正確性留待正式驗收（Azure DevOps 實際解析並執行一次 pipeline）時確認。

```bash
# 確認觸發設定正確（僅 main、關閉 PR）
grep -n "include:" azure-pipelines.yml
grep -n "^pr:" azure-pipelines.yml
```

預期：`include:` 所在區塊列出 `main`；`pr:` 設定為 `none`。

```bash
# 確認 vmImage 已釘選為 ubuntu-24.04，而非浮動標籤 ubuntu-latest
grep -n "vmImage" azure-pipelines.yml
```

預期：輸出包含 `ubuntu-24.04`，不含 `ubuntu-latest`。

```bash
# 確認 SonarQube Cloud 任務為 v4 系列
grep -nE "SonarCloud(Prepare|Analyze|Publish)@" azure-pipelines.yml
```

預期：三個任務皆為 `@4`，不含 `@3` 或其他版本。

```bash
# 確認 sonar-project.properties 不含常見的機密關鍵字
grep -iE "token|password|secret" sonar-project.properties
```

預期：無輸出（grep 回傳非零結束碼），代表檔案中沒有明文機密。

```bash
# 確認已排除 spec-kit 文件目錄
grep -n "sonar.exclusions" sonar-project.properties
```

預期：輸出包含 `.specify/**` 與 `specs/**`。

## 既有測試仍需通過（本機可執行）

系統內建的 `python3` 為 3.8（且未安裝 `pytest`），與專案要求的 Python 3.11+ 不符；
本機驗證 MUST 使用專案既有的 `.venv`（3.12.14，已安裝 `pytest`），而非系統 `python3`：

```bash
.venv/bin/python -m pytest
```

預期：本功能未修改任何程式碼，既有全部測試（`tests/unit`、`tests/integration`）應維持原本的
通過狀態（對應 Constitution Check：原則 IV 未被破壞）。此步驟驗證的是「既有測試未被破壞」，
**不等同於** 正式驗收（正式驗收仍須由使用者推送後在 Azure DevOps 觀察，見上方「重要提醒」）。
