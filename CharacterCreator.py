import re
from typing import Text
import bs4
import mechanize
import requests
import unicodedata
import time
from pprint import pp, pprint
from bs4 import BeautifulSoup
import concurrent.futures

class CharacterCreator:
    def create(self, character_name):
        """
        Main method that manages the charactor creation.

        character_name: This will be the name the character will be given.
        """
        total_start_time = time.perf_counter()

        print("Fetching character.. ", end="", flush=True)
        start_time = time.perf_counter()
        soup = self.fetch_character(character_name)
        print("%.2fs" % (time.perf_counter() - start_time))

        print("Cleaning up HTML.. ", end="", flush=True)
        start_time = time.perf_counter()
        self.soup_cleanup(soup)
        print("%.2fs" % (time.perf_counter() - start_time))

        character_array = {}

        print("Reading main stats..", end="", flush=True)
        start_time = time.perf_counter()
        character_array['main_stats'] = self.get_main_stats(character_name, soup)
        print("%.2fs" % (time.perf_counter() - start_time))

        print("Reading combat stats..", end="", flush=True)
        start_time = time.perf_counter()
        character_array['combat'] = self.get_combat_stats(soup)
        print("%.2fs" % (time.perf_counter() - start_time))

        start_time = time.perf_counter()
        character_array['ability'] = self.get_ability_stats_multithread(soup)
        finish = time.perf_counter()
        print("Abilities multithread took %.2fs" % (finish - start_time))
        
        print("Reading other stats..", end="", flush=True)
        start_time = time.perf_counter()
        character_array['other'] = self.get_other_stats(soup)
        print("%.2fs" % (time.perf_counter() - start_time))

        #pp(character_array, width=150)

        print()
        print("Complete creation took %.2fs!" % (time.perf_counter() - total_start_time))
        print()

        return character_array

    def fetch_character(self, character_name) -> BeautifulSoup:
        """
        This creates the call to the website to create a charactor.
        It sets neccessary form values and returns the charactor page as a BeautifulSoup object.
        """
        
        # Setting Browser and Website
        br = mechanize.Browser()
        br.addheaders = [("User-agent","Mozilla/5.0")]
        url = "https://fastcharacter.com/"
        br.open(url)

        # Fill character creation form
        br.select_form(nr=0)
        if character_name != "":
            br["randomname"] = ["no"]
            br["pcname"] = character_name

        br["pcformat"] = ["text"]

        response2 = br.submit()
        return BeautifulSoup(response2, 'html.parser')

    def soup_cleanup(self, soup: BeautifulSoup):
        """
        Removes elements that are not of any use.
        E.g. <br> and \\n
        """
        breaks = soup.findAll("br")
        for br in breaks:
            br.decompose()

        for elem in soup.findAll(string=True):
            if isinstance(elem, bs4.element.NavigableString) and elem.text == "\n":
                    elem.extract()
            elem.replace("\n", "")

        for paragraph in soup.findAll("p"):
            if paragraph.text == "":
                paragraph.decompose()

    def translate(self, searchtext):
        """
        Given a search text this method will attempt to translate the given text.
        If not translation was found the english text will be returned.
        """
        url = "https://www.dnddeutsch.de/tools/json.php?apiv=0.7&s="+ searchtext +"&o=dict&mi=on&mo=on&sp=on&it=on&misc=on"

        response = requests.post(url)
        json_response = response.json()

        if 'result' in json_response:
            return json_response['result'][0]['name_de']

        return searchtext

    def get_main_stats(self, character_name, soup):
        # Main stat character tags.
        character_tags = [
            "Name:",
            "Race/Ancestry/Heritage:",
            "Class & Level:",
            "Background:",
            "Alignment:"
        ]

        # Pass Json to dictionary.
        character_array = {}
        for tag in character_tags:
            tag_name = soup.find('strong', text = tag)
            tag_text = tag_name.nextSibling[1:]
            short_tag = tag.replace(":","")
            if short_tag == "Name":
                character_array["Name"] = tag_text
            elif short_tag == "Class & Level":
                str_arr = tag_text.split()
                klasse = self.translate(str_arr[0])
                character_array["Klasse"] = klasse
                character_array["Level"] = str_arr[1]
            elif short_tag == "Race/Ancestry/Heritage":
                tag_text = self.translate(tag_text)
                character_array["Volk"] = tag_text
            else:
                tag_text = self.translate(tag_text)
                character_array[self.translate(short_tag)] = tag_text
        
        age_elem = soup.find("p", string=re.compile("Age:*"))
        age = re.findall(r'\d+', age_elem.text)
        character_array["Alter"] = age[0]

        return character_array

    def get_combat_stats(self, soup):
        combat_stats = {}
        combat = soup.find(lambda tag:tag.name=="p" and "COMBAT" in tag.text)

        for elem in combat:
            if "FEATURES, TRAITS, SPECIAL ABILITIES" in elem.text:
                break
            if isinstance(elem, bs4.element.Tag):
                combat_stats = self.procces_combat_stats(elem, combat_stats)
  
        return combat_stats

    def procces_combat_stats(self, stat, combat_stats):
        stat_text = stat.text
        if "COMBAT" in stat_text:
            # Extract passive perception
            passive_perception = self.find_non_empty_sibling(stat.next_sibling)
            combat_stats['Passive Wahrnehmung'] = passive_perception.replace("\n", "").split(" ... ")[0]

            # Extract initiative modifier
            initiative_modifier = self.find_non_empty_sibling(passive_perception.next_sibling)
            combat_stats['Initiative Mod'] = initiative_modifier.replace("\n", "").split(" ... ")[0]
        elif "Armor Class" in stat_text:
            armor_class = stat_text.split(" ")[1]
            combat_stats['Rüstungsklasse'] = armor_class

            kind_of_armor = self.find_non_empty_sibling(stat.next_sibling)

            # +2 to exclude the ": "
            index = (kind_of_armor.find(": ")+2)
            combat_stats['Rüstungsart'] = kind_of_armor[index:]
        elif "Speed" in stat_text:
            feet = stat_text[:2]
            meters = int(feet) / 5 + 1.5
            combat_stats['Geschwindigkeit'] = str(meters) + "m"
        elif "hit points" in stat_text:
            hit_points = stat_text[:2]
            combat_stats['Trefferpunkte'] = str(hit_points)
        else:
            stat_name = stat.find("strong").text.replace(".", "")
            ger_stat_name = self.translate((stat_name))

            stat_detail = stat.text.split(stat_name + ". ")
            if len(stat_detail) > 1:
                stat_detail = stat_detail[1]
            else:
                print("index out of range for " + stat_name)

            combat_stats[ger_stat_name] = stat_detail

        return combat_stats

    def get_ability_stats_multithread(self, soup: BeautifulSoup):
        abilities_dict = {}

        start_tag = soup.find("strong",text="ABILITY SCORES & ABILITIES")
        
        start_ability = start_tag.findNext("strong")
        abilities = self.collect_main_abilities(start_ability)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(self.collect_sub_abilities, abilities)

        for result in results:
            for name, data in result.items():
                
                abilities_dict[name] = data

        return abilities_dict

    def collect_main_abilities(self, ability: BeautifulSoup):
        main_abilities = []

        while True:
            main_abilities.append(ability)

            sibling = ability.findNext("strong")
            if ability.text == sibling.text or "COMBAT" in sibling.text:
                break
            ability = sibling

        return main_abilities

    def collect_sub_abilities(self, ability: BeautifulSoup):
        ability_dict = {}
        divider = " "
        ability_key_val = self.get_ability_key_val_pair(ability, divider, 0)
        ability_key = ability_key_val["key"]
        ability_val = ability_key_val["val"]

        ability_dict[ability_key] = {}
        ability_dict[ability_key][ability_key] = ability_val

        subs = self.get_sub_abilities(ability)
        for key in subs:
            ability_dict[ability_key][key] = subs[key]

        return ability_dict
    
    def get_sub_abilities(self, ability: BeautifulSoup):
        divider = " ... "
        sub = ability.nextSibling
        sub_abilities = {}

        while sub != None:
            ability_key_val = self.get_ability_key_val_pair(sub, divider, 1)
            if ability_key_val is None:
                continue
            
            ability_ger = self.translate_sub_ability(ability_key_val['key'])
            ability_ger = unicodedata.normalize("NFKD", ability_ger)
            ability_val = ability_key_val["val"]
  
            sub_abilities[ability_ger] = ability_val

            sub = sub.nextSibling

            if sub == None or not isinstance(sub, bs4.element.NavigableString):
                return sub_abilities 

        return sub_abilities 

    def translate_sub_ability(self, ability: str):
        proficent = False

        if "*" in ability:
            ability = ability.replace("*", "")
            proficent = True
        
        phrases = {
            'Ability Checks': 'Attributcheck',
            'Saving Throws': 'Rettungswurf',
            'Skill': 'Fertigkeit'
        }

        suffix = ""
        export_string = ability
        for phrase, german_phrase in phrases.items():
            if phrase in ability:
                a = ability.replace(phrase, "")
                export_string = self.translate(a.strip())
                suffix = german_phrase
               
        if suffix:
            export_string += " " + suffix

        if proficent:
            export_string += " *"

        return export_string

    def get_ability_key_val_pair(self, ability: BeautifulSoup, divider: str, key_position: int):
        ability_key_val = ability.text.split(divider)

        arr_length = len(ability_key_val)
        if arr_length == 1:
            return
        if arr_length != 2:
            print("Length of \"" + ability.text + "\" array is not 2! Length is: " + str(len(ability_key_val)))
            pp(ability)
            return
        
        ability_key = ""
        ability_val = ""
        if key_position == 0:
            ability_key = self.translate(ability_key_val[0])
            ability_val = ability_key_val[1]
        elif key_position == 1:
            ability_key = self.translate(ability_key_val[1])
            ability_val = ability_key_val[0]
        else:
            print("key_postion is out of bounds. key_position was set to: " + str(key_position))
            return

        pair = {}
        pair["key"] = ability_key.replace("\n", "")
        pair["val"] = ability_val.replace("\n", "")

        return pair
    
    def get_other_stats(self, soup: BeautifulSoup):
        other_stats = {}
        languages = soup.find("strong", text = "Languages:").nextSibling
        other_stats['Sprachen'] = languages.text.lstrip(' ')

        return other_stats

    def find_non_empty_sibling(self, elem):
        if elem == "" or elem == "\n":
            self.find_non_empty_sibling(elem.next_sibling)
        else:
            return elem
