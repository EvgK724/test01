# Схемы кровоснабжения мозга: встроенные SVG без стилей внутри — цвета задаёт CSS страницы.
# Каждый сосуд — <g class="seg" data-seg="ключ" data-evt="yes|maybe|no|na">: широкая прозрачная линия для нажатия
# и видимая линия. Правая половина — зеркальная копия левой (подписи — только слева).
import math

W = 360

def seg(key, d, evt="na", w=3):
    hit = "hit s" if w <= 1 else "hit"          # у тонких ветвей зона нажатия уже, чтобы не перекрывать стволы
    return (f'<g class="seg" data-seg="{key}" data-evt="{evt}">'
            f'<path class="{hit}" d="{d}"/><path class="ln w{w}" d="{d}"/></g>')

def reg(key, d, cls=""):
    """Область (бассейн, регион ASPECTS): нажимается вся площадь."""
    return f'<g class="seg reg{(" " + cls) if cls else ""}" data-seg="{key}"><path class="area" d="{d}"/></g>'

def mirror(inner):
    return f'<g class="r" transform="matrix(-1 0 0 1 {W} 0)">{inner}</g>'

def lbl(x, y, text, anchor="middle", cls="vl"):
    return f'<text class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}">{text}</text>'

def lbl2(x, y, lines, anchor="middle", cls="vl"):
    ts = "".join(f'<tspan x="{x}" dy="{0 if i == 0 else 14}">{t}</tspan>' for i, t in enumerate(lines))
    return f'<text class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}">{ts}</text>'

def svg(view, h, body, aria):
    return (f'<svg class="art" data-view="{view}" viewBox="0 0 {W} {h}" role="img" aria-label="{aria}">'
            + body + '</svg>')

# ——— 1. Виллизиев круг: вид снизу, лоб — вверху
def willis():
    left = "".join([
        # тонкие ветви внизу, стволы сверху: там, где зоны нажатия пересекаются, выигрывает ствол
        '<circle class="cut" cx="130" cy="178" r="7"/>',
        seg("lsa", "M118,148 L116,132 M106,147 L105,131 M94,145 L94,129", "na", 0),
        seg("pcom", "M134,150 C136,166 138,184 140,200", "na", 1),
        seg("sca", "M180,222 C160,224 136,230 116,240", "na", 1),
        seg("aica", "M180,276 C160,278 138,286 120,298", "na", 1),
        seg("pica", "M160,350 C140,352 118,360 104,372", "na", 1),
        seg("va", "M180,318 C172,332 160,350 152,392", "maybe", 3),
        seg("p2", "M140,200 C118,198 98,208 86,228 C76,244 72,262 74,284", "maybe", 2),
        seg("a2", "M166,108 C166,86 168,64 170,36", "no", 2),
        seg("m2", "M72,140 C60,128 50,116 38,100 M72,140 C60,150 50,162 40,178", "maybe", 2),
        seg("p1", "M180,212 C166,208 152,204 140,200", "maybe", 2),
        seg("a1", "M134,150 C148,138 160,122 166,108", "no", 2),
        seg("m1", "M134,150 C112,148 92,146 72,140", "yes", 3),
        seg("ica", "M130,178 L134,150", "yes", 4),
    ])
    mid = seg("acom", "M166,108 L194,108", "na", 1) + seg("ba", "M180,212 L180,318", "yes", 4)
    labels = "".join([
        lbl(118, 184, "ВСА", "end"), lbl(98, 164, "M1"), lbl(40, 145, "M2"),
        lbl(138, 112, "A1", "end"), lbl(158, 64, "A2", "end"), lbl(180, 128, "ПСоА"),
        lbl(144, 176, "ЗСоА", "start"), lbl(160, 197, "P1"), lbl(96, 258, "P2", "start"),
        lbl(122, 254, "ВМА", "start"), lbl(116, 306, "ПНМА", "end"), lbl(190, 262, "ОА", "start"),
        lbl(146, 386, "ПА", "end"), lbl(100, 380, "ЗНМА", "end"),
        lbl(180, 16, "лоб", cls="vl dim"),
    ])
    return svg("willis", 400, left + mirror(left) + mid + labels, "Виллизиев круг, вид снизу: ВСА, СМА, ПМА, ЗМА, основная и позвоночные артерии")

