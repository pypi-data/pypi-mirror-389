import timeit
import numpy as np
from hrvlib.detrend import detrend_og, detrend_sparse, detrend

number = 1000

rr_data = np.loadtxt("../tests/data/training_session_63dce1ec-6804-473e-b3cd-fe1d1e75b816_hrv_1149.csv", skiprows=1)


# Timing the functions
time_one = timeit.timeit(lambda: detrend_sparse(rr_data), number=number)
time_two = timeit.timeit(lambda: detrend_og(rr_data), number=number)
time_cpp = timeit.timeit(lambda: detrend(rr_data), number=number)

print(f"detrend_sparse runtime: {time_one:.6f} seconds")
print(f"detrend_og runtime: {time_two:.6f} seconds")
print(f"detrend_cpp runtime: {time_cpp:.6f} seconds")