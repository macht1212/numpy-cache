import numpy as np

from numpy_cache import save

arr = np.random.random(2_000_000)
save(arr, "data.bin")