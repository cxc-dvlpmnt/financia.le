#!/usr/bin/env python3
"""financia.le — local private daily finance game. Python standard library only."""
import csv, io, json, math, os, random, re, sqlite3, sys, urllib.request, urllib.parse, threading, base64, hmac, time, logging
from datetime import date, datetime, timedelta
from calendar import monthrange
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parent
DB=Path(os.getenv('FINANCIA_DB',str(ROOT/'financia.db')))
DB.parent.mkdir(parents=True,exist_ok=True)
AUTH_USER=os.getenv('FINANCIA_USER','')
AUTH_PASS=os.getenv('FINANCIA_PASSWORD','')
if not AUTH_USER or not AUTH_PASS: raise RuntimeError('Set FINANCIA_USER and FINANCIA_PASSWORD on the server before starting')
ET=ZoneInfo('America/New_York')
FRED={
 'SP500':('S&P 500','Equity indices','index','return', 'daily'),
 'NASDAQCOM':('Nasdaq Composite','Equity indices','index','return','daily'),
 'DJIA':('Dow Jones Industrial Average','Equity indices','index','return','daily'),
 'NASDAQ100':('Nasdaq-100','Equity indices','index','return','daily'),
 'DGS2':('2-year Treasury yield','Rates','%','level','daily'),
 'DGS3':('3-year Treasury yield','Rates','%','level','daily'),
 'DGS5':('5-year Treasury yield','Rates','%','level','daily'),
 'DGS7':('7-year Treasury yield','Rates','%','level','daily'),
 'DGS10':('10-year Treasury yield','Rates','%','level','daily'),
 'DGS20':('20-year Treasury yield','Rates','%','level','daily'),
 'DGS30':('30-year Treasury yield','Rates','%','level','daily'),
 'DGS3MO':('3-month Treasury yield','Rates','%','level','daily'),
 'DFF':('Effective federal funds rate','Rates','%','level','daily'),
 'DPRIME':('U.S. prime rate','Rates','%','level','daily'),
 'T5YIE':('5-year breakeven inflation','Rates','%','level','daily'),
 'T10YIE':('10-year breakeven inflation','Rates','%','level','daily'),
 'T20YIEM':('20-year breakeven inflation','Rates','%','level','monthly'),
 'UNRATE':('U.S. unemployment rate','Macro','%','level','monthly'),
 'CPIAUCSL':('U.S. CPI','Inflation','index','change','monthly'),
 'CPILFESL':('U.S. core CPI','Inflation','index','change','monthly'),
 'PCEPI':('U.S. PCE price index','Inflation','index','change','monthly'),
 'PCEPILFE':('U.S. core PCE price index','Inflation','index','change','monthly'),
 'GDPC1':('U.S. real GDP','Macro','index','change','quarterly'),
 'GDP':('U.S. nominal GDP','Macro','index','change','quarterly'),
 'MORTGAGE15US':('15-year fixed mortgage rate','Rates','%','level','weekly'),
 'MORTGAGE30US':('30-year fixed mortgage rate','Rates','%','level','weekly'),
 'DEXUSEU':('EUR/USD','FX','USD per EUR','both','daily'),
 'DEXUSUK':('GBP/USD','FX','USD per GBP','both','daily'),
 'DEXJPUS':('USD/JPY','FX','JPY per USD','both','daily'),
 'DEXCAUS':('USD/CAD','FX','CAD per USD','both','daily'),
 'DEXCHUS':('USD/CNY','FX','CNY per USD','both','daily'),
 'DEXMXUS':('USD/MXN','FX','MXN per USD','both','daily'),
 'DEXSZUS':('USD/CHF','FX','CHF per USD','both','daily'),
 'DEXUSAL':('AUD/USD','FX','USD per AUD','both','daily'),
 'DCOILWTICO':('WTI crude oil','Commodities','USD/barrel','both','daily'),
 'DCOILBRENTEU':('Brent crude oil','Commodities','USD/barrel','both','daily'),
 'DHHNGSP':('Henry Hub natural gas spot price','Commodities','USD/MMBtu','both','daily'),
 'PCOPPUSDM':('Global copper price (IMF monthly)','Commodities','USD/metric ton','both','monthly'),
 'CSUSHPINSA':('Case-Shiller U.S. National Home Price Index (NSA)','Housing','index','change','monthly'),
 'HPIPONM226N':('FHFA U.S. Purchase-Only Home Price Index (NSA)','Housing','index','change','monthly'),
}
# OECD national share-price indexes via FRED: these are NOT MSCI benchmarks or USD returns.
INTERNATIONAL={
 'SPASTT01JPM661N':('Japan share-price index (OECD)','International indices','index','change','monthly'),
 'SPASTT01DEM661N':('Germany share-price index (OECD)','International indices','index','change','monthly'),
 'SPASTT01KRM661N':('Korea share-price index (OECD)','International indices','index','change','monthly'),
}
FRED.update(INTERNATIONAL)
# Stooq daily close data. These are explicitly named stocks/ETFs, not proprietary index returns.
# Stock/ETF Close is NOT assumed dividend-adjusted; label and provenance reflect that.
STOOQ_TICKERS={
 'AAPL':'Apple','MSFT':'Microsoft','NVDA':'NVIDIA','AMZN':'Amazon','GOOGL':'Alphabet (Class A)',
 'META':'Meta Platforms','BRK.B':'Berkshire Hathaway (Class B)','AVGO':'Broadcom','TSLA':'Tesla',
 'JPM':'JPMorgan Chase','WMT':'Walmart','LLY':'Eli Lilly','V':'Visa','MA':'Mastercard',
 'NFLX':'Netflix','COST':'Costco','XOM':'Exxon Mobil','JNJ':'Johnson & Johnson','PG':'Procter & Gamble',
 'HD':'Home Depot','ABBV':'AbbVie','BAC':'Bank of America','KO':'Coca-Cola','CVX':'Chevron',
 'ORCL':'Oracle','CRM':'Salesforce','AMD':'AMD','CSCO':'Cisco','IBM':'IBM','GE':'GE Aerospace',
 'CAT':'Caterpillar','MCD':'McDonald’s','UNH':'UnitedHealth','DIS':'Disney','PEP':'PepsiCo',
 'ABT':'Abbott Laboratories','MRK':'Merck','GS':'Goldman Sachs','MS':'Morgan Stanley',
 'AXP':'American Express','TMO':'Thermo Fisher','ISRG':'Intuitive Surgical','QCOM':'Qualcomm',
 'INTU':'Intuit','TXN':'Texas Instruments','AMGN':'Amgen','NOW':'ServiceNow',
 'UBER':'Uber','BKNG':'Booking Holdings','SPGI':'S&P Global',
}
# Frozen illustrative US-company universe; NOT claimed to be the actual top 50 by market cap.
STOOQ_ETFS={
 'EFA':('iShares MSCI EAFE ETF','International ETFs'),
 'EEM':('iShares MSCI Emerging Markets ETF','International ETFs'),
 'URTH':('iShares MSCI World ETF','International ETFs'),
 'ACWI':('iShares MSCI ACWI ETF','International ETFs'),
 'VEU':('Vanguard FTSE All-World ex-US ETF','International ETFs'),
 'AGG':('iShares Core U.S. Aggregate Bond ETF','Bond ETFs'),
 'BND':('Vanguard Total Bond Market ETF','Bond ETFs'),
 'TLT':('iShares 20+ Year Treasury Bond ETF','Bond ETFs'),
 'LQD':('iShares iBoxx $ Investment Grade Corporate Bond ETF','Bond ETFs'),
 'HYG':('iShares iBoxx $ High Yield Corporate Bond ETF','Bond ETFs'),
 'MBB':('iShares MBS ETF','Bond ETFs'),
 'GLD':('SPDR Gold Shares ETF','Commodity ETFs'),
 'SLV':('iShares Silver Trust ETF','Commodity ETFs'),
 'PPLT':('abrdn Physical Platinum Shares ETF','Commodity ETFs'),
}
STOOQ={}
STOOQ.update({'STOCK_'+k:(v+' stock closing-price return','Individual stocks','index','return','daily') for k,v in STOOQ_TICKERS.items()})
STOOQ.update({'ETF_'+k:(v+' closing-price return',group,'index','return','daily') for k,(v,group) in STOOQ_ETFS.items()})
CRYPTO={
 'KRAKEN_BTCUSD':('Bitcoin / USD (Kraken)','Crypto','USD','both','daily'),
 'KRAKEN_ETHUSD':('Ethereum / USD (Kraken)','Crypto','USD','both','daily'),
}
MSCI={}
CAT={**FRED,**STOOQ,**CRYPTO}
WEIGHTS={'Equity indices':18,'International indices':10,'Rates':20,'Macro':12,'Inflation':14,'FX':10,'Commodities':12,'Housing':7,'Individual stocks':20,'Bond indices':6,'Crypto':4,'International ETFs':10,'Bond ETFs':6,'Commodity ETFs':5}
LOCK=threading.RLock()

