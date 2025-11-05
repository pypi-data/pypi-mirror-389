import tkinter as tk

class WayneGraphics:
    def __init__(self, width=400, height=400, title="Wayne Graphics"):
        self.root = tk.Tk()
        self.root.title(title)
        self.canvas = tk.Canvas(self.root, width=width, height=height)
        self.canvas.pack()
        self._mouse_press_callback = None
        self._key_press_callback = None

    def onMousePress(self, func):
        self._mouse_press_callback = func
        self.canvas.bind("<Button-1>", self._handle_mouse_press)

    def onKeyPress(self, func):
        self._key_press_callback = func
        self.root.bind("<Key>", self._handle_key_press)

    def _handle_mouse_press(self, event):
        if self._mouse_press_callback:
            self._mouse_press_callback(event.x, event.y)

    def _handle_key_press(self, event):
        if self._key_press_callback:
            self._key_press_callback(event.char)

    def run(self):
        self.root.mainloop()