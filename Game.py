import random
import time
from Enums import Directions, DIRECTIONS

WINDOW_SIZE = 51

# Helper utilities
def inBounds(x,y,board):
    return ((x > 0) and (x < len(board)) and (y > 0) and (y < len(board)))

# Player class for game
class Player(object):
    def getWindowCoords(self, extent):
        leftX = self.x - extent
        topY = self.y - extent
        diameter = (extent * 2) + 1

        out = []
        for x in range(diameter):
            for y in range(diameter):
                out += [(x + leftX, y + topY)]

        return out

    def __init__(self, index, interface, board, startBlobExtent):
        self.interface = interface
        self.x = None
        self.y = None
        self.index = index
        self.direction = random.choice(DIRECTIONS)
        self.isDead = False

        maxCoord = len(board) - 1 - startBlobExtent

        # set x in available x position
        while (self.x == None and self.y == None):
            self.x = random.randint(startBlobExtent, maxCoord)
            self.y = random.randint(startBlobExtent, maxCoord)

            for (x, y) in self.getWindowCoords(startBlobExtent):
                if (board[x][y] != (0, 0)):
                    self.x = None
                    self.y = None

        for (x, y) in self.getWindowCoords(startBlobExtent):
            board[x][y] = (self.index, False)

    def getWindow(self, board):
        window = [[(-1, False)] * WINDOW_SIZE for i in range(WINDOW_SIZE)]
        boardCoords = self.getWindowCoords(WINDOW_SIZE // 2)

        leftX = self.x - (WINDOW_SIZE // 2)
        topY = self.y - (WINDOW_SIZE // 2)

        for (x,y) in boardCoords:
            windowX = x - leftX
            windowY = y - topY
            if (inBounds(x,y,board)):
                window[windowX][windowY] = board[x][y]

        return window

    def setState(self, board):
        if not self.isDead:
            self.interface.setState((self.getWindow(board), self.direction))
        else:
            return None

    def getMove(self):
        opposites = {Directions.LEFT : Directions.RIGHT,
                     Directions.RIGHT: Directions.LEFT,
                     Directions.UP: Directions.DOWN,
                     Directions.DOWN: Directions.UP,
                     Directions.NULL: Directions.NULL}
        newDir = self.interface.getMove()
        if (opposites[newDir] == self.direction):
            return
        if (newDir == Directions.NULL):
            return
        self.direction = newDir

    def __hash__(self):
        return hash(self.index)

# Game logic
class Game(object):
    def __init__(self, boardSize, players):
        self.board = [[(0, 0)] * boardSize for i in range(boardSize)]
        # how far from the center of the start blob the blob extends
        self.startBlobExtent = 1
        self.players = []
        self.timerDelay = 500
        self.running = True
        for player in players:
            self.addPlayer(player)

    def addPlayer(self, interface):
        newPlayer = Player(len(self.players) + 1, interface,
                           self.board, self.startBlobExtent)
        self.players.append(newPlayer)

    def allPlayersDead(self):
        for player in self.players:
            if not player.isDead:
                return False
        return True

    def playerFromIndex(self, player):
        self.players[tailOwner - 1]

    def killPlayer(self, player):
        player.isDead = True
        for x in range(len(self.board)):
            for y in range(len(self.board)):
                (territoryOwner, tailOwner) = self.board[x][y]
                if (tailOwner == player.index): newTailOwner = 0
                if (territoryOwner == player.index): newTerritoryOwner = 0
                self.board[x][y] = (newTerritoryOwner, newTailOwner)


    def collectTerritory(self, player):
        #turn all tails into solid territory
        for y in range(len(self.board)):
            for x in range(len(self.board)):
                (territoryOwner, tailOwner) = self.board[x][y]
                if (tailOwner == player.index):
                    self.board[x][y] = (player.index, 0)

        # collect space inside of the solid territory
        for y in range(len(self.board)):
            prevTail = False
            collecting = False
            horizontalLine = False
            for x in range(len(self.board)):
                (territoryOwner, tailOwner) = self.board[x][y]
                if (territoryOwner == player.index):
                    collecting = False
                    if prevTail:
                        horizontalLine = True
                    prevTail = True
                else:
                    if not horizontalLine and prevTail:
                        collecting = True
                    prevTail = False
                    horizontalLine = False

                    if collecting:
                        self.board[x][y] = (player.index, 0)

    def tick(self):
        dMap = {Directions.LEFT: (-1, 0), Directions.RIGHT: (1, 0),
                Directions.UP: (0, 1), Directions.DOWN: (0, -1)}
        deathList = set()

        livePlayers = list(filter(lambda p: (not p.isDead), self.players))

        for player in livePlayers:
            player.setState(self.board)
        for player in livePlayers:
            player.getMove()
        for player in livePlayers:
            print(player.direction)
            (dx, dy) = dMap[player.direction]
            player.x += dx
            player.y += dy
            if not inBounds(player.x, player.y, self.board):
                deathList.add(player)
        for player in livePlayers:
            (territoryOwner, tailOwner) = self.board[player.x][player.y]
            if (tailOwner != 0):
                deathList.add(self.playerFromIndex(tailOwner))
            for other in livePlayers:
                if (player.index != other.index
                    and player.x == other.x and player.y == other.y):
                    deathList.add(player)
                    deathList.add(player)
        for player in deathList:
            self.killPlayer(player)

        livePlayers = list(filter(lambda p: (not p.isDead), self.players))

        for player in livePlayers:
            (territoryOwner, tailOwner) = self.board[player.x][player.y]
            if (territoryOwner != player.index):
                self.board[player.x][player.y] = (territoryOwner, player.index)
            else:
                self.collectTerritory(player)

        if self.allPlayersDead():
            self.running = False

    def run(self):
        while self.running:
            self.tick()
            time.sleep(self.timerDelay / 1000)
