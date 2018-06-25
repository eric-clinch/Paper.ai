
from Player import Player
from Enums import Directions, DIRECTIONS
from DataParser import State
from Game import WINDOW_SIZE
from DQN import DQN
from DataParser import DataPoint
from TrainPlayer import train
import torch
import random
import math

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

class LearningPlayer(Player):

    replayBuffer = None
    stateCount = 0
    targetUpdateRate = 0
    rewardFunction = lambda x: x
    batchSize = 256
    savePath = None
    saveRate = 0
    NN = None
    targetNN = None
    players = []

    @staticmethod
    def init(NNPath, replayBufferSize=15000, targetUpdateRate=1000, savePath=None, saveRate=1000, initialPoints=None):
        LearningPlayer.replayBuffer = ReplayMemory(replayBufferSize)
        LearningPlayer.targetUpdateRate = targetUpdateRate
        LearningPlayer.rewardFunction = lambda x: math.sqrt(x) if x >= 0 else -math.sqrt(abs(x))
        LearningPlayer.savePath = savePath
        LearningPlayer.saveRate = saveRate

        LearningPlayer.NN = DQN().to(device)
        LearningPlayer.NN.load_state_dict(torch.load(NNPath))

        LearningPlayer.targetNN = DQN().to(device)
        LearningPlayer.targetNN.eval()

        # fill the replay buffer
        if initialPoints is not None:
            initialPoints = initialPoints[:replayBufferSize]
            for point in initialPoints:
                LearningPlayer.replayBuffer.push(point)

    def __init__(self):
        assert(LearningPlayer.NN is not None)  # LearningPlayer.init must be called before the constructor
        self.roundData = []

        board = [[(0, 0)] * WINDOW_SIZE for _ in range(WINDOW_SIZE)]
        board[WINDOW_SIZE//2][WINDOW_SIZE//2] = (1, 0)
        heads = []
        direction = Directions.UP
        score = 0
        rawState = (board, direction, heads, score)
        self.rawState = rawState
        self.state = State(rawState)

        LearningPlayer.players.append(self)
        self.move = None

    def setState(self, s):
        self.rawState = s
        self.state = State(s)
        LearningPlayer.stateCount += 1

        if LearningPlayer.stateCount % 100 == 0:
            print("processed %d states" % LearningPlayer.stateCount)

        if LearningPlayer.stateCount % LearningPlayer.targetUpdateRate == 0:
            LearningPlayer.targetNN.load_state_dict(LearningPlayer.NN.state_dict())

        if LearningPlayer.savePath is not None and LearningPlayer.stateCount % LearningPlayer.saveRate == 0:
            torch.save(LearningPlayer.NN.state_dict(), LearningPlayer.savePath)


    @staticmethod
    def getPlayerMoves():
        inputs = [torch.Tensor(p.state.bitboard) for p in LearningPlayer.players]
        input = torch.stack(inputs).to(device)
        QValues = LearningPlayer.NN(input)
        _, decisions = torch.max(QValues, 1)

        # set player moves
        for i in range(len(LearningPlayer.players)):
            player = LearningPlayer.players[i]
            playerDecision = decisions[i].item()
            player.move = DIRECTIONS[playerDecision]

        # train
        if len(LearningPlayer.replayBuffer) >= LearningPlayer.batchSize:
            train(LearningPlayer.NN, LearningPlayer.targetNN,
                  LearningPlayer.replayBuffer.sample(LearningPlayer.batchSize), batchSize=LearningPlayer.batchSize,
                  rewardFunction=LearningPlayer.rewardFunction)

    def getMove(self):
        if self.move is None:
            LearningPlayer.getPlayerMoves()

        move = self.move
        self.roundData.append((self.rawState, move))
        self.move = None
        return move

    # save all the data when the player dies
    def died(self):
        parsedPoints = DataPoint.parsePoints(self.roundData)
        for point in parsedPoints:
            LearningPlayer.replayBuffer.push(point)

        self.roundData = []

# taken from https://pytorch.org/tutorials/intermediate/reinforcement_q_learning.html
class ReplayMemory(object):

    def __init__(self, capacity):
        self.capacity = capacity
        self.memory = []
        self.position = 0

    def push(self, point):
        if len(self.memory) < self.capacity:
            self.memory.append(None)
        self.memory[self.position] = point
        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)