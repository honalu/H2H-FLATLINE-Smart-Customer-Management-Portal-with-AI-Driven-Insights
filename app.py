from flask import Flask, render_template, request, jsonify
import sqlite3
import os
from churn_model import calculate_health_score, predict_churn, generate_email_text

app = Flask(__name__)

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'customers.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    customers = conn.execute('SELECT * FROM customers').fetchall()
    conn.close()
    
    # Calculate health breakdown for dashboard
    healthy = sum(1 for c in customers if c['health_score'] >= 70)
    at_risk = sum(1 for c in customers if 40 <= c['health_score'] < 70)
    critical = sum(1 for c in customers if c['health_score'] < 40)
    total = len(customers)
    
    return render_template('index.html', 
                         total=total, 
                         healthy=healthy, 
                         at_risk=at_risk, 
                         critical=critical)

@app.route('/customers')
def customers():
    health_filter = request.args.get('health')
    conn = get_db_connection()
    
    if health_filter == 'critical':
        customers = conn.execute('SELECT * FROM customers WHERE health_score < 40 ORDER BY health_score ASC').fetchall()
    elif health_filter == 'at_risk':
        customers = conn.execute('SELECT * FROM customers WHERE health_score >= 40 AND health_score < 70 ORDER BY health_score ASC').fetchall()
    elif health_filter == 'healthy':
        customers = conn.execute('SELECT * FROM customers WHERE health_score >= 70 ORDER BY health_score DESC').fetchall()
    else:
        customers = conn.execute('SELECT * FROM customers ORDER BY id').fetchall()
    
    conn.close()
    return render_template('customers.html', customers=customers, health_filter=health_filter)

@app.route('/predict/<int:customer_id>')
def predict(customer_id):
    conn = get_db_connection()
    customer = conn.execute('SELECT * FROM customers WHERE id = ?', (customer_id,)).fetchone()
    conn.close()
    
    if customer is None:
        return jsonify({'error': 'Customer not found'}), 404
    
    # Run prediction using churn_model.py
    prediction = predict_churn(dict(customer))
    
    return jsonify({
        'customer_id': customer_id,
        'company': customer['company'],
        'churn_probability': prediction['churn_probability'],
        'risk_level': prediction['risk_level'],
        'factors': prediction['factors']
    })

@app.route('/email/<int:customer_id>')
def generate_email(customer_id):
    """
    Requirement #6: Email summary agent
    Returns plain text weekly account review email
    """
    conn = get_db_connection()
    customer = conn.execute('SELECT * FROM customers WHERE id = ?', (customer_id,)).fetchone()
    conn.close()
    
    if customer is None:
        return "Customer not found", 404
    
    # Generate email using churn_model.py
    email_content = generate_email_text(dict(customer))
    
    # Return as plain text, not HTML template
    return email_content, 200, {'Content-Type': 'text/plain; charset=utf-8'}

if __name__ == '__main__':
    app.run(debug=True)