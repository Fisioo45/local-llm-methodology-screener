"""Step 4: fix the annotation order.

All frame papers are shuffled once with a documented seed. The annotator works
top-down: the first 20 ELIGIBLE papers form the pilot, eligible papers 21-40 the
rest of the development set, eligible 41-200 the held-out test set. Ineligible
papers are simply skipped, so no set is ever hand-picked.
auto_hint is a heuristic prompt to check eligibility, never a decision."""
import json, random, re, csv

SEED = 20260923
frame = {r['pmcid']: r for r in json.load(open('data/processed/frame.json', encoding='utf-8'))}
stats = {s['pmcid']: s for s in json.load(open('data/processed/paper_stats.json', encoding='utf-8'))}
ids = sorted(frame)
random.Random(SEED).shuffle(ids)

rows = []
for i, p in enumerate(ids, 1):
    paper = json.load(open(f'data/processed/papers/{p}.json', encoding='utf-8'))
    t, a = paper['title'].lower(), paper['abstract'].lower()
    hints = []
    if paper['article_type'] != 'research-article': hints.append(f"article type '{paper['article_type']}'")
    if re.search(r'\b(review|survey|meta-analys|protocol)\b', t): hints.append('title suggests review/protocol')
    if 'segment' in t + a and not re.search(r'classif', t + a): hints.append('may be segmentation-only')
    if not re.search(r'train|fine-tun|test set|testing set|validation', a + ' ' + ' '.join(s['text'][:3000] for s in paper['sections'][:6]).lower()):
        hints.append('no training/test wording found')
    rows.append({'order_no': i, 'pmcid': p, 'doi': frame[p]['doi'] or '', 'title': paper['title'],
                 'journal': frame[p]['journal'] or '', 'pub_date': frame[p]['pub_date'] or '',
                 'approx_tokens': stats[p]['approx_tokens_total'], 'auto_hint': '; '.join(hints)})

with open('data/processed/annotation_order.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print('rows', len(rows), '| with hints', sum(1 for r in rows if r['auto_hint']))
print('top journals:', sorted(((sum(1 for r in rows if r['journal']==j), j) for j in set(r['journal'] for r in rows)), reverse=True)[:8])
