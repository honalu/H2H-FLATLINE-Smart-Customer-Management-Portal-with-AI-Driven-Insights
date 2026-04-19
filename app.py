import sqlite3
from flask import Flask, render_template
from models import get_db, init_db
app = Flask(__name__)
@app.route('/')
def dashboard():
    return render_template('base.html')
@app.route('/customers')
def customers():
    conn=get_db()
    conn.row_factory=sqlite3.Row
    customers=conn.execute('SELECT*FROM customers').fetchall()
    conn.close()
    return render_template('customers.html',customers=customers)
if __name__=='__main__':
    init_db()
    app.run(debug=True)
    