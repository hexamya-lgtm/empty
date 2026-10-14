"""
دسته‌بندی قاعده‌محور پست‌های یک نویسنده در خروجی CSV کانال تلگرام.

استفاده:
    python analysis/classify_posts.py <channel.csv> <out_dir> [--author Hesam --author Hesäm] [--since 2026-07-15]

خروجی:
    <out_dir>/posts_classified.csv   هر پست با ستون cat (نوع محتوا) و comp (رقابت)
    <out_dir>/category_summary.csv   تعداد، سهم و میانه تعامل هر دسته (کل دوره و دوره اخیر)
    <out_dir>/monthly.csv            تعداد ماهانه پست‌های زنده و محتوایی

دقت: قواعد regex هستند و برای برآورد کلی کافی‌اند (حدود ۸۰–۸۵٪ درست در نمونه‌گیری دستی)،
نه برای برچسب‌گذاری تک‌تک پست‌ها.
"""
import argparse, os, re
import pandas as pd
ap=argparse.ArgumentParser()
ap.add_argument('csv'); ap.add_argument('out_dir')
ap.add_argument('--author',action='append',default=None)
ap.add_argument('--since',default='2026-07-15')
args=ap.parse_args()
authors=args.author or ['Hesam','Hesäm']
os.makedirs(args.out_dir,exist_ok=True)
df=pd.read_csv(args.csv)
df=df[df.author_signature.isin(authors)].copy()
df['date']=pd.to_datetime(df['date'])
df['text']=df.text.fillna('')
FOOT=re.compile(r'^.*@Hex\w*.*$',re.M|re.I)
df['footer']=df.text.str.contains('@HexFPL',case=False)
df['body']=df.text.apply(lambda t: FOOT.sub('',re.sub(r'#\w+','',t)).strip())
df['blen']=df.body.str.len()

def has(t,p): return re.search(p,t,re.I|re.M) is not None
MANAGERS=r'مارسکا|اسلوت|اسلات|اشلوت|آرتتا|گلاسنر|آموریم|فرانک|دی ?‌?زربی|پپ|گواردیولا|ایرائولا|هاو\b|ساژ|هورزلر|امری|فارکه|کریک|لو بریس|رزه|مویس|اندروز|آلونسو|ژابی|روزنیور|نونو|پاتر|کوپر|سیلوا|لوپتگی|اسلاتن|یایسله|فرای|فن پرسی|گراهام پاتر|سرمربی'
LIVE_EVT=r'گل|اسیست|پاس گل|تعویض|کارت|پنالتی|آفساید|VAR|دقیقه|سیو|بونس|کلین ?شیت|نیمه|وقت اضافه|شوت|موقعیت|خروجی|\bIN\b|\bOUT\b|زد|دفکان|defcon|BPS'
RULES=[
 ('promo_bot', r'ربات|پریمیوم|Premium|اشتراک|تخفیف|افیلیت|Affiliate|/start|/group|کد لیگ|اسپانسر|hexfpl\.ir|ble\.ir|ثبت ?نام|لینک عضویت|لینک ورود'),
 ('personal_team', r'Free Transfers?|Overall:|تیم (من|خودم)|من (این هفته|امسال)|ترنسفر(های)? من'),
 ('price_changes', r'تغییرات[_ ]قیمت|📈 افزایش|افزایش قیمت|کاهش قیمت'),
 ('odds_market', r'#Odds|ضرایب|بازارهای شرط|پیش‌بینی‌های مارکت|شرط‌?بندی|درصد کلین'),
 ('live_event', r'Top (DEFCON|BPS)|^\s*\d \| \d+ - |⌚️? ?\d+\'|BONUS|بونس (احتمالی|زنده)'),
 ('fpl_data', r'Hex Average|بهترین مربی|Top10k|توزیع رتبه|آمار کاپیتانی|Highest EO|انتخاب شده توسط|فروش توسط|ownership|مالکیت|بیشترین ترنسفر|بیشترین خرید|بیشترین فروش|از ۱۰ نفر اول|رتبه (اول|دوم|سوم) دنیا|تاپ ?10k|top ?10k'),
 ('fpl_advice_strong', r'اساتید|درفت|وایلدکارت|وایلد کارت|فری ?‌?هیت|بنچ ?بوست|تریپل|کاپیتان|دیفرنشیال|#Scout|BGW|DGW|دابل ?گیم|بلنک'),
 ('fixtures_schedule', r'^🗓|▶️ ?[۰-۹0-9]{2}[:：][۰-۹0-9]{2}'),
 ('team_news_lineup', r'ترکیب (?!منتخب)|XI\b'),
 ('transfer_news', r'رومانو|جیکوبز|اورنستین|اورنشتین|ارنستین|Romano|Ornstein|HERE WE GO|هیر وی گو|نقل ?و ?انتقال|قرارداد|تمدید|پیشنهاد(?!ی)|میلیون (پوند|یورو)|سرمربی جدید|معرفی (خواهد|شد)|جذب|اخراج|توافق|مذاکر|^✅ \S+( \S+)? به \S+|\bبه (چلسی|آرسنال|لیورپول|سیتی|یونایتد|تاتنهام|نیوکسل|ویلا|بایرن|رئال|بارسا)\b|قرضی|جدایی|انتقال'),
 ('injury_team_news', r'مصدوم|غایب|محروم|دور از میادین|آماده(ی)? (بازی|حضور)|در دسترس|بیماری|جراحی|تمرین|ریکاوری|بازگشت|برمی‌?گرد|نیمکت|ترکیب (اصلی|احتمالی)|فیکس|استارت|روتیشن|دقایق بازی|شایعات.*غیبت'),
 ('press_conference', r'«|کنفرانس|مصاحبه|:\s*$|(%s)\s*(درباره|:)' % MANAGERS),
 ('fpl_advice', r'کاپیتان|وایلدکارت|وایلد کارت|فری ?هیت|بنچ ?بوست|تریپل|دیفرنشیال|\bdiff|#Scout|\bEO\b|xGI|گزینه|ترنسفر|درفت|اساتید|کارشناس|فیکسچر|fixture|\bBB\d|\bWC\d|\bFH\d|\bTC\d|بخرید|بفروشید|hidden gem|differential|captain|wildcard|منتخب|بنچ|GW\d+|گیم‌?ویک|هفته (\S+ )?(بعد|آینده)|DGW|BGW|دابل|بلنک|چیپ|FFScout|اسکات|اسکوت|ددلاین'),
 ('stats_trivia', r'آمار|\bxG\b|\bxA\b|shots|on target|big chances|key passes|touches|بیشترین|کمترین|رکورد|میانگین|تا اینجای فصل|اولین|نخستین|متوالی|تاریخ|فقط \S+ (تونسته|توانسته|از)|\d+ بازی|درصد|اوپتا|Opta|📊|مقایسه'),
 ('fpl_game_community', r'چلنج|Challenge|تغییرات فانتزی|قوانین|مینی‌?لیگ|لیگ هکس|اعضا|رتبه‌های اعضا|سوپرلیگ|تیم‌های شرکت'),
 ('results_review', r'خلاصه|نتایج|پایان بازی|\bFT\b|Full ?Time|برد|شکست داد|تساوی|جدول|براکت|صعود|حذف|قهرمان|توپ طلا|تیم (رویایی|منتخب) هفته|\d ?- ?\d|[۰-۹] ?- ?[۰-۹]|2⃣|1⃣|0⃣'),
 ('general_news', r'🚨|گاردین|بلومبرگ|اتحادیه|داور|قضاوت|بی‌?بی‌?سی|اسکای|تلگراف|تایمز|اتلتیک|لکیپ|بیلد|رسمی|اعلام|پرونده|مجازات|باشگاه|ورزشگاه|بازی دوستانه|پیش ?فصل'),
 ('engagement', r'نظرتون|نظر شما|شما (چی|کی|کدوم|هم)|کامنت|بنویسید|بگید|امتیازتون|چطور گذشت|\?|؟|کیا|کسایی که'),
]
def cls(r):
    t=r.text; b=r.body
    if r.media_type=='poll': return 'engagement'
    if r.media_type in ('sticker','gif'): return 'meme_humor'
    if has(b,r'^🗓|▶️ ?[۰-۹0-9]{2}[:：][۰-۹0-9]{2}'): return 'fixtures_schedule'
    if r.blen==0: return 'meme_humor'
    if not r.footer and r.blen<=140 and r.media_type=='text':
        if has(b,r'Top (DEFCON|BPS)|^\s*\d \| \d+ - '): return 'live_event'
        return 'live_event' if has(b,LIVE_EVT) else 'live_reaction'
    for name,p in RULES:
        if has(t,p): return name
    if r.media_type in('photo','video','album','voice','audio') and r.blen<=150: return 'meme_humor'
    if not r.footer and r.blen<=250: return 'live_reaction'
    return 'other'
