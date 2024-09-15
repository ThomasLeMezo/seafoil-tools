import requests
from bs4 import BeautifulSoup
import re
import json
import datetime

from device.seafoil_connexion import SeafoilConnexion
from device.seafoil_log import SeafoilLog


class SeafoilBaseDeVitesse():
    def __init__(self):
        self.url_day_session = 'https://basedevitesse.com/sessionsjour/'
        self.url_user_session = 'https://basedevitesse.com/pageSession/'

        self.soup = None
        self.session_day = []
        self.session_day_header = []
        self.base_name = None

        self.sc = SeafoilConnexion()
        self.sl = SeafoilLog()

    def download_day_session(self, session_date, id_base=1):
        # convert datime to string "2024-03-23" format
        date_str = session_date.strftime("%Y-%m-%d")

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
        response = requests.get(self.session_day[id]['session_url'])
        html = response.text

        # Parse the HTML
        soup = BeautifulSoup(html, 'html.parser')

        # Find link of text "GPX complet (sans filtrage)"
        link = soup.find('a', text=re.compile(r'GPX complet \(sans filtrage\)'))

        if link:
            gpx_url = link.get('href')
            print(gpx_url)
            return gpx_url

    def download_list_user_session(self, user_ids):
        sucess_list = []
        for user_id in user_ids:
            user = self.session_day[user_id]
            url = self.get_url_user_session(user_id)
            success, db_id = self.sc.download_gpx_file(url)

            if success: # Add additional information to the database
                # Process the log
                self.sl.process_log(db_id)

                ## Rider name
                # split the 'rider' column into first name and last name, split only the first space
                first_name, last_name = user['Rider'].split(' ', 1)
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
                sport = self.sc.db.find_water_sport_type(user['Support'])
                # If the sport is not found, add the sport to the database
                if sport is None:
                    sport = self.sc.db.add_water_sport_type(user['Support'])
                # Add the sport to the log
                self.sc.db.update_log_sport_type(db_id, sport['id'])

                sucess_list.append(db_id)
        return sucess_list

# Test the class
if __name__ == '__main__':
    bdv = SeafoilBaseDeVitesse()
    date = datetime.datetime(2024, 3, 23)
    bdv.download_day_session(date)
    bdv.get_url_user_session(0)
