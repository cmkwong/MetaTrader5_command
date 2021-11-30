from controllers.traderController import Trader
import config

# define the trader
trader = Trader(deposit_currency='USD', timezone='Hongkong', local_data_path='', docs_path=config.DOCS_PATH)

output = None
while(output != 'OFF'):
    output = trader.user_input()

trader.end()