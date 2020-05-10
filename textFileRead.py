# Libraries
import webpage2Text
import os
import shutil
import time

# Setup variables
alphabet = []
reportCounter = 0

# Create alphabet list
for i in range(97, 123):
    alphabet.append(chr(i))


# List from text file
def textFileList(textfile):
    file = open(textfile, 'r')
    fileList = file.read().split()
    file.close()
    return fileList


# Drug list sorter
def drugSorter(alphabet, drugList):
    sortedDrugList = [[] for x in range(26)]
    for i in range(len(drugList)):
        for k in range(len(alphabet)):
            if drugList[i][0] == alphabet[k]:
                sortedDrugList[k].append(drugList[i])
    return sortedDrugList


# Report list sorter
def reportSorter(alphabet, reportList, shortestString, longestString):
    sortedReportList = [[] for x in range(26)]
    for i in range(len(reportList)):
        for k in range(len(alphabet)):
            if shortestString <= len(reportList[i]) <= longestString:  # If the word is shorter than the shortest drug name ignore
                if reportList[i][0].lower() == alphabet[k]:
                    sortedReportList[k].append(reportList[i])  # Sort based on alphabet
    return sortedReportList


# Test to see if keyword is returned
def keyWordTest(reportList, keyWordList):
    for i in range(len(reportList)):
        for k in range(len(keyWordList)):
            if reportList[i] == keyWordList[k] or reportList[i] == keyWordList[k].capitalize():  # If keyword is detected
                return True


# Find shortest length string in drug list
def stringLengthFinder(drugList):
    shortestString = 100
    longestString = 0
    for i in range(len(drugList)):
        if len(drugList[i]) < shortestString:
            shortestString = len(drugList[i])
        if len(drugList[i]) >= longestString:
            longestString = len(drugList[i])
    return shortestString, longestString


#User input
def userInput():
    newParse = None
    while newParse not in ('y', 'Y', 'n', 'N'):
        newParse = input('Use currently generated reports? Y/N')
        if newParse == 'y' or newParse == 'Y': # Use currently generated reports
            startTime = time.time()
            return startTime
        elif newParse == 'n'  or newParse == 'N': # Generate new reports
            startTime = time.time()
            try:
                shutil.rmtree('reports')
                os.makedirs('reports')
                return startTime
            except:
                os.makedirs('reports')
                return startTime
        else:
            print('This is not a valid selection')


# Initial setup
startTime = userInput()
keyWordList = textFileList('Keywords.txt')
drugList = textFileList('breastCancerDrugs.txt')
finalReportList = drugSorter(alphabet, drugList)
finalDrugList = drugSorter(alphabet, drugList)
shortestString, longestString = stringLengthFinder(drugList)
webpage2Text.generateReports()

# Main program
while True:

    # Report opening
    reportCounter += 1
    reportName = ' '.join(['reports/report', str(reportCounter)])

    try:
        reportList = textFileList(reportName)  # Generates report list

        if keyWordTest(reportList, keyWordList) == True:
            sortedDrugList = drugSorter(alphabet, drugList)
            sortedReportList = reportSorter(alphabet, reportList, shortestString, longestString)
            for i in range(len(sortedReportList)):
                for j in range(len(sortedReportList[i])):
                    for k in range(len(sortedDrugList[i])):
                        if sortedReportList[i][j] == sortedDrugList[i][k]:
                            value = finalReportList[i][k]
                            del finalReportList[i][k]
                            if isinstance(value,int) == True:
                                newValue = value + 1
                                finalReportList[i].insert(k,newValue)
                                sortedDrugList[i][k] = 'Drug Found'
                            else:
                                finalReportList[i].insert(k,int(1))
                                sortedDrugList[i][k] = 'Drug Found'

    except:
        break

for i in range(len(finalReportList)):
    for j in range(len(finalReportList[i])):
        if finalDrugList[i][j] != finalReportList[i][j]:
            print(finalDrugList[i][j], finalReportList[i][j],)

finalTime = time.time()-startTime
print(round(finalTime, 2))
