import sqlite3
conn = sqlite3.connect('database.db')
c = conn.cursor()
try:
    c.execute('ALTER TABLE requests ADD COLUMN ip TEXT;')
except:
    pass
try:
    c.execute('ALTER TABLE requests ADD COLUMN purpose TEXT;')
except:
    pass
try:
    c.execute('ALTER TABLE requests ADD COLUMN status TEXT;')
except:
    pass
try:
    c.execute('ALTER TABLE requests ADD COLUMN position INTEGER;')
except:
    pass
conn.commit()
conn.close()