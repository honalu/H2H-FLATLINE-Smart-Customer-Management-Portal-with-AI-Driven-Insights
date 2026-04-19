import sqlite3
import random
from faker import Faker

fake = Faker()

# Connect to your database
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Create customers table if it doesn't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    region TEXT,
    plan_tier TEXT,
    nps_score INTEGER
)
''')

# Clear old data so we start fresh
cursor.execute('DELETE FROM customers')

# Generate 200 fake customers
regions = ['North America', 'Europe', 'Asia Pacific', 'LATAM', 'MEA']
plans = ['Free', 'Pro', 'Enterprise']

for i in range(200):
    company = fake.company()
    region = random.choice(regions)
    plan = random.choice(plans)
    nps = random.randint(0, 10)
    
    cursor.execute('''
    INSERT INTO customers (company_name, region, plan_tier, nps_score)
    VALUES (?, ?, ?, ?)
    ''', (company, region, plan, nps))

conn.commit()
conn.close()

print("✅ Generated 200 customers successfully!")