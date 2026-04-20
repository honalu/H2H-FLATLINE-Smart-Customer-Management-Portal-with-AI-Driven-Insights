import datetime

def calculate_health_score(customer):
    """Requirement #4: AI health score"""
    score = 100
    
    # Use .get() with defaults in case column names differ
    nps = customer.get('nps_score', customer.get('nps', 10))
    if nps <= 6:
        score -= 40
    elif nps <= 8:
        score -= 20
    
    days_to_expiry = customer.get('contract_days_remaining', customer.get('days_to_renewal', 365))
    if days_to_expiry < 30:
        score -= 30
    elif days_to_expiry < 90:
        score -= 15
    
    critical_tickets = customer.get('open_critical_tickets', customer.get('critical_tickets', 0))
    score -= (critical_tickets * 10)
    
    usage_trend = customer.get('usage_trend_pct', customer.get('usage_change', 0))
    if usage_trend < -20:
        score -= 20
    elif usage_trend < 0:
        score -= 10
    
    return max(0, min(100, score))

def predict_churn(customer):
    """Requirement #5: Churn prediction + explanations"""
    health_score = customer.get('health_score', calculate_health_score(customer))
    
    if health_score < 40:
        churn_prob = 85 + (40 - health_score) // 4
        risk_level = "Likely to Churn"
    elif health_score < 70:
        churn_prob = 40 + (70 - health_score)
        risk_level = "At Risk"
    else:
        churn_prob = max(5, 30 - health_score // 3)
        risk_level = "Healthy"
    
    factors = []
    nps = customer.get('nps_score', customer.get('nps', 10))
    if nps <= 6:
        factors.append(f"NPS Score: {nps} (Detractor)")
    
    days = customer.get('contract_days_remaining', customer.get('days_to_renewal', 365))
    if days < 30:
        factors.append(f"Contract Expires: {days} days")
    
    tickets = customer.get('open_critical_tickets', customer.get('critical_tickets', 0))
    if tickets > 0:
        factors.append(f"Open Critical Tickets: {tickets}")
    
    usage = customer.get('usage_trend_pct', customer.get('usage_change', 0))
    if usage < -20:
        factors.append(f"Usage Trend: Down {abs(usage)}% MoM")
    
    return {
        'churn_probability': min(99, churn_prob),
        'risk_level': risk_level,
        'factors': factors if factors else ['Account appears stable']
    }

def generate_email_text(customer):
    """Requirement #6: Email summary agent"""
    today = datetime.date.today()
    end_date = today + datetime.timedelta(days=7)
    
    # Handle different possible column names for company
    company = customer.get('company', customer.get('company_name', customer.get('name', 'Customer')))
    
    prediction = predict_churn(customer)
    health_score = customer.get('health_score', 0)
    
    if health_score < 40:
        status = "Critical"
    elif health_score < 70:
        status = "At Risk"
    else:
        status = "Healthy"
    
    # Get all metrics with fallbacks
    nps = customer.get('nps_score', customer.get('nps', 'N/A'))
    days = customer.get('contract_days_remaining', customer.get('days_to_renewal', 'N/A'))
    tickets = customer.get('open_critical_tickets', customer.get('critical_tickets', 0))
    usage = customer.get('usage_trend_pct', customer.get('usage_change', 0))
    region = customer.get('region', customer.get('geo', 'N/A'))
    
    email = f"""Subject: Weekly Account Health Review - {company} ({today.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')})

Hi {company} Team,

Here's your weekly account summary:

Account Status: {status}
Health Score: {health_score}/100
Churn Risk: {prediction['churn_probability']}% - {prediction['risk_level']}

Key Metrics:
- NPS Score: {nps}
- Contract Expires: {days} days
- Open Critical Tickets: {tickets}
- Usage Trend: {usage}% MoM
- Region: {region}

Key Risk Factors:
"""
    
    for i, factor in enumerate(prediction['factors'], 1):
        email += f"{i}. {factor}\n"
    
    email += f"""
Recommended Actions:
1. Schedule executive business review this week
2. Address all open critical support tickets
3. Discuss renewal terms and incentives

Contact your Customer Success Manager: sarah@netgear-portal.com

---
NetGear Smart Portal | AI-Driven Insights
This email was auto-generated on {today.strftime('%B %d, %Y')}
"""
    
    return email