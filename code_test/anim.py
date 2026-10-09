import math, random, subprocess
from PIL import Image, ImageDraw, ImageFilter
W,H,FPS,S=1280,720,30,2
SW,SH=W*S,H*S
BLACK=(20,20,24); WHITE=(255,255,255); HALO=(150,162,195)
def lerp(a,b,t): return a+(b-a)*t
def clamp(x,a=0,b=1): return max(a,min(b,x))
def ease(t): t=clamp(t); return t*t*(3-2*t)
def easeout(t): t=clamp(t); return 1-(1-t)**3
def rot(v,deg):
    r=math.radians(deg); return (v[0]*math.cos(r)-v[1]*math.sin(r), v[0]*math.sin(r)+v[1]*math.cos(r))

# ---------- stickman rig (all sizes in output px; scaled by S when drawing) ----------
HEAD=40; BODY=60; BW=24; THIGH=40; SHIN=40; UARM=34; FARM=32; LW=6
def draw_stickman(d, x, y, pose, scale=1.0, helmet=False):
    """x,y = hip point in output px. pose: lean, thighL/R, kneeL/R, shL/R, elL/R (deg; 0 = straight down, + = toward screen-right),
    expr, look (eye offset -1..1), headtilt"""
    k=S*scale
    def P(p): return (p[0]*k+x*S - 0*k, p[1]*k+y*S) if False else (x*S+p[0]*k, y*S+p[1]*k)
    lean=pose.get('lean',0)
    up=rot((0,-1),lean)
    hip=(0,0); neck=(up[0]*BODY, up[1]*BODY)
    def limb(origin, a1, a2, l1, l2):
        j=(origin[0]+rot((0,1),-a1)[0]*l1, origin[1]+rot((0,1),-a1)[1]*l1)
        e=(j[0]+rot((0,1),-(a1+a2))[0]*l2, j[1]+rot((0,1),-(a1+a2))[1]*l2)
        return j,e
    lw=int(LW*k)
    # legs (behind body)
    for side in ('L','R'):
        j,e=limb(hip, pose.get('thigh'+side,0), -pose.get('knee'+side,0), THIGH, SHIN)
        c2=P(e); fx=(1 if side=='R' else -1)*7*k
        d.line([P(hip),P(j),P(e)],fill=HALO,width=lw+int(3.5*k),joint='curve'); d.line([c2,(c2[0]+fx,c2[1])],fill=HALO,width=lw+int(3.5*k))
        d.line([P(hip),P(j),P(e)],fill=BLACK,width=lw,joint='curve')
        for q in (j,e): r=lw/2; c=P(q); d.ellipse((c[0]-r,c[1]-r,c[0]+r,c[1]+r),fill=BLACK)
        # foot
        c=P(e); fx=(1 if side=='R' else -1)*7*k; d.line([c,(c[0]+fx,c[1])],fill=BLACK,width=lw)
    # body: white capsule with outline
    steps=14
    pts=[]
    a=(hip[0],hip[1]); b=neck
    for i in range(steps+1):
        t=i/steps; px=lerp(a[0],b[0],t); py=lerp(a[1],b[1],t)
        w=BW*(0.9+0.15*math.sin(t*math.pi))
        pts.append((px,py,w))
    # draw as thick line with outline
    outline=[P((p[0],p[1])) for p in pts]
    d.line(outline,fill=BLACK,width=int((BW*2+LW*1.2)*k),joint='curve')
    for c in (outline[0],outline[-1]):
        r=(BW+LW*0.6)*k; d.ellipse((c[0]-r,c[1]-r,c[0]+r,c[1]+r),fill=BLACK)
    d.line(outline,fill=WHITE,width=int(BW*2*k),joint='curve')
    for c in (outline[0],outline[-1]):
        r=BW*k; d.ellipse((c[0]-r,c[1]-r,c[0]+r,c[1]+r),fill=WHITE)
    # arms (in front)
    sh=(neck[0]-up[0]*14, neck[1]-up[1]*14)
    for side in ('L','R'):
        sgn=1 if side=='R' else -1
        o=(sh[0]+sgn*BW*0.95*rot((1,0),lean)[0], sh[1]+sgn*BW*0.95*rot((1,0),lean)[1])
        j,e=limb(o, pose.get('sh'+side,0), pose.get('el'+side,0), UARM, FARM)
        d.line([P(o),P(j),P(e)],fill=HALO,width=lw+int(3.5*k),joint='curve')
        d.line([P(o),P(j),P(e)],fill=BLACK,width=lw,joint='curve')
        for q in (j,e): r=lw/2; c=P(q); d.ellipse((c[0]-r,c[1]-r,c[0]+r,c[1]+r),fill=BLACK)
    # head
    hc=(neck[0]+up[0]*(HEAD-6), neck[1]+up[1]*(HEAD-6))
    c=P(hc); r=HEAD*k; o=LW*k
    d.ellipse((c[0]-r-o,c[1]-r-o,c[0]+r+o,c[1]+r+o),fill=BLACK)
    d.ellipse((c[0]-r,c[1]-r,c[0]+r,c[1]+r),fill=WHITE)
    look=pose.get('look',0); lookup=pose.get('lookup',0)
    ex=look*9*k; ey=-lookup*7*k
    expr=pose.get('expr','neutral')
    er=(5.5 if expr!='shock' else 7.5)*k
    for sx in (-12,12):
        ec=(c[0]+sx*k+ex, c[1]-4*k+ey)
        d.ellipse((ec[0]-er,ec[1]-er,ec[0]+er,ec[1]+er),fill=BLACK)
        d.ellipse((ec[0]-er*0.35+er*0.25,ec[1]-er*0.6,ec[0]+er*0.25+er*0.25,ec[1]-er*0.1),fill=WHITE)
    mc=(c[0]+ex*0.8, c[1]+15*k+ey*0.6)
    if expr=='smile':
        d.arc((mc[0]-11*k,mc[1]-9*k,mc[0]+11*k,mc[1]+5*k),20,160,fill=BLACK,width=int(4*k))
    elif expr=='happy':
        d.chord((mc[0]-12*k,mc[1]-10*k,mc[0]+12*k,mc[1]+10*k),0,180,fill=BLACK)
        d.chord((mc[0]-7*k,mc[1]+2*k,mc[0]+7*k,mc[1]+10*k),0,180,fill=(235,90,90))
    elif expr=='shock':
        d.ellipse((mc[0]-7*k,mc[1]-6*k,mc[0]+7*k,mc[1]+9*k),fill=BLACK)
    if pose.get('sweat'):
        sx,sy=c[0]+26*k,c[1]-18*k
        d.polygon([(sx,sy-9*k),(sx-6*k,sy+3*k),(sx+6*k,sy+3*k)],fill=(120,190,255)); d.ellipse((sx-6*k,sy-2*k,sx+6*k,sy+9*k),fill=(120,190,255))
    if helmet:
        hr=(HEAD+17)*k
        d.ellipse((c[0]-hr,c[1]-hr,c[0]+hr,c[1]+hr),outline=(200,230,255),width=int(4*k))
        d.arc((c[0]-hr*0.75,c[1]-hr*0.8,c[0]+hr*0.2,c[1]+hr*0.1),200,250,fill=(235,245,255),width=int(5*k))
    return P(hc)

