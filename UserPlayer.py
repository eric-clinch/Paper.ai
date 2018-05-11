
from Player import Player
from Enums import Directions
import time
import random
from Game import WINDOW_SIZE
import threading

from tkinter import *

###############################################
# UI based off of 15-112 animations framework #
###############################################

class UserPlayer(Player):
    def __init__(self, width=700, height=700):
        self.board = [[(0, 0)] * WINDOW_SIZE for _ in range(WINDOW_SIZE)]
        self.direction = Directions.UP
        self.nextDirection = Directions.NULL
        self.width = width
        self.height = height
        self.cellWidth = width / WINDOW_SIZE
        self.cellHeight = height / WINDOW_SIZE
        self.setup = False

        root = Tk()
        canvas = Canvas(root, width=self.width, height=self.height)
        canvas.pack()
        # set up events
        root.bind("<Button-1>", lambda event:
                                self.mousePressedWrapper(event, canvas))
        root.bind("<Key>", lambda event:
                                self.keyPressedWrapper(event, canvas))
        self.redrawAll(canvas)
        self.canvas = canvas
        self.root = root
        self.setup = True

        threading.Thread(target = self.run).start()

    def setState(self, state):
        while(not self.setup): pass
        self.board, self.direction = state
        self.redrawAllWrapper(self.canvas)

    def getMove(self):
        return self.nextDirection

    def redrawAllWrapper(self, canvas):
        canvas.delete(ALL)
        canvas.create_rectangle(0, 0, self.width, self.height,
                                fill='white', width=0)
        self.redrawAll(canvas)
        canvas.update()

    def redrawAll(self, canvas):
        intToColor = {-1: 'gray', 0: 'white', 1: 'blue', 2: 'red',
                       3: 'green', 4: 'yellow', 5: 'pink', 6: 'purple',
                       7: 'brown'}
        for row in range(WINDOW_SIZE):
            for col in range(WINDOW_SIZE):
                playerInt, tailInt = self.board[row][col]
                color = (intToColor[tailInt] if tailInt > 0 else
                        intToColor[playerInt])
                cellLeft = col * self.cellWidth
                cellRight = cellLeft + self.cellWidth
                cellTop = row * self.cellHeight
                cellBot = cellTop + self.cellHeight
                canvas.create_rectangle(cellLeft, cellTop, cellRight, cellBot,
                    fill=color, width=1)

    def mousePressedWrapper(self, event, canvas):
        self.mousePressed(event)
        self.redrawAllWrapper(canvas)

    def mousePressed(self, event):
        pass

    def keyPressedWrapper(self, event, canvas):
        self.keyPressed(event)
        self.redrawAllWrapper(canvas)

    def keyPressed(self, event):
        keyToDirection = {"Up": Directions.UP, "Down": Directions.DOWN,
                          "Left": Directions.LEFT, "Right": Directions.RIGHT}
        if event.keysym in keyToDirection:
            self.nextDirection = keyToDirection[event.keysym]

    def run(self):
        try:
            self.root.mainloop()  # blocks until window is closed
        except:
            pass

def randomBoard():
    board = [[(random.randint(0, 2), random.randint(0, 2)) for _ in range(WINDOW_SIZE)]
              for _ in range(WINDOW_SIZE)]
    return board

if __name__ == "__main__":
    player = UserPlayer()
    while(True):
        board = randomBoard()
        player.setState((board, Directions.NULL))
        print(player.getMove())
        time.sleep(.1)
