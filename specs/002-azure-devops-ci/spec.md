# Feature Specification: Azure DevOps CI 品質檢查流程

**Feature Branch**: `002-azure-devops-ci`

**Created**: 2026-10-02

**Status**: Draft

**Input**: User description: "為猜數字遊戲建立 CI 流程，在 Azure DevOps 上自動檢查程式碼品質。

User Story 01 自動觸發：身為開發者，我想要在 main 分支有新的 commit 時自動執行 CI，以便每次變更都被檢查，不需要手動啟動。
User Story 02 單元測試：身為開發者，我想要 CI 執行專案既有的 pytest 單元測試，以便確認變更沒有破壞既有功能。
User Story 03 品質掃描：身為開發者，我想要 CI 使用 SonarQube Cloud 分析程式碼，並在 pipeline 摘要看到 Quality Gate 結果，以便掌握程式碼品質。

驗收準則 AC-01（對應 User Story 01）：Given 有 commit 推送到 main，When Azure DevOps 收到更新，Then pipeline 自動開始執行。
驗收準則 AC-02（對應 User Story 02）：Given pipeline 執行中，When 測試步驟執行，Then 執行全部 pytest 測試，任一測試失敗則 pipeline 失敗。
驗收準則 AC-03（對應 User Story 03）：Given 測試通過，When 品質掃描步驟執行，Then 分析結果上傳到 SonarQube Cloud 專案，且 pipeline 摘要顯示 Quality Gate 結果。

範圍外：本次不產生測試覆蓋率報告、不修改任何遊戲程式碼、不處理 Pull Request 分析。
限制：任何密碼、token 都不得寫入 repo"

## Clarifications

### Session 2026-10-02

- Q: 當 SonarQube Cloud 的 Quality Gate 結果為「失敗」時，pipeline 整體執行結果應該也標示為失敗（擋下該次 build），還是只在摘要中顯示結果、pipeline 仍視為成功？ → A: 僅顯示結果（Option A）——Quality Gate 失敗不影響 pipeline 整體成功/失敗狀態，純粹作為資訊呈現；pipeline 整體成功與否僅取決於建置與 pytest 測試步驟。
- Q: SC-004 的「可接受的回饋週期」應訂為幾分鐘以內（從 commit 推送到 pipeline 摘要顯示 Quality Gate 結果的總時間）？ → A: 10 分鐘以內。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 自動觸發 CI (Priority: P1)

身為開發者，我想要在 main 分支有新的 commit 時自動執行 CI，以便每次變更都被檢查，不需要手動啟動。

**Why this priority**: 若 CI 無法自動觸發，後續的測試與品質掃描皆無法產生持續性的保護效果；開發者仍須手動啟動才能取得回饋，違背「每次變更都被檢查」的核心目的。這是整個功能的基礎，沒有它其餘兩個使用者故事都失去自動化的價值。

**Independent Test**: 推送一個 commit 到 main 分支，觀察 Azure DevOps 是否在不需任何人工操作的情況下自動開始執行 pipeline（即使 pipeline 此時尚未包含測試或掃描步驟，也能驗證觸發行為本身）。

**Acceptance Scenarios**:

1. **Given** 有 commit 推送到 main，**When** Azure DevOps 收到更新，**Then** pipeline 自動開始執行。
2. **Given** 有 commit 推送到非 main 的其他分支，**When** Azure DevOps 收到更新，**Then** pipeline 不會被觸發。

---

### User Story 2 - 執行既有單元測試 (Priority: P2)

身為開發者，我想要 CI 執行專案既有的 pytest 單元測試，以便確認變更沒有破壞既有功能。

**Why this priority**: 在自動觸發的基礎上，執行既有測試是取得「變更是否破壞功能」回饋的核心機制，是整個 CI 流程對開發者最直接的價值來源。

**Independent Test**: 觸發一次 pipeline 執行（可手動觸發以利驗證），確認 pipeline 會執行專案中全部既有的 pytest 測試；分別驗證全部測試通過與至少一項測試失敗兩種情況下的 pipeline 結果。

**Acceptance Scenarios**:

1. **Given** pipeline 執行中，**When** 測試步驟執行，**Then** 執行全部 pytest 測試，任一測試失敗則 pipeline 失敗。
2. **Given** pipeline 執行中，**When** 全部 pytest 測試皆通過，**Then** pipeline 繼續進行後續步驟並標示測試步驟為成功。

---

### User Story 3 - 程式碼品質掃描 (Priority: P3)

身為開發者，我想要 CI 使用 SonarQube Cloud 分析程式碼，並在 pipeline 摘要看到 Quality Gate 結果，以便掌握程式碼品質。

**Why this priority**: 建立在自動觸發與測試執行之上，品質掃描提供超越「測試是否通過」的程式碼品質洞察（如壞味道、重複程式碼、潛在臭蟲），是對品質的進一步把關，價值最高但依賴前兩者先行到位。

**Independent Test**: 在測試已通過的 pipeline 執行中，確認品質掃描步驟會將分析結果上傳至 SonarQube Cloud 專案，並且可在 pipeline 執行摘要畫面看到 Quality Gate 結果（通過或失敗），無需另外登入 SonarQube Cloud 介面即可得知結果。

**Acceptance Scenarios**:

