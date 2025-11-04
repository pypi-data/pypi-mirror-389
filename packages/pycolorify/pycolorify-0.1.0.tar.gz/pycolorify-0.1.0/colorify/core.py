import colorsys, random

COLOR_NAMES = {
    "red": "#ff0000",
    "green": "#008000",
    "blue": "#0000ff",
    "white": "#ffffff",
    "black": "#000000",
    "yellow": "#ffff00",
    "cyan": "#00ffff",
    "magenta": "#ff00ff",
    "orange": "#ffa500",
    "skyblue": "#87ceeb",
    "pink": "#ffc0cb",
    "purple": "#800080",
    "gray": "#808080",
}

def clamp(x, low=0, high=1):
    return max(low, min(high, x))

class Color:
    def __init__(self, value):
        if isinstance(value, str):
            if value.startswith("#"):
                self.hex = value.lower()
            elif value.lower() in COLOR_NAMES:
                self.hex = COLOR_NAMES[value.lower()]
            else:
                raise ValueError(f"Unknown color: {value}")
        elif isinstance(value, tuple) and len(value) == 3:
            self.hex = "#%02x%02x%02x" % value
        else:
            raise ValueError("Color must be a name, hex string, or RGB tuple")

        self.rgb = self._hex_to_rgb(self.hex)
        self.hsl = self._rgb_to_hsl(*self.rgb)

    def _hex_to_rgb(self, hexcode):
        hexcode = hexcode.lstrip("#")
        return tuple(int(hexcode[i:i+2], 16) for i in (0, 2, 4))

    def _rgb_to_hex(self, rgb):
        return "#%02x%02x%02x" % rgb

    def _rgb_to_hsl(self, r, g, b):
        r, g, b = [x/255 for x in (r, g, b)]
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        return (round(h*360), round(s*100), round(l*100))

    def _hsl_to_rgb(self, h, s, l):
        h, s, l = h/360, s/100, l/100
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return (round(r*255), round(g*255), round(b*255))

    def lighten(self, amount=0.1):
        h, s, l = self.hsl
        l = clamp(l/100 + amount)
        return Color(self._rgb_to_hex(self._hsl_to_rgb(h, s, l*100)))

    def darken(self, amount=0.1):
        h, s, l = self.hsl
        l = clamp(l/100 - amount)
        return Color(self._rgb_to_hex(self._hsl_to_rgb(h, s, l*100)))

    @staticmethod
    def random():
        return Color("#%06x" % random.randint(0, 0xFFFFFF))

    def contrast_ratio(self, other):
        def luminance(rgb):
            def f(c):
                c = c / 255
                return c / 12.92 if c <= 0.03928 else ((c+0.055)/1.055)**2.4
            r, g, b = map(f, rgb)
            return 0.2126*r + 0.7152*g + 0.0722*b
        L1, L2 = luminance(self.rgb), luminance(other.rgb)
        return round((max(L1, L2)+0.05) / (min(L1, L2)+0.05), 2)
