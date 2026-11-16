# Build the static bilingual site for lhcviet.com into docs/ (served by GitHub Pages).
# Source text: content/noi-dung_v08.md (LHC Profile 2026 v45r5, with anh Huy's edits of 28/10/2026; services shortened 31/10/2026).
# Usage: python3 tools/build.py
import hashlib
import html, re, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'docs'
SITE = 'https://lhcviet.com'
YEAR = '2026'
md = (ROOT / 'content' / 'noi-dung_v10.md').read_text(encoding='utf-8')
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

STATS = [(vn.split(' ', 1)[0], vn.split(' ', 1)[1], en.split(' ', 1)[1]) for vn, en in nums_raw]

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
    for vn, en in pairs(proj_blk):  # name · financing · region [· status] [· output] [year; LHC role]
        cards = []
        for line in (vn, en):
            m = re.search(r'\s*\[([^;\]]+); ([^\]]+)\]\s*$', line)
            yr, role = (m.group(1), m.group(2)) if m else ('', '')
            f = [x.strip() for x in (line[:m.start()] if m else line).split('·')]
            cards.append(dict(name=f[0], fund=f[1], meta=' · '.join(f[2:-1] if len(f) > 3 else f[2:]),
                              out=f[-1] if len(f) > 3 else '', year=yr, role=role))
        projs.append(tuple(cards))
    SERVICES.append(dict(n=code[-1], title=(tv, te), caps=pairs(cap_blk), projs=projs,
                         id={'vi': SLUG_VI[k], 'en': SLUG_EN[k]}))

GROUPS, FIN = clients[:4], clients[4]
CSS_V = hashlib.md5((ROOT / 'assets' / 'site.css').read_bytes()).hexdigest()[:8]  # cache-busting: browsers reload CSS when it changes

FUNDERS = {
    'WB': ('World Bank', 'https://www.worldbank.org'),
    'ADB': ('Asian Development Bank', 'https://www.adb.org'),
    'JICA': ('Japan International Cooperation Agency', 'https://www.jica.go.jp/english/'),
    'IFC': ('International Finance Corporation', 'https://www.ifc.org'),
    'AFD': ('Agence Française de Développement', 'https://www.afd.fr/en'),
    'JBIC': ('Japan Bank for International Cooperation', 'https://www.jbic.go.jp/en/'),
    'IFAD': ('International Fund for Agricultural Development', 'https://www.ifad.org'),
    'GEF': ('Global Environment Facility', 'https://www.thegef.org'),
    'UNDP': ('United Nations Development Programme', 'https://www.undp.org'),
    'EIB': ('European Investment Bank', 'https://www.eib.org'),
    'KEXIM': ('Export-Import Bank of Korea', 'https://www.koreaexim.go.kr'),
}


def fin_strip(L):
    names, rest = (FIN[0] if L == 'vi' else FIN[1]).split(';', 1)
    chips = ''.join(f'<li><a href="{FUNDERS[n][1]}" title="{E(FUNDERS[n][0])}" target="_blank" rel="noopener">{n}</a></li>'
                    for n in (t.strip() for t in names.split(',')) if n in FUNDERS)
    return f'<ul class="funders">{chips}</ul><p class="finrest">{E(rest.strip().rstrip(".").capitalize())}.</p>'

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
PHONE, PHONE_TEL, EMAIL = '+84 913 189 758', '+84913189758', 'info@lhcviet.com'


# ---------- pages ----------
PAGES = {  # key: (vi path, en path, vi nav label, en nav label)
    'home': ('', 'en/', 'Trang chủ', 'Home'),
    'about': ('gioi-thieu/', 'en/about/', 'Giới thiệu', 'About'),
    'services': ('dich-vu/', 'en/services/', 'Dịch vụ', 'Services'),
    'contact': ('lien-he/', 'en/contact/', 'Liên hệ', 'Contact'),
    'updates': ('cap-nhat/', 'en/updates/', 'Cập nhật chuyên môn', 'Updates'),
    'links': ('lien-ket/', 'en/links/', 'Liên kết hữu ích', 'Useful links'),
    'projects': ('du-an/', 'en/projects/', 'Dự án', 'Projects'),  # also holds the field photos (old /hinh-anh/ redirects here)
    'terms': ('dieu-khoan-su-dung/', 'en/terms/', 'Điều khoản sử dụng', 'Terms of use'),
}
NAV = ['about', 'services', 'projects', 'updates', 'contact']
FOOT = ['about', 'services', 'projects', 'updates', 'links', 'contact']
NAV_LABEL = {'about': ('Giới thiệu', 'About'), 'services': ('Dịch vụ', 'Services'), 'projects': ('Dự án', 'Projects'),
             'updates': ('Cập nhật', 'Updates'), 'contact': ('Liên hệ', 'Contact')}


def path_of(key, L):
    return PAGES[key][0 if L == 'vi' else 1]

def rel(frm, to):
    up = '../' * frm.count('/')
    return (up + to) or './'


logo_svg = (ROOT / 'assets' / 'logo.svg').read_text(encoding='utf-8')
LOGO = re.sub(r'<title>.*?</title>', '', logo_svg).replace('fill="#008854"', 'fill="currentColor"') \
    .replace('width="230" height="81"', 'class="logo" aria-hidden="true" focusable="false"')


ORG_LD = ('<script type="application/ld+json">{"@context":"https://schema.org","@type":"Organization",'
          '"name":"Công ty TNHH Thương mại và Đầu tư LHC Việt Nam",'
          '"alternateName":["LHC Viet Nam Investment and Trading Company Limited","LHC Việt Nam"],'
          f'"url":"{SITE}/","logo":"{SITE}/assets/og.png","foundingDate":"2014-12-29",'
          '"address":{"@type":"PostalAddress","streetAddress":"Số 38B ngõ 77 đường Xuân La","addressLocality":"Phường Tây Hồ, Hà Nội","addressCountry":"VN"}}</script>\n')


