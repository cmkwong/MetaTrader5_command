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

    if input == '-addma':
        params = inputModel.ask_params(MovingAverage)
        trader.add_strategy(MovingAverage, params)

    if input == '-addcoin':
        params = inputModel.ask_params(Cointegration)
        trader.add_strategy(Cointegration, params)

    if input == '-addrl':
        params = inputModel.ask_params(SimpleRL)
        trader.add_strategy(SimpleRL, params)

    else:
        return input