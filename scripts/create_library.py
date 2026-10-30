"""Build a curated variant library of 180 original Czech meal recipes.
No third-party recipe text or image downloads are used.
"""
from __future__ import annotations
import json, re, html, random, math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ING_CATEGORIES={
 'pohanková mouka':'Trvanlivé','ovesná mouka':'Trvanlivé','ovesné vločky':'Trvanlivé','rýžová mouka':'Trvanlivé','hladká mouka':'Trvanlivé','kukuřičná mouka':'Trvanlivé','kukuřičná krupice (polenta)':'Trvanlivé','rýže':'Trvanlivé','kulatozrnná rýže':'Trvanlivé','quinoa':'Trvanlivé','pohanka':'Trvanlivé','jáhly':'Trvanlivé','rýžové nudle':'Trvanlivé','těstoviny':'Trvanlivé','bezvaječné nudle':'Trvanlivé','bramborové noky':'Chlazené',
 'brambory':'Zelenina','cuketa':'Zelenina','mrkev':'Zelenina','dýně Hokkaido':'Zelenina','brokolice':'Zelenina','okurka':'Zelenina','červená řepa':'Zelenina','batáty':'Zelenina','květák':'Zelenina','salátová okurka':'Zelenina','ledový salát':'Zelenina','polníček':'Zelenina','petržel kořenová':'Zelenina','celer bulva':'Zelenina',
 'borůvky':'Ovoce','jablko':'Ovoce','meruňky':'Ovoce','broskev':'Ovoce','hruška':'Ovoce','meloun':'Ovoce',
 'tvaroh':'Mléčné','ricotta':'Mléčné','cottage':'Mléčné','mozzarella':'Mléčné','čerstvý kozí sýr':'Mléčné','žervé':'Mléčné','mléko bez laktózy':'Mléčné','máslo':'Mléčné',
 'vejce':'Vejce','kuřecí prsa':'Maso','krůtí prsa':'Maso','vepřová panenka':'Maso','hovězí kýta':'Maso','králičí maso':'Maso',
 'olivový olej':'Ostatní','řepkový olej':'Ostatní','javorový sirup':'Ostatní','sůl':'Ostatní','pažitka':'Bylinky','petrželka':'Bylinky','bazalka':'Bylinky','tymián':'Bylinky','kopr':'Bylinky','dýňová semínka':'Trvanlivé','slunečnicová semínka':'Trvanlivé'
}
UNITS={'vejce':'ks','jablko':'g','hruška':'g','broskev':'g','meruňky':'g','meloun':'g','olivový olej':'ml','řepkový olej':'ml','mléko bez laktózy':'ml','javorový sirup':'ml','sůl':'g','pažitka':'g','petrželka':'g','bazalka':'g','tymián':'g','kopr':'g'}
ALL=[]


def ingredient(name, amount):
 if name not in ING_CATEGORIES: raise KeyError(f'Unknown ingredient {name}')
 return {'name':name, 'amount':amount,'unit':UNITS.get(name,'g'), 'section':ING_CATEGORIES[name]}


def add(category, family, method, base, variants, minutes=25, protein='vegetarian', note='', season=None):
 """Each variant has (full title, extra ingredients, optional note)"""
 for i, entry in enumerate(variants,1):
  title, extra = entry[0],entry[1]
  addnote=entry[2] if len(entry)>2 else ''
  slug=re.sub('[^a-z0-9]+','-',family.lower().translate(str.maketrans('áčďéěíňóřšťúůýž','acdeeinorstuuyz'))).strip('-')
  rid=f'{category[:1]}-{slug}-{i}'
  ing=[ingredient(n,a) for n,a in base+extra]
  # Steps written around defined preparation method; whole recipe has explicit quantities in ingredients.
  steps=STEPS[method](base,extra)
  allergens=[]
  if any(n in {'tvaroh','ricotta','cottage','mozzarella','čerstvý kozí sýr','žervé','máslo','mléko bez laktózy'} for n,_ in base+extra):allergens.append('mléko')
  if any(n=='vejce' for n,_ in base+extra):allergens.append('vejce')
  if any(n in {'hladká mouka','těstoviny'} for n,_ in base+extra):allergens.append('lepek')
  ALL.append({'id':rid,'category':category,'family':family,'title':title,'description':addnote or note or 'Jednoduché jídlo z čerstvých surovin, vhodné k individuálnímu otestování tolerance.','minutes':minutes,'servings':2,'protein':protein,'season':season or ['all'], 'method':method,'ingredients':ing,'steps':steps,'allergens':allergens,'image':f'assets/img/{rid}.svg','image_kind':'originální ilustrace'})

