#!/usr/bin/env python3
"""بازرس قانون اساسی دکمهٔ به‌روزرسانی.

هر صفحهٔ HTML در ریشه و زیرپوشه‌ها باید دقیقاً یک بار refresh-button.js را
لود کند. خروجی غیرصفر یعنی نقض قانون.

اجرا:  python3 scripts/check-refresh-button.py
"""
import pathlib
import sys

SKIP_DIRS = {
    'vendor', 'node_modules', '.git', '.github', '.agents', '.agent_tmp',
    'fund-automation-android', 'restricted',
}
TAG = 'refresh-button.js'


def main() -> int:
    root = pathlib.Path(__file__).resolve().parent.parent
    missing, duplicate = [], []

    for page in sorted(root.rglob('*.html')):
        if set(page.relative_to(root).parts) & SKIP_DIRS:
            continue
        count = page.read_text(encoding='utf-8', errors='ignore').count(TAG)
        rel = page.relative_to(root)
        if count == 0:
            missing.append(rel)
        elif count > 1:
            duplicate.append((rel, count))

    total = len(missing) + len(duplicate)
    for rel in missing:
        print(f'❌ بدون دکمه: {rel}')
    for rel, n in duplicate:
        print(f'❌ تکراری ({n} بار): {rel}')

    if total:
        print(f'\n{total} صفحه قانون اساسی را نقض می‌کند.')
        return 1

    print('✅ همهٔ صفحات دقیقاً یک دکمهٔ به‌روزرسانی دارند.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
