import inspect
import pyperclip as clp

def enter():
    # setting placeholder
    placeholder = 'Input: '
    user_input = input(placeholder) # waiting user input
    return user_input

# param_format = {
#     'symbols': {"default": "EURUSD AUDJPY AUDUSD CADJPY USDCAD", "example": "EURUSD AUDJPY AUDUSD CADJPY USDCAD", "type": list},
#     'start': {'default': "2010 1 1 0 0", "example": "2010 1 1 0 0", "type": tuple},
#     'end': {'default': "2021 5 1 0 0", "example": "2021 5 1 0 0", "type": tuple},
#     'timeframe': {"default": "1H", "example": "30min 1H 1D 1W 1MN", "type": str},
#     'change_of_close': {"default": "False", "example": "False", "type": bool}
# }

def _params_preprocess(sig):
    params = {}
    for param in sig.parameters.values():
        if (param.kind == param.KEYWORD_ONLY) and (param.default == param.empty):
            input_str = input("{}: ".format(param.name))
            if param.name == 'symbols':
                params[param.name] = input_str.split(' ')
            elif param.name == 'start' or param.name == 'end':
                params[param.name] = list(map(int, input_str.split(' ')))
            else:
                params[param.name] = input_str


def ask_params(class_object):
    # define a moving average strategy
    sig = inspect.signature(class_object)
    params = {}
    for param in sig.parameters.values():
        if (param.kind == param.KEYWORD_ONLY) and (param.default == param.empty):
            input_data = input("{}({}): ".format(param.name, param.annotation.__name__))
            if input_data.find(' ') != -1:
                input_data = input_data.split(' ')
            if param.annotation == bool:
                input_data = bool(int(input_data))
            if type(input_data) != param.annotation:
                if param.annotation == list:
                    input_data = [input_data]
                else:
                    input_data = param.annotation(input_data)
            params[param.name] = input_data
    return params

def int_input():
    try:
        usr_input = input()
        usr_input = int(usr_input)
    except ValueError:
        print("That is not a number. \nPlease enter a Number.")
        return None
    except KeyboardInterrupt:
        print("Wrong input")
        return None
    return usr_input

def float_input():
    try:
        usr_input = input()
        usr_input = float(usr_input)
    except ValueError:
        print("That is not a number. \nPlease enter a number.")
        return None
    except KeyboardInterrupt:
        print("Wrong input")
        return None
    return usr_input

def user_confirm():
    placeholder = 'Input [y]es to confirm OR others to cancel: '
    confirm_input = input(placeholder)
    if confirm_input == 'y' or confirm_input == "yes":
        return True
    else:
        return False