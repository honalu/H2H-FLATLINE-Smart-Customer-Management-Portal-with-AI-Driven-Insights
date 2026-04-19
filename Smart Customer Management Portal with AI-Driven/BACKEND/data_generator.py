import pandas as pd
from faker import Faker
import random
import sqlite3
from datetime import datetime, timedelta

fake = Faker()

def generate_data(n=250):
    data = []

    for _ in range(n):
        contract_start = fake.date_between(start_date='-2y', end_date='today')
        contract_end = contract_start + timedelta(days=random.randint(180, 720))

        data.append({
            "company_name": fake.company(),
            "region": random.choice(["APAC", "EMEA", "AMER"]),
            "plan_tier": random.choice(["Basic", "Pro", "Enterprise"]),
            "contract_start": contract_start,
            "contract_end": contract_end,
            "devices": random.randint(10, 500),
            "tickets": random.randint(0, 50),
            "nps": random.randint(-100, 100),
            "monthly_usage": random.randint(100, 10000)
        })

    df = pd.DataFrame(data)

    conn = sqlite3.connect("database.db")
    df.to_sql("customers", conn, if_exists="replace", index=False)
    conn.close()

    print("✅ Data generated and stored in database.db")

if __name__ == "__main__":
    generate_data()