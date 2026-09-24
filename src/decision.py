"""Scenario decision analysis. No probability or causal effect is learned from NFL injuries."""
from dataclasses import dataclass,asdict,replace
import numpy as np
import pandas as pd
@dataclass(frozen=True)
class Scenario:
 hazard_probability:float=.10
 attributable_fraction:float=.20
 annual_units:float=40.0
 contribution_per_win_m:float=3.0
 wins_per_unit:float=.02
 other_cost_per_unit_m:float=.05
 capex_m:float=150.0
 disruption_m:float=5.0
 annual_extra_opex_m:float=1.0
 annual_nonhealth_benefit_m:float=0.0
 terminal_residual_m:float=0.0
 horizon:int=15
 discount:float=.05
 construction_years:int=2
 study_cost_m:float=.25
 study_years:int=1
 sensitivity:float=.8
 specificity:float=.8
 def validate(self):
  for k in ['hazard_probability','attributable_fraction','sensitivity','specificity']:
   if not 0<=getattr(self,k)<=1:raise ValueError(f'{k} must be between 0 and 1')
  for k,v in asdict(self).items():
   if not np.isfinite(v) or v<0:raise ValueError(f'{k} must be finite and nonnegative')
  if self.horizon<1 or self.construction_years+self.study_years>=self.horizon:raise ValueError('Horizon must exceed construction plus study delay')
  if any(int(getattr(self,k))!=getattr(self,k) for k in ['horizon','construction_years','study_years']):raise ValueError('Year counts must be integers')

def annuity(s,delay=0):return float(sum((1+s.discount)**(-t) for t in range(delay+s.construction_years+1,s.horizon+1)))
def unit_value(s):return s.wins_per_unit*s.contribution_per_win_m+s.other_cost_per_unit_m

def state_values(s,delay=0):
 s.validate();a=annuity(s,delay)
 fixed=-(s.capex_m+s.disruption_m)/(1+s.discount)**delay+a*(s.annual_nonhealth_benefit_m-s.annual_extra_opex_m)+s.terminal_residual_m/(1+s.discount)**s.horizon
 hazard=a*s.annual_units*s.attributable_fraction*unit_value(s)
 return np.array([fixed,fixed+hazard])

def evaluate(s):
 s.validate();p=s.hazard_probability;weights=np.array([1-p,p]);v=state_values(s);delayed=state_values(s,s.study_years)
 relocate=float(weights@v);stay=0.0
 # Joint probabilities of state and binary research signal, NOT a mere EMF meter reading.
 joint_plus=np.array([(1-p)*(1-s.specificity),p*s.sensitivity])
 joint_minus=weights-joint_plus
 branch={};research=-s.study_cost_m
 for label,joint in [('positive',joint_plus),('negative',joint_minus)]:
  prob=float(joint.sum());posterior=float(joint[1]/prob) if prob>0 else None
  weighted_move=float(joint@delayed)
  move=prob>0 and weighted_move>0
  research+=max(0,weighted_move)
  branch[label]={'signal_probability':prob,'posterior_hazard_probability':posterior,'action':'Relocate' if move else 'Stay'}
 best_no_study=max(0,relocate)
 evpi=float(weights@np.maximum(v,0)-best_no_study)
 evsi_delayed=float(research+s.study_cost_m-max(0,float(weights@delayed)))
 # State-conditional research payoff averages over signals and applies branch decisions.
 iv=[]
 for h in [0,1]:
  prob_plus=s.sensitivity if h else 1-s.specificity
  moved=prob_plus*(branch['positive']['action']=='Relocate')+(1-prob_plus)*(branch['negative']['action']=='Relocate')
  iv.append(-s.study_cost_m+moved*delayed[h])
 payoffs=np.array([[0,0],iv,v]);regret=payoffs.max(axis=0)-payoffs
 actions={'Stay':stay,'Investigate':float(research),'Relocate':relocate}
 denom=s.annual_units*unit_value(s)*annuity(s)
 threshold=float(-v[0]/denom) if denom>0 else None
 return {'scenario_only':True,'action_values_m':actions,'preferred_action':max(actions,key=actions.get),'state_move_npv_m':{'no_hazard':float(v[0]),'hazard':float(v[1])},'study_branches':branch,'perfect_information_value_m':max(0,evpi),'sample_information_value_at_delayed_decision_m':max(0,evsi_delayed),'net_study_advantage_vs_act_now_m':float(research-best_no_study),'break_even_probability_times_fraction':threshold,'minimax_regret_action':['Stay','Investigate','Relocate'][int(regret.max(axis=1).argmin())],'max_regret_m':dict(zip(['Stay','Investigate','Relocate'],regret.max(axis=1).tolist())),'annual_benefit_if_hazard_m':s.annual_units*s.attributable_fraction*unit_value(s),'expected_annual_units_avoided':p*s.attributable_fraction*s.annual_units}

def simulate(s,n=20000,seed=49):
 """Independent illustrative triangular financial inputs, fixed subjective hazard probability."""
 rng=np.random.default_rng(seed);result=evaluate(s);h=rng.random(n)<s.hazard_probability
 cap=rng.triangular(.75,1,1.25,n)*s.capex_m
 frac=rng.triangular(.5,1,1.5,n)*s.attributable_fraction;frac=np.clip(frac,0,1)
 unit=rng.triangular(.5,1,1.5,n)*unit_value(s)
 def payoff(delay):
  return -(cap+s.disruption_m)/(1+s.discount)**delay+annuity(s,delay)*(s.annual_nonhealth_benefit_m-s.annual_extra_opex_m+h*s.annual_units*frac*unit)+s.terminal_residual_m/(1+s.discount)**s.horizon
 mv=payoff(0);signal=rng.random(n)<np.where(h,s.sensitivity,1-s.specificity)
 policy=np.where(signal,result['study_branches']['positive']['action']=='Relocate',result['study_branches']['negative']['action']=='Relocate')
 research=-s.study_cost_m+policy*payoff(s.study_years)
 return pd.DataFrame({'Stay':np.zeros(n),'Investigate':research,'Relocate':mv})

def sensitivity_grid(s):
 rows=[]
 for p in np.linspace(0,1,21):
  for f in np.linspace(0,1,21):
   r=evaluate(replace(s,hazard_probability=float(p),attributable_fraction=float(f)))
   rows.append({'hazard_probability':p,'attributable_fraction':f,'preferred_action':r['preferred_action'],**r['action_values_m']})
 return pd.DataFrame(rows)
