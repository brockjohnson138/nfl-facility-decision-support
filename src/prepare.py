"""Auditable player-report and team-game panels. Counts are NOT injury incidence."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw'; PROCESSED=ROOT/'data/processed'
KEY=['season','team','week']
ALIASES={'OAK':'LV','SD':'LAC','STL':'LA','LAR':'LA','JAC':'JAX','WSH':'WAS'}
def teams(s):return s.replace(ALIASES)
def build_features(panel):
 p=panel.sort_values(['team','season','week']).copy()
 # Reset lags each season: no offseason is treated as a normal week.
 group=p.groupby(['team','season'],sort=False)
 for c in ['out_count','listed_count','reserve_count','mean_roster_age']:
  p[f'{c}_lag1']=group[c].shift(1)
  p[f'{c}_lag3']=group[c].transform(lambda x:x.shift(1).rolling(3,min_periods=1).mean())
 p['score_margin_lag3']=group.score_margin.transform(lambda x:x.shift(1).rolling(3,min_periods=1).mean())
 p['missing_previous_report']=p.out_count_lag1.isna().astype(int)
 return p

def prepare():
 PROCESSED.mkdir(parents=True,exist_ok=True)
 games=pd.read_csv(RAW/'games.csv')
 games=games[games.season.between(2016,2025)&games.game_type.eq('REG')&games.home_score.notna()&games.away_score.notna()].copy()
 assert games.game_id.is_unique
 frames=[]
 for side,opp in [('home','away'),('away','home')]:
  f=games[['game_id','season','week','gameday','surface','roof','location']].copy()
  f['team']=teams(games[f'{side}_team']);f['opponent']=teams(games[f'{opp}_team'])
  f['home']=int(side=='home');f['rest']=games[f'{side}_rest']
  f['score_margin']=games[f'{side}_score']-games[f'{opp}_score']
  f['win']=np.where(f.score_margin==0,.5,(f.score_margin>0).astype(float))
  frames.append(f)
 panel=pd.concat(frames,ignore_index=True)
 assert not panel.duplicated(KEY).any()
 injury=pd.concat([pd.read_csv(RAW/f'injuries_{y}.csv') for y in range(2016,2026)],ignore_index=True)
 injury=injury[injury.game_type.eq('REG')].copy();raw_n=len(injury)
 injury.team=teams(injury.team)
 injury['player_key']=injury.gsis_id.fillna('NAME:'+injury.full_name.fillna('UNKNOWN'))
 injury['modified']=pd.to_datetime(injury.date_modified,errors='coerce',utc=True)
 injury=injury.sort_values('modified',na_position='first').drop_duplicates(KEY+['player_key'],keep='last')
 injury['out']=injury.report_status.fillna('').str.lower().eq('out').astype(int)
 injury['doubtful']=injury.report_status.fillna('').str.lower().eq('doubtful').astype(int)
 desc=injury[['report_primary_injury','report_secondary_injury','practice_primary_injury','practice_secondary_injury']].fillna('').agg(' | '.join,axis=1).str.lower()
 # Broad anatomical proxy; knee/ankle reports are not confirmed ligament diagnoses.
 injury['musculoskeletal_proxy']=desc.str.contains(r'hamstring|groin|calf|achilles|knee|ankle|foot|toe|quad|thigh|hip|shoulder|elbow|wrist|hand|finger|back|neck|pectoral|bicep|tricep|oblique|rib|abdomen',regex=True).astype(int)
 injury['musculoskeletal_out']=injury['out']*injury.musculoskeletal_proxy
 injury['illness_or_personal']=desc.str.contains(r'illness|covid|personal|rest|not injury').astype(int)
 injury['out_excluding_noninjury']=injury['out']*(1-injury.illness_or_personal)
 injury=injury.merge(panel[KEY+['game_id','gameday']],on=KEY,how='left',validate='many_to_one')
 unmatched=injury[injury.game_id.isna()];unmatched.to_csv(PROCESSED/'unmatched_reports.csv',index=False)
 injury=injury[injury.game_id.notna()].copy()
 injury.to_csv(PROCESSED/'player_reports.csv',index=False)
 agg=injury.groupby(KEY).agg(listed_count=('player_key','size'),out_count=('out','sum'),doubtful_count=('doubtful','sum'),musculoskeletal_out=('musculoskeletal_out','sum'),out_excluding_noninjury=('out_excluding_noninjury','sum')).reset_index()
 panel=panel.merge(agg,on=KEY,how='left',validate='one_to_one')
 # Entirely absent team reports are unknown, never silently set to zero.
 panel['report_observed']=panel.listed_count.notna()
 coverage=panel.groupby(['season','team']).agg(scheduled_games=('game_id','size'),observed_report_games=('report_observed','sum')).reset_index()
 coverage['coverage']=coverage.observed_report_games/coverage.scheduled_games
 coverage.to_csv(PROCESSED/'coverage.csv',index=False)
 roster_frames=[]
 for y in range(2016,2026):
  r=pd.read_parquet(RAW/f'roster_weekly_{y}.parquet')
  r=r[r.game_type.eq('REG')].copy();r.team=teams(r.team)
  r=r.merge(panel[KEY+['gameday']],on=KEY,how='inner',validate='many_to_one')
  r['age']=(pd.to_datetime(r.gameday)-pd.to_datetime(r.birth_date,errors='coerce')).dt.days/365.25
  r['reserve_flag']=r.status.eq('RES').astype(int)
  r['active_flag']=r.status.isin(['ACT','INA']).astype(int)
  roster_frames.append(r[KEY+['gsis_id','full_name','position','status','status_description_abbr','age','reserve_flag','active_flag']])
 roster=pd.concat(roster_frames,ignore_index=True).drop_duplicates(KEY+['gsis_id','full_name'])
 roster.to_parquet(PROCESSED/'weekly_rosters.parquet',index=False)
 ra=roster.groupby(KEY).agg(reserve_count=('reserve_flag','sum'),roster_records=('gsis_id','size'),mean_roster_age=('age','mean')).reset_index()
 panel=panel.merge(ra,on=KEY,how='left',validate='one_to_one')
 panel=build_features(panel)
 panel.to_csv(PROCESSED/'team_games.csv',index=False)
 summary=panel.groupby(['season','team']).agg(games=('game_id','size'),observed_games=('out_count','count'),out_designations=('out_count','sum'),out_per_observed_game=('out_count','mean'),musculoskeletal_out_per_game=('musculoskeletal_out','mean'),out_excluding_noninjury_per_game=('out_excluding_noninjury','mean'),reserve_per_game=('reserve_count','mean'),win_share=('win','mean')).reset_index()
 summary['coverage']=summary.observed_games/summary.games
 summary['rank_out']=summary.groupby('season').out_per_observed_game.rank(ascending=False,method='min')
 summary.to_csv(PROCESSED/'team_seasons.csv',index=False)
 audit={'seasons':[2016,2025],'raw_regular_season_reports':raw_n,'deduplicated_reports':len(injury),'duplicate_rows_removed':raw_n-len(injury)-len(unmatched),'unmatched_reports':len(unmatched),'team_games':len(panel),'scheduled_games':len(games),'observed_team_games':int(panel.report_observed.sum()),'missing_report_team_games':int((~panel.report_observed).sum()),'missing_report_examples':panel.loc[~panel.report_observed,KEY].to_dict('records'),'roster_rows':len(roster),'roster_team_games_missing':int(panel.roster_records.isna().sum()),'missing_player_ids':int(injury.gsis_id.isna().sum()),'notes':['Blank report status is not Out. A missing whole team report is unknown.','Out designations can repeat for one injury and exclude many reserve-list absences.','Reserve status includes non-injury reserve categories; it is NOT an injured-reserve count.','Anatomical text is a proxy, not a clinical diagnosis or injury mechanism.']}
 (PROCESSED/'quality_audit.json').write_text(json.dumps(audit,indent=2))
 return panel,summary
if __name__=='__main__':
 p,s=prepare();print('Prepared',len(p),'team-games;',int(p.report_observed.sum()),'with reports.')