def page(key, L, title, desc, body):
    me = path_of(key, L)
    other = 'en' if L == 'vi' else 'vi'
    r = lambda p: rel(me, p)
    x = lambda p: p[0] if L == 'vi' else p[1]
    cur = 'updates' if key.startswith('post:') else key
    nav = ''.join(f'<a href="{r(path_of(k, L))}"{" aria-current=page" if k == cur else ""}>{E(NAV_LABEL[k][0 if L == "vi" else 1])}</a>' for k in NAV)
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
<meta property="og:type" content="{'article' if key.startswith('post:') else 'website'}">
<meta property="og:site_name" content="LHC Việt Nam">
<meta property="og:title" content="{E(full_title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{SITE}/{me}">
<meta property="og:image" content="{SITE}/assets/og.png">
<meta property="og:locale" content="{'vi_VN' if L == 'vi' else 'en_US'}">
<meta name="theme-color" content="#ffffff">
<link rel="icon" href="{r('assets/favicon.svg')}" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@300;400;500;600&amp;display=swap">
<link rel="stylesheet" href="{r('assets/site.css')}?v={CSS_V}">
{ORG_LD if key == 'home' else ''}<script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{{"token": "946c4e495cce4109bbbc216c7077181c"}}'></script>
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
 <div class="fcol"><p class="fname">{E(COMPANY[0])}</p><p class="fname2">{E(COMPANY[1])}</p>
 <p>{'Thành lập năm 2014 · Mã số doanh nghiệp: 0106730052' if L == 'vi' else 'Established 2014 · Enterprise code: 0106730052'}</p>
 <p>{E(x(ADDRESS))}</p>
 <p><a href="tel:{PHONE_TEL}">{PHONE}</a> · <a href="mailto:{EMAIL}">{EMAIL}</a></p></div>
 <nav class="fcol fnav" aria-label="{'Liên kết chân trang' if L == 'vi' else 'Footer links'}">{''.join(f'<a href="{r(path_of(k, L))}">{E(PAGES[k][2 if L == 'vi' else 3])}</a>' for k in FOOT)}</nav>
 <div class="fcol fright"><p>Quality Earns Trust</p><p class="fcopy">© {YEAR} {E(x(COMPANY).split(' (')[0])}. {'Bảo lưu mọi quyền.' if L == 'vi' else 'All rights reserved.'}</p><p><a href="{r(path_of('terms', L))}">{'Điều khoản sử dụng' if L == 'vi' else 'Terms of use'}</a></p></div>
