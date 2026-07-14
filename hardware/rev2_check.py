import pcbnew
BW,BH=204.0,60.0
board=pcbnew.LoadBoard("imspi8080_rev2.kicad_pcb")
bb=board.GetBoardEdgesBoundingBox(); OX,OY=bb.GetX(),bb.GetY()
def cbb(f):
    lay=pcbnew.B_CrtYd if f.GetLayer()==pcbnew.B_Cu else pcbnew.F_CrtYd
    try:
        b=f.GetCourtyard(lay).BBox()
        if b.GetWidth()>0 and b.GetHeight()>0:
            return (pcbnew.ToMM(b.GetLeft()-OX),pcbnew.ToMM(b.GetTop()-OY),pcbnew.ToMM(b.GetRight()-OX),pcbnew.ToMM(b.GetBottom()-OY))
    except Exception: pass
    # fallback: union of pad bboxes
    l=t=1e9; r=bo=-1e9
    for p in f.Pads():
        pb=p.GetBoundingBox()
        l=min(l,pb.GetLeft());t=min(t,pb.GetTop());r=max(r,pb.GetRight());bo=max(bo,pb.GetBottom())
    return (pcbnew.ToMM(l-OX),pcbnew.ToMM(t-OY),pcbnew.ToMM(r-OX),pcbnew.ToMM(bo-OY))
boxes={f.GetReference():(cbb(f),"B" if f.GetLayer()==pcbnew.B_Cu else "F") for f in board.GetFootprints()}
off=[]
for ref,(bx,lay) in boxes.items():
    l,t,r,b=bx
    if l<-0.05 or t<-0.05 or r>BW+0.05 or b>BH+0.05:
        off.append((ref,round(l,1),round(t,1),round(r,1),round(b,1)))
M=0.15
def ov(a,b): return not(a[2]<=b[0]+M or b[2]<=a[0]+M or a[3]<=b[1]+M or b[3]<=a[1]+M)
refs=list(boxes); res=[]
for i in range(len(refs)):
    for j in range(i+1,len(refs)):
        ra,rb=refs[i],refs[j];(ba,la),(bc,lb)=boxes[ra],boxes[rb]
        if la==lb and ov(ba,bc): res.append((ra,rb,la))
print(f"OFF-BOARD ({len(off)}):")
for o in off:print("   ",o)
print(f"SAME-LAYER OVERLAPS ({len(res)}):")
for a,b,l in sorted(set(res)):print(f"    {a:4} <-> {b:4}  [{l}]  A={tuple(round(v,1) for v in boxes[a][0])} B={tuple(round(v,1) for v in boxes[b][0])}")
