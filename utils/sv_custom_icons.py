import bpy
import re
import os
import glob
import bpy.utils.previews

DEBUG = True
def logDebug(message, extra=""):
    if DEBUG:
        print(message, extra)

# global variable to store icons in
custom_icons = None

def customIcon(name):
    logDebug("customIcon called")
    global custom_icons

    if name in custom_icons:
        return custom_icons[name].icon_id
    else:
        logDebug("No custom icon found for name: ", name)
        return ""

def loadCustomIcons():
    logDebug("loadIcons called")
    global custom_icons

    custom_icons = bpy.utils.previews.new()

    iconsDir = os.path.join(os.path.dirname(__file__), "../ui/icons")
    iconPattern = "sv_*.png"
    iconPath = os.path.join(iconsDir, iconPattern)
    iconFiles = [os.path.basename(x) for x in glob.glob(iconPath)]
    logDebug(iconFiles)

    iconIDs=[]
    for iconFile in iconFiles:
        iconName = os.path.splitext(iconFile)[0]
        iconID = iconName.upper()
        iconIDs.append(iconID)
        print(iconID)
        custom_icons.load(iconID, os.path.join(iconsDir, iconFile), "IMAGE")

def removeCustomIcons():
    logDebug("unloadIcons called")
    global custom_icons
    bpy.utils.previews.remove(custom_icons)

def register():
    print("wow. registering icons")
    loadCustomIcons()

def unregister():
    print("wow. unregistering icons")
    removeCustomIcons()