def stand(**kw):
    p=dict(lean=0,thighL=-11,kneeL=0,thighR=11,kneeR=0,shL=-24,elL=-8,shR=24,elR=8,expr='neutral',look=0)
    p.update(kw); return p
def walk(ph,**kw):
    s=math.sin(ph)
    p=stand(thighL=28*s,kneeL=max(0,35*math.sin(ph+1.6)),thighR=-28*s,kneeR=max(0,35*math.sin(ph+1.6+math.pi)),
            shL=-22*s-8,elL=-15,shR=22*s+8,elR=15,lean=4,look=0.6)
    p.update(kw); return p
def legs_len(p,scale=1.0):
    # vertical hip height above feet for current leg pose
    def h(a1,a2): 
        return THIGH*math.cos(math.radians(a1))+SHIN*math.cos(math.radians(a1-a2))
    return scale*max(h(p['thighL'],p['kneeL']),h(p['thighR'],p['kneeR']))

# ---------- backgrounds ----------
random.seed(4)
STARS=[(random.uniform(0,W),random.uniform(0,H*0.75),random.uniform(0,6.3),random.uniform(0.6,2.2),random.uniform(1,2.4)) for _ in range(140)]
def sky(d,top,bot,h=H):
    for i in range(0,h*S,8):
        t=i/(h*S); c=tuple(int(lerp(top[j],bot[j],t)) for j in range(3)); d.rectangle((0,i,SW,i+8),fill=c)
