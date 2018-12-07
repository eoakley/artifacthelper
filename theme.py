class keydefaultdict(dict):
    def __init__(self, default_factory, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_factory = default_factory

    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError( key )
        else:
            ret = self[key] = self.default_factory(key)
            return ret


def hex_to_rgb(hex):
    """Convert a hex color "#FFFFFF" to an RGB tuple (255,255,255)."""
    # Pass 16 to the integer function for change of base
    return [int(hex[i:i+2], 16) for i in range(1, 6, 2)]


def rgb_to_hex(rgb):
    """Convert an RGB tuple (255,255,255) to hex "#FFFFFF"."""
    rgb = (int(x) for x in rgb)
    return "#"+"".join(["0{0:x}".format(v) if v < 16 else
                        "{0:x}".format(v) for v in rgb])


def linear_gradient(start, finish, position):
    s = hex_to_rgb(start)
    f = hex_to_rgb(finish)
    return rgb_to_hex((int(s[j] + position * (f[j] - s[j])) for j in range(3)))


def calc_color(val,
               min_val=0,           zero_val=0,           max_val=1,
               min_color='#999999', zero_color='#dddddd', max_color='#fff'):
    if val >= zero_val:
        val = min(val, max_val)
        return linear_gradient(zero_color, max_color, (val - zero_val) / (max_val - zero_val))
    else:
        val = max(val, min_val)
        return linear_gradient(zero_color, min_color, (zero_val - val) / (zero_val - min_val))


tier_colors = {
    'S': '#FF7FFE',
    'A': '#FFA347',
    'B': '#EFEF77',
    'C': '#67CE67',
    'D': '#4C7299',
    'E': '#4848AF',
    'F': '#A854A8',
    'U': '#aaaaaa',
    '?': '#dddddd',
}


"""Get a color like win_rate_colors[53.7]"""
win_rate_colors = keydefaultdict(
    lambda wr: calc_color(
        float(wr),
        min_val=40, zero_val=50, max_val=55,
        min_color='#992828', max_color='#5BBA5F'))


pick_rate_colors = keydefaultdict(
    lambda pr: calc_color(
        float(pr),
        min_val=5, zero_val=16.66, max_val=40,
        max_color='#6CBFF0'))


price_colors = keydefaultdict(
    lambda p: calc_color(
        float(p[1:]) if isinstance(p, str) else p,
        min_val=0, zero_val=1, max_val=5,
        max_color='#FFD70D'))