def conn():
 c=sqlite3.connect(DB,timeout=30)
 c.row_factory=sqlite3.Row
 c.execute('PRAGMA journal_mode=WAL')
 c.execute('CREATE TABLE IF NOT EXISTS observations (series TEXT NOT NULL, day TEXT NOT NULL, value REAL NOT NULL, source TEXT NOT NULL, fetched TEXT NOT NULL, PRIMARY KEY(series,day))')
 c.execute('CREATE TABLE IF NOT EXISTS games (day TEXT NOT NULL, mode TEXT NOT NULL, payload TEXT NOT NULL, created TEXT NOT NULL, PRIMARY KEY(day,mode))')
 c.commit();return c

def iso_now():return datetime.now(ET).isoformat()
def game_day():
 now=datetime.now(ET);return (now.date() if now.hour>=6 else now.date()-timedelta(days=1))
def shift(d,months):
 y=d.year+(d.month-1+months)//12;m=(d.month-1+months)%12+1
 return date(y,m,min(d.day,monthrange(y,m)[1]))
def previous(rows,target):
 for i in range(len(rows)-1,-1,-1):
  if rows[i][0]<=target:return i
 return None

def parse_csv(content,series):
 text=content.decode('utf-8-sig') if isinstance(content,bytes) else content
 reader=csv.DictReader(io.StringIO(text))
 if not reader.fieldnames:raise ValueError('CSV needs a header row')
 fields={x.lower().strip():x for x in reader.fieldnames}
 daycol=next((fields[k] for k in ('date','observation_date','day','observation date') if k in fields),None)
 valcol=next((fields[k] for k in ('value','close','index_level','level','price','adj close','adjusted_close',series.lower()) if k in fields),None)
 if not daycol or not valcol:raise ValueError('CSV needs date and value (or close) columns')
 out=[]
 for row in reader:
  try:
   d=date.fromisoformat(row[daycol].strip()[:10]);v=float(row[valcol].replace(',','').strip())
   if math.isfinite(v):out.append((d.isoformat(),v))
  except (ValueError,TypeError,AttributeError):continue
 if not out:raise ValueError('No valid dated numeric observations found')
 return out

