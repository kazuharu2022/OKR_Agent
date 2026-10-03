# 月次マイルストーンの計画とレビュー

月次目標は独立したOKRではなく、四半期KRに対する期待軌道として扱う。週次チェックインを置き換えない。

## 月次計画

各KRに四半期内3か月分の `monthly_milestones` を設定する。

- `month`: `YYYY-MM`
- `target.value`: その月末の期待到達値または検証可能な完了条件
- `target.unit`: 四半期targetと同じ単位
- `focus_initiatives`: その月に重点化する施策。成果指標と混同しない

最終月のtargetは四半期targetと一致させる。途中月のtargetは機械的に均等配分せず、施策投入時期、季節性、計測遅延、依存関係を考慮する。

## 月次レビュー

対象月の終了後、各マイルストーンへ次を記録する。

1. `actual`: 実績値、観測日、測定元
2. `review.status`: `on_track`、`at_risk`、`off_track`、`unverified`
3. `review.summary`: 差分の理由、学び、翌月に必要な判断
4. `review.reviewed_by` とタイムゾーン付き `reviewed_at`

証拠がない場合は値を推測せず `unverified` とし、summaryに不足理由と取得予定を書く。この場合、`actual` はnullのままでよい。

月次レビューでは四半期ObjectiveやKRを採点・Closeしない。Initiativeは見直せるが、四半期targetまたは未到来月のtarget変更には変更前後と影響を示し、人間の承認を得て `history` に記録する。
