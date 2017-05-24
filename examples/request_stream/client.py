import requests

# Warning: This is a heavy process.

data = ""
for i in range(1, 250000):
    data += str(i)

r = requests.post('http://127.0.0.1:8000/stream', data=data)
print(r.text)
