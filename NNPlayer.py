
from Player import Player
from Enums import Directions, DIRECTIONS
from DataParser import State
from Game import WINDOW_SIZE
from DQN import DQN
import torch

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


class NNPlayer(Player):

    def __init__(self, NNPath):
        board = [[(0, 0)] * WINDOW_SIZE for _ in range(WINDOW_SIZE)]
        board[WINDOW_SIZE//2][WINDOW_SIZE//2] = (1, 0)
        heads = []
        direction = Directions.UP
        score = 0
        state = (board, direction, heads, score)
        self.state = State(state)

        self.NN = DQN().to(device)
        self.NN.train(False)
        self.NN.load_state_dict(torch.load(NNPath))

    def setState(self, s):
        self.state = State(s)

    def getMove(self):
        NNInput = torch.Tensor(self.state.bitboard)
        NNInput = NNInput.unsqueeze(0).to(device)
        QValues = self.NN(NNInput)
        print("Q values:", QValues)
        _, decision = torch.max(QValues, 1)
        decision = decision.item()
        print("decision:", decision)
        print()
        return DIRECTIONS[decision]