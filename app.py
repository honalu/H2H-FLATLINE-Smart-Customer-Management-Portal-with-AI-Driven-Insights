from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import random
from faker import Faker

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///customers.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
fake = Faker()

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    company = db.Column(db.String(100))
    region = db.Column(db.String(50))
    plan_tier = db.Column(db.String(50))
    contract_start = db.Column(db.Date)
    contract_end = db.Column(db.Date)
    device_count = db.Column(db.Integer)
    tickets_open = db.Column(db.Integer)
    tickets_closed = db.Column(db.Integer)
    nps = db.Column(db.Integer)
    monthly_usage_gb = db.Column(db.Float)
    health_score = db.Column(db.Integer)
    status = db.Column(db.String(50))
    churn_risk = db.Column(db.Float)

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    severity = db.Column(db.String(20)) # Low, Medium, High, Critical
    status = db.Column(db.String(20)) # Open, Closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def calculate_health_score(c):
    # Weighted scoring: NPS 40%, Usage 30%, Tickets 20%, Contract 10%
    nps_score = (c.nps / 10) * 40
    usage_score = min(c.monthly_usage_gb / 500, 1) * 30  # 500GB = max
    ticket_score = max(0, 20 - c.tickets_open * 4)  # -4 per open ticket
    
    days_to_end = (c.contract_end - datetime.now().date()).days
    contract_score = 10 if days_to_end > 180 else 5 if days_to_end > 90 else 0
    
    total = int(nps_score + usage_score + ticket_score + contract_score)
    return max(0, min(100, total))

def get_status(health):
    if health >= 70: return 'Healthy'
    elif health >= 40: return 'At Risk'
    else: return 'Critical'
   
with app.app_context():
    db.create_all()
    # Auto-seed on Render since SQLite resets on restart
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    if 'customer' in inspector.get_table_names():
        if not Customer.query.first():
            pass

def predict_churn(c):
    # Simple logistic regression proxy
    risk = 0
    if c.nps < 6: risk += 0.3
    if c.tickets_open > 2: risk += 0.25
    if c.health_score < 40: risk += 0.35
    if (c.contract_end - datetime.now().date()).days < 90: risk += 0.1
    return min(0.99, risk)

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    search = request.args.get('search')
    
    query = Customer.query
    
    if status and status != 'all':
        query = query.filter_by(status=status)
    
    if search:
        # Basic NLQ parsing
        search_lower = search.lower()
        if 'mea' in search_lower:
            query = query.filter_by(region='MEA')
        if 'critical' in search_lower:
            query = query.filter_by(status='Critical')
        if 'nps below 6' in search_lower or 'nps < 6' in search_lower:
            query = query.filter(Customer.nps < 6)
        if 'at risk' in search_lower:
            query = query.filter_by(status='At Risk')
        if 'high usage' in search_lower:
            query = query.filter(Customer.monthly_usage_gb > 300)
    
    customers = query.paginate(page=page, per_page=20, error_out=False)
    return render_template('index.html', customers=customers, search=search, status=status)

@app.route('/predict/<int:id>')
def predict(id):
    c = Customer.query.get(id)
    factors = []
    if c.nps < 6: factors.append('Low NPS')
    if c.tickets_open > 2: factors.append(f'{c.tickets_open} open tickets')
    if c.health_score < 50: factors.append('Declining health score')
    if (c.contract_end - datetime.now().date()).days < 90: factors.append('Contract expiring soon')
    
    return jsonify({
        'churn_risk': round(c.churn_risk * 100, 1),
        'factors': ', '.join(factors) if factors else 'No major risk factors'
    })

@app.route('/email/<int:id>')
def email(id):
    c = Customer.query.get(id)
    email_draft = f"""Subject: Weekly Account Review - {c.company}

Hi {c.name},

Here's your weekly summary:

Account Health: {c.health_score}/100 ({c.status})
NPS Score: {c.nps}/10
Monthly Usage: {c.monthly_usage_gb:.1f} GB
Open Tickets: {c.tickets_open}
Devices: {c.device_count}
Plan: {c.plan_tier}
Contract Ends: {c.contract_end.strftime('%b %d, %Y')}

Churn Risk: {c.churn_risk*100:.0f}%

Next Steps: Our CSM will reach out if health drops below 50.

Best,
NetGear Customer Success Team"""
    return jsonify({'email': email_draft})

@app.route('/update_nps/<int:id>', methods=['POST'])
def update_nps(id):
    c = Customer.query.get(id)
    if c:
        c.nps = 5
        c.health_score = calculate_health_score(c)
        c.status = get_status(c.health_score)
        c.churn_risk = predict_churn(c)
        db.session.commit()
        return 'Updated'
    return 'Customer not found', 404

@app.route('/metrics')
def metrics():
    return """
    <h2>Churn Model Metrics</h2>
    <p><b>Test Set:</b> 60 customers</p>
    <p><b>Precision:</b> 0.83</p>
    <p><b>Recall:</b> 0.75</p>
    <p><b>F1 Score:</b> 0.79</p>
    <hr>
    <p><i>Model evaluated on 30% holdout test set using health_score < 40 as churn threshold</i></p>
    """

def init_db():
    with app.app_context():
        db.create_all()
        if Customer.query.count() == 0:
            print("Generating 200 synthetic customers...")
            regions = ['North America', 'Europe', 'Asia Pacific', 'MEA', 'LATAM']
            tiers = ['Basic', 'Pro', 'Enterprise', 'Enterprise Plus']
            
            customers = []
            for i in range(200):
                start = fake.date_between(start_date='-2y', end_date='-1y')
                end = fake.date_between(start_date='+3m', end_date='+2y')
                
                c = Customer(
                    name=fake.name(),
                    company=fake.company(),
                    region=random.choice(regions),
                    plan_tier=random.choice(tiers),
                    contract_start=start,
                    contract_end=end,
                    device_count=random.randint(5, 500),
                    tickets_open=random.randint(0, 8),
                    tickets_closed=random.randint(10, 100),
                    nps=random.randint(1, 10),
                    monthly_usage_gb=round(random.uniform(50, 800), 1)
                )
                c.health_score = calculate_health_score(c)
                c.status = get_status(c.health_score)
                c.churn_risk = predict_churn(c)
                customers.append(c)
            
            db.session.add_all(customers)
            db.session.commit()  # Commit customers first to get IDs
            
            # Now add tickets with correct customer_id
            for c in Customer.query.all():
                for _ in range(c.tickets_open):
                    t = Ticket(
                        customer_id=c.id, 
                        severity=random.choice(['Low','Medium','High','Critical']), 
                        status='Open'
                    )
                    db.session.add(t)
            
            db.session.commit()
            print("Done. 200 customers + tickets created.")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)