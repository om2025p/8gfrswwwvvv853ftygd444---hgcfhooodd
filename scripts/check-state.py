#!/usr/bin/env python3
"""بازرس وضعیت مخزن — پیش از هر کامیت اجرا شود.

سه چیز را می‌سنجد:
  ۱. هیچ توکن/رمز لو رفته‌ای در فایل‌های ردیابی‌شده نباشد
  ۲. فایل‌های حیاتی وضعیت (PROJECT-STATE.md و AGENTS.md) موجود و غیرخالی باشند
  ۳. شاخه‌ها با ریموت همسطح باشند (کاری گم نشده باشد)

کد خروجی ۱ = شکست.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SECRET_PATTERNS = [
    (r"ghp_[A-Za-z0-9]{20,}", "GitHub personal access token"),
    (r"github_pat_[A-Za-z0-9_]{20,}", "GitHub fine-grained token"),
    (r"\b[0-9]{9,10}:AA[A-Za-z0-9_-]{30,}", "Telegram bot token"),
    (r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----", "private key"),
]

TEXT_SUFFIXES = {".py", ".js", ".md", ".json", ".html", ".css", ".yml", ".yaml", ".sh", ".txt"}
SKIP_DIRS = {".git", "node_modules", "vendor", "restricted", "fund-automation-android"}

REQUIRED = {
    "PROJECT-STATE.md": 2000,   # حداقل بایت
    "AGENTS.md": 5000,
}


def tracked_files():
    out = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    return [ROOT / f for f in out if (ROOT / f).is_file()]


def scan_secrets(files):
    hits = []
    for f in files:
        if f.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in f.parts):
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern, label in SECRET_PATTERNS:
            for m in re.finditer(pattern, text):
                line = text[: m.start()].count("\n") + 1
                hits.append(f"{f.relative_to(ROOT)}:{line} — {label}")
    return hits


def check_state_files():
    problems = []
    for name, min_bytes in REQUIRED.items():
        p = ROOT / name
        if not p.exists():
            problems.append(f"{name} موجود نیست")
        elif p.stat().st_size < min_bytes:
            problems.append(f"{name} خیلی کوچک است ({p.stat().st_size} < {min_bytes} بایت)")
    return problems


def check_branch_sync():
    try:
        local = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
        remote = subprocess.run(
            ["git", "rev-parse", "origin/main"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        return ["origin/main در دسترس نیست (شاید fetch لازم است)"]
    if local != remote:
        return [f"HEAD ({local[:7]}) با origin/main ({remote[:7]}) یکی نیست — پوش کن"]
    return []


def main():
    files = tracked_files()
    failures = 0

    hits = scan_secrets(files)
    if hits:
        print("❌ توکن/رمز لو رفته پیدا شد:")
        for h in hits:
            print("   " + h)
        failures += 1
    else:
        print(f"✅ هیچ رمزی در {len(files)} فایل ردیابی‌شده نیست")

    problems = check_state_files()
    if problems:
        print("❌ مشکل در فایل‌های وضعیت:")
        for p in problems:
            print("   " + p)
        failures += 1
    else:
        print("✅ فایل‌های وضعیت موجود و کامل‌اند")

    unsynced = check_branch_sync()
    if unsynced:
        print("⚠️  شاخه همسطح نیست:")
        for u in unsynced:
            print("   " + u)
    else:
        print("✅ شاخه با origin/main همسطح است")

    if failures:
        print(f"\n{failures} بررسی شکست خورد.")
        return 1
    print("\n✅ همه‌چیز سالم است.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
