from gui.battle_control.ChatCommandsController import ChatCommandsController
from Avatar import PlayerAvatar
from MarkersStorage import MarkersStorage
from markersUtils import showMarker
import BigWorld
from plugins.Engine.ModUtils import BattleUtils,MinimapUtils,FileUtils,HotKeysUtils,DecorateUtils
from warnings import catch_warnings
from debug_utils import LOG_ERROR, LOG_CURRENT_EXCEPTION, LOG_DEBUG, LOG_NOTE
from gui.WindowsManager import g_windowsManager
from chat_shared import CHAT_COMMANDS

class Focus:

    lastCallback = None
    inBattle = False
    myconfig = {
                "pluginEnable":False,
                "setVName":False,
                "swf_path":"gui/scaleform",
                "maxArrows":3,
                "maxArrowTime":60,
                "delIfUnspotted":True,
                "delIfNotVisible":False,
                "delIfDeath":True,
                "colors":("red", "purple"),
                "swf_file_name":"DirectionIndicator.swf",
                "flash_class":"WGDirectionIndicatorFlash",
                "flash_mc_name":"directionalIndicatorMc",
                "flash_size":(680,680),
                "heightMode":"PIXEL",
                "widthMode":"PIXEL",
                "relativeRadius":0.5,
                "moveFocus":False,
                "focus":False,
                "scaleMode":"NoScale",
                "backgroundAlpha":0.0
                } 
    
    def __init__(self):
        self.pluginEnable = False
        
    def readConfig(self):
        Focus.myconfig = FileUtils.readConfig('scripts/client/plugins/Focus_plugin/config.xml',Focus.myconfig,"Focus")
        self.pluginEnable = Focus.myconfig["pluginEnable"]
        
    def run(self):
        saveOldFuncs()
        injectNewFuncs()
               
    @staticmethod 
    def stopBattle():
        Focus.inBattle = False
        MarkersStorage.clear()
        if Focus.lastCallback is not None:
            try:
                BigWorld.cancelCallback(Focus.lastCallback)
            except:
                pass
            Focus.lastCallback = None   
        
    @staticmethod
    def check():
        if not Focus.inBattle:
            return
        MarkersStorage.updateMarkers(Focus.myconfig)
        Focus.lastCallback = BigWorld.callback(0.7,Focus.check)

    @staticmethod
    def new_handlePublicCommand(self, cmd):
        old_handlePublicCommand(self, cmd)
        if not Focus.inBattle:
            Focus.inBattle = True
            Focus.check()
        receiverID = cmd.getFirstTargetID()
        if receiverID and cmd.showMarkerForReceiver():
            showMarker(receiverID,Focus.myconfig)
        
def saveOldFuncs():
    global old_handlePublicCommand
    DecorateUtils.ensureGlobalVarNotExist('old_handlePublicCommand')
    old_handlePublicCommand = ChatCommandsController._ChatCommandsController__handlePublicCommand

def injectNewFuncs():
    ChatCommandsController._ChatCommandsController__handlePublicCommand = Focus.new_handlePublicCommand
    g_windowsManager.onDestroyBattleGUI += Focus.stopBattle