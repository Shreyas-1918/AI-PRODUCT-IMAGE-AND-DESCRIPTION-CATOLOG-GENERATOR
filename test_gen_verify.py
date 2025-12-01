import requests
import json
import time

def test_generate():
    url = "http://127.0.0.1:5000/api/generate"
    payload = {
        "product": "Test Product",
        "variant": 1,
        "verify": True
    }
    headers = {'Content-Type': 'application/json'}
    
    print("Sending request...")
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            data = response.json()
            status = data.get("verification", {}).get("status")
            if status == "success":
                print("VERIFICATION_SUCCESS")
            else:
                print(f"VERIFICATION_FAILURE: {status}")
        else:
            print(f"HTTP_ERROR: {response.status_code}")
    except Exception as e:
        print(f"EXCEPTION: {e}")

if __name__ == "__main__":
    # Wait a bit for server to fully start
    time.sleep(5)
    
    # Check status
    try:
        status_res = requests.get("http://127.0.0.1:5000/api/status")
        print("Server Status:", status_res.json())
    except Exception as e:
        print(f"Could not check status: {e}")

    test_generate()