def stepmix(base, extra):
 # make steps explicit and restrained, avoid false food science claims
 return ['Připrav a odvaž všechny suroviny podle seznamu pro dvě porce.', 'Základ zpracuj podle názvu pokrmu; zeleninu omyj a případně oloupej.', 'Přidej čerstvou náplň či přílohu těsně před podáváním.']

def st_pancake(base,extra):return ['Smíchej mouku s vejci a mlékem či vodou na hladké, spíše řidší těsto.','Na lehce vymazané nepřilnavé pánvi opékej malé palačinky z obou stran dozlatova.','Na ještě vlažné palačinky dej čerstvý sýr a připravené ovoce či zeleninu.']
def st_fritter(base,extra):return ['Syrovou zeleninu nebo brambory nastrouhej a dobře vymačkej přebytečnou tekutinu.','Promíchej s moukou a vejcem, ze směsi vytvaruj menší placičky.','Na troše oleje opékej z obou stran do propečení; podávej s čerstvou oblohou nebo sýrem.']
def st_wrap(base,extra):return ['Z mouky, asi 110 ml vody a oleje vypracuj hladké nekynuté těsto; rozděl na dvě placky.','Rozválej je tence a nasucho opeč na pánvi po obou stranách.','Naplň sýrem a omytou zeleninou, zabal a podávej čerstvé.']
def st_bake(base,extra):return ['Předehřej troubu na 180 °C a vylož malou formu pečicím papírem. Polentu nebo quinou (pokud je používáš) nejprve uvař podle návodu.','Promíchej těsto či zapékací směs ze surovin; ovoce nebo zeleninu vmíchej nakonec.','Peč přibližně 25–35 minut do zpevnění a propečení středu; podávej čerstvé.']
def st_omelet(base,extra):return ['Brambory (pokud jsou v surovinách) nejprve uvař doměkka; ostatní zeleninu nakrájej a krátce podus na pánvi.','Vejce rozšlehej se špetkou soli, nalij na zeleninu a zakryté propeč.','Na závěr případně přidej čerstvý sýr a podávej s připravenou přílohou.']
def st_potato(base,extra):return ['Brambory omyj, nakrájej na menší kousky a osuš.','Na plechu je pokapej trochou oleje a peč přibližně 25–35 minut při 200 °C doměkka.','Podávej se zvoleným čerstvým sýrem a zeleninou či bylinkami.']
def st_polenta(base,extra):return ['Polentu za stálého míchání uvař ve vodě do zhoustnutí (podle návodu na obalu). Tvrdší zeleninu uvař nebo upeč doměkka.','Rozetři ji do nižší vrstvy, nech ztuhnout a rozkrájej na plátky.','Plátky krátce opeč a podávej s čerstvým sýrem a zeleninou.']
def st_waffle(base,extra):return ['Z mouky, vajec a mléka vypracuj hustší těsto.','Vafle upeč ve vaflovači; bez vaflovače lze těsto péct jako malé silnější lívance.','Ozdob připraveným ovocem a čerstvým sýrem.']
def st_muffin(base,extra):return ['Předehřej troubu na 180 °C, formu na muffiny vymaž nebo vylož košíčky.','Smíchej vejce, mouku a najemno nasekanou zeleninu; těsto rozděl do formiček.','Peč asi 20–25 minut, dokud jsou muffiny uvnitř propečené.']
def st_balls(base,extra):return ['Z nastrouhaných brambor nebo tvarohového základu připrav soudržné těsto s moukou.','Utvoř malé taštičky či noky, uvař je v mírně vroucí osolené vodě do provaření.','Podávej s čerstvou ricottou, tvarohem nebo zeleninou uvedenou v surovinách.']
def st_salad(base,extra):return ['Obilninu propláchni a uvař podle návodu na obalu; nech krátce zchladnout.','Zeleninu dobře omyj, tvrdší zeleninu upeč nebo uvař doměkka.','Smíchej s čerstvým sýrem, bylinkami a trochou oleje; podávej hned.']
def st_risotto(base,extra):return ['Rýži krátce zahřej na troše oleje, postupně přilévej horkou vodu a míchej.','Zeleninu zvlášť podus nebo upeč doměkka.','Když je rýže měkká, vmíchej zeleninu a až při podávání čerstvý sýr; nepoužívej dlouho skladovaný vývar.']
def st_pasta(base,extra):return ['Těstoviny uvař v čerstvé vodě podle návodu a sceď.','Zeleninu nakrájej a krátce podus nebo orestuj do změknutí.','Promíchej s čerstvým sýrem, případně bylinkami; ihned podávej.']
def st_soup(base,extra):return ['Zeleninu nakrájej na stejnoměrné kostky a krátce orestuj na troše oleje.', 'Zalij čerstvou vodou, vař asi 15–25 minut doměkka a rozmixuj.', 'Pokud jsou uvedené polenta či pohanka, uvař je zvlášť podle návodu. Z mouky s vodou připrav placku a opeč ji na suché pánvi.', 'Podávej s připravenou přílohou nebo čerstvým sýrem; zbytky rychle zchlaď.']
def st_tray(base,extra):return ['Brambory, batáty či tvrdší zeleninu nakrájej na menší kusy a rozlož na plech. Čerstvou okurku nepeč.','Lehce zakápni olejem a peč v troubě při 190–200 °C do změknutí.','Přidej čerstvý sýr až nakonec, případně jen krátce zapeč.']
def st_rice(base,extra):return ['Rýži propláchni a uvař čerstvou těsně před podáváním.','Zeleninu nakrájej na drobno a krátce opeč na pánvi.','Smíchej s rýží a případně čerstvým sýrem či vejcem; ihned servíruj.']
def st_noodles(base,extra):return ['Rýžové nudle připrav podle návodu na obalu. Pokud recept obsahuje vejce, rozšlehej ho a propeč na pánvi zvlášť.','Zeleninu nakrájej na tenké nudličky a krátce orestuj na troše oleje.','Promíchej s nudlemi a čerstvými bylinkami; vynech fermentované omáčky.']
def st_gnocchi(base,extra):return ['Noky připrav podle obalu nebo z čerstvých uvařených brambor a mouky.','Zeleninu podus do změknutí v samostatné pánvi.','Noky krátce promíchej se zeleninou a čerstvým sýrem; podávej ihned.']
def st_meat(base,extra):return ['Čerstvé maso zpracuj co nejdříve po nákupu, případně použij správně rozmražené. Nakrájej ho na menší porce a osol.', 'Maso zprudka zatáhni na pánvi, poté podle tloušťky a druhu dopeč či podus do bezpečného propečení; u drůbeže zkontroluj propečení ve středu.', 'Mezitím uvař uvedenou rýži, pohanku nebo brambory a připrav zeleninu v páře či na plechu.', 'Podávej hned; neskladuj maso opakovaně ohřívané několik dní.']
def st_veg(base,extra):return ['Zeleninu očisti a nakrájej na menší porce.','Základní přílohu uvař podle návodu; zeleninu opeč či podus do změknutí.','Smíchej s čerstvým sýrem nebo vejcem podle surovin a ihned podávej.']