</div></footer>
</body>
</html>
'''


PHOTOS = {  # key: (file stem, alt VN, alt EN, width/height); caption = alt
    'field': ('thuc-dia-khao-sat', 'Cán bộ LHC khảo sát, phỏng vấn người dân tại hiện trường', 'LHC staff interviewing a local resident during a field survey', 4/3),
    'consult': ('hop-tham-van-cong-dong', 'Họp tham vấn cộng đồng', 'Community consultation meeting', 1600/672),
    'site': ('cong-truong-xay-dung', 'Kiểm soát ra vào tại công trường xây dựng', 'Access control at a construction site', 1272/704),
    'resettle': ('khu-tai-dinh-cu', 'Khu tái định cư đang xây dựng', 'Resettlement site under construction', 1600/1063),
    'training': ('hoi-thao-tap-huan', 'Hội thảo tập huấn về quản lý môi trường – xã hội cho cán bộ dự án', 'Environmental and social management training workshop for project staff', 4/3),
    'team': ('lam-viec-nhom', 'Buổi làm việc của nhóm chuyên gia trong nước và quốc tế', 'Working session of national and international experts', 4/3),
}
PHOTO_SRC = {k: dict(n=n, big=1600, w=1600, h=round(1600 / r), alt=(av, ae), cap=(av, ae)) for k, (n, av, ae, r) in PHOTOS.items()}

# Field photos taken by LHC Viet Nam (faces, number plates, signs and client names blurred; no EXIF/GPS).
# Caption = place and month/year only, as recorded in the photo register (Bang_phan_loai_anh_website_v03).
# key: (file stem, width, height of the -1280 file, alt VN, alt EN, caption VN, caption EN)
FIELD = {
    'p08': ('trang-chu-de-bien-hau-loc', 1085, 604, 'Đê biển và cống ngăn triều ven bãi bồi', 'Sea dyke and tidal sluice on a mudflat coast', 'Hậu Lộc, Thanh Hóa · 11/2024', 'Hau Loc, Thanh Hoa · Nov 2024'),
    'p10': ('doi-ngu-thuc-dia-hau-loc', 1280, 960, 'Nhóm chuyên gia khảo sát hiện trường', 'Expert team on a site survey', 'Hậu Lộc, Thanh Hóa · 10/2024', 'Hau Loc, Thanh Hoa · Oct 2024'),
    'p41': ('lo-gach-mang-thit', 1280, 765, 'Lò gạch thủ công', 'Traditional brick kiln', 'Mang Thít, Vĩnh Long · 06/2025', 'Mang Thit, Vinh Long · Jun 2025'),
    'p07': ('tham-van-cong-dong-hau-loc-v03', 1280, 960, 'Họp tham vấn cộng đồng tại nhà văn hóa thôn', 'Community consultation in a village hall', 'Hậu Lộc, Thanh Hóa · 11/2024', 'Hau Loc, Thanh Hoa · Nov 2024'),
    'p05': ('nha-ven-song-tam-binh', 712, 720, 'Nhà ở ven sông', 'Riverside houses on stilts', 'Tam Bình, Vĩnh Long · 06/2025', 'Tam Binh, Vinh Long · Jun 2025'),
    'p09': ('bai-trieu-hau-loc', 1085, 604, 'Bãi triều và tàu cá lúc nước ròng', 'Tidal flat and fishing boats at low tide', 'Hậu Lộc, Thanh Hóa · 11/2024', 'Hau Loc, Thanh Hoa · Nov 2024'),
    'p43': ('hoi-nghi-du-an', 850, 650, 'Hội nghị của dự án', 'Project meeting', '', ''),
    'p01': ('hop-lam-viec-ha-noi', 1280, 960, 'Cuộc họp làm việc', 'Working meeting', 'Hà Nội', 'Ha Noi'),
    'p42': ('khao-sat-bang-ghe-mang-thit', 712, 720, 'Khảo sát kênh rạch bằng ghe', 'Surveying canals by boat', 'Mang Thít, Vĩnh Long · 06/2025', 'Mang Thit, Vinh Long · Jun 2025'),
    'p12': ('hoi-thao-tam-ky', 1280, 960, 'Hội thảo', 'Workshop', 'Tam Kỳ, Quảng Nam · 06/2024', 'Tam Ky, Quang Nam · Jun 2024'),
    'p33': ('vuon-cao-su-binh-phuoc', 1280, 960, 'Khảo sát tại vườn cao su', 'Site visit to a rubber plantation', 'Bình Phước · 11/2023', 'Binh Phuoc · Nov 2023'),
    'p36': ('hop-cong-truong-vieng-chan', 1280, 960, 'Họp tại văn phòng công trường', 'Meeting at a construction site office', 'Viêng Chăn, Lào', 'Vientiane, Lao PDR'),  # anh Huy 16/11/2026: place only, no date
    'p21': ('cang-ca-nghi-son', 1280, 960, 'Tàu cá neo đậu tại cảng', 'Fishing boats moored in port', 'Nghi Sơn, Thanh Hóa · 01/2024', 'Nghi Son, Thanh Hoa · Jan 2024'),
    'p40': ('cang-ca-thanh-hoa', 1280, 960, 'Khu cảng cá', 'Fishing port', 'Thanh Hóa · 10/2021', 'Thanh Hoa · Oct 2021'),
    'p38': ('sinh-ke-cau-ngang', 795, 765, 'Nông dân vận chuyển nông sản sau thu hoạch', 'Farmers hauling harvested produce', 'Cầu Ngang, Trà Vinh · 05/2022', 'Cau Ngang, Tra Vinh · May 2022'),
    'p02': ('cang-bien-ha-tinh', 1280, 960, 'Nhóm chuyên gia tại cầu cảng, mang đồ bảo hộ', 'Team on a port jetty in safety gear', 'Hà Tĩnh · 09/2025', 'Ha Tinh · Sep 2025'),
    'n01': ('nui-da-voi-rung', 1280, 719, 'Rừng trên núi đá vôi và ruộng lúa', 'Forest on limestone hills above rice fields', 'Rừng trên núi đá vôi và ruộng lúa', 'Forest on limestone hills above rice fields'),
    'b04': ('ho-chua-chi-linh', 638, 430, 'Hồ chứa và mặt đập kết hợp đường', 'Reservoir with a dam crest road', 'Chí Linh, Hải Dương · 04/2019', 'Chi Linh, Hai Duong · Apr 2019'),
    'p06': ('kenh-do-thi-ha-tinh', 1280, 960, 'Kênh thoát nước đô thị', 'Urban drainage canal', 'Thành phố Hà Tĩnh · 11/2024', 'Ha Tinh City · Nov 2024'),
}
PHOTO_SRC.update({k: dict(n=n, big=638 if k == 'b04' else 1280, w=w, h=h, alt=(av, ae), cap=(cv, ce)) for k, (n, w, h, av, ae, cv, ce) in FIELD.items()})
GALLERY = ['p42', 'p06', 'p21', 'p36', 'p38', 'p01']  # newest first, undated last; dropped by anh Huy 16/11/2026: p02 (hi-vis vests), p33 (rubber), p40 (Thanh Hoa 10/2021), b04 (Hai Duong 2019); p12 now on service 6


HOME_FIELD = ['p42', 'p05', 'p06']  # home 'From the field' band: boat survey, riverside houses, urban canal
SVC_PHOTO = {'1': 'p41', '2': 'p07', '3': 'n01', '4': 'p05', '5': 'p09', '6': 'p12'}


def img_tag(key, L, me, sizes='(min-width:1120px) 1072px, 100vw', lazy=True):
    f = PHOTO_SRC[key]
    b = rel(me, f"assets/photos/{f['n']}-{f['big']}.jpg")
    a = rel(me, f"assets/photos/{f['n']}-800.jpg") if f['big'] > 800 else b  # small originals: one file only
    alt = f['alt'][0 if L == 'vi' else 1]
    srcset = f'{a} 800w, {b} {f["big"]}w' if f['big'] > 800 else f'{b} {f["big"]}w'
    return (f'<img src="{a}" srcset="{srcset}" sizes="{sizes}" width="{f["w"]}" height="{f["h"]}" alt="{E(alt)}"'
            + (' loading="lazy"' if lazy else '') + ' decoding="async">')


HALF = '(min-width:1120px) 528px, (min-width:720px) 50vw, 100vw'


def photo(key, L, me, cls='photo', sizes='(min-width:1120px) 1072px, 100vw'):
    cap = PHOTO_SRC[key]['cap'][0 if L == 'vi' else 1]
    return f'<figure class="{cls}">{img_tag(key, L, me, sizes)}' + (f'<figcaption>{E(cap)}</figcaption>' if cap else '') + '</figure>'


def svc_list(L, me):
    x = lambda p: p[0] if L == 'vi' else p[1]
    target = path_of('services', L)
    return ''.join(f'<li><a class="card" href="{rel(me, target)}#{s["id"][L]}"><span class="scode">{s["n"]}</span>'
                   f'<span class="stitle">{E(x(s["title"]))}</span></a></li>' for s in SERVICES)


def svc_photo_cards(L, me):  # home: six service cards, each with a small field photo
    x = lambda p: p[0] if L == 'vi' else p[1]
    target = path_of('services', L)
    return ''.join(f'<li><a class="scard" href="{rel(me, target)}#{s["id"][L]}">'
                   f'{img_tag(SVC_PHOTO[s["n"]], L, me, "(min-width:1120px) 352px, (min-width:720px) 33vw, 100vw")}'
                   f'<span class="sbody"><span class="scode">{s["n"]}</span><span class="stitle">{E(x(s["title"]))}</span></span></a></li>'
                   for s in SERVICES)


SVC_SHORT = [('Môi trường, an toàn lao động', 'Environment, OHS'), ('Xã hội, tái định cư', 'Social, resettlement'),
             ('Vốn tự nhiên', 'Natural capital'), ('Thiên tai, khí hậu', 'Disaster, climate'),
             ('GIS, dữ liệu', 'GIS, data'), ('Hỗ trợ thực hiện', 'Implementation support')]
FUND_KEYS = ['WB', 'ADB', 'AFD', 'IFC', 'JICA', 'JBIC', 'GEF', 'UNDP', 'EIB', 'NSNN']
FUND_LABEL = {'NSNN': ('Ngân sách nhà nước', 'State budget')}


def fund_keys(fund):  # 'GEF qua ADB' -> GEF ADB; 'Ngân sách nhà nước' -> NSNN
    if 'Ngân sách' in fund or 'budget' in fund:
        return ['NSNN']
    return [t for t in re.split(r',\s*|\s+qua\s+|\s+through\s+', fund) if t]


ALL_PROJECTS = []  # (service index, vi card, en card), newest first by end year
for i, s in enumerate(SERVICES):
    for pv, pe in s['projs']:
        ALL_PROJECTS.append((i, pv, pe))
ALL_PROJECTS.sort(key=lambda t: -int(re.findall(r'\d{4}', t[1]['year'])[-1]) if t[1]['year'] else 0)
FEATURED = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 1), (5, 2)]  # (service, project) shown on the home page


def proj_card(i, f, L, me, filt=False):
    v = L == 'vi'
    s = SERVICES[i]
    data = f' data-s="{s["n"]}" data-f="{" ".join(fund_keys(f["fund"]))}"' if filt else ''
    return (f'<li class="pcard"{data}><p class="ptop"><span class="pfund">{E(f["fund"])}</span>'
            + (f'<span class="pyear">{E(f["year"])}</span>' if f['year'] else '') + '</p>'
            f'<h3 class="pname">{E(f["name"])}</h3>'
            + (f'<p class="pmeta">{E(f["meta"])}</p>' if f['meta'] else '')
            + (f'<p class="pout">{E(f["out"])}</p>' if f['out'] else '')
            + (f'<p class="prole">{"Vai trò của LHC" if v else "LHC role"}: {E(f["role"])}</p>' if f['role'] else '')
            + f'<a class="psvc" href="{rel(me, path_of("services", L))}#{s["id"][L]}">{"Dịch vụ" if v else "Service"} {s["n"]} · {E(SVC_SHORT[i][0 if v else 1])}</a></li>')


def home(L):  # PA4 "Quốc tế" (16/11/2026): typographic hero, one wide landscape, rule-separated lists, three field photos
    me = path_of('home', L)
    x = lambda p: p[0] if L == 'vi' else p[1]
    v = L == 'vi'
    groups = ''.join(f'<li>{E(x(g))}</li>' for g in GROUPS)
    feat = ''.join(proj_card(i, SERVICES[i]['projs'][j][0 if v else 1], L, me) for i, j in FEATURED)
    hero = photo('n01', L, me, 'i-photo', '(min-width:1240px) 1160px, 100vw').replace('<figcaption>', '<figcaption hidden>').replace(' loading="lazy"', ' fetchpriority="high"')
    stats = ''.join(f'<div><b>{n}</b><span>{E(a if v else b)}</span></div>' for n, a, b in STATS)
    svc = ''.join(f'<li><a href="{rel(me, path_of("services", L))}#{s["id"][L]}"><span class="n">{int(s["n"]):02d}</span>'
                  f'<span class="t">{E(x(s["title"]))}</span><span class="ar" aria-hidden="true">→</span></a></li>' for s in SERVICES)
    field = ''.join(f'<li>{photo(k, L, me, "", "(min-width:1240px) 370px, (min-width:760px) 31vw, 78vw")}</li>' for k in HOME_FIELD)
    body = f'''<div class="i-hero"><div class="wrap">
 <p class="kicker">{'LHC Việt Nam · Hà Nội, từ 2014' if v else 'LHC Viet Nam · Ha Noi, since 2014'}</p>
 <h1>{'Tư vấn môi trường, xã hội và vốn tự nhiên' if v else 'Environmental, social and natural capital advisory'}</h1>
 <div class="i-sub"><p class="i-pil">{' · '.join(['Môi trường', 'Con người', 'Vốn tự nhiên'] if v else ['Environment', 'People', 'Natural Capital'])}</p>
 <p class="cta"><a class="btn" href="{rel(me, path_of('services', L))}">{'Dịch vụ' if v else 'Our services'}</a><a class="more" href="{rel(me, path_of('contact', L))}">{'Liên hệ' if v else 'Contact us'}</a></p></div>
