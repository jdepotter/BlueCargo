
import helpers
from bs4 import BeautifulSoup
import re
from jobs import Job

class AmericanStorageJob(Job):
    def __init__(self, config):
        super().__init__(config)


    class Validator:
        def __init__(self):
            self.weekMatch = "^WEEK ([0-9]{0,2})$"
            self.hoursMatch = "^Opening hours every day ([0-9]{1,2}[ap]{1}m) .* ([0-9]{1,2}[ap]{1}m) \/ ([0-9]{1,2}[ap]{1}m) .* ([0-9]{1,2}[ap]{1}m)$"
            self.dayMatch = "^([a-zA-Z]+) (morning|afternoon)$"


        def evaluate_match(self, val, match):
            if val == None:
                return None
                
            m = re.match(match, val.strip())

            if m == None:
                return None

            return m.groups()


        def validate_week_match(self, weekVal):
            g = self.evaluate_match(weekVal, self.weekMatch)
            if g == None:
                return None

            return {"week": g[0]}

        
        def validate_hours_match(self, hoursVal):            
            if hoursVal == None:
                return {"morning": None, "afternoon": None}

            g = self.evaluate_match(hoursVal, self.hoursMatch)

            return {"morning": f"{g[0]} - {g[1]}", "afternoon": f"{g[2]} - {g[3]}"}


        def validate_day_match(self, dayVal):
            g = self.evaluate_match(dayVal, self.dayMatch)
            if g == None:
                return None

            return {"day": g[0], "shift": g[1].capitalize() }

            
    class Mapper:
        def __init__(self):
            self.availabilityMapper = {
                "Free": "OPEN",
                "Closed": "CLOSE"
            }

        def mapAvailability(self, availability):
            if availability == None:
                return None
                
            if availability not in self.availabilityMapper:
                return availability

            return self.availabilityMapper[availability]


    def __init__(self, config):
        super().__init__(config)
        self._v = self.Validator()
        self._m = self.Mapper()
        self.openingHourSel = '.opening-hour'
        self.shiftSelf = 'li'
        self.weekSel = 'div.week'
        self.weekHeaderSel = 'h2'

    
    def extract_hours(self, weekItem):
        hours = weekItem.select(self.openingHourSel)[0].string

        vHours = self._v.validate_hours_match(hours)

        if vHours == None:
            raise Exception('Hours', 'Wrong hours format')

        return {"Morning": vHours["morning"], "Afternoon": vHours["afternoon"]}


    def extract_shift(self,hours, weekItem):
        lis = weekItem.find_all(self.shiftSelf)

        shifts = []

        for li in lis:
            day = li.contents[0].string
            availability = li.contents[1].string

            vDay = self._v.validate_day_match(day)

            if vDay == None:
                continue

            availability = self._m.mapAvailability(availability)

            shifts.append({
                "Weekday": vDay["day"],
                "Shift": vDay["shift"],
                "Openin hours": hours[vDay["shift"]],
                "Availability": availability
            })

        return shifts


    def extract_weeks(self, soup):
        weekItems = soup.select(self.weekSel)

        weeks = {}
        for weekItem in weekItems:
            week = weekItem.find(self.weekHeaderSel ).string

            vWeek = self._v.validate_week_match(week)

            if vWeek == None:
                continue

            hours = self.extract_hours(weekItem)
            shifts = self.extract_shift(hours, weekItem)
            
            weeks[f'Week {vWeek["week"]}'] = {
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
