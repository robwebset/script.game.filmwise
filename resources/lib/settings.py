# -*- coding: utf-8 -*-
import os
import xbmc
import xbmcaddon
import xbmcvfs

ADDON = xbmcaddon.Addon(id='script.game.filmwise')
ADDON_ID = ADDON.getAddonInfo('id')
CWD = ADDON.getAddonInfo('path').decode("utf-8")


# Common logging module
def log(txt, loglevel=xbmc.LOGDEBUG):
    if (ADDON.getSetting("logEnabled") == "true") or (loglevel != xbmc.LOGDEBUG):
        if isinstance(txt, str):
            txt = txt.decode("utf-8")
        message = u'%s: %s' % (ADDON_ID, txt)
        xbmc.log(msg=message.encode("utf-8"), level=loglevel)


def os_path_join(dir, file):
    # Check if it ends in a slash
    if dir.endswith("/") or dir.endswith("\\"):
        # Remove the slash character
        dir = dir[:-1]

    # Convert each argument - if an error, then it will use the default value
    # that was passed in
    try:
        dir = dir.decode("utf-8")
    except:
        pass
    try:
        file = file.decode("utf-8")
    except:
        pass
    return os.path.join(dir, file)


# Checks if a directory exists (Do not use for files)
def dir_exists(dirpath):
    # There is an issue with password protected smb shares, in that they seem to
    # always return false for a directory exists call, so if we have a smb with
    # a password and user name, then we return true
    if '@' in dirpath:
        return True

    directoryPath = dirpath
    # The xbmcvfs exists interface require that directories end in a slash
    # It used to be OK not to have the slash in Gotham, but it is now required
    if (not directoryPath.endswith("/")) and (not directoryPath.endswith("\\")):
        dirSep = "/"
        if "\\" in directoryPath:
            dirSep = "\\"
        directoryPath = "%s%s" % (directoryPath, dirSep)
    return xbmcvfs.exists(directoryPath)


##############################
# Stores Various Settings
##############################
class Settings():

    @staticmethod
    def getLastViewed():
        return ADDON.getSetting("lastViewedUrl")

    @staticmethod
    def setLastViewed(url):
        ADDON.setSetting("lastViewedUrl", url)

    @staticmethod
    def isSaveUserAnswers():
        return ADDON.getSetting("saveUserAnswers") == 'true'

    @staticmethod
    def isNotifyNewQuiz():
        return ADDON.getSetting("notifyNewQuiz") == 'true'

    @staticmethod
    def isAutoOpenNewQuiz():
        return ADDON.getSetting("autoOpenNewQuiz") == 'true'

    @staticmethod
    def getTempLocation():
        tmpdestination = xbmc.translatePath('special://profile/addon_data/%s/temp' % ADDON_ID).decode("utf-8")

        # Make sure the directory exists
        if not dir_exists(xbmc.translatePath('special://profile/addon_data/%s' % ADDON_ID).decode("utf-8")):
            xbmcvfs.mkdir(xbmc.translatePath('special://profile/addon_data/%s' % ADDON_ID).decode("utf-8"))
        if not dir_exists(tmpdestination):
            xbmcvfs.mkdir(tmpdestination)
        return tmpdestination

    @staticmethod
    def getCheatLocation():
        res_dir = xbmc.translatePath(os.path.join(CWD, 'resources').encode("utf-8")).decode("utf-8")
        cheatsFile = os.path.join(res_dir, 'cheats.ini')

        # Make sure the file exists
        if not os.path.exists(cheatsFile):
            cheatsFile = None

        return cheatsFile
