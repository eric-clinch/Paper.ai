
from Player import Player
from Enums import Directions
from Game import WINDOW_SIZE
import threading

from tkinter import *

###############################################
# UI based off of 15-112 animations framework #
###############################################


# taken from http://www.cs.cmu.edu/~112/notes/notes-graphics.html
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
    green = green + greenWhiteDistance
    blue = blue + blueWhiteDistance
    return red, green, blue


def averageColors(rgb1, rgb2):
    r1, g1, b1 = rgb1
    r2, g2, b2 = rgb2
    r = (r1 + r2) // 2
    g = (g1 + g2) // 2
    b = (b1 + b2) // 2
    return r, g, b


class VisualPlayer(Player):

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

    def __init__(self, gamePlayer, width=700, height=700):
        assert(isinstance(gamePlayer, Player))
        self.gamePlayer = gamePlayer

        self.board = [[(0, 0)] * WINDOW_SIZE for _ in range(WINDOW_SIZE)]
        self.heads = []
        self.width = width
        self.height = height
        self.timerDelay = 100  # milliseconds
        self.cellWidth = width / WINDOW_SIZE
        self.cellHeight = height / WINDOW_SIZE

        root = Tk()
        canvas = Canvas(root, width=self.width, height=self.height)
        canvas.pack()
        # set up events

        self.canvas = canvas
        self.root = root

        threading.Thread(target=self.run).start()

    def setState(self, state):
        self.board, _, self.heads, _ = state
        self.redrawAllWrapper(self.canvas)
        self.gamePlayer.setState(state)

    def getMove(self):
        return self.gamePlayer.getMove()

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
                    if (playerInt > 0):
                        playerRGB = self.intToRGB[playerInt]
                        rgb = averageColors(rgb, playerRGB)
                else:
                    rgb = self.intToRGB[playerInt]
                cellLeft = col * self.cellWidth
                cellRight = cellLeft + self.cellWidth
                cellTop = row * self.cellHeight
                cellBot = cellTop + self.cellHeight
                canvas.create_rectangle(cellLeft, cellTop, cellRight, cellBot,
                    fill= rgbString(rgb), width=0)

        headRadius = 3
        for head in self.heads:
            headRow, headCol = head
            cellX = headCol * self.cellWidth + self.cellWidth / 2
            cellY = headRow * self.cellHeight + self.cellHeight / 2
            canvas.create_oval(cellX - headRadius, cellY - headRadius,
                               cellX + headRadius, cellY + headRadius, fill="black")

    def run(self):
        try:
            self.root.mainloop()  # blocks until window is closed
        except:
            pass