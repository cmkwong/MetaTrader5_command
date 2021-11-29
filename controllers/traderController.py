from models import commandModel, inputModel, mt5Model, timeModel, fileModel
from utils import tools

class Trader:
    def __init__(self, executor, dataLoader, docs_path):
        self.executor = executor
        self.dataLoader = dataLoader
        self.docs_path = docs_path
        self.strategies = {}

        # connect mt5
        mt5Model.connect_server()
        self.dataLoader.prepare()

    def end(self):
        mt5Model.disconnect_server()

    def user_input(self):
        input = inputModel.enter()
        input = commandModel.check(input, self)
        return input

    def add_strategy(self, strategyClass, params):
        # build the strategy file
        time_str = timeModel.get_current_time_string()
        text = "Strategy: {}\n{}".format(strategyClass.__name__, tools.dic_into_text(params))
        fileModel.create_dir(self.docs_path, time_str, text)
        # add the strategy
        self.strategies[time_str + strategyClass.__name__] = strategyClass(self.dataLoader, **params)

