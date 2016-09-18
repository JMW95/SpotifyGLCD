class MenuButton():
    def __init__(self, logicalpos, actualpos, callback, image):
        self.logicalpos = logicalpos
        self.pos = actualpos
        self.callback = callback
        self.image = image

    def render(self, image):
        image.paste(self.image, self.pos)

    def click(self):
        self.callback(self)