STEPS={
 'pancake':st_pancake,'fritter':st_fritter,'wrap':st_wrap,'bake':st_bake,'omelet':st_omelet,'potato':st_potato,'polenta':st_polenta,'waffle':st_waffle,'muffin':st_muffin,'balls':st_balls,'salad':st_salad,'risotto':st_risotto,'pasta':st_pasta,'soup':st_soup,'tray':st_tray,'rice':st_rice,'noodles':st_noodles,'gnocchi':st_gnocchi,'meat':st_meat,'veg':st_veg,
}

# 20 breakfast families x 3 variants
B='breakfast'
add(B,'pohankove-palacinky','pancake',[('pohanková mouka',150),('vejce',2),('mléko bez laktózy',220)], [('Pohankové palačinky s ricottou a borůvkami',[('ricotta',160),('borůvky',120)]),('Pohankové palačinky s tvarohem a meruňkami',[('tvaroh',180),('meruňky',130)]),('Pohankové palačinky s cottage a broskví',[('cottage',180),('broskev',120)])],25)
add(B,'ovesne-livance','pancake',[('ovesná mouka',160),('vejce',2),('mléko bez laktózy',180)], [('Ovesné lívance s borůvkami a tvarohem',[('tvaroh',180),('borůvky',100)]),('Ovesné lívance s ricottou a jablkem',[('ricotta',170),('jablko',90)]),('Ovesné lívance s meruňkami a ricottou',[('ricotta',170),('meruňky',130)])],20)
add(B,'bramborove-rosti','fritter',[('brambory',480),('vejce',1),('hladká mouka',45)], [('Bramborové rösti s cottage a pažitkou',[('cottage',180),('pažitka',10)]),('Bramborové rösti s čerstvým kozím sýrem',[('čerstvý kozí sýr',125)]),('Bramborové rösti s ricottou a okurkou',[('ricotta',150),('okurka',160)])],30)
add(B,'kukuricne-tortilly','wrap',[('kukuřičná mouka',180),('řepkový olej',15)], [('Kukuřičná tortilla s cottage a okurkou',[('cottage',190),('okurka',180)]),('Kukuřičná tortilla s mozzarellou a bazalkou',[('mozzarella',170),('bazalka',10)]),('Kukuřičná tortilla s ricottou a dušenou mrkví',[('ricotta',160),('mrkev',140)])],25)
add(B,'tvarohove-rezy','bake',[('tvaroh',280),('vejce',2),('ovesná mouka',90)], [('Tvarohový pečený řez s borůvkami',[('borůvky',120)]),('Tvarohový pečený řez s meruňkami',[('meruňky',130)]),('Tvarohový pečený řez s jablkem',[('jablko',100)])],40)
add(B,'slane-omelety','omelet',[('vejce',4),('řepkový olej',10)], [('Omeleta s cuketou a mozzarellou',[('cuketa',180),('mozzarella',100)]),('Omeleta s brokolicí a ricottou',[('brokolice',160),('ricotta',110)]),('Omeleta s dýní a pažitkou',[('dýně Hokkaido',170),('pažitka',10)])],20)
add(B,'pohankove-vafle','waffle',[('pohanková mouka',170),('vejce',2),('mléko bez laktózy',180)], [('Pohankové vafle s borůvkami a ricottou',[('borůvky',120),('ricotta',140)]),('Pohankové vafle s meruňkami a tvarohem',[('meruňky',140),('tvaroh',150)]),('Pohankové vafle s broskví a cottage',[('broskev',150),('cottage',150)])],25)
add(B,'pecene-brambory-rano','potato',[('brambory',500),('olivový olej',12)], [('Pečené brambory s cottage a pažitkou',[('cottage',190),('pažitka',10)]),('Pečené brambory s čerstvým kozím sýrem',[('čerstvý kozí sýr',140)]),('Pečené brambory s ricottou a bazalkou',[('ricotta',180),('bazalka',10)])],35)
add(B,'ovesne-rezy','bake',[('ovesné vločky',180),('vejce',2),('mléko bez laktózy',150)], [('Pečené ovesné řezy s borůvkami',[('borůvky',130)]),('Pečené ovesné řezy s jablkem',[('jablko',100)]),('Pečené ovesné řezy s meruňkami',[('meruňky',120)])],35)
add(B,'slane-muffiny','muffin',[('vejce',3),('ovesná mouka',135)], [('Slané muffiny s cuketou a ricottou',[('cuketa',180),('ricotta',140)]),('Slané muffiny s mrkví a mozzarellou',[('mrkev',180),('mozzarella',120)]),('Slané muffiny s brokolicí a cottage',[('brokolice',180),('cottage',140)])],30)
add(B,'pohankove-placky','pancake',[('pohanková mouka',170),('vejce',2),('mléko bez laktózy',170)], [('Slané pohankové placky s ricottou a pažitkou',[('ricotta',165),('pažitka',10)]),('Slané pohankové placky s cottage a okurkou',[('cottage',165),('okurka',140)]),('Slané pohankové placky s mozzarellou a cuketou',[('mozzarella',155),('cuketa',150)])],25)
add(B,'polentove-placky','polenta',[('kukuřičná krupice (polenta)',180)], [('Polentové plátky s ricottou a bazalkou',[('ricotta',170),('bazalka',8)]),('Polentové plátky s mozzarellou a cuketou',[('mozzarella',170),('cuketa',180)]),('Polentové plátky s čerstvým kozím sýrem',[('čerstvý kozí sýr',140),('pažitka',8)])],25)
add(B,'ryzove-palacinky','pancake',[('rýžová mouka',170),('vejce',2),('mléko bez laktózy',180)], [('Rýžové palačinky s borůvkovým tvarohem',[('borůvky',120),('tvaroh',170)]),('Rýžové palačinky s meruňkovou ricottou',[('meruňky',120),('ricotta',170)]),('Rýžové palačinky s broskví a cottage',[('broskev',130),('cottage',170)])],25)
add(B,'dynove-placicky','fritter',[('dýně Hokkaido',320),('brambory',220),('vejce',1),('hladká mouka',60)], [('Dýňovo-bramborové placičky s tvarohem',[('tvaroh',160)]),('Dýňovo-bramborové placičky s cottage',[('cottage',160)]),('Dýňovo-bramborové placičky s ricottou',[('ricotta',160)])],30)
add(B,'tvarohove-tasticky','balls',[('tvaroh',250),('hladká mouka',160),('vejce',1)], [('Tvarohové taštičky s borůvkami',[('borůvky',100)]),('Tvarohové taštičky s meruňkami',[('meruňky',120)]),('Tvarohové taštičky s broskví',[('broskev',120)])],35)
add(B,'cukete-placky','fritter',[('cuketa',370),('vejce',2),('pohanková mouka',95)], [('Cuketové placičky se žervé',[('žervé',140)]),('Ranní cuketové placičky s ricottou',[('ricotta',140)]),('Cuketové placičky s čerstvým kozím sýrem',[('čerstvý kozí sýr',130)])],25)
add(B,'kukuricne-placky','pancake',[('kukuřičná mouka',170),('vejce',2),('mléko bez laktózy',160)], [('Kukuřičné placky s mozzarellou',[('mozzarella',170)]),('Kukuřičné placky s tvarohem a pažitkou',[('tvaroh',170),('pažitka',10)]),('Kukuřičné placky s kozím sýrem a okurkou',[('čerstvý kozí sýr',140),('okurka',150)])],25)
add(B,'batatove-platky','potato',[('batáty',430),('olivový olej',10)], [('Pečené batátové plátky s ricottou',[('ricotta',160)]),('Pečené batátové plátky s cottage',[('cottage',170)]),('Pečené batátové plátky s mozzarellou',[('mozzarella',160)])],30)
add(B,'zeleninove-vajecne-muffiny','muffin',[('vejce',4),('pohanková mouka',110)], [('Vaječné muffiny s mrkví a pažitkou',[('mrkev',160),('pažitka',10)]),('Vaječné muffiny s cuketou a bazalkou',[('cuketa',150),('bazalka',10)]),('Vaječné muffiny s dýní a mozzarellou',[('dýně Hokkaido',155),('mozzarella',100)])],30)
add(B,'bramborove-noky-rano','balls',[('brambory',350),('hladká mouka',120),('vejce',1)], [('Bramborové noky s ricottou a pažitkou',[('ricotta',160),('pažitka',10)]),('Bramborové noky s cottage a bylinkami',[('cottage',160),('petrželka',10)]),('Bramborové noky s tvarohem a bazalkou',[('tvaroh',160),('bazalka',8)])],35)

