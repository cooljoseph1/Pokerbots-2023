import torch
from torch.utils.data import Dataset, DataLoader
import eval7
import random
from itertools import combinations
from os import path

SAVE_PATH = "small.pt"
CARD_ORDER = ['2c', '2d', '2h', '2s', '3c', '3d', '3h', '3s', '4c', '4d', '4h', '4s', '5c', '5d', '5h', '5s', '6c', '6d', '6h', '6s', '7c', '7d', '7h', '7s', '8c', '8d', '8h', '8s', '9c', '9d', '9h', '9s', 'Tc', 'Td', 'Th', 'Ts', 'Jc', 'Jd', 'Jh', 'Js', 'Qc', 'Qd', 'Qh', 'Qs', 'Kc', 'Kd', 'Kh', 'Ks', 'Ac', 'Ad', 'Ah', 'As']

# class ResBlock(torch.nn.Module):
#     def __init__(self, dimensions):
#         super().__init__()
#         self.layer1 = torch.nn.Linear(dimensions, dimensions)
#         self.layer2 = torch.nn.Linear(dimensions, dimensions)
#         self.activation = torch.nn.ELU()
#     def forward(self, x):
#         h = self.activation(self.layer1(x))
#         return self.activation(x + self.layer2(h))

# class QNN(torch.nn.Module):
#     def __init__(self, dimensions=256, layers=20):
#         super().__init__()
#         self.input_layer = torch.nn.Linear(2*52, dimensions)
#         self.hiddens = [ResBlock(dimensions) for i in range(layers)]
#         self.output_layer = torch.nn.Linear(dimensions, 1)
#         self.activation = torch.nn.Sigmoid()

#     def forward(self, x):
#         x = self.activation(self.input_layer(x))
#         for h in self.hiddens:
#             x = h(x)
#         x = self.activation(self.output_layer(x))
#         return x.view(len(x))

class QNN(torch.nn.Module):
    def __init__(self, dimensions=64, layers=4):
        super().__init__()
        self.input_layer = torch.nn.Linear(2*52, dimensions)
        self.hiddens = torch.nn.ParameterList([torch.nn.Linear(dimensions, dimensions) for i in range(layers)])
        self.output_layer = torch.nn.Linear(dimensions, 1)
        self.activation = torch.nn.ELU()
        self.output_activation = torch.nn.Sigmoid()

    def forward(self, x):
        x = self.activation(self.input_layer(x))
        for h in self.hiddens:
            x = self.activation(h(x))
        x = self.output_activation(self.output_layer(x))
        return x.view(len(x))

def best(hand, board):
    strength = -1
    comb = None
    for five in map(list, combinations(board, 5)):
        if eval7.evaluate(hand + five) > strength:
            comb = hand + five
            strength = eval7.evaluate(comb)
    return strength, comb

def approx(board, hand, iters=10):
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


class ChancesDataset(Dataset):
    def __init__(self, size=1000):
        self.inputs = []
        self.outputs = []
        self.size = size
        self.index = 0
    def append(self, ins, out):
        if len(self) < self.size:
            self.inputs.append(ins)
            self.outputs.append(out)
        else:
            self.inputs[self.index] = ins
            self.outputs[self.index] = out
            self.index += 1
            self.index %= self.size
    def __len__(self):
        return len(self.inputs)
    def __getitem__(self, idx):
        return self.inputs[idx], self.outputs[idx]

def gather_data():
    ins = torch.zeros(52 * 2, dtype=torch.float)
    deck = eval7.Deck()
    deck.shuffle()
    hand = deck.deal(2)
    board = deck.deal(5)
    while board[-1].suit in (1, 2):
        board += deck.deal(1)
    
    revealed = random.choice([0, *range(3, 1+len(board))])
    for card in board[:revealed]:
        ins[CARD_ORDER.index(str(card))] = 1
    for card in hand:
        ins[52 + CARD_ORDER.index(str(card))] = 1

    out = torch.tensor(approx(board[:revealed], hand), dtype=torch.float)

    return ins, out

def batch(size=64):
    ins, outs = zip(*[gather_data() for i in range(size)])
    ins = torch.stack(ins)
    outs = torch.stack(outs)
    return ins, outs

if __name__ == "__main__":
    import argparse
    import matplotlib.pyplot as plt
    import numpy as np

    train_dataset = ChancesDataset(size=1024)
    # Gather initial data
    for i in range(1000):
        train_dataset.append(*gather_data())
    train_dataloader = DataLoader(train_dataset, batch_size=64, shuffle=True)

    parser = argparse.ArgumentParser(prog="P0K3RB0TS Hand Trainer", description="Trains a neural net to give winning chances for a hand/board combo.")
    parser.add_argument('-i', '--inp')
    parser.add_argument('-o', '--out')
    args = parser.parse_args()
    load_path = args.inp or SAVE_PATH
    save_path = args.out or SAVE_PATH

    q_network = QNN()
    if load_path and path.exists(load_path):
        q_network.load_state_dict(torch.load(load_path))

    q_optim = torch.optim.AdamW(q_network.parameters(), lr=1e-4)
    scheduler = torch.optim.lr_scheduler.ExponentialLR(q_optim, gamma=0.7)
    q_loss = torch.nn.HuberLoss()

    def train(ins, targets):
        q_optim.zero_grad()
        outs = q_network(ins)
        loss = q_loss(outs, targets)
        loss.backward()
        return loss

    test_data = torch.zeros((2, 2 * 52), dtype=torch.float)
    test_data[0, 52 + CARD_ORDER.index('As')] = 1.0
    test_data[0, 52 + CARD_ORDER.index('Ac')] = 1.0
    test_data[1, 52 + CARD_ORDER.index('2s')] = 1.0
    test_data[1, 52 + CARD_ORDER.index('7c')] = 1.0

    plt.ion()
    fig = plt.figure()
    ax = fig.add_subplot(111)
    history = 1000
    line, = ax.plot([], [])
    def update_line(loss):
        if history and len(line.get_xdata()) == history:
            line.set_xdata([0])
            line.set_ydata([loss])
        else:
            line.set_xdata(np.append(line.get_xdata(), len(line.get_xdata())))
            line.set_ydata(np.append(line.get_ydata(), loss))
        ax.relim()
        ax.autoscale_view()
        fig.canvas.draw()
        fig.canvas.flush_events()
    
    running_loss = 0.03
    for epoch in range(20):
        for i in range(2000):
            loss = train(*next(iter(train_dataloader)))
            # loss = train(*batch())
            q_optim.step()
            # # Gather new data
            for j in range(1):
                train_dataset.append(*gather_data())
            
            if i % 30 == 0:
                print(f"EPOCH {epoch}, {i}/1000", q_network(test_data).tolist())
                running_loss = 0.9 * running_loss + 0.1 * loss.item()
                update_line(running_loss)
            
            if i % 1000 == 999:
                torch.save(q_network.state_dict(), save_path)
        
        scheduler.step()
