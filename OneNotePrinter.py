from prettytable import PrettyTable
from pprint import pp

class OneNotePrinter:
    base_url = 'https://graph.microsoft.com/v1.0/me/onenote/'
    notebooks_url_str = "notebooks/"
    sections_url_str = "/sections/"
    
    def print_notebooks(self, onenote):
        req_url = self.base_url + self.notebooks_url_str

        notebooks = onenote.get(req_url)
        data = notebooks.json()

        self.print_data(data, "Notebooks:")

    def print_section(self, section_id, onenote):
        req_url = self.base_url + "sections/" + section_id

        notebooks = onenote.get(req_url)
        data = notebooks.json()

        self.print_data(data, "Section:")
   
    def print_sections_for_notebook(self, notebook_id, onenote):
        req_url = self.base_url + self.notebooks_url_str + notebook_id + self.sections_url_str
        sections = onenote.get(req_url).json()

        self.print_data(sections, "Sections for notebook:")
   
    def print_sections_for_section_group(self, section_group_id, onenote):
        req_url = self.base_url + "sectionGroups/" + section_group_id + self.sections_url_str
        notebooks = onenote.get(req_url).json()
        data = notebooks

        self.print_data(data, "Sections for group")

    def print_pages_for_notebook(self, notebook_id, onenote):
        req_url = self.base_url + self.notebooks_url_str + notebook_id + "?$expand=children" #"/pages/"
        notebooks = onenote.get(req_url)
        data = notebooks.json()
        pp(data)
 
        table = PrettyTable()
        table.field_names = ['Name', 'ID', 'Parent', 'Parent ID']
        for val in data['value']:
            parent_id = val['parentSection']['id']
            parent_name = val['parentSection']['displayName']
            table.add_row([val['title'], val['id'], parent_name, parent_id])

        print('Pages:')
        print(table)

    def print_section_groups_for_notebook(self, notebook_id, onenote):
        req_url = self.base_url + self.notebooks_url_str + notebook_id + '/sectionGroups'
        notebooks = onenote.get(req_url)
        data = notebooks.json()

        self.print_data(data, "Sections")

    def print_sub_pages(self, notebook_id, onenote):
        req_url = self.base_url + self.notebooks_url_str + notebook_id + '?$expand=sections,sectionGroups($expand=sections)'
        notebooks = onenote.get(req_url)
        data = notebooks.json()

        print(data['displayName'] + ':')
        table = PrettyTable()
        table.field_names = ['Name', 'ID', 'Section Groups']
        for val in data['sections']:
            table.add_row([val['displayName'], val['id'], ''])
        
        for val in data['sectionGroups']:
            table.add_row([val['displayName'], val['id'], 'X'])
            for sec in val['sections']:
                table.add_row([sec['displayName'], sec['id'], ''])
        
        print('Sections and section groups:')
        print(table)

    def print_pages_in_notebook(self, notebook_id, onenote):
        """
        Prints all pages in a given notebook.

        notebook_id: The OneNote notebook id of which the pages are to be printed out.
        onenote: The OneNote api session.
        """
        req_url = self.base_url + self.notebooks_url_str + notebook_id + self.sections_url_str
        data = onenote.get(req_url).json()
        sections = data['value']

        # Get sections in section groups
        section_groups_req_url = self.base_url + self.notebooks_url_str + notebook_id + '/sectionGroups'
        sections_in_section_groups_data = onenote.get(section_groups_req_url).json()

        for val in sections_in_section_groups_data['value']:
            sections_data = onenote.get(val['sectionsUrl']).json()
            sections.extend(sections_data['value'])

        table = PrettyTable()
        table.field_names = ['Name', 'ID', 'Parent Section']
        for val in data['value']:
            pages = onenote.get(val['pagesUrl']).json()
            for page in pages['value']:
                table.add_row([page['title'], page['id'], page['parentSection']['displayName']])

        print(table)

    def print_data(self, data, data_name):
        """
        Prints the JSON-data that was recieved by a GET call.
        
        data: The JSON response.
        data_name: The string which describes the data that is printed (eg. 'notebooks' or 'sections')
        """
        assert(type(data_name) is str)

        table = PrettyTable()
        table.field_names = ['Name', 'ID']

        if "value" not in data:
            if "displayName" in data:
                table.add_row([data['displayName'], data['id']])
            else:
                print("No values in JSON data found!")
                return
        else:
            for val in data['value']:
                table.add_row([val['displayName'], val['id']])

        print((str(data_name)))
        print(table)

