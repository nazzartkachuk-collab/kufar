import requests
import time
import re
import json
import os
from bs4 import BeautifulSoup

# ============================================
#  НАСТРОЙКИ (ЗАМЕНИТЕ НА СВОИ)
# ============================================

TELEGRAM_TOKEN = "8990778823:AAG0giH8pJzesRCDjHvoODy8puURtO3D1a0"
CHAT_ID = "8299079025"

KUFAR_URLS = [
    "https://www.kufar.by/l?query=gucci&rgn=all&sort=lst.d&suggested_categories=19010%2C8080%2C19020&utm_queryOrigin=Manually_typed",
    "https://www.kufar.by/l?query=balenciaga&utm_queryOrigin=Frequently_searched&utm_suggestionType=Query_only",
    "https://www.kufar.by/l?query=amiri&rgn=all&sort=lst.d&suggested_сategories=19010%2C8080%2C19020&utm_queryOrigin=Manually_typed",
    "https://www.kufar.by/l?query=zegna&rgn=all&sort=lst.d&suggested_сategories=19010%2C8080%2C19020&utm_queryOrigin=Manually_typed",
    "https://www.kufar.by/l?query=lanvin&rgn=all&sort=lst.d&suggested_сategories=19010%2C18030%2C19020",
     "https://www.kufar.by/l?query=украшения&rgn=all&sort=lst.d",
      "https://www.kufar.by/l?query=баленсиага&rgn=all&sort=lst.d",
     "https://www.kufar.by/l?query=burberry&rgn=all&sort=lst.d&suggested_сategories=19010%2C8080",
      "https://www.kufar.by/l?query=stone+island&rgn=all&sort=lst.d&suggested_сategories=19010%2C8080%2C19020ы"
    # добавьте другие ссылки, если нужно
]

LUXURY_BRANDS = ['gucci', 'prada', 'louis vuitton', 'chanel', 'dior',
                 'hermes', 'rolex', 'cartier', 'tiffany', 'bulgari',
                 'balenciaga', 'amiri', 'zegna', 'burberry', 'stone island',
                 'raf simons', 'vetements', 'rick owens']

CHECK_INTERVAL = 900  # 15 минут

# ============================================
#  РАБОТА С ФАЙЛОМ ДЛЯ ХРАНЕНИЯ ID
# ============================================

SEEN_FILE = "seen_ads.json"

def load_seen_ads():
    """Загружает множество ID из файла, если он существует."""
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    return set()

def save_seen_ads(seen_set):
    """Сохраняет множество ID в файл."""
    with open(SEEN_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(seen_set), f)

# ============================================
#  ОТПРАВКА СООБЩЕНИЙ ЧЕРЕЗ API TELEGRAM
# ============================================

def send_telegram_message(text):
    """Отправляет текст в Telegram через Bot API."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': text,
        'parse_mode': 'HTML'
    }
    try:
        resp = requests.post(url, data=payload, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")
        return False

# ============================================
#  ПАРСИНГ KUFAR
# ============================================

def get_ads_from_url(url):
    """Парсит страницу, возвращает список объявлений с люксовыми брендами."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"Ошибка загрузки {url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    ads = []

    link_tags = soup.find_all('a', href=re.compile(r'/item/\d+'))
    for link in link_tags:
        href = link.get('href')
        match = re.search(r'/item/(\d+)', href)
        if not match:
            continue
        ad_id = match.group(1)

        card = link.find_parent('section')
        if not card:
            card = link.find_parent('div', class_=re.compile(r'styles_wrapper'))
        if not card:
            continue

        title_tag = card.find('h3')
        if not title_tag:
            title_tag = card.find(class_=re.compile(r'title'))
        title = title_tag.get_text(strip=True) if title_tag else "Без названия"

        price_tag = card.find('p', class_=re.compile(r'price'))
        if not price_tag:
            price_tag = card.find('span', class_=re.compile(r'price'))
        price = price_tag.get_text(strip=True) if price_tag else "Цена не указана"

        if href.startswith('/'):
            full_link = 'https://www.kufar.by' + href
        else:
            full_link = href

        title_lower = title.lower()
        if any(brand in title_lower for brand in LUXURY_BRANDS):
            ads.append({
                'id': ad_id,
                'title': title,
                'price': price,
                'link': full_link
            })

    return ads

def main():
    print("🚀 Бот запущен. Мониторинг Kufar...")
    
    # Загружаем ранее сохранённые ID
    seen_ads = load_seen_ads()
    print(f"Загружено {len(seen_ads)} ранее отправленных объявлений.")

    # Первый прогон: собираем все текущие объявления и добавляем их в seen_ads,
    # но НЕ отправляем (чтобы не спамить старыми).
    # Для этого мы просто один раз спарсим все URL и обновим множество.
    # После этого будем проверять только новые.
    initial_ads = set()
    for url in KUFAR_URLS:
        ads = get_ads_from_url(url)
        for ad in ads:
            initial_ads.add(ad['id'])
    # Объединяем с уже существующими (на случай, если файл уже был)
    seen_ads.update(initial_ads)
    save_seen_ads(seen_ads)
    print(f"Инициализация завершена. В базе {len(seen_ads)} объявлений. Теперь отслеживаю новые.")

    # Основной цикл
    while True:
        for url in KUFAR_URLS:
            print(f"Проверка {url} в {time.ctime()}")
            ads = get_ads_from_url(url)
            if not ads:
                print("  Новых люксовых объявлений нет.")
            else:
                new_ads_found = False
                for ad in ads:
                    if ad['id'] not in seen_ads:
                        seen_ads.add(ad['id'])
                        new_ads_found = True
                        msg = (f"🛍️ НОВОЕ ЛЮКСОВОЕ ОБЪЯВЛЕНИЕ!\n\n"
                               f"📌 {ad['title']}\n"
                               f"💰 {ad['price']}\n"
                               f"🔗 {ad['link']}")
                        if send_telegram_message(msg):
                            print(f"Отправлено: {ad['title']}")
                        else:
                            print(f"Не удалось отправить: {ad['title']}")
                        time.sleep(1)
                if new_ads_found:
                    # Сохраняем обновлённый список ID в файл
                    save_seen_ads(seen_ads)
                else:
                    print("  Новых объявлений не найдено.")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()