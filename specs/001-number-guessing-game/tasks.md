---

description: "終端機猜數字遊戲的任務清單"
---

# Tasks: 終端機猜數字遊戲

**Input**: Design documents from `/specs/001-number-guessing-game/`

**Prerequisites**: plan.md、spec.md、research.md、data-model.md、contracts/、quickstart.md

**Tests**: 本專案 MUST 包含測試（憲章原則 IV）。各 User Story 階段內採「測試先行」：先寫測試並確認失敗，再實作。

**Organization**: 任務依 User Story 分組。P1：US1、US2（合起來為 MVP）；P2：US3、US4。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可平行執行（不同檔案、無未完成的相依）
- **[Story]**: 任務所屬的 User Story（US1–US4）
- 每項任務皆含精確檔案路徑

## Path Conventions

單一專案：`src/guessing_game/`、`tests/unit/`、`tests/integration/`（見 plan.md）。

## 全域規範（適用於所有任務）

- 所有函式與方法（**含測試函式與測試輔助函式**）MUST 有完整 type hints（測試函式回傳 `-> None`）與 Google 風格 docstring（憲章原則 II）。
- `engine.py` MUST NOT 呼叫 `input()`／`print()`、MUST NOT 匯入 `cli`、MUST NOT 使用 logging（憲章原則 III）。
- 日誌等級固定 INFO、輸出至 `sys.stdout`，僅三類事件，且 MUST NOT 含秘密數字或每次猜測內容（憲章原則 V、FR-017）。
- 訊息字串 MUST 與 `contracts/cli-contract.md` 的訊息表完全一致。
- 使用 `caplog` 的測試 MUST 先呼叫 `caplog.set_level(logging.INFO, logger="guessing_game")`，因為未呼叫 `configure_logging()` 時，INFO 訊息不會被記錄。

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 專案骨架與測試設定

- [ ] T001 依 plan.md 建立目錄結構：`src/guessing_game/`（含空的 `__init__.py`）、`tests/unit/`、`tests/integration/`
- [ ] T002 建立 `pyproject.toml`，僅含 `[tool.pytest.ini_options]`：`pythonpath = ["src"]`、`testpaths = ["tests"]`；不得加入 `[project]` 或任何相依（research D9）
- [ ] T003 [P] 建立或更新儲存庫根目錄的 `.gitignore`，忽略 `__pycache__/`、`.pytest_cache/`、`*.pyc`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 所有 User Story 共用的列舉與純函式，以及架構規則的自動化檢查

**⚠️ CRITICAL**: 完成前不得開始任何 User Story

- [ ] T004 [P] 在 `tests/unit/test_cli_parsing.py` 撰寫 `parse_guess` 與 `parse_play_again` 的單元測試（先寫、須先失敗）：
  - `parse_guess`：`"42"`→42、`"1"`→1、`"100"`→100；`" 42 "`→42（忽略前後空白，FR-015）；`"0"`→0、`"101"`→101、`"-5"`→-5（格式合法、交由 engine 判斷範圍）；數字部分超過 18 位（如 `"9" * 19`）→`10**18`，`"-" + "9" * 19`→`-(10**18)`；`None` 案例：`""`、`"   "`、`"3.5"`、`"50.0"`、`"abc"`、`"#"`、`"+5"`、`"007"`、`"1_0"`、`"５"`（全形數字）
  - `parse_play_again`：`""`、`"   "`→`REPLAY`；`"n"`、`"N"`、`" n "`→`QUIT`；`"y"`、`"yes"`、`"abc"`、`"nn"`→`UNKNOWN`
