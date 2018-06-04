import pickle
import time
from Game import WINDOW_SIZE
from UserPlayer import rgbString, makeLight, averageColors
from tkinter import *
from Enums import Directions
import torch
from DQN import DQN
import os
import threading


def myMap(f, L):
    return list(map(f, L))


def unzip(L):
    return [[a for a,b in row] for row in L], [[b for a,b in row] for row in L]


def getPartitions(L, partitionSize):
    res = []
    for i in range(0, len(L), partitionSize):
        partition = L[i:i + partitionSize]
        res.append(partition)
    return res

intToRGB = {-1: (169, 169, 169),  # gray
            0: (255, 255, 255),  # white
            1: (25, 25, 255),  # blue
            2: (255, 25, 25),  # red
            3: (25, 255, 25),  # green
            4: (255, 255, 0),  # yellow
            5: (255, 20, 147),  # pink
            6: (160, 32, 240),  # purple
            7: (32, 21, 11)  # brown
            }

# a DataPoint consists of a starting state S, an action a taken in this state, a new state S' that the game reaches
# after action a is taken in state S, and a reward R received. If the game ends after action a is taken in state S,
# then S' is None
class DataPoint(object):
    def __init__(self, stateBitboard, action, nextStateBitboard, reward):
        self.stateBitboard = stateBitboard
        self.action = action
        self.nextStateBitboard = nextStateBitboard
        self.reward = reward

    @staticmethod
    def fromStates(state, action, nextState, reward):
        assert isinstance(state, State)
        assert isinstance(action, Directions)
        assert nextState is None or isinstance(nextState, State)
        stateBitboard = state.bitboard
        nextStateBitboard = nextState.bitboard if nextState is not None else None
        return DataPoint(stateBitboard, action, nextStateBitboard, reward)

    @staticmethod
    def fromCompressed(compressed):
        sparseState, action, sparseNextState, reward = compressed
        stateBitboard = DataPoint.fromSparseBord(sparseState)
        nextStateBitboard = DataPoint.fromSparseBord(sparseNextState)
        return DataPoint(stateBitboard, action, nextStateBitboard, reward)

    @staticmethod
    def getSparseBoard(bitboard):
        if bitboard is None:
            return None
        onPoints = []
        layers, rows, cols = len(bitboard), len(bitboard[0]), len(bitboard[0][0])
        assert(layers == State.BITBOARD_DEPTH and rows == WINDOW_SIZE and cols == WINDOW_SIZE)
        for layer in range(layers):
            for row in range(rows):
                for col in range(cols):
                    if bitboard[layer][row][col] == 1:
                        coordinate = (layer, row, col)
                        onPoints.append(coordinate)
        return onPoints

    @staticmethod
    def fromSparseBord(sparseBitboard):
        if sparseBitboard is None:
            return None
        bitboard = [[[0] * WINDOW_SIZE for _ in range(WINDOW_SIZE)] for _ in range(State.BITBOARD_DEPTH)]
        for coordinate in sparseBitboard:
            layer, row, col = coordinate
            bitboard[layer][row][col] = 1
        return bitboard

    def compressed(self):
        sparseState = DataPoint.getSparseBoard(self.stateBitboard)
        sparseNextState = DataPoint.getSparseBoard(self.nextStateBitboard)
        return sparseState, self.action, sparseNextState, self.reward

    def drawBoard(self, canvas, data):
        self.state.drawBoard(canvas, data)
        canvas.create_text(50, 50, text="reward: %d" % self.reward)

    def drawData(self, canvas, data):
        self.state.drawData(canvas, data)
        canvas.create_text(50, 50, text="reward: %d" % self.reward)

    @staticmethod
    def parseFile(path):
        file = open(path, 'rb')
        data = pickle.load(file)
        file.close()

        points = []
        for i in range(len(data)):
            s, action = data[i]
            if action == Directions.NULL:
                continue  # ignore datapoints where we don't know the move
            currentState = State(s)
            nextS, _ = data[i + 1] if i + 1 < len(data) else (None, None)
            nextState = State(nextS) if nextS is not None else None
            nextStateScore = nextState.score if nextState is not None else 0
            reward = nextStateScore - currentState.score
            if nextStateScore == 0:
                reward = - WINDOW_SIZE * WINDOW_SIZE  # makes the reward for dying a constant
            points.append(DataPoint.fromStates(currentState, action, nextState, reward).compressed())
        return points

    # parses all files in the given directory whose names match the given regex
    # stores the result in the given path
    @staticmethod
    def parseData(inputDirectory, regex):
        assert(os.path.isdir(inputDirectory))
        points = []
        for filename in os.listdir(inputDirectory):
            if regex.match(filename):
                print("parsing", filename)
                filePath = inputDirectory + '/' + filename
                filePoints = DataPoint.parseFile(filePath)
                points += filePoints

        return points

    @staticmethod
    def storePoints(points, outputDirectory, outputFilenamePrefix):
        if not os.path.exists(outputDirectory):
            os.makedirs(outputDirectory)

        # save the files in partitions of length 1000
        partitions = getPartitions(points, 1000)
        for i in range(len(partitions)):
            pointPartition = partitions[i]
            outputFilename = "%s_%d.pickle" % (outputFilenamePrefix, i)
            outputPath = outputDirectory + "/" + outputFilename
            file = open(outputPath, 'wb+')
            pickle.dump(pointPartition, file)
            file.close()

    @staticmethod
    def readFile(path):
        file = open(path, 'rb')
        filePoints = pickle.load(file)
        file.close()
        filePoints = myMap(lambda x: DataPoint.fromCompressed(x), filePoints)
        return filePoints

    # reads in the parsed datapoints from files in the given directory whose names
    # match the given regex, and returns a list of all points read in
    @staticmethod
    def readData(directory, regex):
        assert(os.path.isdir(directory))
        print("reading in data")
        files = os.listdir(directory)
        points = []
        for i in range(len(files)):
            filename = files[i]
            if regex.match(filename):
                path = directory + "/" + filename
                points += DataPoint.readFile(path)

        return points


