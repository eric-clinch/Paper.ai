import pickle
from Game import WINDOW_SIZE
from UserPlayer import rgbString, makeLight, averageColors
from tkinter import *

def myMap(f, L):
    return list(map(f, L))

def unzip(L):
    return [[a for a,b in row] for row in L], [[b for a,b in row] for row in L]

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

class StateActionPair(object):
    def __init__(self, pair):
        state, self.action = pair
        self.board, direction, self.heads, self.score = state
        playerCell = self.board[WINDOW_SIZE//2][WINDOW_SIZE//2]
        assert(playerCell[0] == 0 or playerCell[1] == 0)
        playerNum = playerCell[0] if playerCell[1] == 0 else playerCell[1]
        assert(playerNum > 0)

        territoryBoard, tailBoard = unzip(self.board)
        self.playerTerritory = self.getPlayerTerritoryPositions(territoryBoard, playerNum)
        self.enemyTerritory = self.getEnemyTerritoryPositions(territoryBoard, playerNum)
        self.walls = self.getWallPositions(territoryBoard)
        self.playerTail = self.getPlayerTailPositions(tailBoard, playerNum)
        self.enemyTail = self.getEnemyTailPositions(tailBoard, playerNum)
        self.headsBoard = self.getHeadsBoard(self.heads)

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
        data.index = (data.index - 1) % len(data.pairs)
    elif event.keysym == "Right":
        data.index = (data.index + 1) % len(data.pairs)
    elif event.keysym == "Up" or event.keysym == "Down":
        data.drawBoard = not data.drawBoard

def redrawAll(canvas, data):
    if data.drawBoard: data.pairs[data.index].drawBoard(canvas, data)
    else: data.pairs[data.index].drawData(canvas, data)

####################################
# use the run function as-is
####################################

def run(pairs, width=300, height=300):
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
    data.pairs = pairs
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
    directory = "Data"
    path = "Data/player1_2018-05-18 19-51-19.pickle"
    file = open(path, 'rb')
    data = pickle.load(file)
    file.close()

    pairs = []
    for pair in data:
        pairs.append(StateActionPair(pair))

    pair = pairs[-1]
    rows, cols = len(pair.board), len(pair.board[0])
    run(pairs, 700, 700)