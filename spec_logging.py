from datetime import datetime as dt
from traceback import format_exc
from functools import wraps
from os import path, getcwd


def get_date():
    """
    Возвращает текущую дату и время в формате дд-мм-гггг_Ч:М:С.
    """
    return dt.today().strftime("%d-%m-%Y_%H:%M:%S")


def logger(func):
    """
    Логирует вызов и завершение функции, ошибки в ходе выполнения.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Getting the function name
        name = func.__name__

        # Finding the user id of call to identify log and probable errors
        try:
            # If first parameter is message
            user = args[0].from_user.id
        except:
            try:
                # To check parameters of "answer_type" function
                user = args[0].message.from_user.id
            except:
                try:
                    # If first parameter of function is digit
                    # Then it's chat id
                    user = str(args[0])
                    assert user.isdigit()
                except:
                    # If there is no user identifier in parameters of function
                    user = "same"

        def log(action, date):
            """
            Записывает действие action пользователя user с функцией name
            В момент времени date.
            """
            with open(path.join(getcwd(), "data", "logs.txt"), "a") as logs:
                logs.write(
                    "{}: {} at {} from {}.\n".format(action, name, date, user)
                )

        def handle_error(error, date):
            """
            Записывает ошибку error пользователя user в функции name
            В момент времени date.
            """
            # TODO: Send a message on email or in telegram to developer.
            with open(path.join(getcwd(), "data", "errors.txt"), "a") as err:
                err.write(
                    "{} at {} from {}:\n{}\n".format(name, date, user, error)
                )

        log("CALL", get_date())  # Write that function was called
        try:
            func(*args, **kwargs)  # Executing function
        except:
            # Error happened
            date = get_date()
            log("ERROR", date)  # Logging event as error
            handle_error(format_exc(), date)  # Saving traceback of error
        else:
            log("FINISH", get_date())  # Successful execute
    return wrapper
