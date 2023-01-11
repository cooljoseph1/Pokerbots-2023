import numpy as np
import matplotlib.pyplot as plt

from python_skeleton.stats.kelly import *

c = d = 100
p = 0.8
n = np.arange(1000)
x = kelly_me(n, p, c)
y = kelly_opp(n, 1-p, d)
plt.title(f"Break Even Raising, p={p}, c=d={c}")
plt.xlabel("# in pot")
plt.ylabel("# chips to raise")
plt.plot(n, x, label="Break Even")
plt.plot(n, y, label="Thwart Opponent")
plt.legend()

plt.show()