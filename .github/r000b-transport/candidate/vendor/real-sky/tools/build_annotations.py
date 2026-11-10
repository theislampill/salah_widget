#!/usr/bin/env python3
"""Authored pedagogical line choices, not purported IAU official stick figures.
Endpoints are existing measured HIP sources. No asterism invents any star.
"""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
# Paths are deliberately compact bright-source skeletons, not complete mythological illustrations.
patterns=[
 ('Ori','Orion — main figure and belt',[[27989,25336,25930,24436,27366,26727,27989],[25930,26311,26727],[25336,26207,27989],[26311,26241]],'constellation-skeleton'),
 ('UMa','Big Dipper',[[54061,53910,58001,59774,54061],[59774,62956,65378,67301]],'asterism'),
 ('Cas','Cassiopeia — W',[[746,3179,4427,6686,8886]],'constellation-skeleton'),
 ('Cru','Crux — Southern Cross',[[61084,60718],[62434,59747]],'constellation-skeleton'),
 ('Cyg','Cygnus — Northern Cross',[[102098,100453,95947],[97165,100453,104732]],'asterism'),
 ('Lyr','Lyra — bright triangle',[[91262,92420,93194,91262]],'simplified-bright-skeleton'),
 ('Sco','Scorpius — head, body and tail',[[78401,80763,81266,82396,84143,85927,85696],[78820,80763],[78265,80763]],'constellation-skeleton'),
 ('Sgr','Sagittarius — Teapot',[[90185,89931,90496,92041,92855,93506,93864,90185],[93506,94141,92855],[89931,93085,90185]],'asterism'),
 ('Leo','Leo — bright body and sickle',[[49669,50583,54872,57632,54879,49669],[50583,50335,48455]],'simplified-bright-skeleton'),
 ('Tau','Taurus — head and horns',[[21421,20889,20455,20205,20894,21421],[20889,25428],[21421,26451]],'constellation-skeleton'),
 ('Aur','Auriga — pentagon',[[24608,28360,28380,25428,23015,24608]],'asterism'),
 ('Gem','Gemini — bright twin chains',[[36850,35550,32246,30343],[37826,36962,35350,31681],[35550,35350]],'simplified-bright-skeleton'),
 ('Peg','Great Square of Pegasus',[[113963,113881,677,1067,113963]],'asterism'),
 ('And','Andromeda — main chain',[[677,5447,9640]],'constellation-skeleton'),
 ('Per','Perseus — bright skeleton',[[14576,14328,15863,17358,18246,18532,15863],[15863,14668]],'simplified-bright-skeleton'),
 ('CMa','Canis Major — bright body',[[30324,32349,33579,34444,35904],[32349,34444]],'simplified-bright-skeleton'),
 ('CMi','Canis Minor — main pair',[[37279,36188]],'constellation-skeleton'),
 ('Boo','Boötes — bright kite',[[69673,72105,74666,73555,71075,71053,69673],[69673,67927]],'simplified-bright-skeleton'),
 ('Aql','Aquila — bright central chain',[[97278,97649,98036]],'simplified-bright-skeleton'),
 ('Cen','Centaurus — southern pointers',[[71683,68702]],'asterism'),
 ('Tri','Triangulum',[[8796,10064,10670,8796]],'constellation-skeleton'),
 ('Ari','Aries — principal stars',[[9884,8903,8832]],'constellation-skeleton'),
 ('SummerTriangle','Summer Triangle',[[91262,102098,97649,91262]],'multi-constellation-asterism'),
 ('WinterTriangle','Winter Triangle',[[27989,32349,37279,27989]],'multi-constellation-asterism'),
]
cat=json.loads((R/'data/bright-stars.json').read_text());ids={s['hip'] for s in cat['stars']}
missing={hip for _,_,paths,_ in patterns for p in paths for hip in p if hip not in ids}
if missing:raise ValueError(f'Unresolved endpoints: {missing}')
a={'schema':'salah-real-sky/annotations/1','licence':'CC-BY-SA-4.0','enabledByDefault':False,
 'status':'Authored compact chart annotations; NOT IAU official outlines, boundaries, physical connections, or an exhaustive sky culture.',
 'patterns':[{'id':id,'label':label,'kind':kind,'paths':paths} for id,label,paths,kind in patterns]}
(R/'data/annotations.json').write_text(json.dumps(a,indent=2,ensure_ascii=False)+'\n')
# A small cited alias subset. HIP remains the stable machine identity; these are common names,
# not a claim to exhaust the current IAU WGSN registry or to define component identities anew.
names={11767:'Polaris',32349:'Sirius',30438:'Canopus',69673:'Arcturus',91262:'Vega',24608:'Capella',24436:'Rigel',37279:'Procyon',27989:'Betelgeuse',25336:'Bellatrix',27366:'Saiph',25930:'Mintaka',26311:'Alnilam',26727:'Alnitak',97649:'Altair',102098:'Deneb',21421:'Aldebaran',80763:'Antares',37826:'Pollux',36850:'Castor',60718:'Acrux',65474:'Spica',113368:'Fomalhaut',54061:'Dubhe',53910:'Merak',59774:'Megrez',62956:'Alioth',65378:'Mizar',67301:'Alkaid',677:'Alpheratz',5447:'Mirach',9640:'Almaak',746:'Caph',3179:'Shedir',15863:'Mirphak',14576:'Algol',90185:'Kaus Australis',92855:'Nunki',85927:'Shaula',68702:'Hadar',71683:'Rigil Kent'}
(R/'data/common-names.json').write_text(json.dumps({'source':'ESA Hipparcos, Table ID6-1 Volume 13, Common Star Names','url':'https://www.cosmos.esa.int/web/hipparcos/common-star-names','names':names},indent=2)+'\n')
print(len(patterns),'patterns;',len({h for _,_,paths,_ in patterns for p in paths for h in p}),'unique measured endpoints;',len(names),'cited common aliases')
