# OKR Cycle Agent

対話による情報収集、根拠確認、品質レビュー、人間承認、週次チェックイン、期末振り返りを一貫して扱うCodex向けOKRワークフローです。

LLMが組織の戦略や目標を自動決定する仕組みではありません。LLMは質問、構造化、反証、記録を支援し、Objective、目標値、責任者、承認は人間が決定します。

## 特徴

- 必須情報が揃うまで次の正式状態へ進まない状態ゲート
- 不明情報を `UNVERIFIED` / `UNASSIGNED` として明示
- Objective、Key Result、Initiativeの分離
- committed、aspirational、learningの区別
- 根拠、測定元、承認、変更履歴の保存
- Python標準ライブラリだけで動く決定論的validator
- Skillの誤起動と回帰を確認するEvalプロンプト

## ディレクトリ構成

```text
.
├── AGENTS.md
├── README.md
├── .codex/skills/okr-cycle/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   ├── assets/okr-template.json
│   ├── references/
│   │   ├── setting.md
│   │   ├── checkin.md
│   │   └── closing.md
│   └── scripts/validate_okr.py
├── evals/okr-cycle.prompts.csv
├── tests/test_validate_okr.py
└── okrs/                       # 実際の利用時に作成
```

## 必要環境

- Codex
- Python 3.9以降

Agentとvalidatorの実行に追加パッケージはありません。Skill構造検証ツールが必要とするPyYAMLだけは、後述のとおりuvの一時環境で実行します。将来Pythonパッケージを追加する場合もuv環境を使用し、複数のライブラリやサービスを導入する場合はDocker Composeで管理します。

## 使い方

### 1. 新しいOKRを設定する

Codexでこのリポジトリを開き、次のように依頼します。

```text
$okr-cycle を使って、2026年Q4のチームOKRを設定したい。
```

Agentは、既に回答された内容を再質問せず、次に必要な情報を原則1つずつ確認します。主な確認内容は次のとおりです。

1. OKRを設定する理由と、期間終了時の望ましい状態
2. 対象期間と対象範囲
3. 戦略上の優先事項と対象外
4. Ownerと最終承認者
5. 現状値、測定元、更新頻度
6. 制約、依存関係、副作用

作成中のファイルは `okrs/<period>/<id>.json` に保存されます。情報不足の間は `INCOMPLETE` のままです。

### 2. ドラフトを再開する

```text
$okr-cycle で okrs/2026-Q4/TEAM-2026-Q4.json の続きを進めて。
```

Agentはファイルを読み、確認済み事項と不足事項を分け、次に必要な質問をします。

### 3. レビューする

```text
$okr-cycle でこのOKRを反証レビューして。まだ承認・有効化はしないで。
```

レビューでは、成果指標か、必要十分か、Ownerが影響可能か、測定可能か、指標をゲーム化できないかを確認します。全項目が `pass` にならない限り承認待ちへ進みません。

### 4. 承認して有効化する

AgentがObjective、KR、未解決の仮定、リスクを提示した後、内容を確認して明確に承認します。

```text
提示された2026年Q4版のObjectiveとKRを承認し、ACTIVEにしてください。
```

「よさそう」「検討します」などは承認として扱いません。承認者と日付がJSONに記録され、validatorを通過して初めて `ACTIVE` になります。

### 5. チェックインする

```text
$okr-cycle で今週のチェックインを行いたい。
KR1の現在値は42%、測定日は2026-10-16、参照元は社内ダッシュボードです。
```

Agentは実績、見通し、阻害要因、判断事項を追記します。Objectiveや目標値は自動変更しません。

目標値を変更する場合は、変更前後、理由、難易度と比較可能性への影響を確認し、別途承認します。

### 6. Closeする

```text
$okr-cycle で2026年Q4のOKRをCloseしたい。
```

各KRの最終値と根拠を確認し、達成状況、成功した施策、誤っていた仮説、副作用、次期への学びを整理します。人間のClose承認とvalidator通過後に `CLOSED` になります。

## 状態遷移

```text
INCOMPLETE
  └─ 必須情報と測定根拠が揃う
      READY_FOR_REVIEW
        └─ Quality reviewが全項目pass
            AWAITING_HUMAN_APPROVAL
              └─ 人間が現在の内容を明確に承認
                  ACTIVE
                    └─ 最終実績、振り返り、Close承認
                        CLOSED
```

レビューで不足が見つかった場合は前の状態へ戻します。状態変更は `history` に追記し、過去の目標値や失敗を遡及的に消しません。

## 手動検証

OKR JSONを検証します。

```bash
python3 .codex/skills/okr-cycle/scripts/validate_okr.py okrs/2026-Q4/TEAM-2026-Q4.json
```

機械処理用JSON出力:

```bash
python3 .codex/skills/okr-cycle/scripts/validate_okr.py --json okrs/2026-Q4/TEAM-2026-Q4.json
```

warningも失敗扱いにする場合:

```bash
python3 .codex/skills/okr-cycle/scripts/validate_okr.py --strict okrs/2026-Q4/TEAM-2026-Q4.json
```

実装のテスト:

```bash
python3 -m unittest discover -s tests -v
UV_CACHE_DIR=/tmp/okr-uv-cache uv run --with pyyaml python /Users/tera/.codex/skills/.system/skill-creator/scripts/quick_validate.py .codex/skills/okr-cycle
```

validatorは形式、必須フィールド、状態と承認の整合性を検査します。戦略の妥当性や指標の意味を証明するものではないため、Quality reviewと人間承認は省略できません。

## Eval

`evals/okr-cycle.prompts.csv` には、明示呼び出し、暗黙呼び出し、再開、チェックイン、Close、およびSkillを起動すべきでない負例を収録しています。

Skill変更時は、少なくとも次を確認します。

- 必要な依頼でSkillが選択される。
- 一般的な目標理論の説明や単なるToDo整理では誤起動しない。
- 情報不足時に値を捏造しない。
- 承認なしに `ACTIVE` にしない。
- ACTIVE後の目標変更をチェックインとして処理しない。

## 設計上の境界

- OKRは人事評価や報酬の唯一の根拠にはしません。
- LLMのレビュー結果は、人間による戦略判断や承認の代替ではありません。
- 指標が未整備なら、根拠のない数値目標ではなく測定確立またはLearning OKRを検討します。
- validatorのPASSは形式上のゲート通過であり、成果達成や戦略品質の証明ではありません。

## 参考資料

- [Google re:Work: Set goals with OKRs](https://rework.withgoogle.com/intl/en/guides/set-goals-with-okrs)
- [Microsoft Learn: Write effective OKRs](https://learn.microsoft.com/en-us/viva/goals/viva-goals-healthy-okr-program/write-okrs-overview)
- [OpenAI: Rethinking skills and prompts](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)
- [OpenAI: Testing Agent Skills Systematically](https://developers.openai.com/blog/eval-skills)
- [NIST AI RMF: Human-AI Interaction](https://airc.nist.gov/airmf-resources/airmf/appendices/app-c-ai-risk-management-and-human-ai-interaction/)