</div></div>
<div class="wrap">{hero}<div class="i-stats">{stats}</div></div>

<section><div class="wrap i-split">
 <div class="shead"><p class="kicker">{'Giới thiệu' if v else 'About us'}</p></div>
 <div><p class="i-lead">{E(x(intro[0]))}</p><p><a class="more" href="{rel(me, path_of('about', L))}">{'Tìm hiểu về LHC' if v else 'More about LHC'}</a></p></div>
</div></section>

<section class="soft"><div class="wrap i-split">
 <div class="shead"><p class="kicker">{'Dịch vụ' if v else 'Services'}</p><h2>{'Sáu nhóm dịch vụ' if v else 'Six service lines'}</h2></div>
 <ol class="i-svc">{svc}</ol>
</div></section>

<section><div class="wrap">
 <div class="shead"><p class="kicker">{'Từ hiện trường' if v else 'From the field'}</p><h2>{'Khảo sát, tham vấn và giám sát tại địa bàn dự án' if v else 'Surveys, consultation and monitoring on site'}</h2></div>
 <ul class="i-field">{field}</ul>
 <p class="cta" style="margin-top:40px"><a class="more" href="{rel(me, path_of('projects', L))}#{'hinh-anh' if v else 'photos'}">{'Xem thêm hình ảnh' if v else 'More photos'}</a></p>
</div></section>

<section><div class="wrap">
 <div class="shead"><p class="kicker">{'Dự án tiêu biểu' if v else 'Selected projects'}</p><h2>{'Một số dự án gần đây' if v else 'Recent work'}</h2></div>
 <ul class="pgrid">{feat}</ul>
 <p class="cta"><a class="btn ghost" href="{rel(me, path_of('projects', L))}">{'Xem tất cả dự án' if v else 'All projects'}</a></p>
</div></section>

<section class="soft"><div class="wrap i-split">
 <div class="shead"><p class="kicker">{'Khách hàng và nguồn vốn' if v else 'Clients and financing'}</p><h2>{'Chúng tôi làm việc với' if v else 'We work with'}</h2></div>
 <div><ul class="groups">{groups}</ul>
 <div class="fin"><h3 class="lbl">{'Nguồn vốn của các dự án' if v else 'Project financing'}</h3>{fin_strip(L)}</div></div>
