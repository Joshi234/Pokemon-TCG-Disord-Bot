users = {}

dailyMissions = Mission()


class Mission:
    def __init__(self, dataSource, amount):
        self.dataSource = dataSource
        self.amount = amount