# OKRの設定・レビュー

新規作成、未完成ドラフトの再開、承認前の修正に使う。

## 1. Intake

既に回答済みの内容は再質問しない。次の必須情報を、判断への影響が大きい順に確認する。

1. OKRを設定する理由と、期間終了時に変わっていてほしい状態
2. 対象四半期（例: `2026-Q4`、会計年度表記なら `FY2026-Q1`）
3. 対象範囲（個人、チーム、部署、組織など）
4. 戦略上の優先事項と、今回は扱わない事項
5. Ownerと最終承認者
6. 利用可能な実績値、測定元、測定頻度
7. 制約、依存関係、重大な副作用

回答が得られない項目を推測しない。ドラフトには `UNVERIFIED` または `UNASSIGNED` を残し、状態を `INCOMPLETE` に保つ。

## 2. Evidence gate

数値目標を作る前に、指標定義、現状値、観測日、測定元を確認する。

- 現状値が存在する場合は出典と観測日を記録する。
- 現状値が取得可能だが未取得の場合は、取得を次の確認事項にする。
- 現状値を定義できない場合は、測定方法の確立またはLearning OKRを提案する。
- ユーザーが仮の目標値を求めた場合は候補として提示できるが、根拠のない値を正式値にしない。

外部資料を参照した場合は、URL、文書名、版または取得日を `evidence` に残す。

## 3. Draft

原則として1四半期・1スコープあたりObjectiveは1～3個、各ObjectiveのKRは2～4個に絞る。OKR期間は組織の会計年度に合わせた連続3か月の完全な月とし、月単位のObjectiveへ分割しない。

Objectiveは、重要な変化、対象、意味が伝わる短い文にする。KRは次を含める。

- 結果を表す文
- 指標名または検証可能な完了条件
- baseline、target、unit、deadline
- 四半期内3か月分のmonthly milestones
- owner、data source、update cadence
- 必要なguardrail

各KRの `monthly_milestones` には、四半期を構成する3か月を順番に登録する。月次targetは四半期targetへ至る期待軌道であり、最終月のtargetは四半期targetと一致させる。機械的な三等分はせず、施策投入時期、季節性、計測遅延を反映する。

月次の重点作業は `focus_initiatives` に置く。月次マイルストーン自体も作業量ではなく、KRに対応する成果または検証可能な到達点にする。

活動語だけで終わる項目はInitiativeへ移す。例として「調査する」「会議を開催する」「機能を作る」だけではKRにしない。その活動によって何がどう変われば成功かを確認する。

Objectiveごとに `committed`、`aspirational`、`learning` のいずれかを明示する。種類を混同した採点をしない。

## 4. Quality review

次の観点を個別に `pass`、`fail`、`pending` で記録し、理由を書く。

- `outcome_not_activity`: KRが活動ではなく成果を測っているか
- `necessary`: 各KRがObjective達成に必要か
- `sufficient`: KR全体でObjective達成を十分に説明できるか
- `controllable`: Ownerが合理的に影響できるか
- `measurable`: 定義、現状値、四半期・月次目標、期限、測定元が明確か
- `anti_gaming`: 指標のゲーム化や重大な副作用への防止策があるか

1つでも `fail` または `pending` があれば `AWAITING_HUMAN_APPROVAL` に進めない。LLMによるレビュー結果は補助情報であり、人間承認の代替ではない。

## 5. Transitions

### `INCOMPLETE` -> `READY_FOR_REVIEW`

必須情報と測定根拠を入力し、検証スクリプトがエラーなしで終了した場合のみ進める。

### `READY_FOR_REVIEW` -> `AWAITING_HUMAN_APPROVAL`

Quality reviewがすべて `pass` となり、未解決の仮定とリスクをユーザーへ提示した場合のみ進める。

### `AWAITING_HUMAN_APPROVAL` -> `ACTIVE`

現在のObjective、KR、目標値、期間を示したうえで、人間から明確な承認を得る。`approval` に承認者、日時、注記を記録し、状態遷移を `history` に追記してから再検証する。

承認されなかった場合は理由を記録し、`INCOMPLETE` または `READY_FOR_REVIEW` に戻す。
