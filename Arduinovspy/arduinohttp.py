import requests

esp32_ip = "http://ESP32_IP/send"
data_to_send = {"data": "Hello from Python!"}

response = requests.get(esp32_ip, params=data_to_send)
print("Response from ESP32:", response.text)

