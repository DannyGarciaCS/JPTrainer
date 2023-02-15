# Imports
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame as pg

# Slider class
class Slider:

    # Constructor
    def __init__(self, window, position, size, initialFill=0, **kwargs):

        # Builds most constructor arguments
        self.reconstruct(window, position, size, kwargs, initialFill)

        # Non real-time arguments
        self.positionComparator = self.position
        self.sizeComparator = self.size
        self.queueComparator = True
        self.status = "base"
    
    # Updates button's status
    def update(self, position, pressed, released):

        # Slider is being hovered
        self.last = self.fill
        if self.positionComparator[0] < position[0] < self.positionComparator[0] + self.sizeComparator[0] and \
        self.positionComparator[1] < position[1] < self.positionComparator[1] + self.sizeComparator[1]:

            pg.mouse.set_system_cursor(pg.SYSTEM_CURSOR_HAND)
            self.hovering = True

            # Defines button visuals
            if pressed[0] and not self.lastHeld: self.status = "held"

            # We want to update the comparator
            if self.queueComparator:
                self.positionComparator = self.position
                self.sizeComparator = self.size
                self.queueComparator = False

            # Slider is no longer held
            if released == 1:
                self.status = "base"
                self.positionComparator = self.position
                self.sizeComparator = self.size
                self.queueComparator = True

        # Slider stopped being hovered
        elif self.hovering:

            pg.mouse.set_system_cursor(pg.SYSTEM_CURSOR_ARROW)
            self.hovering = False
            if released == 1: self.status = "base"

        # Slider was released
        elif released == 1:
            self.status = "base"
            self.positionComparator = self.position
            self.sizeComparator = self.size
            self.queueComparator = True

        # Updates status
        if self.status == "held":
            self.fill = max(min(position[0] - self.positionComparator[0], self.sizeComparator[0]), 0)
            self.percent = self.fill / self.sizeComparator[0]
        if self.fill != self.last: self.changed = True
        self.lastHeld = pressed[0]

        self.draw()

    # Draws Slider's status
    def draw(self):

        # Draws track
        pg.draw.rect(self.window.display, self.visuals["colorBase"],
        pg.Rect(self.position[0], self.position[1] + self.visuals["trackMargin"], self.size[0],
        self.size[1] - self.visuals["trackMargin"] * 2), border_radius=self.visuals["trackRadius"])

        # Displays comparator position for debugging
        if self.visuals["debugComparator"]:
            pg.draw.rect(self.window.display, (0, 0, 255), pg.Rect(self.positionComparator[0],
            self.positionComparator[1], self.sizeComparator[0], self.sizeComparator[1]), 1)

        # Draws track shadow
        pg.draw.rect(self.window.display, self.visuals["colorShadow"],
        pg.Rect(self.position[0], self.position[1] + self.visuals["trackMargin"], self.percent * self.size[0],
        self.size[1] - self.visuals["trackMargin"] * 2), border_radius=self.visuals["trackRadius"])

        # Draws pointer
        pg.draw.rect(self.window.display, self.visuals["colorPointer"],
        pg.Rect(self.position[0] + self.percent * self.size[0] + self.visuals["pointerMargin"] - self.size[1] / 2,
        self.position[1] + self.visuals["pointerMargin"],
        self.size[1] - self.visuals["pointerMargin"] * 2, self.size[1] - self.visuals["pointerMargin"] * 2),
        border_radius=self.visuals["pointerRadius"])

    # Handles constructor arguments for real-time changes
    def reconstruct(self, window, position, size, kwargs, initialFill=0):

        # Passed arguments
        self.window = window
        self.position = position
        self.size = size

        # Implied arguments
        self.hovering = False
        self.fill = initialFill
        self.percent = initialFill / size[0]
        self.lastHeld = False
        self.changed = False

        # Default visual arguments
        self.visuals = {
            "colorBase": (50, 50, 52),
            "colorPointer": (35, 110, 230),
            "colorShadow": (35, 80, 200),
            "drawBorder": False,
            "borderWidth": 1,
            "borderColor": (0, 0, 0),

            "trackMargin": 0,
            "trackRadius": 0,
            "pointerMargin": 0,
            "pointerRadius": 0,

            "debugComparator": False
        }

        # Replaces all passed visual arguments
        for key in kwargs.keys():
            if key in self.visuals:
                self.visuals[key] = kwargs[key]