# ——— 2. ВСА: сегменты C1–C7, вид сбоку, лицо — слева
def ica():
    deco = "".join([
        '<path class="bone" d="M112,300 L300,300"/>',
        '<rect class="sinus" x="62" y="196" width="80" height="62" rx="18"/>',
        '<path class="ln w2 faint" d="M200,420 L200,398 M200,398 C190,388 178,376 168,366"/>',
        seg("oph", "M100,189 C88,185 76,183 64,184", "na", 1),
        seg("pcom", "M123,160 C140,162 158,166 176,172", "na", 1),
        seg("acha", "M123,152 C140,150 156,148 172,150", "na", 1),
        '<path class="ln w2 faint" d="M122,142 C112,128 104,116 98,104 M122,142 C134,128 146,118 160,110"/>',
    ])
    segs = "".join([
        seg("c1", "M200,398 C204,372 206,340 204,300", "maybe", 4),
        seg("c2", "M204,300 L204,282 C204,268 196,262 182,262 L142,262", "maybe", 4),
        seg("c3", "M142,262 C132,262 126,256 126,246", "maybe", 4),
        seg("c4", "M126,246 C126,232 120,228 108,228 L90,228 C76,228 70,214 76,204", "maybe", 4),
        seg("c5", "M76,204 C80,196 88,192 96,190", "maybe", 4),
        seg("c6", "M96,190 C108,188 118,182 122,172", "yes", 4),
        seg("c7", "M122,172 C124,162 124,152 122,142", "yes", 4),
    ])
    labels = "".join([
        lbl(216, 352, "C1", "start"), lbl(214, 284, "C2", "start"), lbl(150, 252, "C3", "start"),
        lbl(86, 250, "C4"), lbl(66, 205, "C5", "end"), lbl(128, 194, "C6", "start"), lbl(114, 160, "C7", "end"),
        lbl(60, 180, "глазная", "end"), lbl(182, 176, "ЗСоА", "start"), lbl(178, 150, "ПВА", "start"),
        lbl(94, 100, "ПМА", "end"), lbl(166, 108, "СМА", "start"),
        lbl(306, 296, "основание черепа", "end", "vl dim"), lbl(102, 276, "кавернозный синус", "middle", "vl dim"),
        lbl(212, 414, "бифуркация ОСА", "start", "vl dim"), lbl(16, 16, "← лицо", "start", "vl dim"),
    ])
    return svg("ica", 420, deco + segs + labels, "Внутренняя сонная артерия сбоку: сегменты C1–C7")

# ——— 3. СМА: сегменты M1–M4, фронтальный срез одного полушария (латерально — слева, середина — справа).
# M1 делится у порога островка на два ствола M2: верхний идёт по островку вверх, нижний — к нижней круговой борозде;
# каждый продолжается своим M3 (над лобно‑теменной и над височной покрышкой) и M4 на коре.
def mca():
    deco = "".join([
        '<path class="brain" d="M316,30 C236,12 120,20 66,70 C34,100 26,140 30,168 C60,170 96,180 112,190 C96,196 60,200 32,204 C28,236 44,268 82,282 C130,298 220,296 272,280 L316,270 Z"/>',
        '<path class="mid" d="M316,20 L316,290"/>',
        '<path class="gm" d="M120,150 C113,172 112,216 118,246"/>',
        '<ellipse class="nuc" cx="172" cy="196" rx="20" ry="30"/>',
        '<ellipse class="vent" cx="250" cy="122" rx="10" ry="22"/>',
    ])
    segs = "".join([
        seg("lsa", "M226,260 C220,240 196,226 186,214 M206,259 C200,240 184,226 176,218 M186,258 C182,240 170,228 166,222", "na", 0),
        seg("m4", "M34,168 C26,140 34,110 56,84 M36,206 C30,230 40,256 62,272", "no", 2),
        seg("m3", "M126,148 C108,140 84,146 70,158 C58,168 46,170 34,168 M98,262 C84,256 74,246 66,236 C56,222 46,212 36,207", "no", 2),
        seg("aca", "M262,262 C280,250 296,236 308,222 C310,180 310,120 306,60", "no", 2),
        seg("m2", "M150,254 C132,248 120,230 118,206 C118,182 120,162 126,148 M150,254 C136,262 116,266 98,262", "maybe", 3),
        seg("m1", "M262,262 C220,260 180,258 150,254", "yes", 3),
        seg("ica", "M262,304 L262,262", "yes", 4),
    ])
    labels = "".join([
        lbl(200, 280, "M1"), lbl(106, 214, "M2", "end"), lbl(124, 284, "M2"), lbl(88, 138, "M3"), lbl(72, 226, "M3"),
        lbl(22, 132, "M4", "end"), lbl(24, 250, "M4", "end"),
        lbl(206, 206, "перфоранты", "start"), lbl(296, 110, "ПМА", "end"), lbl(270, 318, "ВСА", "start"),
        lbl(190, 158, "базальные ганглии", "middle", "vl dim"), '<text class="vl dim" transform="translate(142,192) rotate(-90)" text-anchor="middle">островок</text>',
        lbl(322, 44, "середина", "end", "vl dim"),
    ])
    return svg("mca", 330, deco + segs + labels, "Средняя мозговая артерия на фронтальном срезе: M1, два ствола M2, M3, M4 и лентикулостриарные артерии")

