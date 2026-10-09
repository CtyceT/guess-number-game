---

description: "Task list template for feature implementation"
---

# Tasks: CI 測試品質與效能量測擴充

**Input**: Design documents from `/specs/003-ci-test-quality-perf/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md
(all present under `specs/003-ci-test-quality-perf/`)

**Tests**: 本功能未要求測試任務。這是 CI 設定與量測工具變更（非遊戲核心邏輯），
spec.md 與 plan.md 皆未要求新增 pytest 測試；每個使用者故事以本機與 Azure DevOps 的
手動驗證（`quickstart.md`）作為獨立測試依據。

**Organization**: 任務依 spec.md 的三個使用者故事分組（P1 → P2 → P3），皆建立在既有的
`azure-pipelines.yml` 與 `sonar-project.properties` 上，`src/` 下任何檔案 MUST NOT 被修改。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可平行進行（不同檔案、不依賴尚未完成的任務）
- **[Story]**: 對應 spec.md 的 US1／US2／US3
- 每個任務皆附確切檔案路徑

## Path Conventions

- 單一專案：`src/`、`tests/`、`benchmarks/`、`azure-pipelines.yml`、`sonar-project.properties`
  皆位於 repo 根目錄（見 plan.md Project Structure）

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 三個使用者故事共用的最小前置設定

- [X] T001 [P] 在 `.gitignore` 新增三行：`test-results.xml`、`coverage.xml`、
  `benchmark_summary.md`，確保 US1／US2／US3 各自產生的 CI 報告檔永不被提交進版本控制
  （對應 `plan.md` Project Structure 的 `.gitignore` 異動項）。

**Checkpoint**: `.gitignore` 就位，三個使用者故事都可以安全產生自己的報告檔。

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 三個使用者故事皆依賴的阻斷性前置工作

本功能沒有額外的阻斷性前置任務：三個使用者故事各自修改 `azure-pipelines.yml` 的不同
區段（US1/US2 插入在既有 pytest 步驟與 `SonarCloudAnalyze@4` 之間；US3 新增在
`SonarCloudPublish@4` 之後），且 `trigger`／`pr`／`SonarCloudPrepare@4`／
`UsePythonVersion@0` 等既有設定維持不變（`research.md` D1、D4），不需要先建立任何共用的
新模型、新服務或新框架。完成 Phase 1 後可直接進入 Phase 3。

**Checkpoint**: 無額外前置任務；Setup 完成即可開始 Phase 3。

---

## Phase 3: User Story 1 - 測試成功率可視化 (Priority: P1) 🎯 MVP

**Goal**: pipeline 摘要呈現每個測試案例的通過/失敗狀態與整體成功率。

**Independent Test**: 推送一次包含至少一項失敗測試的 commit，觀察 Azure DevOps 執行結果的
Tests 分頁是否顯示逐案例通過/失敗與整體成功率；再推送一次全部通過的版本，確認成功率顯示
為 100%。

### Implementation for User Story 1

- [X] T002 [US1] 修改 `azure-pipelines.yml` 中既有的
  `displayName: 'Install pytest and run existing test suite'` 步驟，將
  `python -m pytest` 改為 `python -m pytest --junitxml=test-results.xml`（`pip install`
  那一行此階段先維持 `python -m pip install --upgrade pip pytest` 不變，`pytest-cov` 由
  US2 加入），並將 `displayName` 更新為 `'Run test suite with JUnit results'`
  （對應 `contracts/pipeline-steps.md` §1 的中繼狀態；最終文字由 T005 補上
  `pytest-cov`）。
- [X] T003 [US1] 在 `azure-pipelines.yml` 中，於 T002 修改的步驟之後、`SonarCloudAnalyze@4`
  之前，新增一個 `PublishTestResults@2` 步驟：`condition: succeededOrFailed()`（測試失敗時
  仍要發布，讓開發者看到哪些測試失敗），`testResultsFormat: 'JUnit'`，
  `testResultsFiles: 'test-results.xml'`，`testRunTitle: '猜數字遊戲 pytest 結果'`，
  `failTaskOnMissingResultsFile: true`（完全找不到結果檔時這個任務本身也標示失敗，呼應
  FR-013）（對應 `contracts/pipeline-steps.md` §2 第一個任務）。
- [X] T004 [US1] 依 `specs/003-ci-test-quality-perf/quickstart.md` 的「1. 測試成功率 +
  覆蓋率報告」本機驗證步驟，執行
  `python -m pytest --junitxml=test-results.xml`，確認 repo 根目錄產生格式正確的 JUnit
  `test-results.xml`；完成後可將該檔刪除或留給 T001 的 `.gitignore` 忽略。

**Checkpoint**: User Story 1 可獨立交付並測試——即使尚未實作 US2/US3，推送後的 pipeline
已能在 Tests 分頁呈現逐案例結果與整體成功率。

---

## Phase 4: User Story 2 - 測試覆蓋率報告 (Priority: P2)

**Goal**: pipeline 摘要與 SonarQube Cloud 皆呈現測試覆蓋率，並可識別未覆蓋的程式碼位置。

**Independent Test**: 推送一次 commit，確認 pipeline 摘要的 Code Coverage 分頁顯示整體
覆蓋率百分比，且 SonarQube Cloud 對應專案頁面也顯示覆蓋率與未覆蓋的程式碼位置。

### Implementation for User Story 2

- [X] T005 [US2] 修改 `azure-pipelines.yml` 中 T002 的同一個步驟：`pip install` 那一行改為
  `python -m pip install --upgrade pip pytest pytest-cov`；`pytest` 指令延伸為
  `python -m pytest --junitxml=test-results.xml --cov=src --cov-report=xml`；
  `displayName` 更新為 `'Install pytest/pytest-cov and run test suite with coverage'`
  （對應 `contracts/pipeline-steps.md` §1 最終狀態）。
- [X] T006 [US2] 在 `azure-pipelines.yml` 中，於 T003 新增的 `PublishTestResults@2` 步驟
  之後、`SonarCloudAnalyze@4` 之前，新增一個 `PublishCodeCoverageResults@2` 步驟：**不設定**
  `condition`（沿用預設的 `succeeded()`，測試步驟失敗時這個任務不執行、覆蓋率不會被發布，
  對應 spec.md 的 Edge Case 與 SC-002「100% 的 pipeline 成功執行」），
  `summaryFileLocation: 'coverage.xml'`，`pathToSources: 'src'`，
  `failIfCoverageEmpty: true`（覆蓋率報告為空或遺失時這個任務自己標示失敗，呼應
  FR-013）（對應 `contracts/pipeline-steps.md` §2 第二個任務）。
- [X] T007 [P] [US2] 在 `sonar-project.properties` 檔尾新增一行
  `sonar.python.coverage.reportPaths=coverage.xml`，其餘內容不變，讓既有的
  `SonarCloudAnalyze@4` 步驟讀到 `coverage.xml`（對應 `contracts/pipeline-steps.md` §3，
  以及 FR-006 對 spec 002 FR-009 的取代）。
- [X] T008 [US2] 確認 `sonar-project.properties`（T007 修改後）未殘留任何覆蓋率排除設定
  （目前檔案本就沒有 `sonar.coverage.exclusions` 之類設定，僅需覆核一次，確保 FR-006
  的取代規則沒有被既有設定抵銷）。
- [X] T009 [US2] 依 `quickstart.md` 的「1. 測試成功率 + 覆蓋率報告」本機驗證步驟，執行
  `python -m pytest --junitxml=test-results.xml --cov=src --cov-report=xml`，確認
  `coverage.xml` 產生且為 Cobertura 格式（可用文字編輯器確認根元素為
  `<coverage ...>` 並含 `line-rate` 屬性）。

**Checkpoint**: User Story 1 與 2 皆可獨立運作——pipeline 摘要同時呈現測試成功率與覆蓋率，
SonarQube Cloud 亦顯示覆蓋率。

---

## Phase 5: User Story 3 - 猜數字遊戲效能量測 (Priority: P3)

**Goal**: 每次 CI 自動執行猜數字遊戲 10 次（透過既有 `cli.run()` 介面、固定種子與固定
猜測序列），將平均 CPU 時間、記憶體用量、回應時間顯示在 pipeline 的 Extensions 摘要分頁，
且效能數值不影響 pipeline 整體成功/失敗判定。

**Independent Test**: 推送一次 commit，確認 pipeline 執行摘要的 Extensions 分頁顯示
`benchmark_summary.md` 的內容（10 次樣本的平均 CPU 時間／記憶體用量／回應時間），且無論
數值為何，pipeline 整體結果不受影響。

### Implementation for User Story 3

- [X] T010 [P] [US3] 建立 `benchmarks/bench_driver.py`：依 `research.md` D5 設計，使用固定
  種子 `SEED = 20261009`——
  (a) 先用固定種子 `SEED` 建立一個只在本函式內使用的「影子」
  `GameEngine(rng=random.Random(SEED))`，以二分搜尋演算法（`low=GameEngine.MIN_NUMBER`、
  `high=GameEngine.MAX_NUMBER`）重複呼叫 `guess(mid)` 直到 `is_finished`，記錄下每一步的
  `mid` 值，得到一份固定的猜測數字列表；(b) 用**同一個** `SEED` 建立另一個全新的
  `GameEngine(rng=random.Random(SEED))`，把猜測列表（轉成字串）尾端加上 `"n"`
  包成一個 `input_fn`（每次呼叫回傳序列中的下一個值），`output_fn` 為捨棄輸出的
  no-op（`lambda _: None`，不比對任何輸出文字），呼叫
  `guessing_game.cli.run(input_fn=input_fn, output_fn=output_fn, engine=engine)`
  完成一局；(c) 回傳／以該呼叫的結果作為本模組（獨立執行時）的結束碼。模組只能匯入
  `guessing_game.engine`、`guessing_game.cli` 與標準函式庫，MUST NOT 修改 `src/` 下任何
  檔案。
- [X] T011 [P] [US3] 建立 `benchmarks/measure_once.py`：以 `subprocess.run([sys.executable,
  "benchmarks/bench_driver.py"], ...)` 執行恰好一次 `bench_driver.py`（其唯一子行程），
  在呼叫前後以 `time.perf_counter()` 量測 `response_time_s`；呼叫後立即以
  `resource.getrusage(resource.RUSAGE_CHILDREN)` 取得 `cpu_time_s`（`ru_utime+ru_stime`）
  與 `max_rss_kb`（`ru_maxrss`）；依 `contracts/benchmark-ipc.md` 的 JSON schema，印出恰好
  一行 JSON 至 stdout（成功時 `ok: true, error: null`；`bench_driver.py` 結束碼非 0 時，
  印出 `ok: false` 與簡短 `error` 訊息，三個數值欄位為 `null`）；`measure_once.py` 本身
  MUST 永遠以結束碼 0 結束（不得把子行程的失敗往上傳播為自己的非零結束碼）。
- [X] T012 [US3] 建立 `benchmarks/run_benchmarks.py`：以全新 Python 行程重複呼叫
  `benchmarks/measure_once.py` 10 次（每次都是獨立 `subprocess.run()`），逐行解析
  `contracts/benchmark-ipc.md` 定義的 JSON（解析失敗或行程結束碼非 0 視同該筆樣本
  `ok=false`，記錄錯誤訊息，不中止其餘樣本的量測）；依 `data-model.md` 的驗證規則，平均值
  （`avg_response_time_s`、`avg_cpu_time_s`、`avg_max_rss_kb`）只採計 `ok == true` 的樣本，
  若全部 10 筆皆失敗，平均值欄位 MUST 為 `null`（不得以 0 代表結果良好）；將 `sample_count`
  （固定 10）、`ok_count`、三個平均值與逐筆樣本寫成 Markdown 表格，存至 repo 根目錄的
  `benchmark_summary.md`。依賴 T010、T011。
- [X] T013 [US3] 在 `benchmarks/run_benchmarks.py` 寫出 `benchmark_summary.md` 之後，印出
  `##vso[task.uploadsummary]<benchmark_summary.md 的絕對路徑>` 作為腳本的最後一步標準輸出
  （對應 `research.md` D7），並確保整個 `run_benchmarks.py`（含上游 T012 的彙總邏輯）
  無論樣本成功與否 MUST 永遠以結束碼 0 結束。依賴 T012。
