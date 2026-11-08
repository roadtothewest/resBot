"""Precios por LCSC vía la API pública del cotizador de JLCPCB (sin login). Guarda precios_lcsc.json."""
import csv, json, sys, time, urllib.request
BOM = sys.argv[1]
URL = 'https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList'
def consulta(k):
    r = urllib.request.Request(URL, json.dumps({'keyword': k, 'currentPage': 1, 'pageSize': 5}).encode(), {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
    return json.load(urllib.request.urlopen(r, timeout=30))
out = {}
for f in csv.DictReader(open(BOM, newline='')):
    c = f['LCSC Part #']
    if c in out or not c: continue
    d = consulta(c)
    L = (d.get('data') or {}).get('componentPageInfo', {}).get('list') or []
    e = next((x for x in L if x.get('componentCode') == c), None)
    if e is None: out[c] = {'error': str(d)[:150]}; continue
    if not out: print(sorted(e.keys())[:60])
    out[c] = {'mpn': e.get('componentModelEn'), 'stock': e.get('stockCount'), 'precios': e.get('componentPrices') or e.get('componentPriceList'), 'tipo': e.get('componentLibraryType')}
    time.sleep(.25)
json.dump(out, open('precios_lcsc.json', 'w'), indent=0)
for c, v in out.items():
    p = v.get('precios') or []
    print(c, v.get('mpn'), v.get('stock'), [(q.get('startNumber'), q.get('productPrice')) for q in p][:6] if p else v)
