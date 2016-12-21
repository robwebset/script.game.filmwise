# -*- coding: utf-8 -*-
import os
import hashlib
import traceback
import urllib
import urllib2
from BeautifulSoup import BeautifulSoup

import ConfigParser


#########################
# Main
#########################
class FilmWiseCore():
    def __init__(self):
        self.website = "http://www.filmwise.com"

    def getQuizList(self):
        # Generate the URL and get the page
        html = self._getHtmlSource(self.website + "/invisibles/index.shtml")

        soup = BeautifulSoup(''.join(html))

        searchResults = soup.findAll('table', {"cellpadding": "5", "cellspacing": "0", "border": "0"})

        quizList = []

        for table in searchResults:
            # Only interested in tables with the quiz list in
            if "Invisibles Quiz #" not in str(table):
                continue

            for row in table.findAll('tr'):
                # Get the date
                date = None
                dateColumn = row.find('td', {'class': 'small'})
                if dateColumn is not None:
                    date = dateColumn.getText()

                # Not get the actual detail of the quiz
                detailColumn = row.find('td', {'width': '100%'})
                if detailColumn is None:
                    continue

                title = None
                quizNum = 0
                questionLink = None
                answersLink = None

                for link in detailColumn.findAll('a'):
                    if "answers" in str(link):
                        answersLink = link['href']
                    else:
                        title = link.getText()
                        questionLink = link['href']
                        # Extract the number of the quiz from the title
                        if title not in [None, ""]:
                            try:
                                lastElement = title.split('#')[-1]
                                quizNum = int(lastElement.split(':')[0])
                            except:
                                quizNum = -1

                # If we found a quiz add it to the list
                if questionLink is not None:
                    questionLink = self._fullUrl(questionLink)
                    answersLink = self._fullUrl(answersLink)
                    quizList.append({"number": quizNum, "name": title, "date": date, "link": questionLink, "solution": answersLink})

        return quizList

    def getQuizData(self, quizUrl):
        html = self._getHtmlSource(quizUrl)
        soup = BeautifulSoup(''.join(html))

        quizDetails = {}
        quizDetails['form'] = None
        quizDetails['redirect'] = None
        quizDetails['questions'] = []

        # Get the information needed to submit the form
        formInput = soup.find('input', {"name": "form"})
        if formInput is not None:
            quizDetails['form'] = formInput['value']

        redirectInput = soup.find('input', {"name": "redirect"})
        if redirectInput is not None:
            quizDetails['redirect'] = redirectInput['value']

        table = soup.find('table', {"width": "710"})

        if table is not None:
            for row in table.findAll('tr'):
                if "Movie" in str(row):
                    for column in row.findAll('td'):
                        # Get the image from the column
                        imageTag = column.find('img')
                        if imageTag is not None:
                            image = self._fullUrl(imageTag['src'])
                            # Need to know what the submit form will need to identify this one
                            inputName = column.find('input')
                            if inputName is not None:
                                tag = inputName['name']
                                quizDetails['questions'].append({"name": tag, "image": image})

        return quizDetails

    def getSolution(self, solutionUrl):
        html = self._getHtmlSource(solutionUrl)
        soup = BeautifulSoup(''.join(html))

        solutionDetails = {}

        table = soup.find('table', {"width": "710", "cellpadding": "4", "cellspacing": "0", "border": "0"})

        if table is not None:
            for row in table.findAll('tr'):
                if "answers" not in str(row):
                    continue

                for column in row.findAll('td', {'valign': 'top'}):
                    # Get the image from the column
                    imageTag = column.find('img')
                    if imageTag is not None:
                        image = self._fullUrl(imageTag['src'])
                        # Need to know what the submit form will need to identify this one
                        answerElem = column.find('font', {'class': 'answers'})
                        if answerElem is not None:
                            answer = answerElem.getText()
                            solutionDetails[image] = answer

        return solutionDetails

    def checkAnswer(self, form, redirect, answers):
        url = self.website + "/cgi-bin/score.cgi"
        req = urllib2.Request(url)
        req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')

        arguments = answers.copy()
        arguments['form'] = form
        arguments['redirect'] = redirect

        correctAnswers = 0
        try:
            data = urllib.urlencode(arguments)
            response = urllib2.urlopen(req, data)
            # The URL will tell us how many we got correct
            forwardUrl = response.geturl()

            # Extract the number of correct answers
            scoreIdx = forwardUrl.find("score=")
            if scoreIdx > 0:
                scoreIdx = scoreIdx + 6
                correctAnswers = int(forwardUrl[scoreIdx:scoreIdx + 1])
        except:
            pass

        # TODO: if this is not the latest quiz, then the returned document will
        # actually contain the results, we should read the answers from that
        return correctAnswers

    def _fullUrl(self, partUrl):
        url = partUrl
        if partUrl not in [None, ""]:
            if not partUrl.startswith("http"):
                url = "%s/invisibles/%s" % (self.website, partUrl)
        return url

    def _getHtmlSource(self, url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')

        doc = None
        try:
            response = urllib2.urlopen(req)
            # Holds the webpage that was read via the response.read() command
            doc = response.read()
            # Closes the connection after we have read the webpage.
            try:
                response.close()
            except:
                pass
        except:
            return None
        return doc

    def getHashForImage(self, imageUrl, tempFileName='filmwiseImage.jpg'):
        # First save the image to a temporary file
        if os.path.exists(tempFileName):
            os.remove(tempFileName)

        # Download the file
        try:
            fp, h = urllib.urlretrieve(imageUrl, tempFileName)
        except:
            print "Error: Failed to get file %s" % imageUrl
            return None

        # Now get the hash of the image file
        hash_md5 = hashlib.md5()

        blocksize = 64 * 1024
        try:
            with open(tempFileName, 'rb') as fp:
                while True:
                    data = fp.read(blocksize)
                    if not data:
                        break
                    hash_md5.update(data)
        except:
            print "Error: Failed to create hash for %s" % tempFileName
            return None

        if os.path.exists(tempFileName):
            os.remove(tempFileName)

        return hash_md5.hexdigest()


#########################
# Main
#########################
if __name__ == '__main__':
    filmWise = FilmWiseCore()
    # get the list of available quizzes
    quizList = filmWise.getQuizList()

    print "Available Number of Quizzes is %d" % len(quizList)

    # Read the existing config file
    cheatsFile = ConfigParser.ConfigParser()
    cheatsFile.read('cheats.ini')
    lastQuiz = cheatsFile.getint('History', 'latestQuiz')

    if lastQuiz in [None, ""]:
        lastQuiz = 700

    print "Last Quiz in cheats file = %d" % lastQuiz

    # Make sure the sections exist
    if not cheatsFile.has_section('History'):
        cheatsFile.add_section('History')
    if not cheatsFile.has_section('Cheats'):
        cheatsFile.add_section('Cheats')

    cheatsFile.set('History', 'earliestQuiz', 701)

    highestQuizAdded = lastQuiz

    for quiz in quizList:
        # Only check the quizes from the point we need to get data for
        if quiz['number'] <= lastQuiz:
            continue

        print "Selected quiz is %s" % quiz['name']
        # Make sure there is a solution available
        if quiz['solution'] in [None, ""]:
            continue

        print "Solutions Available"
        # Now get the details of the questions for this quiz number
        quizQuestions = filmWise.getQuizData(quiz['link'])
        quizSolution = filmWise.getSolution(quiz['solution'])

        if (quizQuestions not in [None, ""]) and (quizSolution not in [None, ""]):
            questions = quizQuestions['questions']
            # Generate a map of the original Image URL and the name of the movie
            numQuestions = len(questions)
            if numQuestions > 8:
                numQuestions = 8
                if len(quizSolution) < numQuestions:
                    numQuestions = len(quizSolution)

            answerMap = {}
            for i in range(0, numQuestions):
                img = questions[i]['image']
                if img is None:
                    continue
                solutionImg = img.replace('.jpg', 'a.jpg')
                answer = quizSolution.get(solutionImg, '')
                if answer not in [None, ""]:
                    imgHash = filmWise.getHashForImage(img)
                    if imgHash not in [None, ""]:
                        print "showSolution: Answer is - %s (%s)" % (answer, imgHash)
                        cheatsFile.set('Cheats', imgHash, answer)

                        if quiz['number'] > highestQuizAdded:
                            highestQuizAdded = quiz['number']

    cheatsFile.set('History', 'latestQuiz', highestQuizAdded)

    with open('cheats.ini', 'w') as configfile:
        cheatsFile.write(configfile)

    del filmWise
