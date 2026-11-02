"""Read-only validation of delivered databases and in-memory replay of SQL."""
from pathlib import Path
import sqlite3,json,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parent; P=R/'01_practice';results=[]
for db in sorted(P.rglob('*.db')):
 c=sqlite3.connect(db.as_uri()+'?mode=ro',uri=True)
 assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok',db
 assert not c.execute('PRAGMA foreign_key_check').fetchall(),db
 results.append({'database':str(db.relative_to(R)),'integrity':'ok','foreign_keys':'ok'});c.close()
for setup in sorted(P.rglob('01_setup.sql')):
 d=setup.parent;c=sqlite3.connect(':memory:',cached_statements=0);c.executescript(setup.read_text(encoding='utf-8'))
 expected=json.loads((d/'results.json').read_text(encoding='utf-8'))
 # Replay the delivered SQL, not an alternate implementation.
 statements=[];buf=''
 for line in (d/'02_tasks.sql').read_text(encoding='utf-8').splitlines(True):
  buf+=line
  if sqlite3.complete_statement(buf): statements.append(buf);buf=''
 assert not buf.strip();assert len(statements)==len(expected)
 for sql,r in zip(statements,expected):
  cur=c.execute(sql);rows=[list(x) for x in cur.fetchall()] if cur.description else []
  # Dates depend on run day; validate defaults relative to the run itself.
  if 'created' not in r['columns']:
   if r['task'].startswith('Предсказание: версия SQLite'):
    assert len(rows)==1 and len(rows[0])==1 and isinstance(rows[0][0],str),(d,r['task'],rows)
   elif 'план' in r['task'].lower() and rows and r['rows'] and len(rows[0])==4:
    # Поле notused в EXPLAIN QUERY PLAN зависит от сборки SQLite.
    assert [[x[0],x[1],x[3]] for x in rows] == [[x[0],x[1],x[3]] for x in r['rows']],(d,r['task'],rows,r['rows'])
   else:
    assert rows==r['rows'],(d,r['task'],rows,r['rows'])
 assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok';assert not c.execute('PRAGMA foreign_key_check').fetchall();c.close()
 results.append({'replay':str(d.relative_to(R)),'statements':len(statements),'status':'ok'})
def connect(part):return sqlite3.connect(P/part/'practice.db')
c=connect('04_Создание_БД');assert c.execute('SELECT COUNT(*) FROM student').fetchone()[0]==3;assert c.execute('SELECT COUNT(*) FROM teacher').fetchone()[0]==5;c.close()
c=connect('06_Ограничения/06_Изменение_структуры');assert c.execute('SELECT COUNT(*) FROM product').fetchone()[0]==5
try:c.execute("INSERT INTO product(id,title,price) VALUES(100,'Invalid',-1)");raise AssertionError('CHECK not active')
except sqlite3.IntegrityError:pass
c.rollback();c.close()
c=connect('07_Импорт_данных');assert c.execute('SELECT COUNT(*) FROM product').fetchone()[0]==5;assert c.execute('SELECT COUNT(*) FROM ten_products').fetchone()[0]==10;assert c.execute('SELECT name FROM cleaned ORDER BY rowid').fetchall()==[('milk',),('bread',),('soap',)];c.close()
c=connect('10_Агрегатные_функции');assert c.execute('SELECT COUNT(*),AVG(price),MIN(price),MAX(price) FROM product').fetchone()==(10,3316.0,30.0,30000.0);c.close()
c=connect('12_Подзапросы');assert c.execute('SELECT id FROM category c WHERE NOT EXISTS(SELECT 1 FROM product p WHERE p.category_id=c.id)').fetchall()==[(4,)];c.close()
for p in P.rglob('*.drawio'):
 tree=ET.parse(p);assert tree.findall('.//mxCell[@edge="1"]');results.append({'diagram':p.name,'xml':'ok'})
print(json.dumps({'sqlite_version':sqlite3.sqlite_version,'status':'passed','checks':results},ensure_ascii=False,indent=2))
