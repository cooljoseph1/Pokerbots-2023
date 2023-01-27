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

def reach_winline_chances_deriv(advantage, line):
    """
    Derivative of above function.
    """
    if advantage >= line:
        return 0
    if advantage <= -line:
        return 0
    
    return sign(advantage) * abs(advantage / (1 + line))**(-5/3) / 6
def minimax(bankroll, pot, contribution, call_cost, raise_amounts, line, strength, depth=3):
    """
    Gives your expected winnings according to minimax, as well as the index of the action.
        0 - Fold
        1 - Check/call
        2, 3, 4 - Raise

    Simulates the opponent's strength as a beta distribution that peaks at 1 - strength.
    """
    if depth == 0:
        # Fold chance
        fold_chance = reach_winline_chances(bankroll - contribution, line)
        # Check/call chance
        check_chance = strength * reach_winline_chances(bankroll + pot - contribution, line) + \
                        (1 - strength) * reach_winline_chances(bankroll - contribution - call_cost, line)
        
        # No raising allowed at the end of depth (doesn't make sense because we can't simulate opponent putting more into the pot).
        return (fold_chance, check_chance)
    
    opp_strength = 1 - strength

    # Chance if you fold
    chances = [reach_winline_chances(bankroll - contribution, line)]

    # Chance if you check/call
    chances.append(1 - max(minimax(-bankroll, pot+call_cost, contribution+call_cost, 0,
                                raise_amounts, line, opp_strength, depth=depth-1)))
    
    # Chance if you raise
    for amount in raise_amounts:
        chances.append(1 - max(minimax(-bankroll, pot+call_cost+amount, contribution+call_cost, amount,
                                    raise_amounts, line, opp_strength, depth=depth-1)))
    
    return chances