import asyncio, base64, pathlib, io, json
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont
here = pathlib.Path(__file__).parent
font_b64 = base64.b64encode(pathlib.Path("tile/node_modules/@fontsource/dm-serif-display/files/dm-serif-display-latin-400-normal.woff2").read_bytes()).decode()
# Пути сосудов — из схемы Виллизиева круга (левая половина; правая — зеркально)
LEFT = [
    ("M130,178 L134,150", 17, "v"),                                   # ВСА
    ("M72,140 C60,128 50,116 38,100 M72,140 C60,150 50,162 40,178", 12, "v"),   # M2
    ("M134,150 C148,138 160,122 166,108", 12, "v"),                    # A1
    ("M166,108 C166,86 168,64 170,36", 12, "v"),                       # A2
    ("M134,150 C136,166 138,184 140,200", 9, "v"),                    # ЗСоА
    ("M180,212 C166,208 152,204 140,200", 12, "v"),                    # P1
    ("M140,200 C118,198 98,208 86,228 C76,244 72,262 74,284", 12, "v"),  # P2
    ("M180,318 C172,332 160,350 152,392", 14, "v"),                   # ПА
]
MID = [("M166,108 L194,108", 9, "v"), ("M180,212 L180,318", 17, "v")]
M1 = "M134,150 C112,148 92,146 72,140"
JS = r"""
async ([b64, left, mid, m1]) => {
  const buf = Uint8Array.from(atob(b64), ch => ch.charCodeAt(0)).buffer;
  const face = new FontFace("DMSD", buf); await face.load(); document.fonts.add(face);
  const S = 1024, c = document.createElement("canvas"); c.width = c.height = S;
  const x = c.getContext("2d");
  x.fillStyle = "#0e1113"; x.fillRect(0, 0, S, S);
  const W = 560, H = 680, R = 66, rad = d => d * Math.PI / 180;
  // карточка сзади
  x.save(); x.translate(522, 528); x.rotate(rad(6));
  x.shadowColor = "rgba(0,0,0,.45)"; x.shadowBlur = 40; x.shadowOffsetY = 16;
  x.beginPath(); x.roundRect(-W/2, -H/2, W, H, R); x.fillStyle = "#14191c"; x.fill();
  x.shadowColor = "transparent"; x.lineWidth = 4; x.strokeStyle = "#262e32"; x.stroke(); x.restore();
  // карточка спереди
  x.save(); x.translate(504, 504); x.rotate(rad(-2));
  x.shadowColor = "rgba(0,0,0,.5)"; x.shadowBlur = 48; x.shadowOffsetY = 20;
  x.beginPath(); x.roundRect(-W/2, -H/2, W, H, R); x.fillStyle = "#1b2125"; x.fill();
  x.shadowColor = "transparent"; x.lineWidth = 4; x.strokeStyle = "#313a3f"; x.stroke();
  x.save(); x.beginPath(); x.roundRect(-W/2, -H/2, W, H, R); x.clip();
  // мягкое свечение под схемой
  const g = x.createRadialGradient(0, 70, 20, 0, 70, 300); g.addColorStop(0, "rgba(124,192,221,.10)"); g.addColorStop(1, "rgba(124,192,221,0)");
  x.fillStyle = g; x.fillRect(-W/2, -H/2, W, H);
  x.restore();
  // надпись
  x.fillStyle = "#7cc0dd"; x.textAlign = "left"; x.textBaseline = "alphabetic";
  x.font = "72px DMSD"; x.fillText("CTA", -W/2 + 46, -H/2 + 100);
  // схема: 360×400 → по центру свободного места
  const sc = 1.5, cx = 0, cy = 92;
  x.save(); x.translate(cx - 180 * sc, cy - 214 * sc); x.scale(sc, sc);
  x.lineCap = "round"; x.lineJoin = "round";
  const stroke = (d, w, col) => { x.strokeStyle = col; x.lineWidth = w / sc; x.stroke(new Path2D(d)); };
  const both = (fn) => { fn(); x.save(); x.translate(360, 0); x.scale(-1, 1); fn(); x.restore(); };
  both(() => left.forEach(([d, w]) => stroke(d, w, "#aab4b9")));
  mid.forEach(([d, w]) => stroke(d, w, "#aab4b9"));
  // правая M1 — обычная, левая — «окклюзия»: оранжевая со свечением
  x.save(); x.translate(360, 0); x.scale(-1, 1); stroke(m1, 15, "#aab4b9"); x.restore();
  x.save(); x.shadowOffsetX = 0; x.shadowOffsetY = 0; x.shadowColor = "rgba(217,119,87,.95)"; x.shadowBlur = 34; stroke(m1, 19, "#d97757"); stroke(m1, 19, "#d97757"); x.restore();
  // срезы ВСА
  both(() => { x.beginPath(); x.arc(130, 178, 9, 0, Math.PI * 2); x.fillStyle = "#1b2125"; x.fill(); x.lineWidth = 7 / sc; x.strokeStyle = "#aab4b9"; x.stroke(); });
  x.restore();
  // подпись M1
  x.fillStyle = "#d97757"; x.font = "84px DMSD"; x.textAlign = "center";
  x.fillText("M1", cx + (110 - 180) * sc, cy + (124 - 214) * sc);
  x.restore();
  return c.toDataURL("image/png");
}
"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page()
        await pg.goto("file://" + str(here.resolve()))
        data = await pg.evaluate(JS, [font_b64, LEFT, MID, M1]); await b.close()
    big = Image.open(io.BytesIO(base64.b64decode(data.split(",", 1)[1]))).convert("RGB")
    big.save(here / "tile-1024.png", optimize=True)
    for n in (180, 192):
        big.resize((n, n), Image.LANCZOS).quantize(colors=128, dither=Image.Dither.NONE).save(here / f"icon-{n}.png", optimize=True)
    big.resize((400, 400), Image.LANCZOS).save(here / "icon-400.png", optimize=True)
    others = [Image.open(f).convert("RGB") for f in ("ctp/tile/tile-1024.png", "idm/tile/tile-1024.png", "vm/tile/tile-1024.png")]
    view = Image.new("RGB", (512 + 40 + 790, 560), (24, 30, 44))
    view.paste(big.resize((512, 512), Image.LANCZOS), (20, 24))
    wall = Image.new("RGB", (790, 560), (38, 52, 78)); d = ImageDraw.Draw(wall)
    mask = Image.new("L", (180, 180), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, 179, 179), radius=41, fill=255)
    fnt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
    items = [(others[0], "Перфузия"), (others[1], "Идиомы"), (others[2], "remember"), (big, "Артерии")]
    for i, (img, label) in enumerate(items):
        xx, yy = 20 + i * 190, 60
        wall.paste(img.resize((180, 180), Image.LANCZOS), (xx, yy), mask)
        w = d.textlength(label, font=fnt); d.text((xx + 90 - w / 2, yy + 192), label, font=fnt, fill=(245, 245, 245))
    small = [img.resize((60, 60), Image.LANCZOS) for img, _ in items]
    m60 = Image.new("L", (60, 60), 0); ImageDraw.Draw(m60).rounded_rectangle((0, 0, 59, 59), radius=14, fill=255)
    for i, sm in enumerate(small):
        wall.paste(sm, (20 + i * 190 + 60, 360), m60)
    view.paste(wall, (552, 0)); view.save(here / "look.png")
    print("ok", (here / "tile-1024.png").stat().st_size, (here / "icon-400.png").stat().st_size)
asyncio.run(main())
