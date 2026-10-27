def table(sh,x0,y0,cols,rows,title=None,rh=4.6):
    if title: sh.text(x0,y0-3,title,'tb')
    x=x0
    for n,w in cols:
        sh.rect(x,y0,w,rh,'thin','style="fill:#ececec"'); sh.text(x+1,y0+3.2,n,'tb'); x+=w
    for i,r in enumerate(rows):
        x=x0; y=y0+rh+i*rh
        for (n,w),v in zip(cols,r):
            sh.rect(x,y,w,rh,'thin'); sh.text(x+1,y+3.2,v,'t'); x+=w
    return y0+rh*(len(rows)+1)


def para(sh, x, y, text, width=52, c='t', step=4.2, hang=3):
    """Wrapped text block. Continuation lines are indented by `hang` mm. Returns the next free y."""
    import textwrap
    lines = textwrap.wrap(text, width)
    for i, ln in enumerate(lines):
        sh.text(x + (hang if i else 0), y, ln, c)
        y += step
    return y
