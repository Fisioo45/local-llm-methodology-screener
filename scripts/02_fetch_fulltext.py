"""Step 2: download full-text JATS XML for every paper in the frame (Europe PMC REST).
Idempotent: skips files already on disk. Logs failures to fetch_log.json."""
import json, os, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/raw_xml'
def fetch(pmcid):
    path = f'{OUT}/{pmcid}.xml'
    if os.path.exists(path) and os.path.getsize(path) > 1000: return pmcid, 'cached'
    url = f'https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML'
    for k in range(3):
        try:
            data = urllib.request.urlopen(url, timeout=120).read()
            if len(data) > 1000:
                open(path, 'wb').write(data); return pmcid, 'ok'
        except Exception as e:
            err = str(e)
        time.sleep(2 * (k + 1))
    return pmcid, 'failed'

if __name__ == '__main__':
    frame = json.load(open('data/processed/frame.json', encoding='utf-8'))
    with ThreadPoolExecutor(max_workers=4) as ex:
        results = list(ex.map(fetch, [r['pmcid'] for r in frame]))
    status = {}
    for _, s in results: status[s] = status.get(s, 0) + 1
    json.dump({'status_counts': status, 'failed': [p for p, s in results if s == 'failed']},
              open('data/processed/fetch_log.json', 'w', encoding='utf-8'), indent=1)
    print(status)
