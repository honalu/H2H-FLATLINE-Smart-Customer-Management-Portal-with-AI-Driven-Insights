import sqlite3
import random
from faker import Faker

fake = Faker()

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Drop old table and add health_score column
cursor.execute('DROP TABLE IF EXISTS customers')
cursor.execute('''
CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    region TEXT,
    plan_tier TEXT,
    nps_score INTEGER,
    health_score INTEGER
)
''')

regions = ['North America', 'Europe', 'Asia Pacific', 'LATAM', 'MEA']
plans = ['Free', 'Pro', 'Enterprise']

for i in range(200):
    company = fake.company()
    region = random.choice(regions)
    plan = random.choice(plans)
    nps = random.randint(0, 10)
    
    # Weighted health score: NPS*6 + plan bonus
    plan_score = {'Enterprise': 20, 'Pro': 10, 'Free': 0}
    health = int((nps * 6) + plan_score[plan])
    
    cursor.execute('''
    INSERT INTO customers (company_name, region, plan_tier, nps_score, health_score)
    VALUES (?,?,?,?,?)
    ''', (company, region, plan, nps, health))

conn.commit()
conn.close()

print("✅ Generated 200 customers with health scores!")