
from Enums import Directions, DIRECTIONS
from Player import Player
import socket
import threading

def charToDirection(c):
    c = int(c)
    if c < len(DIRECTIONS):
        return DIRECTIONS[c]
    return DIRECTIONS.NULL

def getStateStr(board, heads):
    coordinateStrs = []
    for row in board:
        rowStrs = list(map(lambda c: "%d,%d" % (c[0],c[1]), row))
        coordinateStrs += rowStrs
    coordinateStr = '.'.join(coordinateStrs)

    headsStrs = list(map(lambda c: "%d,%d" % (c[0],c[1]), heads))
    headsStr = '.'.join(headsStrs)
    return coordinateStr + '/' + headsStr

class SocketPlayer(Player):

    def __init__(self, port=50000):
        host = socket.gethostbyname(socket.gethostname())
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        backlog = 4
        self.server.listen(backlog)
        print("SocketPlayer waiting to receive connection at address", host,
              "on port", port)
        self.client, address = self.server.accept()
        print("accepted connection from address", address)
        self.moveMutex = threading.Lock()
        self.move = Directions.NULL
        threading.Thread(target=self.handleClient).start()

    def handleClient(self):
        self.client.setblocking(1)
        while True:
            try:
                msg = self.client.recv(100).decode("UTF-8")
                if (len(msg) > 0):
                    moveChar = msg[-1]  # we only care about the most recent message
                    newDirection = charToDirection(moveChar)
                    self.moveMutex.acquire()
                    self.move = newDirection
                    self.moveMutex.release()
            except:
                self.moveMutex.acquire()
                self.move = Directions.NULL
                self.moveMutex.release()
                return

    def setState(self, s):
        board, _, heads = s
        str = getStateStr(board, heads) + '\n'
        str = str.encode()
        self.client.send(str)

    def getMove(self):
        self.moveMutex.acquire()
        result = self.move
        self.moveMutex.release()
        return result