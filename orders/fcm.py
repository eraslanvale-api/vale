import requests
import json

def send_to_tokens(tokens, title, body, data=None):
    """
    Sends notifications using Expo Push API.
    """
    if not tokens:
        return {"success": 0, "failure": 0}

    # Filter for valid Expo push tokens
    expo_tokens = [t for t in tokens if t.startswith('ExponentPushToken') or t.startswith('ExpoPushToken')]
    
    if not expo_tokens:
        return {"success": 0, "failure": len(tokens), "error": "no_valid_expo_tokens"}

    url = "https://exp.host/--/api/v2/push/send"
    headers = {
        "host": "exp.host",
        "accept": "application/json",
        "accept-encoding": "gzip, deflate",
        "content-type": "application/json"
    }

    # Expo supports batch sending (up to 100 at a time)
    # For simplicity, we'll send in one batch if small, or you can loop.
    # Here we construct the payload for each token or a broadcast style.
    # Expo API allows an array of messages.
    
    messages = []
    for token in expo_tokens:
        messages.append({
            "to": token,
            "sound": "default",
            "title": title,
            "body": body,
            "data": data or {}
        })

    try:
        # We can send up to 100 messages per request.
        # Simple chunking for safety
        chunk_size = 100
        success_count = 0
        failure_count = 0
        
        for i in range(0, len(messages), chunk_size):
            chunk = messages[i:i + chunk_size]
            response = requests.post(url, headers=headers, json=chunk)
            response.raise_for_status()
            res_data = response.json()
            
            if 'data' in res_data:
                for item in res_data['data']:
                    if item['status'] == 'ok':
                        success_count += 1
                    else:
                        failure_count += 1
            
        return {"success": success_count, "failure": failure_count}

    except Exception as e:
        return {"success": 0, "failure": len(expo_tokens), "error": str(e)}
