
import torch
from Enums import DirectionToInt
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


def getDataLoader(dataPoints, NN, gamma, batchSize, device):
    trainingData = []
    for point in dataPoints:
        nextStateValue = getNextStateValue(point, NN, device)
        Q = point.reward + gamma * nextStateValue
        gameState = torch.FloatTensor(point.stateBitboard)
        move = DirectionToInt[point.action]
        trainingData.append((gameState, nextStateValue, move))
    return torch.utils.data.DataLoader(trainingData, batch_size=batchSize, shuffle=True, num_workers=0, collate_fn=collate)
