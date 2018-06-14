
# convolution block and residual block architecture taken from AlphaZero residual tower architecture

import torch.nn as nn
from Game import WINDOW_SIZE


class ConvBlock(nn.Module):
    def __init__(self, inChannels, outChannels):
        super(ConvBlock, self).__init__()
        self.conv = nn.Conv2d(inChannels, outChannels, 3, stride=1, padding=1)
        self.bn = nn.BatchNorm2d(outChannels)
        self.relu = nn.ReLU()
        
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def forward(self, x):
        return self.relu(self.bn(self.conv(x)))


class ResidualBlock(nn.Module):
    def __init__(self, inChannels, outChannels, downsample, stride):
        super(ResidualBlock, self).__init__()
        self.conv1 = nn.Conv2d(inChannels, outChannels, 3, stride=stride, padding=1)
        self.bn1 = nn.BatchNorm2d(outChannels)
        self.conv2 = nn.Conv2d(outChannels, outChannels, 3, stride=1, padding=1)
        self.bn2 = nn.BatchNorm2d(outChannels)

        self.downsample = downsample
        self.relu = nn.ReLU()

        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def forward(self, x):
        residual = x
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.bn2(self.conv2(x))
        if self.downsample is not None:
            residual = self.downsample(residual)
        x += residual
        return self.relu(x)


class DQN(nn.Module):
    def __init__(self):
        super(DQN, self).__init__()
        self.inChannels = 6

        self.conv = self.makeConvLayer(32)
        self.res1 = self.makeResidualBlock(32)
        self.res2 = self.makeResidualBlock(32)
        self.res3 = self.makeResidualBlock(32)
        self.res4 = self.makeResidualBlock(16)
        self.fc = nn.Linear(WINDOW_SIZE * WINDOW_SIZE * self.inChannels, 4)

    def makeConvLayer(self, outChannels):
        result = ConvBlock(self.inChannels, outChannels)
        self.inChannels = outChannels
        return result

    def makeResidualBlock(self, outChannels, stride=1):
        downsample = None
        if self.inChannels != outChannels or stride != 1:
            downsample = nn.Sequential(
                nn.Conv2d(self.inChannels, outChannels, kernel_size=3, stride=stride, padding=1),
                nn.BatchNorm2d(outChannels)
            )
        result = ResidualBlock(self.inChannels, outChannels, downsample, stride)
        self.inChannels = outChannels
        return result

    def forward(self, x):
        x = self.conv(x)
        x = self.res1(x)
        x = self.res2(x)
        x = self.res3(x)
        x = self.res4(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x
