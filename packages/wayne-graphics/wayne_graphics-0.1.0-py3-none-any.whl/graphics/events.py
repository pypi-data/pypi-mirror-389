def onMousePress(canvas, func):
    canvas.bind("<Button-1>", lambda event: func(event.x, event.y))

def onMouseRelease(canvas, func):
    canvas.bind("<ButtonRelease-1>", lambda event: func(event.x, event.y))

def onMouseDrag(canvas, func):
    canvas.bind("<B1-Motion>", lambda event: func(event.x, event.y))

def onMouseMove(canvas, func):
    canvas.bind("<Motion>", lambda event: func(event.x, event.y))

def onKeyPress(root, func):
    root.bind("<KeyPress>", lambda event: func(event.char))

def onKeyRelease(root, func):
    root.bind("<KeyRelease>", lambda event: func(event.char))

def onStep(root, func, delay=33):
    def step():
        func()
        root.after(delay, step)
    root.after(delay, step)

def onMouseEnter(canvas, func):
    canvas.bind("<Enter>", lambda event: func(event.x, event.y))

def onMouseLeave(canvas, func):
    canvas.bind("<Leave>", lambda event: func(event.x, event.y))

def onRightClick(canvas, func):
    canvas.bind("<Button-3>", lambda event: func(event.x, event.y))

def onMiddleClick(canvas, func):
    canvas.bind("<Button-2>", lambda event: func(event.x, event.y))

def onScroll(canvas, func):
    canvas.bind("<MouseWheel>", lambda event: func(event.delta))

def bind(canvas_or_root, event, func):
    canvas_or_root.bind(event, func)