"""Build the animated banner used by the profile README.

The script keeps the source avatar local and makes the visual language easy to
refresh without hand-editing a binary GIF.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


ASSET_DIR = Path(__file__).resolve().parent
SIZE = (1280, 420)
PRIMARY = (150, 98, 212)  # #9662D4
INK = (12, 7, 22)
LIGHT = (239, 231, 250)
MUTED = (201, 184, 224)
FRAME_COUNT = 16


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(Path(r"C:\\Windows\\Fonts") / name, size)


def cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    width, height = image.size
    target_width, target_height = size
    scale = max(target_width / width, target_height / height)
    resized = image.resize((round(width * scale), round(height * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - target_width) // 2
    top = (resized.height - target_height) // 2
    return resized.crop((left, top, left + target_width, top + target_height))


def circular_avatar() -> Image.Image:
    source = Image.open(ASSET_DIR / "avatar-source.png").convert("RGB")
    tinted = ImageOps.colorize(ImageOps.grayscale(source), black="#160A24", white="#E7DDF7").convert("RGBA")
    size = 244
    avatar = cover(tinted, (size, size))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    avatar.putalpha(mask)
    return avatar


def glow_ellipse(center: tuple[int, int], radius: int, opacity: int) -> Image.Image:
    glow = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    x, y = center
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*PRIMARY, opacity))
    return glow.filter(ImageFilter.GaussianBlur(32))


def chip(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], label: str, label_x: int, text_font: ImageFont.FreeTypeFont) -> None:
    draw.rounded_rectangle(xy, radius=17, fill=(33, 19, 52, 218), outline=(*PRIMARY, 176), width=1)
    draw.text((label_x, xy[1] + 8), label, font=text_font, fill=LIGHT)


def build_frame(index: int, background: Image.Image, avatar: Image.Image) -> Image.Image:
    phase = (math.tau * index) / FRAME_COUNT
    frame = background.copy()
    frame.alpha_composite(Image.new("RGBA", SIZE, (*INK, 72)))

    center = (1056, 211)
    pulse = (math.sin(phase) + 1) / 2
    frame.alpha_composite(glow_ellipse(center, 155 + round(pulse * 10), 86 + round(pulse * 24)))

    effects = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(effects)
    ring_radius = 146 + round(pulse * 10)
    draw.ellipse(
        (center[0] - ring_radius, center[1] - ring_radius, center[0] + ring_radius, center[1] + ring_radius),
        outline=(*PRIMARY, 90 + round(pulse * 95)),
        width=2,
    )
    draw.ellipse((center[0] - 136, center[1] - 136, center[0] + 136, center[1] + 136), outline=(*LIGHT, 190), width=2)

    for particle in range(13):
        particle_phase = phase + particle * 0.83
        x = 770 + ((particle * 79 + index * 13) % 510)
        y = 52 + ((particle * 47 + round(math.sin(particle_phase) * 30)) % 310)
        radius = 1 + (particle % 3 == 0)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*PRIMARY, 75 + (particle % 4) * 30))

    underline_end = 84 + round(496 * ((math.sin(phase - math.pi / 2) + 1) / 2))
    draw.line((84, 271, 580, 271), fill=(107, 70, 151, 125), width=3)
    draw.line((84, 271, underline_end, 271), fill=(*PRIMARY, 255), width=4)
    draw.ellipse((underline_end - 5, 266, underline_end + 5, 276), fill=(*LIGHT, 245))
    frame.alpha_composite(effects)

    avatar_x = center[0] - avatar.width // 2 + round(math.sin(phase) * 2)
    avatar_y = center[1] - avatar.height // 2 + round(math.cos(phase) * 2)
    frame.alpha_composite(avatar, (avatar_x, avatar_y))

    text = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(text)
    draw.text((84, 109), "PYTHON DEVELOPER", font=font("segoeuib.ttf", 18), fill=(*MUTED, 255))
    draw.text((84, 150), "TIMOFEY SOROKA", font=font("segoeuib.ttf", 54), fill=(*LIGHT, 255))
    draw.text((84, 290), "Telegram  ·  APIs  ·  automation", font=font("segoeuil.ttf", 24), fill=(*MUTED, 255))
    chip_font = font("segoeuib.ttf", 14)
    chip(draw, (84, 337, 198, 371), "PYTHON", 107, chip_font)
    chip(draw, (210, 337, 351, 371), "TELEGRAM", 232, chip_font)
    chip(draw, (363, 337, 525, 371), "AUTOMATION", 384, chip_font)
    frame.alpha_composite(text)
    return frame.convert("RGB")


def main() -> None:
    background = cover(Image.open(ASSET_DIR / "profile-banner-background.png").convert("RGBA"), SIZE)
    avatar = circular_avatar()
    frames = [build_frame(index, background, avatar) for index in range(FRAME_COUNT)]
    palette = frames[0].quantize(colors=96, method=Image.Quantize.MEDIANCUT)
    frames = [palette, *(frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames[1:])]
    output = ASSET_DIR / "profile-banner.gif"
    frames[0].save(
        output,
        save_all=True,
        append_images=frames[1:],
        duration=90,
        loop=0,
        optimize=True,
        disposal=2,
    )
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
