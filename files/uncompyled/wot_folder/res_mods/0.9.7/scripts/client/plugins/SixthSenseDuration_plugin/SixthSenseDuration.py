import FMOD
import SoundGroups
import BigWorld
import ResMgr
import GUI
from gui.Scaleform.Battle import Battle
from gui.WindowsManager import g_windowsManager
from debug_utils import LOG_ERROR, LOG_CURRENT_EXCEPTION, LOG_DEBUG, LOG_NOTE
from functools import partial
from gui.shared.utils.HangarSpace import _HangarSpace
from gui import GUI_SETTINGS
import re
from plugins.Engine.ModUtils import BattleUtils,MinimapUtils,FileUtils,HotKeysUtils,DecorateUtils
import subprocess
import threading
from CurrentVehicle import g_currentVehicle

class SixthSenseDuration:
    myConf = {
              'AudioPath': '/GUI/notifications_FX/cybersport_timer',
              'AudioIsExternal': True,
              'AudioExternal': ['res_mods/{v}/scripts/client/plugins/SixthSenseDuration_plugin/resources/cmdmp3win.exe',
                                'res_mods/{v}/scripts/client/plugins/SixthSenseDuration_plugin/resources/sound.mp3'],
              'AudioRange': 9000,
              'AudioTick': 1000,
              'IconRange': 9000,
              'Volume': 1.0,
              'VolumeType': "gui",
              'TimerColor': "#FF8000",
              'TimerFont': 'verdana_medium.font',
              'TimerPosition': "(round(x / 2) + 120, round(y / 6) + 20, 0.7)",
              'TimerRange': 9000,
              'TimerTick': 1000,
              'TimerZeroDelay': 200,
              'TimerText': "%s",
              'pluginEnable' : True,
              'DisplayOriginalIcon': False,
              'IconInactivePosition': "(round(x / 2) + 120,  20, 0.7)",
              'IconUnspottedPosition': "(round(x / 2) + 120, 20, 0.7)",
              'IconSpottedPosition': "(round(x / 2) + 120, 20, 0.7)",
              'IconInactivePath': "scripts/client/plugins/SixthSenseDuration_plugin/resources/inactive.dds",
              'IconUnspottedPath': "scripts/client/plugins/SixthSenseDuration_plugin/resources/unspotted.dds",
              'IconSpottedPath': "scripts/client/plugins/SixthSenseDuration_plugin/resources/spotted.dds",
              'IconSpottedSize': (52,52),
              'IconUnspottedSize': (52,52),
              'IconInactiveSize': (52,52),
              'materialFX': 'ADD'
    }
    guiCountDown = None
    backupVolume = None 
    hasSixthSense = False
    guiUnspotted = None
    guiInactive = None
    guiSpotted = None
    
    
    def __init__(self):
        self.pluginEnable = False
    
    # --------------- audio ------------- #
    @staticmethod
    def playSound(sound,i):
        if i < 1:
            SixthSenseDuration.sequenceEnd()
            return
        sound.stop()
        sound.play()
        i -= 1
        BigWorld.callback(SixthSenseDuration.myConf['AudioTick']/1000, partial(SixthSenseDuration.playSound,sound,i))
    
    @staticmethod
    def sequenceEnd():
        SoundGroups.g_instance.setVolume(SixthSenseDuration.myConf['VolumeType'],SixthSenseDuration.backupVolume)
    
    
    @staticmethod
    def threadedPlayExtSound():
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        subprocess.Popen(SixthSenseDuration.myConf['AudioExternal'], startupinfo=startupinfo)
    
    @staticmethod
    def playExtSound(i):
        if i < 1:
            return
        try:
            t = threading.Thread(target=SixthSenseDuration.threadedPlayExtSound)
            t.start()
        except:
            pass
        i -= 1
        BigWorld.callback(SixthSenseDuration.myConf['AudioTick']/1000, partial(SixthSenseDuration.playExtSound,i))
    
    @staticmethod
    def new_showSixthSenseIndicator(self, isShow):
        if  SixthSenseDuration.myConf['DisplayOriginalIcon'] or not isShow:
            old_showSixthSenseIndicatorFromSixthSenseDuration(self, isShow)
            
        SixthSenseDuration.initGuiSpotted()
        SixthSenseDuration.initGuiUnspotted()
        SixthSenseDuration.guiSpotted.visible = isShow
        SixthSenseDuration.guiUnspotted.visible = not isShow
        SixthSenseDuration.guiInactive.visible = False
        BigWorld.callback(SixthSenseDuration.myConf['IconRange']/1000,SixthSenseDuration.invertIcons)
            
        SixthSenseDuration.startGuiCountDown()
        
        i = SixthSenseDuration.myConf['AudioRange'] / SixthSenseDuration.myConf['AudioTick']
        if not SixthSenseDuration.myConf['AudioIsExternal']:
            sound = SoundGroups.g_instance.FMODgetSound(SixthSenseDuration.myConf['AudioPath'])
            SixthSenseDuration.backupVolume = SoundGroups.g_instance.getVolume(SixthSenseDuration.myConf['VolumeType'])
            SoundGroups.g_instance.setVolume(SixthSenseDuration.myConf['VolumeType'],SixthSenseDuration.myConf['Volume'])
            SixthSenseDuration.playSound(sound,i)
        else:
            SixthSenseDuration.playExtSound(i)

    @staticmethod
    def invertIcons():
        SixthSenseDuration.guiSpotted.visible = False
        SixthSenseDuration.guiUnspotted.visible = True
    
    # --------------- icon ------------- #
    @staticmethod
    def onChangedVeh():
        for c in g_currentVehicle.item.crew:
            tankcrew = c[1]
            if tankcrew is None:
                continue
            skills = tankcrew.skillsMap
            if 'commander_sixthSense' in skills:
                commander_sixthSense = skills['commander_sixthSense']
                if commander_sixthSense.isActive and commander_sixthSense.isEnable:
                    SixthSenseDuration.hasSixthSense = True
                    return
        SixthSenseDuration.hasSixthSense = False
    
    
    @staticmethod
    def new_spaceDone(self):
        old_spaceDoneFromSixthSenseDuration(self)
        GUI_SETTINGS._GuiSettings__settings['sixthSenseDuration'] = SixthSenseDuration.myConf['IconRange']


    # --------------- countdown ------------- #
    @staticmethod
    def initGuiCountDown():
        if SixthSenseDuration.guiCountDown is not None:
            return
        SixthSenseDuration.fixPosition('TimerPosition')
        SixthSenseDuration.guiCountDown = GUI.Text('')
        GUI.addRoot(SixthSenseDuration.guiCountDown)
        SixthSenseDuration.guiCountDown.widthMode = 'PIXEL'
        SixthSenseDuration.guiCountDown.heightMode = 'PIXEL'
        SixthSenseDuration.guiCountDown.verticalPositionMode = 'PIXEL'
        SixthSenseDuration.guiCountDown.horizontalPositionMode = 'PIXEL'
        SixthSenseDuration.guiCountDown.horizontalAnchor = 'LEFT'
        SixthSenseDuration.guiCountDown.verticalAnchor = 'TOP'
        SixthSenseDuration.guiCountDown.colourFormatting = True
        SixthSenseDuration.guiCountDown.font = SixthSenseDuration.myConf['TimerFont']
        SixthSenseDuration.guiCountDown.visible = False
        SixthSenseDuration.guiCountDown.position = SixthSenseDuration.myConf['TimerPosition']
        
    @staticmethod
    def initGuiSpotted():
        if SixthSenseDuration.guiSpotted is None:
            SixthSenseDuration.fixPosition('IconSpottedPosition')
            SixthSenseDuration.guiSpotted = SixthSenseDuration.createTexture(SixthSenseDuration.myConf['IconSpottedPath'], SixthSenseDuration.myConf['IconSpottedPosition'],SixthSenseDuration.myConf['IconSpottedSize'])
        SixthSenseDuration.guiSpotted.visible = False
        
    @staticmethod
    def initGuiUnspotted():
        if SixthSenseDuration.guiUnspotted is None:
            SixthSenseDuration.fixPosition('IconUnspottedPosition')
            SixthSenseDuration.guiUnspotted = SixthSenseDuration.createTexture(SixthSenseDuration.myConf['IconUnspottedPath'], SixthSenseDuration.myConf['IconUnspottedPosition'],SixthSenseDuration.myConf['IconUnspottedSize'])
        SixthSenseDuration.guiUnspotted.visible = SixthSenseDuration.hasSixthSense    
            
    @staticmethod
    def initGuiInactive():
        if SixthSenseDuration.guiInactive is None:
            SixthSenseDuration.fixPosition('IconInactivePosition')
            SixthSenseDuration.guiInactive = SixthSenseDuration.createTexture(SixthSenseDuration.myConf['IconInactivePath'], SixthSenseDuration.myConf['IconInactivePosition'],SixthSenseDuration.myConf['IconInactiveSize'])
        SixthSenseDuration.guiInactive.visible = not SixthSenseDuration.hasSixthSense

    @staticmethod
    def createTexture(texture,position,size):
        item = GUI.Simple(texture)
        GUI.addRoot(item)
        item.widthMode = 'PIXEL'
        item.heightMode = 'PIXEL'
        item.verticalPositionMode = 'PIXEL'
        item.horizontalPositionMode = 'PIXEL'
        item.horizontalAnchor = 'LEFT'
        item.verticalAnchor = 'TOP'
        item.position = position
        item.size = size
        item.materialFX = SixthSenseDuration.myConf['materialFX']
        return item
    
    @staticmethod
    def startGuiCountDown():
        if SixthSenseDuration.myConf['TimerRange'] == 0:
            return
        if SixthSenseDuration.guiCountDown is None:
            SixthSenseDuration.initGuiCountDown()
        SixthSenseDuration.guiCountDown.visible = True
        max = SixthSenseDuration.myConf['TimerRange'] / 1000
        min = - 1
        diff = - SixthSenseDuration.myConf['TimerTick'] / 1000
        for i in xrange(max,min,diff):
            BigWorld.callback(i, partial(SixthSenseDuration.tickGuiCountDown,max-i))
    
    @staticmethod
    def endGuiCountDown():
        if SixthSenseDuration.guiCountDown is not None:
            SixthSenseDuration.guiCountDown.visible = False
            
    @staticmethod
    def endGuiInactive():
        if SixthSenseDuration.guiInactive is not None:
            SixthSenseDuration.guiInactive.visible = False
            
    @staticmethod
    def endGuiUnspotted():
        if SixthSenseDuration.guiUnspotted is not None:
            SixthSenseDuration.guiUnspotted.visible = False
            
    @staticmethod
    def endGuiSpotted():
        if SixthSenseDuration.guiSpotted is not None:
            SixthSenseDuration.guiSpotted.visible = False
    
    @staticmethod    
    def tickGuiCountDown(i):
        color = SixthSenseDuration.myConf['TimerColor']
        color = '\\c' + re.sub('[^A-Za-z0-9]+', '', color) + 'FF;'
        SixthSenseDuration.guiCountDown.text = color + SixthSenseDuration.myConf['TimerText'] % (str(i))
        if i == 0:
            BigWorld.callback(SixthSenseDuration.myConf['TimerZeroDelay']/1000,SixthSenseDuration.endGuiCountDown )

    @staticmethod
    def fixPosition(type):
        x, y = GUI.screenResolution()
        SixthSenseDuration.myConf[type] = eval(SixthSenseDuration.myConf[type])
    
    def readConfig(self):
        SixthSenseDuration.myConf = FileUtils.readConfig('scripts/client/plugins/SixthSenseDuration_plugin/config.xml',SixthSenseDuration.myConf,"SixthSenseDuration")
        self.pluginEnable =  SixthSenseDuration.myConf['pluginEnable']
        wotv = FileUtils.getWotVersion()
        tmp = []
        for d in SixthSenseDuration.myConf['AudioExternal']:
            tmp.append(d.replace('{v}',wotv))
        SixthSenseDuration.myConf['AudioExternal'] = tmp
        SixthSenseDuration.myConf['IconInactivePath'] = SixthSenseDuration.myConf['IconInactivePath'].replace('{v}',wotv)
        SixthSenseDuration.myConf['IconUnspottedPath'] = SixthSenseDuration.myConf['IconUnspottedPath'].replace('{v}',wotv)
        SixthSenseDuration.myConf['IconSpottedPath'] = SixthSenseDuration.myConf['IconSpottedPath'].replace('{v}',wotv)
        
        
    
    def run(self):
        saveOldFuncs()
        injectNewFuncs()
        
