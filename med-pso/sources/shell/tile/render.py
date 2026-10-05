# Иконка плитки в стиле модулей: две карточки, сверху синяя метка, ниже две строки — светлая и оранжевая.
# Запуск из sources/: python3 shell/tile/render.py <папка> <метка> <строка 1> <строка 2>
#   python3 shell/tile/render.py shell/tile "stroke" "time is" "brain"       — плитка «Медицина ПСО»
#   python3 shell/tile/render.py shell/tile-att "ATT" "OAC +" "ASA ?"     — иконка модуля «АТТ»
# Шрифт DM Serif Display — только латиница (sources/tile/node_modules/…).
import asyncio, base64, pathlib, io, sys
from playwright.async_api import async_playwright
from PIL import Image
out, label, line1, line2 = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
out.mkdir(parents=True, exist_ok=True)
font_b64 = base64.b64encode(pathlib.Path("tile/node_modules/@fontsource/dm-serif-display/files/dm-serif-display-latin-400-normal.woff2").read_bytes()).decode()
JS = r"""
async ([b64, label, l1, l2]) => {
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
  x.fillStyle = "#7cc0dd"; x.textAlign = "left"; x.textBaseline = "alphabetic";
  let fi = 68; x.font = fi + "px DMSD"; while (x.measureText(label).width > W - 100){ fi -= 2; x.font = fi + "px DMSD"; } x.fillText(label, -W/2 + 46, -H/2 + 104);
  const fit = (t, fs) => { x.font = fs + "px DMSD"; while (x.measureText(t).width > W - 104){ fs -= 4; x.font = fs + "px DMSD"; } return fs; };
  const fs = Math.min(fit(l1, 236), fit(l2, 236));
  x.font = fs + "px DMSD";
  const m1 = x.measureText(l1), m2 = x.measureText(l2), gap = fs * 0.22;
  const hh = m1.actualBoundingBoxAscent + m1.actualBoundingBoxDescent + gap + m2.actualBoundingBoxAscent + m2.actualBoundingBoxDescent;
  const y1 = 40 - hh / 2 + m1.actualBoundingBoxAscent;
  const y2 = y1 + m1.actualBoundingBoxDescent + gap + m2.actualBoundingBoxAscent;
  x.fillStyle = "#ececea"; x.fillText(l1, -W/2 + 50, y1);
  x.fillStyle = "#d97757"; x.fillText(l2, -W/2 + 50, y2);
  x.restore();
  return c.toDataURL("image/png");
}
"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page()
        await pg.goto("about:blank")
        data = await pg.evaluate(JS, [font_b64, label, line1, line2]); await b.close()
    big = Image.open(io.BytesIO(base64.b64decode(data.split(",", 1)[1]))).convert("RGB")
    big.save(out / "tile-1024.png", optimize=True)
    for n in (180, 192):
        big.resize((n, n), Image.LANCZOS).quantize(colors=128, dither=Image.Dither.NONE).save(out / f"icon-{n}.png", optimize=True)
    big.resize((400, 400), Image.LANCZOS).save(out / "icon-400.png", optimize=True)
    print("ok", out, (out / "icon-400.png").stat().st_size)
asyncio.run(main())
