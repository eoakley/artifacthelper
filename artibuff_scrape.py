from itertools import chain
import pickle

class Artibuff_Card:
    def __init__(self, name, win_rate,pick_rate):
        self.name = name
        self.win_rate = win_rate
        self.pick_rate = pick_rate

    def __repr__(self):
        return 'WR: ' + str(self.win_rate)[:-1] + '% | PR: ' + str(self.pick_rate)[:-1] + '%'
    def __str__(self):
        return 'WR: ' + str(self.win_rate)[:-1] + '% | PR: ' + str(self.pick_rate)[:-1] + '%'

# Validates an ArtifactBuff table row object
def validate_row(row_html):
    try:
        row_html = row_html.text.strip()
        if len(row_html) == 0:
            return None
        
        return row_html
    
    except:
        return None


def string_to_float(string):
    try:
        string = float(string.strip().strip('%').strip())
        return string
    except:
        return None
    
    

def scrape(page_link):
    try:
        page = requests.get(page_link, timeout=10)
        page.raise_for_status()
        
        
        soup = BeautifulSoup(page.content, "html.parser")
        
    #    tree = html.fromstring(page.content)
    #    xpath = '//*/li[1]'
    #    anuncio = tree.xpath(xpath)
        
        tier_list = []
        
        li = soup.find_all('tr')
        
        for item in li:
            name = item.find('td',attrs={'class':'cardName'})
            
            try:
                name = name.find('a')
            except:
                name = None
            name = validate_row(name)
                
            win_rate = item.find('td',attrs={'class':'winRate'})
            win_rate = validate_row(win_rate)
            win_rate = string_to_float(win_rate)
                
            pick_rate = item.find('td',attrs={'class':'pickRate'})
            pick_rate = validate_row(pick_rate)
            pick_rate = string_to_float(pick_rate)
            
            if name != None and win_rate!= None and pick_rate!= None :
                new_card = Artibuff_Card(name,win_rate,pick_rate)
                tier_list.append(new_card)
                
        #tier_list = sorted(tier_list, key=lambda x: x.name, reverse=False)
        
        tier_list_dict = {}
        for c in tier_list:
            tier_list_dict[c.name]= c
            
        return tier_list_dict
    except Exception as err:
        print("ERROR SCRAPING ARTIBUFF" )
        print(err)
        return -1

def dict_union(*args):
    return dict(chain.from_iterable(d.items() for d in args))

def load_pickle(file_name="card_dict.pkl"):
    try:
        with open(file_name, 'rb') as handle:
            b = pickle.load(handle)
        return b
    except Exception as err:
        print("Error loading pickle")
        print(err)

def save_pickle(obj, file_name="card_dict.pkl"):
    try:
        with open(file_name, 'wb') as handle:
            pickle.dump(obj, handle, protocol=pickle.HIGHEST_PROTOCOL)
        return True
    except Exception as err:
        print("Error saving pickle")
        print(err)

def run_scrape():
    print("Updating artibuff database")
    
    heroes = "https://www.artibuff.com/stats/heroes?mode=draft"
    main_deck = "https://www.artibuff.com/stats/mains?mode=draft"
    items = "https://www.artibuff.com/stats/items?mode=draft"

    heroes_dict = scrape(heroes)
    main_dict = scrape(main_deck)
    items_dict = scrape(items)
    
    full_dict = dict_union(heroes_dict,main_dict,items_dict)
    
    file_name="model/card_dict.pkl"
    
    save_pickle(full_dict,file_name)
    print("Done, saved on: ",file_name)
        
if __name__ == "__main__":
    from bs4 import BeautifulSoup
    import requests
    from lxml import html
    
    run_scrape()