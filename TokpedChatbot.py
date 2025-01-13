import discord
from discord.ext import commands
from autocorrect import Speller
import spacy
import re
from TokpedScraper import scrape_tokopedia_items

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)
spell = Speller()
nlp = spacy.load("en_core_web_sm")
max_items = 50
ignored_words = ["good", "times"]

@bot.event
async def on_ready():
    print(f"{bot.user} is Online")

@bot.command()
async def find(ctx, *, query):
    await ctx.send(f"Finding {(query).replace('me', 'you')}")
    operators, price_values, query = extract_user_price_filter(query)
    """
    await ctx.send(query)
    await ctx.send(operators)
    await ctx.send(price_values)
    """
    rating_values, sold_values, seller_values, query = extract_user_trust_filter(query)
    """
    await ctx.send(query)
    await ctx.send(rating_values)
    await ctx.send(sold_values)
    await ctx.send(seller_values)
    """
    search_query = extract_user_search(query)
    #await ctx.send(f"Finding {(search_query)}")
    items = scrape_tokopedia_items(search_query, max_items)
    if "above_average" in operators:
        operators = ['above']
        price_values = [(calculate_percentile_price(items, 75))]
    elif "below_average" in operators:
        operators = ['below']
        price_values = [(calculate_percentile_price(items, 25))]
    if operators and price_values:
        items = filter_items_price(items, operators, price_values)
    if "trusted" in seller_values:
        sold_values = [(calculate_sold_amount(items, 50))]
    if rating_values:
        items = filter_items_rating(items, rating_values)
    if sold_values:
        items = filter_items_sold(items, sold_values)
    if items:
        response = format_items(items)
        await ctx.send(response)
    else:
        await ctx.send("No results found.")

def extract_user_search(query):
    query = nlp(query.lower())
    search_phrases = []
    search_words = []

    for token in query:
        if (token.pos_ in {"NOUN", "PROPN", "ADJ", "NUM"} or token.ent_type_ in {"ORG", "PRODUCT", "GPE"}) and token.text not in ignored_words:
            search_words.append(token.text)
        elif search_words:
            search_phrases.append(" ".join(search_words))
            search_words = []
    if search_words:
        search_phrases.append(" ".join(search_words))

    search_query = " ".join(search_phrases).strip()
    return search_query

def extract_user_price_filter(query):
    price_values = []
    operators = []

    price_match = re.findall(r"(under|below|above)\s*[^0-9]*(\d*(?:[ ,.]\d{3})*)", query)
    range_match = re.search(r"(ranging|range)\s*[^0-9]*(\d*(?:[ ,.]\d{3})*)[^0-9]*(\d*(?:[ ,.]\d{3})*)", query)

    if range_match:
        operators = ['range']
        price_values = [re.sub(r'[^\d]', '', range_match.group(2)),
                        re.sub(r'[^\d]', '', range_match.group(3))]
        if price_values[1] > price_values[0]:
            price_values[0], price_values[1] = price_values[1], price_values[0]
        query = re.sub(r"(ranging|range)\s*[^0-9]*(\d*(?:[ ,.]\d{3})*)[^0-9]*(\d*(?:[ ,.]\d{3})*)", "", query)

    elif len(price_match) == 2:
        operators = ['range']
        price_values = [(re.sub(r'[^\d]', '', price_match[0][1])),
                        (re.sub(r'[^\d]', '', price_match[1][1]))]
        query = re.sub(r"(under|below|above)\s*[^0-9]*(\d*(?:[ ,.]\d{3})*)", "", query)
    elif len(price_match) == 1:
        operators = [price_match[0][0]]
        price_values = [(re.sub(r'[^\d]', '', price_match[0][1]))]
        query = re.sub(r"(under|below|above)\s*[^0-9]*(\d*(?:[ ,.]\d{3})*)", "", query)
    else:
        if re.search(r"(expensive|luxurious)", query):
            operators = ['above_average']
            price_values = [0]
            query = re.sub(r"(expensive|luxurious)", "", query)
        elif re.search(r"(cheap|affordable)", query):
            operators = ['below_average']
            price_values = [0]
            query = re.sub(r"(cheap|affordable)", "", query)

    price_values = [int(price) for price in price_values]
    query = re.sub(r"(price|under|below|above|ranging|range|expensive|luxurious|cheap|affordable|rp)", "", query)
    return operators, price_values, query

