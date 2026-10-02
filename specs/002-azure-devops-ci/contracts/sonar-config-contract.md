# Contract: sonar-project.properties

此文件定義 `sonar-project.properties`（儲存庫根目錄）必須提供的欄位，供
`SonarCloudPrepare@4`（`configMode: 'file'`，見 [azure-pipeline-contract.md](./azure-pipeline-contract.md)）
讀取，也可供開發者在本機以 `sonar-scanner` 直接驗證設定是否正確。

**版本說明**：已依 2026-10-02 的技術決策更新（具體 projectKey／organization、Python 3.12、
新增 `sonar.exclusions`）。

## 必要欄位

| 欄位 | 值 | 說明 | 對應需求 |
|------|----|------|----------|
| `sonar.projectKey` | `john19960810_guess_number_game_113403522` | SonarQube Cloud 專案識別碼（專案已事先建立，見 spec.md Assumptions） | FR-006 |
| `sonar.organization` | `john19960810` | SonarQube Cloud 組織識別碼 | FR-006 |
| `sonar.sources` | `src` | 掃描猜數字遊戲既有原始碼；本功能不修改其內容 | FR-006、FR-010 |
| `sonar.tests` | `tests` | 掃描既有測試目錄 | FR-006、FR-010 |
| `sonar.python.version` | `3.12` | 對應 Technical Context 的 Python 版本（與本機 `.venv` 一致） | FR-006 |
| `sonar.exclusions` | `.specify/**,specs/**` | 防禦性排除 spec-kit 文件目錄；即使 `sonar.sources` 已隱含排除，仍顯式宣告以降低設定漂移風險（research.md D7） | 使用者明確要求第 6 點 |

## 明確排除的欄位

- MUST NOT 設定任何 `sonar.python.coverage.reportPaths` 或其他 coverage 相關欄位
  （對應 FR-009：本次不產生測試覆蓋率報告）。
- MUST NOT 包含任何權杖（token）、密碼或其他機密值；驗證資訊一律由名為
  `sonarcloud-113403522` 的 Service Connection 提供
  （對應 FR-008，見 [azure-pipeline-contract.md](./azure-pipeline-contract.md) 的機密契約）。

## 驗證方式

此設定檔本身無法在本機「執行」出與 Azure DevOps 相同的結果（需要實際的 pipeline 環境與
Service Connection，見使用者第 8 點）。開發者若想在本機預檢設定檔格式與掃描範圍是否符合預期，
可自備一組有效的 SonarQube Cloud token 作為環境變數（**不得** 寫入此檔案或 repo 任何位置）執行：

```bash
sonar-scanner -Dsonar.token="$SONAR_TOKEN"
```

預期：掃描成功完成並於 SonarQube Cloud 專案 `john19960810_guess_number_game_113403522`
頁面看到本次分析紀錄，且分析範圍不包含 `.specify/`、`specs/` 底下的檔案。
此為選用的本機預檢步驟，並非本功能的正式驗收方式（正式驗收見
[azure-pipeline-contract.md](./azure-pipeline-contract.md) 的「驗收方式契約」）。
