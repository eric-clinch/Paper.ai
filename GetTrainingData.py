
import torch
from Enums import Directions, DirectionToInt
from torch.utils.data import Dataset


def getNextStateValue(point, DQN, device):
    if point.nextStateBitboard is None:
        return 0
    nextState = torch.FloatTensor(point.nextStateBitboard)
    nextState = nextState.unsqueeze(0).to(device)
    Qs = DQN(nextState)
    value = torch.max(Qs)
    result = value.item()
    return result


def collate(batch):
    gameStates = [elem[0] for elem in batch]
    nextStateValues = [elem[1] for elem in batch]
    moves = [elem[2] for elem in batch]
    return torch.stack(gameStates, 0), nextStateValues, moves


def rotateClockwise(L):
    rows, cols = len(L), len(L[0])
    result = [[None] * rows for _ in range(cols)]
    for row in range(rows):
        for col in range(cols):
            result[col][rows - row - 1] = L[row][col]
    return result


ROTATE_MOVE_CLOCKWISE = {Directions.UP: Directions.RIGHT, Directions.DOWN: Directions.LEFT,
                         Directions.LEFT: Directions.UP, Directions.RIGHT: Directions.DOWN}


def verticalFlip(L):
    rows, cols = len(L), len(L[0])
    result = [[None] * cols for _ in range(rows)]
    for row in range(rows):
        for col in range(cols):
            result[rows - row - 1][col] = L[row][col]
    return result


VERTICALLY_FLIP_MOVE = {Directions.UP : Directions.DOWN, Directions.DOWN : Directions.UP,
                        Directions.LEFT : Directions.LEFT, Directions.RIGHT : Directions.RIGHT}


# takes as input a gameState and a move, and returns a list of (gameState, move) pairs that are created by augmenting
# the original gameState and move.
def getAugmentedData(gameState, move):
    result = list()
    result.append((gameState, move))
    result.append((verticalFlip(gameState), VERTICALLY_FLIP_MOVE[move]))

    for _ in range(3):
        gameState = rotateClockwise(gameState)
        move = ROTATE_MOVE_CLOCKWISE[move]

        result.append((gameState, move))
        result.append((verticalFlip(gameState), VERTICALLY_FLIP_MOVE[move]))

    return result


def getDataLoader(dataPoints, NN, gamma, batchSize, device, rewardFunction=lambda x: x):
    trainingData = []
    for point in dataPoints:
        nextStateValue = getNextStateValue(point, NN, device)
        Q = torch.FloatTensor([rewardFunction(point.reward) + gamma * nextStateValue])
        gameState = torch.FloatTensor(point.stateBitboard)
        move = DirectionToInt[point.action]

        trainingData.append((gameState, Q, move))
    return torch.utils.data.DataLoader(trainingData, batch_size=batchSize, shuffle=True, num_workers=0)
