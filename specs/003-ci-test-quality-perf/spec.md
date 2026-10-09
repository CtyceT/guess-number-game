# Feature Specification: CI 測試品質與效能量測擴充

**Feature Branch**: `003-ci-test-quality-perf`

**Created**: 2026-10-09

**Status**: Draft

**Input**: User description: "擴充既有的 Azure Pipelines CI（azure-pipelines.yml），新增測試品質與效能量測。

User Story 01 測試成功率：身為開發者，我想要在 pipeline 看到每個單元測試的通過與失敗，以及整體成功率，以便掌握功能是否正常。
User Story 02 測試覆蓋率：身為開發者，我想要在 pipeline 與 SonarQube Cloud 看到測試覆蓋率，以便知道哪些程式碼沒有被測到。
User Story 03 效能量測：身為開發者，我想要每次 CI 都執行猜數字遊戲多次，量測平均的 CPU 時間、記憶體用量與回應時間，並顯示在 pipeline 摘要中，以便追蹤效能變化。

範圍外：不修改任何遊戲程式碼；效能結果不設定門檻，不因效能數字讓 pipeline 失敗。
限制：任何 token 都不得寫入 repo；沿用 spec 002 的觸發方式與 SonarQube Cloud 設定；本 feature 取代 spec 002 FR-009 的覆蓋率排除規定。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 測試成功率可視化 (Priority: P1)

身為開發者，我想要在 pipeline 看到每個單元測試的通過與失敗，以及整體成功率，以便掌握功能是否正常。

**Why this priority**: 建立在既有（spec 002）pytest 執行能力之上，將測試結果以每案例通過/失敗與整體成功率呈現，是最直接、風險最低的可視性提升，且不依賴覆蓋率或效能量測即可獨立交付價值。

**Independent Test**: 觸發一次包含部分失敗測試的 pipeline 執行，確認 pipeline 摘要能顯示每個測試案例的通過/失敗狀態與整體成功率百分比，不需查看原始文字記錄即可得知結果。

**Acceptance Scenarios**:

1. **Given** pipeline 執行中且全部測試通過，**When** 測試步驟完成，**Then** pipeline 摘要顯示每個測試案例為通過狀態，且整體成功率顯示為 100%。
2. **Given** pipeline 執行中且至少一項測試失敗，**When** 測試步驟完成，**Then** pipeline 摘要列出該測試案例為失敗，顯示整體成功率低於 100%，且 pipeline 整體仍標示為失敗（延續既有 CI 失敗判定規則）。

---

### User Story 2 - 測試覆蓋率報告 (Priority: P2)

身為開發者，我想要在 pipeline 與 SonarQube Cloud 看到測試覆蓋率，以便知道哪些程式碼沒有被測到。

**Why this priority**: 建立在 User Story 1 的測試執行與結果呈現之上，進一步提供「哪些程式碼未被測試覆蓋」的洞察；需先有可靠的測試執行結果，覆蓋率數據才有意義。

**Independent Test**: 觸發一次 pipeline 執行，確認 pipeline 產生測試覆蓋率報告並於摘要顯示整體覆蓋率百分比，同時可在 SonarQube Cloud 專案頁面查看覆蓋率與未被覆蓋的程式碼位置。

**Acceptance Scenarios**:

1. **Given** pipeline 執行中，**When** 測試步驟執行完成，**Then** pipeline 產生測試覆蓋率報告，並可在 pipeline 摘要中查看整體覆蓋率百分比。
2. **Given** 覆蓋率報告已產生，**When** 品質掃描步驟執行，**Then** SonarQube Cloud 專案頁面顯示對應的程式碼覆蓋率資訊，並可識別出未被覆蓋的程式碼位置。

---

### User Story 3 - 猜數字遊戲效能量測 (Priority: P3)

身為開發者，我想要每次 CI 都執行猜數字遊戲多次，量測平均的 CPU 時間、記憶體用量與回應時間，並顯示在 pipeline 摘要中，以便追蹤效能變化。