def extract_user_trust_filter(query):
    rating_values = []
    sold_values = []
    seller_values = []

    rating_match = re.search(r"(rating\s*[^0-9]*)(\d*(?:.\d{1}))|(\d*(?:.\d{1}))\s*[^0-9]*rating", query)
    if rating_match:
        if rating_match.group(2):
            rating_values = [float(re.sub(r'[^\d.]', '', rating_match.group(2)))]
        elif rating_match.group(3):
            rating_values = [float(re.sub(r'[^\d.]', '', rating_match.group(3)))]
        query = re.sub(r"(rating\s*[^0-9]*)(\d*(?:.\d{1}))|(\d*(?:.\d{1}))\s*[^0-9]*rating", "", query)
    
    sold_match = re.search(r"(sell|sold)\s*[^0-9]*(\d+)|(\d+)\s*[^0-9]*(sell|sold)", query)
    if sold_match:
        if sold_match.group(2):
            sold_values = [int(re.sub(r'[^\d.]', '', sold_match.group(2)))]
        elif sold_match.group(3):
            sold_values = [int(re.sub(r'[^\d.]', '', sold_match.group(3)))]
        query = re.sub(r"(sell|sold)\s*[^0-9]*(\d+)|(\d+)\s*[^0-9]*(sell|sold)", "", query)
    
    seller_match = re.search(r"(trusted|trustworthy|trust)\s*[^0-9]*(seller|source)|(seller|source)\s*[^0-9]*(trusted|trustworthy|trust)", query)
    if seller_match:
        if not rating_values:
            rating_values = [4.5]
        if not sold_values:
            seller_values = ["trusted"]
        query = re.sub(r"(trusted|trustworthy|trust)\s*[^0-9]*(seller|source)|(seller|source)\s*[^0-9]*(trusted|trustworthy|trust)", "", query)
        
    query = re.sub(r"(rating)", "", query)
    return rating_values, sold_values, seller_values, query
        
def calculate_percentile_price(items, percentile):
    prices = []
    for item in items:
        price = int(item[2].replace('Rp', '').replace('.', ''))
        prices.append(price)
    percentile_price = sum(prices) / len(prices) * (percentile / 100)
    return percentile_price

def calculate_sold_amount(items, percentile):
    solds = []
    for item in items:
        rb = False
        sold = item[6]
        if 'rb' in item[6]:
            sold = sold.replace('rb', '')
            rb = True
        sold = int(sold.replace('terjual', '').replace('+', ''))
        if rb == True:
            sold = sold * 1000
        solds.append(sold)
    percentile_sold = sum(solds) / len(solds) * (percentile / 100)
    return percentile_sold

def filter_items_price(items, operators, price_values):
    items_filtered = []
    for item in items:
        price = int(item[2].replace('Rp', '').replace('.', ''))
        if "range" in operators and price_values[0] <= price <= price_values[1]:
            items_filtered.append(item)
        elif ("below" in operators or "under" in operators) and price <= price_values[0]:
            items_filtered.append(item)
        elif "above" in operators and price >= price_values[0]:
            items_filtered.append(item)
    return items_filtered

def filter_items_rating(items, rating_values):
    items_filtered = []
    for item in items:
        rating = float(item[5])
        if rating >= rating_values[0]:
            items_filtered.append(item)
    return items_filtered

def filter_items_sold(items, sold_values):
    items_filtered = []
    for item in items:
        rb = False
        sold = item[6]
        if 'rb' in item[6]:
            sold = sold.replace('rb', '')
            rb = True
        sold = int(sold.replace('terjual', '').replace('+', ''))
        if rb == True:
            sold = sold * 1000
        if sold >= sold_values[0]:
            items_filtered.append(item)
    return items_filtered

def format_items(items):
    response = ""
    for item in items[:3]:
        link_short = f"[Click here to view product](<{item[10]}>)"
        if item[3] != "No Discount":
            response += f"**{item[1]}**\nPrice: {item[2]}   <-{item[3]}-   ~~{item[4]}~~\nRating: {item[5]}     Sold: {item[6]}\nSeller: {item[7]}        Location: {item[8]}\n{link_short}\n\n"
        else:
            response += f"**{item[1]}**\nPrice: {item[2]}\nRating: {item[5]}        Sold: {item[6]}\nSeller: {item[7]}        Location: {item[8]}\n{link_short}\n\n"
    return response

