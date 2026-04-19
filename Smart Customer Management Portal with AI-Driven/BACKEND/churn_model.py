import pandas as pd
import sqlite3
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report

def train_model():
    conn = sqlite3.connect("database.db")
    df = pd.read_sql("SELECT * FROM customers", conn)

    # Create fake churn label (logic-based)
    df["churn"] = (df["nps"] < 0) & (df["tickets"] > 20)

    X = df[["devices", "tickets", "nps", "monthly_usage"]]
    y = df["churn"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    model = LogisticRegression()
    model.fit(X_train, y_train)

    preds = model.predict(X_test)

    print("\n📊 Model Evaluation:")
    print(classification_report(y_test, preds))

    return model

if __name__ == "__main__":
    train_model()