1. **Given** 測試通過，**When** 品質掃描步驟執行，**Then** 分析結果上傳到 SonarQube Cloud 專案，且 pipeline 摘要顯示 Quality Gate 結果。
2. **Given** 測試步驟失敗，**When** pipeline 因測試失敗而中止，**Then** 品質掃描步驟不會執行。

---

### Edge Cases

- 當 commit 推送到 main 以外的分支時，pipeline 不應被觸發（對應 US1 的排他情境）。
- 當 pytest 測試中有任一測試失敗時，pipeline 必須標示為失敗，且不繼續執行品質掃描步驟。
- 當 pytest 測試套件本身無法執行（例如相依套件安裝失敗）時，pipeline 必須標示為失敗，並在摘要中呈現錯誤原因。
- 當 SonarQube Cloud 服務暫時無法連線或分析逾時時，pipeline 應標示品質掃描步驟失敗，並在摘要中呈現可辨識的錯誤訊息，而不是讓 pipeline 卡住或靜默跳過。
- 當 Quality Gate 結果為「失敗」時，pipeline 摘要仍須清楚顯示該失敗結果（供開發者掌握品質狀態），但不因此回溯讓已通過的測試步驟失敗。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系統 MUST 在偵測到有新 commit 推送至 main 分支時，自動觸發 CI pipeline 執行，無需任何人工啟動動作。
- **FR-002**: 系統 MUST NOT 在 commit 推送至 main 以外的分支時觸發此 CI pipeline。
- **FR-003**: CI pipeline MUST 執行專案中既有的全部 pytest 單元測試。
- **FR-004**: CI pipeline MUST 在任一 pytest 測試失敗時，將整體 pipeline 標示為失敗，並中止後續步驟（包含品質掃描）。
- **FR-005**: CI pipeline MUST 僅在全部 pytest 測試通過後，才執行程式碼品質掃描步驟。
- **FR-006**: CI pipeline MUST 使用 SonarQube Cloud 分析程式碼，並將分析結果上傳至對應的 SonarQube Cloud 專案。
- **FR-007**: CI pipeline MUST 在 pipeline 執行摘要中顯示 SonarQube Cloud 的 Quality Gate 結果（通過或失敗），使開發者無需另外登入 SonarQube Cloud 即可得知結果。
- **FR-007a**: Quality Gate 結果為「失敗」時，CI pipeline MUST NOT 因此將 pipeline 整體執行結果標示為失敗；Quality Gate 結果僅作為資訊呈現，pipeline 整體成敗僅由建置與 pytest 測試步驟決定。
- **FR-008**: 系統 MUST NOT 將任何密碼或 token 以明文形式寫入版本控制庫（repo）；所有機密資訊 MUST 透過 Azure DevOps 的安全機制（例如 secret variable 或 service connection）提供給 pipeline。
- **FR-009**: 此功能 MUST NOT 產生或輸出測試覆蓋率（coverage）報告。
- **FR-010**: 此功能 MUST NOT 修改任何猜數字遊戲既有的程式碼（僅新增 CI 相關設定）。
- **FR-011**: 此功能 MUST NOT 對 Pull Request 觸發分析或檢查；CI 僅針對 main 分支的 commit 運作。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 推送至 main 分支的 commit，100% 會在無人工介入的情況下自動觸發一次 CI 執行。
- **SC-002**: 當程式碼變更導致任一既有單元測試失敗時，100% 的情況下 CI 會將該次執行標示為失敗，使開發者能在合併前得知問題。
- **SC-003**: 開發者可在 CI pipeline 的執行摘要畫面中，直接看到最新一次的 Quality Gate 結果（通過／失敗），100% 的情況下不需另外開啟 SonarQube Cloud 網站查詢。
- **SC-004**: 在測試通過的前提下，從 commit 推送到摘要出現 Quality Gate 結果的整體等待時間，MUST 在 10 分鐘以內。

## Assumptions

- SonarQube Cloud 的組織（organization）與專案（project）已事先建立並與本專案對應；本功能僅負責建立 CI 流程以呼叫既有的 SonarQube Cloud 專案，不包含建立或設定 SonarQube Cloud 專案本身。
- SonarQube Cloud 所需的驗證 token，以及任何其他機密資訊，將由開發者或維運者透過 Azure DevOps 的安全變數（secret variable）或 service connection 機制預先設定，而非經由本功能的程式碼變更寫入。
- CI 流程僅由 main 分支的 commit 觸發；Pull Request 的觸發與分析明確排除於本次範圍外（對應使用者提供的範圍外說明）。
- 既有的 pytest 測試套件與其執行方式（例如測試指令、相依套件安裝方式）已存在於專案中，CI 僅負責呼叫既有測試流程，不需另行設計測試案例。
- 本次不產生測試覆蓋率報告，CI 的測試步驟僅關注測試通過／失敗結果。
- 「品質掃描步驟」（見 FR-005、FR-006、FR-007、FR-007a 與對應 Edge Case）係指實際執行程式碼
  分析與上傳結果的動作（對應實作中的 SonarQube Cloud Analyze／Publish）；準備掃描所需的設定
  （例如寫入 scanner 參數）不算在內，可在測試執行前先行完成——只要分析本身與結果上傳仍只在
  測試通過後才實際發生即可。
