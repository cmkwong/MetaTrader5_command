import config

def check(input):

    if input == '-s':
        # inspect the strategy
        print("Please select the strategy list")
        return config.COMMAND_CHECKED

    if input == '-add':
        # input the start and end date
        #
        pass

    else:
        return input