**Why this priority**: 在測試正確性（US1）與覆蓋率洞察（US2）之上，新增效能趨勢追蹤能力。由於效能數字不設門檻、不影響 pipeline 成敗，屬於資訊性強化，對於「是否可合併」的影響最小，優先度最低。

**Independent Test**: 觸發一次 pipeline 執行，確認猜數字遊戲在無人工互動的情況下被自動執行多次，且 pipeline 摘要顯示多次執行的平均 CPU 時間、平均記憶體用量與平均回應時間，並確認無論量測數值為何，pipeline 整體成功/失敗判定不受影響。

**Acceptance Scenarios**:

1. **Given** pipeline 執行中，**When** 效能量測步驟執行，**Then** 猜數字遊戲被自動執行多次，且 pipeline 摘要顯示平均 CPU 時間、平均記憶體用量與平均回應時間。
2. **Given** 效能量測得到的數值異常地高或低，**When** pipeline 完成，**Then** pipeline 整體結果仍不受效能數值影響（不因效能數字導致 pipeline 失敗）。

---

### Edge Cases

- 當測試覆蓋率報告未能成功產生（例如相依套件安裝失敗）時，pipeline 必須標示為失敗，並在摘要中呈現錯誤原因，使開發者能定位問題。
- 當覆蓋率資料未能成功上傳至 SonarQube Cloud（例如服務暫時無法連線或逾時）時，pipeline 摘要必須顯示可辨識的錯誤訊息，但不因此回溯讓已通過的測試步驟失敗（與既有品質掃描步驟的資訊呈現原則一致）。
- 當效能量測步驟本身發生執行錯誤（而非量測數值不佳，例如遊戲執行逾時或當機）時，pipeline 摘要必須顯示可辨識的錯誤訊息，但不因此影響 pipeline 整體成功/失敗結果。
- 當測試步驟本身失敗時，覆蓋率報告產生與效能量測步驟皆不執行（延續既有「測試失敗則中止後續步驟」規則）。
- 當 commit 推送至 main 以外的分支或為 Pull Request 時，沿用既有觸發方式，不觸發本功能新增的任何步驟。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: CI pipeline MUST 沿用既有觸發機制（僅於 commit 推送至 main 分支時執行，其他分支或 Pull Request 不觸發），不得重新定義觸發條件。
- **FR-002**: CI pipeline MUST 在既有 pytest 測試執行後，於 pipeline 摘要呈現每一測試案例的通過／失敗結果。
- **FR-003**: CI pipeline MUST 在 pipeline 摘要呈現整體測試成功率（通過測試數除以總測試數之百分比）。
- **FR-004**: CI pipeline MUST 產生測試覆蓋率報告（涵蓋猜數字遊戲程式碼），並在 pipeline 摘要中呈現整體覆蓋率百分比。
- **FR-005**: CI pipeline MUST 將測試覆蓋率資料上傳至既有的 SonarQube Cloud 專案（沿用既有 SonarQube Cloud 設定），使覆蓋率與未覆蓋的程式碼位置可在 SonarQube Cloud 介面中查看。
- **FR-006**: 本功能 MUST 取代並廢止先前「不產生測試覆蓋率報告」之限制；自本功能起，CI MUST 產生並呈現測試覆蓋率報告。
- **FR-007**: CI pipeline MUST 在測試步驟完成後，自動執行猜數字遊戲多次（無需任何人工互動），以取得效能量測樣本。
- **FR-008**: CI pipeline MUST 針對猜數字遊戲的每次執行，量測其 CPU 時間、記憶體用量與回應時間。
- **FR-009**: CI pipeline MUST 在 pipeline 摘要中顯示多次執行後的平均 CPU 時間、平均記憶體用量與平均回應時間。
- **FR-010**: 效能量測結果 MUST NOT 設定任何通過／失敗門檻；無論量測數值為何，MUST NOT 導致 pipeline 整體標示為失敗。
- **FR-011**: 效能量測 MUST NOT 修改猜數字遊戲既有的程式碼；僅可新增用於驅動與量測的外部腳本或 CI 設定。
- **FR-012**: 系統 MUST NOT 將任何密碼或 token 以明文形式寫入 repo；所有機密資訊 MUST 沿用既有的 Azure DevOps 安全機制（secret variable 或 service connection）提供。
- **FR-013**: 當測試覆蓋率報告未能成功產生時，CI pipeline MUST 將整體 pipeline 標示為失敗，並呈現錯誤原因。
- **FR-014**: 當覆蓋率資料上傳至 SonarQube Cloud 失敗時，pipeline 摘要 MUST 顯示可辨識的錯誤訊息，但 MUST NOT 因此讓已通過的測試步驟回溯標示為失敗。
- **FR-015**: 當效能量測步驟本身發生執行錯誤時，pipeline 摘要 MUST 顯示可辨識的錯誤訊息，但 MUST NOT 因此影響 pipeline 整體成功/失敗結果。

