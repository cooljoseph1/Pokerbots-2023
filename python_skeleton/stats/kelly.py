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

def sign(x):
    return 1 if x > 0 else -1

def reach_winline_chances(advantage, line):
    """
    Return the chances of winning the overall match given that you currently have `advantage` chips
    more than an equal split (i.e. no bets at all occurred) and that if at the end of your turn either
    player is at or above `line` chips in difference they will win.
    """
    if advantage >= line:
        return 1.0
    if advantage <= -line:
        return 0.0
    return (1 + abs(advantage / (1 + line)) ** (0.3333333) * sign(advantage)) / 2