# Research: 終端機猜數字遊戲

Technical Context 中沒有 `NEEDS CLARIFICATION`；以下記錄各項設計決策與理由，供實作與審查對照。

## D1. 隨機數來源注入

- **Decision**: `GameEngine.__init__(rng: random.Random | None = None)`；未提供時建立 `random.Random()`。
  以 `rng.randint(1, 100)` 產生秘密數字。
- **Rationale**: 使用者要求可注入；`random.Random` 實例讓測試能用固定種子重現，
  也能以子類別覆寫 `randint` 回傳固定值，不需要 monkeypatch 全域狀態。
- **Alternatives considered**:
  - 注入 `Callable[[int, int], int]`：更輕量，但與使用者指定的 `random.Random` 不符，且失去種子重現的直觀性。
  - 直接呼叫模組層級 `random.randint`：測試需 monkeypatch，且共享全域狀態。

## D2. 格式驗證與範圍驗證的歸屬

- **Decision**: 格式驗證（純數字寫法）在 CLI 的 `parse_guess`；範圍規則（1–100）由 GameEngine 持有
  （`MIN_NUMBER`、`MAX_NUMBER`、`is_valid_guess`）。`GameEngine.guess()` 對超出範圍的值拋出 `ValueError`，
  且不改變狀態。
- **Rationale**: 使用者指定 CLI「驗證格式」；範圍是遊戲規則，放在邏輯層可避免 CLI 與 engine 各存一份常數，
  也讓 engine 對非法呼叫保持自我防衛。
- **Alternatives considered**: 全部驗證放 CLI（engine 信任輸入）——engine 被誤用時會默默產生錯誤結果，
  且範圍常數重複。

## D3. 輸入格式規則（對應 FR-007、FR-008、FR-015）

- **Decision**: 先 `strip()` 前後空白，再以正規表達式 `^-?(0|[1-9][0-9]*)$` 判定格式。
  符合者轉為 `int`（可能為 0 或負數，交由 engine 判斷範圍）；不符合者為格式無效。
  使用明確的 `[0-9]` 而非 `\d` 或 `str.isdigit()`。
- **Rationale**:
  - 排除空白、小數（`3.5`、`50.0`）、字母／符號、帶 `+` 或前導零（`+5`、`007`）——符合澄清第 2 題。
  - `-5` 格式合法但超出範圍，能顯示「超出範圍」訊息（FR-008）。
  - `\d` 與 `isdigit()` 會接受全形數字（如 `５`）與其他 Unicode 數字，`int()` 也會轉換它們；
    明確限定 ASCII 數字可避免行為不明確。
- **Alternatives considered**: 直接 `int(text)` + `try/except`——會接受 `+5`、`007`、`1_0`、全形數字，違反澄清結果。

## D4. 超長數字字串

- **Decision**: 格式通過後，若數字部分（不含負號）超過 18 位，不呼叫 `int()`，
  直接回傳 `+10**18`（正數）或 `-10**18`（負數）；否則正常 `int()` 轉換。
- **Rationale**: Python 3.11 對超過約 4300 位的數字串呼叫 `int()` 會拋出 `ValueError`。
  這類輸入格式上是整數、數值上必然超出 1–100，歸入「超出範圍」最符合 FR-008，
  且不會崩潰（SC-004）。預先截斷讓 `parse_guess` 不需要 `try/except`，行為可預測。
- **Alternatives considered**: 捕捉 `int()` 的 `ValueError`——需要額外的哨兵值與例外路徑；
  且 4300 位這個門檻是直譯器實作細節，不宜寫進規則。

## D5. 「是否再玩」判定（對應澄清第 1 題、FR-011～FR-013、FR-016）

- **Decision**: `parse_play_again(raw) -> PlayAgainChoice`：`strip()` 後為空字串 → `REPLAY`；
  `lower()` 後等於 `"n"` → `QUIT`；其他 → `UNKNOWN`（CLI 提示並重新詢問）。
