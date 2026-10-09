# Contract: `measure_once.py` → `run_benchmarks.py` IPC

`measure_once.py` 是一個獨立行程，被 `run_benchmarks.py` 以
`subprocess.run([sys.executable, "benchmarks/measure_once.py"], ...)` 呼叫；兩者之間透過
「一行 JSON 印在 stdout」作為唯一的資料契約。`run_benchmarks.py` 呼叫 10 次，每次都是全新的
`measure_once.py` 行程（理由見 `research.md` D6：避免 `RUSAGE_CHILDREN.ru_maxrss` 的
累積峰值污染單次量測結果）。

## 呼叫方式

```text
python benchmarks/measure_once.py
```

- 不需要命令列參數或 stdin 輸入。
- `measure_once.py` 內部以 `subprocess.run([sys.executable, "benchmarks/bench_driver.py"])`
  執行恰好一次 `bench_driver.py`，作為它自己唯一的子行程。

## 標準輸出契約（成功時，結束碼 0）

標準輸出 MUST 恰好一行合法 JSON（無額外的前後綴文字、無多行輸出）：

```json
{"response_time_s": 0.0123, "cpu_time_s": 0.0041, "max_rss_kb": 9024, "ok": true, "error": null}
```

| 欄位 | 型別 | 說明 |
|---|---|---|
| `response_time_s` | number | `bench_driver.py` 子行程的 wall-clock 執行時間（秒），由 `time.perf_counter()` 的前後差取得 |
| `cpu_time_s` | number | 子行程的 CPU 時間（秒），取 `resource.getrusage(resource.RUSAGE_CHILDREN)` 的 `ru_utime + ru_stime` |
| `max_rss_kb` | integer | 子行程的峰值記憶體（KB），取同一次 `getrusage(RUSAGE_CHILDREN)` 的 `ru_maxrss` |
| `ok` | boolean | 子行程結束碼是否為 0 |
| `error` | string \| null | `ok` 為 `false` 時的簡短錯誤描述；`ok` 為 `true` 時為 `null` |

## 標準輸出契約（子行程失敗時，`measure_once.py` 結束碼仍為 0）

即使 `bench_driver.py` 執行失敗（非零結束碼或逾時），`measure_once.py` MUST NOT 以非零結束碼
中止；而是印出 `ok: false` 與對應的 `error` 訊息，讓 `run_benchmarks.py` 可以把這一筆記錄為
失敗樣本並繼續處理其餘樣本：

```json
{"response_time_s": null, "cpu_time_s": null, "max_rss_kb": null, "ok": false, "error": "bench_driver exited with code 1"}
```

## `run_benchmarks.py` 的消費規則

- 對每一次呼叫，解析 stdout 的最後一行為 JSON；解析失敗（非合法 JSON，或行程本身的
  結束碼非 0）視同該筆樣本 `ok=false`，並記錄可辨識的錯誤訊息，不中止其餘 9 次量測。
- 平均值計算只採計 `ok == true` 的樣本（見 `data-model.md` 的驗證規則）。
