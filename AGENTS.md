# OKR repository instructions

## Communication and environment

- 解答、確認質問、生成する運用文書は日本語にする。
- ツールやPythonパッケージを追加する場合はuv環境を使用する。
- 複数のライブラリやサービスを導入する場合はDocker Composeを使用する。

## Project workflow

- OKRの新規設定、レビュー、チェックイン、Closeには `.codex/skills/okr-cycle/SKILL.md` を使用する。
- 正式な状態は `okrs/<period>/<id>.json` を正本とする。
- OKR本体は組織の会計年度に合わせた連続3か月の四半期単位とし、各KRに四半期内3か月分の月次マイルストーンを設定する。
- 月次目標は独立ObjectiveではなくKRの到達軌道として扱い、週次チェックインを継続する。
- baseline、target、owner、実績、根拠、承認を推測しない。不明な値は `UNVERIFIED` または `UNASSIGNED` とする。
- Objective、Key Result、Initiativeを混同しない。
- 人間の明確な承認なしにOKRを `ACTIVE` にしない。ACTIVE後の目標値変更と期末Closeも承認対象とする。
- OKRを報酬、人事評価、懲戒の唯一の根拠として扱わない。

## Validation

変更したOKRは次で検証する。

```bash
python3 .codex/skills/okr-cycle/scripts/validate_okr.py <okr-json>
```

Skillやvalidatorを変更した場合は次も実行する。

```bash
UV_CACHE_DIR=/tmp/okr-uv-cache uv run --with pyyaml python /Users/tera/.codex/skills/.system/skill-creator/scripts/quick_validate.py .codex/skills/okr-cycle
python3 -m unittest discover -s tests -v
```
