# Phase 0 Research: CI 測試品質與效能量測擴充

## Pre-check: 既有注入點是否足以產生固定目標數字，並驅動完整的遊戲介面

檢查 `src/guessing_game/engine.py` 與 `src/guessing_game/cli.py`：

- `GameEngine.__init__(self, rng: random.Random | None = None)` 已將隨機來源外部注入；
  `start_new_round()` 僅透過 `self._rng.randint(MIN_NUMBER, MAX_NUMBER)` 產生秘密數字。
  傳入固定種子的 `random.Random(SEED)`，秘密數字即為該種子下的固定值，無需修改 `src/`。
- `GameEngine.guess(value)` 回傳 `GuessResult`（`TOO_HIGH` / `TOO_LOW` / `CORRECT`），是公開、
  非 I/O 的核心 API。
- `cli.run(input_fn: Callable[[str], str] = input, output_fn: Callable[[str], None] = print,
  engine: GameEngine | None = None) -> int`（`src/guessing_game/cli.py:140-154`）**同時**
  開放 `engine` 與 `input_fn` 兩個注入點，兩者可以一起使用：呼叫方可以傳入自建的
  `GameEngine`（帶固定種子），並以 `input_fn` 提供預先決定好的猜測序列，驅動的是遊戲的
  完整介面（`run()`），而不只是底層的 `GameEngine`。

**結論**：既有注入點（`rng` 參數 + `cli.run()` 的 `engine`／`input_fn` 參數）已足以在不修改
`src/` 的前提下，透過 `cli.run()` 這個既有遊戲介面完成一局確定性、可重現的執行。不需要停下
來回報，也不需要退而只呼叫 `GameEngine`；見 D5 的修訂設計。

## Decisions

### D1. 沿用既有觸發方式與 SonarQube Cloud 設定

- **Decision**: `azure-pipelines.yml` 的 `trigger`/`pr` 區塊與 `SonarCloudPrepare@4` 的
  `organization`/`SonarCloud` service connection 設定維持不變。
- **Rationale**: spec 003 明確限制「沿用 spec 002 的觸發方式與 SonarQube Cloud 設定」。
- **Alternatives considered**: 重新定義觸發條件或建立新的 SonarQube 專案——不符合範圍，已排除。

### D2. 測試覆蓋率：pytest-cov 產生 `coverage.xml`

- **Decision**: pytest 指令加上 `--cov=src --cov-report=xml`，產生 Cobertura 相容的
  `coverage.xml`；透過 `PublishCodeCoverageResults@2` 上傳至 pipeline 摘要，並在
  `sonar-project.properties` 新增 `sonar.python.coverage.reportPaths=coverage.xml` 讓
  SonarQube Cloud 讀取同一份報告。
- **Rationale**: 專案憲章 v1.1.0 已明確允許開發／CI 環境使用 `pytest-cov`；XML 格式可同時被
  Azure DevOps 覆蓋率發布工具與 SonarQube 的 Python coverage sensor 消費，避免重複產生報告。
- **Alternatives considered**: 僅產生 HTML 報告（機器不可讀，SonarQube 無法消費，已排除）；
  直接使用 `coverage.py` CLI 而非 `pytest-cov`（需額外一道指令整合 pytest 執行結果，較繁瑣，
  已排除，優先用憲章已核准、與 pytest 整合度更高的 `pytest-cov`）。

### D3. 測試成功率：JUnit XML + `PublishTestResults@2`

- **Decision**: pytest 指令加上 `--junitxml=test-results.xml`；透過
  `PublishTestResults@2`（`testResultsFormat: JUnit`）上傳，使 Azure DevOps 原生「Tests」
  摘要呈現每案例通過/失敗與整體成功率。
- **Rationale**: JUnit XML 是 Azure DevOps 原生支援的測試結果格式，可直接得到逐案例結果與
  彙總成功率，無需自行解析 pytest 文字輸出。
- **Alternatives considered**: 自行解析 pytest 輸出產生自訂摘要（重造輪子，已排除）。

### D4. 執行順序：pytest（含覆蓋率／測試結果產出）先於 `SonarCloudAnalyze@4`

- **Decision**: 維持現有順序（`SonarCloudPrepare@4` → `UsePythonVersion@0` → pytest 步驟 →
  `PublishTestResults@2` → `PublishCodeCoverageResults@2` → `SonarCloudAnalyze@4` →
  `SonarCloudPublish@4`），新步驟插入於既有 pytest 步驟之後、`SonarCloudAnalyze@4` 之前。
