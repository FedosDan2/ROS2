#!/usr/bin/env python3
"""Проверить общий контракт evidence для ПР01–ПР14.

Команда дополняет, но не заменяет тесты в репозитории решения. Для работы
нужна только стандартная библиотека Python.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

PRACTICE_RE = re.compile(r"^PR(0[1-9]|1[0-4])$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def validate(practice_id: str, root: Path, manifest_dir: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = manifest_dir / f"{practice_id.lower()}.json"
    if not manifest_path.is_file():
        return [f"манифест не найден: {manifest_path}"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report_path = root / "evidence" / practice_id.lower() / "report.json"
    if not report_path.is_file():
        return [f"отсутствует {report_path}"]
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return [f"некорректный JSON в {report_path}: {error}"]

    if report.get("schema_version") != 1:
        errors.append("report.schema_version должен быть равен 1")
    if report.get("practice_id") != practice_id:
        errors.append(f"report.practice_id должен быть равен {practice_id}")
    report_commit = str(report.get("commit", ""))
    if not COMMIT_RE.fullmatch(report_commit):
        errors.append("report.commit должен содержать полный 40-символьный git SHA в нижнем регистре")
    else:
        inside_work_tree = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
            check=False,
            capture_output=True,
            text=True,
        )
        if inside_work_tree.returncode == 0 and inside_work_tree.stdout.strip() == "true":
            implementation = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "--verify", f"{report_commit}^{{commit}}"],
                check=False,
                capture_output=True,
                text=True,
            )
            if implementation.returncode != 0:
                errors.append("report.commit должен указывать commit, доступный в истории репозитория")
            else:
                implementation_sha = implementation.stdout.strip()
                ancestor = subprocess.run(
                    ["git", "-C", str(root), "merge-base", "--is-ancestor", implementation_sha, "HEAD"],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                if ancestor.returncode != 0:
                    errors.append("report.commit должен быть предком проверяемого HEAD")
                else:
                    changed = subprocess.run(
                        [
                            "git",
                            "-C",
                            str(root),
                            "diff",
                            "--name-only",
                            "--relative",
                            f"{implementation_sha}..HEAD",
                            "--",
                        ],
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    if changed.returncode != 0:
                        errors.append("не удалось сравнить report.commit с проверяемым HEAD")
                    else:
                        evidence_prefix = f"evidence/{practice_id.lower()}/"
                        disallowed = [
                            path
                            for path in changed.stdout.splitlines()
                            if path != "AI_USAGE.md" and not path.startswith(evidence_prefix)
                        ]
                        if disallowed:
                            preview = ", ".join(disallowed[:5])
                            errors.append(
                                "после report.commit могут меняться только evidence текущей ПР "
                                f"и AI_USAGE.md; неожиданные пути: {preview}"
                            )
                    worktree_paths: set[str] = set()
                    for command in (
                        ["git", "-C", str(root), "diff", "--name-only", "--relative"],
                        ["git", "-C", str(root), "diff", "--cached", "--name-only", "--relative"],
                        ["git", "-C", str(root), "ls-files", "--others", "--exclude-standard"],
                    ):
                        pending = subprocess.run(
                            command,
                            check=False,
                            capture_output=True,
                            text=True,
                        )
                        if pending.returncode != 0:
                            errors.append("не удалось проверить незакоммиченные изменения")
                            break
                        worktree_paths.update(pending.stdout.splitlines())
                    evidence_prefix = f"evidence/{practice_id.lower()}/"
                    unexpected_worktree = sorted(
                        path
                        for path in worktree_paths
                        if path != "AI_USAGE.md" and not path.startswith(evidence_prefix)
                    )
                    if unexpected_worktree:
                        preview = ", ".join(unexpected_worktree[:5])
                        errors.append(
                            "после report.commit незакоммиченными могут быть только evidence "
                            f"текущей ПР и AI_USAGE.md; неожиданные пути: {preview}"
                        )

    version_path = Path(__file__).resolve().parents[1] / "VERSION"
    if version_path.is_file():
        kit_root = version_path.parent
        file_manifest = kit_root / "MANIFEST.sha256"
        if not file_manifest.is_file():
            errors.append("в course kit отсутствует MANIFEST.sha256")
        else:
            for line in file_manifest.read_text(encoding="utf-8").splitlines():
                digest, separator, relative_path = line.partition("  ")
                candidate = (kit_root / relative_path).resolve()
                if not separator or not SHA256_RE.fullmatch(digest) or kit_root not in candidate.parents:
                    errors.append(f"некорректная запись манифеста course kit: {line}")
                    continue
                if not candidate.is_file():
                    errors.append(f"в course kit отсутствует файл: {relative_path}")
                    continue
                actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
                if actual != digest:
                    errors.append(f"не совпала контрольная сумма course kit: {relative_path}")
        course_kit = report.get("course_kit")
        expected_version = version_path.read_text(encoding="utf-8").strip()
        if not isinstance(course_kit, dict):
            errors.append("report.course_kit должен содержать version и archive_sha256")
        else:
            if course_kit.get("version") != expected_version:
                errors.append(f"report.course_kit.version должен быть равен {expected_version}")
            if not SHA256_RE.fullmatch(str(course_kit.get("archive_sha256", ""))):
                errors.append("report.course_kit.archive_sha256 должен содержать 64 hex-символа в нижнем регистре")
    commands = report.get("commands")
    if not isinstance(commands, list) or not commands or not all(isinstance(item, str) and item.strip() for item in commands):
        errors.append("report.commands должен быть непустым массивом строк")
    tests = report.get("tests")
    if not isinstance(tests, list) or not tests:
        errors.append("report.tests должен быть непустым массивом")
    else:
        statuses = {item.get("status") for item in tests if isinstance(item, dict)}
        if not statuses <= {"passed", "failed", "skipped"}:
            errors.append("status теста должен быть passed, failed или skipped")
        if "passed" not in statuses:
            errors.append("хотя бы один открытый тест должен иметь status=passed")
    defect = report.get("defect")
    if not isinstance(defect, dict) or not all(str(defect.get(key, "")).strip() for key in ("reproducer", "root_cause", "proof_after")):
        errors.append("report.defect должен описывать reproducer, root_cause и proof_after")
    time = report.get("time")
    if not isinstance(time, dict):
        errors.append("report.time должен содержать contact_academic_hours и self_study_hours")
    else:
        if not isinstance(time.get("contact_academic_hours"), (int, float)):
            errors.append("report.time.contact_academic_hours должен быть числом")
        if not isinstance(time.get("self_study_hours"), (int, float)):
            errors.append("report.time.self_study_hours должен быть числом")
    ai_used = report.get("ai_used")
    if not isinstance(ai_used, bool):
        errors.append("report.ai_used должен быть логическим значением")
    ai_usage = root / "AI_USAGE.md"
    if not ai_usage.is_file():
        errors.append("для каждой ПР требуется AI_USAGE.md в корне, в том числе при report.ai_used=false")
    elif not ai_usage.read_text(encoding="utf-8").strip():
        errors.append("AI_USAGE.md не должен быть пустым: опишите помощь или укажите, что ИИ не использовался")

    for pattern in manifest.get("required_paths", []):
        matches = list(root.glob(pattern))
        if not matches:
            errors.append(f"не найден обязательный путь: {pattern}")
        elif all(path.is_file() and path.stat().st_size == 0 for path in matches):
            errors.append(f"все найденные файлы пусты: {pattern}")

    for claim in manifest.get("required_claims", []):
        if report.get("claims", {}).get(claim) is not True:
            errors.append(f"report.claims.{claim} должен быть true")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("practice_id", type=str.upper)
    parser.add_argument("--submission", type=Path, default=Path.cwd())
    parser.add_argument(
        "--manifest-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "practices" / "manifests",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not PRACTICE_RE.fullmatch(args.practice_id):
        parser.error("practice_id должен находиться в диапазоне PR01…PR14")
    errors = validate(args.practice_id, args.submission.resolve(), args.manifest_dir.resolve())
    payload = {"practice_id": args.practice_id, "status": "passed" if not errors else "failed", "errors": errors}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
    elif errors:
        print(f"{args.practice_id}: на доработку", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
    else:
        print(f"{args.practice_id}: контракт evidence выполнен")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
