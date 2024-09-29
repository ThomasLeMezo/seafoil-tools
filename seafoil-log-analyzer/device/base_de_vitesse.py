from enum import Enum

import requests
from bs4 import BeautifulSoup
import re
import json
import datetime

from .seafoil_connexion import SeafoilConnexion
from .seafoil_log import SeafoilLog


class SeafoilBaseDeVitesse():

    class BdvInfoType(Enum):
        DAY_SESSION = 1
        USER_SESSION = 2

    def __init__(self):
        self.url_default = "https://basedevitesse.com/"
        self.url_day_session = self.url_default + 'sessionsjour/'
        self.url_user_session = self.url_default + 'pageSession/'
        self.url_user_list = self.url_default + 'classementnational/'
        self.url_user_list_session = self.url_default + 'sessionsUtilisateur/?IDuser='

        self.soup = None
        self.session_day = []
        self.session_day_header = []
        self.base_current_id = None
        self.base_list = []

        self.rider_current_idx = None
        self.rider_list = []
        self.rider_list_ui = []

        self.rider_session_list = []
        self.session_user_header = []

        self.sc = SeafoilConnexion()
        self.sl = SeafoilLog()

        # Enum with list type
        self.info_type = self.BdvInfoType.DAY_SESSION

        self.update()

    def update(self):
        self.base_list = self.sl.db.get_basevitesse_all()
        self.rider_list = self.sl.db.get_basevitesse_rider_all()
        self.rider_list_ui = [f"{rider['first_name']} {rider['last_name']}" for rider in self.rider_list]

    def download_day_session(self, session_date):
        # convert datime to string "2024-03-23" format
        date_str = session_date.strftime("%Y-%m-%d")

        if self.base_current_id is None:
            return None

        id_base = self.base_list[self.base_current_id]['web_id']

        params = {
            'date': date_str,
            'IDbase': id_base
        }

        response = requests.get(self.url_day_session, params=params)
        html = response.text

        # Parse the HTML
        soup = BeautifulSoup(html, 'html.parser')

        # Extract base name
        self.base_name = ""
        try:
            self.base_name = soup.find('h5').get_text()
        except:
            print("No data found")
            return None

        # Update db
        self.sl.db.update_base_name(id_base, self.base_name)

        # Extract the table
        table = soup.find('table', id="table")

        # Extract rows from the table
        rows = table.find_all('tr')

        # First row is the header
        header = rows[0]
        header_cells = header.find_all(['th'])
        self.session_day_header = [cell.get_text() for cell in header_cells]

        self.session_day = []

        for row in rows[1:]:
            # Extract cells in each row

            cells = row.find_all(['td', 'th'])  # Using both 'td' and 'th' to include headers
            # extract cell and remove '\n' and padding spaces
            cell_data = [cell.get_text().strip() for cell in cells]

            # Use the header_data to create a dict
            user_session = dict(zip(self.session_day_header, cell_data))

            # Extract links from each cells and add to cell_data
            links = row.find_all('a')
            if len(links) == 2:
                user_session['user_url'] = links[0].get('href')
                user_session['session_url'] = links[1].get('href')

            # Add the user session to the list
            self.session_day.append(user_session)

        return self.session_day

    def get_url_user_session(self, id):
        url_session = ''
        if self.info_type == self.BdvInfoType.DAY_SESSION:
            url_session = self.session_day[id]['session_url']
        elif self.info_type == self.BdvInfoType.USER_SESSION:
            url_session = self.rider_session_list[id]['session_url']

        response = requests.get(url_session)
        html = response.text

        # Parse the HTML
        soup = BeautifulSoup(html, 'html.parser')

        # Find link of text "GPX complet (sans filtrage)"
        link = soup.find('a', text=re.compile(r'GPX complet \(sans filtrage\)'))

        if link:
            gpx_url = link.get('href')
            print(gpx_url)
            return gpx_url

    def download_list_user_session(self, idx_list):
        sucess_list = []
        for idx in idx_list:
            url = self.get_url_user_session(idx)
            success, db_id = self.sc.download_gpx_file(url)

            if success: # Add additional information to the database
                # Process the log
                self.sl.process_log(db_id)

                ## Rider name
                # split the 'rider' column into first name and last name, split only the first space
                if self.info_type == self.BdvInfoType.DAY_SESSION:
                    user = self.session_day[idx]
                    first_name, last_name = user['Rider'].split(' ', 1)
                elif self.info_type == self.BdvInfoType.USER_SESSION:
                    first_name = self.rider_list[self.rider_current_idx]['first_name']
                    last_name = self.rider_list[self.rider_current_idx]['last_name']

                # Try to find the rider in the database
                rider = self.sc.db.find_rider(first_name, last_name)
                # If the rider is not found, add the rider to the database
                if rider is None:
                    rider_id = self.sc.db.add_rider(first_name, last_name)
                else:
                    rider_id = rider['id']
                # Add the rider to the log
                self.sc.db.update_log_rider(db_id, rider_id)

                ## Water Sport type
                # Find the water sport type in the database
                sport = None
                if self.info_type == self.BdvInfoType.DAY_SESSION:
                    sport = self.sc.db.find_water_sport_type(user['Support'])
                elif self.info_type == self.BdvInfoType.USER_SESSION:
                    sport = self.sc.db.find_water_sport_type(self.rider_session_list[idx]['Support'])
                # If the sport is not found, add the sport to the database
                if sport is None:
                    sport = self.sc.db.add_water_sport_type(user['Support'])
                # Add the sport to the log
                self.sc.db.update_log_sport_type(db_id, sport['id'])

                sucess_list.append(db_id)
        return sucess_list

    def download_list_base(self):
        try:
            response = requests.get(self.url_default)
            html = response.text

            # Parse the HTML
            soup = BeautifulSoup(html, 'html.parser')

            # Find all links that contains "base="
            links = soup.find_all('a', href=re.compile(r'\?base='))

            # For all links extract the number after "base=" and the text
            for link in links:
                base_id = int(link.get('href').split('=')[1])
                if base_id == 0:
                    continue
                base_name = link.get_text()
                # remove the parenthesis and its content
                base_name = re.sub(r'\(.*\)', '', base_name).strip()
                self.sl.db.update_base_name(base_id, base_name)
            self.update()
            return True

        except Exception as e:
            print("Error: ", e)
            return False

    def download_rider_list(self):
        try:
            response = requests.get(self.url_user_list)
            html = response.text

            # Parse the HTML
            soup = BeautifulSoup(html, 'html.parser')

            # Extract the table
            table = soup.find('table', id="table")

            # Extract rows from the table
            rows = table.find_all('tr')

            # First row is the header
            header = rows[0]
            header_cells = header.find_all(['th'])

            for row in rows[1:]:
                # Extract cells in each row

                cells = row.find_all(['td', 'th'])  # Using both 'td' and 'th' to include headers
                # extract cell and remove '\n' and padding spaces
                cell_data = [cell.get_text().strip() for cell in cells]

                first_name, last_name = cell_data[1].split(' ', 1)

                # Extract links from each cells and add to cell_data
                user_session = row.find_all('a')[0].get('href')

                # Extract the number after "IDuser="
                user_id = int(user_session.split('=')[1])

                # Add the user to the database
                self.sl.db.insert_basevitesse_rider(first_name, last_name, user_id)

            return True

        except Exception as e:
            print("Error: ", e)
            return False

    def download_rider_session_list(self):
        try:
            rider_id = self.rider_list[self.rider_current_idx]['web_id']
            response = requests.get(self.url_user_list_session + str(rider_id))
            html = response.text

            # Parse the HTML
            soup = BeautifulSoup(html, 'html.parser')

            # Extract the table
            table = soup.find('table', id="table")

            # Extract rows from the table
            rows = table.find_all('tr')

            # First row is the header
            header = rows[0]
            header_cells = header.find_all(['th'])
            self.session_user_header = [cell.get_text() for cell in header_cells]

            self.rider_session_list.clear()
            for row in rows[1:]:
                # Extract cells in each row
                cells = row.find_all(['td', 'th'])  # Using both 'td' and 'th' to include headers
                # extract cell and remove '\n' and padding spaces
                cell_data = [cell.get_text().strip() for cell in cells]

                # Use the header_data to create a dict
                user_session = dict(zip(self.session_user_header, cell_data))

                # Extract links from each cells and add to cell_data
                links = row.find_all('a')
                if len(links) > 0:
                    user_session['session_url'] = links[0].get('href')

                # Add the user session to the list
                self.rider_session_list.append(user_session)
            return self.rider_session_list

        except Exception as e:
            print("Error: ", e)
            return None


# Test the class
if __name__ == '__main__':
    bdv = SeafoilBaseDeVitesse()
    date = datetime.datetime(2024, 3, 23)
    bdv.download_day_session(date)
    bdv.get_url_user_session(0)
