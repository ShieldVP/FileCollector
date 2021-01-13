import telebot
from os import getcwd, mkdir, path
from shutil import rmtree
from file_collector import collect
from spec_logging import logger
from config import TOKEN


# Some global vars

# Connecting to telegram
bot = telebot.TeleBot(TOKEN)
# Small main keyboard
keyboard = telebot.types.ReplyKeyboardMarkup(True, True)
keyboard.row("Привет!", 'Как это работает?', "Работает неправильно...")
# Connects chat id with name of working directory and name of caught file
user_files = dict()
# Set of users who want to complain. Needed to keep in memory those users
# To write down their complains from next message
complaining_users = set()
# Names of types of documents. Will be shown after editing a message
document_types = {1: "акт", 2: "счёт", 3: "счёт-фактуры", 4: "акт выверки"}


# File system functions

def safe_crete_directory(id):
    """
    Создаёт временную папку для хранения файлов пользователя,
    Разрешая коллизии в случае их возникновения.
    """
    working_directory, counter = path.join(getcwd(), "cache", id), 0
    while True:
        try:
            mkdir(working_directory + str(counter))
        except:
            counter += 1
        else:
            working_directory += str(counter)
            return working_directory


def clean_up(id):
    """
    Удаляет временные файлы, созданные при обработке запросов пользователя.
    """
    try:
        # If there are some files of user
        rmtree(user_files[id][0])
        user_files.pop(id)
    except:
        # If there is no file belongs to user
        pass


# Functions handling commands

@bot.message_handler(commands=['start'])
@logger
def start_command(message):
    """
    Обрабатывает команду начала работы с ботом.
    """
    greeting(message.chat.id)


@bot.message_handler(commands=['help'])
@logger
def help_command(message):
    """
    Обрабатывает команду запроса помощи.
    """
    help_message(message.chat.id)


@bot.message_handler(commands=['complain'])
@logger
def complain_command(message):
    """
    Обрабатывает команду принятия жалобы.
    """
    complain(message.chat.id)


# Text handler function

@bot.message_handler(content_types=["text"])
@logger
def handle_text(message):
    """
    Обрабатывает текстовые сообщения от пользователя.
    """
    if message.text.lower() == "как это работает?":
        help_message(message.chat.id)
    elif message.text.lower() == "привет!":
        greeting(message.chat.id)
    elif message.text.lower() == "работает неправильно...":
        complain(message.chat.id)
    elif message.chat.id in complaining_users:
        get_complain(message)
    else:
        bot.send_message(
            message.chat.id,
            "Извините, я не понимаю 😞",
            reply_markup=keyboard
        )


# Standard answers

@logger
def greeting(chat_id):
    """
    Обрабатывает запрос начала работы с ботом.
    """
    bot.send_message(
        chat_id,
        'Здравствуйте, Вас приветствует бот, помогающий в разделении '
        'документов на отдельные счета, акты и счета-фактуры. Загрузите целый '
        'файл в формате pdf, после чего выбирете тип документа и скачайте '
        'результат. Приятной работы!',
        reply_markup=keyboard
    )


@logger
def help_message(chat_id):
    """
    Обрабатывает запрос помощи.
    """
    bot.send_message(
        chat_id,
        "Вам нужно отправить в данный чат файл в формате pdf "
        "(предварительно сохраните rtf как pdf), после чего появится меню "
        "с выбором типа документа. Как только Вы выберете, файл обработается,"
        " и Вам вышлется готовый результат. Удачи!",
        reply_markup=keyboard
    )


@logger
def complain(chat_id):
    """
    Обрабатывает запрос на жалобу.
    """
    complaining_users.add(chat_id)
    bot.send_message(
        chat_id,
        "Нам очень жаль. Пожалуйста, подробно опишите проблему. "
        "Следующее Ваше сообщение будет записано и передано разработчикам.",
        reply_markup=keyboard
    )