# 20 lunch families x 3 variations; meat in three families
L='lunch'
add(L,'jemne-rizoto','risotto',[('kulatozrnná rýže',185),('olivový olej',15)], [('Dýňové rizoto s ricottou',[('dýně Hokkaido',350),('ricotta',140)]),('Mrkvové rizoto s mozzarellou',[('mrkev',280),('mozzarella',140)]),('Cuketové rizoto s čerstvým kozím sýrem',[('cuketa',340),('čerstvý kozí sýr',130)])],35)
add(L,'quinoovy-talir','salad',[('quinoa',180),('olivový olej',15)], [('Quinoa s pečenou dýní a cottage',[('dýně Hokkaido',340),('cottage',180)]),('Quinoa s červenou řepou a ricottou',[('červená řepa',320),('ricotta',160)]),('Quinoa s brokolicí a mozzarellou',[('brokolice',300),('mozzarella',170)])],35)
add(L,'bramborove-zapekanky','tray',[('brambory',550),('olivový olej',15)], [('Zapečené brambory s brokolicí a mozzarellou',[('brokolice',280),('mozzarella',180)]),('Zapečené brambory s cuketou a ricottou',[('cuketa',320),('ricotta',180)]),('Zapečené brambory s mrkví a kozím sýrem',[('mrkev',280),('čerstvý kozí sýr',150)])],45)
add(L,'pohankovy-hrnec','salad',[('pohanka',180),('řepkový olej',14)], [('Pohanka s mrkví a cottage',[('mrkev',250),('cottage',170)]),('Pohanka s dýní a ricottou',[('dýně Hokkaido',300),('ricotta',160)]),('Pohanka s cuketou a mozzarellou',[('cuketa',290),('mozzarella',160)])],30)
add(L,'testoviny-s-ricottou','pasta',[('těstoviny',200),('ricotta',200)], [('Penne s cuketou a ricottou',[('cuketa',280),('bazalka',8)]),('Fusilli s brokolicí a ricottou',[('brokolice',280),('pažitka',8)]),('Těstoviny s dýní a ricottou',[('dýně Hokkaido',300),('petrželka',8)])],25)
add(L,'polentove-obedy','polenta',[('kukuřičná krupice (polenta)',200)], [('Polenta s pečenou řepou a kozím sýrem',[('červená řepa',300),('čerstvý kozí sýr',150)]),('Polenta s cuketou a mozzarellou',[('cuketa',290),('mozzarella',170)]),('Polenta s dýní a cottage',[('dýně Hokkaido',290),('cottage',180)])],35)
add(L,'zeleninove-kremy','soup',[('brambory',180),('řepkový olej',12)], [('Dýňový krém s čerstvým sýrem',[('dýně Hokkaido',480),('ricotta',140)]),('Mrkvový krém s tvarohem',[('mrkev',460),('tvaroh',150)]),('Cuketový krém s mozzarellou',[('cuketa',480),('mozzarella',150)])],30)
add(L,'zeleninova-ryze','rice',[('rýže',190),('řepkový olej',14)], [('Rýže s mrkví a cuketou',[('mrkev',190),('cuketa',210),('vejce',2)]),('Rýže s dýní a brokolicí',[('dýně Hokkaido',220),('brokolice',200),('ricotta',130)]),('Rýže s červenou řepou a mozzarellou',[('červená řepa',250),('mozzarella',150)])],30)
add(L,'noky-se-zeleninou','gnocchi',[('bramborové noky',420)], [('Bramborové noky s cuketou a ricottou',[('cuketa',300),('ricotta',175)]),('Bramborové noky s mrkví a mozzarellou',[('mrkev',280),('mozzarella',160)]),('Bramborové noky s dýní a cottage',[('dýně Hokkaido',300),('cottage',175)])],25)
add(L,'pecene-bataty','tray',[('batáty',520),('olivový olej',12)], [('Pečené batáty s ricottou a petrželkou',[('ricotta',175),('petrželka',10)]),('Pečené batáty s cottage a okurkou',[('cottage',175),('okurka',150)]),('Pečené batáty s kozím sýrem',[('čerstvý kozí sýr',150),('pažitka',8)])],40)
add(L,'ryzove-nudle','noodles',[('rýžové nudle',200),('řepkový olej',15)], [('Rýžové nudle s cuketou a mrkví',[('cuketa',240),('mrkev',180),('vejce',2)]),('Jemné rýžové nudle s brokolicí a ricottou',[('brokolice',260),('ricotta',160)]),('Rýžové nudle s dýní a mozzarellou',[('dýně Hokkaido',250),('mozzarella',155)])],25)
add(L,'bramborove-placky','fritter',[('brambory',520),('hladká mouka',75),('vejce',2)], [('Bramborové placičky s tvarohem a pažitkou',[('tvaroh',180),('pažitka',10)]),('Bramborové placičky s ricottou a cuketou',[('ricotta',180),('cuketa',180)]),('Bramborové placičky s cottage a mrkví',[('cottage',180),('mrkev',170)])],30)
add(L,'jahlovy-talir','salad',[('jáhly',185),('olivový olej',12)], [('Jáhly s dýní a mozzarellou',[('dýně Hokkaido',310),('mozzarella',165)]),('Jáhly s cuketou a ricottou',[('cuketa',290),('ricotta',170)]),('Jáhly s brokolicí a cottage',[('brokolice',290),('cottage',170)])],30)
add(L,'pecena-zelenina-s-pohankou','veg',[('pohanka',180),('řepkový olej',15)], [('Pohanka s pečenou mrkví a ricottou',[('mrkev',330),('ricotta',150)]),('Pohanka s pečenou řepou a kozím sýrem',[('červená řepa',320),('čerstvý kozí sýr',150)]),('Pohanka s pečeným květákem a mozzarellou',[('květák',320),('mozzarella',150)])],40)
add(L,'vejce-s-bramborami','omelet',[('vejce',4),('brambory',420)], [('Bramborová frittata s cuketou',[('cuketa',270),('mozzarella',140)]),('Bramborová frittata s brokolicí',[('brokolice',260),('ricotta',140)]),('Bramborová frittata s dýní',[('dýně Hokkaido',260),('cottage',160)])],35)
add(L,'kukuricny-nakyp','bake',[('kukuřičná krupice (polenta)',180),('vejce',2)], [('Kukuřičný nákyp s brokolicí a mozzarellou',[('brokolice',280),('mozzarella',150)]),('Kukuřičný nákyp s cuketou a cottage',[('cuketa',280),('cottage',175)]),('Kukuřičný nákyp s dýní a ricottou',[('dýně Hokkaido',280),('ricotta',165)])],45)
add(L,'kureci-obed','meat',[('kuřecí prsa',320),('řepkový olej',12)], [('Kuřecí prso s bramborami a mrkví',[('brambory',510),('mrkev',300)]),('Kuřecí prso s rýží a cuketou',[('rýže',180),('cuketa',310)]),('Kuřecí prso s pohankou a dýní',[('pohanka',175),('dýně Hokkaido',315)])],35,'meat')
add(L,'kruti-obed','meat',[('krůtí prsa',320),('olivový olej',12)], [('Krůtí nudličky s rýžovými nudlemi a mrkví',[('rýžové nudle',190),('mrkev',280)]),('Krůtí plátek s quinou a brokolicí',[('quinoa',185),('brokolice',260)]),('Krůtí maso s pečenými batáty',[('batáty',490),('cuketa',235)])],35,'meat')
add(L,'hovezi-obed','meat',[('hovězí kýta',320),('řepkový olej',12)], [('Hovězí plátek s bramborovou kaší',[('brambory',540),('mrkev',245)]),('Hovězí plátek s pohankou a cuketou',[('pohanka',180),('cuketa',300)]),('Hovězí plátek s rýží a pečenou mrkví',[('rýže',180),('mrkev',320)])],50,'meat')
add(L,'zapecena-quinoa','bake',[('quinoa',185),('vejce',2)], [('Zapečená quinoa s brokolicí',[('brokolice',290),('ricotta',145)]),('Zapečená quinoa s dýní',[('dýně Hokkaido',290),('mozzarella',145)]),('Zapečená quinoa s mrkví',[('mrkev',280),('cottage',170)])],40)

