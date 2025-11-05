import numpy as np
from hrvlib._core import hello_from_bin, compute_mean_centered


def hello() -> str:
    return hello_from_bin()

def cmc(vec: np.ndarray) -> np.ndarray:
    return compute_mean_centered(vec)