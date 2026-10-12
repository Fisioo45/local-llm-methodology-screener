"""Step 3: parse JATS XML into a clean per-paper JSON record.

Keeps: title, abstract, every body section (with its heading path), table and
figure captions, table cell text (split sizes often live in tables), and back
matter (data/code availability, supplementary material). References are dropped.
Also records length statistics used to plan the LLM context budget.
v1.1 (after pilot): also keeps footnote groups/notes inside sections and front-matter
footnotes, where some journals put data/code availability statements, and every
abstract block (author highlights / key points are separate <abstract> elements)."""
import json, glob, os, re
import xml.etree.ElementTree as ET

def txt(el):
    if el is None: return ''
    s = ''.join(el.itertext())
    return re.sub(r'\s+', ' ', s).strip()

METHOD_PAT = re.compile(r'method|material|dataset|data set|data collection|experiment|implementation|'
                        r'training|evaluation|model|preprocess|pre-process|study design|participants', re.I)

def walk_sections(sec, path, out):
    title = txt(sec.find('title'))
    p = path + [title] if title else path
    own = []
    for ch in sec:
        tag = ch.tag.split('}')[-1]
        if tag in ('p', 'list', 'disp-formula', 'def-list', 'statement', 'fn-group', 'fn', 'boxed-text', 'notes'):
            own.append(txt(ch))   # fn-group/notes inside sections often hold data/code availability statements
        elif tag in ('table-wrap', 'fig'):
            cap = txt(ch.find('.//caption')); lab = txt(ch.find('label'))
            body = ''
            if tag == 'table-wrap' and ch.find('.//table') is not None:   # cells ' | ', rows ' ; '
                body = ' ; '.join(' | '.join(txt(c) for c in tr if c.tag.split('}')[-1] in ('td', 'th'))
                                  for tr in ch.find('.//table').iter() if tr.tag.split('}')[-1] == 'tr')
            foot = txt(ch.find('table-wrap-foot')) if tag == 'table-wrap' else ''   # table footnotes
            own.append(f'[{lab or tag}] {cap} {body} {foot}'.strip())
    if any(own):
        out.append({'path': ' > '.join(p), 'text': '\n'.join(x for x in own if x)})
    for ch in sec:
        if ch.tag.split('}')[-1] == 'sec':
            walk_sections(ch, p, out)

def parse(path):
    root = ET.parse(path).getroot()
    front, body, back = root.find('front'), root.find('body'), root.find('back')
    rec = {'pmcid': os.path.basename(path)[:-4],
           'title': txt(root.find('.//article-meta/title-group/article-title')),
           'abstract': '\n'.join(txt(a) for a in root.findall('.//article-meta/abstract')),  # incl. highlights/key points
           'article_type': root.get('article-type', ''), 'sections': [], 'back': []}
    if body is not None:
        loose = [txt(ch) for ch in body if ch.tag.split('}')[-1] == 'p']
        if any(loose): rec['sections'].append({'path': '(body)', 'text': '\n'.join(loose)})
        for sec in body.findall('sec'): walk_sections(sec, [], rec['sections'])
    floats = root.find('floats-group')          # some journals keep all tables/figures here
    if floats is not None:
        walk_sections(floats, ['Tables and figures'], rec['sections'])
    if back is not None:
        for ch in back:
            tag = ch.tag.split('}')[-1]
            if tag in ('ref-list',): continue
            t = txt(ch)
            if t: rec['back'].append({'tag': tag, 'title': txt(ch.find('title')), 'text': t[:4000]})
    # some journals put data-availability statements in front matter notes
    if front is not None:
        for n in front.iter():
            if n.tag.split('}')[-1] in ('notes', 'custom-meta-group', 'author-notes', 'fn') and re.search(r'availab', txt(n), re.I):
                rec['back'].append({'tag': 'front-note', 'title': '', 'text': txt(n)[:4000]})
    words_all = sum(len(s['text'].split()) for s in rec['sections']) + sum(len(b['text'].split()) for b in rec['back'])
    words_m = sum(len(s['text'].split()) for s in rec['sections'] if METHOD_PAT.search(s['path']))
    rec['stats'] = {'n_sections': len(rec['sections']), 'words_total': words_all, 'words_methodlike': words_m,
                    'approx_tokens_total': int(words_all * 1.35), 'has_methodlike_heading': words_m > 0}
    return rec

if __name__ == '__main__':
    os.makedirs('data/processed/papers', exist_ok=True)
    stats = []
    for f in sorted(glob.glob('data/raw_xml/*.xml')):
        try:
            r = parse(f)
        except ET.ParseError as e:
            print('parse error', f, e); continue
        json.dump(r, open(f"data/processed/papers/{r['pmcid']}.json", 'w', encoding='utf-8'))
        stats.append({'pmcid': r['pmcid'], 'article_type': r['article_type'], **r['stats']})
    json.dump(stats, open('data/processed/paper_stats.json', 'w', encoding='utf-8'), indent=0)
    import statistics as st
    tok = sorted(s['approx_tokens_total'] for s in stats); mt = sorted(s['words_methodlike'] * 1.35 for s in stats)
    q = lambda a, p: a[int(p * (len(a) - 1))]
    print('papers', len(stats), '| article types', {t: sum(1 for s in stats if s['article_type'] == t) for t in set(s['article_type'] for s in stats)})
    print('full-text tokens  p10/p50/p90/max:', q(tok, .1), q(tok, .5), q(tok, .9), tok[-1])
    print('method-like tokens p10/p50/p90/max:', int(q(mt, .1)), int(q(mt, .5)), int(q(mt, .9)), int(mt[-1]))
    print('no method-like heading:', sum(1 for s in stats if not s['has_methodlike_heading']))