# ——— 4. Вертебробазилярная система: вид спереди
def vb():
    ticks = "".join(f'<path class="bone" d="M124,{y} L148,{y}"/>' for y in (336, 310, 284, 258, 232))
    left = "".join([
        '<path class="ln w2 faint" d="M30,410 L150,410"/>',
        ticks,
        seg("pcom", "M140,34 C138,26 136,18 134,10", "na", 1),
        seg("sca", "M180,56 C160,58 138,62 120,68", "na", 1),
        seg("aica", "M180,128 C160,128 136,132 116,140", "na", 1),
        seg("pica", "M168,164 C152,158 130,160 110,166", "na", 1),
        seg("p2", "M140,34 C120,32 100,38 84,50", "maybe", 2),
        seg("p1", "M180,40 C166,38 152,36 140,34", "maybe", 2),
        seg("v1", "M120,410 C122,384 128,362 136,344", "na", 3),
        seg("v2", "M136,344 L136,230", "na", 3),
        seg("v3", "M136,230 C136,212 118,208 116,196 C114,184 130,178 148,178", "na", 3),
        seg("v4", "M148,178 C160,178 172,166 180,150", "maybe", 3),
    ])
    mid = seg("ba", "M180,150 L180,40", "yes", 4)
    labels = "".join([
        lbl(116, 382, "V1", "end"), lbl(126, 292, "V2", "end"), lbl(108, 214, "V3", "end"), lbl(180, 194, "V4"),
        lbl(104, 168, "ЗНМА", "end"), lbl(112, 146, "ПНМА", "end"), lbl(116, 74, "ВМА", "end"),
        lbl(160, 28, "P1"), lbl(80, 44, "P2", "end"), lbl(130, 12, "ЗСоА", "end"), lbl(190, 100, "ОА", "start"),
        lbl(152, 340, "C6", "start", "vl dim"), lbl(152, 236, "C2", "start", "vl dim"),
        lbl(30, 404, "подключичная", "start", "vl dim"),
    ])
    return svg("vb", 420, left + mirror(left) + mid + labels, "Вертебробазилярная система спереди: позвоночные артерии V1–V4, основная артерия и её ветви")

# ——— 5. Бассейны на аксиальном срезе (уровень тел боковых желудочков), лоб — вверху
def terr():
    outline = "M180,20 C110,20 44,72 38,170 C32,262 78,352 180,380 C282,352 328,262 322,170 C316,72 250,20 180,20 Z"
    aca = "M180,20 C150,20 124,30 106,44 C124,90 138,150 150,220 C156,250 162,272 168,290 L180,292 Z"
    pca = "M180,380 C140,370 108,352 86,330 C112,316 142,302 168,290 L180,292 Z"
    mca = ("M106,44 C80,60 42,110 39,170 C36,240 52,296 86,330 C112,316 142,302 168,290 "
           "C162,272 156,250 150,220 C138,150 124,90 106,44 Z")
    deep = "M124,160 C134,160 140,180 140,200 C140,220 134,240 124,240 C114,240 108,220 108,200 C108,180 114,160 124,160 Z"
    vent = "M172,150 C160,162 156,192 160,230 C162,244 168,252 174,254 L176,150 Z"
    left = reg("aca", aca, "t-aca") + reg("mca", mca, "t-mca") + reg("pca", pca, "t-pca") + reg("deep", deep, "t-deep")
    body = (left + mirror(left) + f'<path class="vent2" d="{vent}"/>' + mirror(f'<path class="vent2" d="{vent}"/>')
            + f'<path class="outline" d="{outline}"/><path class="mid" d="M180,20 L180,380"/>'
            + lbl(150, 78, "ПМА") + lbl(76, 204, "СМА") + lbl(134, 346, "ЗМА")
            + lbl2(124, 266, ["глубокие", "ветви"]) + lbl(180, 14, "лоб", cls="vl dim"))
    return svg("terr", 396, body, "Бассейны ПМА, СМА и ЗМА на аксиальном срезе")

