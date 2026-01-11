import requests
import logging
from django.conf import settings

# Logger konfigürasyonu
logger = logging.getLogger(__name__)

# SMS API Ayarları - NAC Telekom
# Port 9588 yerine standart 443 portu (https) kullanılıyor.
# Cloudflare Worker Proxy (PythonAnywhere whitelist engelini aşmak için)
# Orijinal URL: https://smsapi.nac.com.tr/v1/json/syncreply/Submit
# SSL hatası almamak için HTTP deniyoruz (Cloudflare genelde HTTPS'e yönlendirir ama proxy tüneli için HTTP daha rahat olabilir)
SMS_API_URL = "http://still-hill-6661sms-proxy.eraslanvale.workers.dev/"

SMS_USERNAME = "ferhatkucukaslan"
SMS_API_PASSWORD = "ajcDLcgdeHV"  # API şifresi
SMS_FROM = "08507770174"

# PythonAnywhere Proxy Ayarları
# Free hesaplar için proxy gereklidir.
# Cloudflare Worker kullanıldığında, Worker adresi genellikle whitelist'te olmayabilir 
# ancak workers.dev domainleri bazen erişilebilir olabilir. 
# Eğer Cloudflare Worker da 403 verirse, tek çare PythonAnywhere whitelist talebidir.
PROXY_URL = "http://proxy.server:3128"
PROXIES = {
    "http": PROXY_URL,
    "https": PROXY_URL,
}

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
    
    headers = {"Content-Type": "application/json"}
    
    # Yeni API JSON yapısı (smsapi.nac.com.tr)
    payload = {
        "Credential": {
            "Username": SMS_USERNAME,
            "Password": SMS_API_PASSWORD
        },
        "Header": {
            "From": SMS_FROM,
            "ValidityPeriod": 0
        },
        "Message": message,
        "To": [phone],
        "DataCoding": "Default"
    }
    
    logger.info(f"Sending SMS to {phone} with content: {message}")
    
    try:
        # PythonAnywhere Free Tier için Proxy Ayarları
        try:
            response = requests.post(
                SMS_API_URL, 
                json=payload, 
                headers=headers, 
                timeout=30,
                proxies=PROXIES
            )
        except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError) as proxy_err:
             # Proxy hatası (Örn: Local ortamda proxy yoksa veya proxy 403 veriyorsa)
             # Eğer 403 Forbidden varsa bu whitelist sorunudur, ancak yine de proxysiz denemekte fayda var (belki localdir)
             logger.warning(f"Proxy bağlantı hatası veya erişim engeli: {proxy_err}. Proxysiz deneniyor...")
             response = requests.post(
                SMS_API_URL, 
                json=payload, 
                headers=headers, 
                timeout=30
            )

        if response.status_code == 200:
            logger.info(f"SMS başarıyla gönderildi: {phone} - Response: {response.text}")
            return True
        else:
            logger.error(f"SMS gönderim hatası: Status={response.status_code}, Body={response.text}")
            return False
            
    except requests.exceptions.SSLError as e:
        logger.warning(f"SSL Error for {SMS_API_URL}. Retrying without verify: {e}")
        try:
            # SSL hatası durumunda verify=False ile tekrar dene
            response = requests.post(
                SMS_API_URL, 
                json=payload, 
                headers=headers, 
                timeout=30, 
                verify=False,
                proxies=PROXIES
            )
            if response.status_code == 200:
                logger.info(f"SMS başarıyla gönderildi (No Verify): {phone} - Response: {response.text}")
                return True
            else:
                logger.error(f"SMS gönderim hatası (No Verify): Status={response.status_code}, Body={response.text}")
                return False
        except Exception as e2:
            logger.error(f"SMS retry failed: {e2}")
            return False
            
    except Exception as e:
        logger.error(f"SMS gönderim genel hatası: {e}")
        return False


def send_verification_sms(phone_number, code):
    """Hesap doğrulama SMS'i gönder"""
    message = f"Premium Vale hesap doğrulama kodunuz: {code}"
    return send_sms(phone_number, message)


def send_password_reset_sms(phone_number, code):
    """Parola sıfırlama SMS'i gönder"""
    message = f"Premium Vale parola sıfırlama kodunuz: {code}"
    return send_sms(phone_number, message)