D='dinner'
add(D,'cuketove-placicky','fritter',[('cuketa',440),('vejce',2),('pohanková mouka',100)], [('Cuketové placičky s pažitkovým tvarohem',[('tvaroh',170),('pažitka',12)]),('Cuketové placičky s ricottou',[('ricotta',175),('bazalka',8)]),('Cuketové placičky s cottage a okurkou',[('cottage',175),('okurka',170)])],30)
add(D,'kremova-dynova-polevka','soup',[('dýně Hokkaido',460),('brambory',160),('řepkový olej',10)], [('Dýňový krém s polentovými plátky',[('kukuřičná krupice (polenta)',115)]),('Dýňový krém s ricottou',[('ricotta',150)]),('Dýňový krém s pohankovými krutony',[('pohanka',110)])],30)
add(D,'bramborovy-plech','tray',[('brambory',560),('olivový olej',14)], [('Bramborový plech s cuketou a ricottou',[('cuketa',300),('ricotta',160)]),('Bramborový plech s mrkví a mozzarellou',[('mrkev',310),('mozzarella',160)]),('Bramborový plech s brokolicí a cottage',[('brokolice',290),('cottage',170)])],40)
add(D,'testoviny-bylinkove','pasta',[('těstoviny',195)], [('Těstoviny s ricottou a bazalkou',[('ricotta',200),('bazalka',15)]),('Těstoviny s cuketou a mozzarellou',[('cuketa',290),('mozzarella',170)]),('Těstoviny s brokolicí a tvarohem',[('brokolice',280),('tvaroh',180)])],25)
add(D,'pecene-korenove','tray',[('brambory',320),('řepkový olej',14)], [('Pečená mrkev s bramborami a kozím sýrem',[('mrkev',350),('čerstvý kozí sýr',155)]),('Pečená řepa s bramborami a ricottou',[('červená řepa',350),('ricotta',165)]),('Pečený celer s bramborami a mozzarellou',[('celer bulva',320),('mozzarella',165)])],45)
add(D,'pohankovy-talir-vecer','salad',[('pohanka',175),('olivový olej',12)], [('Pohankový talíř s dýní a mozzarellou',[('dýně Hokkaido',275),('mozzarella',160)]),('Pohankový talíř s mrkví a ricottou',[('mrkev',280),('ricotta',170)]),('Pohankový talíř s cuketou a cottage',[('cuketa',285),('cottage',170)])],30)
add(D,'jemne-zeleninove-noky','gnocchi',[('bramborové noky',420)], [('Noky s cuketou a žervé',[('cuketa',300),('žervé',165)]),('Noky s dýní a ricottou',[('dýně Hokkaido',290),('ricotta',170)]),('Noky s brokolicí a mozzarellou',[('brokolice',290),('mozzarella',165)])],25)
add(D,'rychle-nudle','noodles',[('rýžové nudle',185),('řepkový olej',12)], [('Rýžové nudle s cuketou a bazalkou',[('cuketa',290),('mozzarella',150),('bazalka',8)]),('Rýžové nudle s mrkví a vajíčkem',[('mrkev',280),('vejce',2)]),('Rýžové nudle s brokolicí a ricottou',[('brokolice',270),('ricotta',165)])],25)
add(D,'pecena-dyne-s-naplni','tray',[('dýně Hokkaido',480),('olivový olej',10)], [('Pečená dýně s cottage',[('cottage',180),('pažitka',8)]),('Pečená dýně s ricottou',[('ricotta',180),('bazalka',8)]),('Pečená dýně s kozím sýrem',[('čerstvý kozí sýr',150),('tymián',5)])],40)
add(D,'slana-polenta','polenta',[('kukuřičná krupice (polenta)',190)], [('Opečená polenta s mrkví a ricottou',[('mrkev',270),('ricotta',170)]),('Opečená polenta s cuketou a cottage',[('cuketa',280),('cottage',175)]),('Opečená polenta s brokolicí a mozzarellou',[('brokolice',280),('mozzarella',170)])],30)
add(D,'bramborove-frittaty','omelet',[('vejce',4),('brambory',340)], [('Frittata s cuketou a pažitkou',[('cuketa',260),('pažitka',12)]),('Frittata s brokolicí a mozzarellou',[('brokolice',260),('mozzarella',140)]),('Frittata s mrkví a cottage',[('mrkev',280),('cottage',150)])],30)
add(D,'peceny-batat','tray',[('batáty',500),('řepkový olej',12)], [('Batáty s ricottou a pažitkou',[('ricotta',170),('pažitka',8)]),('Batáty s mozzarellou a cuketou',[('mozzarella',160),('cuketa',260)]),('Batáty s cottage a čerstvou okurkou',[('cottage',175),('okurka',160)])],40)
add(D,'ryze-s-pecenou-zeleninou','rice',[('rýže',180),('řepkový olej',12)], [('Rýže s pečenou mrkví a vejcem',[('mrkev',280),('vejce',2)]),('Rýže s pečenou dýní a mozzarellou',[('dýně Hokkaido',280),('mozzarella',150)]),('Rýže s brokolicí a ricottou',[('brokolice',280),('ricotta',160)])],30)
add(D,'quinoa-s-jarnim-syrem','salad',[('quinoa',170)], [('Quinoa s okurkou, ricottou a bazalkou',[('okurka',190),('ricotta',170),('bazalka',8)]),('Quinoa s dýní, cottage a pažitkou',[('dýně Hokkaido',280),('cottage',170),('pažitka',8)]),('Quinoa s mrkví a čerstvým kozím sýrem',[('mrkev',280),('čerstvý kozí sýr',155)])],30)
add(D,'pecene-bramborove-noky','gnocchi',[('bramborové noky',400)], [('Pečené noky s cuketou a tvarohem',[('cuketa',290),('tvaroh',170)]),('Pečené noky s mrkví a ricottou',[('mrkev',290),('ricotta',160)]),('Pečené noky s dýní a mozzarellou',[('dýně Hokkaido',290),('mozzarella',160)])],30)
add(D,'zeleninove-kremy-vecer','soup',[('brambory',160),('řepkový olej',12)], [('Krém z cukety se sýrovou plackou',[('cuketa',480),('hladká mouka',120),('ricotta',100)]),('Krém z mrkve s pohankovými placičkami',[('mrkev',460),('pohanková mouka',140),('vejce',1)]),('Krém z brokolice s polentou',[('brokolice',440),('kukuřičná krupice (polenta)',140)])],30)
add(D,'zeleninove-nakypy','bake',[('vejce',3),('brambory',320)], [('Bramborový nákyp s cuketou a tvarohem',[('cuketa',290),('tvaroh',165)]),('Bramborový nákyp s mrkví a mozzarellou',[('mrkev',290),('mozzarella',170)]),('Bramborový nákyp s dýní a ricottou',[('dýně Hokkaido',290),('ricotta',170)])],45)
add(D,'pecena-mrkev-s-prilohou','veg',[('mrkev',350),('řepkový olej',12)], [('Pečená mrkev s pohankou a ricottou',[('pohanka',175),('ricotta',165)]),('Pečená mrkev s quinou a cottage',[('quinoa',175),('cottage',170)]),('Pečená mrkev s rýží a kozím sýrem',[('rýže',175),('čerstvý kozí sýr',150)])],35)
add(D,'kruti-vecere','meat',[('krůtí prsa',320),('řepkový olej',12)], [('Krůtí plátek s dýňovým pyré',[('dýně Hokkaido',340),('brambory',230)]),('Krůtí nudličky s rýží a cuketou',[('rýže',180),('cuketa',280)]),('Krůtí maso s batáty a mrkví',[('batáty',370),('mrkev',250)])],35,'meat')
add(D,'veprova-vecere','meat',[('vepřová panenka',310),('olivový olej',12)], [('Vepřová panenka s pečenou řepou a bramborami',[('červená řepa',280),('brambory',390)]),('Vepřová panenka s rýží a brokolicí',[('rýže',180),('brokolice',270)]),('Vepřová panenka s pohankou a mrkví',[('pohanka',175),('mrkev',280)])],40,'meat')

assert len(ALL)==180, f'expected 180, got {len(ALL)}'
assert {r['category'] for r in ALL}=={'breakfast','lunch','dinner'}
for cat in ['breakfast','lunch','dinner']:
 assert sum(r['category']==cat for r in ALL)==60
 assert len({r['family'] for r in ALL if r['category']==cat})==20
assert len({r['id'] for r in ALL})==180

from collections import Counter
assert len({r['title'] for r in ALL})==180

(ROOT/'recipes'/'library.json').write_text(json.dumps({'version':1,'servings':2,'recipes':ALL},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Created',len(ALL),'recipes: 60 breakfast, 60 lunch, 60 dinner')
