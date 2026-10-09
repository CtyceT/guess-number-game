<!--
Sync Impact Report
- Version change: 1.0.0 → 1.1.0
- Modified principles: I. 技術棧限制（Python 3.11+、僅標準函式庫、pytest）
  → I. 技術棧限制（Python 3.11+、僅標準函式庫、pytest、pytest-cov）
  - 新增：開發與 CI 環境除 pytest 外，MAY 使用 pytest-cov 產生測試覆蓋率報告。
  - 新增：效能量測工具 MUST 僅使用標準函式庫。
  - 執行期程式碼僅限標準函式庫之限制維持不變。
- Added sections: none
- Removed sections: none
- Other changes: Additional Constraints 之相依管理條款同步更新，納入 pytest-cov 為允許相依。
- Deferred TODOs: none
-->
# 終端機猜數字遊戲 Constitution

## Core Principles

### I. 技術棧限制（Python 3.11+、僅標準函式庫、pytest、pytest-cov）
- 程式碼 MUST 以 Python 3.11 或更新版本實作。
- 執行期程式碼 MUST 僅使用 Python 標準函式庫，不得引入任何第三方套件。
- 測試 MUST 使用 pytest；開發與 CI 環境除 pytest 外，MAY 使用 pytest-cov 產生測試覆蓋率報告。
- pytest 與 pytest-cov 是僅允許的第三方相依，且僅限開發／CI／測試環境，不得用於執行期程式碼。
- 效能量測工具 MUST 僅使用 Python 標準函式庫（例如 `timeit`），不得引入第三方效能量測套件。

理由：本專案用於練習 SDD 流程，零相依可降低環境變因，讓學習聚焦於流程本身；納入 pytest-cov
可驗證測試覆蓋率而不影響執行期的零相依原則；效能量測限定標準函式庫以維持環境一致性與結果可重現性。

### II. Google Python Style Guide 與型別／文件規範
- 程式碼 MUST 遵循 Google Python Style Guide。
- 所有函式與方法（含私有函式與測試輔助函式）MUST 具備完整的 type hints（參數與回傳值）。
- 所有函式與方法 MUST 具備 Google 風格 docstring，至少說明用途，並於適用時包含
  `Args:`、`Returns:`、`Raises:` 區塊。

理由：一致的風格與明確的型別／文件，使規格、程式與測試之間更容易對照與審查。

### III. 邏輯與 I/O 分離（NON-NEGOTIABLE）
- 遊戲邏輯層 MUST NOT 直接呼叫 `input()` 或 `print()`。
- 所有使用者輸入與輸出 MUST 集中於獨立的 I/O 層（例如 CLI 進入點），
  並由 I/O 層呼叫邏輯層。
- 邏輯層 MUST 以純函式或以參數／回傳值傳遞資料的類別實作，使其可在不模擬任何終端機
  輸入輸出的情況下獨立測試。

理由：分離關注點使核心邏輯可被單元測試，也讓日後更換介面（例如 GUI）不需修改邏輯。

### IV. 核心邏輯單元測試
- 所有核心邏輯（例如目標數字產生、猜測比對、範圍與輸入驗證、勝負判定）MUST 具備
  pytest 單元測試。
- 測試 MUST 涵蓋正常情況、邊界值與錯誤輸入。
- 測試 MUST 具決定性；涉及隨機性的邏輯 MUST 可注入固定種子或固定值以利驗證。
- 合併前，所有 pytest 測試 MUST 通過。

理由：核心邏輯的正確性是遊戲可信度的基礎，單元測試是驗證規格是否被滿足的主要手段。

### V. 日誌規範（logging、INFO、stdout）
- 日誌 MUST 使用內建 `logging` 模組，不得以 `print()` 代替日誌。
- 日誌等級 MUST 固定為 INFO，不得提供其他等級的設定或切換。
- 日誌 MUST 輸出至 stdout（例如 `logging.StreamHandler(sys.stdout)`）。
- 日誌的初始設定 MUST 集中於單一位置（應用程式進入點），其餘模組僅取得 logger 使用。

理由：統一的日誌行為使執行過程可預期、可觀察，且不與遊戲互動輸出混用機制。

## Additional Constraints

- 專案 MUST 維持精簡：僅實作規格中明確要求的功能，避免預先設計與不必要的抽象。
- 專案結構 MUST 將邏輯層、I/O 層與測試分置於不同模組或目錄，以體現原則 III。
- 相依管理：除 pytest 與 pytest-cov 外新增任何相依，MUST 先依 Governance 程序修訂本憲章。

## Development Workflow

- 開發 MUST 遵循 SDD（Spec-Driven Development）流程：
  規格（specify）→ 計畫（plan）→ 任務（tasks）→ 實作（implement）。
- 每個實作變更 MUST 可追溯至規格中的需求或任務。
- 提交合併前 MUST 確認：pytest 全數通過、新增函式皆有 type hints 與 docstring、
  邏輯層未出現 `input()`／`print()`、日誌設定符合原則 V。
- 計畫階段 MUST 進行 Constitution Check；違反任何原則者 MUST 於計畫中明確記錄並說明理由。

## Governance

- 本憲章優先於其他開發慣例與偏好；規格、計畫與任務 MUST 與本憲章一致。
- 修訂程序：任何修訂 MUST 以文件記錄變更內容與理由、更新版本號與 Last Amended 日期，
  並同步檢視 spec、plan、tasks 等相依文件是否需要調整。
- 版本規則（語意化版本）：
  - MAJOR：不相容的治理規則或原則移除／重新定義。
  - MINOR：新增原則或章節，或實質擴充既有規範。
  - PATCH：文字澄清、用詞與錯字修正等非語意變更。
- 合規審查：每次計畫審查與合併審查 MUST 驗證是否符合本憲章；
  任何偏離 MUST 有書面理由，否則不得合併。

**Version**: 1.1.0 | **Ratified**: 2026-09-25 | **Last Amended**: 2026-10-09
