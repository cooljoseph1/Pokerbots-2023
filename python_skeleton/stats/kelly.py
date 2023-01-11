import numpy as np

def kelly_me(n, p, c):
    return c - np.exp((np.log(c) - p * np.log(c + n)) / (1-p))

def kelly_opp(n, q, d):
    # Uses Newton's method.
    if q >= 0.5:
        return np.inf
    def f(x):
        return (1-q)*np.log(d-x)+q*np.log(d+n+x)-np.log(d)
    def fp(x):
        return (q-1)/(d-x)+q/(d+n+x)
    x = d / 2
    for i in range(10):
        x -= f(x) / fp(x)
    return x