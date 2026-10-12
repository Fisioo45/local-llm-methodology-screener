"""Step 1: build the sampling frame from Europe PMC.

Scope: 2025 open-access primary studies that train a deep-learning classifier on
medical images, full text in Europe PMC, licence CC BY or CC0 (so annotations and
short evidence quotes can be redistributed).

Europe PMC's 'core' result pages fail intermittently when paged with a cursor, so:
  (a) list all hits with resultType=lite (reliable), then
  (b) fetch licence / publication type with 'core' in small PMCID batches,
      splitting any batch that fails until the problem record is isolated.
The exact query, run time and every count are written to frame_log.json."""
import json, urllib.request, urllib.parse, datetime, time

MODALITY = ('(ABSTRACT:"MRI" OR ABSTRACT:"magnetic resonance" OR ABSTRACT:"CT" OR ABSTRACT:"computed tomography" '
            'OR ABSTRACT:"X-ray" OR ABSTRACT:"radiograph*" OR ABSTRACT:"histopatholog*" OR ABSTRACT:"whole slide" '
            'OR ABSTRACT:"fundus" OR ABSTRACT:"dermoscop*" OR ABSTRACT:"ultrasound" OR ABSTRACT:"mammogra*" '
            'OR ABSTRACT:"endoscop*" OR ABSTRACT:"OCT" OR ABSTRACT:"optical coherence")')
QUERY = ('(ABSTRACT:"deep learning" OR ABSTRACT:"convolutional neural network" OR ABSTRACT:"vision transformer") '
         'AND (ABSTRACT:"classification" OR ABSTRACT:"classify" OR ABSTRACT:"classifier") '
         f'AND {MODALITY} AND PUB_YEAR:2025 AND OPEN_ACCESS:y AND IN_EPMC:y')
BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?"

def get(params, tries=4):
    for k in range(tries):
        try:
            d = json.load(urllib.request.urlopen(BASE + urllib.parse.urlencode(params), timeout=180))
            if 'resultList' in d: return d
        except Exception:
            pass
        time.sleep(1.5 * (k + 1))
    return None

def list_lite(query):
    out, cursor = [], '*'
    while True:
        d = get({'query': query, 'format': 'json', 'pageSize': 1000, 'resultType': 'lite', 'cursorMark': cursor})
        res = d['resultList']['result'] if d else []
        if not res: return d['hitCount'] if d else None, out
        out += res; hit = d['hitCount']
        if d.get('nextCursorMark') in (None, cursor): return hit, out
        cursor = d['nextCursorMark']

def core_batch(pmcids, failed):
    q = ' OR '.join(f'PMCID:{p}' for p in pmcids)
    d = get({'query': q, 'format': 'json', 'pageSize': 1000, 'resultType': 'core'}, tries=2)
    if d is not None: return d['resultList']['result']
    if len(pmcids) == 1: failed.append(pmcids[0]); return []
    mid = len(pmcids) // 2
    return core_batch(pmcids[:mid], failed) + core_batch(pmcids[mid:], failed)

if __name__ == '__main__':
    hit, lite = list_lite(QUERY)
    ids = sorted({r['pmcid'] for r in lite if r.get('pmcid')})
    failed, core = [], []
    for i in range(0, len(ids), 50):
        core += core_batch(ids[i:i + 50], failed); time.sleep(0.3)
    keep, lic_counts = [], {}
    for r in core:
        lic = (r.get('license') or 'none').lower().strip()
        lic_counts[lic] = lic_counts.get(lic, 0) + 1
        pt = [p.lower() for p in r.get('pubTypeList', {}).get('pubType', [])]
        if lic not in ('cc by', 'cc0'): continue
        if any(w in p for p in pt for w in ('review', 'editorial', 'comment', 'letter', 'erratum', 'retract')): continue
        keep.append({'pmcid': r['pmcid'], 'doi': r.get('doi'), 'title': r.get('title'),
                     'journal': r.get('journalInfo', {}).get('journal', {}).get('title'),
                     'pub_date': r.get('firstPublicationDate'), 'license': lic, 'pub_types': pt})
    keep.sort(key=lambda x: x['pmcid'])
    json.dump(keep, open('data/processed/frame.json', 'w', encoding='utf-8'), indent=1)
    log = {'query': QUERY, 'run_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
           'hit_count': hit, 'listed_lite': len(lite), 'unique_pmcids': len(ids), 'core_records': len(core),
           'core_failed_pmcids': failed, 'licence_counts': lic_counts, 'frame_size_after_filters': len(keep)}
    json.dump(log, open('data/processed/frame_log.json', 'w', encoding='utf-8'), indent=1)
    print({k: v for k, v in log.items() if k != 'query'})
