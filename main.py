from UserPlayer import UserPlayer
from Game import Game

players = [UserPlayer(),
           UserPlayer(upKey = "w", downKey = "s",
                      leftKey = "a", rightKey = "d")
          ]
game = Game(100, players)

game.run()
