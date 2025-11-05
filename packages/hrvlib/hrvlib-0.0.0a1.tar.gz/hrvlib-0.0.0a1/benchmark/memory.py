import numpy as np
from hrvlib.detrend import detrend_og, detrend_sparse
from hrvlib._core import detrend

rr_data = np.loadtxt("tests/data/training_session_63dce1ec-6804-473e-b3cd-fe1d1e75b816_hrv_1149.csv", skiprows=1)

# detrend_og(rr_data, lambada=25)
# detrend_sparse(rr_data, lambada=25)
x = detrend(rr_data, lambda_val=25)
# x = compute_mean_centered(rr_data)

print(x)