- [X] T014 [US3] 在 `azure-pipelines.yml` 的 `SonarCloudPublish@4` 步驟之後新增一個步驟：
  `script: python benchmarks/run_benchmarks.py`，
  `displayName: 'Run guessing game performance benchmark (10 runs, stdlib only)'`，
  `continueOnError: true`（對應 `contracts/pipeline-steps.md` §4，落實 FR-010／FR-015）。
  依賴 T012、T013。
- [X] T015 [US3] 為 `benchmarks/bench_driver.py`、`benchmarks/measure_once.py`、
  `benchmarks/run_benchmarks.py` 內的每個函式補上完整的 type hints（參數與回傳值）與
  Google 風格 docstring（至少說明用途，適用時含 `Args:`／`Returns:`／`Raises:`），符合
  專案憲章原則 II。依賴 T010、T011、T012。
- [X] T016 [US3] 依 `quickstart.md` 的「2. 效能量測腳本」與「3. 確認未修改 src/」本機驗證：
  (a) 連續執行兩次 `python benchmarks/run_benchmarks.py`，確認兩次的平均 CPU 時間／回應
  時間相近，記憶體峰值未出現被先前執行污染的異常模式；(b) 暫時讓 `bench_driver.py` 的
  二分搜尋故意失敗一次（例如暫時改一個會拋例外的分支，驗證完還原），確認
  `run_benchmarks.py` 仍以結束碼 0 結束並在摘要中標示該筆樣本失敗；(c) 執行
  `git status --short src/`，確認無任何輸出。依賴 T010–T014。

