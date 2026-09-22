#!/usr/bin/env python3
"""Generate editor.html: a local, offline editing surface for content/state.json.

Run: python3 make_editor.py
Then open editor.html in a browser, edit, and press Save to download an updated
state.json. Drop that back over content/state.json and run build.py.

editor.html embeds a snapshot of state.json, so regenerate it after any change to
content/state.json (or use the Load button inside the editor to pull a fresh file in).
Writes two copies: editor.html in the repo root (gitignored, for local editing) and
public/editor.html, which Vercel serves at /editor so the articles can be edited from
a browser anywhere. Both embed the full state.json, including the internal `slot`
blocks that build.py strips from the public article pages.
"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).parent
STATE = (ROOT / 'content' / 'state.json').read_text(encoding='utf-8')

# Reuse the site stylesheet so the editor looks like the published page.
BUILD = (ROOT / 'build.py').read_text(encoding='utf-8')
SITE_CSS = re.search(r'^CSS = """(.*?)"""', BUILD, re.S | re.M).group(1)

EDITOR_CSS = """
body{padding-bottom:0}
.wrap{max-width:52rem}
.bar{position:sticky;top:0;z-index:20;display:flex;flex-wrap:wrap;gap:10px;align-items:center;
padding:12px 0;margin-bottom:6px;background:var(--ground);border-bottom:1px solid var(--rule)}
.bar select,.bar button,.bar label.fake{font-family:var(--f-mono);font-size:11px;letter-spacing:.08em;
text-transform:uppercase;padding:8px 12px;border:1px solid var(--rule-strong);background:var(--surface);
color:var(--ink);border-radius:2px;cursor:pointer}
.bar button.primary{background:var(--accent);border-color:var(--accent);color:#fff}
.bar button:disabled{opacity:.45;cursor:default}
.bar .sp{flex:1}
.bar .stat{font-family:var(--f-mono);font-size:11px;color:var(--muted);letter-spacing:.05em}
.bar .stat b{color:var(--ink);font-weight:500}
.bar .stat.bad{color:var(--uv-vhigh)}
#checks{margin:0 0 18px;padding:10px 14px;border:1px solid var(--rule);background:var(--surface);
font-family:var(--f-mono);font-size:11px;line-height:1.9;color:var(--muted);border-radius:2px}
#checks .ok::before{content:"OK  ";color:var(--uv-low)}
#checks .bad{color:var(--uv-vhigh)}
#checks .bad::before{content:"!!  "}
[contenteditable]{outline:0;border-radius:2px;transition:background .12s,box-shadow .12s}
[contenteditable]:hover{background:color-mix(in srgb,var(--accent) 5%,transparent)}
[contenteditable]:focus{background:color-mix(in srgb,var(--accent) 9%,transparent);
box-shadow:0 0 0 2px color-mix(in srgb,var(--accent) 30%,transparent)}
.blk{position:relative}
.blk .tools{position:absolute;left:-118px;top:2px;display:flex;gap:3px;opacity:0;transition:opacity .12s}
.blk:hover .tools,.blk:focus-within .tools{opacity:1}
.blk .tools button{font-family:var(--f-mono);font-size:10px;padding:3px 6px;border:1px solid var(--rule-strong);
background:var(--surface);color:var(--muted);border-radius:2px;cursor:pointer;line-height:1.4}
.blk .tools button:hover{color:var(--accent);border-color:var(--accent)}
.blk .tag{position:absolute;right:-64px;top:4px;font-family:var(--f-mono);font-size:9.5px;
letter-spacing:.1em;text-transform:uppercase;color:var(--muted);opacity:.5}
.dirty>[contenteditable]{box-shadow:inset 3px 0 0 var(--uv-mod)}
sup.mk{user-select:none;cursor:default;background:var(--accent-soft);padding:0 2px;border-radius:2px}
.locked{border:1px dashed var(--rule-strong);padding:8px;border-radius:2px;position:relative}
.locked::after{content:"FIGURE ARTWORK, NOT EDITABLE HERE";position:absolute;top:-8px;left:10px;
background:var(--ground);padding:0 6px;font-family:var(--f-mono);font-size:9px;letter-spacing:.1em;color:var(--muted)}
h3.sec{font-family:var(--f-mono);font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;
color:var(--accent);margin:46px 0 10px;padding-top:14px;border-top:1px solid var(--rule)}
details.faqrow{border-bottom:1px solid var(--rule);padding:4px 0}
details.faqrow summary{cursor:text;font-weight:600;font-size:1rem;padding:12px 0;list-style:none;
display:flex;justify-content:space-between;gap:14px;align-items:baseline}
details.faqrow summary::-webkit-details-marker{display:none}
details.faqrow summary::after{content:"\\2212";font-family:var(--f-mono);color:var(--accent);font-weight:400}
details.faqrow p{margin:0 0 14px;font-size:.95rem;color:var(--ink-2)}
details.faqrow summary>[contenteditable],details.faqrow>[contenteditable]{flex:1}
ol.refs-list li>[contenteditable]{display:block}
.hint{font-size:.85rem;color:var(--muted);margin:0 0 22px;max-width:60ch}
.hint code{font-family:var(--f-mono);font-size:.9em;background:var(--surface-2);padding:1px 4px;border-radius:2px}
"""

JS = r"""
const STATE = JSON.parse(document.getElementById('state-data').textContent);
let artIdx = STATE.articles.length - 1;
const dirty = new Set();          // paths the user actually touched
const $ = (s, r) => (r || document).querySelector(s);

