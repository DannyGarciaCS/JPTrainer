# Imports
import time
import threading
from tensorflow import keras
import matplotlib.pyplot as plt
import numpy as np
from src.modules.dictionary import *

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame as pg

# Button class
class Canvas:

    # Constructor
    def __init__(self, window, position, size):

        # Passed arguments
        self.window = window
        self.position = position
        self.size = size
        self.backgroundColor = (255, 255, 255)
        self.guideColor = (255, 0, 0)

        # Implied
        self.brushColor = (0, 0, 0)
        self.brushSize = 40
        self.canvas = pg.Surface(self.size).convert()
        self.canvas.fill(self.backgroundColor)

        # Drawing variables
        self.held = False
        self.previous = (-1, -1)
        self.timer = None
        self.refreshRate = 0.01

        self.preview = pg.Surface((200, 200)).convert()
        self.preview.fill(self.backgroundColor)

        self.kanaModel = None
        self.n5Model = None
        self.predictions = []
        self.predictionThread = threading.Thread(target=self.loadModels)
        self.predictionThread.start()
        self.prediction = ""

        self.boostIndex = None
        self.boostSuite = ""
        self.boostMagnitude = 0.2

        self.predictionFont = pg.font.Font("data/tsunagiGothic.ttf", 130)
        self.predictionRender = None
    
    # Loads used models
    def loadModels(self):
        self.kanaModel = keras.models.load_model("model/hkModel")
        self.n5Model = keras.models.load_model("model/n5Model")

    # Updates button's status
    def update(self, position, pressed):

        drawing = False

        # User is drawing in canvas
        if self.position[0] <= position[0] <= self.position[0] + self.size[0] and \
        self.position[1] <= position[1] <= self.position[1] + self.size[1] and pressed[0]:

            if self.held == False:
                drawing = True

                # Starts canvas status
                self.held = True
                self.previous = position
                self.timer = time.time()

        # Stopped holding
        elif self.held:

            # Draws end of line
            drawing = True

            # Resets canvas status
            self.held = False
            self.previous = (-1, -1)
            self.timer = None

        # Drawing link
        if self.held and time.time() - self.timer >= self.refreshRate:

            # Draws body of line
            start = (self.previous[0] - self.position[0], self.previous[1] - self.position[1])
            end = (position[0] - self.position[0], position[1] - self.position[1])
            self.connect(start, end)
            
            # Updates canvas status
            self.held = True
            self.previous = position
            self.timer = time.time()
            drawing = True
        
        if drawing: self.handlePrediction()
        self.draw(position)
    
    # Draws a smooth line composed of circles
    def connect(self, start, end):

        # Draws endpoints 
        pg.draw.circle(self.canvas, self.brushColor, start, int(self.brushSize / 2.2))
        pg.draw.circle(self.canvas, self.brushColor, end, int(self.brushSize / 2.2))
        pg.draw.line(self.canvas, self.brushColor, start, end, self.brushSize)

    # Draws canvas status
    def draw(self, position):

        # Draws canvas
        self.window.blit(self.canvas, self.position)

        # Draws vertical guides
        for vGuide in range(2):
            pg.draw.line(self.window.display, self.guideColor, (self.position[0] + self.size[0] / 3 * (vGuide + 1),
            self.position[1]), (self.position[0] + self.size[0] / 3 * (vGuide + 1), self.position[1] + self.size[1]), 2)

        # Draws horizontal guides
        for hGuide in range(2):
            pg.draw.line(self.window.display, self.guideColor, (self.position[0],
            self.position[1] + self.size[1] / 3 * (hGuide + 1)), (self.position[0] + \
                self.size[0], self.position[1] + self.size[1] / 3 * (hGuide + 1)), 2)

        # Draws preview
        self.window.blit(self.preview, (self.position[0] + self.size[0] + 50, self.position[1]))

        # Draws predictions
        pg.draw.rect(self.window.display, self.backgroundColor,
        (self.position[0] + self.size[0] + 50, self.position[1] + 700, 200, 200))

        if self.prediction != "":
            self.window.blit(self.predictionRender,
            (self.position[0] + self.size[0] + 85, self.position[1] + 735))
        
        # Draws brush size guide
        pg.draw.circle(self.window.display, (255, 0, 0), position, self.brushSize / 2, 4)

    # Resets canvas
    def wipeCanvas(self):
        self.canvas.fill(self.backgroundColor)
        self.preview.fill(self.backgroundColor)
        self.prediction = ""

    # Handles predictions of canvas
    def handlePrediction(self):

        # Generates preview
        sample = []
        target = pg.transform.smoothscale(self.canvas, (50, 50))
        for row in range(50):
            for col in range(50):
                sample.append(min(target.get_at((col, row))) / 255)
        sample = np.array(sample)

        # Makes predictions
        if self.kanaModel is not None and self.n5Model is not None:
            if not self.predictionThread.isAlive():
                self.predictionThread = threading.Thread(
                target=self.makePredictions, args=(sample.reshape(1, 50, 50, 1), ))
                self.predictionThread.start()

        self.preview = pg.transform.scale(target, (200, 200))
        
    # Makes predictions
    def makePredictions(self, data):

        kanaPrediction = self.kanaModel.predict(data, verbose=0)
        n5Prediction = self.n5Model.predict(data, verbose=0)

        if self.boostSuite == "kana":
            kanaPrediction[0][self.boostIndex] += self.boostMagnitude
        
        elif self.boostSuite == "n5":
            n5Prediction[0][self.boostIndex] += self.boostMagnitude
        
        kanaPredictionHighest = max(list(kanaPrediction[0])) if not \
        self.boostSuite == "kana" else max(list(kanaPrediction[0])) + self.boostMagnitude / 2
        n5PredictionHighest = max(list(n5Prediction[0])) if not self.boostSuite == "n5" else \
        max(list(kanaPrediction[0])) + self.boostMagnitude / 2

        kana = HIRAGANA + KATAKANA

        if kanaPredictionHighest > n5PredictionHighest:
            self.prediction = kana[kanaPrediction.argmax()]
        else: self.prediction = N5KANJI[n5Prediction.argmax()]

        self.predictionRender = self.predictionFont.render(self.prediction, True, (0, 0, 0))
    
    # Boosts the confidence in correct value to give user benefit of the doubt
    def boostCharacter(self, character):

        KANA = HIRAGANA + KATAKANA

        # Boosting kana character
        if character in KANA:
            self.boostIndex = KANA.index(character)
            self.boostSuite = "kana"
        
        # Boosting kanji character
        elif character in N5KANJI:
            self.boostIndex = N5KANJI.index(character)
            self.boostSuite = "n5"
