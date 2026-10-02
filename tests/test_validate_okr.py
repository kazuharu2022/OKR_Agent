from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / ".codex/skills/okr-cycle/scripts/validate_okr.py"
SPEC = importlib.util.spec_from_file_location("validate_okr", VALIDATOR_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VALIDATOR
SPEC.loader.exec_module(VALIDATOR)


def valid_ready_document() -> dict:
    return {
        "schema_version": "1.0",
        "id": "TEAM-2026-Q4",
        "period": {"label": "2026-Q4", "start": "2026-10-01", "end": "2026-12-31"},
        "status": "READY_FOR_REVIEW",
        "context": {
            "scope": "プロダクトチーム",
            "strategy": "新規利用者が価値を得るまでの時間を短縮する",
            "out_of_scope": ["料金改定"],
            "owner": "Product Lead",
            "decision_owner": "VP Product",
        },
        "objectives": [
            {
                "id": "O1",
                "statement": "新規利用者が初週で製品価値を実感できる状態にする",
                "why": "初月離脱を減らすため",
                "classification": "committed",
                "key_results": [
                    {
                        "id": "KR1",
                        "statement": "初期設定完了率を高める",
                        "kind": "metric",
                        "metric": "登録後7日以内の初期設定完了率",
                        "direction": "increase",
                        "baseline": {
                            "value": 52,
                            "observed_at": "2026-09-30",
                            "source": "analytics/onboarding",
                            "verification": "verified",
                            "note": "",
                        },
                        "target": {"value": 70, "unit": "%", "deadline": "2026-12-31"},
                        "owner": "Growth Lead",
                        "data_source": "analytics/onboarding",
                        "update_cadence": "weekly",
                        "guardrails": ["サポート問い合わせ率を10%以下に維持"],
                        "actual": None,
                    },
                    {
                        "id": "KR2",
                        "statement": "初回価値到達時間を短縮する",
                        "kind": "metric",
                        "metric": "登録から主要操作完了までの中央値",
                        "direction": "decrease",
                        "baseline": {
                            "value": 48,
                            "observed_at": "2026-09-30",
                            "source": "analytics/time-to-value",
                            "verification": "verified",
                            "note": "",
                        },
                        "target": {"value": 24, "unit": "hours", "deadline": "2026-12-31"},
                        "owner": "Product Lead",
                        "data_source": "analytics/time-to-value",
                        "update_cadence": "weekly",
                        "guardrails": ["主要操作のエラー率を2%以下に維持"],
                        "actual": None,
                    },
                ],
                "initiatives": ["オンボーディング導線の実験"],
                "dependencies": ["分析イベントの継続取得"],
                "risks": ["完了率だけを上げて理解度が下がる可能性"],
            }
        ],
        "evidence": [
            {"source": "analytics/onboarding", "observed_at": "2026-09-30", "note": "baseline export"}
        ],
        "assumptions": [],
        "quality_review": {
            "reviewer": "UNASSIGNED",
            "reviewed_at": None,
            "checks": {
                "outcome_not_activity": {"result": "pending", "note": ""},
                "necessary": {"result": "pending", "note": ""},
                "sufficient": {"result": "pending", "note": ""},
                "controllable": {"result": "pending", "note": ""},
                "measurable": {"result": "pending", "note": ""},
                "anti_gaming": {"result": "pending", "note": ""},
            },
        },
        "approval": {"status": "pending", "approved_by": None, "approved_at": None, "note": ""},
        "checkins": [],
        "closure": None,
        "history": [],
    }


class ValidateOkrTests(unittest.TestCase):
    def errors(self, document: dict) -> list:
        return [issue for issue in VALIDATOR.validate_document(document) if issue.level == "error"]

    def test_repository_template_is_valid_incomplete_document(self) -> None:
        template = json.loads(
            (ROOT / ".codex/skills/okr-cycle/assets/okr-template.json").read_text(encoding="utf-8")
        )
        self.assertEqual([], self.errors(template))

    def test_ready_document_passes_deterministic_gate(self) -> None:
        self.assertEqual([], self.errors(valid_ready_document()))

    def test_ready_document_rejects_unverified_baseline(self) -> None:
        document = valid_ready_document()
        document["objectives"][0]["key_results"][0]["baseline"]["verification"] = "unverified"
        codes = {issue.code for issue in self.errors(document)}
        self.assertIn("BASELINE_UNVERIFIED", codes)

    def test_awaiting_approval_requires_all_review_checks_to_pass(self) -> None:
        document = valid_ready_document()
        document["status"] = "AWAITING_HUMAN_APPROVAL"
        codes = {issue.code for issue in self.errors(document)}
        self.assertIn("REVIEW_NOT_PASSED", codes)

    def test_active_requires_explicit_human_approval(self) -> None:
        document = self.valid_active_document()
        document["approval"] = {"status": "pending", "approved_by": None, "approved_at": None, "note": ""}
        codes = {issue.code for issue in self.errors(document)}
        self.assertIn("APPROVAL_REQUIRED", codes)

    def test_valid_active_document_passes(self) -> None:
        self.assertEqual([], self.errors(self.valid_active_document()))

    def test_valid_closed_document_passes(self) -> None:
        self.assertEqual([], self.errors(self.valid_closed_document()))

    def test_closed_requires_actuals_and_reflection(self) -> None:
        document = self.valid_active_document()
        document["status"] = "CLOSED"
        codes = {issue.code for issue in self.errors(document)}
        self.assertIn("CLOSURE_REQUIRED", codes)
        self.assertIn("ACTUAL_REQUIRED", codes)

    @staticmethod
    def valid_active_document() -> dict:
        document = deepcopy(valid_ready_document())
        document["status"] = "ACTIVE"
        document["quality_review"]["reviewer"] = "OKR facilitator"
        document["quality_review"]["reviewed_at"] = "2026-10-01T09:00:00+09:00"
        for check in document["quality_review"]["checks"].values():
            check["result"] = "pass"
            check["note"] = "確認済み"
        document["approval"] = {
            "status": "approved",
            "approved_by": "VP Product",
            "approved_at": "2026-10-01T10:00:00+09:00",
            "note": "会議で承認",
        }
        document["history"] = [
            {
                "at": "2026-10-01T10:00:00+09:00",
                "actor": "VP Product",
                "event": "STATE_TRANSITION",
                "from": "AWAITING_HUMAN_APPROVAL",
                "to": "ACTIVE",
                "reason": "ObjectiveとKRを承認",
            }
        ]
        return document

    @classmethod
    def valid_closed_document(cls) -> dict:
        document = cls.valid_active_document()
        document["status"] = "CLOSED"
        for kr in document["objectives"][0]["key_results"]:
            kr["actual"] = {
                "value": kr["target"]["value"],
                "observed_at": "2026-12-31",
                "source": kr["data_source"],
                "score": 1,
            }
        document["closure"] = {
            "closed_at": "2027-01-05T10:00:00+09:00",
            "approved_by": "VP Product",
            "summary": "両KRを達成",
            "lessons": ["週次レビューが阻害要因の早期発見に有効だった"],
        }
        document["history"].append(
            {
                "at": "2027-01-05T10:00:00+09:00",
                "actor": "VP Product",
                "event": "STATE_TRANSITION",
                "from": "ACTIVE",
                "to": "CLOSED",
                "reason": "最終実績と振り返りを承認",
            }
        )
        return document


if __name__ == "__main__":
    unittest.main()