def stars(d,t,ymax=1.0,dim=1.0):
    for x,y,ph,f,r in STARS:
        if y>H*ymax: continue
        a=0.45+0.55*(0.5+0.5*math.sin(t*f*2+ph)); a*=dim
        c=int(255*a); rr=r*S*(0.7+0.5*a)
        d.ellipse((x*S-rr,y*S-rr,x*S+rr,y*S+rr),fill=(c,c,min(255,c+20)))
def glow_circle(img,cx,cy,r,color,glow=2.2,strength=0.55):
    g=Image.new('RGBA',img.size,(0,0,0,0)); gd=ImageDraw.Draw(g)
    for i in range(10,0,-1):
        rr=r*(1+(glow-1)*i/10); al=int(255*strength*(1-i/10)**1.5)
        gd.ellipse(((cx-rr)*S,(cy-rr)*S,(cx+rr)*S,(cy+rr)*S),fill=color+(al,))
    g=g.filter(ImageFilter.GaussianBlur(10*S)); img.alpha_composite(g)
def moon_disc(d,cx,cy,r,t=0):
    d.ellipse(((cx-r)*S,(cy-r)*S,(cx+r)*S,(cy+r)*S),fill=(244,244,236))
    for (ox,oy,cr) in [(-0.3,-0.2,0.18),(0.25,0.15,0.12),(0.05,0.4,0.09),(-0.15,0.3,0.07),(0.35,-0.3,0.08)]:
        x=cx+ox*r; y=cy+oy*r; rr=cr*r
        d.ellipse(((x-rr)*S,(y-rr)*S,(x+rr)*S,(y+rr)*S),fill=(214,214,206))
def earth_disc(d,cx,cy,r):
    d.ellipse(((cx-r)*S,(cy-r)*S,(cx+r)*S,(cy+r)*S),fill=(64,140,230))
    for (ox,oy,w,h) in [(-0.35,-0.25,0.5,0.35),(0.2,0.1,0.45,0.5),(-0.2,0.35,0.3,0.2)]:
        x=cx+ox*r; y=cy+oy*r
        d.ellipse(((x-w*r/2)*S,(y-h*r/2)*S,(x+w*r/2)*S,(y+h*r/2)*S),fill=(86,190,96))
def hill(d,col,col2,base=560):
    pts=[(0,SH)]+[(x*S,(base+28*math.sin(x/210)+18*math.sin(x/97))*S) for x in range(0,W+20,20)]+[(SW,SH)]
    d.polygon(pts,fill=col)
    pts=[(0,SH)]+[(x*S,(base+60+16*math.sin(x/150+1))*S) for x in range(0,W+20,20)]+[(SW,SH)]
    d.polygon(pts,fill=col2)
def ground_y(x,base=560): return base+28*math.sin(x/210)+18*math.sin(x/97)
CRATERS=[(150,640,70),(520,672,46),(900,632,90),(1180,668,55),(700,700,30)]
def moon_ground(d,base=600):
    pts=[(0,SH)]+[(x*S,(base+6*math.sin(x/90))*S) for x in range(0,W+20,20)]+[(SW,SH)]
    d.polygon(pts,fill=(168,170,176))
    for x,y,r in CRATERS:
        d.ellipse(((x-r)*S,(y-r*0.28)*S,(x+r)*S,(y+r*0.28)*S),fill=(140,142,150))
        d.ellipse(((x-r*0.85)*S,(y-r*0.2)*S,(x+r*0.85)*S,(y+r*0.26)*S),fill=(150,152,160))

