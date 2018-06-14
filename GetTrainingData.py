
# some parts of this code referenced from
# https://pytorch.org/tutorials/intermediate/reinforcement_q_learning.html

import torch
from Enums import Directions, DirectionToInt
from torch.utils.data import Dataset

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


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
    # transpose the batch (see http://stackoverflow.com/a/19343/3343043 for
    # detailed explanation).
    transposed = zip(*batch)
    states, nextStates, actions, rewards = transposed

    nonFinalMask = torch.tensor(tuple(map(lambda s: s is not None, nextStates)), device=device, dtype=torch.uint8)
    nonFinalNextStates = torch.cat([s for s in nextStates if s is not None])

    return torch.stack(states), nonFinalMask, nonFinalNextStates, torch.cat(actions), torch.cat(rewards)


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


def mapAugmentation(augmentation, bitboard):
    return list(map(augmentation, bitboard))


# takes as input a bitboard and a move, and returns a list of (bitboard, move) pairs that are created by augmenting
# the original bitboard and move.
def getAugmentedData(bitboard, move):
    result = list()
    result.append((bitboard, move))
    result.append((mapAugmentation(verticalFlip, bitboard), VERTICALLY_FLIP_MOVE[move]))

    for _ in range(3):
        bitboard = mapAugmentation(rotateClockwise, bitboard)
        move = ROTATE_MOVE_CLOCKWISE[move]

        result.append((bitboard, move))
        result.append((mapAugmentation(verticalFlip, bitboard), VERTICALLY_FLIP_MOVE[move]))

    return result


def getDataLoader(dataPoints, NN, gamma, batchSize, device, rewardFunction=lambda x: x, augment=False):
    trainingData = []
    for point in dataPoints:
        nextStateValue = getNextStateValue(point, NN, device)
        Q = torch.FloatTensor([rewardFunction(point.reward) + gamma * nextStateValue], device=device)

        gameState = point.stateBitboard
        move = point.action
        if augment:
            stateMovePairs = getAugmentedData(gameState, move)
        else:
            stateMovePairs = [(gameState, move)]

        for gameState, move in stateMovePairs:
            gameState = torch.FloatTensor(gameState, device=device)
            moveInt = DirectionToInt[move]
            trainingData.append((gameState, Q, moveInt))

    return torch.utils.data.DataLoader(trainingData, batch_size=batchSize, shuffle=True, num_workers=0)