# ——— 6. ASPECTS: две половины среза — уровень базальных ганглиев и над ними
def ring_sector(cx, cy, r1x, r1y, r2x, r2y, a0, a1, n=24):
    """Сектор кольца между двумя полуэллипсами; углы в градусах: 90 — вперёд (вверх), 180 — латерально (влево)."""
    pts_o = [(cx + r2x * math.cos(math.radians(a)), cy - r2y * math.sin(math.radians(a))) for a in
             [a0 + (a1 - a0) * i / n for i in range(n + 1)]]
    pts_i = [(cx + r1x * math.cos(math.radians(a)), cy - r1y * math.sin(math.radians(a))) for a in
             [a1 - (a1 - a0) * i / n for i in range(n + 1)]]
    pts = pts_o + pts_i
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"

def ellipse_path(cx, cy, rx, ry, rot=0):
    pts = []
    for i in range(36):
        t = 2 * math.pi * i / 36
        x, y = rx * math.cos(t), ry * math.sin(t)
        c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        pts.append((cx + x * c - y * s, cy + x * s + y * c))
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"

def aspects():
    def half(ox, level):
        cx, cy = ox + 166, 118          # точка на средней линии
        R2x, R2y, R1x, R1y = 150, 104, 112, 78
        out = []
        out.append(reg("x-aca" + level, ring_sector(cx, cy, R1x, R1y, R2x, R2y, 90, 118), "a-off"))
        out.append(reg("x-pca" + level, ring_sector(cx, cy, R1x, R1y, R2x, R2y, 242, 270), "a-off"))
        if level == "g":
            out.append(reg("am1", ring_sector(cx, cy, R1x, R1y, R2x, R2y, 118, 150)))
            out.append(reg("am2", ring_sector(cx, cy, R1x, R1y, R2x, R2y, 150, 205)))
            out.append(reg("am3", ring_sector(cx, cy, R1x, R1y, R2x, R2y, 205, 242)))
            out.append(reg("ai", ring_sector(cx, cy, 92, 64, 104, 72, 150, 205)))
            out.append(reg("al", ellipse_path(ox + 104, cy + 2, 17, 30, -8)))
            out.append(reg("ac", ellipse_path(ox + 138, cy - 34, 11, 16, 20)))
            out.append(reg("aic", "M{a},{b} L{c},{d} L{e},{f} L{g},{h} L{i},{j} L{k},{l} Z".format(
                a=ox + 124, b=cy - 30, c=ox + 130, d=cy - 26, e=ox + 128, f=cy + 2, g=ox + 136, h=cy + 32,
                i=ox + 129, j=cy + 36, k=ox + 120, l=cy + 2)))
            out.append(f'<path class="vent2" d="{ellipse_path(ox + 154, cy - 36, 7, 18, 10)}"/>')
            out.append(f'<path class="thal" d="{ellipse_path(ox + 150, cy + 30, 12, 20)}"/>')
        else:
            out.append(reg("am4", ring_sector(cx, cy, R1x, R1y, R2x, R2y, 118, 160)))
            out.append(reg("am5", ring_sector(cx, cy, R1x, R1y, R2x, R2y, 160, 205)))
            out.append(reg("am6", ring_sector(cx, cy, R1x, R1y, R2x, R2y, 205, 242)))
            out.append(f'<path class="vent2" d="{ellipse_path(ox + 152, cy, 8, 40)}"/>')
        out.append(f'<path class="mid" d="M{cx},{cy - R2y - 6} L{cx},{cy + R2y + 6}"/>')
        return "".join(out)
    body = half(0, "g") + half(184, "s")
    L = lambda x, y, t: lbl(x, y + 4, t, cls="vl on-reg")
    body += "".join([
        L(62, 44, "M1"), L(26, 122, "M2"), L(64, 196, "M3"), L(84, 114, "I"), L(104, 124, "L"),
        L(138, 88, "C"), L(126, 162, "IC"),
        L(246, 50, "M4"), L(212, 120, "M5"), L(248, 192, "M6"),
        lbl(88, 244, "базальные ганглии", cls="vl dim"), lbl(272, 244, "над ганглиями", cls="vl dim"),
    ])
    return svg("aspects", 250, body, "Регионы ASPECTS на двух уровнях: C, L, IC, I, M1–M3 и M4–M6")

VIEWS_SVG = {"willis": willis(), "ica": ica(), "mca": mca(), "vb": vb(), "terr": terr(), "aspects": aspects()}

if __name__ == "__main__":
    for k, v in VIEWS_SVG.items():
        print(k, len(v))