# ---------- particles ----------
class Dust:
    def __init__(s): s.P=[]
    def burst(s,x,y,t0,n=26,col=(205,205,210)):
        for _ in range(n):
            a=random.uniform(math.pi*1.05,math.pi*1.95); v=random.uniform(60,170)
            s.P.append([x,y,math.cos(a)*v,math.sin(a)*v*0.6,t0,random.uniform(3,7),col])
    def draw(s,d,t,g=40):
        for x,y,vx,vy,t0,r,col in s.P:
            dt=t-t0
            if dt<0 or dt>1.6: continue
            px=x+vx*dt; py=y+vy*dt+0.5*g*dt*dt
            al=1-dt/1.6; rr=r*(1+dt)*S
            c=tuple(int(lerp(160,col[i],al)) for i in range(3))
            d.ellipse((px*S-rr,py*S-rr,px*S+rr,py*S+rr),fill=c+(int(220*al),))

def finish(img,shake=(0,0),zoom=1.0,cx=0.5,cy=0.5,fade=1.0,flash=0.0):
    if zoom!=1.0 or shake!=(0,0):
        cw,ch=SW/zoom,SH/zoom; l=cx*SW-cw/2+shake[0]*S; tp=cy*SH-ch/2+shake[1]*S
        l=max(0,min(SW-cw,l)); tp=max(0,min(SH-ch,tp))
        img=img.crop((int(l),int(tp),int(l+cw),int(tp+ch)))
    o=img.convert('RGB').resize((W,H),Image.LANCZOS)
    if flash>0: o=Image.blend(o,Image.new('RGB',(W,H),(255,255,255)),clamp(flash))
    if fade<1: o=Image.eval(o,lambda v,k=clamp(fade):int(v*k))
    return o

# ---------- scenes ----------
dust=Dust()
def scene1(t):   # 0 - 5.0 : walk in at night, look up at Moon, point
    img=Image.new('RGBA',(SW,SH)); d=ImageDraw.Draw(img,'RGBA')
    sky(d,(10,18,48),(36,52,104)); stars(d,t,0.7)
    glow_circle(img,1010,150,70,(220,230,255),glow=2.6,strength=0.5); d=ImageDraw.Draw(img,'RGBA'); moon_disc(d,1010,150,70)
    hill(d,(40,92,70),(30,72,56))
    # walk
    wt=clamp(t/3.0); x=lerp(-60,520,ease(wt)) if t<3.0 else 520
    if t<3.0:
        p=walk(t*7.5); bob=3*abs(math.cos(t*7.5))
    else:
        tt=t-3.0
        p=stand(look=0.7,lookup=ease(tt/0.4),headtilt=0)
        p['expr']='shock' if 0.3<tt<1.1 else ('smile' if tt>=1.1 else 'neutral')
        # point at moon with right arm
        a=ease((tt-0.9)/0.35)
        p['shR']=lerp(24,135,a); p['elR']=lerp(8,5,a); p['lean']=lerp(0,4,a)
        bob=0
    y=ground_y(x)-legs_len(p,1.5)-bob
    draw_stickman(d,x,y,p,scale=1.5)
    z=1.0+0.05*ease(t/5)
    return finish(img,zoom=z,cx=0.52,cy=0.5)
def zoom_trans(t):  # 5.0 - 5.6 : fast zoom into the Moon + flash
    img=Image.new('RGBA',(SW,SH)); d=ImageDraw.Draw(img,'RGBA')
    sky(d,(10,18,48),(36,52,104)); stars(d,5.0,0.7)
    glow_circle(img,1010,150,70,(220,230,255),glow=2.6,strength=0.5); d=ImageDraw.Draw(img,'RGBA'); moon_disc(d,1010,150,70)
    hill(d,(40,92,70),(30,72,56))
    u=ease(t/0.6); z=1.05+8*u**2
    return finish(img,zoom=z,cx=lerp(0.52,1010/W,u),cy=lerp(0.5,150/H,u),flash=clamp((u-0.55)/0.45))