- **Rationale**: SonarQube 的靜態分析需要在分析當下讀到 `coverage.xml`，因此覆蓋率檔案必須
  在 `SonarCloudAnalyze@4` 執行前就已存在於工作目錄。
- **Alternatives considered**: 無；此為使用者明確指定的順序限制。

### D5. 效能量測驅動：透過 `cli.run()` 的 `engine` + `input_fn` 注入點，驅動完整遊戲介面

- **Decision**: `benchmarks/bench_driver.py` 不直接在自己的迴圈裡呼叫
  `GameEngine.guess()`，而是呼叫既有的遊戲介面 `cli.run(input_fn=..., output_fn=...,
  engine=...)` 來完成一局。使用的固定種子為 `SEED = 20261009`（取自本 spec 的建立日期
  2026-10-09，純粹為了好記且不需臨時決定；數值本身對正確性沒有特殊意義，換成任何其他
  固定整數同樣成立）。步驟如下：
  1. 用固定種子 `SEED` 建一個「影子」`GameEngine(rng=random.Random(SEED))`，在
     `bench_driver.py` 自己的程式碼裡（不呼叫 `run()`）以二分搜尋演算法對這個影子
     engine 重複呼叫 `guess(mid)`，記錄下每一步的猜測值，直到 `is_finished`，得到一份
     固定的猜測數字列表（例如 `[50, 75, 62, ...]`）。這一步只是「預先算出答案」，
     不牽涉 `cli.run()`。
  2. 用**同一個** `SEED` 建立另一個全新的 `GameEngine(rng=random.Random(SEED))`（因種子
     相同，產生的秘密數字與步驟 1 相同），把預先算出的猜測列表尾端加上 `"n"`，包成一個
     簡單的 `input_fn`（例如一個迭代器，每次呼叫回傳下一個值），`output_fn` 則是單純
     丟棄輸出的 no-op（不檢查、不比對任何輸出文字），然後呼叫
     `cli.run(input_fn=input_fn, output_fn=output_fn, engine=engine)`。
  3. `run()` 內部的 `_play_round` 會依序把預先算好的猜測餵給 engine，直到
     `GuessResult.CORRECT`；接著 `_wants_to_play_again` 呼叫 `input_fn` 一次，拿到
     `"n"`，回傳 `False`，`run()` 印出道別訊息並以結束碼 `0` 返回。
  `bench_driver.py` 整體仍以獨立行程執行（`python benchmarks/bench_driver.py`），作為被
  量測的「負載」本身。
- **Rationale**: 使用者要求驅動方式要符合 spec 的 Assumption「驅動既有遊戲介面完整執行
  一局」，也就是要走 `cli.run()` 這個既有的遊戲介面，而不是繞過它只呼叫底層
  `GameEngine`。`run()` 的 `engine` 與 `input_fn` 兩個參數恰好都是公開、既有的注入點，
  可以同時使用：`engine` 固定了秘密數字，`input_fn` 提供固定的猜測序列；由於猜測序列是
  在呼叫 `run()` 之前，針對同一個固定種子的「影子」engine 預先算好的，`input_fn` 完全
  不需要讀取或比對 `output_fn` 收到的任何文字（中文或其他語言的畫面字串），因此對
  `cli.py` 的畫面文字沒有任何耦合。
- **Alternatives considered**: 不透過 `cli.run()`，只在 `bench_driver.py` 自己的迴圈裡
  直接呼叫 `GameEngine.guess()`（先前版本的設計；已排除——這樣只量測到核心邏輯層，沒有
  實際執行到 `cli.py` 的 I/O 介面與迴圈邏輯，不符合 spec Assumption 明確寫出的「驅動既有
  遊戲介面完整執行一局」）；透過比對 `output_fn` 收到的中文字串（"太大"/"太小"/"答對"）
  即時決定下一個猜測（已排除——耦合於畫面文字、且使用者明確要求不需要比對任何輸出
  字串，預先算好整份猜測列表更直接也更穩健）；針對特定種子預先手算並硬編碼一組猜測
  數字常數（已排除——若未來 Python random 演算法或種子處理方式改變，硬編碼列表可能
  失效，而「用同一顆種子跑一次影子 engine 算出列表」在程式碼裡是自我一致的，種子一變
  列表也會自動跟著算對）。

