import math


def pixels_to_ss_coords(x, y):
    try:
        ch = "ABCDEFGHIJKLMNOPQRSTU"
        x1 = int(math.floor((x * 20) / 16384))
        y1 = ((y * 20) / 16384) + 1
        return ch[x1] + str(y1)
    except:
        return "InvalidCoord?"


def tiles_to_ss_coords(x, y):
    return pixels_to_ss_coords(x << 4, y << 4)


def pixels_to_ss_area(x, y):
    try:
        f = 3277.6
        xc = ["FarLeft", "Left", "Center", "Right", "FarRight"]
        yc = ["FarUp-", "Up-", "", "Down-", "FarDown-"]
        xi = int(math.floor(x / f))
        yi = int(math.floor(y / f))
        return yc[yi]+xc[xi]
    except:
        return "InvalidCoord?"


def tiles_to_ss_area(x, y):
    return pixels_to_ss_area(x << 4, y << 4)
