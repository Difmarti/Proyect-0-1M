import psycopg2
from psycopg2.extras import RealDictCursor
import json

conn=psycopg2.connect(host='10.30.90.102',port=5432,database='trading_db',user='trading_user',password='Secure7319')
cur=conn.cursor(cursor_factory=RealDictCursor)
cur.execute("SELECT * FROM trading_signals WHERE time >= NOW() - INTERVAL '24 hours' ORDER BY time DESC LIMIT 20")
print(json.dumps([dict(r) for r in cur.fetchall()], default=str, indent=2))
