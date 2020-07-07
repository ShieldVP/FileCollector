# Imports

from PyPDF2 import PdfFileReader as read, PdfFileWriter as create_pdf
from os import mkdir, path
from shutil import make_archive
from functools import wraps
import fitz


# Functions

def normalize_spaces(func):
    """
    Удаляет двойные пробелы, пробелы по краям в возвращаемой строке.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        tmp = func(*args, **kwargs)
        return ' '.join(tmp.split())
    return wrapper


@normalize_spaces
def find_name(text, document_type):
    """
    Находит номер документа в зависимости от его типа.
    Возвращает название файла (без двойных пробелов).
    """
    if document_type == 1:
        for j in range(len(text)):
            if text[j].startswith("Договор №"):
                return text[j][9:-14] + " акт"
            elif text[j].startswith("Государственный контракт №"):
                return text[j][26:-14] + " акт"
    elif document_type == 2:
        for j in range(len(text)):
            if text[j] == "Договор " or text[j] == "контракт ":
                return text[j + 1][1:-1] + " счёт"
    elif document_type == 3:
        for j in range(len(text)):
            if text[j].startswith("Договор №"):
                return text[j][10:] + " с-ф"
            elif text[j].startswith("Государственный контракт №"):
                return text[j][27:] + " с-ф"
    elif document_type == 4:
        for j in range(len(text)):
            if text[j].startswith("Договор №"):
                return text[j][10:-15] + " ав"
            elif text[j].startswith("Государственный контракт №"):
                return text[j][27:-15] + " ав"


def save_file(document, name, dir_name, errors, page):
    """
    Сохраняет файл с названием name, в папке dir_name.
    Если такой файл уже есть, то сохраняет с добавлением индекса кратности.
    В случае возникновения ошибки сохраняет их в errors.
    """
    try:
        if path.exists(path.join(dir_name, name + ".pdf")):
            it = 1
            new_name = name + f" ({it}).pdf"
            while path.exists(path.join(dir_name, new_name)):
                it += 1
                new_name = name + f" ({it}).pdf"
            document.write(open(path.join(dir_name, new_name), "wb"))
        else:
            document.write(open(path.join(dir_name, name + ".pdf"), "wb"))
    except:
        errors.append((1, page + 1))


def extract_files(pdf, text_pdf, dir_name, document_type):
    """
    Функция проходит по каждой странице, запрашивает название у неё и
    Сохраняет её как отдельный документ.
    """
    errors = list()
    for i in range(pdf.getNumPages()):
        # Extracting current page
        document = create_pdf()
        document.addPage(pdf.getPage(i))
        text = text_pdf.loadPage(i).getText().split('\n')
        # Writing current document
        name = find_name(text, document_type)
        if name:
            save_file(document, name, dir_name, errors, i)
        else:
            errors.append((0, i + 1))
    return errors


def collect(working_directory, file_name, document_type):
    """
    Выполнение основной задачи бота:
    Разделение pdf файла на отдельные документы
    с названиями - номерами документов.
    Функция принимает параметры:
    Путь до рабочей директории,
    Название файла в формате pdf,
    Тип документа: акт - 1, счёт - 2, счёт-фактуры - 3, акт выверки - 4
    Функция возвращает:
    Адрес результирующего архива,
    Список ошибок, возникших в ходе работы.
    """

    no_suffix_file_name = file_name[:-4]
    dir_name = no_suffix_file_name
    pdf_document = path.join(working_directory, file_name)

    # Opening pdf version of file
    with open(pdf_document, "rb") as file:
        # Works well with separating on pages
        pdf = read(file)
        # Works well with extracting the text
        text_pdf = fitz.open(pdf_document)
        # Creating new folder for result
        new_directory = working_directory + "/" + dir_name
        mkdir(new_directory)
        # Separating pages and saving them with correct names
        err = extract_files(pdf, text_pdf, new_directory, document_type)
    # Creating a result archive
    make_archive(new_directory, 'zip', new_directory)
    return new_directory + ".zip", err
