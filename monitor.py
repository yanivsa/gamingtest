#!/usr/bin/env python3
import json, os, sys, urllib.request
from copy import deepcopy
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'travel'/'data.json'
HISTORY=ROOT/'travel'/'history.jsonl'
ALERT=ROOT/'travel'/'alert.md'
TZ=ZoneInfo('Asia/Jerusalem')
ALLOWED_DEPART={'2026-09-27','2026-09-28'}
ALLOWED_RETURN={'2026-10-01','2026-10-02'}
DENY=('turkey','türkiye','טורקיה','egypt','jordan','uae','dubai','qatar','bahrain','morocco','tunisia','lebanon','oman','saudi','kuwait')

def now(): return datetime.now(TZ).replace(microsecond=0).isoformat()
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def save(p,obj): p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def validate(payload):
    deals=payload.get('deals',[])
    if len(deals)!=3: raise ValueError('provider payload must contain exactly 3 deals')
    cats=[d.get('category') for d in deals]
    if cats!=['BEST VALUE','BEST PRICE','SMART UPGRADE / SURPRISE']:
        raise ValueError('deal categories/order invalid')
    for d in deals:
        text=(d.get('destination','')+' '+d.get('country','')).lower()
        if any(x in text for x in DENY): raise ValueError('excluded destination detected')
        dep=d.get('departure_date'); ret=d.get('return_date')
        if dep not in ALLOWED_DEPART or ret not in ALLOWED_RETURN: raise ValueError('date outside hard Sukkot window')
        if ret=='2026-10-02' and not d.get('return_morning',False): raise ValueError('2 Oct return must be morning')
        if not d.get('flight_url') or not d.get('hotel_url'): raise ValueError('reproducible links required')
        if d.get('total_ils',0)<=0: raise ValueError('invalid total')
    return payload

def fetch_provider(url):
    req=urllib.request.Request(url,headers={'User-Agent':'family-travel-monitor/1.0'})
    with urllib.request.urlopen(req,timeout=45) as r:
        return json.loads(r.read().decode('utf-8'))

def meaningful(old,new):
    oldmap={d.get('stable_id'):d for d in old.get('deals',[])}
    events=[]
    for d in new.get('deals',[]):
        prev=oldmap.get(d.get('stable_id'))
        if not prev:
            events.append(f"NEW: {d.get('destination')} — ₪{d.get('total_ils'):,.0f}")
            continue
        before=float(prev.get('total_ils',0)); after=float(d.get('total_ils',0)); delta=after-before
        pct=(delta/before*100) if before else 0
        d['change_ils']=round(delta,2); d['change_pct']=round(pct,2)
        if delta<=-300 or pct<=-3:
            events.append(f"PRICE DROP: {d.get('destination')} {delta:,.0f} ₪ ({pct:.1f}%)")
    if old.get('deals') and new.get('deals') and old['deals'][0].get('stable_id')!=new['deals'][0].get('stable_id'):
        events.append('BEST VALUE changed')
    return events

def main():
    current=load(DATA)
    ts=now(); endpoint=os.getenv('TRAVEL_PROVIDER_JSON_URL','').strip()
    updated=deepcopy(current)
    updated.setdefault('automation',{})['last_attempt_at']=ts
    updated['generated_at']=ts
    events=[]
    if endpoint:
        try:
            incoming=validate(fetch_provider(endpoint))
            incoming.setdefault('automation',{})['status']='live'
            incoming['automation']['provider_mode']='external-live-provider'
            incoming['automation']['last_attempt_at']=ts
            incoming['automation']['last_verified_live_refresh']=ts
            incoming['generated_at']=ts
            events=meaningful(current,incoming)
            updated=incoming
        except Exception as e:
            updated['automation']['status']='degraded'
            updated['automation']['provider_mode']='last-known-good'
            updated['automation']['last_error']=str(e)[:300]
    else:
        updated['automation']['status']='foundation-live'
        updated['automation']['provider_mode']='awaiting-provider-adapters'
        updated['automation']['note']='Hourly runner works. Provider adapters are being implemented by Jules; last verified prices are preserved.'
    save(DATA,updated)
    with HISTORY.open('a',encoding='utf-8') as f:
        f.write(json.dumps({'at':ts,'status':updated['automation'].get('status'),'best':updated.get('deals',[{}])[0].get('stable_id'),'events':events},ensure_ascii=False)+'\n')
    if events:
        ALERT.write_text('# Travel deal alert\n\n'+'\n'.join('- '+e for e in events)+'\n',encoding='utf-8')
    elif ALERT.exists(): ALERT.unlink()
    print(json.dumps({'at':ts,'events':events,'status':updated['automation'].get('status')},ensure_ascii=False))

if __name__=='__main__': main()