### D6. 效能量測：以「每次一個子行程」量測 `RUSAGE_CHILDREN`，避免 `ru_maxrss` 失真

- **Decision**: 新增 `benchmarks/measure_once.py` 作為量測用的包裝行程：它本身以
  `subprocess.run()` 執行恰好一次 `bench_driver.py`（其唯一的子行程），並在該次
  `subprocess.run()` 前後以 `time.perf_counter()` 量測回應時間（整局總執行時間），執行後
  立即呼叫 `resource.getrusage(resource.RUSAGE_CHILDREN)` 取得 CPU 時間
  （`ru_utime + ru_stime`）與峰值記憶體（`ru_maxrss`），並將結果以單行 JSON 印至 stdout。
  `benchmarks/run_benchmarks.py` 作為協調者，對 `measure_once.py` 重複呼叫 10 次（每次都是
  全新的 Python 行程），逐行解析 JSON，彙總成平均值。
- **Rationale**: `RUSAGE_CHILDREN` 的 `ru_maxrss` 是呼叫行程「所有已回收子行程」的歷史峰值
  （monotonic 高水位），並非逐次重置、也不是累加——同一個長期存活的協調者行程若連續呼叫
  `subprocess.run()` 10 次，只要某一次子行程的峰值低於先前任何一次，`getrusage()` 回報的
  仍會是先前較高的峰值，導致該次量測的記憶體數值失真。讓每次量測都在「全新且只會有一個
  子行程」的包裝行程中讀取 `RUSAGE_CHILDREN`，可保證讀到的峰值精確對應這一次、也只對應
  這一次執行。
- **Alternatives considered**: 由同一個長期存活的協調者行程直接呼叫 10 次
  `subprocess.run()` 並在每次呼叫前後比較 `getrusage()` 差值（已排除——使用者已指出此法
  在記憶體峰值遞減時會失真）；在 `bench_driver.py` 內部以 `RUSAGE_SELF` 自行量測
  （已排除——這會讓被量測對象「自己量測自己」，混入量測程式碼本身的額外負擔，且需要
  在負載行程內加入量測邏輯，偏離「驅動腳本只負責完成一局」的單一職責）。

### D7. 結果呈現：`benchmark_summary.md` + `##vso[task.uploadsummary]`

- **Decision**: `run_benchmarks.py` 將 10 次樣本與平均值寫成 Markdown 表格存至
  `benchmark_summary.md`（repo 根目錄），並於標準輸出印出
  `##vso[task.uploadsummary]<benchmark_summary.md 的絕對路徑>`，使其顯示於 Azure Pipelines
  執行結果的 Extensions／摘要分頁。
- **Rationale**: `task.uploadsummary` 是 Azure Pipelines 原生、用於將一段 Markdown 內容
  附加到執行摘要畫面的 logging command，直接對應使用者要求「顯示在 pipeline 的 Extensions
  分頁」；使用絕對路徑可避免工作目錄不一致造成找不到檔案。
- **Alternatives considered**: `PublishPipelineArtifact`（已排除——產生的是可下載的附件，
  不是摘要頁內顯示的內容，不符合需求）。

### D8. 效能步驟不得讓 pipeline 失敗：YAML 層 `continueOnError: true` + 腳本內部容錯

- **Decision**: 執行 `run_benchmarks.py` 的 pipeline 步驟加上 `continueOnError: true`；
  腳本內部對單次量測失敗（例如 `bench_driver.py` 非零結束）也會在摘要中註記錯誤樣本，
  但仍盡力完成其餘樣本並寫出摘要檔案，不主動以非零結束碼中止。
- **Rationale**: 直接落實 FR-010／FR-015——不論量測數值或量測步驟本身是否發生例外，
  都不得讓 pipeline 整體失敗；`continueOnError` 提供 YAML 層的保險，獨立於腳本內部的
  例外處理是否完備。
- **Alternatives considered**: 僅依賴腳本內部的 try/except 保證永遠回傳 0
  （已排除作為唯一機制——若直譯器層級發生非預期中止（例如被系統 OOM 砍掉），仍需要
  YAML 層的 `continueOnError` 作為最後一道防線）。

## Outstanding NEEDS CLARIFICATION

無。使用者於本次 `/speckit-plan` 輸入已涵蓋全部技術決策所需資訊，且 `/speckit-clarify`
階段已解決效能量測次數、回應時間定義與輸入決定性等規格層級的開放問題。
