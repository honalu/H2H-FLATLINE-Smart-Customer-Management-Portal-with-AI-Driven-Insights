import requests

url = "http://127.0.0.1:5000/query"

data = {
    "query": "top 5 customers with highest nps"
}

response = requests.post(url, json=data)

print(response.json())