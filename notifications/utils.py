import requests
import json

def send_expo_push_notification(tokens, title, message, data=None):
    """
    Expo Push API kullanarak bildirim gönderir.
    tokens: String (tek token) veya List (birden fazla token)
    """
    url = 'https://exp.host/--/api/v2/push/send'
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Accept-Encoding': 'gzip, deflate',
    }

    if isinstance(tokens, str):
        tokens = [tokens]
    
    # Filter out empty tokens
    tokens = [t for t in tokens if t]

    if not tokens:
        return

    # Expo en fazla 100 token kabul eder, eğer daha fazlaysa batch yapılabilir ama şimdilik basit tutalım.
    # Her kullanıcı için mesaj oluşturuyoruz
    messages = []
    for token in tokens:
        if not token.startswith('ExponentPushToken') and not token.startswith('ExpoPushToken'):
            continue
            
        messages.append({
            'to': token,
            'title': title,
            'body': message,
            'data': data or {},
            'sound': 'default',
        })

    if not messages:
        return

    try:
        # Chunking (Expo recommends batches of 100)
        chunk_size = 100
        for i in range(0, len(messages), chunk_size):
            chunk = messages[i:i + chunk_size]
            response = requests.post(url, headers=headers, data=json.dumps(chunk))
            print(f"Expo Push Notification Response ({i}-{i+len(chunk)}): {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Expo Push Notification Error: {e}")
