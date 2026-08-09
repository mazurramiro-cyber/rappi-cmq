"""
build_data.py
Convierte todos los CSV de la carpeta scrapeos/ en un unico data.json
que lee la pagina (index.html). No necesita servidor.

Uso:  py build_data.py     (genera data.json)
"""
import csv, json, re
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent
SCRAPEOS_DIR = BASE / "scrapeos"
OUT_JSON = BASE / "data.json"

CMQ = ["1890","Bajo Cero","Pilsen","Quilmes","Brahma","Budweiser","Andes Origen","Andes","Michelob Ultra","Stella Artois","Corona","Patagonia","Quilmes 0","Stella Artois 0","Corona 0"]
COMP = ["Schneider","Amstel","Salta Cautiva","Salta","Imperial","Miller","Grolsch","Pampa","Heineken","Estrella Galicia","Blue Moon","Antares","Rabieta","Ortuzar","Cordoba","Warsteiner","Santa Fe","Starberg","Asahi","Kunstmann","Bitburger","Kostritzer","Guinness","Guinnes","Estrella Damm","Peroni","Sol","Temple","Goose Island"]
ALL = sorted(set(CMQ+COMP), key=len, reverse=True)
FIGHTS = [
 {"name":"1890 / Bajo Cero vs Ortuzar / Cordoba","cmq":["1890","Bajo Cero"],"comp":["Ortuzar","Cordoba"],"seg":"Value"},
 {"name":"Brahma vs Amstel","cmq":["Brahma"],"comp":["Amstel"],"seg":"Core"},
 {"name":"Quilmes vs Schneider","cmq":["Quilmes"],"comp":["Schneider"],"seg":"Core"},
 {"name":"Andes Origen vs Imperial","cmq":["Andes Origen","Andes"],"comp":["Imperial"],"seg":"Core+"},
 {"name":"Andes vs Miller","cmq":["Andes Origen","Andes"],"comp":["Miller"],"seg":"Core+"},
 {"name":"Michelob Ultra vs Miller","cmq":["Michelob Ultra"],"comp":["Miller"],"seg":"Core+"},
 {"name":"Budweiser vs Amstel","cmq":["Budweiser"],"comp":["Amstel"],"seg":"Core"},
 {"name":"Stella vs Pampa / Heineken / Grolsch","cmq":["Stella Artois","Stella Artois 0"],"comp":["Pampa","Heineken","Grolsch"],"seg":"Premium"},
]
BAD = ["pronto de vuelta","bebida refrescante remix","patrocinado","agregar"]
STYLE = [("sin alcohol","0.0"),("0 0","0.0"),("cero","0.0"),("ipa","ipa"),("apa","apa"),("pale ale","apa"),("cream stout","stout"),("stout","stout"),("amber","amber"),("roja","roja"),("red","roja"),("negra","negra"),("noire","negra"),("golden","golden"),("oro","golden"),("dorada","golden"),("honey","honey"),("kolsch","kolsch"),("scotch","scotch"),("pure gold","puregold"),("session","session"),("pilsner","lager"),("pilsen","lager"),("rubia","rubia"),("lager","lager"),("chopp","rubia"),("clasica","rubia"),("original","rubia"),("light","light"),("ultra","light"),("belgian white","witbier"),("schwarzbier","negra"),("extra","lager")]

def norm(s):
    s=(s or "").lower()
    for a,b in [("\u00e1","a"),("\u00e9","e"),("\u00ed","i"),("\u00f3","o"),("\u00fa","u"),("\u00f1","n")]: s=s.replace(a,b)
    return re.sub(r"[^a-z0-9]+"," ",s).strip()
def numf(v):
    try:
        if v in (None,""): return None
        return float(str(v).replace(",","."))
    except: return None
def ml_text(t):
    if not t: return None
    t=str(t).lower()
    m=re.search(r"(\d+(?:[\.,]\d+)?)\s*(ml|cc|cm3)\b",t)
    if m: return float(m.group(1).replace(",","."))
    m=re.search(r"(\d+(?:[\.,]\d+)?)\s*l\b",t)
    if m: return float(m.group(1).replace(",","."))*1000
    for c in re.findall(r"(\d{3,4})",t):
        v=int(c)
        if 200<=v<=2000: return float(v)
    return None
def bucket(ml):
    if ml is None: return "S/C"
    if 250<=ml<=290: return "275"
    if 320<=ml<=360: return "330/355"
    if 400<=ml<=420: return "410"
    if 450<=ml<=510: return "473"
    if 580<=ml<=620: return "600"
    if 690<=ml<=740: return "710/730"
    if 990<=ml<=1010: return "1000"
    return str(int(round(ml)))
def clean(s):
    s=str(s or ""); s=re.sub(r"\s+1\s*[xX]\s*\d+\s*(mL|ML|cc|CC)\b","",s); return re.sub(r"\s+"," ",s).strip()
def style_of(t):
    nd=norm(t)
    for kw,tok in STYLE:
        if kw in nd: return tok
    return "rubia"
def is_pack(t,dyn=""):
    nd=norm(t); nd2=norm(dyn)
    if "pack" in nd or "sixpack" in nd or "combo" in nd or nd2=="pack": return True
    if re.match(r"^\s*\d+\s*[xX]\s+",str(t or "")): return True
    return False
def infer(text):
    nd=norm(text)
    for b,pats in [("Stella Artois 0",["stella artois 0","stella artois cerveza 0"]),("Quilmes 0",["quilmes 0","quilmes 0 0"]),("Corona 0",["corona cerveza cero","corona 0 0","corona cero"])]:
        if any(p in nd for p in pats): return b
    for b in ALL:
        if norm(b) in nd: return "Guinness" if b=="Guinnes" else b
    if "cerveza fria" in nd: return "Andes Origen"
    return "Sin marca"
