
import helpers
from bs4 import BeautifulSoup
import re
from jobs import Job

class AmericanStorageJob(Job):
    def __init__(self, config):
        super().__init__(config)


    class Validator:
        self.weekMatch = "^WEEK ([0-9]{0,2})$"
        self.hoursMatch = "^Opening hours every day ([0-9]{1,2}[ap]{1}m) .* ([0-9]{1,2}[ap]{1}m) \/ ([0-9]{1,2}[ap]{1}m) .* ([0-9]{1,2}[ap]{1}m)$"
        self.dayMatch = "^([a-zA-Z]+) (morning|afternoon)$"

        def validate_week_match(self, weekVal):
            if weekVal == None:
                return None
                
            m = re.match(self.weekMatch, weekVal.strip())

            if m == None:
                return None

            g = m.groups()
            return {"week": g[0]}

        
        def validate_hours_match(self, hoursVal):
            if hoursVal == None:
                return {"morning": None, "afternoon": None}

            m = re.match(self.hoursVal, hoursVal.strip())

            if m == None:
                return None

            g = m.groups()
            return {"morning": f"{g[0]} - {g[1]}", "afternoon": f"{g[2]} - {g[3]}"}


        def validate_day_match()

            

        class Mpper:
            self.availabilityMapper = {
                "free": "OPEN",
                "closed": "CLOSE"
            }


    def __init__(self):

    
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
