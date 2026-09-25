# Implementation Plan: 終端機猜數字遊戲

**Branch**: `001-number-guessing-game`（僅為功能識別名稱；實際在 `master` 上作業）| **Date**: 2026-09-25 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-number-guessing-game/spec.md`

## Summary

以 Python 3.11 標準函式庫實作終端機猜數字遊戲。系統隨機產生 1–100 的整數，玩家反覆猜測並得到
「太大／太小／答對」回饋，答對後顯示總猜測次數並可再玩一局。

技術方法為兩層架構（對應憲章原則 III）：

- **GameEngine（純邏輯層）**：產生秘密數字、判定猜測結果、管理單局狀態（有效猜測次數、是否結束）。
  隨機數來源由建構子注入 `random.Random`，不依賴任何 I/O。
- **CLI（輸入輸出層）**：讀取輸入、驗證格式、顯示訊息、處理「是否再玩」、處理 Ctrl+C／Ctrl+D，
  並在進入點初始化 logging。相依方向僅限 CLI → GameEngine。

格式驗證（純數字寫法）屬於 CLI；範圍規則（1–100）屬於 GameEngine，兩者各自單一來源。

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: 僅標準函式庫（`random`、`logging`、`re`、`enum`、`sys`）

**Storage**: N/A（不保存任何跨局或跨程式重啟的紀錄）

**Testing**: pytest（唯一第三方相依，僅限開發／測試環境）

**Target Platform**: 任何可執行 Python 3.11+ 的終端機環境（開發環境為 Linux／WSL2）

**Project Type**: CLI（單一專案）

**Performance Goals**: 每次輸入的回應為即時（人類無感延遲）；SC-001：啟動後 10 秒內可輸入第一次猜測

**Constraints**: 邏輯層不得呼叫 `input()`／`print()`；日誌固定 INFO、輸出至 stdout、僅三類事件、
不得含秘密數字；Ctrl+C／Ctrl+D 不得出現堆疊追蹤

**Scale/Scope**: 單一玩家、單一程序；約 2 個原始碼模組、1 個進入點、3–4 個測試檔

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 檢查結果 | 依據 |
|------|----------|------|
| I. Python 3.11+、僅標準函式庫、pytest | ✅ 通過 | 執行期僅用 `random`、`logging`、`re`、`enum`、`sys`；不引入任何套件；`pyproject.toml` 只放 pytest 設定，不含 `[project]` 相依 |
| II. Google Style、type hints、docstring | ✅ 通過 | 所有函式與方法（含測試函式、測試輔助函式）皆標註型別並附 Google 風格 docstring；測試函式回傳型別為 `-> None` |
| III. 邏輯與 I/O 分離 | ✅ 通過 | `engine.py` 不含 `input()`／`print()`，也不匯入 `cli`；I/O 全在 `cli.py`；`tests/unit/test_architecture.py` 以 AST 自動檢查此規則 |
| IV. 核心邏輯單元測試 | ✅ 通過 | GameEngine 與 CLI 純函式（`parse_guess`、`parse_play_again`）皆有 pytest 單元測試，涵蓋正常、邊界與錯誤輸入；隨機性以注入 `random.Random` 消除 |
| V. 日誌（logging、INFO、stdout） | ✅ 通過 | 僅在 CLI 進入點呼叫 `configure_logging()`；等級固定 INFO、handler 綁定 `sys.stdout`；僅記錄三類事件 |
| 工作流程：SDD、可追溯 | ✅ 通過 | 每項設計對應 spec 的 FR／SC（見 data-model.md 與 contracts/） |

**Gate 結果**：無違規，Complexity Tracking 免填。

**Phase 1 設計後重新檢查**：設計未新增任何相依、未讓 engine 依賴 I/O、日誌事件維持三類；全部原則仍通過。

## Project Structure

### Documentation (this feature)

```text
specs/001-number-guessing-game/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── engine-api.md    #   GameEngine 公開介面
│   └── cli-contract.md  #   終端機互動、訊息、日誌與結束行為
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
pyproject.toml               # 僅含 [tool.pytest.ini_options]（pythonpath、testpaths）
src/
└── guessing_game/
    ├── __init__.py
    ├── __main__.py          # 進入點：python -m guessing_game → cli.main()
    ├── engine.py            # GameEngine、GuessResult（純邏輯，無 I/O、不匯入 cli）
    └── cli.py               # parse_guess、parse_play_again、configure_logging、run、main

tests/
├── unit/
│   ├── test_engine.py       # GameEngine 行為（注入固定 Random；無任何終端機 I/O）
│   ├── test_cli_parsing.py  # parse_guess、parse_play_again 純函式
│   └── test_architecture.py # AST 檢查：engine.py 無 input/print、無 cli 匯入
└── integration/
    └── test_cli_flow.py     # 以注入的 input_fn／output_fn 腳本化驅動 run()，驗證完整流程與日誌
```

**Structure Decision**: 採單一專案（Option 1 精簡版）。`src/guessing_game/` 內以兩個模組落實兩層架構：
`engine.py`（邏輯）與 `cli.py`（I/O）。不建立 `models/`、`services/`、`lib/` 等額外層級，
以符合憲章「維持精簡」的限制。`cli.run()` 接受可注入的 `input_fn`／`output_fn`，
讓整合測試不需真實終端機；`GameEngine` 的測試完全不涉及 I/O。

## Complexity Tracking

無憲章違規，無需填寫。