def moon_bg(t):
    img=Image.new('RGBA',(SW,SH)); d=ImageDraw.Draw(img,'RGBA')
    sky(d,(4,6,16),(14,16,30)); stars(d,t,0.8)
    glow_circle(img,190,140,52,(120,180,255),glow=2.0,strength=0.45); d=ImageDraw.Draw(img,'RGBA'); earth_disc(d,190,140,52)
    moon_ground(d); return img,d
JUMP0,JUMP1=6.6,9.4
def scene2(t):   # 5.6 - 11.0 : big floaty Moon jump
    img,d=moon_bg(t)
    tt=t
    X=560 if tt<JUMP0 else (560+200*ease(clamp((tt-JUMP0)/(JUMP1-JUMP0))) if tt<JUMP1 else 760)
    gy=600+6*math.sin(X/90)
    if tt<6.1: p=stand(expr='smile',look=0); y=gy-legs_len(p,1.5)
    elif tt<JUMP0:   # crouch
        a=ease((tt-6.1)/0.5); p=stand(thighL=-35*a-6,kneeL=70*a,thighR=35*a+6,kneeR=70*a,shL=-12-40*a,shR=12+40*a,elL=-30*a,elR=30*a,expr='smile')
        p['thighL']=-6-30*a; p['thighR']=6+30*a
        y=gy-legs_len(p,1.5)
    elif tt<JUMP1:   # airborne: low gravity parabola
        u=(tt-JUMP0)/(JUMP1-JUMP0); h=240*4*u*(1-u)
        p=stand(thighL=-10-10*math.sin(u*math.pi),kneeL=25*math.sin(u*math.pi),thighR=10+10*math.sin(u*math.pi),kneeR=25*math.sin(u*math.pi),
                shL=-125+18*math.sin(tt*5),elL=-15,shR=125-18*math.sin(tt*5),elR=15,expr='happy' if 0.15<u<0.85 else 'shock',lookup=0.3)
        y=gy-legs_len(p,1.5)-h
        # dotted trail
        for k in range(0,int(u*30)):
            uu=k/30; tx=560+200*ease(uu); ty=600-legs_len(stand(),1.5)-240*4*uu*(1-uu)+10
            r=3*S; d.ellipse((tx*S-r,ty*S-r,tx*S+r,ty*S+r),fill=(255,255,255,110))
    else:            # land + celebrate
        a=ease((tt-JUMP1)/0.35); b=ease((tt-JUMP1-0.35)/0.4)
        k=a*(1-b)
        p=stand(thighL=-6-30*k,kneeL=70*k,thighR=6+30*k,kneeR=70*k,shL=lerp(-150,-150,1),shR=150,elL=-10,elR=10,expr='happy')
        p['shL']=-125+15*math.sin(tt*9); p['shR']=125-15*math.sin(tt*9)
        y=gy-legs_len(p,1.5)
    if abs(tt-JUMP0)<1/FPS and not getattr(dust,'b1',0): dust.burst(560,gy,JUMP0); dust.b1=1
    if abs(tt-JUMP1)<1/FPS and not getattr(dust,'b2',0): dust.burst(760,gy,JUMP1,n=34); dust.b2=1
    draw_stickman(d,X,y,p,scale=1.5,helmet=True)
    dust.draw(d,tt)
    sh=(0,0)
    if 0<tt-JUMP1<0.3: k=6*(1-(tt-JUMP1)/0.3); sh=(random.uniform(-k,k),random.uniform(-k,k))
    return finish(img,shake=sh,zoom=1.0+0.04*ease((tt-5.6)/5.4))
