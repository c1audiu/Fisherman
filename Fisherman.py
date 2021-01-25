import pyautogui,pyaudio,audioop,threading,time,win32api,configparser,mss,mss.tools
from PIL import ImageOps,Image
from dearpygui.core import *
from dearpygui.simple import *
from numpy import *
import random

#Loads Settings
parser = configparser.ConfigParser()
parser.read('settings.ini')
debugmode = parser.getboolean('Settings','debug')
max_volume = parser.get('Settings','Volume_Threshold')
start_x = int(parser.get('Settings','start_x'))
start_y = int(parser.get('Settings','start_y'))


minimum_time = float(parser.get('Settings','minimum_pull'))
maximum_time = float(parser.get('Settings','maximum_pull'))

#Coords for fishing spots
coords = []

#Sound Volume
total = 0

#Current Bot State
STATE = "IDLE"

#Coords for important image locations
bounding_box = (start_x,start_y,start_x+1,start_y+1)

#Thread Stopper
stop_button = False

#Stuff for mouse events
state_left = win32api.GetKeyState(0x01)
state_right = win32api.GetKeyState(0x02)

##########################################################
#
#   These Functions handle bot state / minigame handling
#
##########################################################

#Scans the current input volume
def check_volume():
    global total,STATE,max_volume,stop_button
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,channels=2,rate=44100,input=True,frames_per_buffer=1024)
    current_section = 0
    while 1:
        if stop_button == False:
            total=0
            for i in range(0,2):
                data=stream.read(1024)
                if True:
                    reading=audioop.max(data, 2)
                    total=total+reading
                    if total > max_volume and STATE != "SOLVING" and STATE != "DELAY" and STATE != "CASTING":
                        do_minigame()
        else:
            break

#Cast the hook to random location selected
def cast_hook_to_coords():
    global STATE
    if stop_button == False:
        pyautogui.mouseUp()
        spot = random.choice(coords)
        x,y = spot
        pyautogui.moveTo(x,y,tween=pyautogui.linear)
        time.sleep(0.2)
        pyautogui.mouseDown()
        time.sleep(random.uniform(0.2,0.5))
        pyautogui.mouseUp()
        log_info(f"Casted to:{x,y}",logger="Information")
        time.sleep(5.0)
        STATE = "CAST"

#Runs the casting function
def cast_hook():
    global STATE   
    while 1:
        if stop_button == False: 
            time.sleep(1)
            if STATE == "CASTING" or STATE == "STARTED":
                cast_hook_to_coords()
            elif STATE == "CAST":
                time.sleep(10)
                if STATE == "CAST":
                    STATE = "CASTING"
            else:
                time.sleep(10)
        else:
            break

#Gets Color Value
def GET_VALUE(bounding_box1):
    image = mss.mss().grab(bounding_box1)
    img = Image.frombytes("RGB", image.size, image.bgra, "raw", "BGRX")
    GrayImage = ImageOps.grayscale(img)
    a = array(GrayImage.getcolors())
    value = a.sum()
    print(value)
    return value

#Uses the color of a area to determine when to hold or let go of a mouse. Is calibrated by modifying boundingbox on line 16 as well as the 80 on like 93          
def do_minigame():
    global STATE,minimum_time,maximum_time
    time.sleep(0.5)
    if STATE != "CASTING" and STATE != "STARTED":
        STATE = "SOLVING"
        log_info(f'Attempting Minigame',logger="Information")
        pyautogui.mouseDown()
        pyautogui.mouseUp()
        while 1:
            if stop_button == False:
                value = GET_VALUE(bounding_box)
                if value > 150:
                    if debugmode is True:
                        log_info(f'Mouse Down',logger="Information")
                    pyautogui.mouseDown()
                    time.sleep(random.uniform(minimum_time,maximum_time))
                elif value < 80 or total < 10:
                    STATE = "CASTING"
                    break
                else:
                    if debugmode is True:
                        log_info(f'Mouse Up',logger="Information")
                    pyautogui.mouseUp()
            else:
                break

##########################################################
#
#   These Functions are all Callbacks used by DearPyGui
#
##########################################################

#Generates the areas used for casting
def generate_coords(sender,data):
    global coords,STATE,state_left
    amount_of_choords = get_value("Amount Of Spots")
    for n in range(int(amount_of_choords)):
        n = n+1
        temp = []
        log_info(f'[spot:{n}]|Press Spacebar over the spot you want',logger="Information")
        time.sleep(1)
        while True:
            a = win32api.GetKeyState(0x20)  
            if a != state_left:
                state_left = a 
                if a < 0:
                    break
            time.sleep(0.001) 
        x,y = pyautogui.position()
        temp.append(x)
        temp.append(y)
        coords.append(temp)
        log_info(f'Position:{n} Saved. | {x,y}',logger="Information")