- [ ] T005 [P] 建立 `src/guessing_game/engine.py`，僅含 `GuessResult(enum.Enum)`，成員 `TOO_HIGH`、`TOO_LOW`、`CORRECT`（data-model.md），附模組與類別 docstring
- [ ] T006 建立 `src/guessing_game/cli.py`：定義 `PlayAgainChoice(enum.Enum)`（`REPLAY`、`QUIT`、`UNKNOWN`）、`parse_guess(raw: str) -> int | None`（`strip()` 後以 `^-?(0|[1-9][0-9]*)$` 判定，使用 `[0-9]` 不得用 `\d`／`isdigit()`；數字部分超過 18 位時直接回傳 `±10**18`、不呼叫 `int()`；不符格式回傳 `None`）、`parse_play_again(raw: str) -> PlayAgainChoice`（`strip()` 後空字串→`REPLAY`、`lower()` 等於 `"n"`→`QUIT`、其他→`UNKNOWN`）；使 T004 的測試通過（依賴 T004）
- [ ] T007 [P] 在 `tests/unit/test_architecture.py` 以 `ast` 解析 `src/guessing_game/engine.py`，斷言：(1) 不存在對 `input`、`print` 的呼叫；(2) 不存在 `import cli`、`from guessing_game import cli`、`from guessing_game.cli import ...` 或 `from . import cli` 等匯入；(3) 不匯入 `logging`（依賴 T005）

**Checkpoint**: 列舉與純函式就緒，架構檢查可運作 — User Story 可開始

---

## Phase 3: User Story 1 - 開始遊戲 (Priority: P1) 🎯 MVP

**Goal**: 開局時由系統以可注入的隨機來源產生 1–100 的秘密數字，並在 CLI 進入點初始化日誌、記錄「新局開始」。

**Independent Test**: 執行 `tests/unit/test_engine.py` 的開局測試與 `tests/integration/test_cli_flow.py` 的 US1 測試：engine 以 `randint(1, 100)` 產生秘密數字且初始狀態正確；`run()` 開局時記錄一次「新局開始」。

### Tests for User Story 1 ⚠️（先寫、須先失敗）

- [ ] T008 [P] [US1] 在 `tests/unit/test_engine.py` 撰寫開局測試：定義測試用 `RecordingRandom(random.Random)`，覆寫 `randint` 以記錄參數並回傳固定值；斷言建構 `GameEngine(rng)` 時 `randint` 以 `(1, 100)` 被呼叫恰好一次；`MIN_NUMBER == 1`、`MAX_NUMBER == 100`；初始 `attempts == 0`、`is_finished is False`；呼叫 `start_new_round()` 後 `randint` 再次以 `(1, 100)` 被呼叫、`attempts == 0`、`is_finished is False`；未提供 `rng` 時可正常建構（FR-001、SC-002）
- [ ] T009 [P] [US1] 在 `tests/integration/test_cli_flow.py` 撰寫 US1 測試：`configure_logging()` 後 `logging.getLogger("guessing_game")` 含恰好一個綁定 `sys.stdout` 的 `StreamHandler`、等級為 `logging.INFO`，連續呼叫兩次仍只有一個 handler（測試結束需移除該 handler 並還原等級）；以注入固定 `RecordingRandom`（`randint` 回傳 50）的 engine 與輸入腳本 `["50", "n"]` 呼叫 `run()` 時，`caplog` 中「新局開始」恰好出現一次且為 INFO 等級（FR-017）；此腳本在 US1 階段不會被消耗，US2 起消耗 `"50"`，US4 起消耗 `"n"`，因此在各階段皆有效

### Implementation for User Story 1

- [ ] T010 [US1] 在 `src/guessing_game/engine.py` 實作 `GameEngine`：類別常數 `MIN_NUMBER = 1`、`MAX_NUMBER = 100`；`__init__(self, rng: random.Random | None = None) -> None`（預設 `random.Random()`，建構時即開始第一局）；`start_new_round()`（以 `rng.randint(MIN_NUMBER, MAX_NUMBER)` 產生私有 `_secret`，`_attempts = 0`，`_finished = False`）；唯讀屬性 `attempts`、`is_finished`；秘密數字 MUST NOT 有任何公開讀取方式（FR-002；依賴 T005、T008）
- [ ] T011 [US1] 在 `src/guessing_game/cli.py` 新增：`configure_logging() -> None`（設定套件 logger `logging.getLogger("guessing_game")`：等級 `logging.INFO`、`StreamHandler(sys.stdout)`、格式 `"%(levelname)s %(message)s"`；重複呼叫不得產生重複 handler；僅供 `main()` 呼叫）；`run(input_fn: Callable[[str], str] = input, output_fn: Callable[[str], None] = print, engine: GameEngine | None = None) -> int` 骨架：未提供 engine 時建立 `GameEngine()`、以 `logging.getLogger(__name__).info("新局開始")` 記錄後回傳 `0`（主迴圈於 US2 加入）；`main() -> int`（先 `configure_logging()` 再 `return run()`）（依賴 T006、T009、T010）
- [ ] T012 [US1] 建立 `src/guessing_game/__main__.py`：`raise SystemExit(main())`（匯入 `guessing_game.cli.main`），使 `PYTHONPATH=src python3 -m guessing_game` 可執行（依賴 T011）

