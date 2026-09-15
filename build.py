#!/usr/bin/env python3
"""Build the static site in public/ from content/state.json.

Run: python3 build.py
Vercel serves public/ (see vercel.json). No dependencies.
"""
import json, os, re, html, pathlib

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / 'public'
STATE = json.loads((ROOT / 'content' / 'state.json').read_text(encoding='utf-8'))

# Blocks that are internal production notes and never go on the public mirror.
INTERNAL_BLOCK_TYPES = {'slot'}

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
         'family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&amp;'
         'family=IBM+Plex+Mono:wght@400;500&amp;'
         'family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&amp;display=swap">')

CSS = """
:root{--ground:#F7F6FA;--surface:#FFF;--surface-2:#F1EFF6;--ink:#17141F;--ink-2:#3B3548;
--muted:#6B647A;--rule:#E1DEE9;--rule-strong:#CBC6D8;--accent:#6B3FA0;--accent-soft:#EEE7F7;
--uv-low:#2E9E5B;--uv-mod:#D9A400;--uv-high:#DE6B1F;--uv-vhigh:#C33A2E;--uv-extreme:#7B3FA8;
--skin-1:#F2D9C4;--skin-2:#E0BFA3;--skin-3:#C99C7C;
--f-display:"Newsreader","Iowan Old Style",Georgia,serif;
--f-body:"IBM Plex Sans","Helvetica Neue",Arial,sans-serif;
--f-mono:"IBM Plex Mono","SF Mono",Menlo,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
--ground:#131120;--surface:#1C192B;--surface-2:#242034;--ink:#EFECF6;--ink-2:#CFC9DD;
--muted:#A198B6;--rule:#332E47;--rule-strong:#463F5E;--accent:#B694EC;--accent-soft:#2A2340;
--uv-low:#4FC183;--uv-mod:#E8BE3E;--uv-high:#FF9152;--uv-vhigh:#F2695C;--uv-extreme:#B98BE0;
--skin-1:#4A3A31;--skin-2:#5C4739;--skin-3:#6E5443}}
:root[data-theme="dark"]{--ground:#131120;--surface:#1C192B;--surface-2:#242034;--ink:#EFECF6;
--ink-2:#CFC9DD;--muted:#A198B6;--rule:#332E47;--rule-strong:#463F5E;--accent:#B694EC;
--accent-soft:#2A2340;--uv-low:#4FC183;--uv-mod:#E8BE3E;--uv-high:#FF9152;--uv-vhigh:#F2695C;
--uv-extreme:#B98BE0;--skin-1:#4A3A31;--skin-2:#5C4739;--skin-3:#6E5443}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--f-body);
font-size:17px;line-height:1.68;-webkit-font-smoothing:antialiased}
.wrap{max-width:48rem;margin:0 auto;padding:0 26px 110px}
a{color:var(--accent);text-decoration:none;border-bottom:1px solid color-mix(in srgb,var(--accent) 35%,transparent)}
a:hover{border-bottom-color:var(--accent)}
:focus-visible{outline:2px solid var(--accent);outline-offset:3px;border-radius:2px}
.top{display:flex;align-items:baseline;gap:14px;padding:26px 0 0;font-family:var(--f-mono);
font-size:11px;letter-spacing:.13em;text-transform:uppercase;color:var(--muted)}
.top a{border-bottom:0;color:var(--muted)}.top a:hover{color:var(--accent)}
.draft{margin:22px 0 0;padding:10px 14px;background:var(--accent-soft);color:var(--accent);
font-size:.82rem;border-radius:2px}
header.hd{padding:34px 0 30px}
.eyebrow{font-family:var(--f-mono);font-size:11.5px;letter-spacing:.14em;text-transform:uppercase;
color:var(--accent);margin:0 0 18px}
h1{font-family:var(--f-display);font-weight:500;font-size:clamp(2.2rem,5.2vw,3.4rem);
line-height:1.06;letter-spacing:-.022em;margin:0 0 16px;text-wrap:balance;max-width:22ch}
.sub{font-family:var(--f-display);font-style:italic;font-size:clamp(1.1rem,2.3vw,1.35rem);
line-height:1.42;color:var(--ink-2);margin:0;max-width:46ch}
.meta{display:flex;flex-wrap:wrap;gap:6px 20px;margin-top:28px;padding-top:16px;
border-top:1px solid var(--rule);font-family:var(--f-mono);font-size:11.5px;
letter-spacing:.05em;color:var(--muted);text-transform:uppercase}
article{max-width:34.5rem}
article>p{margin:0 0 20px}
.standfirst{font-size:1.1rem;color:var(--ink-2)}
h2{font-family:var(--f-display);font-weight:500;font-size:1.66rem;line-height:1.2;
letter-spacing:-.015em;margin:46px 0 14px;text-wrap:balance}
sup{font-family:var(--f-mono);font-size:.62em;font-weight:500;vertical-align:super;line-height:0}
sup a{border-bottom:0;padding:0 1px}
strong{font-weight:600;color:var(--ink)}
blockquote{margin:32px 0;padding:0 0 0 20px;border-left:2px solid var(--accent);
font-family:var(--f-display);font-size:1.2rem;line-height:1.42;color:var(--ink);max-width:42ch}
blockquote p{margin:0 0 8px}
blockquote cite{display:block;font-family:var(--f-mono);font-style:normal;font-size:.7rem;
letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-top:10px;line-height:1.5}
figure{margin:36px 0;max-width:44rem}
figure svg{display:block;width:100%;height:auto;background:var(--surface);
border:1px solid var(--rule);border-radius:2px}
figure img{display:block;width:100%;height:auto;border-radius:2px;background:var(--surface-2)}
figcaption{font-size:.85rem;color:var(--muted);margin-top:10px;line-height:1.5}
figcaption b{font-family:var(--f-mono);font-size:.78rem;letter-spacing:.08em;
text-transform:uppercase;color:var(--accent);font-weight:500}
.note{margin:28px 0;padding:16px 18px;background:var(--surface);border:1px solid var(--rule);max-width:42rem}
.note h4{font-family:var(--f-mono);font-size:10px;letter-spacing:.13em;text-transform:uppercase;
color:var(--accent);margin:0 0 8px;font-weight:500}
.note p{margin:0 0 10px;font-size:.94rem;color:var(--ink-2)}.note p:last-child{margin:0}
.tablewrap{overflow-x:auto;border:1px solid var(--rule);background:var(--surface);margin:30px 0;max-width:44rem}
table{border-collapse:collapse;width:100%;min-width:520px;font-size:.87rem}
th,td{text-align:left;padding:10px 13px;border-bottom:1px solid var(--rule);vertical-align:top}
thead th{font-family:var(--f-mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;
color:var(--muted);font-weight:500;background:var(--surface-2)}
tbody tr:last-child td{border-bottom:0}
ul{padding-left:1.15em}ul li{margin-bottom:9px}
.faq{margin-top:46px;max-width:34.5rem}
.faq h2{margin-top:0}
details{border-bottom:1px solid var(--rule);padding:4px 0}
summary{cursor:pointer;font-weight:600;font-size:1rem;padding:12px 0;list-style:none;
display:flex;justify-content:space-between;gap:14px;align-items:baseline}
summary::-webkit-details-marker{display:none}
summary::after{content:"+";font-family:var(--f-mono);color:var(--accent);font-weight:400}
details[open] summary::after{content:"\\2212"}
details p{margin:0 0 14px;font-size:.95rem;color:var(--ink-2)}
.refs{margin-top:56px;padding-top:24px;border-top:2px solid var(--ink);max-width:45rem}
.refs h2{font-family:var(--f-mono);font-size:11px;letter-spacing:.13em;text-transform:uppercase;
color:var(--muted);margin:0 0 6px;font-weight:500}
.refs .apa{font-size:.8rem;color:var(--muted);margin:0 0 18px;max-width:52ch}
ol.refs-list{margin:0;padding-left:0;list-style:none;counter-reset:ref;
display:flex;flex-direction:column;gap:12px}
ol.refs-list li{counter-increment:ref;font-size:.82rem;line-height:1.55;color:var(--ink-2);
padding-left:2.4em;text-indent:-1.2em;overflow-wrap:anywhere}
ol.refs-list a{word-break:break-all}
ol.refs-list li::before{content:counter(ref) ". ";font-family:var(--f-mono);color:var(--accent)}
ol.refs-list li:target{background:var(--accent-soft);border-radius:2px}
.cards{display:flex;flex-direction:column;gap:2px;margin-top:34px;background:var(--rule);
border:1px solid var(--rule)}
.card{display:block;background:var(--ground);padding:24px 26px;border-bottom:0}
.card:hover{background:var(--surface)}
.card h2{font-family:var(--f-display);font-size:1.5rem;font-weight:500;margin:0 0 8px;
letter-spacing:-.015em;line-height:1.2;color:var(--ink)}
.card p{margin:0 0 12px;color:var(--ink-2);font-size:.97rem;max-width:52ch}
.card .cm{font-family:var(--f-mono);font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
footer{margin-top:64px;padding-top:20px;border-top:1px solid var(--rule);
font-size:.82rem;color:var(--muted);max-width:45rem}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
"""


