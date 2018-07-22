
from Player import Player
from Enums import Directions, DIRECTIONS
from DataParser import State
from Game import WINDOW_SIZE
import torch

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def greedy(QValues):
    _, decision = torch.max(QValues, 1)
    return decision

class NNPlayer(Player):

    # the given decision function should take a tensor of Q-values of size 1x4, and return a tensor of size 1 which
    # stores the action to be made.
    def __init__(self, NNPath, architecture, decisionFunction=greedy):
        board = [[(0, 0)] * WINDOW_SIZE for _ in range(WINDOW_SIZE)]
        board[WINDOW_SIZE//2][WINDOW_SIZE//2] = (1, 0)
        heads = []
        direction = Directions.UP
        score = 0
        state = (board, direction, heads, score)
        self.state = State(state)

        self.NN = architecture().to(device)
        self.NN.train(False)
        self.NN.eval()
        self.NN.load_state_dict(torch.load(NNPath))
        self.decisionFunction = decisionFunction

    def setState(self, s):
        self.state = State(s)

    def getMove(self):
        NNInput = torch.Tensor(self.state.bitboard)
        NNInput = NNInput.unsqueeze(0).to(device)
        QValues = self.NN(NNInput)
        print(QValues)
        decision = self.decisionFunction(QValues).item()
        return DIRECTIONS[decision]