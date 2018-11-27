import re
import json

class Tier_List_Card:
    def __init__(self, name, tier,tier_rank = "",card_type="",custom=""):
        self.name = name
        self.tier = tier
        self.tier_rank = tier_rank
        self.type = card_type
        self.custom = custom

    def __repr__(self):
        return self.tier + ' (' + self.tier_rank + ') ' + self.custom
    def __str__(self):
        return self.tier + ' (' + self.tier_rank + ') ' + self.custom
    

def scrape(page_link):
    try:
        page = requests.get(page_link, timeout=10)
        page.raise_for_status()
        
        
        soup = BeautifulSoup(page.content, "html.parser")
        
    #    tree = html.fromstring(page.content)
    #    xpath = '//*/li[1]'
    #    anuncio = tree.xpath(xpath)
               
        li = soup.find_all('script')
        sc_final = -1
        for sc in li:
            if ('const CARDS =' in sc.text):
                sc_final = sc.text
                
        if sc_final == -1:
            print("Error while scraping")
            return -1
        
        
        regex_const = 'const CARDS = (.*?}]);'
        m = re.findall(regex_const,sc_final)
        
        cards = json.loads(m[0])
        
        cards_by_type = {}
            
        for item in cards:
            name = item['name']
            tier = item['tier']
            tier_rank = item['tierRank']
            card_type = item['deck']
            
            
            if name != '' and tier!= '' :
                new_card = Tier_List_Card(name,tier,tier_rank=tier_rank,card_type=card_type)
                
                if card_type in cards_by_type:
                    cards_by_type[card_type].append(new_card)
                else:
                    cards_by_type[card_type] = [new_card]
                    
        for key in cards_by_type.keys():
            lista = cards_by_type[key]
            lista = sorted(lista, key=lambda x: x.name, reverse=False)     
            cards_by_type[key] = lista
            
        return cards_by_type
    except Exception as err:
        print("ERROR SCRAPING ARTIBUFF" )
        print(err)
        return -1

def make_tier_text(tier_lists,filename="tier_list.txt"):
    import os.path
    
    if os.path.exists(filename):
        dict_original = read_tier_text(filename)
    else:
        dict_original = {}
        
    
    
    file_txt = "#################################################################################################################################\n"
    file_txt +="# This file represents your tier list file. Default values are taken from https://drawtwo.gg/hypeds-limited-tier-list           #\n"
    file_txt +="# Tiers vary from S to F (S is the strongest) and each tier has an inside tier rank (1 is the best position inside the tier)    #\n"
    file_txt +="# Besides the tier and tier rank values you can also customize a custom value for each card that will be printed on the screen  #\n"
    file_txt +="#################################################################################################################################\n"
    for card_type in tier_lists.keys():
        lista_cards = tier_lists[card_type]
        file_txt += "# "+card_type.upper()+":\n"
        file_txt += "#card name; tier; tier rank; custom rank\n"
        for card in lista_cards:
            custom = ""
            if card.name in dict_original:
                custom = dict_original[card.name].custom
    
            file_txt += ";".join([card.name,card.tier,str(card.tier_rank),custom])+"\n"
        file_txt +="#################################################################################################################################\n"
    
    with open(filename, "w") as text_file:
        text_file.write(file_txt)
        
    return True
    
            
            
def read_tier_text(filename="tier_list.txt"):
    tier_dict = {}
    with open(filename, "r") as ins:
        for line in ins:
            if line.startswith("#")==False:
                props = line.split(";")
                name = props[0].strip()
                tier = props[1].strip()
                tier_rank = props[2].strip()
                custom = props[3].rstrip("\n")
                card = Tier_List_Card(name,tier,tier_rank=tier_rank,custom=custom)
                tier_dict[name] = card
                
    return tier_dict
    
        

def run_scrape():
    print("Updateing artibuff database")
    
    tier_link = "https://drawtwo.gg/hypeds-limited-tier-list"

    tier_lists = scrape(tier_link)
    
    make_tier_text(tier_lists,filename="tier_list.txt")
    
    tier_dict = read_tier_text(filename="tier_list.txt")
    

if __name__ == "__main__":
    from bs4 import BeautifulSoup
    import requests

    run_scrape()