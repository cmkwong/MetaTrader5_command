import config
from strategies.movingAverage import MovingAverage
from strategies.conintegration import Cointegration
from strategies.RL import SimpleRL

from utils import paramModel

def check(input, trader):

    if input == '-s':
        # inspect the strategy
        print("Please select the strategy list")
        return config.COMMAND_CHECKED

    # add the strategies as candidates
    elif input == '-addma':
        params = paramModel.ask_params(MovingAverage, config.PARAMS_PATH, config.PARAMS_FILENAME)
        trader.add_candidates(MovingAverage, params)
        return config.COMMAND_CHECKED

    elif input == '-addcoin':
        params = paramModel.ask_params(Cointegration, config.PARAMS_PATH, config.PARAMS_FILENAME)
        trader.add_candidates(Cointegration, params)
        return config.COMMAND_CHECKED

    elif input == '-addrl':
        params = paramModel.ask_params(SimpleRL, config.PARAMS_PATH, config.PARAMS_FILENAME)
        trader.add_candidates(SimpleRL, params)
        return config.COMMAND_CHECKED

    # train the candidates
    elif input == '-train':
        return config.COMMAND_CHECKED

    else:
        return input