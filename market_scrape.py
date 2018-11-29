#market prices scrap by bolo

import json
from urllib import request

def get_prices():
    """Get card prices from market using 3 requests. Don't spam this!"""
    prices = {}
    for i in range(3):
        req = request.urlopen('https://steamcommunity.com/market/search/render/?' + \
            'search_descriptions=0&sort_column=name&sort_dir=asc&appid=583950&norender=1&start='+str(100*i)+'&count=100')
        s = req.read().decode()
        a = json.loads(s)
        for b in a['results']:
            name = b['name']
            prices[name] = {'sell_price':b['sell_price_text'], 'sell_listings': b['sell_listings'], 'rarity':b['asset_description']['type']}
            print(name, end=', ')
        
        print('\n------\nCollected,', len(prices), 'prices.\n\n')
    return prices

if __name__ == "__main__":
    prices = get_prices()
    for key in prices.keys():
        print(key, prices[key]['sell_price'])