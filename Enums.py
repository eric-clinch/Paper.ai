
from enum import Enum

class Directions(Enum):
    NULL = 0
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4

DIRECTIONS = [Directions.UP, Directions.DOWN, Directions.LEFT, Directions.RIGHT]
DirectionToInt = {Directions.UP: 0, Directions.DOWN: 1, Directions.LEFT: 2, Directions.RIGHT: 3}