**Checkpoint**: 三個使用者故事皆可獨立運作；US3 新增的 `benchmarks/` 與 pipeline 末端步驟
不影響 US1／US2 既有行為。

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 跨三個使用者故事的最終確認

- [X] T017 [P] 比對 `azure-pipelines.yml` 完成後的步驟順序與
  `specs/003-ci-test-quality-perf/contracts/pipeline-steps.md` 的目標狀態是否一致：
  `checkout` → `SonarCloudPrepare@4` → `UsePythonVersion@0` → pytest 步驟（T005）→
  `PublishTestResults@2`（T003）→ `PublishCodeCoverageResults@2`（T006）→
  `SonarCloudAnalyze@4` → `SonarCloudPublish@4` → 效能量測步驟（T014）；並確認
  `trigger.branches.include` 仍只有 `main`、`pr: none` 未被改動（FR-001），逐行比對這兩個
  區塊與修改前的 `azure-pipelines.yml`。
- [X] T018 依 `specs/003-ci-test-quality-perf/quickstart.md` 完整跑一次本機驗證（US1、
  US2、US3 全部步驟），並再次執行 `git status --short src/` 確認輸出為空、檢查本次異動的
  所有檔案（`azure-pipelines.yml`、`sonar-project.properties`、`.gitignore`、
  `benchmarks/*.py`）內未出現任何密碼或 token 字面值（對應 FR-012）。依賴 T001–T016。