def saveOldFuncs():
    global old_showSixthSenseIndicatorFromSixthSenseDuration,old_spaceDoneFromSixthSenseDuration
    DecorateUtils.ensureGlobalVarNotExist('old_showSixthSenseIndicatorFromSixthSenseDuration')
    DecorateUtils.ensureGlobalVarNotExist('old_spaceDoneFromSixthSenseDuration')
    old_showSixthSenseIndicatorFromSixthSenseDuration = Battle.showSixthSenseIndicator
    old_spaceDoneFromSixthSenseDuration = _HangarSpace._HangarSpace__spaceDone
    
def injectNewFuncs():
    Battle.showSixthSenseIndicator = SixthSenseDuration.new_showSixthSenseIndicator
    _HangarSpace._HangarSpace__spaceDone = SixthSenseDuration.new_spaceDone
    g_windowsManager.onInitBattleGUI += SixthSenseDuration.initGuiCountDown
    g_windowsManager.onInitBattleGUI += SixthSenseDuration.initGuiInactive
    g_windowsManager.onInitBattleGUI += SixthSenseDuration.initGuiSpotted
    g_windowsManager.onInitBattleGUI += SixthSenseDuration.initGuiUnspotted
    g_windowsManager.onDestroyBattleGUI += SixthSenseDuration.endGuiCountDown
    g_windowsManager.onDestroyBattleGUI += SixthSenseDuration.endGuiInactive
    g_windowsManager.onDestroyBattleGUI += SixthSenseDuration.endGuiSpotted
    g_windowsManager.onDestroyBattleGUI += SixthSenseDuration.endGuiUnspotted
    g_currentVehicle.onChanged += SixthSenseDuration.onChangedVeh
