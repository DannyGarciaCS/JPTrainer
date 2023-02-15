# Imports
from src.classes.Button import Button

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame as pg

# Initializes dashboard scene
def boot(window, settings):

    # Scene variables
    clock = pg.time.Clock()
    ui = generateUI(window, settings)

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
        response = handleUI(window, settings, ui, position, pressed, released)
        if response != None: return response
        window.update()
        window.fill((0, 0, 0))
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

    return {
        "canvas": None,
        "buttons": [
            Button(window, (0, 0), (666, 1075), drawBackground=False),
            Button(window, (666, 0), (666, 1075), drawBackground=False),
            Button(window, (1333, 0), (666, 1075), drawBackground=False),
            Button(
                window,
                (0, 1075),
                (2000, 125),
                drawBackground=False,
                drawText=True,
                textSize=40,
                text="Start Studying",
            ),
        ],
        "images": [
            (
                pg.image.load("media/hiraganaBanner.png").convert_alpha(),
                (99, 222),
            ),
            (
                pg.image.load("media/katakanaBanner.png").convert_alpha(),
                (764, 217),
            ),
            (
                pg.image.load("media/kanjiBanner.png").convert_alpha(),
                (1458, 218),
            ),
        ],
    }

# Handles input and visualization
def handleUI(window, settings, ui, position, pressed, released):

    # Draws hiragana banner background
    if settings.get("studyHiragana"):
        linearGradient(window.display, settings.get("highBlue2"), settings.get("highBlue1"), (0, 0, 666, 1200))
    else: linearGradient(window.display, settings.get("menuGray4"), settings.get("menuGray3"), (0, 0, 666, 1200))

    # Draws katakana banner background
    if settings.get("studyKatakana"):
        linearGradient(window.display, settings.get("highYellow2"), settings.get("highYellow1"), (666, 0, 667, 1200))
    else: linearGradient(window.display, settings.get("menuGray4"), settings.get("menuGray3"), (666, 0, 667, 1200))

    # Draws kanji banner background
    if settings.get("studyKanji"):
        linearGradient(window.display, settings.get("highRed2"), settings.get("highRed1"), (1333, 0, 667, 1200))
    else: linearGradient(window.display, settings.get("menuGray4"), settings.get("menuGray3"), (1333, 0, 667, 1200))

    # Navigation menu background
    pg.draw.rect(window.display, settings.get("menuGray2"), pg.Rect(0, 1075, 2000, 125))

    # Draws images
    for image in ui["images"]:
        window.blit(image[0], image[1])

    # Updates and draws button objects
    for button in ui["buttons"]: button.update(position, pressed, released)
    return handleButtons(ui, settings)


# Handles button behavior
def handleButtons(ui, settings):

    # Hiragana button was pressed
    if ui["buttons"][0].send:
        settings.set("studyHiragana", not settings.get("studyHiragana"))
        settings.save()

    # Hiragana button was pressed
    if ui["buttons"][1].send:
        settings.set("studyKatakana", not settings.get("studyKatakana"))
        settings.save()

    # Hiragana button was pressed
    if ui["buttons"][2].send:
        settings.set("studyKanji", not settings.get("studyKanji"))
        settings.save()

    # Study button was pressed
    if ui["buttons"][3].send and (settings.get("studyHiragana") or
    settings.get("studyKatakana") or settings.get("studyKanji")):
        pg.mouse.set_system_cursor(pg.SYSTEM_CURSOR_ARROW)
        return True, "dashboard"

# Draws a linear gradient in the shape of a rect
def linearGradient(window, startColor, endColor, rect):

    # Fixes rect format
    if type(rect) in [tuple, list]:
        rect = pg.Rect(rect)

    # Draws gradient
    gradient = pg.Surface((2, 2))
    pg.draw.line(gradient, startColor, (0, 0), (0, 1))
    pg.draw.line(gradient, endColor, (1, 0), (1, 1))
    gradient = pg.transform.smoothscale(gradient, (rect.width, rect.height))

    # Blits gradient
    window.blit(gradient, rect)  

# Unlocks set of buttons
def unlockButtons(buttons):
    for button in buttons:
        button.unlock()
