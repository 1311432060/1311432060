import io
import os

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import config

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "C:\\Windows\\Fonts\\segoeui.ttf",
    "C:\\Windows\\Fonts\\segoeuib.ttf",
]

REGULAR_HINTS = ("DejaVuSans.ttf", "Arial.ttf", "Arial Unicode.ttf", "segoeui.ttf")
BOLD_HINTS = ("DejaVuSans-Bold.ttf", "Arial Bold.ttf", "segoeuib.ttf")

CARD_RADIUS = 12


def _find_font(hints) -> str:
    for path in FONT_CANDIDATES:
        if os.path.exists(path) and os.path.basename(path) in hints:
            return path
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    return ""


def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    path = _find_font(BOLD_HINTS if bold else REGULAR_HINTS)
    if path:
        return ImageFont.truetype(path, size)
    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()


def _cover(image: Image.Image, width: int, height: int) -> Image.Image:
    scale = max(width / image.width, height / image.height)
    resized = image.resize(
        (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
        Image.LANCZOS,
    )
    left = (resized.width - width) // 2
    top = (resized.height - height) // 2
    return resized.crop((left, top, left + width, top + height))


def _background_layer(path: str, width: int, height: int, palette: dict):
    try:
        source = Image.open(path).convert("RGBA")
    except Exception:
        return None
    layer = _cover(source, width, height)
    if config.BACKGROUND_BLUR > 0:
        layer = layer.filter(ImageFilter.GaussianBlur(config.BACKGROUND_BLUR))
    overlay_alpha = max(0, min(255, config.BACKGROUND_OVERLAY))
    if overlay_alpha:
        overlay = Image.new("RGBA", (width, height), palette["overlay"] + (overlay_alpha,))
        layer = Image.alpha_composite(layer, overlay)
    return layer


def _corner_mask(width: int, height: int) -> Image.Image:
    scale = 4
    mask = Image.new("L", (width * scale, height * scale), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, width * scale - 1, height * scale - 1),
        radius=CARD_RADIUS * scale,
        fill=255,
    )
    return mask.resize((width, height), Image.LANCZOS)


def _rounded_card(width: int, height: int, palette: dict, background: str = "") -> Image.Image:
    card = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)
    draw.rounded_rectangle(
        (0, 0, width - 1, height - 1),
        radius=CARD_RADIUS,
        fill=palette["bg"],
    )

    mask = _corner_mask(width, height)

    layer = _background_layer(background, width, height, palette) if background else None
    if layer is not None:
        card.paste(layer, (0, 0), mask)

    draw.rounded_rectangle(
        (0, 0, width - 1, height - 1),
        radius=CARD_RADIUS,
        outline=palette["border"],
        width=2,
    )
    card.putalpha(mask)
    return card


def _text(draw: ImageDraw.ImageDraw, position, content, font, fill, anchor=None,
          shadow: bool = True):
    if shadow:
        x, y = position
        draw.text((x + 1, y + 1), content, font=font, fill=(0, 0, 0, 140), anchor=anchor)
    draw.text(position, content, font=font, fill=fill, anchor=anchor)


def _avatar(url: str, size: int):
    if not url:
        return None
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        avatar = Image.open(io.BytesIO(response.content)).convert("RGBA")
    except Exception:
        return None
    avatar = avatar.resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
    avatar.putalpha(mask.resize((size, size), Image.LANCZOS))
    return avatar


def _format_number(value: int) -> str:
    if value >= 1000:
        return f"{value / 1000:.1f}k".replace(".0k", "k")
    return str(value)


def render_stats_card(stats: dict, path: str) -> str:
    palette = config.theme()
    width, height = 500, 220
    background = config.background_path(config.BACKGROUND_IMAGE)
    card = _rounded_card(width, height, palette, background)
    draw = ImageDraw.Draw(card)
    shadow = bool(background)

    title_font = load_font(22, bold=True)
    label_font = load_font(15)
    value_font = load_font(16, bold=True)

    avatar = _avatar(stats.get("avatar_url", ""), 64)
    text_x = 28
    if avatar is not None:
        card.paste(avatar, (28, 26), avatar)
        text_x = 108

    _text(draw, (text_x, 32), f"{stats['name']}'s GitHub Stats", title_font,
          palette["title"], shadow=shadow)
    _text(draw, (text_x, 62), f"@{stats['username']}", label_font,
          palette["muted"], shadow=shadow)

    rows = [
        ("Total Stars", stats["stars"]),
        ("Total Forks", stats["forks"]),
        ("Public Repos", stats["public_repos"]),
        ("Followers", stats["followers"]),
        ("Following", stats["following"]),
        ("Contributions (1y)", stats["contributions"]),
    ]

    column_x = (28, 268)
    start_y = 110
    line_height = 26
    for index, (label, value) in enumerate(rows):
        x = column_x[index // 3]
        y = start_y + (index % 3) * line_height
        _text(draw, (x, y), label, label_font, palette["text"], shadow=shadow)
        _text(draw, (x + 200, y), _format_number(value), value_font,
              palette["accent"], anchor="ra", shadow=shadow)

    card.save(path)
    return path


def render_language_card(stats: dict, path: str) -> str:
    palette = config.theme()
    languages = list(stats["languages"].items())[: config.TOP_LANGUAGES]
    total = sum(size for _, size in languages) or 1

    width = 500
    rows = (len(languages) + 1) // 2
    height = 120 + rows * 28
    background = config.background_path(config.LANGS_BACKGROUND_IMAGE)
    card = _rounded_card(width, height, palette, background)
    draw = ImageDraw.Draw(card)
    shadow = bool(background)

    title_font = load_font(20, bold=True)
    text_font = load_font(14)

    _text(draw, (28, 24), "Most Used Languages", title_font, palette["title"], shadow=shadow)

    bar_x, bar_y, bar_w, bar_h = 28, 66, width - 56, 14
    bar = Image.new("RGBA", (bar_w, bar_h), (0, 0, 0, 0))
    bar_draw = ImageDraw.Draw(bar)
    offset = 0
    for index, (name, size) in enumerate(languages):
        segment = bar_w - offset if index == len(languages) - 1 else int(bar_w * size / total)
        bar_draw.rectangle((offset, 0, offset + segment, bar_h), fill=config.language_color(name))
        offset += segment

    mask = Image.new("L", (bar_w, bar_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, bar_w - 1, bar_h - 1), radius=7, fill=255)
    card.paste(bar, (bar_x, bar_y), mask)

    for index, (name, size) in enumerate(languages):
        x = 28 + (index % 2) * 236
        y = 104 + (index // 2) * 28
        draw.ellipse((x, y + 3, x + 11, y + 14), fill=config.language_color(name))
        percent = size / total * 100
        _text(draw, (x + 20, y), f"{name} {percent:.1f}%", text_font,
              palette["text"], shadow=shadow)

    card.save(path)
    return path
