# -*- coding: utf-8 -*-
import os
import hashlib
import traceback
import urllib
import urllib2
import ConfigParser
from BeautifulSoup import BeautifulSoup
import xbmc

# Import the common settings
from settings import log
from settings import Settings


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
                            log("getQuizList: Quiz number is %s" % quizNum)

                # If we found a quiz add it to the list
                if questionLink is not None:
                    questionLink = self._fullUrl(questionLink)
                    answersLink = self._fullUrl(answersLink)
                    quizList.append({"number": quizNum, "name": title, "date": date, "link": questionLink, "solution": answersLink})
                    log("getQuizList: %d: %s %s - %s (%s)" % (quizNum, date, title, questionLink, answersLink))

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
            log("getQuizData: form is %s" % quizDetails['form'])

        redirectInput = soup.find('input', {"name": "redirect"})
        if redirectInput is not None:
            quizDetails['redirect'] = redirectInput['value']
            log("getQuizData: redirect is %s" % quizDetails['redirect'])

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
                                log("getQuizData: Question %s is %s" % (tag, image))

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

        for img in solutionDetails:
            log("getSolution: %s (%s)" % (solutionDetails[img], img))

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
            log("checkAnswers: url forwarded to %s" % forwardUrl)

            # Extract the number of correct answers
            scoreIdx = forwardUrl.find("score=")
            if scoreIdx > 0:
                scoreIdx = scoreIdx + 6
                correctAnswers = int(forwardUrl[scoreIdx:scoreIdx + 1])
                log("checkAnswers: Number of correct answers is %d" % correctAnswers)
        except:
            pass

        # TODO: if this is not the latest quiz, then the returned document will
        # actually contain the results, we should read the answers from that
        return correctAnswers

    def getCheatAnswer(self, imageUrl):
        # First try and get the hash of the image
        imgHash = self._getHashForImage(imageUrl)

        if imgHash in [None, ""]:
            return None

        # Now load the cheat values and see if the image has appears before
        cheatsFileLocation = Settings.getCheatLocation()
        if cheatsFileLocation in [None, ""]:
            log("getCheatAnswer: Failed to load cheats file")
            return None

        log("getCheatAnswer: File location is %s" % cheatsFileLocation)

        cheatAnswer = None

        # Now try and load the cheats file and look for the answer
        try:
            cheatsFile = ConfigParser.ConfigParser()
            cheatsFile.read(cheatsFileLocation)

            # Now perform a lookup for the image hash
            if cheatsFile.has_option('Cheats', imgHash):
                cheatAnswer = cheatsFile.get('Cheats', imgHash)

            if cheatAnswer not in [None, ""]:
                log("getCheatAnswer: found answer for %s (%s) of %s" % (imageUrl, imgHash, cheatAnswer))
            else:
                log("getCheatAnswer: cheat answer not available for %s (%s)" % (imageUrl, imgHash))
        except:
            log("getCheatAnswer: Failed to load answer for %s (%s)" % (imageUrl, imgHash))

        return cheatAnswer

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
                log("FilmWiseCore: Failed to close connection for %s" % url)
        except:
            log("FilmWiseCore: ERROR opening page %s" % url, xbmc.LOGERROR)
            log("FilmWiseCore: %s" % traceback.format_exc(), xbmc.LOGERROR)
            return None
        return doc

    def _getHashForImage(self, imageUrl, tempFileName=None):
        # Get the location of the temporary directory
        if tempFileName in [None, ""]:
            tempFileName = "%s/filmwiseImage.jpg" % Settings.getTempLocation()

        # Make sure there is not an old image left behind
        if os.path.exists(tempFileName):
            os.remove(tempFileName)

        # First save the image to a temporary file
        try:
            fp, h = urllib.urlretrieve(imageUrl, tempFileName)
        except:
            log("FilmWiseCore: Failed to get file %s" % imageUrl)
            return None

        hashValue = None

        # Make sure the image was downloaded OK
        if os.path.exists(tempFileName):
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

                hashValue = hash_md5.hexdigest()
            except:
                log("FilmWiseCore: Failed to create hash for %s" % imageUrl)

            os.remove(tempFileName)

        return hashValue
