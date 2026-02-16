import requests
import json
from django.core.mail import send_mail
from django.conf import settings

def send_html_email(subject, message, recipient_list):
    """
    Standart HTML şablonu kullanarak e-posta gönderir.
    Marka renkleri:
    - Primary (Gold): #D4AF37
    - Navy: #0D1B3A
    """
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f8fafc;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                margin-top: 40px;
                margin-bottom: 40px;
            }}
            .header {{
                background-color: #0D1B3A; /* Navy 900 */
                padding: 40px;
                text-align: center;
                border-bottom: 4px solid #D4AF37; /* Primary Gold */
            }}
            .logo-text {{
                color: #ffffff;
                font-size: 24px;
                font-weight: 900;
                text-transform: uppercase;
                letter-spacing: -0.05em;
                margin: 0;
            }}
            .logo-highlight {{
                color: #D4AF37; /* Primary Gold */
            }}
            .content {{
                padding: 40px;
                color: #334155;
            }}
            .title {{
                font-size: 20px;
                font-weight: 800;
                color: #0D1B3A; /* Navy 900 */
                margin-bottom: 24px;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }}
            .message-box {{
                background-color: #fdfbeb; /* Primary 50 */
                border-left: 4px solid #D4AF37; /* Primary Gold */
                padding: 24px;
                border-radius: 8px;
                font-size: 16px;
                line-height: 1.6;
                color: #0f172a;
            }}
            .footer {{
                background-color: #f8fafc;
                padding: 32px;
                text-align: center;
                border-top: 1px solid #e2e8f0;
            }}
            .footer-text {{
                color: #94a3b8;
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }}
            .social-links {{
                margin-top: 16px;
            }}
            .social-link {{
                color: #64748b;
                text-decoration: none;
                margin: 0 8px;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 class="logo-text">Premium <span class="logo-highlight">Vale</span></h1>
            </div>
            <div class="content">
                <h2 class="title">{subject}</h2>
                <div class="message-box">
                    {message.replace(chr(10), '<br>')}
                </div>
            </div>
            <div class="footer">
                <p class="footer-text">© 2024 Premium Vale Hizmetleri</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        send_mail(
            subject=subject,
            message=message, # Fallback plain text
            html_message=html_content, # HTML Content
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=True
        )
        return True
    except Exception as e:
        print(f"Email send error: {e}")
        return False

def send_expo_push_notification(tokens, title, message, data=None, sound='default', channel_id='default'):
    """
    Expo Push API kullanarak bildirim gönderir.
    tokens: String (tek token) veya List (birden fazla token)
    sound: 'default' veya özel ses dosyası adı (örn: 'notification.wav')
    channel_id: Android bildirim kanalı ID'si
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
            'sound': sound, 
            'channelId': channel_id,
            'badge': 1,
            'priority': 'high',
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
