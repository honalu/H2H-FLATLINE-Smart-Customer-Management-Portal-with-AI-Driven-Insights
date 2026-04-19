import sqlite3
from openai import OpenAI
client = OpenAI()

def get_sql_from_llm(user_query):
    
    print("Calling OpenAI...")

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=f"""
            Convert this natural language query into SQL.
            Table: customers
            Columns: company_name, region, plan_tier, contract_start, contract_end, devices, tickets, nps, monthly_usage

            Query: {user_query}
            """
        )

        return response.output[0].content[0].text.strip()

    except Exception as e:
        print("ERROR:", e)
        return "SELECT * FROM customers LIMIT 5"


def run_query(nl_query):
    query = nl_query.lower()

    # 🔥 Smart fallback (AI-like behavior)
    if "highest nps" in query or "top nps" in query:
        sql = "SELECT * FROM customers ORDER BY nps DESC LIMIT 5"

    elif "lowest nps" in query or "low nps" in query:
        sql = "SELECT * FROM customers ORDER BY nps ASC LIMIT 5"

    elif "enterprise" in query:
        sql = "SELECT * FROM customers WHERE plan_tier='Enterprise'"

    elif "pro plan" in query:
        sql = "SELECT * FROM customers WHERE plan_tier='Pro'"

    elif "basic plan" in query:
        sql = "SELECT * FROM customers WHERE plan_tier='Basic'"

    elif "high usage" in query:
        sql = "SELECT * FROM customers ORDER BY monthly_usage DESC LIMIT 5"

    elif "low usage" in query:
        sql = "SELECT * FROM customers ORDER BY monthly_usage ASC LIMIT 5"

    elif "tickets more than" in query:
        try:
            num = int(query.split()[-1])
            sql = f"SELECT * FROM customers WHERE tickets > {num}"
        except:
            sql = "SELECT * FROM customers LIMIT 5"

    elif "apac" in query:
        sql = "SELECT * FROM customers WHERE region='APAC'"

    elif "emea" in query:
        sql = "SELECT * FROM customers WHERE region='EMEA'"

    elif "amer" in query:
        sql = "SELECT * FROM customers WHERE region='AMER'"

    else:
        sql = "SELECT * FROM customers LIMIT 5"

    print("\n🧠 Generated SQL:", sql)

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    result = cursor.execute(sql).fetchall()
    conn.close()

    return result


if __name__ == "__main__":
    while True:
        q = input("Ask: ")
        print(run_query(q))


