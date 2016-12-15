# -*- coding: utf-8 -*-
import sys
import xbmc
import xbmcaddon
import xbmcgui

if sys.version_info >= (2, 7):
    import json
else:
    import simplejson as json

# Import the common settings
from resources.lib.settings import log
from resources.lib.settings import Settings

from resources.lib.core import FilmWiseCore
from resources.lib.viewer import FilmWiseViewer

ADDON = xbmcaddon.Addon(id='script.game.filmwise')
ICON = ADDON.getAddonInfo('icon')


##################################
# Main of the FilmWise Service
##################################
if __name__ == '__main__':
    log("FilmWise: Service Started")

    notifyRequired = False

    json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Addons.GetAddonDetails", "params": { "addonid": "repository.robwebset", "properties": ["enabled", "broken", "name", "author"]  }, "id": 1}')
    json_response = json.loads(json_query)

    displayNotice = True
    if ("result" in json_response) and ('addon' in json_response['result']):
        addonItem = json_response['result']['addon']
        if (addonItem['enabled'] is True) and (addonItem['broken'] is False) and (addonItem['type'] == 'xbmc.addon.repository') and (addonItem['addonid'] == 'repository.robwebset') and (addonItem['author'] == 'robwebset'):
            displayNotice = False

    if displayNotice:
        json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Addons.GetAddonDetails", "params": { "addonid": "repository.urepo", "properties": ["enabled", "broken", "name", "author"]  }, "id": 1}')
        json_response = json.loads(json_query)

        if ("result" in json_response) and ('addon' in json_response['result']):
            addonItem = json_response['result']['addon']
            if (addonItem['enabled'] is True) and (addonItem['broken'] is False) and (addonItem['type'] == 'xbmc.addon.repository') and (addonItem['addonid'] == 'repository.urepo'):
                displayNotice = False

    if displayNotice:
        xbmc.executebuiltin('Notification("robwebset or URepo Repository Required","github.com/robwebset/repository.robwebset",10000,%s)' % ADDON.getAddonInfo('icon'))
    else:
        # Check if the settings mean we want to notify the user
        notifyRequired = Settings.isNotifyNewQuiz()

    if notifyRequired:
        log("FilmWise: Notify enabled")
        lastViewed = Settings.getLastViewed()
        if lastViewed not in [None, ""]:
            # Find out the current list
            filmWise = FilmWiseCore()
            quizList = filmWise.getQuizList()

            # Now the system has been loaded, we should update the last viewed setting
            if len(quizList) > 0:
                if lastViewed != quizList[0]['link']:
                    # Either display the notification or open the viewer automatically
                    if Settings.isAutoOpenNewQuiz():
                        log("FilmWise: Service auto starting quiz: %s" % quizList[0]['link'])

                        # Now get the details of the selected quiz
                        quizDetails = filmWise.getQuizData(quizList[0]['link'])

                        viewer = FilmWiseViewer.createFilmWiseViewer(quizList[0]['number'], quizList[0]['name'], quizDetails, quizList[0]['solution'])
                        viewer.doModal()

                        # Record that we actually viewed the latest quiz
                        Settings.setLastViewed(quizList[0]['link'])
                    else:
                        quizNum = ''
                        if quizList[0]['number'] > 0:
                            quizNum = " (#%d)" % quizList[0]['number']
                        msg = "%s%s" % (ADDON.getLocalizedString(32013).encode('utf-8'), quizNum)
                        xbmcgui.Dialog().notification(ADDON.getLocalizedString(32001).encode('utf-8'), msg, ICON, 5000, False)
                else:
                    log("FilmWise: Latest quiz already viewed")
            else:
                log("FilmWise: No quiz found")

            del filmWise
    else:
        log("FilmWise: Notify disabled")

    log("FilmWise: Service Ended")
