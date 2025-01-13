from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import sqlite3
import time

conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    name TEXT NOT NULL,
    price TEXT NOT NULL,
    discount_price TEXT,
    discount_percent TEXT,
    rating REAL,
    sold TEXT,
    seller TEXT,
    location TEXT,
    badge TEXT,
    link TEXT NOT NULL
)
''')
conn.commit()
conn.close()

def scrape_tokopedia_items(search_query, max_items):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    options = Options()
    options.add_argument("--headless")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36")

    driver = webdriver.Chrome(options=options)
    url = f"https://www.tokopedia.com/search?st=product&q={search_query}"
    driver.get(url)

    items = []
    while len(items) < max_items:
        while True:
            current_scroll_position = driver.execute_script("return window.scrollY + window.innerHeight")
            total_height = driver.execute_script("return document.body.scrollHeight")
            
            if current_scroll_position >= total_height:
                break
            else:
                driver.execute_script("window.scrollBy(0, 300);")
                time.sleep(0.1)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        item_cards = soup.find_all('div', class_='css-5wh65g')
        print(">", len(item_cards), "products found.")

        for card in item_cards:
            if len(items) >= max_items:
                break
            try:
                try:
                    name = card.find('span', class_='_0T8-iGxMpV6NEsYEhwkqEg==').text.strip()
                    price = card.find('div', class_='_67d6E1xDKIzw+i2D2L0tjw==').text.strip()
                    link = card.find('a', class_='oQ94Awb6LlTiGByQZo8Lyw== IM26HEnTb-krJayD-R0OHw==').get('href')
                except AttributeError:
                    break
                try:
                    discount_percent = card.find('span', class_='vRrrC5GSv6FRRkbCqM7QcQ==').text.strip()
                    if discount_percent:
                        discount_price = card.find('span', class_='q6wH9+Ht7LxnxrEgD22BCQ==').text.strip()
                except AttributeError:
                    discount_percent = "No Discount"
                    discount_price = "No Discount"
                try:
                    rating = card.find('span', class_='_9jWGz3C-GX7Myq-32zWG9w==').text.strip()
                except AttributeError:
                    rating = 0.0
                try:
                    sold = card.find('span', class_='se8WAnkjbVXZNA8mT+Veuw==').text.strip()
                except AttributeError:
                    sold = "0 terjual"
                try:
                    seller = card.find('span', class_='pC8DMVkBZGW7-egObcWMFQ==').text.strip()
                except AttributeError:
                    seller = "No Seller"
                try:
                    location = card.find('span', class_='pC8DMVkBZGW7-egObcWMFQ== flip').text.strip()
                except AttributeError:
                    location = "No Location"
                badge_raw = card.find('img', class_='YtXczlnkXDXQ59u3vhDxiA==')
                try:
                    img_src = badge_raw['src']
                    if 'official_store_badge' in img_src:
                        badge = "Official"
                    elif 'goldmerchant' in img_src:
                        badge = "Gold"
                    elif 'power_merchant' in img_src:
                        badge = "Power"
                except TypeError:
                    badge = "No Badge"
            except AttributeError:
                pass
            #print(">", name, "\n>", price, "\n>", discount_percent, "\n>", discount_price, "\n>", rating, "\n>", sold, "\n>", seller, "\n>", location, "\n>", badge, "\n>", link)
            items.append((search_query, name, price, discount_percent, discount_price, rating, sold, seller, location, badge, link))
        print(">", len(items), "total products appended.")
        
        if len(items) < max_items:
            try:
                driver.execute_script("window.scrollBy(0, -300);")
                next_button = driver.find_elements(By.CLASS_NAME, 'css-16uzo3v-unf-pagination-item')
                next_button[1].click()
                time.sleep(0.4)
            except Exception as e:
                print("Error:", e)
                break

    driver.quit()
    
    for query, name, price, discount_percent, discount_price, rating, sold, seller, location, badge, link in items:
        cursor.execute('''
        INSERT INTO items (query, name, price, discount_percent, discount_price, rating, sold, seller, location, badge, link)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (query, name, price, discount_percent, discount_price, rating, sold, seller, location, badge, link))
    conn.commit()

    #Temp Check
    print("\n>", len(items), "items saved.")
    cursor.execute("SELECT * FROM items")
    rows = cursor.fetchall()
    print(">", len(rows), "total items in database.\n")
    conn.close()

    return items

"""
search_query = "Baju Batik Wanita-Dress Batik Cheongsam Merah" #input("> Search query: ")
max_items = 10 #int(input("> Max query count: "))
items = scrape_tokopedia_items(search_query, max_items)
"""