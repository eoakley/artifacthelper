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