def store(series,rows,source):
 with LOCK:
  c=conn()
  try:
   c.executemany('INSERT INTO observations VALUES(?,?,?,?,?) ON CONFLICT(series,day) DO UPDATE SET value=excluded.value,source=excluded.source,fetched=excluded.fetched',[(series,d,v,source,iso_now()) for d,v in rows]);c.commit()
  finally:c.close()
 return len(rows)

def fred_fetch(series,key):
 if key:
  qs=urllib.parse.urlencode({'series_id':series,'api_key':key,'file_type':'json','observation_start':'2000-01-01'})
  url='https://api.stlouisfed.org/fred/series/observations?'+qs
  req=urllib.request.Request(url,headers={'User-Agent':'financia.le personal app'})
  with urllib.request.urlopen(req,timeout=25) as r:data=json.load(r)
  if 'error_message' in data:raise ValueError(data['error_message'])
  rows=[]
  for x in data.get('observations',[]):
   try:
    v=float(x['value'])
    if math.isfinite(v):rows.append((x['date'],v))
   except (ValueError,KeyError):pass
  return rows
 raise ValueError('FRED_API_KEY is required; configure it as a server-side environment variable')

def stooq_fetch(symbol,key):
 if not key:raise ValueError('STOOQ_API_KEY not configured; get download access from Stooq')
 qs=urllib.parse.urlencode({'s':symbol.lower()+'.us','i':'d','d1':'20000101','d2':date.today().strftime('%Y%m%d'),'apikey':key})
 req=urllib.request.Request('https://stooq.com/q/d/l/?'+qs,headers={'User-Agent':'financia.le personal research contact via site'})
 with urllib.request.urlopen(req,timeout=30) as r:content=r.read(8_000_000)
 if not content.startswith(b'Date,'):raise ValueError('Stooq did not return daily-price CSV (check key, symbol or quota)')
 return parse_csv(content,symbol)