</div></section>

<section class="i-dark"><div class="wrap"><p class="kicker">{'Cam kết' if v else 'Our commitment'}</p><p class="credo">{E(x(CREDO))}</p>
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
    whys = ''.join(f'<li><h3>{E(x(h))}</h3><p>{E(x(t))}</p></li>' for h, t in WHY)
    body = f'''<div class="phead"><div class="wrap"><p class="kicker">{'Giới thiệu' if v else 'About us'}</p><h1>{'LHC Việt Nam' if v else 'LHC Viet Nam'}</h1></div></div>
<section><div class="wrap"><div class="prose wide">{''.join(f'<p>{E(x(p))}</p>' for p in intro)}</div></div></section>
<section class="tint" id="{'tam-nhin' if v else 'vision'}"><div class="wrap">
 <div class="shead"><p class="kicker">{'Tầm nhìn · Sứ mệnh · Giá trị cốt lõi' if v else 'Vision · Mission · Core values'}</p><h2>{'Mỗi dự án là một cam kết.' if v else 'Every project is a commitment.'}</h2></div>
 <div class="vmrow">
  <div class="vmblk"><h3>{'Tầm nhìn' if v else 'Vision'}</h3><p>{E(x(vision))}</p></div>
  <div class="vmblk"><h3>{'Sứ mệnh' if v else 'Mission'}</h3><p>{E(x(mission))}</p></div>
 </div>
 <h3 class="vmh">{'Giá trị cốt lõi' if v else 'Core values'}</h3>
 <ul class="values">{values}</ul>
</div></section>
<section><div class="wrap">
 <div class="shead"><p class="kicker">{'Ba trụ cột' if v else 'Three pillars'}</p></div>
 <div class="pillars">{pillars}</div>
 {photo('p10', L, path_of('about', L), 'photo svcphoto fp ptop', '(min-width:920px) 880px, 100vw')}
</div></section>
<section id="{'vi-sao-chon-lhc' if v else 'why-lhc'}"><div class="wrap">
 <div class="shead"><p class="kicker">{'Vì sao chọn LHC' if v else 'Why LHC'}</p><h2>{E(x(why[0]))}</h2></div>
 <ul class="why">{whys}</ul>
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
        for pv, pe in s['projs']:
            f = pv if v else pe
            projs += (f'<li class="proj"><span class="pfund">{E(f["fund"])}</span><span class="pname">{E(f["name"])}</span>'
                      f'<span class="pmeta">{E(" · ".join(x for x in (f["year"], f["meta"]) if x))}</span>'
                      + (f'<span class="pout">{E(f["out"])}</span>' if f['out'] else '')
                      + (f'<span class="prole">{"Vai trò của LHC" if v else "LHC role"}: {E(f["role"])}</span>' if f['role'] else '') + '</li>')
        blocks += (f'<section class="svc" id="{s["id"][L]}"><div class="wrap">'
                   f'<div class="shead"><p class="kicker">{"Dịch vụ" if v else "Service"} {s["n"]}</p><h2>{E(x(s["title"]))}</h2></div>'
                   + (photo(SVC_PHOTO[str(s["n"]).lstrip("0")], L, me, 'photo svcphoto fp', '(min-width:920px) 880px, 100vw') if str(s["n"]).lstrip("0") in SVC_PHOTO else '') +
                   f'<div class="two"><div><h3 class="lbl">{"Năng lực" if v else "Capabilities"}</h3><ul class="caps">{caps}</ul></div>'
                   f'<div><h3 class="lbl">{"Một số dự án" if v else "Selected projects"}</h3><ul class="projs">{projs}</ul></div></div>'
                   f'</div></section>\n')
    body = f'''<div class="phead"><div class="wrap"><p class="kicker">{'Dịch vụ' if v else 'Services'}</p><h1>{'Sáu nhóm dịch vụ' if v else 'Six service lines'}</h1>
 <ul class="cards compact">{svc_list(L, me)}</ul></div></div>
{blocks}'''
    title = 'Dịch vụ' if v else 'Services'
    desc = ('ĐTM, ESIA/ESMP, kế hoạch tái định cư, EMDP, SEP, LMP, giám sát độc lập, kiểm toán ESHS, vốn tự nhiên, rủi ro thiên tai, GIS và hỗ trợ thực hiện dự án.'
            if v else 'EIA, ESIA/ESMP, resettlement plans, EMDP, SEP, LMP, independent monitoring, ESHS audits, natural capital, disaster risk, GIS and implementation support.')
    return page('services', L, title, desc, body)


def contact_page(L):
    x = lambda p: p[0] if L == 'vi' else p[1]
    v = L == 'vi'
    body = f'''<div class="phead"><div class="wrap"><p class="kicker">{'Liên hệ' if v else 'Contact'}</p><h1>{E(x(COMPANY))}</h1></div></div>
<section><div class="wrap two">
 <dl class="contact">
  <dt>{'Trụ sở' if v else 'Head office'}</dt><dd>{E(x(ADDRESS).split(': ', 1)[1])}</dd>
  <dt>{'Điện thoại' if v else 'Telephone'}</dt><dd><a href="tel:{PHONE_TEL}">{PHONE}</a></dd>
  <dt>Email</dt><dd><a href="mailto:{EMAIL}">{EMAIL}</a></dd>
 </dl>
 <p class="credo">{E(x(CREDO))}</p>
