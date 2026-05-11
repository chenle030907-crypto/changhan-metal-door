from pathlib import Path
import math
import random

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)


PALETTE = {
    "black": (12, 13, 14),
    "graphite": (28, 30, 31),
    "steel": (118, 126, 128),
    "aluminum": (194, 199, 198),
    "mist": (232, 235, 234),
    "glass": (178, 194, 198),
    "line": (82, 88, 90),
    "white": (246, 247, 245),
}


def mix(a, b, t):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


def gradient(size, top, bottom):
    width, height = size
    img = Image.new("RGB", size, top)
    draw = ImageDraw.Draw(img)
    for y in range(height):
        t = y / max(1, height - 1)
        draw.line((0, y, width, y), fill=mix(top, bottom, t))
    return img


def add_noise(img, amount=8, seed=11):
    random.seed(seed)
    noise = Image.effect_noise(img.size, 40).convert("L")
    noise = noise.point(lambda p: int((p - 128) * amount / 24 + 128))
    overlay = Image.merge("RGB", (noise, noise, noise))
    return Image.blend(img, overlay, 0.05)


def vignette(img, strength=120):
    width, height = img.size
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    margin = int(min(width, height) * 0.05)
    draw.ellipse(
        (-width * 0.28, -height * 0.2, width * 1.28, height * 1.18),
        fill=255,
    )
    mask = mask.filter(ImageFilter.GaussianBlur(radius=min(width, height) // 5))
    dark = Image.new("RGB", img.size, (0, 0, 0))
    return Image.composite(img, dark, mask.point(lambda p: 255 - int(p * strength / 255)))


def brushed_rect(draw, box, base, direction="vertical", lines=18):
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=base)
    w, h = x1 - x0, y1 - y0
    if direction == "vertical":
        for i in range(lines):
            x = x0 + int(w * i / max(1, lines - 1))
            c = mix(base, PALETTE["white"], 0.10 if i % 2 else 0.03)
            draw.line((x, y0, x, y1), fill=c, width=max(1, w // 160))
    else:
        for i in range(lines):
            y = y0 + int(h * i / max(1, lines - 1))
            c = mix(base, PALETTE["black"], 0.10 if i % 2 else 0.02)
            draw.line((x0, y, x1, y), fill=c, width=max(1, h // 160))


def glass_rect(draw, box, tint=None, outline=None, width=2):
    tint = tint or (166, 181, 184)
    outline = outline or (210, 216, 216)
    draw.rectangle(box, fill=tint, outline=outline, width=width)
    x0, y0, x1, y1 = box
    draw.polygon(
        [(x0, y0), (x1, y0), (x0 + (x1 - x0) * 0.18, y1), (x0, y1)],
        fill=mix(tint, PALETTE["white"], 0.24),
    )
    draw.line((x0 + 12, y0 + 10, x1 - 12, y0 + 10), fill=mix(outline, PALETTE["white"], 0.2), width=1)


def draw_architecture_base(size, mood="dark"):
    w, h = size
    if mood == "light":
        img = gradient(size, (236, 238, 236), (185, 190, 190))
    else:
        img = gradient(size, (55, 58, 59), (14, 15, 16))
    img = add_noise(img)
    d = ImageDraw.Draw(img)

    horizon = int(h * 0.58)
    d.rectangle((0, horizon, w, h), fill=(42, 44, 45) if mood == "dark" else (212, 214, 212))
    for i in range(12):
        y = horizon + int((h - horizon) * i / 11)
        alpha = i / 11
        c = mix((82, 85, 86), (20, 21, 22), alpha) if mood == "dark" else mix((190, 194, 194), (246, 247, 246), alpha)
        d.line((0, y, w, y), fill=c, width=1)
    for x in range(-w, w * 2, max(80, w // 9)):
        d.line((x, horizon, int(w * 0.50), h), fill=(73, 76, 77) if mood == "dark" else (188, 192, 192), width=1)

    ceiling = int(h * 0.18)
    d.rectangle((0, 0, w, ceiling), fill=(23, 25, 26) if mood == "dark" else (219, 222, 221))
    for x in range(0, w, max(90, w // 10)):
        d.line((x, 0, x + int(w * 0.12), ceiling), fill=(62, 66, 67), width=1)
    for y in range(ceiling // 4, ceiling, max(38, ceiling // 4)):
        d.line((0, y, w, y), fill=(67, 70, 71), width=1)

    return img


def draw_facade(d, size, box, rows=2, cols=4, frame=22, tint=(122, 138, 142)):
    x0, y0, x1, y1 = box
    brushed_rect(d, (x0, y0, x1, y1), (64, 68, 69), lines=26)
    inner = (x0 + frame, y0 + frame, x1 - frame, y1 - frame)
    ix0, iy0, ix1, iy1 = inner
    cell_w = (ix1 - ix0) / cols
    cell_h = (iy1 - iy0) / rows
    for r in range(rows):
        for c in range(cols):
            gx0 = int(ix0 + c * cell_w + frame * 0.18)
            gy0 = int(iy0 + r * cell_h + frame * 0.18)
            gx1 = int(ix0 + (c + 1) * cell_w - frame * 0.18)
            gy1 = int(iy0 + (r + 1) * cell_h - frame * 0.18)
            glass_rect(d, (gx0, gy0, gx1, gy1), tint=mix(tint, PALETTE["white"], 0.06), width=1)
    for c in range(cols + 1):
        x = int(ix0 + c * cell_w)
        brushed_rect(d, (x - frame // 4, iy0, x + frame // 4, iy1), (112, 119, 120), lines=6)
    for r in range(rows + 1):
        y = int(iy0 + r * cell_h)
        brushed_rect(d, (ix0, y - frame // 5, ix1, y + frame // 5), (112, 119, 120), direction="horizontal", lines=6)


def draw_swing_door(d, box, double=True):
    x0, y0, x1, y1 = box
    brushed_rect(d, (x0, y0, x1, y1), (72, 76, 77), lines=28)
    gap = max(4, (x1 - x0) // 120)
    inner = (x0 + 28, y0 + 28, x1 - 28, y1 - 28)
    ix0, iy0, ix1, iy1 = inner
    if double:
        mid = (ix0 + ix1) // 2
        glass_rect(d, (ix0, iy0, mid - gap, iy1), tint=(118, 135, 139), width=2)
        glass_rect(d, (mid + gap, iy0, ix1, iy1), tint=(112, 130, 134), width=2)
        brushed_rect(d, (mid - 5, iy0, mid + 5, iy1), (168, 173, 172), lines=4)
        d.rounded_rectangle((mid - 62, iy0 + 190, mid - 45, iy0 + 300), radius=8, fill=(213, 218, 217))
        d.rounded_rectangle((mid + 45, iy0 + 190, mid + 62, iy0 + 300), radius=8, fill=(213, 218, 217))
    else:
        glass_rect(d, inner, tint=(128, 143, 146), width=2)


def draw_sliding_door(d, box):
    x0, y0, x1, y1 = box
    brushed_rect(d, (x0, y0, x1, y1), (67, 72, 73), lines=24)
    ix0, iy0, ix1, iy1 = x0 + 30, y0 + 60, x1 - 30, y1 - 28
    overhead = (x0 + 20, y0 + 18, x1 - 20, y0 + 58)
    brushed_rect(d, overhead, (115, 121, 122), direction="horizontal", lines=12)
    panels = [
        (ix0, iy0, (ix0 + ix1) // 2 - 8, iy1),
        ((ix0 + ix1) // 2 + 8, iy0, ix1, iy1),
    ]
    for panel in panels:
        glass_rect(d, panel, tint=(130, 146, 150), width=2)
    mid = (ix0 + ix1) // 2
    d.line((mid, iy0, mid, iy1), fill=(230, 233, 232), width=3)
    d.ellipse((mid - 28, y0 + 25, mid + 28, y0 + 48), outline=(210, 216, 215), width=2)


def draw_revolving_door(d, box):
    x0, y0, x1, y1 = box
    cx = (x0 + x1) // 2
    top = y0 + 20
    bottom = y1 - 25
    width = x1 - x0
    d.ellipse((cx - width // 2, top, cx + width // 2, bottom), fill=(72, 78, 79), outline=(190, 196, 195), width=7)
    d.ellipse((cx - width // 2 + 34, top + 24, cx + width // 2 - 34, bottom - 24), fill=(120, 139, 143), outline=(226, 229, 228), width=3)
    for angle in (90, 210, 330):
        rad = math.radians(angle)
        px = cx + math.cos(rad) * width * 0.38
        py = (top + bottom) / 2 + math.sin(rad) * (bottom - top) * 0.34
        d.line((cx, (top + bottom) // 2, px, py), fill=(233, 236, 235), width=5)
    brushed_rect(d, (cx - 8, top + 34, cx + 8, bottom - 34), (180, 186, 185), lines=5)


def draw_access_control(d, box):
    x0, y0, x1, y1 = box
    brushed_rect(d, box, (83, 88, 89), lines=26)
    glass_rect(d, (x0 + 40, y0 + 52, x1 - 150, y1 - 40), tint=(96, 111, 115), width=2)
    panel = (x1 - 120, y0 + 170, x1 - 58, y0 + 320)
    d.rounded_rectangle(panel, radius=13, fill=(17, 18, 19), outline=(192, 198, 198), width=2)
    d.rectangle((panel[0] + 11, panel[1] + 16, panel[2] - 11, panel[1] + 56), fill=(72, 91, 94))
    for i in range(4):
        y = panel[1] + 76 + i * 18
        d.line((panel[0] + 17, y, panel[2] - 17, y), fill=(97, 104, 105), width=1)
    d.ellipse((panel[0] + 22, panel[3] - 36, panel[0] + 40, panel[3] - 18), fill=(178, 207, 204))


def draw_partition(d, box):
    x0, y0, x1, y1 = box
    brushed_rect(d, (x0, y0, x1, y1), (96, 101, 102), lines=24)
    cols = 5
    for i in range(cols):
        gx0 = x0 + 26 + i * (x1 - x0 - 52) // cols
        gx1 = x0 + 26 + (i + 1) * (x1 - x0 - 52) // cols - 8
        glass_rect(d, (gx0, y0 + 36, gx1, y1 - 36), tint=(154, 170, 173), width=1)
    for i in range(1, cols):
        sx = x0 + 24 + i * (x1 - x0 - 48) // cols
        brushed_rect(d, (sx - 5, y0 + 20, sx + 5, y1 - 20), (177, 183, 182), lines=3)


def draw_clean_door(d, box):
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=(226, 229, 228), outline=(166, 172, 172), width=4)
    d.rectangle((x0 + 38, y0 + 42, x1 - 38, y1 - 42), fill=(236, 238, 237), outline=(176, 181, 181), width=3)
    glass_rect(d, (x0 + 80, y0 + 74, x1 - 80, y0 + 230), tint=(173, 190, 193), width=2)
    d.rounded_rectangle((x1 - 94, y0 + 310, x1 - 62, y0 + 335), radius=8, fill=(103, 109, 110))
    d.rectangle((x0 - 26, y0 - 14, x1 + 26, y0 + 18), fill=(202, 207, 207))


def product_image(filename, kind, mood="dark"):
    size = (1200, 900)
    img = draw_architecture_base(size, mood=mood)
    d = ImageDraw.Draw(img)
    if kind == "partition":
        draw_partition(d, (110, 205, 1090, 620))
    elif kind == "revolving":
        draw_facade(d, size, (165, 120, 1035, 705), rows=2, cols=4, frame=20)
        draw_revolving_door(d, (410, 275, 790, 710))
    elif kind == "sensor":
        draw_facade(d, size, (140, 150, 1060, 720), rows=2, cols=4, frame=20)
        draw_sliding_door(d, (330, 310, 870, 722))
    elif kind == "access":
        draw_facade(d, size, (160, 145, 1040, 720), rows=2, cols=4, frame=20)
        draw_access_control(d, (375, 260, 825, 720))
    elif kind == "clean":
        draw_clean_door(d, (405, 180, 795, 720))
        d.rectangle((0, 0, 1200, 900), outline=(210, 214, 213), width=0)
    else:
        draw_facade(d, size, (130, 125, 1070, 735), rows=2, cols=4, frame=20)
        draw_swing_door(d, (350, 285, 850, 735), double=True)
    img = vignette(img, 80 if mood == "dark" else 48)
    img.save(ASSETS / filename, quality=92)


def hero_image():
    size = (2400, 1500)
    img = draw_architecture_base(size, mood="dark")
    d = ImageDraw.Draw(img)
    draw_facade(d, size, (250, 155, 2150, 1160), rows=3, cols=7, frame=32, tint=(105, 122, 126))
    draw_sliding_door(d, (830, 610, 1570, 1180))
    d.rectangle((0, 1180, 2400, 1500), fill=(24, 25, 26))
    for i in range(22):
        y = 1180 + i * 18
        d.line((0, y, 2400, y), fill=(42, 44, 45), width=1)
    for x in (260, 620, 1780, 2140):
        brushed_rect(d, (x, 160, x + 34, 1180), (130, 136, 136), lines=5)
    for i in range(10):
        x = 230 + i * 210
        d.line((x, 1220, x + 520, 1500), fill=(56, 59, 60), width=2)
    img = vignette(img, 105)
    img.save(ASSETS / "hero-metal-door.png", quality=94)


def case_image(filename, kind):
    size = (1200, 780)
    mood = "light" if kind in {"hospital", "office"} else "dark"
    img = draw_architecture_base(size, mood=mood)
    d = ImageDraw.Draw(img)
    if kind == "mall":
        draw_facade(d, size, (100, 112, 1100, 650), rows=2, cols=6, frame=18)
        draw_sliding_door(d, (395, 330, 805, 650))
        d.line((120, 110, 1080, 110), fill=(205, 210, 210), width=5)
    elif kind == "hotel":
        draw_facade(d, size, (120, 96, 1080, 650), rows=2, cols=5, frame=18)
        draw_revolving_door(d, (450, 278, 750, 654))
        d.rectangle((0, 650, 1200, 780), fill=(34, 35, 35))
    elif kind == "hospital":
        d.rectangle((0, 0, 1200, 780), fill=(232, 235, 235))
        for x in (120, 1080):
            d.line((x, 0, x, 780), fill=(196, 201, 202), width=4)
        draw_sliding_door(d, (355, 230, 845, 690))
    elif kind == "office":
        draw_partition(d, (105, 160, 1095, 570))
        draw_swing_door(d, (450, 310, 750, 675), double=True)
    else:
        d.rectangle((0, 0, 1200, 780), fill=(52, 55, 56))
        for x in range(80, 1160, 140):
            d.rectangle((x, 70, x + 60, 610), fill=(75, 80, 81))
            d.line((x + 60, 70, x + 60, 610), fill=(130, 137, 138), width=2)
        draw_swing_door(d, (360, 245, 840, 650), double=True)
        d.rectangle((0, 620, 1200, 780), fill=(35, 36, 37))
    img = vignette(add_noise(img, amount=6), 58)
    img.save(ASSETS / filename, quality=91)


def factory_image(filename, kind):
    size = (1200, 780)
    img = gradient(size, (226, 229, 228), (92, 98, 99))
    img = add_noise(img, amount=7)
    d = ImageDraw.Draw(img)
    if kind == "equipment":
        d.rectangle((0, 0, 1200, 150), fill=(211, 214, 213))
        for x in range(70, 1180, 170):
            d.line((x, 0, x - 90, 780), fill=(162, 167, 168), width=2)
        brushed_rect(d, (175, 260, 1025, 560), (91, 98, 99), direction="horizontal", lines=20)
        d.rectangle((250, 325, 970, 500), fill=(34, 36, 37), outline=(184, 190, 190), width=4)
        for x in range(320, 920, 100):
            d.line((x, 325, x, 500), fill=(93, 101, 102), width=2)
        d.rectangle((520, 210, 680, 310), fill=(156, 162, 162))
    elif kind == "workshop":
        d.rectangle((0, 0, 1200, 130), fill=(196, 200, 200))
        for x in range(80, 1200, 140):
            d.line((x, 0, x + 40, 780), fill=(145, 151, 152), width=2)
        for i in range(5):
            y = 250 + i * 80
            brushed_rect(d, (150, y, 1050, y + 24), (132, 139, 140), direction="horizontal", lines=10)
        for x in (270, 510, 760):
            draw_swing_door(d, (x, 300, x + 150, 620), double=True)
    elif kind == "installation":
        draw_facade(d, size, (140, 95, 1060, 610), rows=2, cols=5, frame=18)
        draw_swing_door(d, (430, 275, 770, 650), double=True)
        for x in (300, 875):
            d.ellipse((x, 555, x + 38, 593), fill=(26, 27, 28))
            d.rectangle((x + 12, 590, x + 28, 690), fill=(31, 33, 34))
            d.line((x + 18, 620, x - 25, 660), fill=(31, 33, 34), width=8)
            d.line((x + 23, 620, x + 60, 650), fill=(31, 33, 34), width=8)
    else:
        d.rectangle((0, 0, 1200, 780), fill=(180, 185, 185))
        for i in range(6):
            y = 145 + i * 78
            x0 = 90 + i * 42
            brushed_rect(d, (x0, y, 1130 - i * 16, y + 42), (128 + i * 8, 135 + i * 8, 136 + i * 8), direction="horizontal", lines=12)
            d.ellipse((1000 - i * 10, y + 8, 1030 - i * 10, y + 38), fill=(82, 88, 89))
        d.line((85, 612, 1115, 612), fill=(236, 238, 237), width=3)
    img = vignette(img, 48)
    img.save(ASSETS / filename, quality=91)


def qr_image():
    size = 640
    img = Image.new("RGB", (size, size), PALETTE["white"])
    d = ImageDraw.Draw(img)
    margin = 64
    cell = 16
    random.seed(42)
    d.rectangle((0, 0, size - 1, size - 1), outline=(176, 182, 182), width=2)
    for corner in [(margin, margin), (size - margin - cell * 7, margin), (margin, size - margin - cell * 7)]:
        x, y = corner
        d.rectangle((x, y, x + cell * 7, y + cell * 7), fill=PALETTE["black"])
        d.rectangle((x + cell, y + cell, x + cell * 6, y + cell * 6), fill=PALETTE["white"])
        d.rectangle((x + cell * 2, y + cell * 2, x + cell * 5, y + cell * 5), fill=PALETTE["black"])
    grid = (size - margin * 2) // cell
    for gy in range(grid):
        for gx in range(grid):
            x = margin + gx * cell
            y = margin + gy * cell
            if (gx < 8 and gy < 8) or (gx > grid - 9 and gy < 8) or (gx < 8 and gy > grid - 9):
                continue
            v = (gx * 17 + gy * 23 + random.randint(0, 7)) % 5
            if v in (0, 2):
                d.rectangle((x, y, x + cell - 3, y + cell - 3), fill=PALETTE["black"])
    d.rectangle((232, 282, 408, 358), fill=PALETTE["white"], outline=(160, 166, 166), width=2)
    d.text((258, 306), "CHANGHAN", fill=PALETTE["black"])
    img.save(ASSETS / "wechat-qr.png")


def main():
    hero_image()
    product_image("product-kfc-door.png", "kfc")
    product_image("product-sensor-door.png", "sensor")
    product_image("product-revolving-door.png", "revolving")
    product_image("product-access-control.png", "access")
    product_image("product-office-partition.png", "partition", mood="light")
    product_image("product-clean-door.png", "clean", mood="light")
    for filename, kind in [
        ("case-mall.png", "mall"),
        ("case-hotel.png", "hotel"),
        ("case-hospital.png", "hospital"),
        ("case-office.png", "office"),
        ("case-factory.png", "factory"),
    ]:
        case_image(filename, kind)
    for filename, kind in [
        ("factory-equipment.png", "equipment"),
        ("factory-workshop.png", "workshop"),
        ("factory-installation.png", "installation"),
        ("factory-material.png", "material"),
    ]:
        factory_image(filename, kind)
    qr_image()


if __name__ == "__main__":
    main()
