import inspect
import pyperclip as clp

def enter():
    # setting placeholder
    placeholder = 'Input: '
    user_input = input(placeholder) # waiting user input
    return user_input

def ask_params(class_object):
    # define a moving average strategy
    sig = inspect.signature(class_object)
    params = {}
    for param in sig.parameters.values():
        if (param.kind == param.KEYWORD_ONLY) and (param.default == param.empty):
            input_data = input("{}({}): ".format(param.name, param.annotation.__name__))
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