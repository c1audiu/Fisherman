import pyautogui,pyaudio,audioop,threading,time,win32api,configparser,mss,mss.tools,cv2,numpy
from dearpygui.core import *
from dearpygui.simple import *
import random

#Loads Settings
parser = configparser.ConfigParser()
parser.read('settings.ini')
debugmode = parser.getboolean('Settings','debug')
max_volume = parser.get('Settings','Volume_Threshold')
screen_area = parser.get('Settings','tracking_zone')

screen_area = screen_area.strip('(')
screen_area = screen_area.strip(')')
cordies = screen_area.split(',')
screen_area = int(cordies[0]),int(cordies[1]),int(cordies[2]),int(cordies[3])

#screen_area = x1,y1,x2,y2
#Coords for fishing spots
coords = []

#Sound Volume
total = 0

#Current Bot State
STATE = "IDLE"

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

def get_new_spot():
    return random.choice(coords)

#Runs the casting function
def cast_hook():
    global STATE
    while 1:
        if stop_button == False:
            if STATE == "CASTING" or STATE == "STARTED":
                time.sleep(2.6)
                pyautogui.mouseUp()
                x,y = get_new_spot()
                pyautogui.moveTo(x,y,tween=pyautogui.linear,duration=0.2)
                time.sleep(0.2)
                pyautogui.mouseDown()
                time.sleep(random.uniform(0.2,0.5))
                pyautogui.mouseUp()
                log_info(f"Casted towards:{x,y}",logger="Information")
                time.sleep(2.5)
                STATE = "CAST"
            elif STATE == "CAST":
                time.sleep(20)
                if STATE == "CAST":
                    log_info(f"Seems to be stuck on cast. Recasting",logger="Information")
                    STATE = "CASTING"
                    pyautogui.mouseUp()
                    cast_hook()
        else:
            break

#Uses obj detection with OpenCV to find and track bobbers left / right coords
def do_minigame():
    global STATE
    if STATE != "CASTING" and STATE != "STARTED":
        STATE = "SOLVING"
        log_info(f'Attempting Minigame',logger="Information")
        pyautogui.mouseDown()
        pyautogui.mouseUp()
        #Initial scan. Waits for bobber to appear
        time.sleep(0.5)
        valid,location,size = Detect_Bobber()
        if valid == "TRUE":
            while 1:
                valid,location,size = Detect_Bobber()
                if valid == "TRUE":
                    if location[0] < size / 2:
                        pyautogui.mouseDown()
                    else:
                        pyautogui.mouseUp()
                else:
                    if STATE != "CASTING":
                        STATE = "CASTING"
                        pyautogui.mouseUp()
                        break
        else:
            STATE = "CASTING"

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

#Sets tracking zone for image detection
def Grab_Screen(sender,data):
    global screen_area
    state_left = win32api.GetKeyState(0x20)
    image_coords = []
    log_info(f'Please hold and drag space over tracking zone (top left to bottom right)',logger="Information")
    while True:
        a = win32api.GetKeyState(0x20)
        if a != state_left:  # Button state changed
            state_left = a
            if a < 0:
                x,y = pyautogui.position()
                image_coords.append([x,y])
            else:
                x,y = pyautogui.position()
                image_coords.append([x,y])
                break
        time.sleep(0.001)
    start_point = image_coords[0]
    end_point = image_coords[1]
    screen_area = start_point[0],start_point[1],end_point[0],end_point[1]
    log_info(f'Updated tracking area to {screen_area}',logger="Information")

#Detects bobber in tracking zone using openCV
def Detect_Bobber():
    start_time = time.time()
    with mss.mss() as sct:
        base = numpy.array(sct.grab(screen_area))
        base = numpy.flip(base[:, :, :3], 2)  # 1
        base = cv2.cvtColor(base, cv2.COLOR_RGB2BGR)
        bobber = cv2.imread('bobber.png')
        bobber = numpy.array(bobber, dtype=numpy.uint8)
        bobber = numpy.flip(bobber[:, :, :3], 2)  # 1
        bobber = cv2.cvtColor(bobber, cv2.COLOR_RGB2BGR)
        result = cv2.matchTemplate(base,bobber,cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        if max_val > 0.5:
            print(f"Bobber Found!. Match certainty:{max_val}")
            print("%s seconds to calculate" % (time.time() - start_time))
            return ["TRUE",max_loc,base.shape[1]]
        else:
            print(f"Bobber not found. Match certainty:{max_val}")
            print("%s seconds to calculate" % (time.time() - start_time))
            return ["FALSE",max_loc,base.shape[1]]

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

#Saves settings to settings.ini
def save_settings(sender,data):
    fp = open('settings.ini')
    p = configparser.ConfigParser()
    p.read_file(fp)
    p.set('Settings', 'volume_threshold', str(max_volume))
    p.set('Settings','tracking_zone',str(screen_area))
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
    add_spacing(count = 3)
    add_button("Set Fishing Spots",width=130,callback=generate_coords,tip = "Starts function that lets you select fishing spots")
    add_same_line()
    add_button("Set Tracking Zone",callback=Grab_Screen,tip="Sets zone bot tracks for solving fishing minigame")
    add_spacing(count = 5)
    add_button("Start Bot",callback=start,tip = "Starts the bot")
    add_same_line()
    add_button("Stop Bot",callback = stop,tip = "Stops the bot")
    add_same_line()
    add_button("Save Settings",callback=save_settings,tip = "Saves bot settings to settings.ini")
    add_spacing(count = 5)
    add_logger("Information",log_level=0)
    log_info(f'Loaded Settings. Volume Threshold:{max_volume},Tracking Zone:{screen_area},Debug Mode:{debugmode}',logger="Information")

threading.Thread(target = Setup_title).start()
start_dearpygui()