**Checkpoint**: US1 可獨立驗證 — engine 開局與日誌初始化皆有測試涵蓋

---

## Phase 4: User Story 2 - 猜測與提示 (Priority: P1) 🎯 MVP

**Goal**: 玩家輸入猜測後得到「太大」、「太小」或「答對」，答對即結束本局。

**Independent Test**: 在固定秘密數字（例如 50）下，輸入 70、30、50，依序顯示 `太大`、`太小`、`答對` 並結束本局；US1 + US2 即為最小可玩版本。

### Tests for User Story 2 ⚠️（先寫、須先失敗）

- [ ] T013 [P] [US2] 在 `tests/unit/test_engine.py` 新增 `guess()` 測試（秘密數字固定為 50）：`guess(70)`→`TOO_HIGH`、`guess(30)`→`TOO_LOW`、`guess(50)`→`CORRECT` 且 `is_finished is True`；每次有效猜測 `attempts` 加 1；答對後再次 `guess()` 拋 `RuntimeError` 且狀態不變；答對後 `start_new_round()` 使 `attempts == 0`、`is_finished is False`；以 `random.Random(seed)` 對至少 100 個不同種子，用二分搜尋找出秘密數字，斷言皆能在 1–100 內答對（SC-002）；對 1 到 100 每個秘密數字以二分搜尋策略模擬遊玩，斷言皆在 7 次有效猜測內答對（SC-006）
- [ ] T014 [P] [US2] 在 `tests/integration/test_cli_flow.py` 新增 US2 測試：以固定秘密數字 50 的 engine 與腳本化 `input_fn`／`output_fn` 呼叫 `run()`，輸入序列 `["70", "30", "50", "n"]`（結尾的 `"n"` 在 US2 階段不會被消耗，US4 起用於回應「是否再玩」），斷言輸出依序含 `太大`、`太小`、`答對`；答對後 `engine.is_finished is True`；`input_fn` 收到的提示字串為 `請輸入猜測（1-100）：`（FR-003～FR-006）；另斷言除最後的 `答對` 訊息外，答對前所有 `output_fn` 輸出皆不含秘密數字 `"50"`（FR-002）

### Implementation for User Story 2

- [ ] T015 [US2] 在 `src/guessing_game/engine.py` 實作 `GameEngine.guess(self, value: int) -> GuessResult`：本局已結束→拋 `RuntimeError` 且狀態不變；`value > _secret`→`_attempts += 1` 並回傳 `TOO_HIGH`；`value < _secret`→`_attempts += 1` 並回傳 `TOO_LOW`；`value == _secret`→`_attempts += 1`、`_finished = True` 並回傳 `CORRECT`（範圍檢查於 US3 加入；依賴 T010、T013）
- [ ] T016 [US2] 在 `src/guessing_game/cli.py` 的 `run()` 加入猜測迴圈：以 `input_fn("請輸入猜測（1-100）：")` 讀取，經 `parse_guess` 取得整數後呼叫 `engine.guess()`，依結果以 `output_fn` 輸出 `太大`／`太小`／`答對`；答對即離開迴圈並回傳 `0`；`parse_guess` 回傳 `None` 時，暫時直接重新提示、不呼叫 `engine.guess()`（錯誤訊息與範圍外處理於 US3 加入，此階段範圍外的數字仍會被 engine 計次）（依賴 T011、T014、T015）

