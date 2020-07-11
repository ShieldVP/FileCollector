# Imports

from PyPDF2 import PdfFileReader as read, PdfFileWriter as create_pdf
from os import mkdir, path
from shutil import make_archive
from functools import wraps
import io
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage


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


def extract_text_by_page(pdf_file):
    """
    Генератор текста страниц.
    Выдаёт текст со страницы с номером, соответствующим текущей итерации.
    """
    for page in pdf_file:
        resource_manager = PDFResourceManager()
        fake_file_handle = io.StringIO()
        converter = TextConverter(resource_manager, fake_file_handle)
        page_interpreter = PDFPageInterpreter(resource_manager, converter)
        page_interpreter.process_page(page)

        text = fake_file_handle.getvalue()
        yield text

        # Close open handles
        converter.close()
        fake_file_handle.close()


@normalize_spaces
def find_name(page, document_type):
    """
    Находит номер документа в зависимости от его типа.
    Возвращает название файла (без двойных пробелов).
    """
    if document_type == 1:
        start, shift = page.find("Договор №"), 9
        if start == -1:
            start, shift = page.find("Государственный контракт №"), 26
        end = page.find("от")
        name = page[start + shift:end] + " акт"
        return name
    elif document_type == 2:
        start, shift = page.find("Договор"), 7
        if start == -1:
            start, shift = page.find("контракт"), 8
        end = page.find("Расчетный")
        name = page[start + shift:end] + " счёт"
        return name
    elif document_type == 3:
        start, shift = page.find("Договор №"), 9
        if start == -1:
            start, shift = page.find("Государственный контракт №"), 26
        end = page.find("Валюта")
        name = page[start + shift:end] + " с-ф"
        return name
    elif document_type == 4:
        start, shift = page.find("Договор №"), 9
        if start == -1:
            start, shift = page.find("Государственный контракт №"), 26
        end = page.find("от")
        name = page[start + shift:end] + " ав"
        return name


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
    for i, page in enumerate(extract_text_by_page(text_pdf)):
        # Extracting current page
        document = create_pdf()
        document.addPage(pdf.getPage(i))
        # Writing current document
        name = find_name(page, document_type)
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
        text_pdf = PDFPage.get_pages(
            file,
            caching=True,
            check_extractable=True
        )
        # Creating new folder for result
        new_directory = path.join(working_directory, dir_name)
        mkdir(new_directory)
        # Separating pages and saving them with correct names
        err = extract_files(pdf, text_pdf, new_directory, document_type)
    # Creating a result archive
    make_archive(new_directory, 'zip', new_directory)
    return new_directory + ".zip", err
