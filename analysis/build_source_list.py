"""
ساخت فهرست منابع X برای ایجنت از خروجی دسته‌بندی فالووینگ‌ها و اکانت‌های کشف‌شده.

استفاده:
    python analysis/build_source_list.py <workflow_result.json> <following.csv> <out.csv>

ورودی JSON (خروجی workflow، که فالووینگ‌های غیرفوتبالی را هم دارد و در مخزن نمی‌آید) سه کلید دارد: classified (اکانت‌هایی که الان فالو می‌کنید)،
candidates (اکانت‌های پیشنهادی جدید با نتیجه‌ی راستی‌آزمایی) و gaps.
خروجی فقط اکانت‌های فوتبالی را نگه می‌دارد؛ اکانت‌های غیرفوتبالی کنار گذاشته می‌شوند.
"""
import csv, json, sys

COLUMNS = ['username', 'name', 'origin', 'category', 'club', 'tier', 'priority',
           'use_for', 'verification', 'evidence_url', 'note']
PRIORITY_ORDER = {'core': 0, 'extended': 1, 'monitor': 2, 'skip': 3}
# منابعی که حسام در پست‌هایش بارها نقل کرده (جیکوبز ۱۸، کروک ۸، مت لاو ۶ بار)
CORE_OVERRIDES = {'jacobsben', 'alex_crook', 'matt_law_dt'}
# حساب‌های شخصی که منبع خبری نیستند
EXCLUDE = {'__msnp__'}


def main(result_path, following_path, out_path):
    result = json.load(open(result_path, encoding='utf-8'))
    names = {r['username'].lower(): r['name'] for r in csv.DictReader(open(following_path, encoding='utf-8'))}

    rows = []
    for a in result['classified']:
        if not a['football_related'] or a['category'] == 'non_football' or a['username'].lower() in EXCLUDE:
            continue
        if a['username'].lower() in CORE_OVERRIDES:
            a['priority'] = 'core'
        rows.append({
            'username': a['username'], 'name': names.get(a['username'].lower(), ''),
            'origin': 'following', 'category': a['category'], 'club': a['club'],
            'tier': a['tier'], 'priority': a['priority'], 'use_for': ' '.join(a['use_for']),
            'verification': 'followed', 'evidence_url': '', 'note': a['note'],
        })

    for c in result['candidates']:
        v = c.get('verification') or {}
        verdict = v.get('verdict', 'unchecked')
        if verdict in ('not_active', 'not_relevant'):
            continue
        handle = c['username']
        if verdict == 'handle_corrected' and v.get('corrected_username'):
            handle = v['corrected_username'].lstrip('@')
        # اولویت پیشنهادی حفظ می‌شود؛ ستون verification می‌گوید کدام هندل‌ها
        # باید قبل از پایش با API خود X چک شوند (unverifiable)
        rows.append({
            'username': handle, 'name': c['name'], 'origin': 'discovered',
            'category': c['category'], 'club': c['club'], 'tier': c['tier'],
            'priority': c['priority'],
            'use_for': ' '.join(c['use_for']), 'verification': verdict,
            'evidence_url': v.get('evidence_url') or c.get('evidence_url', ''),
            'note': c['why'] + (f" | {v['note']}" if v.get('note') else ''),
        })

    seen, unique = set(), []
    for r in rows:
        k = r['username'].lower()
        if k not in seen:
            seen.add(k)
            unique.append(r)
    unique.sort(key=lambda r: (PRIORITY_ORDER.get(r['priority'], 9), r['category'], r['club'], r['username'].lower()))

    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(unique)
    print(f'{len(unique)} football accounts written to {out_path}')


if __name__ == '__main__':
    main(*sys.argv[1:4])
