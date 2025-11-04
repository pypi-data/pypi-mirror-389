import requests

def exec(sql):
    url = "http://light-datalakehouse:8080/query"
    params = {'sql': sql}
    response = requests.get(url, params=params)
    return response.json()