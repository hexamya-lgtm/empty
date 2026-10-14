# Hex FPL – اتوماسیون محتوا

بررسی پست‌های کانال [@HexFPL](https://t.me/hexfpl) و طرح یک ایجنت دومرحله‌ای (پیشنهاد ← تأیید ← انتشار) برای تولید خودکار پست‌های محتوایی فارسی.

- `docs/automation-report.html` — گزارش کامل: انواع پست، میزان خودکارشدنی بودن هر کدام، طرح ایجنت، منابع، هزینه و فازبندی.
- `analysis/classify_posts.py` — دسته‌بندی قاعده‌محور پست‌های یک نویسنده از خروجی CSV کانال.
- `analysis/output/category_summary.csv` — تعداد، سهم و میانه‌ی تعامل هر دسته (کل دوره و سه ماه اخیر).
- `analysis/output/monthly.csv` — تعداد ماهانه‌ی پست‌های زنده و محتوایی.
- `sources/x_accounts.csv` — فهرست اکانت‌های فوتبالی X برای پایش ایجنت: دسته، باشگاه، رده‌ی اعتبار، اولویت، کاربرد و وضعیت راستی‌آزمایی هندل.
- `analysis/build_source_list.py` — ساخت همان فهرست از خروجی دسته‌بندی و کشف اکانت‌ها.

اجرای دوباره:

```bash
python analysis/classify_posts.py data/channel.csv analysis/output --author Hesam --author Hesäm --since 2026-07-15
```
