
from Player import Player
import datetime
import pickle
import copy

class DataPlayer(Player):
    def initFileName(self):
        gamePlayerClass = self.gamePlayer.__class__.__name__
        now = datetime.datetime.now()
        currentTime = now.strftime("%Y-%m-%d %H-%M-%S")
        self.fileName = "Data/%s_%s.pickle" % (gamePlayerClass, currentTime)

    def __init__(self, gamePlayer):
        assert(isinstance(gamePlayer, Player))
        self.gamePlayer = gamePlayer
        self.initFileName()
        self.dataGathered = []
        self.state = None

    def setState(self, state):
        self.state = copy.deepcopy(state)
        self.gamePlayer.setState(state)

    def getMove(self):
        move = self.gamePlayer.getMove()
        self.dataGathered.append((self.state, move))
        return move

    # save all the data when the player dies
    def died(self):
        file = open(self.fileName, 'wb')
        pickle.dump(self.dataGathered, file)
        file.close()

        self.initFileName()
        self.dataGathered = []
        self.state = None