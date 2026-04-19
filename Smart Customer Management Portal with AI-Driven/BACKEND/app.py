from flask import Flask, request, jsonify
import sqlite3
from nl_query import run_query
from churn_model import train_model

app = Flask(__name__)

# Train model once
model = train_model()

@app.route("/")
def home():
    return "✅ Smart Customer Backend Running"

# Get customers
@app.route("/customers")
def get_customers():
    conn = sqlite3.connect("database.db")
    data = conn.execute("SELECT * FROM customers LIMIT 20").fetchall()
    conn.close()
    return jsonify(data)

# Natural language query
@app.route("/query", methods=["POST"])
def query():
    user_query = request.json.get("query")
    result = run_query(user_query)

    columns = ["company", "region", "plan", "start", "end", "devices", "tickets", "nps", "usage"]
    formatted = [dict(zip(columns, row)) for row in result]

    return jsonify(formatted)

# Churn endpoint
@app.route("/churn")
def churn():
    return "📊 Churn model trained. Check terminal for metrics."

if __name__ == "__main__":
    app.run(debug=True)
