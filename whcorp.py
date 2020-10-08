import helpers
from bs4 import BeautifulSoup
import re
from jobs import Job

class WHCorpJob(Job):
    class Validator:
        def __init__(self):
            self.shiftMatch = "^(Morning|Afternoon) \(([0-9]{1,2}[ap]{1}m) - ([0-9]{1,2}[ap]{1}m)\)$"
            self.weekMatch = "^Week ([0-9]{0,2})$"
            self.appointmentNoteMatch = "^On (morning|afternoon)s, appointments are( not)* required$"
            self.appoitmentNoteValues = ['morning', 'afternoon']
            self.statusValues = ['OPEN', 'CLOSED']
            self.shiftLabel = 'Shift'
            self.dayLabel = 'Day'
            self.dayValues = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


        def validate_shift_match(self, shiftVal):
            if shiftVal == None:
                return {"shift": None}

            m = re.match(self.shiftMatch, shiftVal.strip())

            if m == None:
                return None

            g = m.groups()
            return {"shift": g[0], "hours": f"{g[1]} - {g[2]}"}


        def validate_week_match(self, weekVal):
            if weekVal == None:
                return None

            m = re.match(self.weekMatch, weekVal.strip())

            if m == None:
                return None

            g = m.groups()
            return {"week": g[0]}


        def validate_status_value(self, statusVal):
            if statusVal == None:
                return None

            statusValTrim = statusVal.strip()
            return statusValTrim if statusValTrim in self.statusValues else None


        def validate_shift_label(self, val):
            return val.strip() == self.shiftLabel


        def validate_day_label(self, val):
            return val.strip() == self.dayLabel


        def validate_day_value(self, val):
            valTrim = val.strip()
            return valTrim if valTrim in self.dayValues else None


        def validate_note_appointment(self, note):
            if note == None or note.strip() == None: return None

            m = re.match(self.appointmentNoteMatch, note.strip())

            if m == None:
                return None

            g = m.groups()

            return {"shift": g[0].capitalize(), "appRequired": True} if g[1] == None else {"shift": g[0].capitalize(), "appRequired": False}


    def __init__(self, config):
        super().__init__(config)
        self._v = self.Validator()
        self.noteSel = 'dl'
        self.noteSubSel = 'dd'
        self.shiftTableSel = 'table.table'
        self.dayHeaderSel = 'th'
        self.shiftHeaderSel = 'th'
        self.weekValueSel = ['th', 'td']


    def extract_appointment_notes(self, soup):
        notes = soup.find(self.noteSel).find_all(self.noteSubSel)

        appRequireds = {}
        for note in notes:
            vNote = self._v.validate_note_appointment(note.string)

            if vNote != None:
                appRequireds[vNote["shift"]] = vNote["appRequired"]

        return appRequireds
         

    def extract_days(self, thead):
        days = []
        ths = thead.tr.find_all(self.dayHeaderSel)

        if len(ths) == 0 or self._v.validate_day_label(ths[0].string) == False:
            raise Exception('Day', 'Missing days row')

        for th in ths[1:]:
            cols = int(th.attrs['colspan']) if 'colspan' in th.attrs else 1
            for i in range(cols):
                days.append(self._v.validate_day_value(th.string))

        return days


    def extract_shifts(self, days, tbody):
        shifts = []

        tds = tbody.tr.find_all(self.shiftHeaderSel)

        if len(tds) == 0 or self._v.validate_shift_label(tds[0].string) == False:
            raise Exception('Shift', 'Missing shifts row')

        shiftsA = []
        for td in tds[1:]:
            cols = int(td.attrs['colspan']) if 'colspan' in td.attrs else 1

            for i in range(cols):
                shiftsA.append(td.string)

        if len(shiftsA) != len(days):
            raise Exception('Shift', 'Days and shifts not aligned')

        for i in range(len(shiftsA)):
            day = days[i]
            shift = shiftsA[i]

            if day == None:
                continue

            vShift = self._v.validate_shift_match(shift)

            if vShift == None:
                raise Exception('Shift', 'Wrong format')

            if vShift['shift'] == None:
                vShift['shift'] = 'Morning' if i%2 == 0 else 'Afternoon'
                vShift['hours'] = None

            shifts.append({
                "Weekday": day,
                "Shift": vShift['shift'],
                "Opening hours": vShift['hours']
            })

        return shifts
        

    def extract_weeks(self, shifts, appNotes, tbody):
        trs = tbody.find_all('tr')

        weeks = {}
        for tr in trs[1:]:
            tds = tr.find_all(self.weekValueSel)

            if len(tds) == 0:
                continue

            weekV = self._v.validate_week_match(tds[0].string)

            if weekV == None:
                continue

            statusA = []
            for td in tds[1:]:
                cols = int(td.attrs['colspan']) if 'colspan' in td.attrs else 1

                for i in range(cols):
                    statusA.append(td.string)

            if len(statusA) != len(shifts):
                continue

            week = {self.name: []}
            weeks[f"Week {weekV['week']}"] = week

            for i in range(len(statusA)):
                shift = shifts[i].copy()
                daytime = shift['Shift']

                status = self._v.validate_status_value(statusA[i])

                if status == 'OPEN' and daytime in appNotes and appNotes[daytime]:
                    status = 'Appointment required'

                shift['Availability'] = status

                week[self.name].append(shift)

        return weeks    

        
    def run_job(self):
        try:
            page_content = helpers.download_page_content(self.url)
            soup = BeautifulSoup(page_content, 'html.parser')

            table = soup.select(self.shiftTableSel)[0]
            thead = table.thead
            tbody = table.tbody

            appNotes = self.extract_appointment_notes(soup)
            days = self.extract_days(thead)
            shifts = self.extract_shifts(days, tbody)
            weeks = self.extract_weeks(shifts, appNotes, tbody)

        except Exception as err:
            raise(err)

        return weeks