**Checkpoint**: US1 + US2 皆可獨立運作 — MVP 可玩

---

## Phase 5: User Story 3 - 輸入驗證 (Priority: P2)

**Goal**: 非整數或超出範圍的輸入得到明確錯誤訊息，且不消耗猜測次數、不改變本局狀態。

**Independent Test**: 在遊戲進行中輸入 `abc`、`3.5`、`+5`、`007`、空白、`0`、`101`、`-5`，每次都顯示對應錯誤訊息並重新提示，`engine.attempts` 不增加。

### Tests for User Story 3 ⚠️（先寫、須先失敗）

- [ ] T017 [P] [US3] 在 `tests/unit/test_engine.py` 新增範圍測試：`is_valid_guess(1)`、`is_valid_guess(100)` 為 `True`；`is_valid_guess(0)`、`is_valid_guess(101)`、`is_valid_guess(-5)` 為 `False`；`guess(0)`、`guess(101)`、`guess(-5)` 拋 `ValueError`，且 `attempts`、`is_finished` 皆不變；邊界值 1 與 100 為有效猜測（FR-008、FR-009）
- [ ] T018 [P] [US3] 在 `tests/integration/test_cli_flow.py` 新增 US3 測試：固定秘密數字 50，輸入序列 `["abc", "3.5", "+5", "007", "", "0", "101", "-5", " 42 ", "50", "n"]`（結尾的 `"n"` 在 US3 階段不會被消耗，US4 起用於回應「是否再玩」）；斷言格式無效者（前五項）輸出 `輸入無效：請輸入 1 到 100 的整數。`，範圍外者（`0`、`101`、`-5`）輸出 `輸入無效：數字必須介於 1 到 100 之間。`；每次錯誤後重新提示；最終 `engine.attempts == 2`（僅 `" 42 "` 與 `"50"` 計次，FR-009、FR-015）；另斷言答對前所有 `output_fn` 輸出皆不含秘密數字 `"50"`（錯誤訊息只含「1」、「100」，FR-002）

### Implementation for User Story 3

- [ ] T019 [US3] 在 `src/guessing_game/engine.py` 新增 `is_valid_guess(self, value: int) -> bool`（`MIN_NUMBER <= value <= MAX_NUMBER`），並讓 `guess()` 在範圍外時於任何狀態變更之前拋 `ValueError`（檢查順序：先範圍、再是否已結束，兩者皆不得改變狀態；依賴 T015、T017）
- [ ] T020 [US3] 在 `src/guessing_game/cli.py` 的 `run()` 猜測迴圈處理無效輸入：`parse_guess` 回傳 `None`→輸出 `輸入無效：請輸入 1 到 100 的整數。`；`engine.is_valid_guess()` 為 `False`→輸出 `輸入無效：數字必須介於 1 到 100 之間。`；兩者皆不呼叫 `engine.guess()`、不計次，並重新提示（依賴 T016、T018、T019）

**Checkpoint**: US1–US3 皆可獨立運作

---

## Phase 6: User Story 4 - 結束與再玩 (Priority: P2)

**Goal**: 答對後顯示總猜測次數並詢問是否再玩；Enter 再玩、`n`／`N` 離開、其他輸入重新詢問；記錄「本局結束」與「玩家離開」。

**Independent Test**: 完成一局後看到 `答對！你總共猜了 N 次。` 與再玩提示；分別輸入 Enter、`n`、`y` 驗證行為與日誌。

### Tests for User Story 4 ⚠️（先寫、須先失敗）

