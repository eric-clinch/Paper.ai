
from tkinter import *
from Enums import Directions, DIRECTIONS
from Game import WINDOW_SIZE
import threading
import socket

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
    green = 255 - greenWhiteDistance
    blue = 255 - blueWhiteDistance
    return red, green, blue


def getServerInfo(data):
    data.host = input("what is the host address? ")
    data.port = int(input("what is the host port? "))

def initDicts(data):
    data.intToRGB = {-1: (169, 169, 169),  # gray
                0: (255, 255, 255),  # white
                1: (0, 0, 255),  # blue
                2: (255, 0, 0),  # red
                3: (0, 255, 0),  # green
                4: (255, 255, 0),  # yellow
                5: (255, 20, 147),  # pink
                6: (160, 32, 240),  # purple
                7: (32, 21, 11)  # brown
                }
    keyToDirection = {"Up": Directions.UP, "Down": Directions.DOWN,
                      "Left": Directions.LEFT, "Right": Directions.RIGHT}
    data.keyToDirectionChar = dict()
    for key in keyToDirection:
        directionIndex = DIRECTIONS.index(keyToDirection[key])
        data.keyToDirectionChar[key] = str(directionIndex)


def parseState(stateStr):
    pass


def handleServer(data):
    data.server.setblocking(1)
    msg = ""
    while True:
        msg += data.server.recv(100).decode("UTF-8")
        if "\n" in msg:
            messages = msg.split("\n")  # we only care about the last message
            stateStr = messages[-2]  # get the last completed state
            msg = messages[-1]
            data.board = eval(stateStr)

def init(data):
    initDicts(data)
    data.board = [[(0, 0)] * WINDOW_SIZE for _ in range(WINDOW_SIZE)]
    data.direction = Directions.UP
    data.nextDirection = Directions.NULL
    data.cellWidth = data.width / WINDOW_SIZE
    data.cellHeight = data.height / WINDOW_SIZE

    getServerInfo(data)
    data.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("attempting to connect to server at address", data.host,
          "on port", data.port)
    data.server.connect((data.host, data.port))
    print("connected to server")
    threading.Thread(target=handleServer, args=(data,)).start()


def mousePressed(event, data):
    pass


def keyPressed(event, data):
    if event.keysym in data.keyToDirectionChar:
        directionChar = data.keyToDirectionChar[event.keysym]
        data.server.send(directionChar.encode())


def redrawAll(canvas, data):
    for row in range(WINDOW_SIZE):
        for col in range(WINDOW_SIZE):
            playerInt, tailInt = data.board[row][col]
            if (tailInt > 0):
                rgb = data.intToRGB[tailInt]
                rgb = makeLight(rgb)
            else:
                rgb = data.intToRGB[playerInt]
            cellLeft = col * data.cellWidth
            cellRight = cellLeft + data.cellWidth
            cellTop = row * data.cellHeight
            cellBot = cellTop + data.cellHeight
            canvas.create_rectangle(cellLeft, cellTop, cellRight, cellBot,
                                    fill=rgbString(rgb), width=0)

    xCenter = data.width / 2
    yCenter = data.height / 2
    radius = 3
    canvas.create_oval(xCenter - radius, yCenter - radius,
                       xCenter + radius, yCenter + radius, fill="black")

def timerFired(data):
    pass

####################################
# use the run function as-is
####################################

def run(width=300, height=300):
    def redrawAllWrapper(canvas, data):
        canvas.delete(ALL)
        canvas.create_rectangle(0, 0, data.width, data.height,
                                fill='white', width=0)
        redrawAll(canvas, data)
        canvas.update()

    def mousePressedWrapper(event, canvas, data):
        mousePressed(event, data)
        redrawAllWrapper(canvas, data)

    def keyPressedWrapper(event, canvas, data):
        keyPressed(event, data)
        redrawAllWrapper(canvas, data)

    def timerFiredWrapper(canvas, data):
        timerFired(data)
        redrawAllWrapper(canvas, data)
        # pause, then call timerFired again
        canvas.after(data.timerDelay, timerFiredWrapper, canvas, data)
    # Set up data and call init
    class Struct(object): pass
    data = Struct()
    data.width = width
    data.height = height
    data.timerDelay = 100 # milliseconds
    root = Tk()
    init(data)
    # create the root and the canvas
    canvas = Canvas(root, width=data.width, height=data.height)
    canvas.pack()
    # set up events
    root.bind("<Button-1>", lambda event:
                            mousePressedWrapper(event, canvas, data))
    root.bind("<Key>", lambda event:
                            keyPressedWrapper(event, canvas, data))
    timerFiredWrapper(canvas, data)
    # and launch the app
    root.mainloop()  # blocks until window is closed
    print("bye!")


if __name__ == "__main__":
    run(700, 700)