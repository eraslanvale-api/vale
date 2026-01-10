import requests
import base64
from django.conf import settings

# SMS API Ayarları - NAC Telekom
SMS_API_URL = "https://smslogin.nac.com.tr:9588/sms/create"
SMS_USERNAME = "ferhatkucukaslan"
SMS_API_PASSWORD = "ajcDLcgdeHV"  # API şifresi
SMS_FROM = "08507770174"


def get_auth_header():
    """Basic Authentication header oluştur"""
    credentials = f"{SMS_USERNAME}:{SMS_API_PASSWORD}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}


def format_phone_number(phone_number):
    """Telefon numarasını API formatına çevir (90XXXXXXXXXX)"""
    phone = str(phone_number).strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    
    # Başındaki + işaretini kaldır
    if phone.startswith("+"):
        phone = phone[1:]
    
    # Başında 0 varsa kaldır
    if phone.startswith("0"):
        phone = phone[1:]
    
    # 90 ile başlamıyorsa ekle
    if not phone.startswith("90"):
        phone = "90" + phone
    
    return phone


def send_sms(phone_number, message):
    """SMS gönderim fonksiyonu - NAC Telekom / Netgsm"""
    phone = format_phone_number(phone_number)
    
    headers = get_auth_header()
    headers["Content-Type"] = "application/json"
    
    # İstenen yeni JSON yapısı
    payload = {
        "type": 1,
        "sendingType": 0,
        "title": "Premium Vale",
        "content": message,
        "number": phone,  # Formatlanmış numara (örn: 905xxxxxxxxx)
        "encoding": 0,
        "sender": SMS_FROM,
        "validity": 60,
        "commercial": False,
        "recipientType": 0
    }
    
    try:
        response = requests.post(SMS_API_URL, json=payload, headers=headers, timeout=30)
        
        # Yanıt formatı değişmiş olabilir, status_code ile kontrol edelim
        if response.status_code == 200:
            print(f"SMS başarıyla gönderildi: {phone}")
            return True
        else:
            print(f"SMS gönderim hatası: Status={response.status_code}, Body={response.text}")
            return False
            
    except Exception as e:
        print(f"SMS gönderim hatası: {e}")
        return False


def send_verification_sms(phone_number, code):
    """Hesap doğrulama SMS'i gönder"""
    message = f"Premium Vale hesap doğrulama kodunuz: {code}"
    return send_sms(phone_number, message)


def send_password_reset_sms(phone_number, code):
    """Parola sıfırlama SMS'i gönder"""
    message = f"Premium Vale parola sıfırlama kodunuz: {code}"
    return send_sms(phone_number, message)