/* ---------- helpers ---------- */
const esc = s => s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
function markMarkers(html){        // lock citation markers so typing can't break the anchor
  return html.replace(/<sup>(<a href="#r\d+">\d+<\/a>)<\/sup>/g,
                      '<sup class="mk" contenteditable="false">$1</sup>');
}
function unmarkMarkers(html){
  return html.replace(/<sup class="mk" contenteditable="false">/g,'<sup>')
             .replace(/ /g,'&nbsp;');
}
function setByPath(path, value){
  let o = STATE; const p = path.split('.');
  while (p.length > 1) { const k = p.shift(); o = Array.isArray(o) ? o[+k] : o[k]; }
  o[p[0]] = value; dirty.add(path); refresh();
}
function words(a){                  // mirrors words() in build.py exactly
  const t = a.blocks.filter(b => b.type !== 'slot' && b.type !== 'figure')
                    .map(b => b.html || '').join(' ');
  return (t.replace(/<[^>]+>/g, ' ').match(/\S+/g) || []).length;
}

/* ---------- editable field ---------- */
function field(html, path, tag, cls){
  const el = document.createElement(tag || 'div');
  if (cls) el.className = cls;
  el.setAttribute('contenteditable', 'true');
  el.spellcheck = true;
  el.dataset.path = path;
  el.innerHTML = markMarkers(html || '');
  el.addEventListener('input', () => {
    setByPath(path, unmarkMarkers(el.innerHTML));
    el.closest('.blk') && el.closest('.blk').classList.add('dirty');
  });
  el.addEventListener('paste', e => {                 // strip Word/web formatting
    e.preventDefault();
    const t = (e.clipboardData || window.clipboardData).getData('text/plain');
    document.execCommand('insertText', false, t);
  });
  return el;
}
function wrapBlock(inner, label, i){
  const w = document.createElement('div'); w.className = 'blk';
  const tag = document.createElement('span'); tag.className = 'tag'; tag.textContent = label;
  const tools = document.createElement('div'); tools.className = 'tools';
  if (i !== null){
    const add = document.createElement('button'); add.textContent = '+ para'; add.title = 'Add a paragraph below';
    add.onclick = () => { STATE.articles[artIdx].blocks.splice(i+1, 0, {type:'p', html:'New paragraph.'});
                          dirty.add('articles.'+artIdx+'.blocks'); render(); };
    const del = document.createElement('button'); del.textContent = 'delete'; del.title = 'Delete this block';
    del.onclick = () => { if (!confirm('Delete this ' + label + '?')) return;
                          STATE.articles[artIdx].blocks.splice(i, 1);
                          dirty.add('articles.'+artIdx+'.blocks'); render(); };
    const up = document.createElement('button'); up.textContent = '↑';
    up.onclick = () => { if (i === 0) return; const b = STATE.articles[artIdx].blocks;
                         [b[i-1], b[i]] = [b[i], b[i-1]]; dirty.add('articles.'+artIdx+'.blocks'); render(); };
    tools.append(up, add, del);
  }
  w.append(tools, tag, inner);
  return w;
}