- [ ] T019 推送到 `main` 分支，依 `quickstart.md`「Azure DevOps 驗證」一節，在 Azure
  DevOps 介面核對五項：Tests 分頁（US1）、Code Coverage 分頁（US2）、SonarQube Cloud
  覆蓋率與未覆蓋位置（US2）、Extensions 摘要分頁的 `benchmark_summary.md` 內容（US3）、
  pipeline 整體成功/失敗不受效能數值影響（US3）。**此為手動步驟，Claude MUST NOT 自行
  執行 `git push`**（使用者已在 `/speckit-plan` 階段明確指示）。依賴 T018。

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**：無依賴，可立即開始。
- **Foundational (Phase 2)**：無額外任務，Setup 完成即視為滿足。
- **User Story 1 (Phase 3)**：依賴 Phase 1 完成；T002 → T003 → T004 依序進行（皆修改／
  驗證同一個 `azure-pipelines.yml` 步驟區段）。
- **User Story 2 (Phase 4)**：依賴 Phase 3 完成（T005 延伸 T002 修改的同一個步驟；T006
  插入在 T003 之後）；T007 可與 T005／T006 平行進行（不同檔案）；T008 依賴 T007；T009
  依賴 T005。
- **User Story 3 (Phase 5)**：依賴 Phase 1 完成，與 US1／US2 的程式碼無直接依賴，但因三者
  皆修改 `azure-pipelines.yml`，實際落地時建議接續 US2 之後進行以避免編輯衝突；
  T010/T011 → T012 → T013 → T014 → T015 → T016。
