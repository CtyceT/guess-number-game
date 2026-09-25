# Contract: GameEngine 公開介面

模組：`guessing_game.engine`。此為邏輯層對 CLI（與測試）暴露的完整介面。

## 約束（憲章原則 III）

- 模組 MUST NOT 呼叫 `input()`／`print()`，MUST NOT 匯入 `guessing_game.cli`。
- 模組 MUST NOT 使用 logging（日誌由 CLI 負責）。
- 秘密數字 MUST NOT 透過任何公開成員暴露（FR-002）。

## `class GuessResult(enum.Enum)`

| 成員 | 意義 |
|------|------|
| `TOO_HIGH` | 猜測大於秘密數字 |
| `TOO_LOW` | 猜測小於秘密數字 |
| `CORRECT` | 猜測等於秘密數字 |

## `class GameEngine`

### 類別常數

| 名稱 | 型別 | 值 |
|------|------|----|
| `MIN_NUMBER` | `int` | `1` |
| `MAX_NUMBER` | `int` | `100` |

### `__init__(self, rng: random.Random | None = None) -> None`

- 未提供 `rng` 時使用新的 `random.Random()`。
- 建構完成時已開始第一局：產生秘密數字、`attempts == 0`、`is_finished is False`。

### `start_new_round(self) -> None`

- 以 `rng.randint(MIN_NUMBER, MAX_NUMBER)` 重新產生秘密數字，`attempts` 歸零，`is_finished` 設為 `False`。
- 可在任何狀態呼叫（進行中或已結束）。

### `is_valid_guess(self, value: int) -> bool`

- 回傳 `MIN_NUMBER <= value <= MAX_NUMBER`。純查詢，不改變狀態。

### `guess(self, value: int) -> GuessResult`

| 情況 | 行為 |
|------|------|
| `value` 超出範圍 | 拋 `ValueError`；`attempts`、`is_finished` 皆不變 |
| 本局已結束 | 拋 `RuntimeError`；狀態不變 |
| `value > secret` | `attempts += 1`，回傳 `TOO_HIGH` |
| `value < secret` | `attempts += 1`，回傳 `TOO_LOW` |
| `value == secret` | `attempts += 1`，`is_finished = True`，回傳 `CORRECT` |

### 屬性

| 名稱 | 型別 | 說明 |
|------|------|------|
| `attempts` | `int`（唯讀） | 本局有效猜測次數 |
| `is_finished` | `bool`（唯讀） | 本局是否已答對 |

## 可測試性保證

- 注入的 `rng` 只被 `start_new_round()` 呼叫（每局一次 `randint`），因此測試可用
  `random.Random(seed)` 重現，或以覆寫 `randint` 的子類別固定秘密數字。
- 對應測試：`tests/unit/test_engine.py`，不得啟動任何真實終端機輸入輸出。