#Starts the bots threads
def start(data,sender):
    global max_volume,stop_button,STATE
    STATE = "STARTING"
    stop_button = False
    volume_manager = threading.Thread(target = check_volume)
    hook_manager = threading.Thread(target = cast_hook)
    if stop_button == False:
        max_volume = get_value("Set Volume Threshold")
        if len(coords) == 0:
            log_info(f'Please Select Fishing Coords first',logger="Information")
            return
        else:
            volume_manager.start()
            log_info(f'Volume Scanner Started',logger="Information")
            hook_manager.start()
            log_info(f'Hook Manager Started',logger="Information")
            log_info(f'Bot Started',logger="Information")
    STATE = "STARTED"

#Stops the bot and closes active threads
def stop(data,sender):
    global stop_button,STATE
    STATE = "STOPPING"
    stop_button = True
    log_info(f'Stopping Hook Manager',logger="Information")
    log_info(f'Stopping Volume Scanner',logger="Information")
    pyautogui.mouseUp()
    STATE = "STOPPED"
    log_info(f'Stopped Bot',logger="Information")

#Updates Bot Volume
def save_volume(sender,data):
    global max_volume
    max_volume = get_value("Set Volume Threshold")
    log_info(f'Max Volume Updated to :{max_volume}',logger="Information")

#Title Tracking
def Setup_title():
    while 1:
        set_main_window_title(f"Fisherman | Albion Online Bot | Status:{STATE} | Current Volume:{max_volume} \ {total} |")
        time.sleep(0.1)

#Lets you pick Screen Coords
def Setup_Tracking(sender,data):
    global start_x,start_y,state_right
    log_info(f'Right click over the area you want to track',logger="Information")
    while True:
        b = win32api.GetKeyState(0x02)
        if b != state_right:
            state_right = b
            if b < 0:
                break
            time.sleep(0.001)
    meme = pyautogui.position()
    start_x = meme[0]
    start_y = meme[1]
    log_info(f'Updated Tracking Zone to :{start_x},{start_y}',logger="Information")

def save_minimum_pull(sender,data):
    global minimum_time
    minimum_time = get_value("Minimum Pull Time")
    minimum_time = round(minimum_time,2)
    log_info(f'Updated Minimum Pull Time to :{minimum_time}',logger="Information")

def save_maximum_pull(sender,data):
    global maximum_time
    maximum_time = get_value("Maximum Pull Time")
    maximum_time = round(maximum_time,2)
    log_info(f'Updated Maximum Pull Time to :{maximum_time}',logger="Information")

#Saves settings to settings.ini
def save_settings(sender,data):
    fp = open('settings.ini')
    p = configparser.ConfigParser()
    p.read_file(fp)
    p.set('Settings', 'volume_threshold', str(max_volume))
    p.set('Settings', 'start_x', str(start_x))
    p.set('Settings', 'start_y', str(start_y))
    p.set('Settings', 'minimum_pull', str(minimum_time))
    p.set('Settings', 'maximum_pull', str(maximum_time))
    p.write(open(f'Settings.ini', 'w'))
    log_info(f'Saved New Settings to settings.ini',logger="Information")

#Settings for DearPyGui window
set_main_window_size(700,500)
set_style_window_menu_button_position(0)
set_theme("Gold")
set_global_font_scale(1)
set_main_window_resizable(False)

#Creates the DearPyGui Window
with window("Fisherman Window",width = 684,height = 460):
    set_window_pos("Fisherman Window",0,0)
    add_input_int("Amount Of Spots",max_value=10,min_value=0,tip = "Amount of Fishing Spots")
    add_input_int("Set Volume Threshold",max_value=100000,min_value=0,default_value=int(max_volume),callback = save_volume ,tip = "Volume Threshold to trigger catch event")
    add_input_float("Maximum Pull Time",min_value=0,max_value=3,default_value=maximum_time,callback=save_maximum_pull,tip = "Max pulling time in fish minigame")
    add_input_float("Minimum Pull Time",min_value=0,max_value=3,default_value=minimum_time,callback=save_minimum_pull,tip = "Min pulling time in fish minigame")
    add_spacing(count = 3)
    add_button("Set Fishing Spots",width=130,callback=generate_coords,tip = "Starts function that lets you select fishing spots")
    add_same_line()
    add_button("Select Pixel",callback=Setup_Tracking,tip="Sets zone bot tracks for solving fishing minigame")
    add_spacing(count = 5)
    add_button("Start Bot",callback=start,tip = "Starts the bot")
    add_same_line()
    add_button("Stop Bot",callback = stop,tip = "Stops the bot")
    add_same_line()
    add_button("Save Settings",callback=save_settings,tip = "Saves bot settings to settings.ini")
    add_spacing(count = 5)
    add_logger("Information",log_level=0)
    log_info(f'Loaded Settings. x:{start_x} , y:{start_y} , volume threshold:{max_volume} , Debug Mode:{debugmode}',logger="Information")

threading.Thread(target = Setup_title).start()
start_dearpygui()
