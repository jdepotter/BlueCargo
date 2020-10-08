class Job:
    def __init__(self, config):
        self.config = config
        self.url = config["url"]
        self.name = config["name"]

    def run_job(self):
        return