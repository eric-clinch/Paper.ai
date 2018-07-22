from UserPlayer import UserPlayer
from SocketPlayer import SocketPlayer
from DataPlayer import DataPlayer
from SquarePlayer import SquarePlayer
from VisualPlayer import VisualPlayer

from NNPlayer import NNPlayer
from LearningPlayer import LearningPlayer
from DQN import DQN
from DuelNetwork import DuelNetwork

from DataParser import DataPoint
from Game import Game
import re
import math
import torch

def boltzmann(QValues, T, softmax):
    distribution = softmax(QValues / T)
    decision = torch.distributions.categorical.Categorical(distribution).sample()
    return decision

def boltzmannInstance(T):
    softmax = torch.nn.Softmax(dim=1)
    return lambda x: boltzmann(x, T, softmax)

def initLearningPlayer():
    regex = re.compile("2018-05-20_data_[0-9]*.pickle")
    points = DataPoint.readData("D:/paper.ai/parsed_data", regex)
    rewardFunction = lambda x: math.sqrt(x) if x >= 0 else 0
    LearningPlayer.init("NNs/trained_DuelNetwork", DuelNetwork, savePath="NNs/learned_DuelNetwork",
                        initialPoints=points, decisionFunction=boltzmannInstance(.1), rewardFunction=rewardFunction)

players = []

# players.append(DataPlayer(UserPlayer(), name="player1"))
# players.append(DataPlayer(SocketPlayer(50000), name="player2"))

# players.append(UserPlayer())
# players.append(NNPlayer("NNs/learned_NN_MSE"))

path = "NNs/learned_DuelNetwork"
players.append(VisualPlayer(NNPlayer(path, DuelNetwork)))
numOpponents = 2
for _ in range(numOpponents):
    players.append(NNPlayer(path, DuelNetwork))

# initLearningPlayer()
# numPlayers = 16
# for _ in range(numPlayers):
#     players.append(LearningPlayer())


print("starting game")
game = Game(100, players, timerDelay=0)
game.run()