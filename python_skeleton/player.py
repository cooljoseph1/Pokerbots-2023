from skeleton.actions import FoldAction, CallAction, CheckAction, RaiseAction
from skeleton.states import GameState, TerminalState, RoundState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot

from stats.kelly import *

import eval7
import math
from itertools import combinations

def best(hand, board):
    strength = -1
    comb = None
    for five in map(list, combinations(board, 5)):
        if eval7.evaluate(hand + five) > strength:
            comb = hand + five
            strength = eval7.evaluate(comb)
    return strength, comb

def approx(board, hand, iters=1000):
    t = 0
    for i in range(iters):
        deck = eval7.Deck()
        for card in hand + board:
            deck.cards.remove(card)
        deck.shuffle()
        opp_hand = deck.deal(2)
        b = board.copy()
        if len(b) == 0:
            b += deck.deal(5)
        elif len(b) < 5:
            b += deck.deal(5 - len(board))
        while b[-1].suit in (1, 2):
            b += deck.deal(1)
        my_strength, _ = best(hand, b)
        opp_strength, _ = best(opp_hand, b)
        t += int(my_strength > opp_strength) + 0.5 * int(my_strength == opp_strength)
    return t / iters


from ai.strength import *

try:
    1/0
    prepare("ai/small.pt")
except:
    def win_chances(board, hand):
        board = [*map(eval7.Card, board)]
        hand = [*map(eval7.Card, hand)]
        return approx(board, hand)


class Player(Bot):
    '''
    A pokerbot.
    '''

    def __init__(self):
        '''
        Called when a new game starts. Called exactly once.

        Arguments:
        Nothing.

        Returns:
        Nothing.
        '''
        pass

    def handle_new_round(self, game_state, round_state, active):
        '''
        Called when a new round starts. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Nothing.
        '''
        #my_bankroll = game_state.bankroll  # the total number of chips you've gained or lost from the beginning of the game to the start of this round
        #game_clock = game_state.game_clock  # the total number of seconds your bot has left to play this game
        #round_num = game_state.round_num  # the round number from 1 to NUM_ROUNDS
        #my_cards = round_state.hands[active]  # your cards
        #big_blind = bool(active)  # True if you are the big blind
        pass

    def handle_round_over(self, game_state, terminal_state, active):
        '''
        Called when a round ends. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        terminal_state: the TerminalState object.
        active: your player's index.

        Returns:
        Nothing.
        '''
        #my_delta = terminal_state.deltas[active]  # your bankroll change from this round
        #previous_state = terminal_state.previous_state  # RoundState before payoffs
        #street = previous_state.street  # int of street representing when this round ended
        #my_cards = previous_state.hands[active]  # your cards
        #opp_cards = previous_state.hands[1-active]  # opponent's cards or [] if not revealed
        pass

    def get_action(self, game_state, round_state, active):
        '''
        Where the magic happens - your code should implement this function.
        Called any time the engine needs an action from your bot.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Your action.
        '''
        legal_actions = round_state.legal_actions()  # the actions you are allowed to take
        street = round_state.street  # int representing pre-flop, flop, turn, or river respectively
        my_cards = round_state.hands[active]  # your cards
        board_cards = round_state.deck[:street]  # the board cards
        my_pip = round_state.pips[active]  # the number of chips you have contributed to the pot this round of betting
        opp_pip = round_state.pips[1-active]  # the number of chips your opponent has contributed to the pot this round of betting
        my_stack = round_state.stacks[active]  # the number of chips you have remaining
        opp_stack = round_state.stacks[1-active]  # the number of chips your opponent has remaining
        continue_cost = opp_pip - my_pip  # the number of chips needed to stay in the pot
        my_contribution = STARTING_STACK - my_stack  # the number of chips you have contributed to the pot
        opp_contribution = STARTING_STACK - opp_stack  # the number of chips your opponent has contributed to the pot

        max_cost = math.inf
        if RaiseAction in legal_actions:
           min_raise, max_raise = round_state.raise_bounds()  # the smallest and largest numbers of chips for a legal bet/raise
           min_cost = min_raise - my_pip  # the cost of a minimum bet/raise
           max_cost = max_raise - my_pip  # the cost of a maximum bet/raise

        # TODO: more fancy stuff based on previous rounds.
        p = win_chances(board_cards, my_cards)
        eps = 1e-2
        p = min(1-eps, max(eps, p))
        q = 1 - p
        n = my_contribution + opp_contribution
        try:
            max_bet = int(kelly_me(n, p, my_stack))
        except:
            raise Exception(f"{n} {p} {my_stack} {kelly_me(n, p, my_stack)}")

        print(f"ROUND {game_state.round_num}; max_bet = {max_bet} ({kelly_me(n, p, my_stack)})")
        print(f"continue_cost = {continue_cost}")
        print(f"n = {n}, p = {p}, c = {my_stack}, my/opp_pip = {my_pip}/{opp_pip}")
        
        if continue_cost > max_bet: # Not worth it to even call.
            if CheckAction in legal_actions:
                return CheckAction()
            else:
                return FoldAction()
        
        if opp_stack == 0:
            opp_bet = 0
        else:
            opp_bet = kelly_opp(n + continue_cost, q, opp_stack)
        print(f"opp_bet = {opp_bet}")
        bet = min(max_bet, max_cost, max(min_cost, opp_bet + continue_cost))
        bet = int(bet)

        print(f"min_cost={min_cost}, max_cost={max_cost}, bet={bet}")

        if bet >= min_cost and RaiseAction in legal_actions:
            return RaiseAction(my_pip + bet)
        elif CallAction in legal_actions:
                return CallAction()
        return CheckAction()


if __name__ == '__main__':
    run_bot(Player(), parse_args())
