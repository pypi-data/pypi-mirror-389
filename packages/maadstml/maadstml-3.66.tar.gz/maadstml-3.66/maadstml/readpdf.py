import sys
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
#from StringIO import StringIO
from io import StringIO
import urllib.request  
import tmltextsummary
import os
import datetime
import glob


from pdfminer.layout import LAParams
from pdfminer.converter import TextConverter
 
class MyParser(object):
    def __init__(self, pdf):
        ## Snipped adapted from Yusuke Shinyamas 
        #PDFMiner documentation
        # Create the document model from the file
        parser = PDFParser(open(pdf, 'rb'))
        document = PDFDocument(parser)
        # Try to parse the document
        if not document.is_extractable:
            raise PDFTextExtractionNotAllowed
        # Create a PDF resource manager object 
        # that stores shared resources.
        rsrcmgr = PDFResourceManager()
        # Create a buffer for the parsed text
        retstr = StringIO()
        # Spacing parameters for parsing
        laparams = LAParams()
        codec = 'utf-8'
 
        # Create a PDF device object
        device = TextConverter(rsrcmgr, retstr,
                               laparams = laparams)
        # Create a PDF interpreter object
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        # Process each page contained in the document.
        for page in PDFPage.create_pages(document):
            interpreter.process_page(page)
         
        self.records            = []
         
        lines = retstr.getvalue().splitlines()
        for line in lines:
            self.handle_line(line)
     
    def handle_line(self, line):
        # Customize your line-by-line parser here
        self.records.append(line)

def scrapepdf(theurl,fn):
    scraped_data = urllib.request.urlopen(theurl)  
    file = open(fn, 'wb')
    file.write(scraped_data.read())
    file.close()
    #return article_text

def startpdfreading(filename,fvalue,keycount):
  #os.path.abspath(os.getcwd())
  thesize=round(os.path.getsize(filename)/1000000,2)
  m_time = os.path.getmtime(filename)
  dt_m = datetime.datetime.fromtimestamp(m_time)
  c_time = os.path.getctime(filename)
  # convert creation timestamp into DateTime object
  dt_c = datetime.datetime.fromtimestamp(c_time)
  co = str(dt_c) [0:19]
  mo = str(dt_m) [0:19]

  p = MyParser(filename)
  thetext='\n'.join(p.records)
  article_text=thetext.encode('utf8')
  summarized="{\"filename\":\"" + filename + "\",\"filesize(MB)\":"+str(thesize)+",\"filecreatedon\":\"" + co + "\",\"filemodifiedon\":\"" + mo + "\",\"keywords\":" +  tmltextsummary.startsummary(thetext,fvalue,keycount)
 # print(summarized)
  return summarized
## else:
##     mylist = [f for f in glob.glob(filefolder +"/*.pdf")]
##     #print(mylist)
##     summaryarr = ""
##     for filename in mylist:         
##        thesize=round(os.path.getsize(filename)/1000000,2)
##        m_time = os.path.getmtime(filename)
##        dt_m = datetime.datetime.fromtimestamp(m_time)
##        c_time = os.path.getctime(filename)
##        # convert creation timestamp into DateTime object
##        dt_c = datetime.datetime.fromtimestamp(c_time)
##        co = str(dt_c) [0:19]
##        mo = str(dt_m) [0:19]
##
##        p = MyParser(filename)
##        thetext='\n'.join(p.records)
##        article_text=thetext.encode('utf8')
##        summarized="{\"filename\":\"" + filename + "\",\"filesize(MB)\":"+str(thesize)+",\"filecreatedon\":\"" + co + "\",\"filemodifiedon\":\"" + mo + "\",\"keywords\":" +  tmltextsummary.startsummary(thetext,fvalue,keycount)
##        # print(summarized)
##        summaryarr = summarized + ","
##     summaryarr = summaryarr[-1]
##     return summaryarr
##     
##    # read dir
##    

##if __name__ == '__main__':
##
##    fname=sys.argv[1]
##    fvalue=sys.argv[2]
##    fu=sys.argv[3]
##    fu=int(fu)
##
##    if fu==0:
##    #fname='C:\\inetpub\\wwwroot\\T2A_WEBSITE\\STOCKS\\MAADS\\csvuploads\\theoryofvalue.pdf'
##       try:
##         p = MyParser(sys.argv[1])
##         thetext='\n'.join(p.records)
##         print (thetext.encode('utf8'))
##       except Exception as e:
##         print("ERROR: This PDF seems to be locked...it is not allowing extraction: %s" % (e))  
##    elif fu==1:
##       fn=sys.argv[4]
##       try:
##         scrapepdf(fname,fn)
##         p = MyParser(fn)
##         thetext='\n'.join(p.records)
##         print (thetext.encode('utf8'))
##       except Exception as e:
##         print("ERROR: This PDF seems to be locked...it is not allowing extraction: %s" % (e))  
##         
##        
##
