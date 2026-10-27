# Build the static bilingual site for lhcviet.com into docs/ (served by GitHub Pages).
# Source text: content/noi-dung_v03.md (copied verbatim from the LHC Profile 2026 v45r5).
# Usage: python3 tools/build.py
import html, re, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'docs'
SITE = 'https://lhcviet.com'
YEAR = '2026'
md = (ROOT / 'content' / 'noi-dung_v03.md').read_text(encoding='utf-8')
E = html.escape


# ---------- content ----------
def sec(start, end=None):
    i = md.index(start)
    j = md.index(end, i + 1) if end else len(md)
    return md[i:j]

def pairs(block):
    return re.findall(r'- \*\*VN:\*\* (.+)\n- \*\*EN:\*\* (.+)', block)

nums_raw = pairs(sec('### Con số năng lực', '### Đoạn'))
intro = pairs(sec('### Đoạn giới thiệu ngắn', '## 2.'))
vision = pairs(sec('### Tầm nhìn', '### Sứ mệnh'))[0]
mission = pairs(sec('### Sứ mệnh', '### Giá trị'))[0]
vals_raw = [p for p in pairs(sec('### Giá trị cốt lõi', '### Ba trụ cột')) if re.match(r'0\d ', p[0])]
pill_txt = pairs(sec('### Ba trụ cột', '## 3.'))
quality = pairs(sec('## 5. Quản lý chất lượng', '## 6.'))
why = pairs(sec('## 6. Vì sao chọn LHC', '## 7.'))
contact = pairs(sec('## 7. Liên hệ', '## 8.'))
clients = pairs(sec('## 4. Khách hàng và đối tác', '## 5.'))

STATS = [('122', 'hợp đồng, nhiệm vụ, 2015–2026', 'contracts and assignments, 2015–2026'),
         ('96', 'dự án, tiểu dự án', 'projects and subprojects'),
         ('11', 'đối tác phát triển và tổ chức tài chính', 'development partners and financial institutions'),
         ('34/34', 'tỉnh, thành phố và Lào', 'provinces and cities, plus Laos'),
         ('77', 'hợp đồng LHC độc lập hoặc đứng đầu liên danh', 'contracts as single firm or JV lead member')]
# guard: the figures above must match the source text
for (n, v, e), (sv, se) in zip(STATS, nums_raw):
    assert sv.startswith(n) and v.split(',')[0].split(' ')[0] in sv and e.split(' ')[0] in se, (n, sv)

VALUES = []
for vn, en in vals_raw:
    wv = vn[3:].split(' ')
    ne, se = en[3:].split(' ', 1)
    VALUES.append((vn[:2], (' '.join(wv[:2]), ne), (' '.join(wv[2:]), se)))

PILLARS = list(zip([('Môi trường', 'Environment'), ('Con người', 'People'), ('Vốn tự nhiên', 'Natural Capital')], pill_txt))

SERVICES = []
heads = re.findall(r'(?m)^### (3\.\d) (.+?) / (.+)$', md)
SLUG_EN = ['environment-ohs', 'social-resettlement', 'natural-capital', 'disaster-climate', 'gis-data', 'implementation-support']
SLUG_VI = ['moi-truong-ats', 'xa-hoi-tai-dinh-cu', 'von-tu-nhien', 'thien-tai-khi-hau', 'gis-du-lieu', 'ho-tro-thuc-hien']
for k, (code, tv, te) in enumerate(heads):
    nxt = heads[k + 1][0] if k + 1 < len(heads) else None
    blk = sec(f'### {code} ', f'### {nxt} ' if nxt else '## 4.')
    cap_blk, proj_blk = blk.split('**Một số dự án')
    projs = []
    for vn, en in pairs(proj_blk):
        fv = [x.strip() for x in vn.split('·')]
        fe = [x.strip() for x in en.split('·')]
        if len(fv) == 4:  # a project line without location, or without output
            if re.match(r'\d{4}', fv[2]):
                fv.insert(2, ''); fe.insert(2, '')
            else:
                fv.append(''); fe.append('')
        projs.append((fv, fe))
    SERVICES.append(dict(n=code[-1], title=(tv, te), caps=pairs(cap_blk), projs=projs,
                         id={'vi': SLUG_VI[k], 'en': SLUG_EN[k]}))