df['cat']=df.apply(cls,axis=1).replace({'fpl_advice_strong':'fpl_advice','team_news_lineup':'injury_team_news'})
def comp(t):
    if re.search(r'#FIFAWorldCup|جام جهانی|World ?Cup|#WCfantasy',t,re.I): return 'world_cup'
    if re.search(r'#UCLfantasy|لیگ قهرمانان|UCL|#UWCL|🇪🇺',t,re.I): return 'ucl'
    return 'pl_fpl'
df['comp']=df.text.apply(comp)
df['tehran']=df.date.dt.tz_convert('Asia/Tehran')
df=df.drop(columns=[c for c in df.columns if c.startswith('reaction_')])
df.to_csv(os.path.join(args.out_dir,'posts_classified.csv'),index=False)

LIVE={'live_reaction','live_event'}
def summary(d):
    g=d.groupby('cat').agg(n=('cat','size'),views_median=('views','median'),reactions_median=('reactions_total','median'),forwards_median=('forwards','median'),body_len_median=('blen','median'))
    g['share_pct']=(g.n/g.n.sum()*100).round(1)
    return g
recent=df[df.tehran>=pd.Timestamp(args.since,tz='Asia/Tehran')]
days=max((recent.tehran.max()-recent.tehran.min()).days,1)
s=summary(df).join(summary(recent).add_prefix('recent_'),how='left')
s['recent_per_week']=(s.recent_n/days*7).round(1)
s.sort_values('n',ascending=False).to_csv(os.path.join(args.out_dir,'category_summary.csv'))
m=df.assign(month=df.tehran.dt.strftime('%Y-%m'),kind=df.cat.map(lambda c:'live' if c in LIVE else 'content'))
m.groupby(['month','kind']).size().unstack(fill_value=0).to_csv(os.path.join(args.out_dir,'monthly.csv'))
print(s.sort_values('n',ascending=False)[['n','share_pct','recent_n','recent_share_pct','recent_per_week','recent_views_median','recent_reactions_median']])