def strip_tags(s):
    return re.sub(r'<[^>]+>', ' ', s)


def words(a):
    txt = ' '.join(b.get('html', '') for b in a['blocks']
                   if b['type'] not in INTERNAL_BLOCK_TYPES and b['type'] != 'figure')
    return len(strip_tags(txt).split())


def page(title, body, desc='', canonical=''):
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<meta name="robots" content="noindex, nofollow">\n'
            + ('<meta name="description" content="%s">\n' % html.escape(desc) if desc else '')
            + '<title>%s</title>\n' % html.escape(title)
            + FONTS + '\n<style>' + CSS + '</style>\n</head>\n<body>\n<div class="wrap">\n'
            + body + '\n</div>\n</body>\n</html>\n')


def render_blocks(a):
    out = []
    for b in a['blocks']:
        t = b['type']
        if t in INTERNAL_BLOCK_TYPES:
            continue
        if t == 'h2':
            out.append('<h2>%s</h2>' % b['html'])
        elif t == 'quote':
            out.append('<blockquote><p>%s</p>%s</blockquote>'
                       % (b['html'], '<cite>%s</cite>' % b['cite'] if b.get('cite') else ''))
        elif t == 'figure':
            out.append('<figure>%s<figcaption>%s</figcaption></figure>' % (b.get('svg', ''), b['html']))
        elif t == 'image':
            out.append(
                '<figure><img src="/images/%s" alt="%s" width="1400" height="788" loading="lazy" '
                'decoding="async"><figcaption>%s</figcaption></figure>'
                % (b['file'], html.escape(b.get('alt', '')), b['html']))
        elif t == 'table':
            out.append('<div class="tablewrap">%s</div>' % b['html'])
        elif t == 'note':
            out.append('<div class="note">%s</div>' % b['html'])
        elif t == 'list':
            out.append('<ul>%s</ul>' % b['html'])
        else:
            out.append('<p>%s</p>' % b['html'])
    return '\n'.join(out)