### Key Entities

- **測試執行結果（Test Run Result）**：單次 pipeline 執行中，每個測試案例的名稱與通過／失敗狀態，以及由此彙總的整體成功率。
- **覆蓋率報告（Coverage Report）**：單次 pipeline 執行所產生的整體覆蓋率百分比，以及對應到 SonarQube Cloud 可識別的未覆蓋程式碼位置。
- **效能量測樣本（Performance Sample）**：猜數字遊戲單次自動執行所量測到的 CPU 時間、記憶體用量與回應時間。
- **效能量測摘要（Performance Summary）**：單次 pipeline 執行中，多個效能量測樣本彙總而得的平均 CPU 時間、平均記憶體用量與平均回應時間。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% 的 pipeline 執行完成後，開發者可直接在 pipeline 摘要中看到每個測試案例的通過/失敗狀態與整體成功率，不需查看原始記錄檔。
- **SC-002**: 100% 的 pipeline 成功執行皆同時在 pipeline 摘要與 SonarQube Cloud 兩處呈現最新的測試覆蓋率百分比。
- **SC-003**: 開發者可在 SonarQube Cloud 介面中識別出未被測試覆蓋的程式碼位置，不需額外工具或手動比對程式碼。
- **SC-004**: 每次 pipeline 執行，開發者都能在摘要中看到猜數字遊戲至少 5 次自動執行後的平均 CPU 時間、平均記憶體用量與平均回應時間三項效能指標。
- **SC-005**: 100% 的情況下，pipeline 整體成功/失敗判定不受效能量測數值影響，僅由建置與測試結果決定。
- **SC-006**: 本功能上線後，既有猜數字遊戲程式碼檔案（CI 設定與量測腳本以外）維持零修改。

## Assumptions

- 本功能沿用既有（spec 002）CI 觸發方式（僅 main 分支 commit 觸發，不含 Pull Request）與 SonarQube Cloud 組織／專案設定，不重新設定這些項目。
- 測試覆蓋率報告採用與 SonarQube Cloud 相容的標準格式產生；產生覆蓋率報告所需的工具已由專案憲章允許於開發／CI 環境中使用。
- 效能量測透過新增的外部驅動腳本（不修改遊戲既有原始程式碼）提供模擬的猜測輸入，驅動既有遊戲介面完整執行一局；此驅動腳本與其 CI 設定視為本功能新增內容，不構成對遊戲程式碼的修改。
- 每次 pipeline 執行時，猜數字遊戲至少自動執行 5 次以取得平均效能數值；此次數為合理預設值，未來可視需要調整。
- CPU 時間、記憶體用量與回應時間之量測僅使用標準函式庫提供的工具取得，不引入第三方效能量測套件（符合專案憲章對效能量測工具的限制）。
- 本功能取代先前 CI 規格中「不產生測試覆蓋率報告」之限制；該限制自本功能生效後不再適用。
- SonarQube Cloud 所需的驗證 token 與其他機密資訊，沿用既有 Azure DevOps 安全變數設定提供，本功能不新增或變更機密資訊的注入方式。