- [ ] T021 [P] [US4] 在 `tests/integration/test_cli_flow.py` 新增 US4 測試（使用依序回傳固定值的 `SequenceRandom(random.Random)` 讓兩局秘密數字為 50 與 20）：
  - 答對後輸出 `答對！你總共猜了 3 次。`（例：輸入 `["70", "30", "50"]`），且 `input_fn` 收到提示 `再玩一局？按 Enter 再玩，輸入 n 離開：`（FR-010、FR-011）
  - 再玩輸入 `""` → 開始新局、`engine.attempts == 0`、秘密數字重新產生，`caplog` 出現第二次 `新局開始`（FR-012）
  - 輸入 `"n"` 與 `"N"`（分別各一個測試）→ 輸出 `再見！`、回傳 `0`、日誌含 `玩家離開（原因：n）`（FR-013）
  - 輸入 `"y"`、`"abc"` → 輸出 `請按 Enter 再玩，或輸入 n 離開。` 並重新詢問，不開新局也不結束（FR-016）
  - 答對時日誌含 `本局結束，總猜測次數：3`（FR-017）

### Implementation for User Story 4

- [ ] T022 [US4] 在 `src/guessing_game/cli.py` 的 `run()` 擴充：答對後輸出 `答對！你總共猜了 {engine.attempts} 次。`（取代 US2 僅輸出 `答對` 的行為，仍須含「答對」二字）並記錄 `本局結束，總猜測次數：{attempts}`；以 `input_fn("再玩一局？按 Enter 再玩，輸入 n 離開：")` 詢問並交給 `parse_play_again`：`REPLAY`→`engine.start_new_round()`、記錄 `新局開始`、回到猜測迴圈；`QUIT`→輸出 `再見！`、記錄 `玩家離開（原因：n）`、回傳 `0`；`UNKNOWN`→輸出 `請按 Enter 再玩，或輸入 n 離開。` 並重新詢問；首局開局的 `新局開始` 記錄維持於 US1 的位置（依賴 T020、T021）

**Checkpoint**: 四個 User Story 皆完整運作

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: 跨 Story 的需求（中斷處理、日誌限制、風格檢查）與最終驗證

- [ ] T023 [P] 在 `tests/integration/test_cli_flow.py` 撰寫中斷測試（先寫、須先失敗）：以會拋出 `KeyboardInterrupt` 或 `EOFError` 的 `input_fn`，分別在「猜測階段」與「是否再玩階段」各測一次，共 4 個情境；斷言：`run()` 回傳 `0`、不向外傳播例外、`output_fn` 收到 `已離開遊戲，再見！`（此訊息之前先輸出一個換行）、日誌含 `玩家離開（原因：Ctrl+C）` 或 `玩家離開（原因：輸入結束）`（FR-014、SC-005）
- [ ] T024 在 `src/guessing_game/cli.py` 以單一 `try/except (KeyboardInterrupt, EOFError)` 包住 `run()` 的整個遊戲迴圈：捕捉後輸出換行與 `已離開遊戲，再見！`、依例外類型記錄 `玩家離開（原因：Ctrl+C）` 或 `玩家離開（原因：輸入結束）`、回傳 `0`；不得顯示堆疊追蹤（research D6；依賴 T022、T023）
- [ ] T025 在 `tests/integration/test_cli_flow.py` 新增日誌限制測試：以固定秘密數字 73 完整跑一局（含無效輸入、答對、再玩、`n` 離開），收集 `caplog` 所有訊息，斷言：每則皆為 INFO；訊息集合僅屬「新局開始」、「本局結束，總猜測次數：N」、「玩家離開（原因：…）」三類；任何日誌訊息皆不含秘密數字 `73`，也不含任何猜測輸入內容（FR-002、FR-017；依賴 T024）
- [ ] T026 [P] 在 `tests/unit/test_style.py` 以 `ast` 掃描 `src/` 與 `tests/` 下所有 `.py` 檔中的每個函式與方法（含測試函式），斷言皆有 docstring、所有參數（`self`／`cls` 除外）與回傳值皆有型別註記（憲章原則 II）
- [ ] T027 執行 `python3 -m pytest` 並修正所有失敗，直到全數通過；此步驟同時驗證 T007（架構規則）與 T026（風格規則）
- [ ] T028 依 `specs/001-number-guessing-game/quickstart.md` 執行手動驗證情境 1–13 與結束碼範例（`printf '\n' | PYTHONPATH=src python3 -m guessing_game; echo "exit=$?"`），記錄任何與規格不符之處並回頭修正
- [ ] T029 人工對照 Google Python Style Guide 審查 `src/guessing_game/` 與 `tests/` 的所有檔案並修正缺失：命名（函式與變數 `snake_case`、類別 `PascalCase`、常數 `UPPER_SNAKE_CASE`）、單行長度不超過 80 字元、import 分組與排序（標準函式庫→第三方→本專案）、docstring 使用 `Args:`／`Returns:`／`Raises:` 區塊；此項無法以標準函式庫自動檢查，故為人工審查（憲章原則 II）

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 無相依，可立即開始
- **Foundational (Phase 2)**: 依賴 Setup 完成 — 阻擋所有 User Story
- **User Stories (Phase 3–6)**: 皆依賴 Foundational 完成；由於 US2、US3、US4 都修改同一組檔案（`engine.py`、`cli.py`、`test_engine.py`、`test_cli_flow.py`），**建議依優先順序循序進行**（US1 → US2 → US3 → US4）
- **Polish (Phase 7)**: 依賴所有 User Story 完成

