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