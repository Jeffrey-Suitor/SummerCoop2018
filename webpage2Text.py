import urllib.request
import bs4
import re

def generateReports():
    websites = open('urlLinks.txt')
    websiteList = websites.read().split()
    websites.close()

    for i in range(len(websiteList)):

        try: # Checks to see if report is already created
            reportName = ' '.join(['reports/report', str(i+1)])
            report = open(reportName, 'r')
            report.close()

        except: #If report is not created
            url = str(websiteList[i])
            headers = {}
            headers['User-Agent'] = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"
            req = urllib.request.Request(url, headers = headers)
            webpage = str(urllib.request.urlopen(req).read())
            soup = bs4.BeautifulSoup(webpage,"lxml")
            [s.extract() for s in soup(['style', 'script', '[document]', 'head', 'title'])]
            visibleText = soup.getText()
            newString = re.sub("[^a-zA-Z]+", " ", str(visibleText.encode("utf-8")))

            # Create new report
            reportName = ' '.join(['reports/report', str(i+1)])
            newReport = open(reportName, "w+")
            newReport.write(newString)
            newReport.close()
