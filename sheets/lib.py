import math
import design as D
W,H=431.8,279.4
CSS="""
.obj{stroke:#111;stroke-width:.5;fill:none;stroke-linejoin:round}
.thk{stroke:#111;stroke-width:.8;fill:none}
.thin{stroke:#111;stroke-width:.25;fill:none}
.hid{stroke:#444;stroke-width:.25;fill:none;stroke-dasharray:1.8 1}
.ctr{stroke:#444;stroke-width:.2;fill:none;stroke-dasharray:6 1.2 1 1.2}
.dim{stroke:#111;stroke-width:.2;fill:none}
.wl{stroke:#2a6fb5;stroke-width:.3;fill:none;stroke-dasharray:3 1.5}
.t{font:2.4px Arial,Helvetica,sans-serif;fill:#111}
.tb{font:bold 2.4px Arial,Helvetica,sans-serif;fill:#111}
.ts{font:2px Arial,Helvetica,sans-serif;fill:#333}
.th{font:bold 3px Arial,Helvetica,sans-serif;fill:#111}
.cut{fill:url(#hatch);stroke:#111;stroke-width:.4}
.prop{fill:#f6e3c2;stroke:#8a5a12;stroke-width:.3}
.elec{fill:#d6efe6;stroke:#1d7a5c;stroke-width:.3}
.blade{fill:#e1defa;stroke:#5a4fc4;stroke-width:.35}
.gray{fill:#e4e4e4;stroke:#555;stroke-width:.3}
.water{fill:#cfe3f6}
"""
class Sheet:
    def __init__(s,no,title,sub,scale,rev=None):
        rev=rev or D.REV
        s.no,s.title,s.sub,s.scale,s.rev=no,title,sub,scale,rev; s.e=[]
    def add(s,x): s.e.append(x)
    def line(s,x1,y1,x2,y2,c='obj'): s.add(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" class="{c}"/>')
    def rect(s,x,y,w,h,c='obj',extra=''): s.add(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" class="{c}" {extra}/>')
    def poly(s,pts,c='obj',extra=''): s.add(f'<polygon points="{" ".join(f"{x:.2f},{y:.2f}" for x,y in pts)}" class="{c}" {extra}/>')
    def pline(s,pts,c='obj'): s.add(f'<polyline points="{" ".join(f"{x:.2f},{y:.2f}" for x,y in pts)}" class="{c}"/>')
    def circ(s,x,y,r,c='obj',extra=''): s.add(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" class="{c}" {extra}/>')
    def text(s,x,y,t,c='t',anchor='start',rot=0):
        tr=f' transform="rotate({rot} {x:.2f} {y:.2f})"' if rot else ''
        s.add(f'<text x="{x:.2f}" y="{y:.2f}" class="{c}" text-anchor="{anchor}"{tr}>{t}</text>')
    def arrow(s,x,y,dx,dy):
        L,Wd=1.8,0.6; n=math.hypot(dx,dy); ux,uy=dx/n,dy/n; px,py=-uy,ux
        s.add(f'<polygon points="{x:.2f},{y:.2f} {x-ux*L+px*Wd:.2f},{y-uy*L+py*Wd:.2f} {x-ux*L-px*Wd:.2f},{y-uy*L-py*Wd:.2f}" fill="#111"/>')
    def dimh(s,x1,x2,y,label,yo1=None,yo2=None,tdy=-0.9,anchor='middle'):
        if yo1 is not None: s.line(x1,yo1,x1,y+(1.2 if y>yo1 else -1.2),'dim')
        if yo2 is not None: s.line(x2,yo2,x2,y+(1.2 if y>yo2 else -1.2),'dim')
        s.line(x1,y,x2,y,'dim'); s.arrow(x1,y,1,0); s.arrow(x2,y,-1,0)
        s.text((x1+x2)/2,y+tdy,label,'t',anchor)
    def dimv(s,y1,y2,x,label,xo1=None,xo2=None,tdx=-0.9):
        if xo1 is not None: s.line(xo1,y1,x+(1.2 if x>xo1 else -1.2),y1,'dim')
        if xo2 is not None: s.line(xo2,y2,x+(1.2 if x>xo2 else -1.2),y2,'dim')
        s.line(x,y1,x,y2,'dim'); s.arrow(x,y1,0,1); s.arrow(x,y2,0,-1)
        s.text(x+tdx,(y1+y2)/2,label,'t','middle',-90)
    def tag(s,x,y,n):
        s.circ(x,y,2.3,'thin','style="fill:#fff"'); s.text(x,y+0.85,str(n),'tb','middle')
    def leader(s,x1,y1,x2,y2): s.line(x1,y1,x2,y2,'thin')
    def frame(s):
        out=[]
        out.append(f'<rect x="8" y="8" width="{W-16}" height="{H-16}" fill="none" stroke="#111" stroke-width=".8"/>')
        out.append(f'<text x="12" y="16.5" class="th">RC Recovery Barge</text>')
        out.append(f'<text x="{W-12}" y="16.5" class="th" text-anchor="end" style="font-size:4.2px">{s.title}</text>')
        out.append(f'<text x="{W-12}" y="21" class="ts" text-anchor="end">{s.sub}</text>')
        out.append(f'<line x1="8" y1="25" x2="{W-8}" y2="25" stroke="#111" stroke-width=".4"/>')
        x0,y0,w,h=W-8-146,H-8-30,146,30
        out.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="#fff" stroke="#111" stroke-width=".6"/>')
        for yy in (y0+10,y0+20): out.append(f'<line x1="{x0}" y1="{yy}" x2="{x0+w}" y2="{yy}" stroke="#111" stroke-width=".25"/>')
        out.append(f'<line x1="{x0+110}" y1="{y0+10}" x2="{x0+110}" y2="{y0+h}" stroke="#111" stroke-width=".25"/>')
        for xx in (x0+36,x0+72): out.append(f'<line x1="{xx}" y1="{y0+20}" x2="{xx}" y2="{y0+h}" stroke="#111" stroke-width=".25"/>')
        T=lambda x,y,t,c='t',a='start': out.append(f'<text x="{x}" y="{y}" class="{c}" text-anchor="{a}">{t}</text>')
        T(x0+2,y0+3.5,'PROJECT','ts'); T(x0+2,y0+8,D.PROJECT,'tb')
        T(x0+2,y0+13.5,'SHEET','ts'); T(x0+2,y0+18,s.title,'tb')
        T(x0+112,y0+13.5,'SHEET NO.','ts'); T(x0+112,y0+19,s.no,'th')
        T(x0+2,y0+23.5,'SCALE','ts'); T(x0+2,y0+28,s.scale,'t')
        T(x0+38,y0+23.5,'DATE','ts'); T(x0+38,y0+28,D.REV_DATE,'t')
        T(x0+74,y0+23.5,'REVISION','ts'); T(x0+74,y0+28,s.rev+', issued for review','t')
        T(x0+112,y0+23.5,'UNITS','ts'); T(x0+112,y0+28,'mm unless noted','t')
        return "\n".join(out)
    def svg(s):
        defs='<defs><pattern id="hatch" width="1.6" height="1.6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="1.6" stroke="#555" stroke-width=".25"/></pattern></defs>'
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">{defs}<rect width="{W}" height="{H}" fill="#fff"/>'+s.frame()+"\n".join(s.e)+'</svg>'
