import numpy as np
from datetime import datetime

def calculate_scores(repo):
    """
    Proje metriklerini kullanarak Kalite, Aktivite ve Öğrenme skorlarını hesaplar.
    """
    stars = repo.get('stars', 0)
    forks = repo.get('forks', 0)
    issues = repo.get('issues', 0)

    # QUALITY (Kalite): Yıldız ve Fork sayılarının logaritmik ağırlığı
    quality = (np.log1p(stars) * 0.6 + np.log1p(forks) * 0.4) * 10

    # ACTIVITY (Aktivite): Son güncelleme tarihine göre güncel kalma durumu
    try:
        last_update = datetime.strptime(repo['update_date'], "%Y-%m-%d")
        days = (datetime.now() - last_update).days
        activity = max(0, 100 - days)
    except:
        activity = 50

    # LEARNING (Öğrenme): Readme uzunluğuna göre eğitim değeri
    readme_len = repo.get('readme_length', 0)
    learning = min(100, readme_len / 50)

    return {
        "quality": round(quality, 2),
        "activity": round(activity, 2),
        "learning": round(learning, 2)
    }

def generate_why(repo):
    """
    Skorlara dayanarak projenin neden seçilmesi gerektiğini açıklayan metinler üretir.
    """
    why = []

    if repo['scores']['quality'] > 50:
        why.append("Yüksek topluluk ilgisi (star/fork)")

    if repo['scores']['activity'] > 70:
        why.append("Aktif olarak geliştiriliyor")

    if repo['scores']['learning'] > 50:
        why.append("Öğrenmek için iyi dokümantasyon")

    if not why:
        why.append("Ortalama seviyede bir proje")

    return why

def classify_level(repo):
    """
    Yıldız sayısına göre projenin zorluk/kıdem seviyesini belirler.
    """
    stars = repo.get('stars', 0)

    if stars < 100:
        return "Beginner"
    elif stars < 500:
        return "Intermediate"
    else:
        return "Advanced"

def detect_risk(repo):
    """
    Son güncelleme üzerinden projenin terk edilip edilmediğini kontrol eder.
    """
    try:
        last_update = datetime.strptime(repo['update_date'], "%Y-%m-%d")
        days = (datetime.now() - last_update).days

        if days > 180:
            return "Pasif proje"
        else:
            return "Aktif"
    except:
        return "Bilinmiyor"