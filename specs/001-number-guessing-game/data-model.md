# Data Model: 終端機猜數字遊戲

本專案無持久化儲存；以下為記憶體內的實體、列舉與狀態轉換，皆不涉及框架或 I/O。

## 常數

| 名稱 | 值 | 位置 | 對應需求 |
|------|----|------|----------|
| `MIN_NUMBER` | 1 | `GameEngine` | FR-001、FR-008 |
| `MAX_NUMBER` | 100 | `GameEngine` | FR-001、FR-008 |

## 實體：GameEngine（遊戲局，對應 Spec 的 Game Round）

位置：`src/guessing_game/engine.py`

| 欄位 | 型別 | 可見度 | 說明 |
|------|------|--------|------|
| `_rng` | `random.Random` | 私有 | 隨機數來源（建構子注入；預設為新的 `random.Random()`） |
| `_secret` | `int` | 私有 | 秘密數字，1–100；整局不變；不提供公開讀取（FR-002） |
| `_attempts` | `int` | 私有 | 本局有效猜測次數，初始 0（FR-010） |
| `_finished` | `bool` | 私有 | 本局是否已答對，初始 `False` |

公開唯讀屬性：`attempts`（有效猜測次數）、`is_finished`（本局是否已結束）。

驗證規則：

- `is_valid_guess(value)`：`MIN_NUMBER <= value <= MAX_NUMBER` 才回傳 `True`（FR-008）。
- `guess(value)`：
  - 範圍外 → 拋 `ValueError`，狀態（次數、是否結束）不變（FR-009 的邏輯層保證）。
  - 本局已結束 → 拋 `RuntimeError`（避免結束後繼續計次）。
  - 其他 → `_attempts += 1`，比較後回傳 `GuessResult`；等於秘密數字時 `_finished = True`。

## 列舉：GuessResult（猜測判定結果，對應 Spec 的 Guess）

位置：`src/guessing_game/engine.py`

| 成員 | 意義 | 對應需求 |
|------|------|----------|
| `TOO_HIGH` | 猜測大於秘密數字 | FR-004 |
| `TOO_LOW` | 猜測小於秘密數字 | FR-005 |
| `CORRECT` | 猜測等於秘密數字 | FR-006 |

「無效」不是 `GuessResult` 成員：無效輸入在到達 engine 之前就被 CLI 攔截（格式錯誤），
或被 `is_valid_guess` 攔截（範圍錯誤），不屬於有效猜測、不計次。

## 列舉：PlayAgainChoice

位置：`src/guessing_game/cli.py`

| 成員 | 觸發輸入（忽略前後空白） | 對應需求 |
|------|--------------------------|----------|
| `REPLAY` | 空字串（直接按 Enter） | FR-012 |
| `QUIT` | `n` 或 `N` | FR-013 |
| `UNKNOWN` | 其他任何輸入 | FR-016 |

## CLI 純函式的輸入／輸出資料

| 函式 | 輸入 | 輸出 | 規則 |
|------|------|------|------|
| `parse_guess(raw)` | `str` | `int \| None` | `strip()` 後符合 `^-?(0\|[1-9][0-9]*)$` 回傳 `int`（可為 0 或負數）；否則 `None`（格式無效）。數字部分超過 18 位時不呼叫 `int()`，直接回傳 `±10**18`（必然超出範圍，見 research D4） |
| `parse_play_again(raw)` | `str` | `PlayAgainChoice` | 見上表 |

## 狀態轉換（單局）

```text
                  start_new_round()
                        │
                        ▼
              ┌───────────────────┐
              │  IN_PROGRESS      │◄──── 有效猜測且結果為 TOO_HIGH / TOO_LOW
              │  attempts = n     │      （attempts += 1，維持 IN_PROGRESS）
              └─────────┬─────────┘
                        │ 有效猜測且結果為 CORRECT（attempts += 1）
                        ▼
              ┌───────────────────┐
              │  FINISHED         │──── start_new_round() ──► IN_PROGRESS（attempts = 0，重新產生秘密數字）
              └───────────────────┘

無效輸入（格式錯誤或超出範圍）：不進入 engine，狀態完全不變（FR-009）。
```

## 實體與需求對照

| 實體／規則 | 需求 |
|-----------|------|
| 秘密數字產生 | FR-001、FR-002、SC-002 |
| 判定結果 | FR-004～FR-006、SC-003 |
| 有效次數 | FR-009、FR-010 |
| 新局重置 | FR-012、SC-007 |
