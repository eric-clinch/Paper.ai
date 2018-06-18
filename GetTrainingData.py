
# some parts of this code referenced from
# https://pytorch.org/tutorials/intermediate/reinforcement_q_learning.html

import torch
from Enums import Directions, DirectionToInt
from torch.utils.data import Dataset

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


def getPartitions(L, partitionSize):
    res = []
    for i in range(0, len(L), partitionSize):
        partition = L[i:i + partitionSize]
        res.append(partition)
    return res


def rotateClockwise(L):
    if L is None:
        return None

    rows, cols = len(L), len(L[0])
    result = [[None] * rows for _ in range(cols)]
    for row in range(rows):
        for col in range(cols):
            result[col][rows - row - 1] = L[row][col]
    return result


ROTATE_MOVE_CLOCKWISE = {Directions.UP: Directions.RIGHT, Directions.DOWN: Directions.LEFT,
                         Directions.LEFT: Directions.UP, Directions.RIGHT: Directions.DOWN}


def verticalFlip(L):
    if L is None:
        return None

    rows, cols = len(L), len(L[0])
    result = [[None] * cols for _ in range(rows)]
    for row in range(rows):
        for col in range(cols):
            result[rows - row - 1][col] = L[row][col]
    return result


VERTICALLY_FLIP_MOVE = {Directions.UP: Directions.DOWN, Directions.DOWN: Directions.UP,
                        Directions.LEFT: Directions.LEFT, Directions.RIGHT: Directions.RIGHT}


def mapAugmentation(augmentation, bitboard):
    return list(map(augmentation, bitboard)) if bitboard is not None else None


# takes as input a bitboard and a move, and returns a list of (bitboard, move) pairs that are created by augmenting
# the original bitboard and move.
def getAugmentedData(bitboard, nextStateBitboard, move, verticalAugment=False):
    result = list()
    result.append((bitboard, nextStateBitboard, move))
    if verticalAugment:
        result.append((mapAugmentation(verticalFlip, bitboard), mapAugmentation(verticalFlip, nextStateBitboard),
                       VERTICALLY_FLIP_MOVE[move]))

    for _ in range(3):
        bitboard = mapAugmentation(rotateClockwise, bitboard)
        nextStateBitboard = mapAugmentation(rotateClockwise, nextStateBitboard)
        move = ROTATE_MOVE_CLOCKWISE[move]

        result.append((bitboard, nextStateBitboard, move))
        if verticalAugment:
            result.append((mapAugmentation(verticalFlip, bitboard), mapAugmentation(verticalFlip, nextStateBitboard),
                           VERTICALLY_FLIP_MOVE[move]))

    return result


def collate(batch):
    # transpose the batch (see http://stackoverflow.com/a/19343/3343043 for
    # detailed explanation).
    transposed = tuple(zip(*batch))

    states, nextStates, actions, rewards = transposed

    nonFinalMask = torch.ByteTensor(tuple(map(lambda s: s is not None, nextStates)))
    nonFinalNextStates = torch.stack([s for s in nextStates if s is not None])

    return (torch.stack(states),
            nonFinalMask, nonFinalNextStates,
            torch.cat(actions),
            torch.cat(rewards))


def getDataLoader(dataPoints, batchSize, rewardFunction=lambda x: x, augment=False):

    trainintData = []
    for point in dataPoints:

        gameState = point.stateBitboard
        action = point.action
        nextGameState = point.nextStateBitboard if point.nextStateBitboard is not None else None

        if augment:
            stateMovePairs = getAugmentedData(gameState, nextGameState, action)
        else:
            stateMovePairs = [(gameState, nextGameState, action)]

        reward = torch.Tensor([rewardFunction(point.reward)])

        for state, nextState, action in stateMovePairs:
            state = torch.Tensor(state)
            nextState = torch.Tensor(nextState) if nextState is not None else None
            action = torch.LongTensor([DirectionToInt[action]])
            trainintData.append((state, nextState, action, reward))

    return torch.utils.data.DataLoader(trainintData, batch_size=batchSize, shuffle=True, num_workers=0,
                                       collate_fn=collate, pin_memory=True)
