from controllers import traderController

# define the trader
trader = traderController.Trader()

output = None
while(output != 'OFF'):
    output = trader.run()

trader.end()