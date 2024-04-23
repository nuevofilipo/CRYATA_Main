import requests

# # For local hosts
# response = requests.post("http://localhost:5000/force")
# print("query running")
# print(response.json())

# For remote hosts on railway app
response = requests.post("https://table-system-production.up.railway.app/control")
print("query running")
print(response.json())  # Output: {'message': 'Controller is now ON'}
