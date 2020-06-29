# Imports

from PyPDF2 import PdfFileReader as read, PdfFileWriter as create_pdf
from os import mkdir, path
from shutil import make_archive
import fitz


# Functions

def find_name(text, document_type):
    if document_type == 1:
        for j in range(len(text)):
            if text[j].startswith("Договор №") or \
                    text[j].startswith("Государственный контракт №"):
                return text[j].split()[1][1:] + " акт"
    elif document_type == 2:
        for j in range(len(text)):
            if text[j] == "Договор " or text[j] == "контракт ":
                return text[j + 1][1:-1] + " счёт"
    elif document_type == 3:
        for j in range(len(text)):
            if text[j].startswith("Договор №") or \
                    text[j].startswith("Государственный контракт №"):
                return text[j].split()[2] + " с-ф"


def save_file(document, name, dir_name, errors, page):
    try:
        document.write(open(path.join(dir_name, name + ".pdf"), "wb"))
    except:
        errors.append((1, page + 1))


def extract_files(pdf, text_pdf, dir_name, document_type):
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
    Путь до рабочей директории,
    Название файла в формате pdf,
    Тип документа: акт - 1, счёт - 2, счёт-фактуры - 3
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
