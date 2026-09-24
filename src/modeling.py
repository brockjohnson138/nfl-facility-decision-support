"""Temporal benchmarking for reported Out counts, NOT diagnosis or EMF causality."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import PoissonRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_poisson_deviance
from sklearn.inspection import permutation_importance
import joblib
ROOT=Path(__file__).resolve().parents[1];O=ROOT/'outputs';P=ROOT/'data/processed'
NUM=['week','rest','home','out_count_lag1','out_count_lag3','listed_count_lag1','listed_count_lag3','reserve_count_lag1','reserve_count_lag3','mean_roster_age_lag1','score_margin_lag3','missing_previous_report']
CAT=['team']
FEATURES=NUM+CAT
NAMES=['training_mean','last_game','poisson','gradient_boosting','random_forest']
def estimator(name):
 prep=ColumnTransformer([('num',make_pipeline(SimpleImputer(strategy='median',add_indicator=True),StandardScaler()),NUM),('cat',OneHotEncoder(handle_unknown='ignore',sparse_output=False),CAT)])
 models={'poisson':PoissonRegressor(alpha=.15,max_iter=1000),'gradient_boosting':HistGradientBoostingRegressor(loss='poisson',learning_rate=.05,max_iter=120,max_leaf_nodes=8,l2_regularization=5,early_stopping=False,random_state=49),'random_forest':RandomForestRegressor(n_estimators=200,min_samples_leaf=20,max_features=.8,n_jobs=2,random_state=49)}
 return make_pipeline(prep,models[name])
def fit_predict(name,train,test):
 if name=='training_mean':return np.full(len(test),train.out_count.mean()),None
 if name=='last_game':return test.out_count_lag1.fillna(train.out_count.mean()).to_numpy(),None
 m=estimator(name);m.fit(train[FEATURES],train.out_count)
 return np.maximum(m.predict(test[FEATURES]),1e-6),m

def scores(y,p):return {'mae':float(mean_absolute_error(y,p)),'rmse':float(np.sqrt(mean_squared_error(y,p))),'poisson_deviance':float(mean_poisson_deviance(y,np.maximum(p,1e-6)))}
def run_models():
 O.mkdir(exist_ok=True)
 d=pd.read_csv(P/'team_games.csv');d=d[d.out_count.notna()].copy()
 validation=[]
 for year in [2021,2022,2023]:
  train=d[d.season<year];val=d[d.season==year]
  for name in NAMES:
   pred,_=fit_predict(name,train,val)
   validation.append({'model':name,'validation_season':year,**scores(val.out_count,pred)})
 v=pd.DataFrame(validation);v.to_csv(O/'validation_metrics.csv',index=False)
 selected=v.groupby('model').mae.mean().idxmin()
 train=d[d.season<=2023];cal=d[d.season==2024];test=d[d.season==2025]
 predframes=[];metrics=[];selected_model=None
 for name in NAMES:
  pred,m=fit_predict(name,train,test)
  cp,_=fit_predict(name,train,cal)
  residual=np.abs(cal.out_count.to_numpy()-cp)
  q=float(np.quantile(residual,min(1,np.ceil((len(residual)+1)*.9)/len(residual)),method='higher'))
  low=np.maximum(0,pred-q);high=pred+q
  metrics.append({'model':name,'selected_by_validation':bool(name==selected),**scores(test.out_count,pred),'interval_90_coverage':float(np.mean((test.out_count>=low)&(test.out_count<=high))),'interval_mean_width':float(np.mean(high-low)),'calibration_residual_quantile':q})
  f=test[['game_id','team','season','week','out_count']].copy();f['prediction']=pred;f['lower90']=low;f['upper90']=high;f['model']=name;predframes.append(f)
  if name==selected and m is not None:selected_model=m
 pd.DataFrame(metrics).to_csv(O/'test_metrics.csv',index=False)
 preds=pd.concat(predframes,ignore_index=True);preds.to_csv(O/'test_predictions.csv',index=False)
 if selected_model is not None:
  joblib.dump(selected_model,O/'selected_model.joblib')
  imp=permutation_importance(selected_model,test[FEATURES],test.out_count,n_repeats=10,random_state=49,scoring='neg_mean_absolute_error',n_jobs=2)
  pd.DataFrame({'feature':FEATURES,'mae_increase':imp.importances_mean,'sd':imp.importances_std}).sort_values('mae_increase',ascending=False).to_csv(O/'feature_importance.csv',index=False)
 # Paired MAE difference with teams as resampling blocks; repeated games stay together.
 wide=preds.pivot(index=['game_id','team','out_count'],columns='model',values='prediction').reset_index()
 wide['improvement']=abs(wide.out_count-wide.training_mean)-abs(wide.out_count-wide[selected])
 by=wide.groupby('team').improvement.mean().to_numpy();rng=np.random.default_rng(49)
 boot=rng.choice(by,size=(5000,len(by)),replace=True).mean(axis=1)
 card={'target':'Number of players designated Out in each observed team-game injury report; not incident injuries, all games missed, or IR burden.','selected_model':selected,'features':FEATURES,'training_seasons':[2016,2023],'selection_validation_seasons':[2021,2022,2023],'interval_calibration_season':2024,'test_season':2025,'train_rows':len(train),'calibration_rows':len(cal),'test_rows':len(test),'test_mae_improvement_over_training_mean':float(wide.improvement.mean()),'team_block_bootstrap_95_interval':np.quantile(boot,[.025,.975]).tolist(),'limits':['Predictive associations are not causal effects. No EMF exposure feature exists.','Lags are previous games within season; no current injury status or current result is a predictor.','Historical snapshots lack full as-of versioning; this is retrospective temporal evaluation, not a verified live trading-style backtest.','Intervals calibrated on 2024 residuals are empirical; temporal and team dependence prevent guaranteed nominal coverage.','Models and hyperparameters fixed before final test evaluation. Latest test features may use earlier observed games in 2025; weights are frozen.','Team identity and reserve counts may encode reporting practices; feature importance does not identify causes.']}
 (O/'model_card.json').write_text(json.dumps(card,indent=2))
 return card
if __name__=='__main__':print(json.dumps(run_models(),indent=2))