def scene3(t):   # 11.0 - 15.5 : split screen Earth vs Moon jump
    img=Image.new('RGBA',(SW,SH)); d=ImageDraw.Draw(img,'RGBA')
    # left: Earth
    for i in range(0,SH,8):
        tt=i/SH; c=(int(lerp(110,190,tt)),int(lerp(180,225,tt)),int(lerp(245,250,tt))); d.rectangle((0,i,SW//2,i+8),fill=c)
    d.ellipse((90*S,70*S,170*S,150*S),fill=(255,214,90))
    d.rectangle((0,600*S,SW//2,SH),fill=(96,176,90)); d.rectangle((0,628*S,SW//2,SH),fill=(78,150,74))
    # right: Moon
    for i in range(0,SH,8):
        tt=i/SH; c=(int(lerp(4,14,tt)),int(lerp(6,16,tt)),int(lerp(16,30,tt))); d.rectangle((SW//2,i,SW,i+8),fill=c)
    for x,y,ph,f,r in STARS:
        if x>W/2 and y<H*0.75:
            a=0.5+0.5*math.sin(t*f*2+ph); c=int(255*(0.4+0.6*a)); rr=r*S
            d.ellipse((x*S-rr,y*S-rr,x*S+rr,y*S+rr),fill=(c,c,c))
    earth_disc(d,1150,110,36)
    d.rectangle((SW//2,600*S,SW,SH),fill=(168,170,176)); d.ellipse((900*S,640*S,1060*S,676*S),fill=(150,152,160))
    d.line((SW//2,0,SW//2,SH),fill=(255,255,255),width=6*S)
    # jumpers
    tt=t-11.0
    gy=600
    # Earth: three quick hops of 0.55s, 60px
    pe=stand(expr='smile')
    he=0
    if 0.6<tt<0.6+3*0.6:
        u=((tt-0.6)%0.6)/0.6; he=60*4*u*(1-u)
        pe=stand(shL=-40,shR=40,elL=-20,elR=20,thighL=-12,thighR=12,kneeL=20,kneeR=20,expr='smile')
    elif tt>=0.6+3*0.6: pe=stand(expr='shock',look=0.8,sweat=True)
    draw_stickman(d,320,gy-legs_len(pe,1.1)-he,pe,scale=1.1)
    # Moon: one big slow jump of 2.7s, 330px
    pm=stand(expr='smile'); hm=0
    if 0.6<tt<3.3:
        u=(tt-0.6)/2.7; hm=260*4*u*(1-u)
        pm=stand(shL=-125,shR=125,elL=-15,elR=15,thighL=-15,thighR=15,kneeL=25,kneeR=25,expr='happy')
    elif tt>=3.3: pm=stand(expr='happy',shL=-125,shR=125,elL=-15,elR=15)
    draw_stickman(d,960,gy-legs_len(pm,1.1)-hm,pm,scale=1.1,helmet=True)
    # peak height markers (dotted lines that draw in)
    a=ease((tt-1.0)/0.6)
    if a>0:
        for (x0,x1,hh,col) in [(220,420,60,(255,90,90)),(860,1060,260,(255,214,0))]:
            yy=gy-legs_len(stand(),1.1)-hh-(BODY+2*HEAD+20)*1.1
            for xx in range(x0,int(lerp(x0,x1,a)),18):
                d.line((xx*S,yy*S,(xx+10)*S,yy*S),fill=col+(230,),width=4*S)
    return finish(img)
def scene4(t):   # 15.5 - 18.0 : wave goodbye on the Moon, fade
    img,d=moon_bg(t)
    tt=t-15.5; X=760; gy=600+6*math.sin(X/90)
    p=stand(expr='happy' if tt>0.4 else 'smile',look=0)
    p['shR']=130+20*math.sin(tt*10); p['elR']=25*math.sin(tt*10+1)
    y=gy-legs_len(p,1.5)
    draw_stickman(d,X,y,p,scale=1.5,helmet=True)
    z=1.0+0.25*ease(tt/2.5)
    return finish(img,zoom=z,cx=0.5,cy=0.62,fade=1-clamp((tt-1.8)/0.7))
SC=[(0,5.0,scene1),(5.0,5.6,lambda t:zoom_trans(t-5.0)),(5.6,11.0,scene2),(11.0,15.5,scene3),(15.5,18.0,scene4)]
def frame(t):
    for a,b,f in SC:
        if a<=t<b: return f(t)
    return SC[-1][2](SC[-1][1]-1e-3)
if __name__=='__main__':
    import sys
    out=sys.argv[1]; N=int(18.0*FPS)
    p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-preset','medium',out],stdin=subprocess.PIPE)
    for i in range(N): p.stdin.write(frame(i/FPS).tobytes())
    p.stdin.close(); p.wait()
