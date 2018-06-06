
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


def getTrainAndTest(points, trainRatio=0.8, shuffle=True):
    if shuffle: random.shuffle(points)
    numPoints = len(points)
    numTraining = int(trainRatio * numPoints)

    return points[:numTraining], points[numTraining:]


def getLoss(outputs, targets, actions):
    indexes = actions.view(-1, 1)
    actionQValues = torch.gather(outputs, 1, indexes)

    loss = criterion(actionQValues, targets)
    return loss


def getDataLoss(NN, dataLoader):
    runningLose = 0
    count = 0
    for data in dataLoader:
        inputs, targest, actions = data

        inputs = Variable(inputs.to(device))
        count += 1

        outputs = NN(inputs)

        loss = getLoss(outputs, targest, actions)
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

        loss = getLoss(outputs, targets, actions)
        loss.backward()
        optim.step()
        runningLose += loss.item()
    return runningLose / count


def trainForNEpochs(NN, dataLoader, optim, epochs):
    assert(epochs > 0)
    trainLoss = None
    for i in range(epochs):
        trainLoss = trainEpoch(NN, dataLoader, criterion, optim)
        if verboseLevel >= 3:
            print("epoch %d training loss: %f" % (i, trainLoss))
    return trainLoss


def expandHorizon(NN, trainingData, testingData, epochs):
    optim = optimizer.Adam(NN.parameters(), lr=learningRate, weight_decay=weightDecay)

    trainingLoss = getDataLoss(NN, trainingData)
    testLoss = getDataLoss(NN, testingData)
    if verboseLevel >= 2:
        print("initial training loss: %f, test loss: %f" % (trainingLoss, testLoss))

    startTime = time.time()
    trainingLoss = trainForNEpochs(NN, trainingData, optim, epochs)
    testLoss = getDataLoss(NN, testingData)
    if verboseLevel >= 2:
        print("time to expand agent horizon:", time.time() - startTime)
        print("final training loss: %f, test loss: %f\n" % (trainingLoss, testLoss))

    return trainingLoss, testLoss


def train(NN, trainingPoints, testingPoints, horizonLength, rewardFunction=lambda x: x,
          saveFormat=None, saveDirectory=None, epochsPerHerizon=10):

    if saveDirectory is not None and not os.path.exists(saveDirectory):
        os.makedirs(saveDirectory)

    startTime = time.time()
    for i in range(horizonLength):
        if verboseLevel >= 1:
            print("training horizon level %d" % i)
        trainingData = getDataLoader(trainingPoints, NN, discountFactor, batchSize, device, rewardFunction)
        testingData = getDataLoader(testingPoints, NN, discountFactor, batchSize, device, rewardFunction)
        expandHorizon(NN, trainingData, testingData, epochsPerHerizon)

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
    criterion = nn.MSELoss()

    def rewardFunction(x):
        return 1 if x > 0 else -1 if x < 0 else 0

    NN = DQN().to(device)

    # regex = re.compile("2018-05-20_data_[0-9]*.pickle")
    regex = re.compile("2018-05-20_data_0.pickle")

    startTime = time.time()
    points = DataPoint.readData("D:/paper.ai/parsed_data", regex)
    print("time to read in data:", time.time() - startTime)
    trainingPoints, testingPoints = getTrainAndTest(points, shuffle=False)

    discountFactor = 0.95
    batchSize = 1

    saveFormat = "clipped_horizon_level_%d"
    saveDirectory = "NNs"
    train(NN, trainingPoints, testingPoints, 20, saveFormat=None, saveDirectory=saveDirectory,
          rewardFunction=rewardFunction)

    torch.save(NN.state_dict(), resultPath)