def kraken_fetch(pair):
 # Kraken public OHLC returns a limited recent window, not a complete historical archive.
 qs=urllib.parse.urlencode({'pair':pair,'interval':1440})
 req=urllib.request.Request('https://api.kraken.com/0/public/OHLC?'+qs,headers={'User-Agent':'financia.le personal game'})
 with urllib.request.urlopen(req,timeout=25) as r:data=json.load(r)
 if data.get('error'):raise ValueError(str(data['error']))
 result=data.get('result',{});keys=[k for k in result if k!='last']
 if len(keys)!=1:raise ValueError('Unexpected Kraken OHLC response')
 out=[];today=datetime.now(ZoneInfo('UTC')).date()
 for x in result[keys[0]]:
  d=datetime.fromtimestamp(int(x[0]),ZoneInfo('UTC')).date()
  if d>=today:continue # exclude still-forming daily candle
  v=float(x[4])
  if v>0 and math.isfinite(v):out.append((d.isoformat(),v))
 return out

def fetch_extra():
 results=[];key=os.getenv('STOOQ_API_KEY','').strip()
 if key:
  for sid in STOOQ:
   ticker=sid.split('_',1)[1]
   try:
    rows=stooq_fetch(ticker,key)
    if len(rows)<30:raise ValueError('Too few historical observations')
    results.append({'series':sid,'count':store(sid,rows,'Stooq daily Close (adjustment not guaranteed)'),'ok':True})
   except Exception as e:results.append({'series':sid,'ok':False,'error':str(e)[:170]})
   time.sleep(.25)
 for sid,pair in [('KRAKEN_BTCUSD','XBTUSD'),('KRAKEN_ETHUSD','ETHUSD')]:
  try:
   rows=kraken_fetch(pair)
   if len(rows)<30:raise ValueError('Too few Kraken observations')
   results.append({'series':sid,'count':store(sid,rows,'Kraken UTC daily close'),'ok':True})
  except Exception as e:results.append({'series':sid,'ok':False,'error':str(e)[:170]})
 return results

def fetch_all():
 key=os.getenv('FRED_API_KEY','').strip();results=[]
 for s in FRED:
  try:
   rows=fred_fetch(s,key)
   if not rows:raise ValueError('No observations returned')
   n=store(s,rows,'FRED');results.append({'series':s,'count':n,'ok':True})
  except Exception as e:results.append({'series':s,'ok':False,'error':str(e)[:170]})
 return results

def series_rows(c,s,cutoff):
 return [(date.fromisoformat(r['day']),r['value']) for r in c.execute('SELECT day,value FROM observations WHERE series=? AND day<? ORDER BY day',(s,cutoff.isoformat()))]

def fixture_rows(s,day):
 # Explicitly simulated DEMO data, deterministic across runs and dates.
 seed=sum((i+1)*ord(x) for i,x in enumerate(s)); rng=random.Random(seed)
 kind=CAT[s][3];freq=CAT[s][4]
 base= 1000 if kind=='return' else (4 if CAT[s][2]=='%' else (300 if kind=='change' else 80))
 if s in ('GDP','GDPC1'):base=20000
 if s.startswith('DEX'):base=140 if s=='DEXJPUS' else (7 if s=='DEXCHUS' else 1.2)
 if s.startswith('DCOIL'):base=65
 d=date(2010,1,1);v=base;out=[]
 while d<=day:
  if freq=='daily':valid=d.weekday()<5;step=timedelta(days=1)
  elif freq=='weekly':valid=d.weekday()==3;step=timedelta(days=1)
  elif freq=='monthly':valid=d.day==1;step=timedelta(days=1)
  else:valid=d.day==1 and d.month in (1,4,7,10);step=timedelta(days=1)
  if valid:
   if CAT[s][2]=='%':v=max(-1,v+rng.gauss(0,.018))
   else:v=max(.01,v*(1+rng.gauss(.00015 if freq=='daily' else .003,.009 if freq=='daily' else .014)))
   out.append((d,v))
  d+=step
 return out

