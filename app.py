from requests_oauthlib.oauth2_session import OAuth2Session
from OAuth2Connector import OAuth2Connector
from CharacterCreator import CharacterCreator
import argparse
from pprint import pp
from prettytable import PrettyTable
from bs4 import BeautifulSoup
import configparser

class App:
    auth_connector =  OAuth2Connector()
    args = None
    verbose = False
    character_creator = CharacterCreator()

    def main(self):
        parser = argparse.ArgumentParser(description='Create dnd nps easily.')
        parser.add_argument('-ct',"--createtoken", action="store_true")
        parser.add_argument('-cc',"--createcharacterpage", action="store_true")
        parser.add_argument('-vb',"--verbose", action="store_true")
        self.args, _ = parser.parse_known_args()
        
        self.verbose = self.args.verbose

        if self.args.createtoken == True:
            if self.verbose:
                print("A new OneNote API token will be created..")
            self.auth_connector.create_token()
        else:
            if self.verbose:
                print("Loading token..")
            self.auth_connector.token_is_expired()
 
        if self.args.createcharacterpage == True:
            if self.verbose:
                print("Creating character..")
            onenote = self.auth_connector.get_onenote_session()

            config = configparser.ConfigParser()
            config.read('configs/configs.ini')

            self.create_character_page(config['onenote']['section_id'], onenote)

    def create_character_page(self, section_id, onenote: OAuth2Session):
        url = 'https://graph.microsoft.com/v1.0/me/onenote/sections/'+ section_id +'/pages'
        character_creator = CharacterCreator()
   
        character_name = input("What is your characters name? (Leave empty for random name) \n")
        
        print("Creating Character..")

        character = character_creator.create(character_name=character_name)

        if self.verbose:
            print("Character created..")
            pp(character)
        
        data = self.character_html_builder(character)
        if self.verbose:
            print("Created HTML:")
            pp(data)

        response = onenote.post(url=url, data=data, json={'title': 'presentation'}, headers={"Content-type":"text/html"})
        if self.verbose:
            print("Posted character to onenote")
            pp(response.json())
        
        code = response.status_code
        if code == 201:
            print("Success! Your character has been created! Refresh your notebook and enjoy!")
        else:
            print("Response Code: " + code)
            pp(response.json())

    
    def character_html_builder(self, character):
        # Load character template page and use it to create a BeautifulSoup object.
        with open('characterpage.html', 'r') as f:
            contents = f.read()

        website_colors = {
            'highlight': '#73594A',
            'background': '#F2E0D0',
            'normal': '#4f4430'
        }

        soup = BeautifulSoup(contents, 'html5lib')

        # Insert character data into page.
        soup.find('title').string = character['main_stats']['Name']

        main_table = self.create_main_table(character['main_stats'], website_colors)
        soup.find(id="main-table").insert(0, main_table)

        combat_table = self.create_combat_table(character['combat'], website_colors)
        soup.find(id="combat-table").insert(0, combat_table)

        ability_table = self.create_ability_table(character['ability'], website_colors)
        soup.find(id="ability-table").insert(0, ability_table)

        return str(soup).encode(encoding='UTF-8', errors='strict')

    def create_main_table(self, main_stats, color):
        """
        Takes the main_stats dictionary and creates a fromatted BeautifulSoup object.

        Returns the formatted BeautifulSoup object.

        main_stats: Dictionary with all ability values.
        """
        table = PrettyTable()
        for key in main_stats.keys():     
            table.add_column(main_stats[key], [key])
 
        # Create BeautifulSoup object with html character table.
        table_soup = BeautifulSoup(table.get_html_string(), 'html5lib')
        table_soup.find('table')['style'] = "border: 1em solid black; margin-right: 200px; table-layout: fixed; width: 800px; background-color: " + color['background']

        for th in table_soup.findAll('th'):
            th['style'] = "text-align:center; white-space: nowrap; overflow: hidden; color:" + color['highlight']

        for td in table_soup.findAll('td'):
            td['style'] = "text-align:center; color: " + color['normal'] +"; white-space: nowrap; overflow: hidden;"
        
        return table_soup

    def create_combat_table(self, combat_stats, color):
        """
        Takes the combat_stats dictionary and creates a fromatted BeautifulSoup object.

        Returns the formatted BeautifulSoup object.

        combat_stats: Dictionary with all ability values.
        """
        table = PrettyTable(["1", "2"])

        for key in combat_stats:
            table.add_row([key, combat_stats[key]])
        
        # Create BeautifulSoup object with html character table.
        table_soup = BeautifulSoup(table.get_html_string(), 'html5lib')
        table_soup.find('table')['style'] = "width: 400px; background-color: " + color['background']
        table_soup.find('th').parent.decompose()

        first_column = True
        for td in table_soup.findAll('td'):
            if first_column == True:
                td['style'] = "width: 150px;"
                first_column = False
            else:
                td['style'] = "width: 250px;"
                break
        for tr in table_soup.findAll('tr'):
            tr['style'] = "color: " + color['normal']
    
        return table_soup

    def create_ability_table(self, ability_stats, color):
        """
        Takes the ability_stats dictionary and creates a fromatted BeautifulSoup object.

        Returns the formatted BeautifulSoup object.
        ability_stats: Dictionary with all ability values.
        """
        table = PrettyTable(["1", "2"])

        for ability_key in ability_stats:
            for key in ability_stats[ability_key]:
                table.add_row([key, ability_stats[ability_key][key]])
        
        # Create BeautifulSoup object with html character table.
        table_soup = BeautifulSoup(table.get_html_string(), 'html5lib')
        table_soup.find('table')['style'] = "border: 1em solid black; width: 300px; background-color: " + color['background']
        
        for tr in table_soup.findAll("tr"):
            if tr.find('th') != None:
                tr.decompose()
                continue

            td = tr.find('td')
            if td != None and td.text in ability_stats.keys():
                tr['style'] = "font-weight: bold; text-decoration: underline; color: " + color['highlight']
            else:
                tr['style'] = "color: " + color['normal']

        first_column = True
        for td in table_soup.findAll('td'):
            if first_column == True:
                td['style'] = "width: 250px; color: " + color['highlight']
                first_column = False
            else:
                td['style'] = "width: 50px; color: " + color['highlight']
                break

        return table_soup

if __name__ == "__main__":
    app = App()
    app.main()