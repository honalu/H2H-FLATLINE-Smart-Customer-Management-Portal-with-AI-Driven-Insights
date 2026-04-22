from flask import Flask, render_template, request, jsonify
import sqlite3
import random

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row # This makes customer['customer_name'] work
    return conn

@app.route('/')
def index():
    conn = get_db()
    customers = conn.execute("SELECT * FROM customers").fetchall()

    # Add status based on health_score for display
    customer_list = []
    total = healthy = at_risk = critical = 0

    for row in customers:
        customer = dict(row)
        total += 1
        if customer['health_score'] >= 70:
            customer['status'] = 'Healthy'
            healthy += 1
        elif customer['health_score'] >= 40:
            customer['status'] = 'At Risk'
            at_risk += 1
        else:
            customer['status'] = 'Critical'
            critical += 1
        customer_list.append(customer)

    conn.close()
    return render_template('index.html', 
                           customers=customer_list,
                           total=total,
                           healthy=healthy,
                           at_risk=at_risk,
                           critical=critical)

@app.route('/search')
def search():
    query = request.args.get('q', '').lower()
    conn = get_db()

    # Basic NLQ: parse "critical customers in MEA"
    sql = "SELECT * FROM customers WHERE 1=1"
    params = []

    if 'critical' in query:
        sql += " AND health_score < 40"
    elif 'at risk' in query:
        sql += " AND health_score >= 40 AND health_score < 70"
    elif 'healthy' in query:
        sql += " AND health_score >= 70"

    if 'mea' in query:
        sql += " AND region =?"
        params.append('MEA')
    elif 'latam' in query:
        sql += " AND region =?"
        params.append('LATAM')
    elif 'north america' in query:
        sql += " AND region =?"
        params.append('North America')
    elif 'asia' in query:
        sql += " AND region =?"
        params.append('Asia Pacific')
    elif 'europe' in query:
        sql += " AND region =?"
        params.append('Europe')

    if 'nps below' in query:
        try:
            nps_val = int(query.split('nps below')[1].strip().split()[0])
            sql += " AND nps_score <?"
            params.append(nps_val)
        except:
            pass

    customers = conn.execute(sql, params).fetchall()
    customer_list = [dict(row) for row in customers]
    conn.close()
    return jsonify(customer_list)

@app.route('/filter/<status>')
def filter_status(status):
    conn = get_db()
    if status == 'Critical':
        customers = conn.execute("SELECT * FROM customers WHERE health_score < 40").fetchall()
    elif status == 'At Risk':
        customers = conn.execute("SELECT * FROM customers WHERE health_score >= 40 AND health_score < 70").fetchall()
    elif status == 'Healthy':
        customers = conn.execute("SELECT * FROM customers WHERE health_score >= 70").fetchall()
    else: # All
        customers = conn.execute("SELECT * FROM customers").fetchall()

    customer_list = [dict(row) for row in customers]
    conn.close()
    return jsonify(customer_list)

@app.route('/predict/<int:customer_id>')
def predict(customer_id):
    conn = get_db()
    customer = conn.execute("SELECT * FROM customers WHERE id =?", (customer_id,)).fetchone()
    conn.close()

    if not customer:
        return jsonify({"error": "Customer not found"})

    # Simple churn logic: lower health + lower nps = higher risk
    churn_risk = 100 - customer['health_score'] + (10 - customer['nps_score']) * 2
    churn_risk = max(0, min(100, churn_risk)) # Clamp 0-100

    return jsonify({
        "customer_name": customer['customer_name'],
        "company_name": customer['company_name'],
        "churn_risk": f"{churn_risk}%"
    })

@app.route('/email/<int:customer_id>')
def email(customer_id):
    conn = get_db()
    customer = conn.execute("SELECT * FROM customers WHERE id =?", (customer_id,)).fetchone()
    conn.close()

    if not customer:
        return jsonify({"error": "Customer not found"})

    # Determine status
    if customer['health_score'] >= 70:
        status = 'Healthy'
    elif customer['health_score'] >= 40:
        status = 'At Risk'
    else:
        status = 'Critical'

    email_draft = f"""Subject: Customer Health Update - {customer['company_name']}

Hi Team,

Customer: {customer['customer_name']}
Company: {customer['company_name']}
Region: {customer['region']}
Plan: {customer['plan_tier']}
Health Score: {customer['health_score']}/100 - {status}
NPS: {customer['nps_score']}/10

Recommended Action: {'Schedule check-in call' if status!= 'Healthy' else 'Maintain engagement'}

Best,
Customer Success Team"""

    return jsonify({"email": email_draft})

if __name__ == '__main__':
    app.run(debug=True)