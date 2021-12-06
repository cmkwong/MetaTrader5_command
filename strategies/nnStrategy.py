import os

from models import fileModel
import config

class NNStrategy:
    def __init__(self, strategy_id):
        self.strategy_id = strategy_id
        self.setup_NN_paths()

    def setup_NN_paths(self):
        strategy_record_path = os.path.join(config.RECORDS_PATH, self.strategy_id)
        self.buffer_save_path = fileModel.create_dir(strategy_record_path, 'buffer')
        self.runs_save_path = fileModel.create_dir(strategy_record_path, 'runs')
        self.net_saved_path = fileModel.create_dir(strategy_record_path, 'nets')