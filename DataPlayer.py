
from Player import Player
import datetime
import pickle
import copy
import os

class DataPlayer(Player):
    def initFileName(self):
        now = datetime.datetime.now()
        currentTime = now.strftime("%Y-%m-%d %H-%M-%S")
        self.fileName = "%s/%s_%s.pickle" % (self.directory, self.name, currentTime)

    def __init__(self, gamePlayer, name=None, directory="Data"):
        assert(isinstance(gamePlayer, Player))
        self.gamePlayer = gamePlayer
        self.directory = directory
        if not os.path.exists(directory):
            os.makedirs(directory)
        if name == None:
            self.name = self.gamePlayer.__class__.__name__
        else:
            self.name = name
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
        file = open(self.fileName, 'wb+')
        pickle.dump(self.dataGathered, file)
        file.close()

        self.initFileName()
        self.dataGathered = []
        self.state = None