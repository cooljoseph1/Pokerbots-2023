import torch
import eval7
import random
from itertools import combinations
from os import path

SAVE_PATH = "small.pt"
CARD_ORDER = ['2c', '2d', '2h', '2s', '3c', '3d', '3h', '3s', '4c', '4d', '4h', '4s', '5c', '5d', '5h', '5s', '6c', '6d', '6h', '6s', '7c', '7d', '7h', '7s', '8c', '8d', '8h', '8s', '9c', '9d', '9h', '9s', 'Tc', 'Td', 'Th', 'Ts', 'Jc', 'Jd', 'Jh', 'Js', 'Qc', 'Qd', 'Qh', 'Qs', 'Kc', 'Kd', 'Kh', 'Ks', 'Ac', 'Ad', 'Ah', 'As']

class QNN(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.hiddens = torch.nn.ParameterList([torch.nn.Linear(2*52, 128)] + [torch.nn.Linear(128, 128) for i in range(10)])
        self.hiddens.append(torch.nn.Linear(128, 1))
        self.activation = torch.nn.ELU()

    def forward(self, x):
        for h in self.hiddens:
            x = self.activation(h(x))
        return x.view(len(x))

def best(hand, board):
    strength = -1
    comb = None
    for five in map(list, combinations(board, 5)):
        if eval7.evaluate(hand + five) > strength:
            comb = hand + five
            strength = eval7.evaluate(comb)
    return strength, comb

def data():
    ins = torch.zeros(52 * 2, dtype=torch.float)
    deck = eval7.Deck()
    deck.shuffle()
    my_hand = deck.deal(2)
    opp_hand = deck.deal(2)
    board = deck.deal(5)
    while board[-1].suit in (1, 2):
        board += deck.deal(1)
    
    revealed = random.choice([0, *range(3, 1+len(board))])
    for card in board[:revealed]:
        ins[CARD_ORDER.index(str(card))] = 1
    for card in my_hand:
        ins[52 + CARD_ORDER.index(str(card))] = 1
    
    my_strength, _ = best(my_hand, board)
    opp_strength, _ = best(opp_hand, board)

    out = 0.5
    if my_strength > opp_strength:
        out = 1.0
    elif my_strength < opp_strength:
        out = 0.0
    return ins, out


def batch(size=64):
    ins, outs = zip(*(data() for i in range(size)))
    ins = torch.stack(ins)
    outs = torch.tensor(outs)
    return ins, outs

if __name__ == "__main__":
    q_network = QNN()
    if path.exists(SAVE_PATH):
        q_network.load_state_dict(torch.load(SAVE_PATH))

    q_optim = torch.optim.Adam(q_network.parameters(), lr=1e-4)
    scheduler = torch.optim.lr_scheduler.ExponentialLR(q_optim, gamma=0.8)
    q_loss = torch.nn.HuberLoss()

    def train(ins, targets):
        q_optim.zero_grad()
        outs = q_network(ins)
        loss = q_loss(outs, targets)
        loss.backward()
        return loss

    test = torch.zeros((2, 2 * 52), dtype=torch.float)
    test[0, 52 + CARD_ORDER.index('As')] = 1.0
    test[0, 52 + CARD_ORDER.index('Ac')] = 1.0
    test[1, 52 + CARD_ORDER.index('2s')] = 1.0
    test[1, 52 + CARD_ORDER.index('7c')] = 1.0

    for epoch in range(20):
        for i in range(1000):
            train(*batch())
            q_optim.step()
        scheduler.step()
        print(q_network(test))

    torch.save(q_network.state_dict(), SAVE_PATH)
