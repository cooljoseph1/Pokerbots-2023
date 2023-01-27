from skeleton.actions import FoldAction, CallAction, CheckAction, RaiseAction
from skeleton.states import GameState, TerminalState, RoundState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot

from stats.kelly import *

import eval7
import math
import random

def get_winner(hand, board, cards):
    deals = random.sample(cards, k=15)
    opp_hand = deals[:2]
    board = board + deals[2:]
    x = min([i for i in range(4, len(board)) if board[i].suit in (0, 3)], default=len(board) - 1)
    board = board[:x+1]
    my_strength = eval7.evaluate(hand + board)
    opp_strength = eval7.evaluate(opp_hand + board)
    return int(my_strength > opp_strength) + 0.5 * int(my_strength == opp_strength)

def approx(board, hand, iters=1000):
    deck = eval7.Deck()
    for card in hand + board:
        deck.cards.remove(card)
    cards = deck.deal(52 - len(hand) - len(board))
    
    t = sum([get_winner(hand, board, cards) for _ in range(iters)])
    return t / iters - 1 / 2 / iters**0.5 # Subtract one standard deviation to be more conservative.

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

        future_rounds_left = NUM_ROUNDS - game_state.round_num # Number of rounds in the future excluding this current one
        win_line = 1 + future_rounds_left + (future_rounds_left + 1 - active) // 2 # If by the end of our turn, our advantage is at least this amount,
                                                                                   # we can guarantee a win by always folding
        ## Consider: Should we start always folding?
        advantage_if_fold = game_state.bankroll - my_contribution # How many chips would we have more than an equal split, even if we folded now?
        if advantage_if_fold >= win_line:
            # Always fold if we can
            if FoldAction in legal_actions:
                return FoldAction()
            else:
                return CheckAction()

        ## Okay, so we can't just always fold to victory. Let's try placing bets.
        # First, let's see how much we're allowed to raise.
        # Note: By looking at the engine, it appears that the minimum amount we can raise is max(opp_bet - my_bet + 2, 2 * opp_bet - 2 * my_bet)
        #       and the maximum amount we can raise is 2 * opp_bet - my_bet.
        #       Nevertheless, I think it prudent to just use the function we were given.
        max_cost = math.inf
        min_cost = -math.inf
        if RaiseAction in legal_actions:
           min_raise, max_raise = round_state.raise_bounds()  # the smallest and largest numbers of chips for a legal bet/raise
           min_cost = min_raise - my_pip  # the cost of a minimum bet/raise
           max_cost = max_raise - my_pip  # the cost of a maximum bet/raise
        else:
            min_raise, max_raise = my_pip, my_pip
            min_cost = min_raise - my_pip  # the cost of a minimum bet/raise
            max_cost = max_raise - my_pip  # the cost of a maximum bet/raise

        p = win_chances(board_cards, my_cards)
        eps = 1e-2
        p = min(1-eps, max(eps, p))

        actions = ["fold", "check", "call", "raise small", "raise medium", "raise large"]
        """
        Meaning of the actions:
        fold: fold.
        check: check.
        call: call.
        raise small: Raise the minimum you can.
        raise medium: Raise the geometric mean of the minimum and maximum you can raise.
        raise large: Raise the maximum you can.
        """

        strengths = {}
        for action in actions:
            if action == "fold":
                strengths[action] = reach_winline_chances(advantage_if_fold, win_line)
            elif action == "check":
                win_advantage = opp_contribution + advantage_if_fold
                lose_advantage = advantage_if_fold
                strengths[action] = p * reach_winline_chances(win_advantage, win_line) + (1 - p) * reach_winline_chances(lose_advantage, win_line)
            elif action == "call":
                win_advantage = opp_contribution + advantage_if_fold
                lose_advantage = advantage_if_fold - opp_contribution + my_contribution
                strengths[action] = p * reach_winline_chances(win_advantage, win_line) + (1 - p) * reach_winline_chances(lose_advantage, win_line)
            elif action == "raise small":
                raise_amount = min_cost
                new_equilibrium = my_contribution + raise_amount
                win_advantage = new_equilibrium + advantage_if_fold
                lose_advantage = advantage_if_fold - raise_amount
                strengths[action] = p * reach_winline_chances(win_advantage, win_line) + (1 - p) * reach_winline_chances(lose_advantage, win_line)
            elif action == "raise medium":
                raise_amount = int((min_cost * max_cost) ** 0.5)
                new_equilibrium = my_contribution + raise_amount
                win_advantage = new_equilibrium + advantage_if_fold
                lose_advantage = advantage_if_fold - raise_amount
                strengths[action] = p * reach_winline_chances(win_advantage, win_line) + (1 - p) * reach_winline_chances(lose_advantage, win_line)
            elif action == "raise large":
                raise_amount = max_cost
                new_equilibrium = my_contribution + raise_amount
                win_advantage = new_equilibrium + advantage_if_fold
                lose_advantage = advantage_if_fold - raise_amount
                strengths[action] = p * reach_winline_chances(win_advantage, win_line) + (1 - p) * reach_winline_chances(lose_advantage, win_line)
    
        actions.sort(key=lambda action: strengths[action], reverse=True) # Sort the actions we might take in reverse order, so the best action is first
        for action in actions:
            # First, check if we can do the action. If we can't, then move on to the next action possible
            if action == "fold":
                if FoldAction not in legal_actions:
                    continue
            elif action == "check":
                if CheckAction not in legal_actions:
                    continue
            elif action == "call":
                if CallAction not in legal_actions:
                    continue
            elif action.startswith("raise"):
                if RaiseAction not in legal_actions:
                    continue

            # Do the action and return it
            if action == "fold":
                return FoldAction()
            elif action == "check":
                return CheckAction()
            elif action == "call":
                return CallAction()
            elif action == "raise small":
                bet = min_cost
                return RaiseAction(my_pip + bet)
            elif action == "raise medium":
                bet = int((min_cost * max_cost) ** 0.5)
                return RaiseAction(my_pip + bet)
            elif action == "raise large":
                bet = max_cost
                return RaiseAction(my_pip + bet)
        
        # By default, return a CheckAction.
        return CheckAction()


if __name__ == '__main__':
    #approx([], [])
    run_bot(Player(), parse_args())
