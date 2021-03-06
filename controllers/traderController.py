from controllers.executeController import Executor
from controllers.dataLoaderController import DataLoader
from controllers.mt5Controller import Mt5Controller
from models import commandModel, timeModel, fileModel
from selfUtils import tools

from utils import inputModel

class Trader:
    def __init__(self, deposit_currency, timezone, local_data_path, docs_path):

        # init
        self.mt5Controller = Mt5Controller(timezone)
        self.executor = Executor()
        self.dataLoader = DataLoader(self.mt5Controller, local_data_path, deposit_currency)
        self.dataLoader.prepare()

        # prepare
        self.docs_path = docs_path
        self.candidates = {}

    def end(self):
        self.mt5Controller.disconnect_server()

    def user_input(self):
        input = inputModel.enter()
        input = commandModel.check(input, self)
        return input

    def add_candidates(self, strategyClass, params):
        # build the strategy file
        time_str = timeModel.get_current_time_string(with_seconds=True)
        candidate_id = "{}_{}".format(time_str, strategyClass.__name__)
        text = "Strategy: {}\n{}".format(strategyClass.__name__, tools.dic_into_text(params))
        fileModel.create_dir(self.docs_path, candidate_id, text)
        # create strategy class and add into Trader
        self.candidates[candidate_id] = strategyClass(self.dataLoader, candidate_id, **params)
        print("{} added".format(candidate_id))

