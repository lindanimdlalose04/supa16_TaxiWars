"""Generate all game art + sound assets for Supa16 Taxi Wars.
Run once: python gen_assets.py  -> writes into ./supa16/assets/
Art style: chunky, flat, outlined (BTD5-style pieces on a Risk-style board).
Everything drawn at 3x and downscaled for smooth anti-aliased edges.
"""
import os, math, wave, struct
import numpy as np
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "supa16", "assets")
os.makedirs(OUT, exist_ok=True)

INK = (47, 44, 38, 255)

REGION_ROOFS = {
    "northern_natal": (217, 140, 46),
    "midlands":       (109, 158, 74),
    "north_coast":    (216, 106, 82),
    "durban":         (134, 108, 196),
    "south_coast":    (74, 128, 196),
}
WALL = (248, 244, 232)
WALL_SHADE = (228, 221, 203)


def darker(c, f=0.62):
    return (int(c[0]*f), int(c[1]*f), int(c[2]*f), 255)


def house(roof_rgb, w=66, h=62, faded=False):
    """Chunky house: wide wall (number canvas), big roof, door, outline."""
    S = 3
    W, H = w*S, h*S
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ow = 4*S  # outline width

    roof_h = int(H*0.40)
    wall_top = roof_h - 2*S
    wall_l, wall_r = int(W*0.10), int(W*0.90)

    # wall
    d.rounded_rectangle([wall_l, wall_top, wall_r, H-ow//2],
                        radius=5*S, fill=WALL, outline=INK, width=ow)
    # wall base shade strip
    d.rectangle([wall_l+ow, H-12*S, wall_r-ow, H-ow], fill=WALL_SHADE)
    # roof (overhanging)
    apex = (W//2, ow//2)
    rl, rr = (2*S, roof_h), (W-2*S, roof_h)
    d.polygon([rl, apex, rr], fill=roof_rgb+(255,), outline=None)
    # roof shading: right half slightly darker for chunky depth
    d.polygon([(W//2, ow//2), rr, (W//2, roof_h)],
              fill=tuple(int(c*0.86) for c in roof_rgb)+(255,))
    d.line([rl, apex, rr], fill=INK, width=ow, joint="curve")
    d.line([rl, rr], fill=INK, width=ow)
    # tiny chimney
    ch_w = 7*S
    d.rectangle([int(W*0.68), 6*S, int(W*0.68)+ch_w, roof_h-6*S],
                fill=darker(roof_rgb, 0.8), outline=INK, width=2*S)

    img = img.resize((w, h), Image.LANCZOS)
    if faded:
        px = np.array(img).astype(np.float32)
        g = px[..., :3].mean(axis=2, keepdims=True)
        px[..., :3] = px[..., :3]*0.25 + g*0.75       # desaturate
        px[..., :3] = px[..., :3]*0.65 + 255*0.35      # lift toward paper
        px[..., 3] *= 0.85
        img = Image.fromarray(px.clip(0, 255).astype(np.uint8))
    return img


def taxi(body_rgb, dark_rgb, w=46, h=30):
    """Top-down chunky minibus taxi."""
    S = 3
    W, H = w*S, h*S
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ow = 3*S
    # wheels (poke out top/bottom)
    for wx in (int(W*0.22), int(W*0.74)):
        d.rounded_rectangle([wx, 0, wx+10*S, H], radius=4*S, fill=(35, 33, 29, 255))
    # body
    d.rounded_rectangle([2*S, 3*S, W-2*S, H-3*S], radius=8*S,
                        fill=body_rgb+(255,), outline=INK, width=ow)
    # windshield (front = right)
    d.rounded_rectangle([int(W*0.66), 6*S, int(W*0.82), H-6*S], radius=3*S,
                        fill=(225, 238, 240, 255), outline=INK, width=2*S)
    # rear window
    d.rounded_rectangle([int(W*0.10), 7*S, int(W*0.20), H-7*S], radius=2*S,
                        fill=(225, 238, 240, 255), outline=INK, width=2*S)
    # roof stripe
    d.rounded_rectangle([int(W*0.26), 5*S, int(W*0.60), H-5*S], radius=4*S,
                        fill=dark_rgb+(255,), outline=INK, width=2*S)
    return img.resize((w, h), Image.LANCZOS)


# ---- write images -----------------------------------------------------------
for key, roof in REGION_ROOFS.items():
    house(roof).save(os.path.join(OUT, f"house_{key}.png"))
    house(roof, w=34, h=32, faded=True).save(os.path.join(OUT, f"house_{key}_done.png"))

taxi((22, 138, 109), (10, 84, 66)).save(os.path.join(OUT, "taxi_p1.png"))
taxi((205, 76, 122), (130, 42, 72)).save(os.path.join(OUT, "taxi_p2.png"))

# ---- synthesized SFX --------------------------------------------------------
SR = 22050

def env(n, a=0.005, r=0.25):
    t = np.linspace(0, 1, n)
    e = np.minimum(t/max(a, 1e-6), 1.0) * np.exp(-t/r)
    return e

def tone(f, dur, kind="sine", bend=0.0):
    n = int(SR*dur)
    t = np.arange(n)/SR
    freq = f*(1+bend*t/dur)
    ph = 2*np.pi*np.cumsum(freq)/SR
    if kind == "sine":
        w = np.sin(ph)
    elif kind == "tri":
        w = 2/np.pi*np.arcsin(np.sin(ph))
    else:
        w = np.sign(np.sin(ph))
    return w

def write_wav(name, data, vol=0.5):
    data = np.clip(data*vol, -1, 1)
    pcm = (data*32767).astype(np.int16)
    with wave.open(os.path.join(OUT, name), "w") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes(pcm.tobytes())

# click: short woody tick
n = int(SR*0.07)
write_wav("sfx_click.wav", tone(900, 0.07, "tri")*env(n, r=0.03), 0.35)
# move: soft whoosh-ish slide (two quick tones)
a = tone(330, 0.16, "sine", bend=0.6)*env(int(SR*0.16), r=0.12)
write_wav("sfx_move.wav", a, 0.3)
# coin: bright two-note pickup
c1 = tone(880, 0.09, "sine")*env(int(SR*0.09), r=0.06)
c2 = tone(1318, 0.14, "sine")*env(int(SR*0.14), r=0.09)
write_wav("sfx_coin.wav", np.concatenate([c1, c2]), 0.4)
# danger: low buzz drop
dgr = tone(220, 0.3, "square", bend=-0.45)*env(int(SR*0.3), r=0.22)
write_wav("sfx_danger.wav", dgr, 0.28)
# toll: short cash register tick-ding
t1 = tone(660, 0.05, "tri")*env(int(SR*0.05), r=0.04)
t2 = tone(990, 0.10, "sine")*env(int(SR*0.10), r=0.07)
write_wav("sfx_toll.wav", np.concatenate([t1, t2]), 0.35)
# claim region: rising triad
tr = np.concatenate([tone(523, 0.1)*env(int(SR*0.1), r=0.08),
                     tone(659, 0.1)*env(int(SR*0.1), r=0.08),
                     tone(784, 0.22)*env(int(SR*0.22), r=0.16)])
write_wav("sfx_claim.wav", tr, 0.42)
# win: little fanfare
fan = np.concatenate([tone(523, 0.12)*env(int(SR*0.12), r=0.1),
                      tone(659, 0.12)*env(int(SR*0.12), r=0.1),
                      tone(784, 0.12)*env(int(SR*0.12), r=0.1),
                      tone(1046, 0.4)*env(int(SR*0.4), r=0.3)])
write_wav("sfx_win.wav", fan, 0.45)

print("assets written to", OUT, "->", sorted(os.listdir(OUT)))
