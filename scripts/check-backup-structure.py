#!/usr/bin/env python3
"""بازرس قانون ساختار بکاپ: هر اپ باید از EmaratBackupPath استفاده کند."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {'vendor', 'node_modules', 'fund-automation-android', 'restricted', '.git'}
APPS = {
    'gold/percent.html': 'gold1', 'gold2/percent.html': 'gold2',
    'gold3/percent.html': 'gold3', 'gold4/percent.html': 'gold4',
    'gold5/percent.html': 'gold5', 'gold6/percent.html': 'gold6',
    'gold7/percent.html': 'gold7', 'gold8/percent.html': 'gold8',
    'gold9/percent.html': 'gold9', 'gym/index.html': 'gym',
    'ai-chat/index.html': 'ai-chat', 'skincare/index.html': 'skincare',
}


def main():
    errors = []

    lib = ROOT / 'backup-path.js'
    if not lib.exists():
        errors.append('backup-path.js وجود ندارد')

    for rel, app in APPS.items():
        p = ROOT / rel
        if not p.exists():
            errors.append(f'{rel}: فایل نیست')
            continue
        s = p.read_text(encoding='utf-8')
        if 'backup-path.js' not in s:
            errors.append(f'{rel}: اسکریپت backup-path.js تزریق نشده')
        if f'"{app}"' not in s and f"'{app}'" not in s:
            errors.append(f'{rel}: شناسهٔ اپ «{app}» در EmaratBackupPath نیست')

    for rel, app in (('gold/percent.html', 'gold1'), ('gold4/percent.html', 'gold4'),
                     ('gold5/percent.html', 'gold5'), ('gold9/percent.html', 'gold9')):
        p = ROOT / rel
        if p.exists() and 'recordUpdate(' not in p.read_text(encoding='utf-8'):
            errors.append(f'{rel}: recordUpdate صدا زده نمی‌شود')

    tracker = ROOT / 'usage-tracker.js'
    if tracker.exists() and 'EmaratBackupPath' not in tracker.read_text(encoding='utf-8'):
        errors.append('usage-tracker.js: از EmaratBackupPath استفاده نمی‌کند')

    # هیچ بکاپی نباید در مخزن عمومی ردیابی شود
    for pat in ('gold4/gold4_backup.json', 'gold5/gold5_backup.json',
                'monthly-deposit/fund_backup.json'):
        p = ROOT / pat
        if p.exists():
            try:
                import subprocess
                r = subprocess.run(['git', 'ls-files', '--error-unmatch', pat],
                                   cwd=ROOT, capture_output=True)
                if r.returncode == 0:
                    errors.append(f'{pat}: هنوز در گیت ردیابی می‌شود (باید ignored باشد)')
            except Exception:
                pass

    sw = ROOT / 'sw.js'
    if sw.exists() and 'backup-path.js' not in sw.read_text(encoding='utf-8'):
        errors.append('sw.js: backup-path.js در ASSETS نیست')

    if errors:
        print('❌ نقض قانون ساختار بکاپ:')
        for e in errors:
            print('  -', e)
        print(f'\n{len(errors)} مورد نقض شد.')
        return 1
    print('✅ ساختار بکاپ در همهٔ اپ‌ها مطابق قانون است.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