class State(object):

    BITBOARD_DEPTH = 6

    def __init__(self, state):
        self.board, direction, self.heads, self.score = state
        playerCell = self.board[WINDOW_SIZE//2][WINDOW_SIZE//2]
        assert(playerCell[0] != playerCell[1])
        playerNum = playerCell[0] if playerCell[1] == 0 else playerCell[1]
        assert(playerNum > 0)

        territoryBoard, tailBoard = unzip(self.board)
        self.playerTerritory = self.getPlayerTerritoryPositions(territoryBoard, playerNum)
        self.enemyTerritory = self.getEnemyTerritoryPositions(territoryBoard, playerNum)
        self.playerTail = self.getPlayerTailPositions(tailBoard, playerNum)
        self.enemyTail = self.getEnemyTailPositions(tailBoard, playerNum)
        self.headsBoard = self.getHeadsBoard(self.heads)
        self.walls = self.getWallPositions(territoryBoard)
        self.bitboard = [self.playerTerritory, self.enemyTerritory,
                                     self.playerTail, self.enemyTail,
                                     self.headsBoard, self.walls]
        assert(len(self.bitboard) == State.BITBOARD_DEPTH)

    def drawBoard(self, canvas, data):
        cellWidth = data.width / WINDOW_SIZE
        cellHeight = data.height / WINDOW_SIZE
        for row in range(WINDOW_SIZE):
            for col in range(WINDOW_SIZE):
                playerInt, tailInt = self.board[row][col]
                if (tailInt > 0):
                    rgb = intToRGB[tailInt]
                    rgb = makeLight(rgb)
                    if (playerInt > 0):
                        playerRGB = intToRGB[playerInt]
                        rgb = averageColors(rgb, playerRGB)
                else:
                    rgb = intToRGB[playerInt]
                cellLeft = col * cellWidth
                cellRight = cellLeft + cellWidth
                cellTop = row * cellHeight
                cellBot = cellTop + cellHeight
                canvas.create_rectangle(cellLeft, cellTop, cellRight, cellBot,
                    fill= rgbString(rgb), width=0)

        headRadius = 3
        for head in self.heads:
            headRow, headCol = head
            cellX = headCol * cellWidth + cellWidth / 2
            cellY = headRow * cellHeight + cellHeight / 2
            canvas.create_oval(cellX - headRadius, cellY - headRadius,
                               cellX + headRadius, cellY + headRadius, fill="black")

    def drawData(self, canvas, data):
        cellWidth = data.width / WINDOW_SIZE
        cellHeight = data.height / WINDOW_SIZE
        headRadius = 3
        for row in range(WINDOW_SIZE):
            for col in range(WINDOW_SIZE):
                isPlayerTerritory = self.playerTerritory[row][col]
                isEnemyTerritory = self.enemyTerritory[row][col]
                assert(not (isPlayerTerritory and isEnemyTerritory))
                isPlayerTail = self.playerTail[row][col]
                isEnemyTail = self.enemyTail[row][col]
                assert(not (isPlayerTail and isEnemyTail))
                assert(not (isPlayerTail and isPlayerTerritory))
                assert(not (isEnemyTail and isEnemyTerritory))

                rgb = None
                if isPlayerTerritory > 0:
                    rgb = intToRGB[1]
                if isPlayerTail > 0:
                    rgb = makeLight(intToRGB[1])
                if isEnemyTerritory > 0:
                    if rgb == None: rgb = intToRGB[2]
                    else: rgb = averageColors(rgb, intToRGB[2])
                if isEnemyTail > 0:
                    if rgb == None: rgb = makeLight(intToRGB[2])
                    else: rgb = averageColors(rgb, makeLight(intToRGB[2]))
                if self.walls[row][col]:
                    assert(rgb == None)
                    rgb = intToRGB[-1]
                if rgb == None: rgb = intToRGB[0]
                cellLeft = col * cellWidth
                cellRight = cellLeft + cellWidth
                cellTop = row * cellHeight
                cellBot = cellTop + cellHeight
                canvas.create_rectangle(cellLeft, cellTop, cellRight, cellBot,
                    fill= rgbString(rgb), width=0)

                if self.headsBoard[row][col]:
                    cellX = col * cellWidth + cellWidth / 2
                    cellY = row * cellHeight + cellHeight / 2
                    canvas.create_oval(cellX - headRadius, cellY - headRadius,
                                       cellX + headRadius, cellY + headRadius, fill="black")

    @staticmethod
    def getPlayerTerritoryPositions(territoryBoard, playerNum):
        playerFilter = lambda x: 1 if x == playerNum else 0
        return myMap(lambda row: myMap(playerFilter, row), territoryBoard)

    @staticmethod
    def getEnemyTerritoryPositions(territoryBoard, playerNum):
        enemyFilter = lambda x: 1 if (x != playerNum and x > 0) else 0
        return myMap(lambda row: myMap(enemyFilter, row), territoryBoard)

    @staticmethod
    def getWallPositions(territoryBoard):
        wallFilter = lambda x: 1 if x < 0 else 0
        return myMap(lambda row: myMap(wallFilter, row), territoryBoard)

    @staticmethod
    def getPlayerTailPositions(tailBoard, playerNum):
        playerFilter = lambda x: 1 if x == playerNum else 0
        return myMap(lambda row: myMap(playerFilter, row), tailBoard)

    @staticmethod
    def getEnemyTailPositions(tailBoard, playerNum):
        enemyFilter = lambda x: 1 if (x != playerNum and x > 0) else 0
        return myMap(lambda row: myMap(enemyFilter, row), tailBoard)

    @staticmethod
    def getHeadsBoard(heads):
        headsBoard = [[0] * WINDOW_SIZE for _ in range(WINDOW_SIZE)]
        for head in heads:
            headRow, headCol = head
            if headRow >= 0 and headCol >= 0 and headRow < WINDOW_SIZE and headCol < WINDOW_SIZE:
                headsBoard[headRow][headCol] = 1
        return headsBoard


def init(data):
    data.index = 0
    data.drawBoard = True


def keyPressed(event, data):
    if event.keysym == "Left":
        data.index = (data.index - 1) % len(data.points)
    elif event.keysym == "Right":
        data.index = (data.index + 1) % len(data.points)
    elif event.keysym == "Up" or event.keysym == "Down":
        data.drawBoard = not data.drawBoard


def redrawAll(canvas, data):
    if data.drawBoard: data.points[data.index].drawBoard(canvas, data)
    else: data.points[data.index].drawData(canvas, data)


def run(points, width=600, height=600):
    def redrawAllWrapper(canvas, data):
        canvas.delete(ALL)
        canvas.create_rectangle(0, 0, data.width, data.height,
                                fill='white', width=0)
        redrawAll(canvas, data)
        canvas.update()

    def keyPressedWrapper(event, canvas, data):
        keyPressed(event, data)
        redrawAllWrapper(canvas, data)

    # Set up data and call init
    class Struct(object): pass
    data = Struct()
    data.width = width
    data.height = height
    data.points = points
    root = Tk()
    init(data)
    # create the root and the canvas
    canvas = Canvas(root, width=data.width, height=data.height)
    canvas.pack()
    # set up events
    root.bind("<Key>", lambda event:
                            keyPressedWrapper(event, canvas, data))
    redrawAll(canvas, data)
    # and launch the app
    root.mainloop()  # blocks until window is closed


if __name__ == "__main__":
    file = open("gameplay_data/player1_2018-05-20 00-13-24.pickle", 'rb')
    data = pickle.load(file)
    file.close()
    data = myMap(lambda x: State(x[0]), data)
    run(data)

    # regex = re.compile("player[12]_2018-05-20 .*\.pickle")
    regex = re.compile("player1_2018-05-20 00-13-24\.pickle")
    points = DataPoint.parseData("gameplay_data", regex)
    # DataPoint.storePoints(points, "D:/paper.ai/parsed_data2", "2018-05-20_data")


    # regex = re.compile("2018-05-20_data_[0-9]*.pickle")

    # startTime = time.time()
    # points = DataPoint.readData("D:/paper.ai/parsed_data", regex)
    # print("time to read:", time.time() - startTime)
    # print(len(points))