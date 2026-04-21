from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('customers.db')
    conn.row_factory = sqlite3.Row
    return conn

# Requirement #3 + #4: Homepage Dashboard with NLQ + Health Scores
@app.route('/')
def index():
    conn = get_db_connection()
    customers = conn.execute('SELECT * FROM customers').fetchall()
    conn.close()

    # Requirement #4: Calculate health breakdown for dashboard cards
    total = len(customers)
    healthy = sum(1 for c in customers if c['health_score'] >= 70)
    at_risk = sum(1 for c in customers if 40 <= c['health_score'] < 70)
    critical = sum(1 for c in customers if c['health_score'] < 40)

    return render_template('index.html',
                           customers=customers,
                           total=total,
                           healthy=healthy,
                           at_risk=at_risk,
                           critical=critical)

# Requirement #2: Web portal with filters + Requirement #3: NLQ
@app.route('/customers')
def customers():
    conn = get_db_connection()
    query = request.args.get('query', '').lower()
    health_filter = request.args.get('health', '')
    
    sql = 'SELECT * FROM customers WHERE 1=1'
    params = []
    
    # Requirement #2: Health filter buttons
    if health_filter:
        if health_filter == 'critical':
            sql += ' AND health_score < 40'
        elif health_filter == 'at_risk':
            sql += ' AND health_score >= 40 AND health_score < 70'
        elif health_filter == 'healthy':
            sql += ' AND health_score >= 70'
    
    # Requirement #3: Simple Natural Language Query parsing
    if query:
        if 'critical' in query:
            sql += ' AND health_score < 40'
        if 'at risk' in query or 'at_risk' in query:
            sql += ' AND health_score >= 40 AND health_score < 70'
        if 'healthy' in query:
            sql += ' AND health_score >= 70'
        if 'mea' in query:
            sql += " AND region = 'MEA'"
        if 'amer' in query:
            sql += " AND region = 'AMER'"
        if 'emea' in query:
            sql += " AND region = 'EMEA'"
        if 'apac' in query:
            sql += " AND region = 'APAC'"
        if 'latam' in query:
            sql += " AND region = 'LATAM'"
        if 'north america' in query:
            sql += " AND region = 'North America'"
        if 'asia pacific' in query:
            sql += " AND region = 'Asia Pacific'"
        if 'nps below 6' in query or 'nps < 6' in query:
            sql += " AND nps_score < 6"
        if 'nps below 7' in query or 'nps < 7' in query:
            sql += " AND nps_score < 7"
    
    customers = conn.execute(sql, params).fetchall()
    
    # Recalculate cards for filtered view
    total = len(customers)
    healthy = sum(1 for c in customers if c['health_score'] >= 70)
    at_risk = sum(1 for c in customers if 40 <= c['health_score'] < 70)
    critical = sum(1 for c in customers if c['health_score'] < 40)
    conn.close()
    
    return render_template('index.html',
                           customers=customers,
                           total=total,
                           healthy=healthy,
                           at_risk=at_risk,
                           critical=critical)

# Requirement #5: Churn Prediction API
@app.route('/predict/<int:customer_id>')
def predict_churn(customer_id):
    conn = get_db_connection()
    customer = conn.execute('SELECT * FROM customers WHERE id = ?', (customer_id,)).fetchone()
    conn.close()
    
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    
    # Simple rule-based churn risk
    score = customer['health_score']
    nps = customer['nps_score'] or 0
    
    if score < 40 or nps < 4:
        risk = "High"
        reason = "Low health score and/or NPS indicates churn risk"
    elif score < 70 or nps < 7:
        risk = "Medium"
        reason = "Moderate health/NPS — monitor closely"
    else:
        risk = "Low"
        reason = "Healthy account with good engagement"
    
    return jsonify({
        "customer_id": customer_id,
        "company": customer['company_name'],
        "health_score": score,
        "nps": nps,
        "churn_risk": risk,
        "reason": reason
    })

# Requirement #6: Email Summary Agent
@app.route('/email/<int:customer_id>')
def generate_email(customer_id):
    conn = get_db_connection()
    customer = conn.execute('SELECT * FROM customers WHERE id = ?', (customer_id,)).fetchone()
    conn.close()
    
    if not customer:
        return "Customer not found", 404
    
    company = customer['company_name']
    health = customer['health_score']
    nps = customer['nps_score'] or 0
    status = 'Critical' if health < 40 else 'At Risk' if health < 70 else 'Healthy'
    
    email = f"""Subject: Weekly Account Review - {company}

Hi Team,

Here's the weekly summary for {company}:

**Account Health:** {status}
- Health Score: {health}/100
- NPS Score: {nps}/10
- Region: {customer['region']}

**Key Observations:**
"""
    if health < 40:
        email += "- Account is in critical state. Immediate outreach recommended.\n- Review open tickets and contract renewal date.\n"
    elif health < 70:
        email += "- Account shows at-risk signals. Proactive engagement needed.\n- Check recent support interactions and usage trends.\n"
    else:
        email += "- Account is healthy. Continue regular check-ins.\n- Potential upsell opportunity.\n"
    
    email += f"\n**Next Steps:**\n- CSM to schedule review call\n- Share QBR deck with stakeholders\n\nBest,\nNetGear Smart Portal"
    
    return email, 200, {'Content-Type': 'text/plain; charset=utf-8'}

if __name__ == '__main__':
    app.run(debug=True)