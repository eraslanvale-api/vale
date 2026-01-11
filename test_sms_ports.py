import requests

def test_port(url):
    print(f"Testing {url}...")
    try:
        response = requests.get(url, timeout=5)
        print(f"Success! Status: {response.status_code}")
        return True
    except Exception as e:
        print(f"Failed: {e}")
        return False

if __name__ == "__main__":
    print("Checking alternative ports for SMS API...")
    
    # Test Standard HTTPS (443)
    test_port("https://smslogin.nac.com.tr/sms/create")
    
    # Test Standard HTTP (80)
    test_port("http://smslogin.nac.com.tr/sms/create")