def question_for(s,rows,slot,day):
 name,group,unit,kind,freq=CAT[s]
 if slot==1 and freq!='daily':return None
 if slot==1:
  endtarget=day-timedelta(days=1);months=None
 else:
  months={2:1,3:6,4:12,5:60}[slot];endtarget=day-timedelta(days=1)
 e=previous(rows,endtarget)
 if e is None:return None
 enddate,endval=rows[e]
 if (endtarget-enddate).days>({'daily':7,'weekly':15,'monthly':90,'quarterly':180}[freq]):return None
 # Return questions require previous session (Q1) or a horizon-matched starting point.
 isreturn=kind=='return' or (kind=='both' and (slot==1 or slot>=3))
 ischange=kind=='change'
 if slot==1 and kind not in ('return','both'):return None
 start=None;startval=None
 if isreturn or ischange:
  if slot==1:st=e-1
  else:
   target=shift(enddate,-months)
   st=previous(rows,target)
  if st is None or st>=e:return None
  start,startval=rows[st]
  if slot>1 and (target-start).days>({'daily':7,'weekly':15,'monthly':55,'quarterly':115}[freq]):return None
  if startval==0:return None
  answer=100*(endval/startval-1)
  typ='daily_return' if slot==1 else ('calculated_change' if ischange else 'period_return')
  ansunit='%'
 else:
  answer=endval;typ='rate_level' if unit=='%' else 'level';ansunit=unit
 # Important: no time-travel for revised macro data: current vintage is used, game frozen.
 if not math.isfinite(answer):return None
 if typ=='daily_return':tol=.25 if group in ('Equity indices','International indices','Individual stocks','International ETFs','Bond ETFs','Commodity ETFs') else 1.0
 elif typ in ('period_return','calculated_change'):
  tol={2:2,3:4,4:6,5:15}.get(slot,2)
  if group=='Inflation':tol={2:.3,3:.4,4:.7,5:2}.get(slot,.4)
  if group=='Macro':tol={2:1,3:2,4:3,5:6}.get(slot,2)
  if group=='Housing':tol={2:.5,3:2,4:4,5:12}.get(slot,2)
  if group=='FX':tol*=.65
  if group in ('Commodities','Commodity ETFs','Crypto'):tol*=1.7
 elif typ=='rate_level':tol=.5
 else:tol=max(abs(answer)*(.10 if group in ('Commodities','Crypto') else .07),.0001)
 if slot==1:question=f'What was the {name} return on {enddate.strftime("%b %-d, %Y")}?'
 elif typ in ('period_return','calculated_change'):
  phrase={2:'one month',3:'six months',4:'one year',5:'five years'}[slot]
  question=f'How much did {name} change over the {phrase} ending {enddate.strftime("%b %Y") if freq in ("monthly","quarterly") else enddate.strftime("%b %-d, %Y")}?'
 else:question=f'What was the {name} on {enddate.strftime("%b %Y") if freq in ("monthly","quarterly") else enddate.strftime("%b %-d, %Y")}?'
 if typ=='rate_level':question=f'What was the {name} on {enddate.strftime("%b %-d, %Y") if freq in ("daily","weekly") else enddate.strftime("%b %Y")}?'
 chartstart=start if start else enddate-timedelta(days=365 if slot==5 else 90)
 chart=[{'date':d.isoformat(),'value':round(v,6)} for d,v in rows if chartstart<=d<=enddate]
 if len(chart)>220:
  k=math.ceil(len(chart)/220);chart=chart[::k]+([chart[-1]] if chart[-1] not in chart[::k] else [])
 return {'slot':slot,'series':s,'name':name,'group':group,'question':question,'type':typ,'unit':ansunit,'answer':answer,'display':round(answer,2 if ansunit=='%' else (4 if group=='FX' else 2)),'precision':2 if ansunit=='%' else (4 if group=='FX' else 2),'tolerance':tol,'end':enddate.isoformat(),'start':start.isoformat() if start else None,'endValue':endval,'startValue':startval,'chart':chart,'source':None}