</div></section>'''
    title = 'Liên hệ' if v else 'Contact'
    desc = f'{x(COMPANY)}. {x(ADDRESS)}. {PHONE}. {EMAIL}'
    return page('contact', L, title, desc, body)


# ---------- useful links ----------
LINKS = [  # (group vi, group en, [(name vi, name en, url)]) - official pages, checked 28/10/2026
    ('Khung chính sách môi trường và xã hội của nhà tài trợ', 'Financiers\' environmental and social frameworks', [
        ('Ngân hàng Thế giới (WB): Khung môi trường và xã hội', 'World Bank: Environmental and Social Framework', 'https://www.worldbank.org/esf'),
        ('Ngân hàng Phát triển châu Á (ADB): Khung chính sách môi trường và xã hội', 'Asian Development Bank: Environmental and Social Framework', 'https://www.adb.org/who-we-are/safeguards/environmental-social-framework'),
        ('IFC: Tiêu chuẩn hoạt động về bền vững môi trường và xã hội', 'IFC: Performance Standards on Environmental and Social Sustainability', 'https://www.ifc.org/performancestandards'),
        ('JICA: Hướng dẫn về cân nhắc môi trường và xã hội (2022)', 'JICA: Guidelines for Environmental and Social Considerations (2022)', 'https://www.jica.go.jp/english/our_work/social_environmental/guideline/'),
        ('AFD: Chính sách quản lý rủi ro môi trường và xã hội', 'AFD: Environmental and Social Risk Management Policy', 'https://www.afd.fr/en/ressources/environmental-and-social-risk-management-policy-afd-funded-operations'),
        ('UNDP: Tiêu chuẩn xã hội và môi trường', 'UNDP: Social and Environmental Standards', 'https://www.undp.org/accountability/social-and-environmental-responsibility/social-and-environmental-standards'),
    ]),
    ('Văn bản pháp luật và cơ quan nhà nước', 'Vietnamese law and government agencies', [
        ('Cơ sở dữ liệu quốc gia về pháp luật (Bộ Tư pháp)', 'National Legal Database (Ministry of Justice)', 'https://vbpl.vn/'),
        ('Hệ thống văn bản, Cổng Thông tin điện tử Chính phủ', 'Legal documents, Government e-Portal', 'https://vanban.chinhphu.vn/'),
        ('Cổng Thông tin điện tử Chính phủ', 'Government e-Portal of Viet Nam', 'https://chinhphu.vn/'),
        ('Bộ Nông nghiệp và Môi trường', 'Ministry of Agriculture and Environment', 'https://mae.gov.vn/'),
    ]),
]


def links_page(L):
    v = L == 'vi'
    groups = ''
    for gv, ge, items in LINKS:
        lis = ''.join(f'<li><a href="{u}" rel="noopener" target="_blank">{E(nv if v else ne)}</a><span class="host">{E(u.split("/")[2].removeprefix("www."))}</span></li>' for nv, ne, u in items)
        groups += f'<div><h2 class="sub">{E(gv if v else ge)}</h2><ul class="links">{lis}</ul></div>'
    body = f'''<div class="phead"><div class="wrap"><p class="kicker">{'Tài liệu tham khảo' if v else 'Reference'}</p><h1>{'Liên kết hữu ích' if v else 'Useful links'}</h1></div></div>
<section><div class="wrap two">{groups}</div></section>'''
    desc = ('Liên kết đến khung chính sách môi trường và xã hội của WB, ADB, IFC, JICA, AFD, UNDP và cơ sở dữ liệu pháp luật Việt Nam.'
            if v else 'Links to the environmental and social frameworks of WB, ADB, IFC, JICA, AFD and UNDP, and to Vietnamese legal databases.')
    return page('links', L, 'Liên kết hữu ích' if v else 'Useful links', desc, body)


FILTER_JS = '''<script>
(()=>{const bar=document.querySelector('.pfilters'),g=document.querySelector('.pgrid.all');if(!bar||!g)return;bar.hidden=false;
let s='',f='';const n=document.querySelector('.pcount'),none=document.querySelector('.pnone');
bar.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;
if(b.dataset.t==='s')s=b.dataset.v;else f=b.dataset.v;
b.parentElement.querySelectorAll('button').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));
let k=0;g.querySelectorAll('.pcard').forEach(c=>{const ok=(!s||c.dataset.s===s)&&(!f||c.dataset.f.split(' ').includes(f));c.hidden=!ok;k+=ok});
n.textContent=k;none.hidden=k>0});})();
</script>'''


def projects_page(L):
    v = L == 'vi'
    me = path_of('projects', L)
    cards = ''.join(proj_card(i, pv if v else pe, L, me, filt=True) for i, pv, pe in ALL_PROJECTS)
    used = {k for _, pv, _ in ALL_PROJECTS for k in fund_keys(pv['fund'])}
    btn = lambda t, val, lab, on=False: f'<button type="button" data-t="{t}" data-v="{val}" aria-pressed="{"true" if on else "false"}">{E(lab)}</button>'
    sbtn = btn('s', '', 'Tất cả' if v else 'All', True) + ''.join(btn('s', s['n'], SVC_SHORT[i][0 if v else 1]) for i, s in enumerate(SERVICES))
    fbtn = btn('f', '', 'Tất cả' if v else 'All', True) + ''.join(btn('f', k, FUND_LABEL.get(k, (k, k))[0 if v else 1]) for k in FUND_KEYS if k in used)
    items = ''.join(photo(k, L, me, 'photo gitem', HALF) for k in GALLERY)
    body = f'''<div class="phead"><div class="wrap"><p class="kicker">{'Dự án' if v else 'Projects'}</p><h1>{'Dự án tiêu biểu' if v else 'Selected projects'}</h1>
 <p class="lede">{'Một số dự án tiêu biểu LHC Việt Nam đã và đang thực hiện, kèm năm, nguồn vốn và vai trò của LHC. Tên chủ đầu tư và giá trị hợp đồng không được nêu.' if v else 'A selection of LHC Viet Nam assignments, with the year, source of financing and LHC\'s role. Client names and contract values are not disclosed.'}</p></div></div>
<section><div class="wrap">
 <div class="pfilters" hidden>
  <div class="fgroup"><p class="lbl">{'Lĩnh vực' if v else 'Service line'}</p><div class="fbtns">{sbtn}</div></div>
  <div class="fgroup"><p class="lbl">{'Nguồn vốn' if v else 'Financing'}</p><div class="fbtns">{fbtn}</div></div>
  <p class="pshow" aria-live="polite">{'Đang hiển thị' if v else 'Showing'} <span class="pcount">{len(ALL_PROJECTS)}</span> {'dự án' if v else 'projects'}</p>
 </div>
 <ul class="pgrid all">{cards}</ul>
 <p class="pnone" hidden>{'Không có dự án phù hợp với bộ lọc.' if v else 'No project matches these filters.'}</p>