GROUPS, FIN = clients[:4], clients[4]

princ = [p for p in quality if re.match(r'\d ', p[0])]
QNAMES = [('Phù hợp yêu cầu', 'Conformity with requirements'), ('Dựa trên bằng chứng', 'Evidence-based'),
          ('Đúng chuyên môn, đúng vai trò', 'Right expertise, right role'), ('Rà soát và kiểm soát', 'Review and control'),
          ('Cải tiến liên tục', 'Continual improvement')]
PRINCIPLES = [(QNAMES[i], (vn[2 + len(QNAMES[i][0]) + 1:], en[2 + len(QNAMES[i][1]) + 1:])) for i, (vn, en) in enumerate(princ)]
STEPS = [('Rà soát yêu cầu, lập kế hoạch', 'Requirements review, planning'), ('Huy động, phân công chuyên gia', 'Mobilize and assign experts'),
         ('Kiểm soát dữ liệu và phương pháp', 'Control of data and methods'), ('Rà soát kỹ thuật, kiểm tra chéo', 'Technical review, cross-check'),
         ('Kiểm soát trước phát hành', 'Control before release'), ('Phản hồi, chỉnh sửa, lưu giữ', 'Feedback, revision, archiving')]
WHY = [(why[i], why[i + 1]) for i in range(1, len(why), 2)]

COMPANY = contact[0]
ADDRESS = contact[1]
CREDO = contact[2]
PHONE, PHONE_TEL, EMAIL = '+84 913 189 758', '+84913189758', 'admin@lhcviet.com'


# ---------- pages ----------
PAGES = {  # key: (vi path, en path, vi nav label, en nav label)
    'home': ('', 'en/', 'Trang chủ', 'Home'),
    'about': ('gioi-thieu/', 'en/about/', 'Giới thiệu', 'About'),
    'services': ('dich-vu/', 'en/services/', 'Dịch vụ', 'Services'),
    'contact': ('lien-he/', 'en/contact/', 'Liên hệ', 'Contact'),
}
NAV = ['about', 'services', 'contact']


def path_of(key, L):
    return PAGES[key][0 if L == 'vi' else 1]

def rel(frm, to):
    up = '../' * frm.count('/')
    return (up + to) or './'


logo_svg = (ROOT / 'assets' / 'logo.svg').read_text(encoding='utf-8')
LOGO = re.sub(r'<title>.*?</title>', '', logo_svg).replace('fill="#008854"', 'fill="currentColor"') \
    .replace('width="230" height="81"', 'class="logo" aria-hidden="true" focusable="false"')


