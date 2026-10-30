#!/usr/bin/env python3
"""Deterministic, offline, idempotent weekly meal planner with durable archive.
Requires Python standard library only; intended for GitHub Actions.
"""
from __future__ import annotations
import argparse, collections, datetime as dt, hashlib, json, random
from pathlib import Path
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1]
LIBRARY=ROOT/'recipes/library.json'
PLANS=ROOT/'plans'
INDEX=PLANS/'index.json'
KEYS=('breakfast','lunch','dinner')
LABELS=('Snídaně','Oběd','Večeře')
DAYS=('Pondělí','Úterý','Středa','Čtvrtek','Pátek','Sobota','Neděle')


def next_monday(today:dt.date)->dt.date:
    delta=(7-today.weekday())%7
    return today+dt.timedelta(days=delta or 7)

def read_json(path):return json.loads(path.read_text(encoding='utf-8'))
def save_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

def load_history():
    if not INDEX.exists():return []
    idx=read_json(INDEX)
    results=[]
    for w in idx.get('weeks',[]):
        fp=PLANS/w['file']
        if fp.exists():results.append(read_json(fp))
    return sorted(results,key=lambda p:p['week_start'],reverse=True)

def make_week(week_start:dt.date, recipes:list[dict], history:list[dict]):
    seed=int(hashlib.sha256(str(week_start).encode('ascii')).hexdigest()[:12],16)
    rng=random.Random(seed)
    by_cat={k:[r for r in recipes if r['category']==k] for k in KEYS}
    by_id={r['id']:r for r in recipes}
    prev=history[:8]
    used_ids=collections.Counter()
    last_id_ages={}
    family_ages={}
    for age,week in enumerate(prev):
        for day in week['days']:
            for meal in day['meals']:
                rid=meal['id']; fam=meal['family']
                used_ids[rid]+=1
                last_id_ages.setdefault(rid,age)
                family_ages.setdefault((meal['category'],fam),age)
    # One lunch and one dinner with meat: two meat-based mains for the whole week.
    meat_slots={'lunch':rng.choice([1,2,3]),'dinner':rng.choice([4,5,6])}
    chosen_ids=set(); chosen_families={k:set() for k in KEYS}
    selected_by_day=[]
    previous_methods=[]
    for day_idx in range(7):
        selected=[]
        for cat in KEYS:
            want_meat=(cat in meat_slots and day_idx==meat_slots[cat])
            pool=[r for r in by_cat[cat]
                  if (r['protein']=='meat')==want_meat
                  and r['id'] not in chosen_ids
                  and r['family'] not in chosen_families[cat]]
            if not pool:raise RuntimeError(f'No recipe pool for {cat} at {week_start}')
            def score(r):
                age=last_id_ages.get(r['id'],99)
                family_age=family_ages.get((cat,r['family']),99)
                recent_penalty=(12-age)*8 if age<6 else (8-age)*2 if age<8 else 0
                family_penalty=75 if family_age==0 else 20 if family_age==1 else 6 if family_age==2 else 0
                method_penalty=7 if r['method'] in [x['method'] for x in selected] else 0
                yesterday_penalty=4 if r['method'] in previous_methods else 0
                historic_penalty=used_ids[r['id']]*5
                # Jitter deterministic; prevents biased fixed order for ties.
                return recent_penalty+family_penalty+method_penalty+yesterday_penalty+historic_penalty+rng.random()*8
            recipe=min(pool,key=score)
            chosen_ids.add(recipe['id']); chosen_families[cat].add(recipe['family'])
            selected.append(recipe)
        previous_methods=[x['method'] for x in selected]
        selected_by_day.append({'date':str(week_start+dt.timedelta(days=day_idx)),
                                'day_name':DAYS[day_idx], 'meals':selected})
    meat_count=sum(m['protein']=='meat' for d in selected_by_day for m in d['meals'])
    assert meat_count==2
    basket={}
    for day in selected_by_day:
        for meal in day['meals']:
            for ing in meal['ingredients']:
                key=(ing['name'],ing['unit'])
                if key not in basket:
                    basket[key]={'name':ing['name'],'unit':ing['unit'],'amount':0,'section':ing['section']}
                basket[key]['amount']+=ing['amount']
    order=['Zelenina','Ovoce','Mléčné','Maso','Vejce','Trvanlivé','Chlazené','Bylinky','Ostatní']
    shopping=sorted(basket.values(),key=lambda x:(order.index(x['section']) if x['section'] in order else 99,x['name']))
    return {'schema_version':2,'week_start':str(week_start),
            'week_end':str(week_start+dt.timedelta(days=6)),
            'servings':2,'recipe_count':21,'meat_count':meat_count,
            'notes':['21 jídel pro 2 dospělé','Bez snídaňových kaší a rýžových chlebíčků','2 masová hlavní jídla za týden',
                     'Čerstvé mléčné výrobky a vejce podle vlastní tolerance; přísné vyřazování má být krátkodobé'],
            'days':selected_by_day,'shopping':shopping}

def generate(week_start:dt.date|None=None):
    if week_start is None:week_start=next_monday(dt.datetime.now(ZoneInfo('Europe/Prague')).date())
    if week_start.weekday()!=0:raise ValueError('The date must be a Monday (YYYY-MM-DD).')
    filename=f'{week_start.isoformat()}.json'
    target=PLANS/filename
    if target.exists():
        print(f'Week {filename} already exists; preserving history unchanged.')
        return False
    library=read_json(LIBRARY)['recipes']
    history=load_history()
    plan=make_week(week_start,library,history)
    save_json(target,plan)
    index=read_json(INDEX) if INDEX.exists() else {'schema_version':2,'weeks':[]}
    index['weeks']=[w for w in index.get('weeks',[]) if w['file']!=filename]
    index['weeks'].append({'file':filename,'start':str(week_start),'end':str(week_start+dt.timedelta(days=6)),
                            'meat_count':plan['meat_count'],'meals':21})
    index['weeks'].sort(key=lambda w:w['start'],reverse=True)
    save_json(INDEX,index)
    print(f'Created {filename}: 21 distinct recipes, 2 meat mains, {len(plan["shopping"])} grocery lines.')
    return True

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--week',default='',help='Monday start date YYYY-MM-DD (optional)')
    args=parser.parse_args()
    generate(dt.date.fromisoformat(args.week) if args.week else None)

if __name__=='__main__':main()
