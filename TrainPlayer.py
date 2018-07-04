
# some parts of this code referenced from
# https://github.com/yunjey/pytorch-tutorial/blob/master/tutorials/02-intermediate/deep_residual_network/main.py

import torch
import torch.nn as nn
from torch.autograd import Variable
import torch.optim as optimizer
from DQN import DQN
from DuelNetwork import DuelNetwork
from DataParser import DataPoint
from GetTrainingData import getDataLoader
import re
import time
import random
import os
import math

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

verboseLevel = 0

def getTrainAndTest(points, trainRatio=0.8, shuffle=True):
    if shuffle:
        random.shuffle(points)
    numPoints = len(points)
    numTraining = int(trainRatio * numPoints)

    return points[:numTraining], points[numTraining:]


def getLoss(outputs, targets, actions, criterion):
    indexes = actions.view(-1, 1).to(device)
    actionQValues = torch.gather(outputs, 1, indexes).to(device)
    targets = targets.to(device)

    loss = criterion(actionQValues, targets.unsqueeze(1))
    return loss


def getDataLoss(NN, dataLoader, criterion, discountFactor):
    runningLose = 0
    count = 0
    for data in dataLoader:
        count += 1
        states, nonFinalMask, nonFinalNextStates, actions, rewards = data

        states = Variable(states.to(device))
        nonFinalNextStates = nonFinalNextStates.to(device)
        rewards = rewards.to(device)

        outputs = NN(states)
        nextStateValues = torch.zeros(len(states), device=device, requires_grad=False)
        nextStateValues[nonFinalMask] = NN(nonFinalNextStates).max(1)[0].detach()

        expectedStateActionValues = (nextStateValues * discountFactor) + rewards

        loss = getLoss(outputs, expectedStateActionValues, actions, criterion)
        runningLose += loss.item()
    return runningLose / count


# trains the given nn on the given data for one epoch, then returns the average loss
def trainEpoch(NN, targetNN, dataLoader, criterion, optim, discountFactor):
    startTime = time.time()

    runningLose = 0
    count = 0
    for data in dataLoader:
        optim.zero_grad()
        count += 1
        states, nonFinalMask, nonFinalNextStates, actions, rewards = data

        states = Variable(states.to(device))
        nonFinalNextStates = nonFinalNextStates.to(device)
        rewards = rewards.to(device)

        outputs = NN(states)
        nextStateValues = torch.zeros(len(states), device=device, requires_grad=False)

        _, optimalActions = torch.max(NN(nonFinalNextStates), 1)
        optimalActions = optimalActions.view(-1, 1).to(device)
        targetQs = targetNN(nonFinalNextStates).detach()
        nextStateValues[nonFinalMask] = torch.gather(targetQs, 1, optimalActions).view(-1)

        expectedStateActionValues = (nextStateValues * discountFactor) + rewards

        loss = getLoss(outputs, expectedStateActionValues, actions, criterion)
        loss.backward()
        optim.step()
        runningLose += loss.item()
    if verboseLevel >= 2:
        print("time to train epoch: %f" % (time.time() - startTime))
    return runningLose / count


def train(NN, targetNN, trainingPoints, epochs=1, learningRate=0.001, weightDecay=0.004, batchSize=256,
          rewardFunction=lambda x: x, saveDirectory=None, saveFileName=None, targetUpdateRate=5, discountFactor=0.99,
          augmentData=False):

    criterion = nn.MSELoss()
    optim = optimizer.Adam(NN.parameters(), lr=learningRate, weight_decay=weightDecay)

    if saveDirectory is not None and not os.path.exists(saveDirectory):
        os.makedirs(saveDirectory)

    startTime = time.time()
    testLoss = None
    trainingData = getDataLoader(trainingPoints, batchSize, rewardFunction, augment=augmentData)
    if verboseLevel >= 1:
        print("time to get dataLoader: %f" % (time.time() - startTime))
        print("training on ~%d points" % (len(trainingData) * batchSize))

    startTime = time.time()
    for i in range(epochs):
        if i % targetUpdateRate == 0 and i > 0:
            print("updating targetNN")
            targetNN.load_state_dict(NN.state_dict())

        trainLoss = trainEpoch(NN, targetNN, trainingData, criterion, optim, discountFactor)
        if verboseLevel >= 1:
            print("epoch %d training loss: %f\n" % (i, trainLoss))

        if saveFileName is not None and saveDirectory is not None and i % 10 == 0:
            savePath = saveDirectory + "/" + saveFileName
            torch.save(NN.state_dict(), savePath)

    if verboseLevel >= 1:
        print("time to train:", time.time() - startTime)

    return testLoss


if __name__ == "__main__":
    print("using device=%s" % device)
    NNPath = None

    learningRate = 0.0001
    weightDecay = 0.02
    verboseLevel = 3

    def rewardFunction(x):
        return 1 if x > 0 else -1 if x < 0 else 0

    NN = DuelNetwork().to(device)
    if NNPath is not None:
        NN.load_state_dict(torch.load(NNPath))

    targetNN = DuelNetwork().to(device)
    targetNN.eval()
    targetNN.load_state_dict(NN.state_dict())

    # regex = re.compile("2018-05-20_data_[0-9]*.pickle")
    regex = re.compile("2018-05-20_data_0.pickle")

    startTime = time.time()
    points = DataPoint.readData("D:/paper.ai/parsed_data", regex)
    print("time to read in data: %f\n" % (time.time() - startTime))

    discountFactor = 0.95
    batchSize = 256
    epochs = 600
    targetUpdateRate = 10
    rewardFunction = lambda x: math.sqrt(x) if x >= 0 else -math.sqrt(abs(x))
    augmentData = True

    saveDirectory = "NNs"
    saveFileName = "trained_NN"

    train(NN, targetNN, points, epochs=epochs, saveDirectory=saveDirectory, batchSize=batchSize,
          saveFileName=saveFileName, targetUpdateRate=targetUpdateRate, rewardFunction=rewardFunction,
          augmentData=augmentData, discountFactor=discountFactor)