def page(key, L, title, desc, body):
    me = path_of(key, L)
    other = 'en' if L == 'vi' else 'vi'
    r = lambda p: rel(me, p)
    x = lambda p: p[0] if L == 'vi' else p[1]
    nav = ''.join(f'<a href="{r(path_of(k, L))}"{" aria-current=page" if k == key else ""}>{E(PAGES[k][2 if L == "vi" else 3])}</a>' for k in NAV)
    full_title = f'{title} | LHC Việt Nam' if L == 'vi' else f'{title} | LHC Viet Nam'
    if key == 'home':
        full_title = title
    return f'''<!doctype html>
<html lang="{L}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(full_title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{SITE}/{me}">
<link rel="alternate" hreflang="vi" href="{SITE}/{path_of(key, 'vi')}">
<link rel="alternate" hreflang="en" href="{SITE}/{path_of(key, 'en')}">
<link rel="alternate" hreflang="x-default" href="{SITE}/{path_of(key, 'vi')}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="LHC Việt Nam">
<meta property="og:title" content="{E(full_title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{SITE}/{me}">
<meta property="og:image" content="{SITE}/assets/og.png">
<meta property="og:locale" content="{'vi_VN' if L == 'vi' else 'en_US'}">
<meta name="theme-color" content="#0d3b2a">
<link rel="icon" href="{r('assets/favicon.svg')}" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600&amp;family=Literata:opsz,wght@7..72,500;7..72,600&amp;display=swap">
<link rel="stylesheet" href="{r('assets/site.css')}">
</head>
<body>
<a class="skip" href="#main">{'Bỏ qua menu' if L == 'vi' else 'Skip to content'}</a>
<header class="top"><div class="wrap">
 <a class="brand" href="{r(path_of('home', L))}" aria-label="{'LHC Việt Nam, trang chủ' if L == 'vi' else 'LHC Viet Nam, home'}">{LOGO}</a>
 <nav aria-label="{'Menu chính' if L == 'vi' else 'Main menu'}">{nav}</nav>
 <a class="lang" href="{r(path_of(key, other))}" hreflang="{other}" lang="{other}">{'English' if L == 'vi' else 'Tiếng Việt'}</a>
</div></header>
<main id="main">
{body}
</main>
<footer><div class="wrap">
 <div class="fcol"><p class="fname">{E(x(COMPANY))}</p><p>{E(x(ADDRESS))}</p>
 <p><a href="tel:{PHONE_TEL}">{PHONE}</a> · <a href="mailto:{EMAIL}">{EMAIL}</a></p></div>
 <div class="fcol fright"><p>Quality Earns Trust</p><p>© {YEAR} LHC {'Việt Nam' if L == 'vi' else 'Viet Nam'}</p></div>
</div></footer>
</body>
</html>
'''


def svc_list(L, me):
    x = lambda p: p[0] if L == 'vi' else p[1]
    target = path_of('services', L)
    return ''.join(f'<li><a class="card" href="{rel(me, target)}#{s["id"][L]}"><span class="scode">{s["n"]}</span>'
                   f'<span class="stitle">{E(x(s["title"]))}</span></a></li>' for s in SERVICES)


