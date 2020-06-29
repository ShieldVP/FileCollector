from datetime import datetime as dt
from traceback import format_exc
from functools import wraps
from os import path, getcwd


def get_date():
    return dt.today().strftime("%d-%m-%Y_%H:%M:%S")


def logger(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        name = func.__name__
        try:
            user = args[0].from_user.id
        except:
            try:
                user = args[0].message.from_user.id
            except:
                try:
                    user = str(args[0])
                    assert user.isdigit()
                except:
                    user = "same"

        def log(action, date):
            with open(path.join(getcwd(), "data", "logs.txt"), "a") as logs:
                logs.write(
                    "{}: {} at {} from {}.\n".format(action, name, date, user)
                )

        def handle_error(error, date):
            with open(path.join(getcwd(), "data", "errors.txt"), "a") as err:
                err.write(
                    "{} at {} from {}:\n{}\n".format(name, date, user, error)
                )

        log("CALL", get_date())
        try:
            func(*args, **kwargs)
        except:
            date = get_date()
            log("ERROR", date)
            handle_error(format_exc(), date)
        else:
            log("FINISH", get_date())
    return wrapper