/* ---------- render ---------- */
function render(){
  const a = STATE.articles[artIdx], base = 'articles.' + artIdx, body = $('#body');
  body.innerHTML = '';
  const H = (t, c) => { const h = document.createElement('h3'); h.className = 'sec'; h.textContent = t;
                        body.append(h); };

  H('Eyebrow, title and deck');
  body.append(wrapBlock(field(a.eyebrow, base + '.eyebrow', 'p', 'eyebrow'), 'eyebrow', null));
  body.append(wrapBlock(field(a.title, base + '.title', 'h1'), 'title', null));
  body.append(wrapBlock(field(a.sub, base + '.sub', 'p', 'sub'), 'deck', null));

  H('Opening');
  body.append(wrapBlock(field(a.standfirst, base + '.standfirst', 'p', 'standfirst'), 'standfirst', null));

  H('Body');
  a.blocks.forEach((b, i) => {
    const p = base + '.blocks.' + i;
    if (b.type === 'figure'){
      const fig = document.createElement('figure');
      const art = document.createElement('div'); art.className = 'locked'; art.innerHTML = b.svg || '';
      const cap = field(b.html, p + '.html', 'figcaption');
      fig.append(art, cap);
      body.append(wrapBlock(fig, 'figure', i));
    } else if (b.type === 'h2'){
      body.append(wrapBlock(field(b.html, p + '.html', 'h2'), 'h2', i));
    } else if (b.type === 'quote'){
      const q = document.createElement('blockquote');
      q.append(field(b.html, p + '.html', 'p'), field(b.cite || '', p + '.cite', 'cite'));
      body.append(wrapBlock(q, 'quote', i));
    } else if (b.type === 'list'){
      body.append(wrapBlock(field(b.html, p + '.html', 'ul'), 'list', i));
    } else if (b.type === 'table'){
      const d = field(b.html, p + '.html', 'div'); d.classList.add('tablewrap');
      body.append(wrapBlock(d, 'table', i));
    } else if (b.type === 'note'){
      const d = field(b.html, p + '.html', 'div'); d.classList.add('note');
      body.append(wrapBlock(d, 'note', i));
    } else if (b.type === 'image'){
      const fig = document.createElement('figure');
      const im = document.createElement('div'); im.className = 'locked';
      im.textContent = 'image: ' + b.file;
      fig.append(im, field(b.html, p + '.html', 'figcaption'));
      body.append(wrapBlock(fig, 'image', i));
    } else {
      body.append(wrapBlock(field(b.html, p + '.html', 'p'), b.type, i));
    }
  });

  if (a.faq && a.faq.length){
    H('Frequently asked questions');
    a.faq.forEach((f, i) => {
      // same <details>/<summary> accordion the build writes, held open so it stays editable
      const row = document.createElement('details');
      row.className = 'faqrow'; row.open = true;
      const sum = document.createElement('summary');
      sum.append(field(f.q, base + '.faq.' + i + '.q', 'span'));
      sum.addEventListener('click', e => e.preventDefault());   // click to type, not to collapse
      const ans = field(f.a, base + '.faq.' + i + '.a', 'p');
      row.append(sum, ans);
      body.append(wrapBlock(row, 'faq ' + (i+1), null));
    });
  }

  H('References, APA 7th, numbered by first citation');
  const ol = document.createElement('ol'); ol.className = 'refs-list';
  a.refs.forEach((r, i) => {
    const li = document.createElement('li'); li.id = 'r' + r.n;
    li.append(field(r.html, base + '.refs.' + i + '.html', 'div'));
    ol.append(li);
  });
  body.append(ol);
  refresh();
}

/* ---------- live integrity checks ---------- */
function refresh(){
  const a = STATE.articles[artIdx];
  let txt = (a.standfirst || '') + (a.sub || '') + (a.title || '');
  a.blocks.forEach(b => txt += (b.html || '') + (b.cite || ''));
  (a.faq || []).forEach(f => txt += f.q + f.a);
  const seen = []; (txt.match(/#r(\d+)/g) || []).forEach(m => {
    const n = +m.slice(2); if (!seen.includes(n)) seen.push(n); });
  const refs = a.refs.map(r => r.n);
  const orphan = seen.filter(n => !refs.includes(n));
  const uncited = refs.filter(n => !seen.includes(n));
  const ordered = JSON.stringify(seen) === JSON.stringify(refs);
  const plain = txt.replace(/<sup>.*?<\/sup>/g, '').replace(/<[^>]+>/g, ' ');
  const dash = /[—–]/.test(plain) || /&[mn]dash;/.test(txt);
  const rnd = (plain.match(/randomi[sz]/gi) || []).length;
  const w = words(a);

  const L = [];
  L.push(`<div class="${orphan.length ? 'bad' : 'ok'}">Citation markers point at a real reference${orphan.length ? ': missing ' + orphan.join(', ') : ''}</div>`);
  L.push(`<div class="${uncited.length ? 'bad' : 'ok'}">Every reference is cited${uncited.length ? ': uncited ' + uncited.join(', ') : ''}</div>`);
  L.push(`<div class="${ordered ? 'ok' : 'bad'}">References numbered in order of first citation${ordered ? '' : ' &mdash; order is now ' + seen.join(', ')}</div>`);
  L.push(`<div class="${dash ? 'bad' : 'ok'}">No em or en dashes (house style)</div>`);
  L.push(`<div class="${rnd ? 'bad' : 'ok'}">The word "randomised" stays out of the body${rnd ? ': ' + rnd + ' found' : ''}</div>`);
  L.push(`<div class="ok">Word count ${w.toLocaleString()} &nbsp;&middot;&nbsp; ${a.refs.length} references &nbsp;&middot;&nbsp; ${dirty.size} field(s) edited</div>`);
  $('#checks').innerHTML = L.join('');
  $('#wc').innerHTML = '<b>' + w.toLocaleString() + '</b> words';
  $('#save').disabled = dirty.size === 0;
  $('#save').textContent = dirty.size ? 'Save state.json (' + dirty.size + ')' : 'Save state.json';
}