def home(L):
    me = path_of('home', L)
    x = lambda p: p[0] if L == 'vi' else p[1]
    v = L == 'vi'
    stats = ''.join(f'<div class="stat"><b>{n}</b><p>{E(a if v else b)}</p></div>' for n, a, b in STATS)
    pillars = ''.join(f'<article class="pillar"><h3>{E(x(n))}</h3><p>{E(x(t))}</p></article>' for n, t in PILLARS)
    groups = ''.join(f'<li>{E(x(g))}</li>' for g in GROUPS)
    whys = ''.join(f'<li><h3>{E(x(h))}</h3><p>{E(x(t))}</p></li>' for h, t in WHY)
    body = f'''<div class="hero"><div class="wrap">
 <p class="kicker">{'LHC Việt Nam · Thành lập 2014, Hà Nội' if v else 'LHC Viet Nam · Established 2014, Ha Noi'}</p>
 <h1>{'Tư vấn môi trường, xã hội và vốn tự nhiên' if v else 'Environmental, Social &amp; Natural Capital Advisory'}</h1>
 <p class="pillars-line">{'Môi trường · Con người · Vốn tự nhiên' if v else 'Environment · People · Natural Capital'}</p>
 <p class="cta"><a class="btn" href="{rel(me, path_of('services', L))}">{'Dịch vụ' if v else 'Our services'}</a><a class="btn ghost" href="{rel(me, path_of('contact', L))}">{'Liên hệ' if v else 'Contact us'}</a></p>
 <div class="stats">{stats}</div>
</div></div>

<section><div class="wrap two">
 <div class="shead"><p class="kicker">{'Giới thiệu' if v else 'About us'}</p><h2>{'Hơn mười năm tư vấn cho dự án đầu tư công và tư nhân' if v else 'More than ten years advising public and private investment projects'}</h2></div>
 <div class="prose"><p>{E(x(intro[0]))}</p><p><a class="more" href="{rel(me, path_of('about', L))}">{'Tìm hiểu về LHC' if v else 'More about LHC'}</a></p></div>
</div></section>

<section class="tint"><div class="wrap">
 <div class="shead"><p class="kicker">{'Ba trụ cột' if v else 'Three pillars'}</p></div>
 <div class="pillars">{pillars}</div>
</div></section>

<section><div class="wrap">
 <div class="shead"><p class="kicker">{'Dịch vụ' if v else 'Services'}</p><h2>{'Sáu nhóm dịch vụ' if v else 'Six service lines'}</h2></div>
 <ul class="cards">{svc_list(L, me)}</ul>
</div></section>

<section class="tint"><div class="wrap">
 <div class="shead"><p class="kicker">{'Khách hàng và đối tác' if v else 'Clients and partners'}</p><h2>{'Chúng tôi làm việc với' if v else 'We work with'}</h2></div>
 <ul class="groups">{groups}</ul>
 <div class="fin"><h3 class="lbl">{'Nguồn vốn của các dự án' if v else 'Project financing'}</h3><p>{E(x(FIN))}</p></div>
</div></section>

<section><div class="wrap">
 <div class="shead"><p class="kicker">{'Vì sao chọn LHC' if v else 'Why LHC'}</p><h2>{E(x(why[0]))}</h2></div>
 <ul class="why">{whys}</ul>
</div></section>

<section class="band"><div class="wrap">
 <p class="credo">{E(x(CREDO))}</p>
 <p class="cta"><a class="btn" href="{rel(me, path_of('contact', L))}">{'Liên hệ với chúng tôi' if v else 'Get in touch'}</a></p>
</div></section>'''
    title = 'LHC Việt Nam · Tư vấn môi trường, xã hội và vốn tự nhiên' if v else 'LHC Viet Nam · Environmental, Social & Natural Capital Advisory'
    desc = ('Công ty tư vấn môi trường, xã hội, tái định cư, dân tộc thiểu số, giới và vốn tự nhiên tại Hà Nội; ĐTM, ESIA, RAP, EMDP, SEP, giám sát độc lập cho dự án vốn WB, ADB, JICA, AFD, IFC.'
            if v else 'Ha Noi-based environmental, social, resettlement, ethnic minority, gender and natural capital consultancy; EIA, ESIA, RAP, EMDP, SEP and independent monitoring for WB, ADB, JICA, AFD and IFC-financed projects.')
    return page('home', L, title, desc, body)


def about(L):
    x = lambda p: p[0] if L == 'vi' else p[1]
    v = L == 'vi'
    values = ''.join(f'<li><span class="vnum">{n}</span><h3>{E(x(nm))}</h3><p>{E(x(t))}</p></li>' for n, nm, t in VALUES)
    pillars = ''.join(f'<article class="pillar"><h3>{E(x(n))}</h3><p>{E(x(t))}</p></article>' for n, t in PILLARS)
    prs = ''.join(f'<li><h3>{E(x(n))}</h3><p>{E(x(t))}</p></li>' for n, t in PRINCIPLES)
    steps = ''.join(f'<li>{E(x(s))}</li>' for s in STEPS)
    body = f'''<div class="phead"><div class="wrap"><p class="kicker">{'Giới thiệu' if v else 'About us'}</p><h1>{'LHC Việt Nam' if v else 'LHC Viet Nam'}</h1></div></div>
<section><div class="wrap two">
 <div class="prose">{''.join(f'<p>{E(x(p))}</p>' for p in (intro[0], intro[1], intro[3]))}</div>
 <div class="prose"><div class="vm"><h2>{'Tầm nhìn' if v else 'Vision'}</h2><p>{E(x(vision))}</p></div><div class="vm"><h2>{'Sứ mệnh' if v else 'Mission'}</h2><p>{E(x(mission))}</p></div></div>
</div></section>
<section class="tint"><div class="wrap">
 <div class="shead"><p class="kicker">{'Giá trị cốt lõi' if v else 'Core values'}</p></div>
 <ul class="values">{values}</ul>
</div></section>
<section><div class="wrap">
 <div class="shead"><p class="kicker">{'Ba trụ cột' if v else 'Three pillars'}</p></div>
 <div class="pillars">{pillars}</div>
</div></section>
<section class="tint" id="{'chat-luong' if v else 'quality'}"><div class="wrap">
 <div class="shead"><p class="kicker">{'Quản lý chất lượng' if v else 'Quality management'}</p><h2>{E(x(quality[0]))}</h2><p class="lede">{E(x(quality[1]))}</p></div>
 <div class="two">
  <div><h3 class="sub">{'Năm nguyên tắc' if v else 'Five principles'}</h3><ol class="princ">{prs}</ol></div>
  <div><h3 class="sub">{'Quy trình sáu bước' if v else 'Six-step process'}</h3><ol class="steps">{steps}</ol></div>
 </div>
</div></section>'''
    title = 'Giới thiệu' if v else 'About'
    desc = (x(vision)[:155] + '…')
    return page('about', L, title, desc, body)


