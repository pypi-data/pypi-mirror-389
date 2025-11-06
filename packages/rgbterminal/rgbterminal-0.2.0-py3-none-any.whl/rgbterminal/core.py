import numpy as np
import colorsys

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
        if not self.text:
            return ""
        
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
    @property
    def in_256color(self):
        return self._template.in_256color


    def text(self, text: str, rgb: tuple[int, int, int] = None, truecolor: bool = None) -> RGBText:
        color = rgb if rgb is not None else self._template.rgb
        tc = truecolor if truecolor is not None else self._template.truecolor
        
        return RGBText(text=text, rgb=color, truecolor=tc)

    def t(self, text: str) -> RGBText:
        return self.text(text)

    def t_truecolor(self, text: str) -> RGBText:
        return self.text_truecolor(text)
    
class GradientText:
    def __init__(self, text: str, rgb_stops: list[tuple[int,int,int]], truecolor: bool = False):
        self.text = text
        self.rgb_stops = rgb_stops
        self.truecolor = truecolor

    def __str__(self):
        if not self.text:
            return ""

        n = len(self.text)
        num_stops = len(self.rgb_stops)
        stop_indices = np.linspace(0, n-1, num=num_stops, dtype=int)

        hls_stops = [colorsys.rgb_to_hls(r/255, g/255, b/255) for r,g,b in self.rgb_stops]

        hs, ls, ss = np.zeros(n), np.zeros(n), np.zeros(n)

        for i in range(num_stops - 1):
            start_idx, end_idx = stop_indices[i], stop_indices[i+1]
            h1, l1, s1 = hls_stops[i]
            h2, l2, s2 = hls_stops[i+1]

            dh = h2 - h1
            if abs(dh) > 0.5:
                if dh > 0:
                    h1 += 1
                else:
                    h2 += 1

            seg_len = end_idx - start_idx + 1
            hs[start_idx:end_idx+1] = np.mod(np.linspace(h1, h2, seg_len), 1.0)
            ls[start_idx:end_idx+1] = np.linspace(l1, l2, seg_len)
            ss[start_idx:end_idx+1] = np.linspace(s1, s2, seg_len)

        rgb_list = [tuple(int(c*255) for c in colorsys.hls_to_rgb(h,l,s)) for h,l,s in zip(hs, ls, ss)]

        out = ''.join(f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m{c}\033[0m" if self.truecolor else self._to_256(c,rgb)
                      for c,rgb in zip(self.text, rgb_list))
        return out

    def _to_256(self, char, rgb):
        r, g, b = rgb
        r_level = int(r/255*5)
        g_level = int(g/255*5)
        b_level = int(b/255*5)
        code = 16 + 36*r_level + 6*g_level + b_level
        return f"\033[38;5;{code}m{char}\033[0m"


class GradientTextFactory:
    def __init__(self, rgb_stops: list[tuple[int,int,int]] = None, truecolor: bool = False):
        self.rgb_stops = rgb_stops if rgb_stops is not None else [(255,255,255), (0,0,0)]
        self.truecolor = truecolor

    def text(self, text: str, rgb_stops: list[tuple[int,int,int]] = None, truecolor: bool = None) -> GradientText:
        stops = rgb_stops if rgb_stops is not None else self.rgb_stops
        tc = truecolor if truecolor is not None else self.truecolor
        return GradientText(text=text, rgb_stops=stops, truecolor=tc)

    # Short alias
    def t(self, text: str, rgb_stops: list[tuple[int,int,int]] = None, truecolor: bool = None) -> GradientText:
        return self.text(text, rgb_stops, truecolor)
