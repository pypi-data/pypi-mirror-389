# rgbtext/core.py

class RGBText:
    def __init__(self, text: str, rgb: tuple[int, int, int] = None, truecolor: bool = False):
        self.truecolor: bool = truecolor
        self.text: str = text
        self.rgb: tuple[int, int, int] = rgb if rgb is not None else (0, 0, 0)

    @property
    def r(self): return self.rgb[0]
    @property
    def g(self): return self.rgb[1]
    @property
    def b(self): return self.rgb[2]

    @property
    def red(self): return self.r
    @property
    def green(self): return self.g
    @property
    def blue(self): return self.b

    @property
    def r_level(self): return int(self.r / 255 * 5)
    @property
    def g_level(self): return int(self.g / 255 * 5)
    @property
    def b_level(self): return int(self.b / 255 * 5)
    @property
    def red_level(self): return self.r_level
    @property
    def green_level(self): return self.g_level
    @property
    def blue_level(self): return self.b_level

    @property
    def code(self): return 16 + 36 * self.r_level + 6 * self.g_level + self.b_level

    def __repr__(self): return str(self)

    def __str__(self):
        if self.truecolor:
            return f"\033[38;2;{self.r};{self.g};{self.b}m{self.text}\033[0m"
        else:
            return f"\033[38;5;{self.code}m{self.text}\033[0m"

    @property
    def in_256color(self):
        return f"\033[38;5;{self.code}m{self.text}\033[0m"


class RGBTextFactory:
    def __init__(self, rgb: tuple[int, int, int] = None, truecolor: bool = False):
        self._template = RGBText(text="", rgb=rgb if rgb else (0, 0, 0), truecolor=truecolor)

    @property
    def r(self): return self._template.r
    @property
    def g(self): return self._template.g
    @property
    def b(self): return self._template.b
    @property
    def red(self): return self._template.red
    @property
    def green(self): return self._template.green
    @property
    def blue(self): return self._template.blue
    @property
    def r_level(self): return self._template.r_level
    @property
    def g_level(self): return self._template.g_level
    @property
    def b_level(self): return self._template.b_level
    @property
    def red_level(self): return self._template.red_level
    @property
    def green_level(self): return self._template.green_level
    @property
    def blue_level(self): return self._template.blue_level
    @property
    def code(self): return self._template.code

    def text(self, text: str) -> RGBText:
        return RGBText(text=text, rgb=self._template.rgb, truecolor=self._template.truecolor)

    def t(self, text: str) -> RGBText:
        return self.text(text)

    def text_truecolor(self, text: str) -> RGBText:
        return RGBText(text=text, rgb=self._template.rgb, truecolor=True)

    def t_truecolor(self, text: str) -> RGBText:
        return self.text_truecolor(text)