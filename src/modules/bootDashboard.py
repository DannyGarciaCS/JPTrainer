# Imports
from src.classes.Canvas import Canvas
from src.classes.Button import Button
from src.classes.Slider import Slider
from src.modules.dictionary import *
from random import shuffle

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame as pg

# Initializes dashboard scene
def boot(window, settings):

    # Scene variables
    clock = pg.time.Clock()
    ui = generateUI(window, settings)

    studyCollection = []
    score = [0, 0]

    # Adds hiragana characters
    if settings.get("studyHiragana"):
        studyCollection.extend("HI" + character for character in HIRAGANA)

    # Adds katakana characters
    if settings.get("studyKatakana"):
        studyCollection.extend("KA" + character for character in KATAKANA)

    # Adds kanji characters
    if settings.get("studyKanji"):
        studyCollection.extend("N5" + character for character in N5KANJI)

    fullCollection = studyCollection.copy()
    shuffle(studyCollection)
    ui["canvas"].boostCharacter(studyCollection[0][-1])

    # Main scene loop
    while True:

        # Event handling
        position, pressed, released = getMouse(window)
        for event in pg.event.get():

            # Cross is pressed
            if event.type == pg.QUIT: return False, ""

            # Mouse button is released
            if event.type == pg.MOUSEBUTTONUP: released = event.button

        # Updates window
        response = handleUI(window, settings, ui, position, pressed, released, studyCollection, score, fullCollection)
        if response != None: return response
        window.update()
        window.fill(settings.get("menuGray2"))
        clock.tick(120)

# Refreshes mouse information
def getMouse(window):

    # Mouse position
    position = list(pg.mouse.get_pos())
    position[0] = position[0] * window.aspectX
    position[1] = position[1] * window.aspectY

    # Mouse interactivity
    pressed = pg.mouse.get_pressed()
    released = 0

    return position, pressed, released

# Generates ui elements
def generateUI(window, settings):

    ui = {

        "fontHeader": pg.font.Font("data/tsunagiGothic.ttf", 50),
        "fontSubheader": pg.font.Font("data/tsunagiGothic.ttf", 40),
        "fontBody": pg.font.Font("data/tsunagiGothic.ttf", 30),

        "canvas": Canvas(window, (100, 100), (1000, 1000)), 
        "sliders": [
            Slider(window, (1150, 625), (200, 50), initialFill=100, colorBase=(55, 55, 55),
            colorPointer=(35,135,230), colorShadow=(40,85,235), trackMargin=17, trackRadius=10,
            pointerMargin=10, pointerRadius=15),

            Slider(window, (1700, 1055), (180, 50), initialFill=90, colorBase=(55, 55, 55),
            colorPointer=(35,135,230), colorShadow=(40,85,235), trackMargin=17, trackRadius=10,
            pointerMargin=10, pointerRadius=15)
        ],
        "buttons": [
            Button(window, (1150, 325), (200, 75), colorBase=settings.get("menuGray4"),
            colorHighlight=settings.get("menuGray5"), colorClick=settings.get("menuGray3"),
            borderRadius=10, drawText=True, text="Brush", textSize=30),

            Button(window, (1150, 425), (200, 75), colorBase=settings.get("menuGray4"),
            colorHighlight=settings.get("menuGray5"), colorClick=settings.get("menuGray3"),
            borderRadius=10, drawText=True, text="Eraser", textSize=30),

            Button(window, (1150, 525), (200, 75), colorBase=settings.get("menuGray4"),
            colorHighlight=settings.get("menuGray5"), colorClick=settings.get("menuGray3"),
            borderRadius=10, drawText=True, text="Wipe", textSize=30),

            Button(window, (1150, 1025), (200, 75), colorBase=settings.get("menuGray4"),
            colorHighlight=settings.get("menuGray5"), colorClick=settings.get("menuGray3"),
            borderRadius=10, drawText=True, text="Submit", textSize=30),
        ]
    }

    ui["buttons"][0].lock = "active"
    ui["header"] = ui["fontHeader"].render("Write the Following:", True, (255, 255, 255))

    ui["settingsHeader"] = ui["fontHeader"].render("Settings:", True, (255, 255, 255))

    ui["predictionEaseSetting"] = ui["fontBody"].render("Prediction Ease:", True, (255, 255, 255))

    return ui

# Handles input and visualization
def handleUI(window, settings, ui, position, pressed, released, studyCollection, score, fullCollection):

    window.blit(ui["header"], (1440, 100))
    target = studyCollection[0][-1]

    # Determines character to be written
    if target in HIRAGANA: predictionMessage = "Hiragana: " + KANA_MAP[HIRAGANA.index(target)].capitalize()
    elif target in KATAKANA: predictionMessage = "Katakana: " + KANA_MAP[KATAKANA.index(target)].capitalize()
    elif target in N5KANJI: predictionMessage = "N5 Kanji: " + N5KANJI_MAP[N5KANJI.index(target)].capitalize().split(",")[0]

    # Prints statistics
    window.blit(ui["fontSubheader"].render(predictionMessage, True, (255, 255, 255)), (1440, 160))
    window.blit(ui["fontBody"].render(f"Correct: {score[0]}", True, (255, 255, 255)), (1440, 220))
    window.blit(ui["fontBody"].render(f"Incorrect: {score[1]}", True, (255, 255, 255)), (1440, 250))

    seenCount = len(fullCollection)-len(studyCollection)
    window.blit(ui["fontBody"].render(
    f"Accuracy: {score[0]/seenCount*100 if seenCount > 0 else 100:.02f}%", True, (255, 255, 255)), (1440, 280))

    window.blit(ui["settingsHeader"], (1440, 980))
    window.blit(ui["predictionEaseSetting"], (1440, 1060))

    # Updates and draws button objects
    for button in ui["buttons"]: button.update(position, pressed, released)
    for slider in ui["sliders"]: slider.update(position, pressed, released)
    
    # Updates and draws canvas objects
    ui["canvas"].update(position, pressed)

    return handleInput(ui, studyCollection, score, fullCollection)

# Handles button behavior
def handleInput(ui, studyCollection, score, fullCollection):

    # Brush button
    if ui["buttons"][0].send:
        unlockButtons(ui["buttons"])
        ui["buttons"][0].lock = "active"
        ui["canvas"].brushColor = (0, 0, 0)

    # Eraser button
    if ui["buttons"][1].send:
        unlockButtons(ui["buttons"])
        ui["buttons"][1].lock = "active"
        ui["canvas"].brushColor = ui["canvas"].backgroundColor

    # Wipe button
    if ui["buttons"][2].send:
        ui["canvas"].wipeCanvas()

    # Submit button
    if ui["buttons"][3].send and ui["canvas"].prediction != "":

        # Determines validity of prediction
        if ui["canvas"].prediction == studyCollection[0][-1]: score[0] += 1
        else: score[1] += 1

        # Resets collection if empty
        studyCollection.append(studyCollection.pop(0))
        ui["canvas"].boostCharacter(studyCollection[0][-1])
        ui["canvas"].wipeCanvas()

    # Brush size slider
    if ui["sliders"][0].changed:
        ui["canvas"].brushSize = int(20 + 60 * ui["sliders"][0].percent)
    
    # Prediction ease slider
    if ui["sliders"][1].changed:
        ui["canvas"].boostMagnitude = 0.4 * ui["sliders"][0].percent

# Unlocks set of buttons
def unlockButtons(buttons):
    for button in buttons:
        button.unlock()
