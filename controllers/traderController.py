from models import commandModel, inputModel, mt5Model

class Trader:
    def __init__(self, executeController):
        self.executeController = executeController

    def run(self):
        # connect mt5
        mt5Model.connect_server()
        input = inputModel.enter()
        input = commandModel.check(input)
        return input

    def end(self):
        mt5Model.disconnect_server()