def parse_dyn(text,desc):
    m=re.search(r"(\d+(?:[\.,]\d+)?)\s*%\s*OFF",str(text or ""),re.I)
    if m:
        v=float(m.group(1).replace(",","."))
        return 0.0 if v>=100 else v/100
    v=numf(desc)
    if v is None or v>=100: return 0.0
    return v/100
def grupo(b): return "CMQ" if b in CMQ else "Competencia"
def seg(b):
    if b in ["1890","Bajo Cero","Pilsen","Ortuzar","Cordoba","Warsteiner"]: return "Value"
    if b in ["Quilmes","Brahma","Budweiser","Schneider","Amstel","Salta"]: return "Core"
    if b in ["Andes Origen","Andes","Michelob Ultra","Imperial","Miller","Salta Cautiva","Estrella Damm"]: return "Core+"
    if b in ["Stella Artois","Pampa","Heineken","Grolsch","Peroni"]: return "Premium"
    if b in ["Corona","Patagonia","Estrella Galicia","Blue Moon","Antares","Rabieta","Guinness","Asahi","Kunstmann","Bitburger","Kostritzer","Goose Island","Temple","Sol"]: return "Super Premium"
    if b in ["Quilmes 0","Stella Artois 0","Corona 0"]: return "Sin alcohol"
    return "Revisar"
def fecha_fn(p):
    m=re.search(r"(\d{4})(\d{2})(\d{2})",p.name)
    if m: return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d")

def read_csv(path,fecha):
    rows=[]
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        for rec in csv.DictReader(f,delimiter=";"):
            prod=rec.get("producto") or ""; desc=rec.get("descripcion") or ""; mcol=rec.get("marca") or ""
            texto=" ".join([x for x in [prod,desc,mcol] if x and x.strip() not in ("-","")]).strip()
            if not texto: continue
            dyn_text=rec.get("dinamica") or ""
            if is_pack(texto,dyn_text): continue
            marca=mcol.strip() if mcol.strip() not in ("-","") else infer(texto)
            if marca=="Guinnes": marca="Guinness"
            ntxt=norm(texto)
            if marca=="Sin marca" and "cerveza" not in ntxt: continue
            if "cerveza" not in ntxt and marca not in ALL: continue
            sku=clean(texto)
            if norm(sku) in BAD: continue
            ml=ml_text(rec.get("calibre")) or ml_text(texto)
            cal=bucket(ml)
            fleje=numf(rec.get("fleje")); d=parse_dyn(dyn_text,rec.get("descuento"))
            ptc=round(fleje*(1-d),2) if fleje is not None else numf(rec.get("precio"))
            rows.append({"fecha":fecha,"marca":marca,"sku":sku,"calibre":cal,"grupo":grupo(marca),"segmento":seg(marca),"fleje":fleje,"ptc":ptc,"dinamica":d,"sig":f"{marca}|{cal}|{style_of(texto)}"})
    return rows

def build():
    csvs=sorted(SCRAPEOS_DIR.glob("rappi_cervezas_*.csv"))
    by={}; dates=set(); tot=0
    for p in csvs:
        fecha=fecha_fn(p); dates.add(fecha)
        for r in read_csv(p,fecha):
            tot+=1; sig=r["sig"]
            e=by.setdefault(sig,{"marca":r["marca"],"sku":r["sku"],"calibre":r["calibre"],"grupo":r["grupo"],"segmento":r["segmento"],"dates":{}})
            if len(r["sku"])>len(e["sku"]): e["sku"]=r["sku"]
            old=e["dates"].get(fecha)
            if old is None or ((r["ptc"] or 1e18)<(old.get("ptc") or 1e18)):
                e["dates"][fecha]={"fleje":r["fleje"],"ptc":r["ptc"],"dinamica":r["dinamica"]}
    pivot=list(by.values()); dates=sorted(dates); ult=dates[-1] if dates else None
    pivot.sort(key=lambda x:(0 if (ult and ult in x["dates"]) else 1,x["segmento"],x["grupo"]!="CMQ",x["marca"],x["calibre"],x["sku"]))
    stats=[]
    for m in sorted({r["marca"] for r in pivot}):
        items=[r for r in pivot if r["marca"]==m]; pres=set(); dp=set(); dyns=[]; ptcs=[]
        for r in items:
            for dte,x in r["dates"].items():
                pres.add(dte)
                if (x.get("dinamica") or 0)>0: dp.add(dte)
                dyns.append(x.get("dinamica") or 0)
                if x.get("ptc") is not None: ptcs.append(x["ptc"])
        stats.append({"marca":m,"grupo":grupo(m),"segmento":seg(m),"dias":len(pres),"dias_dinamica":len(dp),"max_dinamica":max(dyns or [0]),"avg_dinamica":(sum(dyns)/len(dyns)) if dyns else 0,"avg_ptc":(sum(ptcs)/len(ptcs)) if ptcs else None})
    stats.sort(key=lambda x:(-x["dias_dinamica"],-x["max_dinamica"],x["marca"]))
    payload={"pivot":pivot,"dates":dates,"stats":stats,"fights":FIGHTS,"meta":{"generado":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"sku_rows":len(pivot),"registros_validos":tot,"dias":len(dates)}}
    OUT_JSON.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    return payload

if __name__=="__main__":
    d=build()
    print("[OK] data.json generado")
    print(f"     dias: {d['meta']['dias']} -> {d['dates']}")
    print(f"     SKUs: {d['meta']['sku_rows']}  registros: {d['meta']['registros_validos']}")
