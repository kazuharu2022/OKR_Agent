#!/usr/bin/env python3
"""Validate the deterministic gates of an OKR lifecycle document."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any


STATUSES = {
    "INCOMPLETE",
    "READY_FOR_REVIEW",
    "AWAITING_HUMAN_APPROVAL",
    "ACTIVE",
    "CLOSED",
}
CLASSIFICATIONS = {"committed", "aspirational", "learning"}
KR_KINDS = {"metric", "milestone"}
DIRECTIONS = {"increase", "decrease", "maintain", "binary"}
REVIEW_RESULTS = {"pass", "fail", "pending"}
REVIEW_CHECKS = {
    "outcome_not_activity",
    "necessary",
    "sufficient",
    "controllable",
    "measurable",
    "anti_gaming",
}
PLACEHOLDERS = {"", "UNVERIFIED", "UNASSIGNED", "TBD", "UNKNOWN"}
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,63}$")


@dataclass(frozen=True)
class Issue:
    level: str
    code: str
    path: str
    message: str


def _missing(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() in PLACEHOLDERS)


def _iso_date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _iso_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def validate_document(document: Any) -> list[Issue]:
    issues: list[Issue] = []

    def add(level: str, code: str, path: str, message: str) -> None:
        issues.append(Issue(level, code, path, message))

    def require_text(container: Any, key: str, path: str) -> str | None:
        if not isinstance(container, dict) or _missing(container.get(key)):
            add("error", "REQUIRED", f"{path}.{key}", "値が必要です")
            return None
        value = container[key]
        if not isinstance(value, str):
            add("error", "TYPE", f"{path}.{key}", "文字列である必要があります")
            return None
        return value.strip()

    def require_date(container: Any, key: str, path: str) -> date | None:
        raw = require_text(container, key, path)
        if raw is None:
            return None
        parsed = _iso_date(raw)
        if parsed is None:
            add("error", "DATE", f"{path}.{key}", "YYYY-MM-DD形式の日付が必要です")
        return parsed

    def require_datetime(container: Any, key: str, path: str) -> datetime | None:
        raw = require_text(container, key, path)
        if raw is None:
            return None
        parsed = _iso_datetime(raw)
        if parsed is None:
            add("error", "DATETIME", f"{path}.{key}", "タイムゾーン付きISO 8601日時が必要です")
        return parsed

    if not isinstance(document, dict):
        return [Issue("error", "ROOT_TYPE", "$", "ルートはJSONオブジェクトである必要があります")]

    if document.get("schema_version") != "1.0":
        add("error", "SCHEMA_VERSION", "$.schema_version", '対応する値は"1.0"です')

    status = document.get("status")
    if status not in STATUSES:
        add("error", "STATUS", "$.status", f"許可値: {', '.join(sorted(STATUSES))}")
        status = "INCOMPLETE"

    if status == "INCOMPLETE":
        if _missing(document.get("id")):
            add("warning", "DRAFT_ID", "$.id", "正式化前にIDを設定してください")
        if not document.get("objectives"):
            add("warning", "DRAFT_OBJECTIVE", "$.objectives", "Objectiveが未作成です")
        return issues

    okr_id = require_text(document, "id", "$")
    if okr_id and not ID_PATTERN.fullmatch(okr_id):
        add("error", "ID_FORMAT", "$.id", "3～64文字の英数字、点、下線、ハイフンを使用してください")

    period = document.get("period")
    if not isinstance(period, dict):
        add("error", "TYPE", "$.period", "オブジェクトである必要があります")
        period = {}
    require_text(period, "label", "$.period")
    period_start = require_date(period, "start", "$.period")
    period_end = require_date(period, "end", "$.period")
    if period_start and period_end and period_start > period_end:
        add("error", "PERIOD_ORDER", "$.period", "startはend以前である必要があります")

    context = document.get("context")
    if not isinstance(context, dict):
        add("error", "TYPE", "$.context", "オブジェクトである必要があります")
        context = {}
    for key in ("scope", "strategy", "owner", "decision_owner"):
        require_text(context, key, "$.context")
    if not isinstance(context.get("out_of_scope"), list):
        add("error", "TYPE", "$.context.out_of_scope", "配列である必要があります")

    objectives = document.get("objectives")
    if not isinstance(objectives, list):
        add("error", "TYPE", "$.objectives", "配列である必要があります")
        objectives = []
    if not 1 <= len(objectives) <= 3:
        add("error", "OBJECTIVE_COUNT", "$.objectives", "この実装では1期間・1スコープにつき1～3個にしてください")

    objective_ids: set[str] = set()
    all_krs: list[tuple[str, dict[str, Any], str]] = []
    for oi, objective in enumerate(objectives):
        opath = f"$.objectives[{oi}]"
        if not isinstance(objective, dict):
            add("error", "TYPE", opath, "オブジェクトである必要があります")
            continue
        objective_id = require_text(objective, "id", opath)
        if objective_id:
            if objective_id in objective_ids:
                add("error", "DUPLICATE_ID", f"{opath}.id", "Objective IDが重複しています")
            objective_ids.add(objective_id)
        require_text(objective, "statement", opath)
        require_text(objective, "why", opath)
        classification = require_text(objective, "classification", opath)
        if classification and classification not in CLASSIFICATIONS:
            add("error", "CLASSIFICATION", f"{opath}.classification", f"許可値: {', '.join(sorted(CLASSIFICATIONS))}")

        key_results = objective.get("key_results")
        if not isinstance(key_results, list):
            add("error", "TYPE", f"{opath}.key_results", "配列である必要があります")
            key_results = []
        if not 1 <= len(key_results) <= 5:
            add("error", "KR_COUNT", f"{opath}.key_results", "1～5個にしてください")
        elif len(key_results) not in {2, 3, 4}:
            add("warning", "KR_FOCUS", f"{opath}.key_results", "通常は2～4個を推奨します")

        kr_ids: set[str] = set()
        for ki, kr in enumerate(key_results):
            kpath = f"{opath}.key_results[{ki}]"
            if not isinstance(kr, dict):
                add("error", "TYPE", kpath, "オブジェクトである必要があります")
                continue
            kr_id = require_text(kr, "id", kpath)
            if kr_id:
                if kr_id in kr_ids:
                    add("error", "DUPLICATE_ID", f"{kpath}.id", "同じObjective内でKR IDが重複しています")
                kr_ids.add(kr_id)
            require_text(kr, "statement", kpath)
            kind = require_text(kr, "kind", kpath)
            if kind and kind not in KR_KINDS:
                add("error", "KR_KIND", f"{kpath}.kind", f"許可値: {', '.join(sorted(KR_KINDS))}")
            require_text(kr, "metric", kpath)
            direction = require_text(kr, "direction", kpath)
            if direction and direction not in DIRECTIONS:
                add("error", "DIRECTION", f"{kpath}.direction", f"許可値: {', '.join(sorted(DIRECTIONS))}")
            require_text(kr, "owner", kpath)
            require_text(kr, "data_source", kpath)
            require_text(kr, "update_cadence", kpath)
            if not isinstance(kr.get("guardrails"), list):
                add("error", "TYPE", f"{kpath}.guardrails", "配列である必要があります")

            baseline = kr.get("baseline")
            if not isinstance(baseline, dict):
                add("error", "TYPE", f"{kpath}.baseline", "オブジェクトである必要があります")
                baseline = {}
            verification = baseline.get("verification")
            if verification not in {"verified", "unverified", "not_applicable"}:
                add("error", "BASELINE_VERIFICATION", f"{kpath}.baseline.verification", "verified、unverified、not_applicableのいずれかが必要です")
            elif verification == "unverified":
                add("error", "BASELINE_UNVERIFIED", f"{kpath}.baseline", "レビュー以降の状態では未検証baselineを残せません")
            elif verification == "not_applicable":
                if classification != "learning":
                    add("error", "BASELINE_REQUIRED", f"{kpath}.baseline", "not_applicableはLearning Objectiveに限ります")
                require_text(baseline, "note", f"{kpath}.baseline")
            elif verification == "verified":
                if _missing(baseline.get("value")):
                    add("error", "REQUIRED", f"{kpath}.baseline.value", "検証済みの現状値が必要です")
                require_date(baseline, "observed_at", f"{kpath}.baseline")
                require_text(baseline, "source", f"{kpath}.baseline")

            target = kr.get("target")
            if not isinstance(target, dict):
                add("error", "TYPE", f"{kpath}.target", "オブジェクトである必要があります")
                target = {}
            if _missing(target.get("value")):
                add("error", "REQUIRED", f"{kpath}.target.value", "目標値または完了条件が必要です")
            require_text(target, "unit", f"{kpath}.target")
            deadline = require_date(target, "deadline", f"{kpath}.target")
            if deadline and period_start and deadline < period_start:
                add("error", "DEADLINE_RANGE", f"{kpath}.target.deadline", "対象期間より前です")
            if deadline and period_end and deadline > period_end:
                add("error", "DEADLINE_RANGE", f"{kpath}.target.deadline", "対象期間より後です")

            all_krs.append((classification or "", kr, kpath))

        for list_key in ("initiatives", "dependencies", "risks"):
            if not isinstance(objective.get(list_key), list):
                add("error", "TYPE", f"{opath}.{list_key}", "配列である必要があります")

    for list_key in ("evidence", "assumptions", "checkins", "history"):
        if not isinstance(document.get(list_key), list):
            add("error", "TYPE", f"$.{list_key}", "配列である必要があります")

    checkins = document.get("checkins", [])
    if isinstance(checkins, list):
        for ci, checkin in enumerate(checkins):
            cpath = f"$.checkins[{ci}]"
            if not isinstance(checkin, dict):
                add("error", "TYPE", cpath, "オブジェクトである必要があります")
                continue
            require_datetime(checkin, "at", cpath)
            require_text(checkin, "actor", cpath)
            require_text(checkin, "summary", cpath)
            confidence = require_text(checkin, "confidence", cpath)
            if confidence and confidence not in {"on_track", "at_risk", "off_track", "unverified"}:
                add("error", "CONFIDENCE", f"{cpath}.confidence", "on_track、at_risk、off_track、unverifiedのいずれかが必要です")
            for key in ("blockers", "decisions"):
                if not isinstance(checkin.get(key), list):
                    add("error", "TYPE", f"{cpath}.{key}", "配列である必要があります")

    history = document.get("history", [])
    if isinstance(history, list):
        for hi, event in enumerate(history):
            hpath = f"$.history[{hi}]"
            if not isinstance(event, dict):
                add("error", "TYPE", hpath, "オブジェクトである必要があります")
                continue
            require_datetime(event, "at", hpath)
            require_text(event, "actor", hpath)
            event_name = require_text(event, "event", hpath)
            require_text(event, "reason", hpath)
            if event_name == "STATE_TRANSITION":
                previous = require_text(event, "from", hpath)
                current = require_text(event, "to", hpath)
                if previous and previous not in STATUSES:
                    add("error", "HISTORY_STATE", f"{hpath}.from", "不明な状態です")
                if current and current not in STATUSES:
                    add("error", "HISTORY_STATE", f"{hpath}.to", "不明な状態です")

    quality_review = document.get("quality_review")
    if not isinstance(quality_review, dict):
        add("error", "TYPE", "$.quality_review", "オブジェクトである必要があります")
        quality_review = {}
    checks = quality_review.get("checks")
    if not isinstance(checks, dict):
        add("error", "TYPE", "$.quality_review.checks", "オブジェクトである必要があります")
        checks = {}
    for check_name in REVIEW_CHECKS:
        check = checks.get(check_name)
        cpath = f"$.quality_review.checks.{check_name}"
        if not isinstance(check, dict):
            add("error", "REVIEW_CHECK", cpath, "resultとnoteを持つオブジェクトが必要です")
            continue
        result = check.get("result")
        if result not in REVIEW_RESULTS:
            add("error", "REVIEW_RESULT", f"{cpath}.result", f"許可値: {', '.join(sorted(REVIEW_RESULTS))}")

    if status in {"AWAITING_HUMAN_APPROVAL", "ACTIVE", "CLOSED"}:
        require_text(quality_review, "reviewer", "$.quality_review")
        require_datetime(quality_review, "reviewed_at", "$.quality_review")
        for check_name in REVIEW_CHECKS:
            check = checks.get(check_name, {})
            if isinstance(check, dict) and check.get("result") != "pass":
                add("error", "REVIEW_NOT_PASSED", f"$.quality_review.checks.{check_name}.result", "承認待ち以降はpassが必要です")
            if isinstance(check, dict):
                require_text(check, "note", f"$.quality_review.checks.{check_name}")

    approval = document.get("approval")
    if not isinstance(approval, dict):
        add("error", "TYPE", "$.approval", "オブジェクトである必要があります")
        approval = {}
    approval_status = approval.get("status")
    if approval_status not in {"pending", "approved", "rejected"}:
        add("error", "APPROVAL_STATUS", "$.approval.status", "pending、approved、rejectedのいずれかが必要です")
    if status == "AWAITING_HUMAN_APPROVAL" and approval_status != "pending":
        add("error", "STATE_APPROVAL_MISMATCH", "$.approval.status", "承認待ち状態ではpendingである必要があります")
    if status in {"ACTIVE", "CLOSED"}:
        if approval_status != "approved":
            add("error", "APPROVAL_REQUIRED", "$.approval.status", "ACTIVE以降は人間のapprovedが必要です")
        require_text(approval, "approved_by", "$.approval")
        require_datetime(approval, "approved_at", "$.approval")
        active_transition = any(
            isinstance(event, dict)
            and event.get("event") == "STATE_TRANSITION"
            and event.get("from") == "AWAITING_HUMAN_APPROVAL"
            and event.get("to") == "ACTIVE"
            for event in history
        ) if isinstance(history, list) else False
        if not active_transition:
            add("error", "ACTIVE_TRANSITION_REQUIRED", "$.history", "承認待ちからACTIVEへの遷移記録が必要です")

    if status == "CLOSED":
        closure = document.get("closure")
        if not isinstance(closure, dict):
            add("error", "CLOSURE_REQUIRED", "$.closure", "Close情報が必要です")
            closure = {}
        require_datetime(closure, "closed_at", "$.closure")
        require_text(closure, "approved_by", "$.closure")
        require_text(closure, "summary", "$.closure")
        lessons = closure.get("lessons")
        if not isinstance(lessons, list) or not lessons:
            add("error", "LESSONS_REQUIRED", "$.closure.lessons", "1件以上の学びが必要です")

        close_transition = any(
            isinstance(event, dict)
            and event.get("event") == "STATE_TRANSITION"
            and event.get("from") == "ACTIVE"
            and event.get("to") == "CLOSED"
            for event in history
        ) if isinstance(history, list) else False
        if not close_transition:
            add("error", "CLOSE_TRANSITION_REQUIRED", "$.history", "ACTIVEからCLOSEDへの遷移記録が必要です")

        for classification, kr, kpath in all_krs:
            actual = kr.get("actual")
            if not isinstance(actual, dict):
                add("error", "ACTUAL_REQUIRED", f"{kpath}.actual", "Close時には最終実績が必要です")
                continue
            if _missing(actual.get("value")):
                add("error", "ACTUAL_REQUIRED", f"{kpath}.actual.value", "最終実績値が必要です")
            require_date(actual, "observed_at", f"{kpath}.actual")
            require_text(actual, "source", f"{kpath}.actual")
            score = actual.get("score")
            if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 1:
                add("error", "SCORE", f"{kpath}.actual.score", "0～1の数値が必要です")
            elif classification == "committed" and score not in {0, 1}:
                add("error", "COMMITTED_SCORE", f"{kpath}.actual.score", "committed KRは原則0または1で採点します")

    return issues


def _print_human(path: Path, issues: list[Issue]) -> None:
    errors = sum(issue.level == "error" for issue in issues)
    warnings = sum(issue.level == "warning" for issue in issues)
    for issue in issues:
        marker = "ERROR" if issue.level == "error" else "WARN"
        print(f"[{marker}] {issue.code} {issue.path}: {issue.message}")
    print(f"{path}: errors={errors}, warnings={warnings}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="OKR JSONの状態ゲートを検証します")
    parser.add_argument("path", type=Path, help="検証対象のJSONファイル")
    parser.add_argument("--json", action="store_true", dest="json_output", help="結果をJSONで出力")
    parser.add_argument("--strict", action="store_true", help="warningも終了コード1にする")
    args = parser.parse_args(argv)

    try:
        document = json.loads(args.path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"ファイルがありません: {args.path}", file=sys.stderr)
        return 2
    except (OSError, json.JSONDecodeError) as exc:
        print(f"JSONを読み込めません: {exc}", file=sys.stderr)
        return 2

    issues = validate_document(document)
    if args.json_output:
        print(json.dumps([asdict(issue) for issue in issues], ensure_ascii=False, indent=2))
    else:
        _print_human(args.path, issues)

    has_error = any(issue.level == "error" for issue in issues)
    has_warning = any(issue.level == "warning" for issue in issues)
    return 1 if has_error or (args.strict and has_warning) else 0


if __name__ == "__main__":
    raise SystemExit(main())
