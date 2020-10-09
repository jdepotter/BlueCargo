import json
from whcorp import WHCorpJob
from americanstorage import AmericanStorageJob
import pprint

def load_config():
    config = {}
    with open('./config.json') as c:
        config = json.load(c)

    return config


def job_factory(name, config):
    if name == 'WHCorp':
        return WHCorpJob(config)
    elif name == "AmericanStorage":
        return AmericanStorageJob(config)

    raise Exception('Error', f'No job for {name}')


def merge_schedules(schedule1, schedule2):
    for week in schedule2:
        if week not in schedule1:
            schedule1[week] = {}

        for name in schedule2[week]:
            schedule1[week][name] = schedule2[week][name]

def run_jobs():
    config = load_config()

    schedule = {}
    for site in config["sites"]:
        job = job_factory(site['name'], site)

        try:
            siteSchedule = job.run_job()
            merge_schedules(schedule, siteSchedule)
        except Exception as err:
            print(repr(err))
        
    pprint.pprint(schedule)


run_jobs()