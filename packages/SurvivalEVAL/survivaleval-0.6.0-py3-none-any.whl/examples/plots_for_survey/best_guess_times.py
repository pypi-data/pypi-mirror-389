import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from scipy.integrate import cumulative_trapezoid
import math
import seaborn as sns
import matplotlib.patches as patches
import matplotlib.lines as mlines
import pandas as pd
import lifelines
from lifelines import CoxPHFitter, KaplanMeierFitter
from matplotlib.axis import Axis
from matplotlib.spines import Spine

from SurvivalEVAL import SingleTimeEvaluator


plt.style.use('seaborn-v0_8-paper')
plt.rcParams["figure.figsize"] = (4, 3)
plt.rc('axes', titlesize=9.5)     # fontsize of the axes title
plt.rc('axes', labelsize=9.5)    # fontsize of the x and y labels
# plt.rc('xtick', labelsize=10)    # fontsize of the tick labels
# plt.rc('ytick', labelsize=10)    # fontsize of the tick labels
plt.rc('legend', fontsize=9.5)    # legend fontsize
plt.rc('figure', titlesize=9.5)  # fontsize of the figure title

plt.rcParams['font.size'] = 12


# ==============================================================================
# 1. Load the Data
# ==============================================================================
data = lifelines.datasets.load_gbsg2()
# preprocessing
data.rename(columns={'cens': 'event'}, inplace=True)
data['horTh'] = data['horTh'].map({'no': 0, 'yes': 1})
data['menostat'] = data['menostat'].map({'Pre': 0, 'Post': 1})
data['tgrade'] = data['tgrade'].map({'I': 1, 'II': 2, 'III': 3})
# randomly divide the data into training and validation sets
df_train = data.sample(frac=0.7, random_state=42)  # 70% for training
df_train = df_train.reset_index(drop=True)
df_test = data.drop(df_train.index)  # remaining 30% for testing
df_test = df_test.reset_index(drop=True)
x_test = df_test.drop(columns=['time', 'event']).values

# ==============================================================================
# 2. Fit a Kaplan-Meier Model
# ==============================================================================
kmf = KaplanMeierFitter()
kmf.fit(df_train['time'], event_observed=df_train['event'])

# renormalize the km curve at 3 years
year = 3
target_time = 365 * year
surv_at_target = kmf.survival_function_at_times(target_time).values[0]
kmf_surv_renorm = kmf.survival_function_ / surv_at_target
kmf_surv_renorm.iloc[kmf_surv_renorm.index < target_time] = 1.0

fig, ax = plt.subplots()
kmf.plot_survival_function(ax=ax, label=r'$S_E(t)$', ci_show=False, linewidth=2, color='cornflowerblue')
# plot the renormalized survival curve
ax.step(kmf_surv_renorm.index, kmf_surv_renorm['KM_estimate'], where="post",
        label=r'$S_E(t \mid t > 3)$', linestyle='--', linewidth=2, color='orange')
# fill the grey area under the renormalized curve
ax.fill_between(kmf_surv_renorm.index, 0, kmf_surv_renorm['KM_estimate'],
                where=(kmf_surv_renorm.index >= target_time), color='orange', alpha=0.2)
# add a vertical line at target time
ax.axvline(x=target_time, color='grey', linestyle='--', linewidth=2)
ax.set_xlabel('Time (days)')
ax.set_ylabel('Survival Probability')
ax.legend()
plt.tight_layout()
plt.savefig('margin_times.png', dpi=400)