def render_article(a):
    b = ['<div class="top"><a href="/">&larr; All articles</a></div>']
    b.append('<div class="draft">Draft. Not yet bylined, medically reviewed or illustrated. '
             'Not for publication.</div>')
    b.append('<header class="hd"><p class="eyebrow">%s</p><h1>%s</h1><p class="sub">%s</p>'
             '<div class="meta"><span>%s</span><span>%s words</span>'
             '<span>%d references</span></div></header>'
             % (a['eyebrow'], a['title'], a['sub'], a['date'], f"{words(a):,}", len(a['refs'])))
    b.append('<article>')
    if a.get('standfirst'):
        b.append('<p class="standfirst">%s</p>' % a['standfirst'])
    b.append(render_blocks(a))
    b.append('</article>')
    if a.get('faq'):
        b.append('<div class="faq"><h2>Frequently asked questions</h2>')
        for f in a['faq']:
            b.append('<details><summary>%s</summary><p>%s</p></details>' % (f['q'], f['a']))
        b.append('</div>')
    if a.get('refs'):
        b.append('<div class="refs"><h2>References</h2>'
                 '<p class="apa">Formatted to APA 7th edition and numbered in order of first '
                 'citation, so the markers in the text resolve directly.</p><ol class="refs-list">')
        for r in a['refs']:
            b.append('<li id="r%d">%s</li>' % (r['n'], r['html']))
        b.append('</ol></div>')
    b.append('<footer>Internal draft mirror. Sunscreens are regulated in Singapore as cosmetic '
             'products under the ASEAN Cosmetic Directive; oral supplements are regulated as '
             'health supplements. Neither may carry claims to treat, prevent or cure disease.</footer>')
    return page(strip_tags(a['title']).strip(), '\n'.join(b), desc=strip_tags(a['sub']).strip())


def render_index():
    b = ['<header class="hd"><p class="eyebrow">Heliocare editorial</p>'
         '<h1>Photoprotection articles</h1>'
         '<p class="sub">Evidence-led photoprotection writing for the Singapore market. '
         'Every statistic carries a named source.</p></header>']
    b.append('<div class="draft">Every piece here is a draft: not yet bylined, medically reviewed '
             'or illustrated. Search engines are blocked from indexing this site.</div>')
    b.append('<div class="cards">')
    for a in STATE['articles']:
        b.append('<a class="card" href="/%s"><h2>%s</h2><p>%s</p>'
                 '<div class="cm">%s words &middot; %d references &middot; %s</div></a>'
                 % (a['id'], a['title'], strip_tags(a['sub']).strip(),
                    f"{words(a):,}", len(a['refs']), a['date']))
    b.append('</div>')
    b.append('<footer>Internal draft mirror, generated from content/state.json. '
             'Not a publishing destination.</footer>')
    return page('Heliocare Editorial', '\n'.join(b))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'index.html').write_text(render_index(), encoding='utf-8')
    for a in STATE['articles']:
        (OUT / (a['id'] + '.html')).write_text(render_article(a), encoding='utf-8')
    (OUT / 'robots.txt').write_text('User-agent: *\nDisallow: /\n', encoding='utf-8')
    print('built %d pages into %s' % (len(STATE['articles']) + 1, OUT))
    for a in STATE['articles']:
        print('  /%-22s %5s words  %2d refs' % (a['id'], f"{words(a):,}", len(a['refs'])))


if __name__ == '__main__':
    main()
