
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
import copy

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


def getTrainAndTest(points, trainRatio=0.8, shuffle=True):
    if shuffle: random.shuffle(points)
    numPoints = len(points)
    numTraining = int(trainRatio * numPoints)

    return points[:numTraining], points[numTraining:]


def getLoss(outputs, targets, actions, criterion):
    indexes = actions.view(-1, 1).to(device)
    actionQValues = torch.gather(outputs, 1, indexes).to(device)
    targets = targets.to(device)

    loss = criterion(actionQValues, targets)
    return loss


def getDataLoss(NN, dataLoader, criterion):
    runningLose = 0
    count = 0
    for data in dataLoader:
        inputs, targets, actions = data

        inputs = Variable(inputs.to(device))
        count += 1

        outputs = NN(inputs)

        loss = getLoss(outputs, targets, actions, criterion)
        runningLose += loss.item()
    return runningLose / count


# trains the given nn on the given data for one epoch, then returns the average loss
def trainEpoch(NN, dataLoader, criterion, optim):
    runningLose = 0
    count = 0
    for data in dataLoader:
        inputs, targets, actions = data

        inputs = Variable(inputs.to(device))
        count += 1

        optim.zero_grad()
        outputs = NN(inputs)

        loss = getLoss(outputs, targets, actions, criterion)
        loss.backward()
        optim.step()
        runningLose += loss.item()
    return runningLose / count


def trainForNEpochs(NN, dataLoader, optim, criterion, epochs):
    assert(epochs > 0)
    trainLoss = None
    for i in range(epochs):
        trainLoss = trainEpoch(NN, dataLoader, criterion, optim)
        if verboseLevel >= 3:
            print("epoch %d training loss: %f" % (i, trainLoss))
    return trainLoss


def expandHorizon(NN, trainingData, testingData, learningRate, weightDecay, criterion, epochs):
    optim = optimizer.Adam(NN.parameters(), lr=learningRate, weight_decay=weightDecay)

    trainingLoss = getDataLoss(NN, trainingData, criterion)
    testLoss = getDataLoss(NN, testingData, criterion)
    if verboseLevel >= 2:
        print("initial training loss: %f, test loss: %f" % (trainingLoss, testLoss))

    startTime = time.time()
    trainingLoss = trainForNEpochs(NN, trainingData, optim, criterion, epochs)
    testLoss = getDataLoss(NN, testingData, criterion)
    if verboseLevel >= 2:
        print("time to expand agent horizon:", time.time() - startTime)
        print("final training loss: %f, test loss: %f\n" % (trainingLoss, testLoss))

    return trainingLoss, testLoss


def train(NN, trainingPoints, testingPoints, horizonLength, learningRate=0.001, weightDecay=0.004,
          rewardFunction=lambda x: x, saveFormat=None, saveDirectory=None, epochsPerHerizon=10):

    criterion = nn.SmoothL1Loss()

    if saveDirectory is not None and not os.path.exists(saveDirectory):
        os.makedirs(saveDirectory)

    testLoss = None

    startTime = time.time()
    for i in range(horizonLength):
        if verboseLevel >= 1:
            print("training horizon level %d" % i)
        trainingData = getDataLoader(trainingPoints, NN, discountFactor, batchSize, device, rewardFunction)
        testingData = getDataLoader(testingPoints, NN, discountFactor, batchSize, device, rewardFunction)
        _, testLoss = expandHorizon(NN, trainingData, testingData, learningRate,
                                    weightDecay, criterion, epochsPerHerizon)

        if saveFormat is not None and saveDirectory is not None and i % 5 == 0:
            saveFileName = saveFormat % i
            savePath = saveDirectory + "/" + saveFileName
            torch.save(NN.state_dict(), savePath)

    if verboseLevel >= 1:
        print("time to train:", time.time() - startTime)

    return testLoss


if __name__ == "__main__":
    print("using device", device)

    learningRate = 0.0001
    weightDecay = 0.02
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
    horizonLength = 20
    epochsPerHorizon = 20

    saveFormat = "horizon_level_%d"
    saveDirectory = "NNs"
    resultPath = "NNs/trained_NN"

    train(NN, trainingPoints, testingPoints, 150,
                     saveFormat=saveFormat, saveDirectory=saveDirectory, epochsPerHerizon=epochsPerHorizon)

    torch.save(NN.state_dict(), resultPath)