</div></section>
<section class="tint" id="{'hinh-anh' if v else 'photos'}"><div class="wrap">
 <div class="shead"><p class="kicker">{'Hình ảnh' if v else 'Photos'}</p><h2>{'Hình ảnh hiện trường' if v else 'Field photos'}</h2>
 <p class="lede">{'Một số hình ảnh LHC Việt Nam chụp trong quá trình khảo sát, tham vấn và giám sát dự án. Khuôn mặt và thông tin nhận dạng đã được làm mờ.' if v else 'A selection of photos taken by LHC Viet Nam during project surveys, consultations and monitoring. Faces and identifying details have been blurred.'}</p></div>
 <div class="gallery">{items}</div>
</div></section>
{FILTER_JS}'''
    desc = ('Dự án tiêu biểu của LHC Việt Nam về môi trường, xã hội, tái định cư, vốn tự nhiên và khí hậu, kèm hình ảnh hiện trường; lọc theo lĩnh vực và nguồn vốn.'
            if v else 'Selected LHC Viet Nam projects in environment, social, resettlement, natural capital and climate, with field photos; filter by service line and financing.')
    return page('projects', L, 'Dự án' if v else 'Projects', desc, body)


TERMS_VI, TERMS_EN = re.sub(r'<!--.*?-->', '', (ROOT / 'content' / 'dieu-khoan.md').read_text(encoding='utf-8'), flags=re.S).split('=== EN ===')


def terms_page(L):
    v = L == 'vi'
    title = 'Điều khoản sử dụng' if v else 'Terms of use'
    body = f'''<div class="phead"><div class="wrap narrow"><p class="kicker">{'Bản quyền' if v else 'Copyright'}</p><h1>{title}</h1></div></div>
<section><div class="wrap narrow"><article class="post">{md2html(TERMS_VI if v else TERMS_EN)}</article></div></section>'''
    desc = ('Điều khoản sử dụng website lhcviet.com: quyền sở hữu nội dung, logo, hình ảnh của LHC Việt Nam, cách trích dẫn và báo vi phạm.'
            if v else 'Terms of use of lhcviet.com: ownership of LHC Viet Nam content, logo and images, how to quote, and how to report misuse.')
    return page('terms', L, title, desc, body)


# ---------- updates (posts) ----------
def inline(t):
    t = E(t, quote=False)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    return re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+)\)', r'<a href="\2" rel="noopener" target="_blank">\1</a>', t)

def md2html(text):
    out, items = [], []
    def flush():
        if items:
            out.append('<ul>' + ''.join(f'<li>{inline(i)}</li>' for i in items) + '</ul>'); items.clear()
    for block in re.split(r'\n\s*\n', text.strip()):
        for line in block.split('\n'):
            if line.startswith('- '):
                items.append(line[2:]); continue
            flush()
            if line.startswith('### '):
                out.append(f'<h2>{inline(line[4:])}</h2>')
            elif line.strip():
                out.append(f'<p>{inline(line)}</p>')
        flush()
    return '\n'.join(out)

def load_posts(include_drafts=False):
    posts = []
    for f in sorted((ROOT / 'content' / 'cap-nhat').glob('*.md'), reverse=True):
        raw = f.read_text(encoding='utf-8')
        _, fm, rest = raw.split('---\n', 2)
        meta = dict(line.split(': ', 1) for line in fm.strip().split('\n'))
        if meta['status'] != 'published' and not include_drafts:
            continue
        parts = re.split(r'(?m)^## (VI|EN|Nguồn / Sources)\s*$', rest)
        sect = dict(zip(parts[1::2], parts[2::2]))
        meta.update(vi=sect['VI'], en=sect['EN'], sources=sect.get('Nguồn / Sources', ''))
        key = 'post:' + meta['slug']
        PAGES[key] = (f"cap-nhat/{meta['slug']}/", f"en/updates/{meta['slug_en']}/", meta['title_vi'], meta['title_en'])
        meta['key'] = key
        posts.append(meta)
    return posts

def fmt_date(d, L):
    y, m, dd = d.split('-')
    return f'{dd}/{m}/{y}' if L == 'vi' else f'{int(dd)} {["January","February","March","April","May","June","July","August","September","October","November","December"][int(m)-1]} {y}'

def post_page(p, L):
    v = L == 'vi'
    me = path_of(p['key'], L)
    body = f'''<div class="phead"><div class="wrap narrow"><p class="kicker">{E(p['topic_vi' if v else 'topic_en'])}</p>
 <h1>{E(p['title_vi' if v else 'title_en'])}</h1><p class="lede">{E(p['summary_vi' if v else 'summary_en'])}</p></div></div>
<section><div class="wrap narrow"><article class="post">{md2html(p['vi' if v else 'en'])}
<h2>{'Nguồn' if v else 'Sources'}</h2>{md2html(p['sources'])}</article>
<p class="back"><a href="{rel(me, path_of('updates', L))}">{'Tất cả bài cập nhật' if v else 'All updates'}</a></p></div></section>'''
    return page(p['key'], L, p['title_vi' if v else 'title_en'], p['summary_vi' if v else 'summary_en'], body)

def updates_page(L, posts):
    v = L == 'vi'
    me = path_of('updates', L)
    items = ''.join(f'''<li><a class="pcard" href="{rel(me, path_of(p['key'], L))}"><span class="kicker">{E(p['topic_vi' if v else 'topic_en'])}</span>
 <span class="ptitle">{E(p['title_vi' if v else 'title_en'])}</span><span class="psum">{E(p['summary_vi' if v else 'summary_en'])}</span></a></li>''' for p in posts)
    if not posts:
        items = f"<li class=\"empty\">{'Bài viết đầu tiên sẽ được đăng trong thời gian tới.' if v else 'The first articles will be published soon.'}</li>"
    body = f'''<div class="phead"><div class="wrap"><p class="kicker">{'Cập nhật' if v else 'Updates'}</p><h1>{'Cập nhật chuyên môn' if v else 'Professional updates'}</h1>
 <p class="lede">{'Văn bản pháp luật mới, thay đổi chính sách của nhà tài trợ và hoạt động của LHC.' if v else 'New Vietnamese legislation, changes in financier policies and LHC news.'}</p></div></div>