@logger
def get_complain(message):
    """
    Записывает жалобу пользователя в complains.txt.
    """
    complaining_users.remove(message.chat.id)
    with open(path.join(getcwd(), "data", "complains.txt"), "a") as comp:
        comp.write(message.text + "\n\n")
    bot.send_message(
        message.chat.id,
        "Ваше сообщение было записано. Спасибо за помощь в разитии бота!",
        reply_markup=keyboard
    )


# Document handling

@bot.message_handler(content_types=["document"])
@logger
def handle_document(message):
    """
    Обработка сообщения с документом.
    При неправильном типе документа, отправляет сообщение об ошибке.
    При стандартных расширениях сохраняет документ
    И предоставляет выбор типа документа.
    """
    # If user sent a new file while the previous one was processing
    clean_up(message.chat.id)

    # Receiving a document
    document_id = message.document.file_id
    document_name = message.document.file_name

    # TODO: Check if extension of caught document is bad.

    file_info = bot.get_file(document_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # Solving collisions
    working_directory = safe_crete_directory(document_id)

    # Downloading a document file
    src = path.join(working_directory, document_name)
    with open(src, "wb") as file:
        file.write(downloaded_file)
    user_files[message.chat.id] = working_directory, document_name

    # Choosing a type of a document
    type_choosing(message.chat.id)


@logger
def type_choosing(chat_id):
    """
    Отправка сообщения с выбором типа документа.
    """
    keys = telebot.types.InlineKeyboardMarkup()
    but_1 = telebot.types.InlineKeyboardButton(text="Акт", callback_data=1)
    but_2 = telebot.types.InlineKeyboardButton(text="Счёт", callback_data=2)
    but_3 = telebot.types.InlineKeyboardButton(text="Счёт-фактуры", callback_data=3)
    but_4 = telebot.types.InlineKeyboardButton(text="Акт выверки", callback_data=4)
    but_5 = telebot.types.InlineKeyboardButton(text="Назад", callback_data="Back")
    keys.add(but_1, but_2, but_3, but_4, but_5)
    bot.send_message(
        chat_id,
        "Какого типа этот документ?",
        reply_markup=keys
    )


@bot.callback_query_handler(func=lambda call: True)
@logger
def answer_type(call):
    """
    Обрабатывает нажатие кнопок выбора типа документа.
    """
    if call.data == "Back":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Вы завершили работу с этим файлом.",
            reply_markup=None
        )
    else:
        # Handle a type of document
        type = int(call.data)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Вы выбрали документ типа {}.".format(document_types[type]),
            reply_markup=None
        )
        process_document(call.message.chat.id, type)
    # Collecting rubbish
    clean_up(call.message.chat.id)


@logger
def process_document(chat_id, type):
    """
    Обработка документа после определения его типа.
    """
    # Which files are we working with?
    working_directory, document_name = user_files[chat_id]

    # Processing document
    result_src, errors = collect(working_directory, document_name, type)

    # Sending a result archive
    if errors:
        find_errors = [str(error[1]) for error in errors if error[0] == 0]
        if find_errors:
            bot.send_message(
                chat_id,
                f"В ходе работы возникла ошибка с страницей № {find_errors[0]}"
                " она была пропущена. Возможно, она не удовлетворяет "
                "стандартному формату данных."
                if len(find_errors) == 1 else
                "В ходе работы возникли ошибки со страницами № " +
                ", ".join(find_errors) +
                " они были пропущены. Возможно, они не удовлетворяют "
                "стандартному формату данных."
            )
        save_errors = [str(error[1]) for error in errors if error[0] == 1]
        if save_errors:
            bot.send_message(
                chat_id,
                "В ходе работы возникла ошибка сохранения с страницей "
                f"№ {save_errors[0]} она была пропущена. "
                "Возможно, она не удовлетворяет стандартному формату данных."
                if len(save_errors) == 1 else
                "В ходе работы возникли ошибки сохранения со страницами № " +
                ", ".join(save_errors) +
                " они были пропущены. Возможно, они не удовлетворяют "
                "стандартному формату данных."
            )
    with open(result_src, 'rb') as result:
        bot.send_document(chat_id, result)


# Program loop

if __name__ == "__main__":
    bot.polling(none_stop=True)
