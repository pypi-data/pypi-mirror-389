import numpy as np

from SurvivalEVAL.Evaluations.Concordance import concordance_ic
from SurvivalEVAL.NonparametricEstimator.SingleEvent import \
    TurnbullEstimatorLifelines

eta = np.array([0.9, 0.2, 0.7, 0.4, 0.5, 0.7, 0.9, 0.3, 0.4])              # risk scores
left = np.array([
    0.20,
    0.20,
    1.20,
    1.50,
    2.00,
    0.00,
    2.20,
    3.00,
    0.90,
], dtype=float)

right = np.array([
    0.80,
    1.20,
    1.80,
    3.30,
    2.00,
    np.inf,
    4.90,
    3.00,
    0.90,
], dtype=float)
# left = np.array([0.0, 6.0, 0.8, 2])              # l_i
# right = np.array([1.0, np.inf, 1.5, 3])          # r_i (inf = right-censored)
left_train = np.array([0.2, 2.0, 1.0, 0.3, 4.0, 3.0, 2, 5, 4, 0])      # training l_i
right_train = np.array([0.6, 3.0, 2.0, 1.5, np.inf, 6.5, 5, 6, np.inf, 3])  # training r_i

# plot the Turnbull estimator for training data
import matplotlib.pyplot as plt

tb = TurnbullEstimatorLifelines(left_train, right_train)
times = tb.survival_times
surv = tb.survival_probabilities
plt.step(times, surv, where="post")
plt.ylim(-0.1, 1.1)
plt.xlabel("Time")
plt.ylabel("Survival Probability S(t)")
plt.title("Turnbull Estimator on Training Data")
plt.grid()
plt.show()

c_ic, num_matrix, den_matrix = concordance_ic(eta, left, right, left_train, right_train, ties="skip")
print("Interval-censored C-index:", c_ic)