<section><div class="wrap"><ul class="plist">{items}</ul></div></section>'''
    desc = ('Cập nhật pháp luật môi trường, đất đai, tái định cư và chính sách môi trường – xã hội của WB, ADB, JICA.'
            if v else 'Updates on Vietnamese environmental, land and resettlement law and on WB, ADB and JICA environmental and social policies.')
    return page('updates', L, 'Cập nhật chuyên môn' if v else 'Professional updates', desc, body)


NOT_FOUND = '''<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Không tìm thấy trang | Page not found</title><meta name="robots" content="noindex">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/site.css?v={CSS_V}"></head>
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


# Old web4s URLs (archived 28/10/2026) -> new pages, so links and search results keep working after the switch
OLD_ARTICLES = ['hop-chuan-bi-du-an-dau-tu-xay-dung-tuyen-duong-tranh-thanh-pho-son-la-tinh-son-la',
    'hoi-thao-bao-cao-ket-qua-danh-gia-hieu-qua-dau-tu-danh-gia-hoan-thanh-du-an-rgep',
    'hop-tham-van-cong-dong-dan-cu-lap-bao-cao-danh-gia-tac-dong-moi-truong-cua-du-an-nang-cao-nang-luc-cho-luc-luong-canh-sat-phong-chay-chua-chay-va-cuu-nan-cuu-ho-su-dung-von-vay-oda-nhat-ban',
    'hoat-dong-giam-sat-tai-dinh-cu-tai-du-an-duong-cao-toc-ben-luc-long-thanh',
    'hoat-dong-tap-huan-tai-tieu-du-an-do-thi-tinh-gia-tinh-thanh-hoa',
    'hoat-dong-tham-van-tai-du-an-nang-cap-mang-luoi-giao-thong-tieu-vung-song-me-kong-mo-rong-lan-thu-2-nang-cap-quoc-lo-217-giai-doan-1-tinh-thanh-hoa',
    'khao-sat-kinh-te-xa-hoi-va-de-xuat-chinh-sach-boi-thuong-ho-tro-va-tai-dinh-cu-phuc-vu-thi-cong-tuyen-ham-cua-du-an-tuyen-duong-sat-do-thi-so-3-thanh-pho-ha-noi',
    '3-hinh-thuc-tham-van-danh-gia-tac-dong-moi-truong',
    'thanh-phan-va-so-luong-ho-so-de-nghi-tham-dinh-bao-cao-danh-gia-tac-dong-moi-truong',
    'trinh-tu-cap-giay-phep-moi-truong',
    'trinh-tu-thuc-hien-cac-buoc-nop-ho-so-tham-dinh-bao-cao-danh-gia-tac-dong-moi-truong-dtm',
    'huong-toi-lo-trinh-quoc-gia-ve-giam-thieu-nhua-dung-mot-lan-o-viet-nam-chien-luoc-va-lua-chon-uu-tien',
    'nhung-diem-chinh-bao-cao-quoc-gia-ve-khi-hau-va-phat-trien-cho-viet-nam',
    'du-an-ho-chua-nuoc-thuc-luyen-tinh-phu-tho']
REDIRECTS = {'linh-vuc-hoat-dong': 'dich-vu/', 'danh-sach-du-an-tieu-bieu': 'du-an/',
    'hinh-anh': 'du-an/#hinh-anh', 'en/photos': 'en/projects/#photos',  # field photos page merged into Projects (11/2026)
    'khach-hangnha-tai-tro': 'gioi-thieu/', 'kinh-doanh-dich-vu': 'dich-vu/', 'do-dac-dia-chinh': 'dich-vu/#gis-du-lieu',
    'tu-van-moi-truong': 'dich-vu/#moi-truong-ats', 'tu-van-tai-dinh-cu': 'dich-vu/#xa-hoi-tai-dinh-cu',
    'tu-van-xa-hoi-gioi-dtts': 'dich-vu/#xa-hoi-tai-dinh-cu', 'tu-van-sinh-ke': 'dich-vu/#xa-hoi-tai-dinh-cu',
    'nang-cao-nang-luc': 'dich-vu/#ho-tro-thuc-hien', 'tin-tuc': 'cap-nhat/', 'environmental-and-social-policies': 'lien-ket/',
    **{a: 'cap-nhat/' for a in OLD_ARTICLES}}


def redirect_page(old, new):
    up = '../' * (old.count('/') + 1)  # old URL may sit one level deeper (en/photos)
    return f'''<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><title>LHC Việt Nam</title>
<meta name="robots" content="noindex"><link rel="canonical" href="{SITE}/{new.split('#')[0]}">
<meta http-equiv="refresh" content="0; url={up}{new}"></head>
<body><p><a href="{up}{new}">LHC Việt Nam</a></p></body></html>
'''


def build(out=OUT, include_drafts=False):
    global OUT
    OUT = out
    cname = 'lhcviet.com\n'  # custom domain for GitHub Pages; never drop it (a lost CNAME takes the site down)
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / 'assets').mkdir(parents=True)
    posts = load_posts(include_drafts)
    builders = {'home': home, 'about': about, 'services': services, 'updates': lambda L: updates_page(L, posts),
                'links': links_page, 'projects': projects_page, 'contact': contact_page, 'terms': terms_page}
    for p in posts:
        builders[p['key']] = lambda L, p=p: post_page(p, L)
    if not posts:  # no published article yet: keep the section out of the site
        del builders['updates']
        if 'updates' in NAV:
            NAV.remove('updates')
        if 'updates' in FOOT:
            FOOT.remove('updates')
    urls = []
    for key, fn in builders.items():
        for L in ('vi', 'en'):
            p = path_of(key, L)
            d = OUT / p
            d.mkdir(parents=True, exist_ok=True)
            (d / 'index.html').write_text(fn(L), encoding='utf-8')
            urls.append((key, p))
    for old, new in REDIRECTS.items():
        if not posts and new.startswith('cap-nhat'):
            new = ''
        (OUT / old).mkdir()
        (OUT / old / 'index.html').write_text(redirect_page(old, new), encoding='utf-8')
    (OUT / '404.html').write_text(NOT_FOUND.replace('{CSS_V}', CSS_V), encoding='utf-8')
    shutil.copy(ROOT / 'assets' / 'site.css', OUT / 'assets' / 'site.css')
    shutil.copytree(ROOT / 'assets' / 'photos', OUT / 'assets' / 'photos')
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
    import sys
    if '--drafts' in sys.argv:  # preview with draft posts, never deployed
        build(ROOT / 'preview', include_drafts=True)
    else:
        build()