- **Rationale**: 純函式，易於單元測試；三種結果與規格一一對應。
- **Alternatives considered**: 接受 `y`／`yes`——澄清結果明確指定「其他輸入重新詢問」，`y` 屬其他輸入。

## D6. Ctrl+C 與 Ctrl+D 處理（對應 FR-014、SC-005）

- **Decision**: `run()` 以單一 `try/except (KeyboardInterrupt, EOFError)` 包住整個遊戲迴圈
  （涵蓋猜測階段與「是否再玩」階段）。捕捉後：輸出友善訊息、記錄「玩家離開」、回傳 exit code 0。
- **Rationale**: 兩種中斷只需一處處理，玩家看到一致行為；集中處理也確保不會有路徑漏掉而洩漏堆疊追蹤。
- **Alternatives considered**: 在每個 `input_fn` 呼叫點各自處理——重複且容易遺漏。

## D7. 日誌（對應 FR-017、憲章原則 V）

- **Decision**: CLI 提供 `configure_logging()`，僅由 `main()` 呼叫：
  `logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(levelname)s %(message)s")`。
  模組以 `logging.getLogger(__name__)` 取得 logger。僅記錄三類事件：
  「新局開始」、「本局結束（含總猜測次數）」、「玩家離開（含原因：輸入 n／Ctrl+C／輸入結束）」。
  GameEngine 不記錄日誌。
- **Rationale**: 日誌初始化集中於進入點（使用者要求）；`run()` 本身不設定 logging，
  因此整合測試可用 `caplog` 驗證事件而不改動全域設定。事件由 CLI 記錄，使 engine 保持純粹，
  也不需擔心 engine 洩漏秘密數字到 stdout。
- **Alternatives considered**: 由 engine 記錄「新局開始」——engine 會多一個副作用，
  且日誌內容與呈現層（stdout）綁得更緊。

## D8. CLI 的可測試性

- **Decision**: `run(input_fn: Callable[[str], str] = input, output_fn: Callable[[str], None] = print,
  engine: GameEngine | None = None) -> int`。`main()` 負責 `configure_logging()`、呼叫 `run()` 並回傳結束碼。
- **Rationale**: 憲章允許 CLI 層使用 `input()`／`print()`；以參數注入而非 monkeypatch 內建函式，
  讓整合測試以腳本化輸入序列驅動完整流程，仍不需真實終端機。
- **Alternatives considered**: `monkeypatch.setattr("builtins.input", ...)` 與 `capsys`——可行但較脆弱，
  且與 `input()` 預設提示字串的互動較不明確。

## D9. 專案封裝與執行方式

- **Decision**: 不建立可安裝套件。`pyproject.toml` 僅含 `[tool.pytest.ini_options]`
  （`pythonpath = ["src"]`、`testpaths = ["tests"]`）；執行方式為 `PYTHONPATH=src python -m guessing_game`。
- **Rationale**: 避免引入建置後端（如 setuptools）等額外相依，貼合憲章「僅標準函式庫、維持精簡」。
- **Alternatives considered**: 完整 `[project]` + 可安裝套件——對本練習專案價值有限，且增加建置相依。

## D10. 架構規則的自動化檢查

- **Decision**: `tests/unit/test_architecture.py` 以 `ast` 解析 `engine.py`，斷言：
  (1) 沒有對 `input`、`print` 的呼叫；(2) 沒有匯入 `cli` 或 `guessing_game.cli`。
- **Rationale**: 憲章原則 III 標為 NON-NEGOTIABLE，把它變成可自動執行的測試，比僅靠審查可靠。
- **Alternatives considered**: 僅於審查時人工檢查——容易疏漏。

## D11. 測試涵蓋策略

- **Decision**: 見 plan.md 專案結構。額外一項測試：以二分搜尋策略對 1–100 每個秘密數字模擬遊玩，
  斷言皆在 7 次有效猜測內答對（對應 SC-006）。
- **Rationale**: SC-006 是可量化的成功標準，能以純邏輯層直接驗證。