def services(L):
    me = path_of('services', L)
    x = lambda p: p[0] if L == 'vi' else p[1]
    v = L == 'vi'
    blocks = ''
    for s in SERVICES:
        caps = ''.join(f'<li>{E(x(c))}</li>' for c in s['caps'])
        projs = ''
        for fv, fe in s['projs']:
            f = fv if v else fe
            meta = ' · '.join(p for p in (f[2], f[3]) if p)
            projs += (f'<li class="proj"><span class="pfund">{E(f[1])}</span><span class="pname">{E(f[0])}</span>'
                      f'<span class="pmeta">{E(meta)}</span>' + (f'<span class="pout">{E(f[4])}</span>' if f[4] else '') + '</li>')
        blocks += (f'<section class="svc" id="{s["id"][L]}"><div class="wrap">'
                   f'<div class="shead"><p class="kicker">{"Dịch vụ" if v else "Service"} {s["n"]}</p><h2>{E(x(s["title"]))}</h2></div>'
                   f'<div class="two"><div><h3 class="lbl">{"Năng lực" if v else "Capabilities"}</h3><ul class="caps">{caps}</ul></div>'
                   f'<div><h3 class="lbl">{"Một số dự án" if v else "Selected projects"}</h3><ul class="projs">{projs}</ul></div></div>'
                   f'</div></section>\n')
    body = f'''<div class="phead"><div class="wrap"><p class="kicker">{'Dịch vụ' if v else 'Services'}</p><h1>{'Sáu nhóm dịch vụ' if v else 'Six service lines'}</h1>
 <p class="lede">{'Dự án được nêu theo lĩnh vực, nguồn vốn, địa bàn, năm và sản phẩm.' if v else 'Projects are listed by sector, financing, location, year and outputs.'}</p>
 <ul class="cards compact">{svc_list(L, me)}</ul></div></div>
{blocks}'''
    title = 'Dịch vụ' if v else 'Services'
    desc = ('ĐTM, ESIA/ESMP, kế hoạch tái định cư, EMDP, SEP, LMP, giám sát độc lập, kiểm toán ESHS, vốn tự nhiên, rủi ro thiên tai, GIS và hỗ trợ thực hiện dự án.'
            if v else 'EIA, ESIA/ESMP, resettlement plans, EMDP, SEP, LMP, independent monitoring, ESHS audits, natural capital, disaster risk, GIS and implementation support.')
    return page('services', L, title, desc, body)


