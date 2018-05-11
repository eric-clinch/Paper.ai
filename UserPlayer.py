
from Player import Player
from Enums import Directions
import time
import random
WINDOW_SIZE = 51
# from Game import WINDOW_SIZE
import threading

from tkinter import *

###############################################
# UI based off of 15-112 animations framework #
###############################################

#taken from http://www.cs.cmu.edu/~112/notes/notes-graphics.html
def rgbString(rgb):
    red, green, blue = rgb
    return "#%02x%02x%02x" % (red, green, blue)

def makeLight(rgb):
    red, green, blue = rgb
    redWhiteDistance = 255 - red
    greenWhiteDistance = 255 - green
    blueWhiteDistance = 255 - blue

    redWhiteDistance //= 2
    greenWhiteDistance //= 2
    blueWhiteDistance //= 2

    red = red + redWhiteDistance
    green = 255 - greenWhiteDistance
    blue = 255 - blueWhiteDistance
    return (red, green, blue)

class UserPlayer(Player):

    intToRGB = {-1: (169, 169, 169), # gray
                0: (255, 255, 255), # white
                1: (0, 0, 255), # blue
                2: (255, 0, 0), # red
                3: (0, 255, 0), # green
                4: (255, 255, 0), # yellow
                5: (255, 20, 147), # pink
                6: (160, 32, 240), # purple
                7: (32, 21, 11) # brown
                }

    def __init__(self, upKey="Up", downKey="Down", leftKey="Left",
                       rightKey="Right", width=700, height=700):
        self.board = [[(0, 0)] * WINDOW_SIZE for _ in range(WINDOW_SIZE)]
        self.direction = Directions.UP
        self.nextDirection = Directions.NULL
        self.width = width
        self.height = height
        self.cellWidth = width / WINDOW_SIZE
        self.cellHeight = height / WINDOW_SIZE
        self.keyToDirection = {upKey: Directions.UP, downKey: Directions.DOWN,
                          leftKey: Directions.LEFT, rightKey: Directions.RIGHT}

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

        threading.Thread(target = self.run).start()

    def setState(self, state):
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
        for row in range(WINDOW_SIZE):
            for col in range(WINDOW_SIZE):
                playerInt, tailInt = self.board[row][col]
                if (tailInt > 0):
                    rgb = self.intToRGB[tailInt]
                    rgb = makeLight(rgb)
                else:
                    rgb = self.intToRGB[playerInt]
                cellLeft = col * self.cellWidth
                cellRight = cellLeft + self.cellWidth
                cellTop = row * self.cellHeight
                cellBot = cellTop + self.cellHeight
                canvas.create_rectangle(cellLeft, cellTop, cellRight, cellBot,
                    fill= rgbString(rgb), width=1)

    def mousePressedWrapper(self, event, canvas):
        self.mousePressed(event)
        self.redrawAllWrapper(canvas)

    def mousePressed(self, event):
        pass

    def keyPressedWrapper(self, event, canvas):
        self.keyPressed(event)
        self.redrawAllWrapper(canvas)

    def keyPressed(self, event):
        if event.keysym in self.keyToDirection:
            self.nextDirection = self.keyToDirection[event.keysym]

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
    player = UserPlayer(upKey='w', downKey='s', leftKey='a', rightKey='d')
    while(True):
        board = randomBoard()
        player.setState((board, Directions.NULL))
        print(player.getMove())
        time.sleep(.1)