/* ---------- toolbar ---------- */
function boot(){
  const sel = $('#pick');
  STATE.articles.forEach((a, i) => {
    const o = document.createElement('option'); o.value = i;
    o.textContent = a.title.replace(/<[^>]+>/g, '');
    sel.append(o);
  });
  sel.value = artIdx;
  sel.onchange = () => { artIdx = +sel.value; render(); };

  $('#save').onclick = () => {
    const blob = new Blob([JSON.stringify(STATE, null, 2) + '\n'], {type: 'application/json'});
    const u = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = u; a.download = 'state.json'; a.click();
    URL.revokeObjectURL(u);
  };
  $('#load').onchange = e => {
    const f = e.target.files[0]; if (!f) return;
    const r = new FileReader();
    r.onload = () => { try {
        const j = JSON.parse(r.result);
        STATE.articles = j.articles; Object.assign(STATE, j);
        dirty.clear(); artIdx = Math.min(artIdx, STATE.articles.length - 1);
        sel.innerHTML = ''; STATE.articles.forEach((a, i) => {
          const o = document.createElement('option'); o.value = i;
          o.textContent = a.title.replace(/<[^>]+>/g, ''); sel.append(o); });
        sel.value = artIdx; render();
      } catch (err) { alert('Could not read that file: ' + err.message); } };
    r.readAsText(f);
  };
  $('#theme').onclick = () => {
    const d = document.documentElement.getAttribute('data-theme') === 'dark';
    document.documentElement.setAttribute('data-theme', d ? 'light' : 'dark');
  };
  window.addEventListener('beforeunload', e => { if (dirty.size) { e.preventDefault(); e.returnValue = ''; } });
  render();
}
boot();
"""

HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Heliocare Editorial &mdash; editor</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&amp;family=IBM+Plex+Mono:wght@400;500&amp;family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&amp;display=swap">
<style>__SITE_CSS____EDITOR_CSS__</style>
</head>
<body>
<div class="wrap">
  <div class="bar">
    <select id="pick" title="Which article to edit"></select>
    <button id="save" class="primary" disabled>Save state.json</button>
    <label class="fake" for="load">Load a state.json</label>
    <input id="load" type="file" accept="application/json,.json" hidden>
    <button id="theme">Light / dark</button>
    <span class="sp"></span>
    <span class="stat" id="wc"></span>
  </div>
  <p class="hint">Click any heading, paragraph, quote, caption, list, table cell, FAQ or reference and type.
  Citation markers are locked so ordinary typing cannot break them, and the panel below re-checks the
  article every keystroke. Edited fields get an amber bar; untouched ones are written back byte for byte,
  so your diff stays small. When you are done press <b>Save state.json</b>, replace
  <code>content/state.json</code> with the downloaded file, then run <code>python3 build.py</code>.
  Figure artwork is shown but not editable here; ask me to change a figure and I will redraw the SVG.</p>
  <div id="checks"></div>
  <div id="body"></div>
</div>
<script id="state-data" type="application/json">__STATE__</script>
<script>__JS__</script>
</body>
</html>
"""

out = (HTML.replace('__SITE_CSS__', SITE_CSS)
           .replace('__EDITOR_CSS__', EDITOR_CSS)
           .replace('__STATE__', STATE.replace('</script>', '<\\/script>'))
           .replace('__JS__', JS))
(ROOT / 'editor.html').write_text(out, encoding='utf-8')
print('wrote editor.html (%.0f KB) from content/state.json' % (len(out) / 1024))

# Also write a deployed copy. Vercel serves public/, so this puts the editor at
# /editor on the draft mirror. Note that it embeds the whole of state.json,
# including the internal `slot` blocks that build.py strips from the public pages.
PUBLIC = ROOT / 'public'
PUBLIC.mkdir(parents=True, exist_ok=True)
(PUBLIC / 'editor.html').write_text(out, encoding='utf-8')
print('wrote public/editor.html (deployed copy, served at /editor)')
print('open it in a browser, edit, press Save, then replace content/state.json and run build.py')
