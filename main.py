from UserPlayer import UserPlayer
from SocketPlayer import SocketPlayer
from Game import Game

players = [UserPlayer(), SocketPlayer()]
game = Game(100, players)

game.run()
