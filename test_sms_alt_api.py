import requests
import json

SMS_API_URL = "https://smsapi.nac.com.tr/v1/json/syncreply/Submit"
SMS_USERNAME = "ferhatkucukaslan"
SMS_API_PASSWORD = "ajcDLcgdeHV"
SMS_FROM = "08507770174"

def test_alt_sms():
    print(f"Testing Alternative API: {SMS_API_URL}")
    
    payload = {
        "Credential": {
            "Username": SMS_USERNAME,
            "Password": SMS_API_PASSWORD
        },
        "Header": {
            "From": SMS_FROM,
            "ValidityPeriod": 0
        },
        "Message": "Premium Vale Test SMS",
        "To": ["905426907712"],
        "DataCoding": "Default"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(SMS_API_URL, json=payload, headers=headers, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_alt_sms()