### User Story Dependencies

- **US1 (P1)**: Foundational 之後即可開始；無其他 Story 相依
- **US2 (P1)**: 依賴 US1 的 `GameEngine` 與 `run()` 骨架；可獨立驗證（固定秘密數字）
- **US3 (P2)**: 依賴 US2 的 `guess()` 與猜測迴圈；可獨立驗證
- **US4 (P2)**: 依賴 US2 的答對流程；其驗證不依賴 US3 的錯誤訊息

### Within Each User Story

- 測試先寫並確認失敗，再實作
- engine（邏輯層）先於 cli（I/O 層）
- 同一檔案的任務不得平行

### Parallel Opportunities

- Phase 1：T003 可與 T001、T002 平行
- Phase 2：T004 與 T005 可平行；T007 在 T005 之後可與 T006 平行
- 各 User Story 內的兩個測試任務可平行（分屬 `test_engine.py` 與 `test_cli_flow.py`）：T008 ∥ T009、T013 ∥ T014、T017 ∥ T018
- Phase 7：T023 與 T026 可平行（不同檔案）；T025 與 T023 同檔，須循序

---

## Parallel Example: User Story 2

```bash
# 同時撰寫 US2 的兩組測試（不同檔案）：
Task: "在 tests/unit/test_engine.py 新增 guess() 測試（T013）"
Task: "在 tests/integration/test_cli_flow.py 新增 US2 測試（T014）"

# 測試確認失敗後，依序實作：
Task: "在 src/guessing_game/engine.py 實作 GameEngine.guess（T015）"
Task: "在 src/guessing_game/cli.py 加入猜測迴圈（T016）"
```

---

## Implementation Strategy

### MVP First（US1 + US2）

1. 完成 Phase 1：Setup
2. 完成 Phase 2：Foundational
3. 完成 Phase 3：US1
4. 完成 Phase 4：US2
5. **STOP and VALIDATE**：執行 `python3 -m pytest`，並手動玩一局確認可猜到答對（已知限制：此階段輸入無效格式時只會重新提示且沒有錯誤訊息，超出 1–100 的數字會被計次；US3 完成後才符合 FR-007～FR-009）
6. 此時已是最小可玩版本（規格中 US1 與 US2 合併即為 MVP）

### Incremental Delivery

1. Setup + Foundational → 基礎就緒
2. US1 + US2 → MVP 可玩
3. US3 → 輸入驗證完整
4. US4 → 完整的結束與再玩循環
5. Polish → 中斷處理、日誌限制、風格檢查、quickstart 驗證

---

## Notes

- [P] 任務 = 不同檔案、無未完成相依
- [Story] 標籤用於追溯任務到 spec.md 的 User Story
- 憲章原則 IV 要求測試，因此每個 Story 都包含測試任務，且測試先於實作
- 每完成一項任務或一組邏輯相關任務後即可 commit
- 避免：模糊任務、同檔案衝突、破壞 Story 獨立性的跨 Story 相依
