import asyncio, base64, pathlib, io
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont
here = pathlib.Path(__file__).parent
font_b64 = base64.b64encode(pathlib.Path("tile/node_modules/@fontsource/dm-serif-display/files/dm-serif-display-latin-400-normal.woff2").read_bytes()).decode()
JS = r"""
async (b64) => {
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
  // rCBF < 30% сверху, крупно Tmax и > 6 s — по центру свободного места
  x.fillStyle = "#7cc0dd"; x.textAlign = "left"; x.textBaseline = "alphabetic";
  let fi = 68; x.font = fi + "px DMSD"; while (x.measureText("rCBF < 30%").width > W - 100){ fi -= 2; x.font = fi + "px DMSD"; } x.fillText("rCBF < 30%", -W/2 + 46, -H/2 + 104);
  const fit = (t, fs) => { x.font = fs + "px DMSD"; while (x.measureText(t).width > W - 104){ fs -= 4; x.font = fs + "px DMSD"; } return fs; };
  const fs = Math.min(fit("Tmax", 236), fit("> 6 s", 236));
  x.font = fs + "px DMSD";
  const m1 = x.measureText("Tmax"), m2 = x.measureText("> 6 s"), gap = fs * 0.22;
  const hh = m1.actualBoundingBoxAscent + m1.actualBoundingBoxDescent + gap + m2.actualBoundingBoxAscent + m2.actualBoundingBoxDescent;
  const y1 = 40 - hh / 2 + m1.actualBoundingBoxAscent;
  const y2 = y1 + m1.actualBoundingBoxDescent + gap + m2.actualBoundingBoxAscent;
  x.fillStyle = "#ececea"; x.fillText("Tmax", -W/2 + 50, y1);
  x.fillStyle = "#d97757"; x.fillText("> 6 s", -W/2 + 50, y2);
  x.restore();
  return c.toDataURL("image/png");
}
"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page()
        await pg.goto("file://" + str(here.resolve()))
        data = await pg.evaluate(JS, font_b64); await b.close()
    big = Image.open(io.BytesIO(base64.b64decode(data.split(",", 1)[1]))).convert("RGB")
    big.save(here / "tile-1024.png", optimize=True)
    for n in (180, 192):
        big.resize((n, n), Image.LANCZOS).quantize(colors=128, dither=Image.Dither.NONE).save(here / f"icon-{n}.png", optimize=True)
    big.resize((400, 400), Image.LANCZOS).save(here / "icon-400.png", optimize=True)
    others = [Image.open("num/tile/tile-1024.png").convert("RGB"), Image.open("hsd/tile/tile-1024.png").convert("RGB"), Image.open("vm/tile/tile-1024.png").convert("RGB")]
    view = Image.new("RGB", (512 + 40 + 790, 560), (24, 30, 44))
    view.paste(big.resize((512, 512), Image.LANCZOS), (20, 24))
    wall = Image.new("RGB", (790, 560), (38, 52, 78)); d = ImageDraw.Draw(wall)
    mask = Image.new("L", (180, 180), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, 179, 179), radius=41, fill=255)
    fnt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
    items = [(others[0], "Цифры"), (others[1], "have it done"), (others[2], "remember"), (big, "Перфузия")]
    for i, (img, label) in enumerate(items):
        xx, yy = 20 + i * 190, 60
        wall.paste(img.resize((180, 180), Image.LANCZOS), (xx, yy), mask)
        w = d.textlength(label, font=fnt); d.text((xx + 90 - w / 2, yy + 192), label, font=fnt, fill=(245, 245, 245))
    # реальный размер на iPhone — 60 pt
    small = [img.resize((60, 60), Image.LANCZOS) for img, _ in items]
    m60 = Image.new("L", (60, 60), 0); ImageDraw.Draw(m60).rounded_rectangle((0, 0, 59, 59), radius=14, fill=255)
    for i, s in enumerate(small):
        wall.paste(s, (20 + i * 190 + 60, 360), m60)
    view.paste(wall, (552, 0)); view.save(here / "look.png")
    print("ok", (here / "tile-1024.png").stat().st_size, (here / "icon-400.png").stat().st_size)
asyncio.run(main())