- **Polish (Phase 6)**：依賴 US1、US2、US3 皆完成。

### Parallel Opportunities

- T001（Setup）可獨立先行。
- T007（US2，`sonar-project.properties`）可與 T005／T006（US2，`azure-pipelines.yml`）
  平行進行。
- T010、T011（US3，`bench_driver.py` 與 `measure_once.py`）為不同檔案，可平行撰寫。
- T017（Polish，唯讀比對）可與 T018 的前半段平行進行。

---

## Parallel Example: User Story 3

```bash
# T010、T011 可同時進行（不同檔案，T012 之前完成即可）：
Task: "Create benchmarks/bench_driver.py per research.md D5"
Task: "Create benchmarks/measure_once.py per contracts/benchmark-ipc.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. 完成 Phase 1（Setup）。
2. Phase 2 無額外任務，直接進入 Phase 3。
3. 完成 Phase 3（User Story 1：T002–T004）。
4. **停下並驗證**：本機跑 `quickstart.md` 步驟 1 的 JUnit 部分；若需要，推送一次觀察
   Azure DevOps 的 Tests 分頁。
5. 此時即為可獨立交付的 MVP：pipeline 已能呈現測試成功率，覆蓋率與效能量測尚未加入。

### Incremental Delivery

1. Setup → Foundational（無額外任務）→ 基礎就位。
2. 加入 User Story 1 → 本機/CI 驗證 → 可視為 MVP。
3. 加入 User Story 2 → 本機/CI 驗證 → 覆蓋率上線。
4. 加入 User Story 3 → 本機/CI 驗證 → 效能量測上線。
5. Polish（T017–T019）收尾，含唯一一次人工 `git push` 與 Azure DevOps 實際核對。

---

## Notes

- `src/` 下任何檔案在整份任務清單中都不會被修改（FR-011／SC-006）；僅有
  `azure-pipelines.yml`、`sonar-project.properties`、`.gitignore` 與新增的 `benchmarks/`
  三個檔案會被異動。
- 效能量測（US3）刻意不比對任何畫面輸出文字——猜測序列在呼叫 `cli.run()` 之前就已用
  同一顆固定種子的「影子」engine 預先算好（見 T010 與 `research.md` D5）。
- `continueOnError: true`（T014）與腳本內部永遠回傳結束碼 0（T011、T013）是兩層獨立的
  保險，確保效能數值或量測例外都不會讓 pipeline 整體失敗（FR-010／FR-015）。
- 除 T019 外，所有任務皆可在本機完成與驗證；T019 是本功能唯一需要實際推送並在 Azure
  DevOps 觀察結果的步驟，且明確由使用者而非 Claude 執行 `git push`。