def contact_page(L):
    x = lambda p: p[0] if L == 'vi' else p[1]
    v = L == 'vi'
    maps = 'https://www.google.com/maps/search/?api=1&amp;query=' + '38B+ng%C3%B5+77+Xu%C3%A2n+La%2C+T%C3%A2y+H%E1%BB%93%2C+H%C3%A0+N%E1%BB%99i'
    body = f'''<div class="phead"><div class="wrap"><p class="kicker">{'Liên hệ' if v else 'Contact'}</p><h1>{E(x(COMPANY))}</h1></div></div>
<section><div class="wrap two">
 <dl class="contact">
  <dt>{'Trụ sở' if v else 'Head office'}</dt><dd>{E(x(ADDRESS).split(': ', 1)[1])}<br><a href="{maps}" rel="noopener">{'Xem bản đồ' if v else 'View on map'}</a></dd>
  <dt>{'Điện thoại' if v else 'Telephone'}</dt><dd><a href="tel:{PHONE_TEL}">{PHONE}</a></dd>
  <dt>Email</dt><dd><a href="mailto:{EMAIL}">{EMAIL}</a></dd>
 </dl>
 <p class="credo">{E(x(CREDO))}</p>
</div></section>'''
    title = 'Liên hệ' if v else 'Contact'
    desc = f'{x(COMPANY)}. {x(ADDRESS)}. {PHONE}. {EMAIL}'
    return page('contact', L, title, desc, body)


NOT_FOUND = '''<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Không tìm thấy trang | Page not found</title><meta name="robots" content="noindex">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/site.css"></head>
<body><main id="main"><div class="phead"><div class="wrap">
<p class="kicker">404</p><h1>Không tìm thấy trang</h1><p class="lede" lang="en">Page not found</p>
<p class="cta"><a class="btn" href="/">Trang chủ</a><a class="btn ghost" href="/en/" lang="en">Home (English)</a></p>
</div></div></main></body></html>
'''


def favicon():
    # first mark of the logo only
    s = re.sub(r'<title>.*?</title>', '', logo_svg).replace('viewBox="0 0 230 81" width="230" height="81"', 'viewBox="0 0 86 81"')
    return s


def og_image(dst):
    from PIL import Image
    W, H = 1200, 630
    img = Image.new('RGB', (W, H), (246, 248, 246))
    logo = Image.open(ROOT / 'assets' / 'logo_3000px.png').convert('RGBA')
    w = 760
    logo = logo.resize((w, round(logo.height * w / logo.width)), Image.LANCZOS)
    img.paste(logo, ((W - w) // 2, (H - logo.height) // 2), logo)
    bar = Image.new('RGB', (W, 28), (0, 136, 84))
    img.paste(bar, (0, H - 28))
    img.save(dst, optimize=True)


def build():
    cname = (OUT / 'CNAME').read_text() if (OUT / 'CNAME').exists() else None  # written by GitHub Pages settings
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / 'assets').mkdir(parents=True)
    builders = {'home': home, 'about': about, 'services': services, 'contact': contact_page}
    urls = []
    for key, fn in builders.items():
        for L in ('vi', 'en'):
            p = path_of(key, L)
            d = OUT / p
            d.mkdir(parents=True, exist_ok=True)
            (d / 'index.html').write_text(fn(L), encoding='utf-8')
            urls.append((key, p))
    (OUT / '404.html').write_text(NOT_FOUND, encoding='utf-8')
    shutil.copy(ROOT / 'assets' / 'site.css', OUT / 'assets' / 'site.css')
    (OUT / 'assets' / 'favicon.svg').write_text(favicon(), encoding='utf-8')
    og_image(OUT / 'assets' / 'og.png')
    (OUT / '.nojekyll').write_text('')
    if cname:
        (OUT / 'CNAME').write_text(cname)
    (OUT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n')
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for key, p in urls:
        sm.append(f'<url><loc>{SITE}/{p}</loc>'
                  f'<xhtml:link rel="alternate" hreflang="vi" href="{SITE}/{path_of(key, "vi")}"/>'
                  f'<xhtml:link rel="alternate" hreflang="en" href="{SITE}/{path_of(key, "en")}"/></url>')
    sm.append('</urlset>')
    (OUT / 'sitemap.xml').write_text('\n'.join(sm) + '\n')
    print('built', len(urls), 'pages into', OUT)


if __name__ == '__main__':
    build()
