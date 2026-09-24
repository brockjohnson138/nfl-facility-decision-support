"""Descriptive uncertainty, sensitivity analyses, and non-causal game outcome prediction."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score,brier_score_loss,log_loss
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'data/processed';O=ROOT/'outputs'
def analyze():
 d=pd.read_csv(P/'team_games.csv');s=pd.read_csv(P/'team_seasons.csv')
 sf=s[s.team.eq('SF')].set_index('season')
 league=s[~s.team.eq('SF')].groupby('season').out_per_observed_game.mean()
 comparison=sf[['out_per_observed_game','rank_out','coverage']].copy()
 comparison['other_31_mean']=league;comparison['difference']=comparison.out_per_observed_game-league
 comparison.reset_index().to_csv(O/'sf_vs_league.csv',index=False)
 rng=np.random.default_rng(49);delta=comparison.difference.to_numpy();boot=rng.choice(delta,(10000,len(delta)),replace=True).mean(axis=1)
 ranking=s.groupby('team').agg(mean_out_per_game=('out_per_observed_game','mean'),mean_reserve_per_game=('reserve_per_game','mean')).sort_values('mean_out_per_game',ascending=False).reset_index()
 ranking.to_csv(O/'decade_rankings.csv',index=False)
 sens=[]
 for label,mask,col in [('All seasons',d.season>=2016,'out_count'),('Exclude 2020-2021',~d.season.isin([2020,2021]),'out_count'),('Anatomical proxy',d.season>=2016,'musculoskeletal_out'),('Exclude illness/personal/rest text',d.season>=2016,'out_excluding_noninjury')]:
  grouped=d[mask].groupby(['season','team'])[col].mean().unstack('team')
  a=grouped.SF;b=grouped.drop(columns='SF').mean(axis=1)
  sens.append({'definition':label,'sf_mean':float(a.mean()),'other_teams_mean':float(b.mean()),'difference':float((a-b).mean())})
 pd.DataFrame(sens).to_csv(O/'benchmark_sensitivity.csv',index=False)
 # Observational game predictions, one row per game; no point spread (can incorporate injuries).
 home=d[d.home.eq(1)].copy();away=d[d.home.eq(0)].copy()
 opp=away[['game_id','out_count','score_margin_lag3','rest']].rename(columns={c:'opp_'+c for c in ['out_count','score_margin_lag3','rest']})
 g=home.merge(opp,on='game_id',validate='one_to_one')
 g=g[(g.score_margin!=0)&g.out_count.notna()&g.opp_out_count.notna()].copy()
 g['out_difference']=g.out_count-g.opp_out_count
 g['prior_margin_difference']=g.score_margin_lag3-g.opp_score_margin_lag3
 g['rest_difference']=g.rest-g.opp_rest
 g['home_win']=(g.score_margin>0).astype(int)
 rows=[];coefs=[]
 for label,features in [('History only',['prior_margin_difference','rest_difference','week']),('History + Out reports',['prior_margin_difference','rest_difference','week','out_difference'])]:
  train=g[g.season<=2023]
  m=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(C=.1,max_iter=1000,random_state=49))
  m.fit(train[features],train.home_win)
  for year in [2024,2025]:
   test=g[g.season==year];pred=m.predict_proba(test[features])[:,1]
   rows.append({'model':label,'season':year,'games':len(test),'auc':float(roc_auc_score(test.home_win,pred)),'brier':float(brier_score_loss(test.home_win,pred)),'log_loss':float(log_loss(test.home_win,pred))})
  coefs.extend([{'model':label,'feature':f,'standardized_log_odds_coefficient':float(c)} for f,c in zip(features,m[-1].coef_[0])])
 pd.DataFrame(rows).to_csv(O/'game_outcome_metrics.csv',index=False)
 pd.DataFrame(coefs).to_csv(O/'game_outcome_coefficients.csv',index=False)
 summary={'sf_mean_out_per_game':float(comparison.out_per_observed_game.mean()),'other_31_mean_out_per_game':float(league.mean()),'sf_decade_rank':int(ranking.index[ranking.team.eq('SF')][0]+1),'mean_difference':float(delta.mean()),'paired_season_bootstrap_95_interval':np.quantile(boot,[.025,.975]).tolist(),'recent_3_year_mean_sf_out_designations':float(sf.loc[2023:2025,'out_designations'].mean()),'interpretation':'Descriptive comparisons of report designations, not injury incidence or an exposure effect. Bootstrap resamples only ten paired seasons; adjacent seasons may be dependent. Team means weight each season equally. Missing report games excluded. Outcomes model is predictive only; no coefficient is converted into causal wins or revenue.'}
 (O/'findings.json').write_text(json.dumps(summary,indent=2));return summary
if __name__=='__main__':print(json.dumps(analyze(),indent=2))
