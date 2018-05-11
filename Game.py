import random
import time
from Enums import Directions, DIRECTIONS

WINDOW_SIZE = 51

# Helper utilities
def inBounds(r,c,board):
    return ((r > 0) and (r < len(board)) and (c > 0) and (c < len(board)))

# Player class for game
class Player(object):
    def getWindowCoords(self, extent):
        leftC = self.c - extent
        topR = self.r - extent
        diameter = (extent * 2) + 1

        out = []
        for r in range(diameter):
            for c in range(diameter):
                out += [(r + topR, c + leftC)]

        return out

    def __init__(self, index, interface, board, startBlobExtent):
        self.interface = interface
        self.c = None
        self.r = None
        self.index = index
        self.direction = random.choice(DIRECTIONS)
        self.isDead = False

        maxCoord = len(board) - 1 - startBlobExtent

        # set x in available x position
        while (self.r == None and self.c == None):
            self.r = random.randint(startBlobExtent, maxCoord)
            self.c = random.randint(startBlobExtent, maxCoord)

            for (r, c) in self.getWindowCoords(startBlobExtent):
                if (board[r][c] != (0, 0)):
                    self.r = None
                    self.c = None

        for (r, c) in self.getWindowCoords(startBlobExtent):
            board[r][c] = (self.index, False)

    def getWindow(self, board):
        window = [[(-1, 0)] * WINDOW_SIZE for i in range(WINDOW_SIZE)]
        boardCoords = self.getWindowCoords(WINDOW_SIZE // 2)

        leftC = self.c - (WINDOW_SIZE // 2)
        topR = self.r - (WINDOW_SIZE // 2)

        for (r,c) in boardCoords:
            windowR = r - topR
            windowC = c - leftC
            if (inBounds(r,c,board)):
                window[windowR][windowC] = board[r][c]

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
        self.timerDelay = 200
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

    def playerFromIndex(self, playerIndex):
        return self.players[playerIndex - 1]

    def killPlayer(self, player):
        player.isDead = True
        for r in range(len(self.board)):
            for c in range(len(self.board)):
                (territoryOwner, tailOwner) = self.board[r][c]
                if (tailOwner == player.index): tailOwner = 0
                if (territoryOwner == player.index): territoryOwner = 0
                self.board[r][c] = (territoryOwner, tailOwner)

    def tryFill(self, r, c, fullSet, player):
        result = set([(r,c)])
        cellStack = []
        cellStack.append((r, c))
        isValid = True

        while(len(cellStack) > 0):
            r, c = cellStack.pop()

            for (dRow, dCol) in [(0,1), (0,-1), (1,0), (-1,0)]:
                newR = r + dRow
                newC = c + dCol
                if inBounds(newR, newC, self.board):
                    if ((newR, newC) in fullSet):
                        fullSet.remove((newR,newC))
                        cellStack.append((newR, newC))
                        result.add((newR, newC))
                else:
                    isValid = False

        return result if isValid else None

    def collectTerritory(self, player):
        fullSet = set()

        #turn all tails into solid territory
        for r in range(len(self.board)):
            for c in range(len(self.board)):
                (territoryOwner, tailOwner) = self.board[r][c]
                if (tailOwner == player.index):
                    self.board[r][c] = (player.index, 0)

        for r in range(len(self.board)):
            for c in range(len(self.board)):
                (territoryOwner, tailOwner) = self.board[r][c]
                if (territoryOwner != player.index):
                    fullSet.add((r,c))

        # collect space inside of the solid territory
        while (len(fullSet) > 0):
            (startR, startC) = fullSet.pop()
            fillSet = self.tryFill(startR, startC, fullSet, player)
            if fillSet == None: continue

            for (r, c) in fillSet:
                (_, tailOwner) = self.board[r][c]
                self.board[r][c] = (player.index, tailOwner)

    def tick(self):
        dMap = {Directions.LEFT: (0, -1), Directions.RIGHT: (0, 1),
                Directions.UP: (-1, 0), Directions.DOWN: (1, 0)}
        deathList = set()

        livePlayers = list(filter(lambda p: (not p.isDead), self.players))

        for player in livePlayers:
            player.setState(self.board)
        for player in livePlayers:
            player.getMove()
        for player in livePlayers:
            (dr, dc) = dMap[player.direction]
            player.r += dr
            player.c += dc
            if not inBounds(player.r, player.c, self.board):
                deathList.add(player)
        livePlayers = list(filter(lambda p: (not p.isDead), self.players))
        for player in livePlayers:
            (territoryOwner, tailOwner) = self.board[player.r][player.c]
            if (tailOwner != 0):
                deathList.add(self.playerFromIndex(tailOwner))
            for other in livePlayers:
                if (player.index != other.index
                        and player.r == other.r and player.c == other.c):
                    deathList.add(player)
                    deathList.add(player)
        for player in deathList:
            self.killPlayer(player)

        livePlayers = list(filter(lambda p: (not p.isDead), self.players))

        for player in livePlayers:
            (territoryOwner, tailOwner) = self.board[player.r][player.c]
            if (territoryOwner != player.index):
                self.board[player.r][player.c] = (territoryOwner, player.index)
            else:
                self.collectTerritory(player)

        if self.allPlayersDead():
            self.running = False

    def run(self):
        while self.running:
            self.tick()
            time.sleep(self.timerDelay / 1000)