def generate(day,mode):
 storage_mode='v3-expanded-'+mode
 with LOCK:
  c=conn()
  try:
   saved=c.execute('SELECT payload FROM games WHERE day=? AND mode=?',(day.isoformat(),storage_mode)).fetchone()
   if saved:return json.loads(saved['payload'])
   pools={};cache={}
   for s in (CAT if mode=='real' else FRED):
    if mode=='real':rows=series_rows(c,s,day)
    else:rows=fixture_rows(s,day)
    if len(rows)<3:continue
    cache[s]=rows
   # cooldown based on past published real/demo games, never current game selections
   recent={}
   for row in c.execute('SELECT day,payload FROM games WHERE mode=? AND day<? AND day>=?',(storage_mode,day.isoformat(),(day-timedelta(days=7)).isoformat())):
    age=(day-date.fromisoformat(row['day'])).days
    for q in json.loads(row['payload'])['questions']:
     recent[q['series']]=min(age,recent.get(q['series'],999))
   for slot in range(1,6):
    pool=[]
    for s,rows in cache.items():
     q=question_for(s,rows,slot,day)
     if not q:continue
     group=q['group'];weight=WEIGHTS.get(group,8)/max(1,sum(1 for x in cache if CAT[x][1]==group))
     age=recent.get(s,999);weight*= .35 if age==1 else .6 if age<=3 else .8 if age<=7 else 1
     pool.append((q,weight))
    if not pool:raise ValueError(f'No eligible real-data questions for Q{slot}. Refresh FRED data or import historical CSVs.')
    pools[slot]=pool
   rng=random.Random(f'financia.le-v3:{mode}:{day.isoformat()}')
   questions=[]
   for slot in range(1,6):
    pool=pools[slot];q=rng.choices([x[0] for x in pool],weights=[x[1] for x in pool],k=1)[0]
    q['source']='SIMULATED DEMO' if mode=='demo' else ('Stooq daily Close (not guaranteed dividend-adjusted)' if q['series'] in STOOQ else 'Kraken UTC daily close' if q['series'] in CRYPTO else 'OECD via FRED (national index, local-market basis)' if q['series'] in INTERNATIONAL else 'FRED (source series: '+q['series']+')')
    questions.append(q)
   result={'date':day.isoformat(),'mode':mode,'questions':questions,'created':iso_now(),'version':3}
   c.execute('INSERT INTO games VALUES(?,?,?,?)',(day.isoformat(),storage_mode,json.dumps(result,allow_nan=False),iso_now()));c.commit()
   return result
  finally:c.close()

def status():
 c=conn()
 try:
  rows=c.execute('SELECT series,COUNT(*) n,MIN(day) first,MAX(day) last FROM observations GROUP BY series').fetchall()
  return {'series':[dict(r) for r in rows],'seriesCount':len(rows),'internationalCount':sum(1 for r in rows if r['series'] in INTERNATIONAL),'fredKey':bool(os.getenv('FRED_API_KEY')),'stooqKey':bool(os.getenv('STOOQ_API_KEY')),'stockCount':sum(1 for r in rows if r['series'].startswith('STOCK_')),'etfCount':sum(1 for r in rows if r['series'].startswith('ETF_')),'cryptoCount':sum(1 for r in rows if r['series'].startswith('KRAKEN_')),'today':game_day().isoformat()}
 finally:c.close()

