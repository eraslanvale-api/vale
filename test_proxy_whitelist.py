import requests

PROXY_URL = "http://proxy.server:3128"
PROXIES = {
    "http": PROXY_URL,
    "https": PROXY_URL,
}

def test_url(url, name):
    print(f"Testing connectivity to {name} ({url})...")
    try:
        response = requests.get(url, proxies=PROXIES, timeout=10)
        print(f"SUCCESS: {name} is accessible. Status: {response.status_code}")
    except Exception as e:
        print(f"FAILURE: {name} is NOT accessible. Error: {e}")

if __name__ == "__main__":
    # 1. Test a domain known to be whitelisted
    test_url("https://www.google.com", "Google")
    
    # 2. Test the NAC API domain
    test_url("https://smsapi.nac.com.tr/v1/json/syncreply/Submit", "NAC SMS API")
