import requests
import json

def main():
    url = "http://127.0.0.1:8000/backend/get_groups_from_db"
    params = {"device_number": 1}  # Assuming device_number 1 exists

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            # Print formatted JSON
            print(json.dumps(data, indent=4, ensure_ascii=False))
        else:
            print(f"Error: HTTP {response.status_code} - {response.text}")

    except requests.exceptions.ConnectionError:
        print("Connection error: Make sure the FastAPI server is running on localhost:8000")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
