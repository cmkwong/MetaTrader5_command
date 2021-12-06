import inspect
import pyperclip as clp

from models import paramModel
import config

def enter():
    # setting placeholder
    placeholder = 'Input: '
    user_input = input(placeholder) # waiting user input
    return user_input

def input_param(param, strategy_param_dict):
    input_data = input("{}({})\nDefault: {}: ".format(param.name, param.annotation.__name__, strategy_param_dict[param.name]))
    if len(input_data) == 0:
        input_data = strategy_param_dict[param.name]
    return input_data

def ask_params(class_object):
    # read the default params text
    strategy_param_dict = paramModel.read_default_param(class_object.__name__)

    # asking the params
    sig = inspect.signature(class_object)
    params = {}
    for param in sig.parameters.values():
        if (param.kind == param.KEYWORD_ONLY) and (param.default == param.empty):
            input_data = input_param(param, strategy_param_dict)
            if type(input_data) != param.annotation:
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