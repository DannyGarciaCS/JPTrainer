# Imports
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame as pg

# Window class
class Window:

    # Constructor
    def __init__(self, settings, title):

        pg.init()
        pg.display.set_caption(title)

        self.settings = settings
        self.screenX = settings.get("screenX")
        self.screenY = settings.get("screenY")
        self.displayX = settings.get("displayX")
        self.displayY = settings.get("displayY")

        self.aspectX = self.displayX / self.screenX
        self.aspectY = self.displayY / self.screenY

        self.updateDisplay()
        self.display = pg.Surface((self.displayX, self.displayY))

    # Updates window surfaces
    def update(self):

        self.screen.blit(pg.transform.smoothscale(self.display, (self.screenX, self.screenY)), (0, 0))
        pg.display.flip()

    # Resizes resolution shown
    def resize(self, x=-1, y=-1):

        self.settings.set("screenX", x if x > 0 else self.settings.get("screenX"))
        self.settings.set("screenY", y if y > 0 else self.settings.get("screenY"))
        self.updateDisplay()

    # Fills window
    def fill(self, color): self.display.fill(color)

    # Fills window with transparent color
    def fillTransparent(self, color):
        surface = pg.Surface((1920, 1080)).convert_alpha()
        surface.fill(color)
        self.blit(surface, (0, 0))

    # Draws on window
    def blit(self, surface, position): self.display.blit(surface, position)

    # Quits pygame
    def quit(self): pg.QUIT

    # Updates used display
    def updateDisplay(self):
            
        # Changes resolution to selection
        self.screenX, self.screenY = self.settings.get("screenX"), self.settings.get("screenY")
        self.screen = pg.display.set_mode((self.screenX, self.screenY), vsync=1)
            
        # Computes aspect ratio and resets mouse status
        self.aspectX = self.displayX / self.screenX
        self.aspectY = self.displayY / self.screenY
        pg.mouse.set_system_cursor(pg.SYSTEM_CURSOR_ARROW)
