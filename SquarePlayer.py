from Enums import Directions
from Player import Player

class SquarePlayer(Player):
    nextDirections = {
        Directions.DOWN: Directions.RIGHT,
        Directions.RIGHT: Directions.UP,
        Directions.UP: Directions.LEFT,
        Directions.LEFT: Directions.DOWN
    }

    def __init__(self):
        self.direction = Directions.NULL

    def setState(self, state):
        (board, direction, heads, score) = state
        self.direction = direction

    def getMove(self):
        return SquarePlayer.nextDirections[self.direction]
