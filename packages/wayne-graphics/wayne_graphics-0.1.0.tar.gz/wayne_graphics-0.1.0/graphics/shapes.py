def drawRect(canvas, x, y, width, height, color="black"):
    return canvas.create_rectangle(x, y, x + width, y + height, fill=color)

def drawCircle(canvas, x, y, radius, color="black"):
    return canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=color)

def drawText(canvas, x, y, text, font=("Arial", 12), color="black"):
    return canvas.create_text(x, y, text=text, font=font, fill=color)