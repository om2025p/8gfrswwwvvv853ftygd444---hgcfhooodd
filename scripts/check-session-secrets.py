#!/usr/bin/env python3
"""بازرس نشست/کوکی — هر فایل نشستی که در گیت ردیابی شود، شکست می‌خورد.

درس گران‌بها: `gold5/easytrader_session.json` شامل کوکی زندهٔ
`.AspNetCore.Identity.Application` بود، در گیت ردیابی شده بود و روی سایت
عمومی با HTTP 200 سرو می‌شد. هر کسی می‌توانست نشست کارگزاری را بدزدد.

این بازرس سه چیز را می‌سنجد:
  ۱. هیچ فایل نشست/کوکی در گیت ردیابی نشده باشد.
  ۲. هیچ ورک‌فلویی فایل نشست را `git add` نکند.
  ۳. الگوهای محرمانه در `.gitignore` حاضر باشند.

خروجی: کد ۱ در صورت نقض.
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SECRET_PATTERNS = [
    re.compile(r"session\.json$", re.I),
    re.compile(r"storage_state.*\.json$", re.I),
    re.compile(r"cookies?.*\.json$", re.I),
]

REQUIRED_IGNORES = [
    "easytrader_session.json",
    "*_session.json",
    "*storage_state*.json",
    "*cookies*.json",
]


def tracked_files():
    out = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    return [f for f in out.splitlines() if f.strip()]


def is_secret_like(path):
    name = Path(path).name
    return any(p.search(name) for p in SECRET_PATTERNS)


def check_tracked():
    bad = [f for f in tracked_files() if is_secret_like(f)]
    return bad


def check_workflows():
    bad = []
    wf_dir = ROOT / ".github" / "workflows"
    if not wf_dir.exists():
        return bad
    for wf in wf_dir.glob("*.y*ml"):
        for lineno, line in enumerate(wf.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if re.search(r"git\s+add\b.*session", stripped, re.I):
                bad.append(f"{wf.relative_to(ROOT)}:{lineno} → {stripped}")
    return bad


def check_gitignore():
    gi = ROOT / ".gitignore"
    if not gi.exists():
        return list(REQUIRED_IGNORES)
    text = gi.read_text(encoding="utf-8")
    lines = {ln.strip() for ln in text.splitlines()}
    return [p for p in REQUIRED_IGNORES if p not in lines]


def main():
    tracked = check_tracked()
    workflows = check_workflows()
    ignores = check_gitignore()

    ok = True
    if tracked:
        ok = False
        print("❌ فایل نشست/کوکی در گیت ردیابی می‌شود:")
        for f in tracked:
            print(f"   {f}")
        print("   درمان: git rm --cached <file>  +  افزودن به .gitignore")
    else:
        print("✅ هیچ فایل نشست/کوکی در گیت ردیابی نمی‌شود.")

    if workflows:
        ok = False
        print("❌ ورک‌فلو فایل نشست را کامیت می‌کند:")
        for w in workflows:
            print(f"   {w}")
    else:
        print("✅ هیچ ورک‌فلویی فایل نشست را git add نمی‌کند.")

    if ignores:
        ok = False
        print("❌ الگوی محرمانه در .gitignore غایب است:")
        for p in ignores:
            print(f"   {p}")
    else:
        print("✅ همهٔ الگوهای محرمانه در .gitignore حاضرند.")

    if not ok:
        print("\n۱ یا چند مورد قانون امنیت نشست را نقض می‌کند.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
