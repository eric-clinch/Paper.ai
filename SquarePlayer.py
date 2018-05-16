from Enums import Directions

class SquarePlayer(object):
    nextDirections = {
        Directions.DOWN: Directions.RIGHT,
        Directions.RIGHT: Directions.UP,
        Directions.UP: Directions.LEFT,
        Directions.LEFT: Directions.DOWN
    }

    def __init__(self):
        self.direction = Directions.NULL

    def setState(self, state):
        (board, direction, heads) = state
        self.direction = direction

    def getMove(self):
        return SquarePlayer.nextDirections[self.direction]
