
# some parts of this code referenced from
# https://github.com/yunjey/pytorch-tutorial/blob/master/tutorials/02-intermediate/deep_residual_network/main.py

import torch
import torch.nn as nn
from torch.autograd import Variable
import torch.optim as optimizer
from DQN import DQN
from DataParser import DataPoint
from GetTrainingData import getDataLoader
import re
import time
import random
import os


def getDataLoss(NN, dataLoader, criterion):
    runningLose = 0
    count = 0
    for data in dataLoader:
        inputs, targetsValues, actions = data

        inputs = Variable(inputs.to(device))
        count += 1

        outputs = NN(inputs)

        loss = getLoss(outputs, targetsValues, actions, criterion)
        runningLose += loss.item()
    return runningLose / count


# def getLoss(outputs, targetsValues, actions, criterion):
#     targets = outputs.clone()
#     for i in range(len(actions)):
#         action = actions[i]
#         targets[i][action] = targetsValues[i]
#     targets = Variable(targets.to(device))
#
#     return criterion(outputs, targets)


def getLoss(outputs, targetsValues, actions, criterion):
    # indexes = torch.Tensor(actions).long()
    indexes = actions.view(-1, 1)
    actionQValues = torch.gather(outputs, 1, indexes)

    return criterion(actionQValues, targetsValues)

# trains the given nn on the given data for one epoch, then returns the average loss
def trainOneEpoch(NN, dataLoader, criterion, optim):
    runningLose = 0
    count = 0
    for data in dataLoader:
        inputs, targetsValues, actions = data

        inputs = Variable(inputs.to(device))
        count += 1

        optim.zero_grad()
        outputs = NN(inputs)

        loss = getLoss(outputs, targetsValues, actions, criterion)
        loss.backward()
        optim.step()
        runningLose += loss.item()
    return runningLose / count


def trainForNEpochs(NN, dataLoader, criterion, optim, epochs, verboseLevel):
    assert(epochs > 0)
    trainLoss = None
    for i in range(epochs):
        trainLoss = trainOneEpoch(NN, dataLoader, criterion, optim)
        if verboseLevel >= 3: print("epoch %d training loss: %f" % (i, trainLoss))
    return trainLoss


def getTrainAndTest(points, trainRatio=0.8, shuffle=True):
    if shuffle: random.shuffle(points)
    numPoints = len(points)
    numTraining = int(trainRatio * numPoints)

    return points[:numTraining], points[numTraining:]


def expandHorizon(NN, trainingData, testingData, epochs, criterion, verboseLevel=0):
    optim = optimizer.Adam(NN.parameters(), lr=learningRate, weight_decay=weightDecay)

    trainingLoss = getDataLoss(NN, trainingData, criterion)
    testLoss = getDataLoss(NN, testingData, criterion)
    if verboseLevel >= 2:
        print("initial training loss: %f, test loss: %f" % (trainingLoss, testLoss))

    startTime = time.time()
    trainingLoss = trainForNEpochs(NN, trainingData, criterion, optim, epochs, verboseLevel)
    testLoss = getDataLoss(NN, testingData, criterion)
    if verboseLevel >= 2:
        print("time to expand agent horizon:", time.time() - startTime)
        print("final training loss: %f, test loss: %f\n" % (trainingLoss, testLoss))

    return trainingLoss, testLoss


def train(NN, trainingPoints, testingPoints, horizonLength, verboseLevel=0, rewardFunction=lambda x: x,
          saveFormat=None, saveDirectory=None, epochsPerHerizon=10):

    if saveDirectory is not None and not os.path.exists(saveDirectory):
        os.makedirs(saveDirectory)

    startTime = time.time()
    criterion = nn.SmoothL1Loss()
    for i in range(horizonLength):
        if verboseLevel >= 1:
            print("training horizon level %d" % i)
        trainingData = getDataLoader(trainingPoints, NN, discountFactor, batchSize, device, rewardFunction)
        testingData = getDataLoader(testingPoints, NN, discountFactor, batchSize, device, rewardFunction)
        expandHorizon(NN, trainingData, testingData, epochsPerHerizon, criterion, verboseLevel=verboseLevel)

        if saveFormat is not None and saveDirectory is not None:
            saveFileName = saveFormat % i
            savePath = saveDirectory + "/" + saveFileName
            torch.save(NN.state_dict(), savePath)

    if verboseLevel >= 1:
        print("time to train:", time.time() - startTime)


if __name__ == "__main__":
    # device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    device = 'cpu'
    print("using device", device)

    learningRate = 0.0001
    weightDecay = 0.02
    resultPath = "NNs/clipped_trained_NN"
    verboseLevel = 3

    def rewardFunction(x):
        return 1 if x > 0 else -1 if x < 0 else 0

    NN = DQN().to(device)

    regex = re.compile("2018-05-20_data_[0-9]*.pickle")
    # regex = re.compile("2018-05-20_data_0.pickle")

    startTime = time.time()
    points = DataPoint.readData("D:/paper.ai/parsed_data", regex)
    print("time to read in data:", time.time() - startTime)
    trainingPoints, testingPoints = getTrainAndTest(points, shuffle=False)

    discountFactor = 0.95
    batchSize = 256

    saveFormat = "clipped_horizon_level_%d"
    saveDirectory = "NNs"
    train(NN, trainingPoints, testingPoints, 20, verboseLevel=verboseLevel,
                 saveFormat=saveFormat, saveDirectory=saveDirectory)

    torch.save(NN.state_dict(), resultPath)