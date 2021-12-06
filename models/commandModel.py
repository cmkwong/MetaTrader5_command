import config
from strategies.movingAverage import MovingAverage
from strategies.conintegration import Cointegration
from strategies.RL import SimpleRL
from models import inputModel

def check(input, trader):

    if input == '-s':
        # inspect the strategy
        print("Please select the strategy list")
        return config.COMMAND_CHECKED

    elif input == '-addma':
        params = inputModel.ask_params(MovingAverage)
        trader.add_strategy(MovingAverage, params)

    elif input == '-addcoin':
        params = inputModel.ask_params(Cointegration)
        trader.add_strategy(Cointegration, params)

    elif input == '-addrl':
        params = inputModel.ask_params(SimpleRL)
        trader.add_strategy(SimpleRL, params)

    else:
        return input