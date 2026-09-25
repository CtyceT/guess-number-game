# Contract: CLI 互動、日誌與結束行為

模組：`guessing_game.cli`。執行方式：`PYTHONPATH=src python -m guessing_game`（無命令列參數）。

## 公開函式

| 函式 | 簽章 | 說明 |
|------|------|------|
| `parse_guess` | `(raw: str) -> int \| None` | 格式驗證；`None` 表示格式無效（FR-007、FR-015） |
| `parse_play_again` | `(raw: str) -> PlayAgainChoice` | 判定「是否再玩」輸入（FR-012、FR-013、FR-016） |
| `configure_logging` | `() -> None` | 設定 logging：INFO、`sys.stdout`；僅由 `main()` 呼叫 |
| `run` | `(input_fn: Callable[[str], str] = input, output_fn: Callable[[str], None] = print, engine: GameEngine \| None = None) -> int` | 遊戲主迴圈；回傳結束碼；不設定 logging |
| `main` | `() -> int` | 進入點：`configure_logging()` 後呼叫 `run()` |

## 輸入規則

### 猜測輸入（`parse_guess`，先 `strip()` 前後空白）

| 輸入 | 結果 | CLI 行為 | 計次 |
|------|------|----------|------|
| `42`、`1`、`100` | 有效整數（在範圍內） | 交給 engine 判定 | 是 |
| `0`、`101`、`-5`、超長數字串 | 有效格式、超出範圍 | 顯示「超出範圍」訊息，重新提示 | 否 |
| 空白、`3.5`、`50.0`、`abc`、`#`、`+5`、`007`、全形數字 | 格式無效 | 顯示「格式錯誤」訊息，重新提示 | 否 |

### 「是否再玩」輸入（`parse_play_again`，先 `strip()`）

| 輸入 | 結果 | CLI 行為 |
|------|------|----------|
| 空字串（直接 Enter） | `REPLAY` | 開始新局 |
| `n`、`N` | `QUIT` | 顯示再見訊息並結束，結束碼 0 |
| 其他 | `UNKNOWN` | 顯示提示並重新詢問 |

## 訊息（輸出至 `output_fn`，繁體中文）

| 情境 | 訊息 |
|------|------|
| 猜測提示 | `請輸入猜測（1-100）：`（作為 `input_fn` 的提示字串） |
| 猜太大 | `太大` |
| 猜太小 | `太小` |
| 答對 | `答對！你總共猜了 {attempts} 次。`（含「答對」與總次數，FR-006、FR-010） |
| 格式錯誤 | `輸入無效：請輸入 1 到 100 的整數。` |
| 超出範圍 | `輸入無效：數字必須介於 1 到 100 之間。` |
| 再玩提示 | `再玩一局？按 Enter 再玩，輸入 n 離開：`（作為 `input_fn` 的提示字串，FR-011） |
| 再玩輸入無法辨識 | `請按 Enter 再玩，或輸入 n 離開。` |
| 輸入 `n` 離開 | `再見！` |
| Ctrl+C／Ctrl+D 離開 | `已離開遊戲，再見！`（先輸出換行以避免接在提示字串後） |

訊息為驗收時的比對依據；措辭變更需同步更新此表與測試。

## 日誌（憲章原則 V、FR-017）

- 設定：套件 logger `logging.getLogger("guessing_game")`，等級 `logging.INFO`，
  handler 為 `logging.StreamHandler(sys.stdout)`，格式 `"%(levelname)s %(message)s"`；
  重複呼叫不得產生重複 handler；僅在 `main()` 內透過 `configure_logging()` 呼叫。
- 僅記錄下列三類事件，且皆為 INFO 等級：

| 事件 | 時機 | 訊息內容 |
|------|------|----------|
| 新局開始 | 每局開始（含首局與再玩） | `新局開始` |
| 本局結束 | 答對時 | `本局結束，總猜測次數：{attempts}` |
| 玩家離開 | 輸入 `n`、Ctrl+C 或 Ctrl+D | `玩家離開（原因：{n / Ctrl+C / 輸入結束}）` |

- 日誌 MUST NOT 包含秘密數字，MUST NOT 記錄每次猜測的內容或無效輸入內容。

## 結束行為

| 情境 | 結束碼 | 堆疊追蹤 |
|------|--------|----------|
| 輸入 `n` 離開 | `0` | 無 |
| Ctrl+C（`KeyboardInterrupt`） | `0` | 無（FR-014、SC-005） |
| Ctrl+D／輸入來源讀完（`EOFError`） | `0` | 無（FR-014、SC-005） |

Ctrl+C 與 Ctrl+D 於猜測階段與「是否再玩」階段的行為一致，皆由 `run()` 的單一
`try/except (KeyboardInterrupt, EOFError)` 處理。

## 對應測試

- `tests/unit/test_cli_parsing.py`：`parse_guess`、`parse_play_again` 全部輸入類別。
- `tests/integration/test_cli_flow.py`：以腳本化 `input_fn`／`output_fn` 驅動 `run()`，
  驗證訊息、不計次行為、再玩流程、Ctrl+C／Ctrl+D、日誌事件（`caplog`）。
