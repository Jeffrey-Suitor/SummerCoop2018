import glob
import errno
import PyPDF2
import easytextract
import textract



def pdf2Text():
    reportNum = 0
    path = 'C:/Users/Jeff Suitor/Desktop/chemobrainPapers/test/1078-0432.CCR-14-2775.full.pdf'
    files = glob.glob(path)
    for name in files:
        try:
            with open(name,'r') as f:
                pdfReader = PyPDF2.PdfFileReader(f)
                num_pages = pdfReader.numPages
                count = 0
                text = ""
                while count < num_pages:
                    pageObj = pdfReader.getPage(count)
                    count += 1
                    text += pageObj.extractText()
                if text != "":
                    text = text
                else:
                    text = textract.process(fileurl, method='tesseract', language='eng')
                punctuations = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
                noPunct = ""
                for char in text:
                    if char not in punctuations:
                        noPunct = noPunct + char
                reportNum +=1
                reportName = ' '.join(['reports/report', str(reportNum)])
                newReport = open(reportName, "w+")
                newReport.write(noPunct)
                newReport.close()

        except IOError as exc:
            print('error')
            if exc.errno != errno.EISDIR:
                raise

import ctypes, sys

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if is_admin():
    print('admin')
    pdf2Text()
else:
    # Re-run the program with admin rights
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)