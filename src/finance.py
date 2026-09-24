"""Historical compensation allocation is descriptive, never a cash saving or injury cost."""
from pathlib import Path
import json
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'data/processed'
def prepare_finance():
 c=pd.read_parquet(ROOT/'data/raw/historical_contracts.parquet')
 rows=[]
 for item in c.itertuples():
  if not isinstance(item.gsis_id,str):continue
  if item.season_history is None:continue
  for rec in item.season_history:
   if str(rec.get('year','')).isdigit() and 2016<=int(rec['year'])<=2025 and rec.get('team')=='49ers':
    rows.append({'gsis_id':item.gsis_id,'season':int(rec['year']),'team':'SF','player':item.player,'cash_paid_m':rec.get('cash_paid'),'cap_number_m':rec.get('cap_number')})
 annual=pd.DataFrame(rows).drop_duplicates(['gsis_id','season','team','cash_paid_m','cap_number_m'])
 key=['gsis_id','season','team']
 conflict=annual.duplicated(key,keep=False)
 annual[conflict].to_csv(P/'contract_conflicts.csv',index=False)
 clean=annual[~conflict].copy()
 clean.to_csv(P/'sf_contract_seasons.csv',index=False)
 inj=pd.read_csv(P/'player_reports.csv')
 inj=inj[inj.team.eq('SF')&inj.out.eq(1)]
 joined=inj.merge(clean,on=key,how='left',validate='many_to_one')
 games=pd.read_csv(P/'team_seasons.csv').query("team == 'SF'")[['season','games']]
 joined=joined.merge(games,on='season',validate='many_to_one')
 joined['cash_allocation_m']=joined.cash_paid_m/joined.games
 joined['cap_allocation_m']=joined.cap_number_m/joined.games
 joined.to_csv(P/'sf_out_compensation.csv',index=False)
 summary=joined.groupby('season').agg(out_designations=('out','size'),matched_cash_designations=('cash_paid_m','count'),cash_allocation_m=('cash_allocation_m',lambda x:x.sum(min_count=1)),cap_allocation_m=('cap_allocation_m',lambda x:x.sum(min_count=1))).reset_index()
 summary['cash_match_rate']=summary.matched_cash_designations/summary.out_designations
 summary.to_csv(P/'sf_compensation_summary.csv',index=False)
 audit={'raw_contract_rows':len(c),'unique_sf_player_season_candidates':len(annual),'conflicting_candidate_rows_excluded':int(conflict.sum()),'unique_sf_player_seasons':len(clean),'out_designations':len(joined),'cash_match_rate':float(joined.cash_paid_m.notna().mean()),'definition':'Annual cash/cap allocation divided by scheduled team games, summed across Out designations. Does not measure injury-attributable loss, avoidable salary, player value, or relocation benefit. Current historical snapshot can contain revisions. Conflicting player-year values excluded; no name-only matching.'}
 (P/'finance_audit.json').write_text(json.dumps(audit,indent=2))
 return summary
if __name__=='__main__':print(prepare_finance().to_string(index=False))
