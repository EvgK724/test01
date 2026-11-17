#!/usr/bin/env python3
"""Offline vector A4 renderer. Reads approved schedule only; never phones or notes.
Same render(months, root) API and top-left PDF baseline slots as browser renderer.
Bundled DejaVu fonts are licensed in fonts/LICENSE. No browser or network access.
"""
import calendar, datetime, json, pathlib, re, sys
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import simpleSplit
ROOT = pathlib.Path(__file__).resolve().parent.parent
MONTHS = 'Январь Февраль Март Апрель Май Июнь Июль Август Сентябрь Октябрь Ноябрь Декабрь'.split()
WEEK = ['ПН','ВТ','СР','ЧТ','ПТ','СБ','ВС']

def render(months, root=ROOT):
    root = pathlib.Path(root)
    fontdir = pathlib.Path(__file__).parent / 'fonts'
    for name, file in [('Duty','DejaVuSans.ttf'),('DutyBold','DejaVuSans-Bold.ttf')]:
        pdfmetrics.registerFont(TTFont(name, str(fontdir/file)))
    data = json.loads((root/'data/schedule.json').read_text())
    out = {}
    for mk in months:
        if not re.fullmatch(r'\d{4}-\d{2}',mk): raise ValueError('PDF_MONTH')
        year, mon = map(int,mk.split('-')); nd = calendar.monthrange(year,mon)[1]
        m = data['months'][mk]; order = m['order']; duty=m['duty']
        if not 1 <= len(order) <= 12 or len(set(order)) != len(order): raise ValueError('PDF_ROWS')
        dates = [f'{mk}-{d:02}' for d in range(1,nd+1)]
        if any(d not in dates or len(set(ids))!=len(ids) or any(i not in order for i in ids) for d,ids in duty.items()): raise ValueError('PDF_DUTY')
        # Fail rather than silently drop ambiguous/overlapping leave marks.
        marks={i:{} for i in order}
        for mark in m.get('marks',[]):
            who=mark['who']; a=datetime.date.fromisoformat(mark['from']); b=datetime.date.fromisoformat(mark['to'])
            if who not in marks or a>b: raise ValueError('PDF_MARK')
            covered=[d for d in dates if mark['from']<=d<=mark['to']]
            for d in covered:
                if d in marks[who] or who in duty.get(d,[]): raise ValueError('PDF_MARK_CONFLICT')
                marks[who][d]=mark['label']
        width,height=landscape(A4); left=8*mm; top=height-22*mm
        namew=44*mm; totalw=15*mm; dayw=(width-16*mm-namew-totalw)/nd
        rowh=10*mm; headerh=13*mm
        for slots in (False,True):
            path=root/'files'/f"{mk}{'-print' if slots else ''}.pdf"; path.parent.mkdir(parents=True,exist_ok=True)
            c=canvas.Canvas(str(path),pagesize=(width,height),invariant=1)
            title=f'ГРАФИК ДЕЖУРСТВ ПСО - {MONTHS[mon-1].upper()} {year}'
            if m.get('status')=='preliminary': title+=' (ПРЕДВАРИТЕЛЬНЫЙ)'
            c.setTitle(title); c.setAuthor(''); c.setSubject('График дежурств без телефонов')
            def text(tx,x,y,maxw,size=8,bold=False,center=False):
                font='DutyBold' if bold else 'Duty'; tx=str(tx)
                while size>6 and pdfmetrics.stringWidth(tx,font,size)>maxw-4: size-=.25
                if pdfmetrics.stringWidth(tx,font,size)>maxw-4: raise ValueError('PDF_TEXT_OVERFLOW')
                c.setFillColorRGB(.08,.12,.18);c.setFont(font,size)
                if center:c.drawCentredString(x+maxw/2,y,tx)
                else:c.drawString(x+2,y,tx)
            def cell(x,y,w,h,fill):
                c.setFillColorRGB(*fill);c.setStrokeColorRGB(.55,.60,.65);c.setLineWidth(.35);c.rect(x,y,w,h,fill=1,stroke=1)
            text(title,left,height-13*mm,width-16*mm,12,True)
            off=set(m.get('off',[])); slotsmap={}; legend={}
            cell(left,top-headerh,namew,headerh,(.89,.93,.96));text('Врач, телефон' if slots else 'Врач',left,top-headerh/2-3,namew,9,True)
            for j,d in enumerate(dates):
                x=left+namew+j*dayw;cell(x,top-headerh,dayw,headerh,(.95,.88,.85) if d in off else (.89,.93,.96))
                text(j+1,x,top-5*mm,dayw,8,True,True);text(WEEK[datetime.date.fromisoformat(d).weekday()],x,top-10*mm,dayw,6.5,False,True)
            tx=left+namew+nd*dayw;cell(tx,top-headerh,totalw,headerh,(.89,.93,.96));text('Всего',tx,top-headerh/2-3,totalw,8,True,True)
            for r,who in enumerate(order):
                y=top-headerh-(r+1)*rowh;bg=(.96,.97,.98) if r%2 else (1,1,1)
                cell(left,y,namew,rowh,bg); name=data['doctors'][who]['name'].upper()
                text(name,left,y+(6 if slots else 4)*mm,namew,8,True)
                if slots: slotsmap[who]=[round(left+2,2),round(height-(y+1.5*mm),2),round(namew-4,2)]
                for j,d in enumerate(dates):
                    x=left+namew+j*dayw;cell(x,y,dayw,rowh,(.98,.93,.90) if d in off else bg)
                    if who in duty.get(d,[]):text('+',x,y+3.4*mm,dayw,12,True,True)
                # Marks span consecutive equal labels, retaining actual leave text.
                j=0
                while j<nd:
                    label=marks[who].get(dates[j])
                    if label is None:j+=1;continue
                    k=j+1
                    while k<nd and marks[who].get(dates[k])==label:k+=1
                    x=left+namew+j*dayw;span=(k-j)*dayw;cell(x,y,span,rowh,(.91,.94,.91))
                    shown=label.upper()
                    if pdfmetrics.stringWidth(shown,'Duty',6)>span-4:
                        if shown not in legend:legend[shown]='М'+str(len(legend)+1)
                        shown=legend[shown]
                    text(shown,x,y+3.4*mm,span,7,False,True);j=k
                cell(tx,y,totalw,rowh,(.89,.93,.96));text(sum(who in duty.get(d,[]) for d in dates),tx,y+3.4*mm,totalw,9,True,True)
            y=top-headerh-(len(order)+1)*rowh
            cell(left,y,namew,rowh,(.89,.93,.96));text('Дежурных за день',left,y+3.4*mm,namew,8,True)
            for j,d in enumerate(dates):
                x=left+namew+j*dayw;cell(x,y,dayw,rowh,(.89,.93,.96));text(len(duty.get(d,[])),x,y+3.4*mm,dayw,8,True,True)
            cell(tx,y,totalw,rowh,(.89,.93,.96));text(sum(len(duty.get(d,[])) for d in dates),tx,y+3.4*mm,totalw,9,True,True)
            # Narrow one-day leave cells use a readable marker, never truncated text.
            ly=y-6*mm
            for label,marker in legend.items():
                for line in simpleSplit(marker+' - '+label,'Duty',8,width-16*mm-4):
                    if ly<8*mm:raise ValueError('PDF_LEGEND_OVERFLOW')
                    text(line,left,ly,width-16*mm,8);ly-=4*mm
            c.showPage();c.save()
            if slots:out[mk]=slotsmap
    return out
if __name__=='__main__':print(json.dumps(render(sys.argv[1:]),ensure_ascii=False))
