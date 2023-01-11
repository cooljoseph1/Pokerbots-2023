from .train import CARD_ORDER, SAVE_PATH, QNN
import torch

model = None
def prepare(path=None):
    global model
    if path is None:
        path = SAVE_PATH
    model = QNN()
    model.load_state_dict(torch.load(path))
    model.eval()

def win_chances(board, hand):
    ins = torch.zeros(52 * 2, dtype=torch.float)
    for card in board:
        ins[CARD_ORDER.index(str(card))] = 1
    for card in hand:
        ins[52 + CARD_ORDER.index(str(card))] = 1
    
    if model is None:
        prepare()
    with torch.no_grad():
        return model(ins).item()

if __name__ == "__main__":
    import eval7
    from train import best, approx
    iters = 10000

    deck = eval7.Deck()
    deck.shuffle()
    my_hand = deck.deal(2)
    opp_hand = deck.deal(2)

    board = deck.deal(0)
    print(win_chances(board, my_hand), win_chances(board, opp_hand), approx(board, my_hand, iters), approx(board, opp_hand, iters), my_hand, opp_hand, board)

    board += deck.deal(3)
    print(win_chances(board, my_hand), win_chances(board, opp_hand), approx(board, my_hand), approx(board, opp_hand), my_hand, opp_hand, board)


    for i in range(2):
        board += deck.deal(1)
        print(win_chances(board, my_hand), win_chances(board, opp_hand), approx(board, my_hand), approx(board, opp_hand), my_hand, opp_hand, board)

    while board[-1].suit in (1, 2):
        board += deck.deal(1)
        print(win_chances(board, my_hand), win_chances(board, opp_hand), approx(board, my_hand), approx(board, opp_hand), my_hand, opp_hand, board)

    
    my_strength, my_comb = best(my_hand, board)
    opp_strength, opp_comb = best(opp_hand, board)

    out = 0.5
    if my_strength > opp_strength:
        out = 1.0
    elif my_strength < opp_strength:
        out = 0.0
    print(out, 1-out, my_comb, opp_comb)