class Handler(BaseHTTPRequestHandler):
 def log_message(self,fmt,*args): logging.info(fmt,*args)
 def authenticated(self):
  raw=self.headers.get('Authorization','')
  if not raw.startswith('Basic '):return False
  try:
   decoded=base64.b64decode(raw[6:],validate=True).decode('utf-8')
   user,sep,password=decoded.partition(':')
   return bool(sep) and hmac.compare_digest(user,AUTH_USER) and hmac.compare_digest(password,AUTH_PASS)
  except (ValueError,UnicodeDecodeError):return False
 def require_auth(self):
  if self.authenticated():return True
  self.send_response(401)
  self.send_header('WWW-Authenticate','Basic realm="financia.le private", charset="UTF-8"')
  self.send_header('Cache-Control','no-store')
  self.send_header('Content-Length','0')
  self.end_headers()
  return False
 def respond(self,obj,status=200):
  data=json.dumps(obj,allow_nan=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
 def do_GET(self):
  p=urllib.parse.urlsplit(self.path)
  if p.path=='/health':return self.respond({'ok':True})
  if not self.require_auth():return
  if p.path=='/api/status':return self.respond(status())
  if p.path=='/api/game':
   qs=urllib.parse.parse_qs(p.query);mode=qs.get('mode',['real'])[0]
   if mode not in ('real','demo'):return self.respond({'error':'Invalid mode'},400)
   try:return self.respond(generate(game_day(),mode))
   except Exception as e:return self.respond({'error':str(e)},503)
  if p.path in ('/','/index.html'):
   raw=(ROOT/'index.html').read_bytes();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.end_headers();return self.wfile.write(raw)
  return self.respond({'error':'Not found'},404)
 def do_POST(self):
  if not self.require_auth():return
  if self.path!='/api/admin/refresh':return self.respond({'error':'Not found'},404)
  if not os.getenv('FRED_API_KEY') and not os.getenv('STOOQ_API_KEY'):return self.respond({'error':'Set FRED_API_KEY or STOOQ_API_KEY in the server environment'},503)
  if not REFRESH_LOCK.acquire(blocking=False):return self.respond({'error':'Refresh already running'},409)
  threading.Thread(target=refresh_worker,daemon=True).start()
  return self.respond({'ok':True,'message':'Data refresh started in background'})

REFRESH_LOCK=threading.Lock()
def refresh_worker():
 try:
  result=(fetch_all() if os.getenv('FRED_API_KEY') else [])+fetch_extra()
  logging.info('Market-data refresh: %s/%s succeeded',sum(x['ok'] for x in result),len(result))
  for x in result:
   if not x['ok']:logging.warning('Data series %s: %s',x['series'],x['error'])
 finally:REFRESH_LOCK.release()
def periodic_refresh():
 # Also refresh on startup; generate() freezes each game only once.
 while True:
  if REFRESH_LOCK.acquire(blocking=False):
   refresh_worker()
  time.sleep(24*60*60)

def main():
 if len(sys.argv)>1 and sys.argv[1]=='refresh':
  out=(fetch_all() if os.getenv('FRED_API_KEY') else [])+fetch_extra()
  for r in out:print(('OK ' if r['ok'] else 'ERR ')+r['series']+': '+str(r.get('count',r.get('error'))))
  print(f"{sum(x['ok'] for x in out)}/{len(out)} series refreshed")
  return
 if len(sys.argv)>3 and sys.argv[1]=='import':
  s=sys.argv[2].upper();p=Path(sys.argv[3]);
  if s not in MSCI:raise SystemExit('Valid MSCI IDs: '+', '.join(MSCI))
  print('Imported',store(s,parse_csv(p.read_bytes(),s),'MSCI CSV (user-supplied)'),'rows for',s);return
 if len(sys.argv)>1 and sys.argv[1]=='test':
  for i in range(30):
   d=date(2026,9,1)+timedelta(days=i);g=generate(d,'demo')
   assert len(g['questions'])==5
   for q in g['questions']:
    assert math.isfinite(q['answer']) and q['tolerance']>0
    assert q['end']<d.isoformat()
    assert q['slot'] in range(1,6)
    if q['start']:assert q['start']<q['end']
    if q['type'] in ('period_return','calculated_change'):
     assert q['end']==max(x[0] for x in fixture_rows(q['series'],d) if x[0]<d).isoformat()
  print('PASS: 30 frozen demo games, 150 valid questions');return
 port=int(os.getenv('PORT','8765'));server=ThreadingHTTPServer((os.getenv('HOST','0.0.0.0'),port),Handler)
 threading.Thread(target=periodic_refresh,daemon=True).start()
 print(f'financia.le listening on port {port} (HTTP Basic Auth enabled)')
 print('Press Ctrl+C to stop. Choose DEMO to play immediately; REAL DATA needs a refresh.')
 try:server.serve_forever()
 except KeyboardInterrupt:print('\nStopped.')
 finally:server.server_close()
if __name__=='__main__':main()
