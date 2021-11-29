from controllers import traderController, executeController, dataLoaderController
import config

# define the trader
executor = executeController.Executor()
dataLoader = dataLoaderController.DataLoader(data_path='', timezone='Hongkong', deposit_currency='USD')
trader = traderController.Trader(executor, dataLoader, config.DOCS_PATH)

output = None
while(output != 'OFF'):
    output = trader.user_input()

trader.end()