from os import path
from win32com.client import Dispatch
from spec_logging import logger


@logger
def convert(src):
    out_file = path.splitext(src)[0] + '.pdf'
    if src != out_file:
        word = Dispatch('Word.Application')
        doc = word.Documents.Open(src)
        doc.SaveAs(out_file, FileFormat=17)  # wdFormatPDF = 17
        doc.Close()
        word.Quit()
