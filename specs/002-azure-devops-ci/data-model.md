# Data Model: Azure DevOps CI 品質檢查流程

本功能不涉及應用程式資料或持久化儲存；以下為 CI 設定本身的「結構」與各步驟之間的狀態轉換，
供實作 `azure-pipelines.yml`／`sonar-project.properties` 與審查對照。

**版本說明**：已依 2026-10-02 的技術決策更新（新增 checkout 步驟、vmImage 與 Python 版本變更、
SonarQube Cloud 任務升級為 v4 並補上具體連線資訊、新增掃描排除規則）。

## 設定實體：Pipeline Trigger（對應 FR-001、FR-002、FR-011）

位置：`azure-pipelines.yml` 的 `trigger`／`pr` 區塊

| 欄位 | 值 | 說明 |
|------|----|------|
| `trigger.branches.include` | `[main]` | 僅 main 分支的 push 觸發（FR-001、FR-002） |
| `pr` | `none` | 關閉 Pull Request 觸發（FR-011） |

## 設定實體：Pipeline Stage（四個循序步驟，對應 US1～US3）

位置：`azure-pipelines.yml` 的 `jobs`／`steps`

| # | 步驟 | 任務／設定 | 失敗時行為 | 對應需求 |
|---|------|------------|------------|----------|
| 0 | 原始碼取得 | `checkout: self`，`fetchDepth: 0` | 失敗則 pipeline 失敗，後續步驟不執行 | D2（research.md）、SonarQube Cloud 分析完整性 |
| 1 | 環境建置 | `UsePythonVersion@0`（`versionSpec: '3.12'`）、`pip install pytest` | 失敗則 pipeline 失敗，後續步驟不執行 | Technical Context、FR-010 |
| 2 | 單元測試 | `python -m pytest` | 任一測試失敗 → 非零結束碼 → pipeline 失敗，不執行步驟 3 | FR-003、FR-004、FR-005 |
| 3 | 品質掃描 | `SonarCloudPrepare@4` → `SonarCloudAnalyze@4` → `SonarCloudPublish@4` | 掃描本身失敗（例如連線失敗）才會讓 pipeline 失敗；Quality Gate 結果本身不影響 pipeline 成敗（FR-007a） | FR-006、FR-007、FR-007a |

步驟 3 僅在步驟 2 成功後執行（YAML 預設 `dependsOn`／循序 `steps` 行為即可達成，不需額外條件判斷）。
執行環境：`pool.vmImage = 'ubuntu-24.04'`（固定版本，不用 `ubuntu-latest`，見 research.md D2）。

## 設定實體：SonarQube Cloud Prepare 任務輸入（對應 FR-006、FR-008）

位置：`azure-pipelines.yml` 的 `SonarCloudPrepare@4` 任務

| 欄位 | 值 | 說明 |
|------|----|------|
| `SonarCloud` | `sonarcloud-113403522` | Service Connection 名稱（機密由此提供，不出現在 YAML 中，FR-008） |
| `organization` | `john19960810` | SonarQube Cloud 組織識別碼 |
| `scannerMode` | `cli` | 獨立 scanner 模式（純 Python 專案，非 MSBuild／Maven／Gradle） |
| `configMode` | `file` | 掃描參數改由 `sonar-project.properties` 提供 |
| `configFile` | `sonar-project.properties` | 設定檔路徑（即預設值，顯式寫出以利閱讀） |

不設定 `cliProjectKey`（`configMode: file` 時由設定檔的 `sonar.projectKey` 提供，見下表，
避免雙處維護同一份資訊）。

## 設定實體：SonarQube Cloud 掃描設定（對應 FR-006、FR-009、使用者排除規則）

位置：`sonar-project.properties`

| 欄位 | 值 | 說明 |
|------|----|------|
| `sonar.projectKey` | `john19960810_guess_number_game_113403522` | SonarQube Cloud 專案識別碼（專案已事先建立，見 spec.md Assumptions） |
| `sonar.organization` | `john19960810` | SonarQube Cloud 組織識別碼 |
| `sonar.sources` | `src` | 掃描猜數字遊戲的原始碼（唯讀，不因本功能而修改） |
| `sonar.tests` | `tests` | 掃描既有測試目錄 |
| `sonar.python.version` | `3.12` | 對應 Technical Context 的 Python 版本（與本機 `.venv` 一致） |
| `sonar.exclusions` | `.specify/**,specs/**` | 防禦性排除 spec-kit 文件目錄；`sonar.sources`／`sonar.tests` 已隱含排除，此為雙重保障（research.md D7） |

本功能不設定任何 `sonar.*coverage*` 相關欄位（對應 FR-009：不產生測試覆蓋率報告）。

## 概念值：Quality Gate Result（非持久化，僅存在於單次 pipeline 執行的摘要畫面）

| 狀態 | 來源 | 是否影響 pipeline 成敗 |
|------|------|------------------------|
| `PASSED` | SonarQube Cloud 分析結果 | 否（僅顯示） |
| `FAILED` | SonarQube Cloud 分析結果 | 否（僅顯示，FR-007a；`SonarCloudPublish@4` 本無提供「依 Quality Gate 結果讓任務失敗」的輸入選項，見 research.md D4/D5） |

此值由 `SonarCloudPublish@4` 任務寫入 pipeline 執行摘要的專屬分頁／區塊，不由本功能自行儲存或轉送。

## 狀態轉換（單次 pipeline 執行）

```text
push to main
      │
      ▼
┌───────────────┐
│ checkout       │──失敗──► pipeline FAILED（後續步驟不執行）
│ (fetchDepth=0) │
└──────┬────────┘
       │成功
       ▼
┌───────────────┐
│ 環境建置        │──失敗──► pipeline FAILED（步驟 2、3 不執行）
│ (Python 3.12)  │
└──────┬────────┘
       │成功
       ▼
┌───────────────┐
│ pytest 測試     │──任一測試失敗──► pipeline FAILED（步驟 3 不執行，FR-004/FR-005）
└──────┬────────┘
       │全數通過
       ▼
┌───────────────┐
│ SonarQube Cloud │──掃描本身失敗（連線／逾時等）──► pipeline FAILED
│ 掃描與發布 (v4)  │
└──────┬────────┘
       │掃描成功完成（不論 Quality Gate 結果為何）
       ▼
pipeline SUCCEEDED，摘要顯示 Quality Gate 結果（PASSED 或 FAILED，FR-007a）
```

推送至非 main 分支的 commit：不進入上述流程（pipeline 不觸發，FR-002）。

## 實體與需求對照

| 實體／規則 | 需求 |
|-----------|------|
| Pipeline Trigger | FR-001、FR-002、FR-011、SC-001 |
| Checkout（fetchDepth: 0） | SonarQube Cloud 分析完整性（research.md D2） |
| 單元測試步驟 | FR-003、FR-004、FR-005、SC-002 |
| 品質掃描步驟（v4 任務） | FR-006、FR-007、SC-003 |
| Quality Gate Result（資訊呈現） | FR-007a |
| SonarQube Cloud 掃描設定（含排除規則） | FR-006、FR-009 |
| Service Connection（機密管理，見 research.md D6） | FR-008 |
