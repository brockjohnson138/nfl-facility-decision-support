"""Download public nflverse snapshots; preserve provenance and never fabricate missing years."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib, json, urllib.request, urllib.error
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw'
BASE='https://github.com/nflverse/nflverse-data/releases/download'
def download(spec):
 name,url=spec; p=RAW/name
 entry={'file':name,'url':url,'retrieved_utc':datetime.now(timezone.utc).isoformat()}
 try:
  if not p.exists():
   req=urllib.request.Request(url,headers={'User-Agent':'NFL-Facility-Research/1.0'})
   with urllib.request.urlopen(req,timeout=60) as response: b=response.read()
   if len(b)<100:raise ValueError('Empty or unexpectedly small response')
   p.write_bytes(b)
  b=p.read_bytes()
  entry.update(status='downloaded',bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
 except Exception as e:entry.update(status='unavailable',error=str(e))
 print(name,entry['status'],flush=True)
 return entry

def main():
 RAW.mkdir(parents=True,exist_ok=True)
 specs=[(f'injuries_{y}.csv',f'{BASE}/injuries/injuries_{y}.csv') for y in range(2015,2026)]
 specs += [(f'roster_weekly_{y}.parquet',f'{BASE}/weekly_rosters/roster_weekly_{y}.parquet') for y in range(2016,2026)]
 specs += [('games.csv','https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv'),('historical_contracts.parquet',f'{BASE}/contracts/historical_contracts.parquet')]
 with ThreadPoolExecutor(max_workers=4) as pool:entries=list(pool.map(download,specs))
 path=ROOT/'data/source_manifest.json'
 prior=json.loads(path.read_text()) if path.exists() else []
 known={e['file']:e for e in prior}
 for e in entries:
  if e['file'] in known and e.get('sha256')==known[e['file']].get('sha256'):e['retrieved_utc']=known[e['file']]['retrieved_utc']
  known[e['file']]=e
 path.write_text(json.dumps(list(known.values()),indent=2))
if __name__=='__main__':main()
