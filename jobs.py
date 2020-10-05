
import helpers
from bs4 import BeautifulSoup
import re

class Job:
    def __init__(self, config):
        self.config = config
        self.url = config["url"]
        self.name = config["name"]

    def run_job(self):
        return


class WHCorpJob(Job):
    def __init__(self, config):
        super().__init__(config)
        self.shiftMatch = "^([a-zA-Z]+) \(([0-9]{1,2}[a-p]m - [0-9]{1,2}[a-p]m)\)$"
        self.weekMatch = "^Week ([0-9]{0,2})$"
        self.mOpen = "OPEN"
        self.aOpen = "OPEN"


    def extract_notes(self, soup):
        notes = soup.find('dl').find_all('dd')
        for note in notes:
            if note.string != None and note.string == "On mornings, appointments are required":
                self.mOpen = "Appointment required"
            if note.string != None and note.string == "On afternoons, appointments are required":
                self.aOpen  = "Appointment required"
         

    def extract_days(self, thead):
        days = []
        tr = thead.tr

        children = tr.find_all(['th', 'td'])
        if len(children) == 0 or children[0].string != 'Day':
            raise Exception('Day', 'Day row unexpected')

        for th in children[1:]:
            days.append(th.string)

        return days


    def extract_shifts(self, days, tbody):
        shifts = []

        tr = tbody.tr

        children = tr.find_all(['th', 'td'])
        if len(children) == 0 or children[0].string != 'Shift ':
            raise Exception('Shift', 'Shift row unexpected')

        j = 0
        for th in children[1:]:
            day = days[j]

            if th.string == None:
                colspan = int(th['colspan'])

                i = 0
                while i < colspan:
                    shifts.append({
                        "Weekday": days[j],
                        "Shift": "Morning",
                        "Opening hours": None
                    })

                    shifts.append({
                        "Weekday": days[j],
                        "Shift": "Afternoon",
                        "Opening hours": None
                    })

                    i += 2   
                    j += 1
                continue

            m = re.match(self.shiftMatch, th.string)
            
            if m == None:
                raise Exception('Shift', 'Shift row wrong format')

            g = m.groups()
            shift = g[0]
            if shift != 'Morning' and shift != 'Afternoon':
                raise Exception('Shift', 'Shift row wrong format')

            shifts.append({
                "Weekday": day,
                "Shift": shift,
                "Opening hours": g[1]
            })

            if shift == 'Afternoon':
                j += 1
        
        return shifts
        

    def extract_weeks(self, shifts, tbody):
        trs = tbody.find_all('tr')

        weeks = {}

        for tr in trs[1:]:
            week = {}

            children = tr.find_all(['th', 'td'])

            if len(children) == 0:
                continue

            m = re.match(self.weekMatch, children[0].string)

            if m == None:
                raise Exception('Week', 'Week row wrong format')

            g = m.groups()
            weeks[f"Week {g[0]}"] = week

            week[self.name] = []

            j = 0
            for td in children[1:]:
                shift = shifts[j].copy()

                daytime = shift['Shift']
                availability = td.string

                if td.string == 'OPEN':
                    if daytime == 'Morning':
                        availability = self.mOpen
                    else:
                        availability = self.aOpen
                
                shift['Availability'] = availability

                week[self.name].append(shift)
                j += 1

        return weeks    

        
    def run_job(self):
        try:
            page_content = helpers.download_page_content(self.url)
            soup = BeautifulSoup(page_content, 'html.parser')

            table = soup.select('table.table')[0]
            thead = table.thead
            tbody = table.tbody

            self.extract_notes(soup)
            days = self.extract_days(thead)
            shifts = self.extract_shifts(days, tbody)
            weeks = self.extract_weeks(shifts, tbody)

        except Exception as err:
            raise(err)

        return weeks


class AmericanStorageJob(Job):
    def __init__(self, config):
        super().__init__(config)
        self.weekMatch = "^WEEK ([0-9]{0,2})$"
        self.hoursMatch = "^Opening hours every day ([0-9]{1,2}[a-p]m) .* ([0-9]{1,2}[a-p]m) \/ ([0-9]{1,2}[a-p]m) .* ([0-9]{1,2}[a-p]m)$"
        self.dayMatch = "^([a-zA-Z]+) ([a-zA-Z]+)$"
        self.availabilityMapper = {
            "free": "OPEN",
            "closed": "CLOSE"
        }

    
    def extract_hours(self, weekItem):
        hours = weekItem.select('.opening-hour')[0].string

        m = re.match(self.hoursMatch, hours)

        if m == None:
            raise Exception('Hours', 'Wrong hours format')

        g = m.groups()

        hours = {"Morning": f"{g[0]} - {g[1]}", "Afternoon": f"{g[2]} - {g[3]}"}

        return hours


    def extract_shift(self,hours, weekItem):
        lis = weekItem.find_all('li')

        shifts = []

        for li in lis:
            daytime = li.contents[0].string
            availability = li.contents[1].string

            m = re.match(self.dayMatch, daytime)

            if m == None:
                continue

            g = m.groups()

            if availability != None:
                availability = availability.split(': ')[1]
                if availability in self.availabilityMapper:
                    availability = self.availabilityMapper[availability]
                else:
                    availability = availability.capitalize()

            shifts.append({
                "Weekday": g[0],
                "Shift": g[1].capitalize(),
                "Openin hours": hours[g[1].capitalize()],
                "Availability": availability
            })

        return shifts


    def extract_weeks(self, soup):
        weekItems = soup.select('div.week')

        weeks = {}
        for weekItem in weekItems:
            weekName = weekItem.find('h2').string

            m = re.match(self.weekMatch, weekName)
            if m == None:
                continue

            g = m.groups()

            hours = self.extract_hours(weekItem)
            shifts = self.extract_shift(hours, weekItem)
            
            weeks[f'Week {g[0]}'] = {
                self.name: shifts
            }
        
        return weeks

    def run_job(self):
        try:
            page_content = helpers.download_page_content(self.url)
            soup = BeautifulSoup(page_content, 'html.parser')            
            weeks = self.extract_weeks(soup)

        except Exception as err:
            raise(err)

        return weeks
