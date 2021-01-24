import pyautogui,pyaudio,audioop,threading,random,time
from PIL import ImageGrab,ImageOps
from dearpygui.core import *
from dearpygui.simple import *
import configparser
from numpy import *
import random

#Loads Settings
parser = configparser.ConfigParser()
parser.read('settings.ini')

debugmode = parser.getboolean('Settings','debug')
#Coords for fishing spots
coords = []
#Sound Volume
total = 0
max_volume = parser.get('Settings','Volume_Threshold')
#Current Bot State
STATE = "IDLE"
#Coords for important image locations
start_x = int(parser.get('Settings','start_x'))
start_y = int(parser.get('Settings','start_y'))
offset = int(parser.get('Settings','X_Offset'))
bounding_box = (start_x - offset, start_y,start_x,start_y+1)   

#Thread Stopper
stop_button = False

#Generates the areas used for casting
def generate_coords(sender,data):
    global coords,STATE
    amount_of_choords = get_value("Amount Of Spots")
    for n in range(int(amount_of_choords)):
        n = n+1
        temp = []
        log_info(f'[spot:{n}]|Press Enter When Hovered over area you want in the console window',logger="Information")
        input()
        x,y = pyautogui.position()
        temp.append(x)
        temp.append(y)
        coords.append(temp)
        log_info(f'Position:{n} Saved. | {x,y}',logger="Information")

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
        spot = random.choice(coords)
        x,y = spot
        pyautogui.moveTo(x,y,tween=pyautogui.linear)
        time.sleep(0.2)
        pyautogui.mouseDown()
        time.sleep(random.randint(1,2))
        pyautogui.mouseUp()
        log_info(f"Casted to:{x,y}",logger="Information")
        time.sleep(1.0)
        STATE = "CAST"

#Runs the casting function
def cast_hook():
    global STATE   
    while 1:
        if stop_button == False: 
            time.sleep(1)
            if STATE == "CASTING" or STATE == "STARTED":
                cast_hook_to_coords()
            else:
                time.sleep(10)
        else:
            break

#Uses the color of a area to determine when to hold or let go of a mouse. Is calibrated by modifying boundingbox on line 16 as well as the 80 on like 93          
def do_minigame():
    global STATE
    STATE = "SOLVING"
    log_info(f'Attempting Minigame',logger="Information")
    pyautogui.mouseDown()
    pyautogui.mouseUp()
    while 1:
        if stop_button == False:
            value = 0
            image = ImageGrab.grab(bounding_box)
            GrayImage = ImageOps.grayscale(image)
            a = array(GrayImage.getcolors())
            for x in a:
                value = x[0] + x[1]
            if value > 110:
                if debugmode:
                    log_info(f'Mouse Down',logger="Information")
                pyautogui.mouseDown()
            elif value < 80 or total == 0:
                STATE = "CASTING"
                break
            else:
                if debugmode:
                    log_info(f'Mouse Up',logger="Information")
                pyautogui.mouseUp()
        else:
            break

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
    STATE = "STARTED"

def stop(data,sender):
    global stop_button,STATE
    STATE = "STOPPING"
    stop_button = True
    log_info(f'Stopping Hook Manager',logger="Information")
    log_info(f'Stopping Volume Scanner',logger="Information")
    pyautogui.mouseUp()
    STATE = "STOPPED"

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
    global start_x,start_y
    log_info(f'Press Enter in console when hovered over area',logger="Information")
    input()
    meme = pyautogui.position()
    start_x = meme[0]
    start_y = meme[1]
    log_info(f'Updated Tracking Zone to :{start_x},{start_y}',logger="Information")

def set_x_offset(sender,data):
    global offset
    offset = get_value("X Offset")
    log_info(f'Updated X Offest to :{offset}',logger="Information")

def save_settings(sender,data):
    fp = open('settings.ini')
    p = configparser.ConfigParser()
    p.read_file(fp)
    p.set('Settings', 'volume_threshold', str(max_volume))
    p.set('Settings', 'x_offset', str(offset))
    p.set('Settings', 'start_x', str(start_x))
    p.set('Settings', 'start_y', str(start_y))
    p.write(open(f'Settings.ini', 'w'))
    log_info(f'Saved New Settings to settings.ini',logger="Information")

#Settings
set_main_window_size(700,500)
set_style_window_menu_button_position(0)
set_theme("Gold")
set_global_font_scale(1)
set_main_window_resizable(False)

#Creates the DearPyGui Window
with window("Fisherman Window",width = 684,height = 460):
    set_window_pos("Fisherman Window",0,0)
    add_input_int("Amount Of Spots",max_value=10,min_value=0,tip = "Amount of Fishing Spots")
    add_input_int("Set Volume Threshold",max_value=100000,min_value=0,default_value=int(max_volume),tip = "Volume Threshold to trigger catch event")
    add_input_int("X Offset",default_value=offset,callback=set_x_offset,tip = "left / right offset for x coord. Creates a 1 pixel line left or right from x point")
    add_button("Set Fishing Spots",width=130,callback=generate_coords,tip = "Starts function that lets you select fishing spots")
    add_same_line()
    add_button("Set Maximum Volume",callback=save_volume)
    add_same_line()
    add_button("Select Pixel",callback=Setup_Tracking,tip="Sets zone bot tracks for solving fishing minigame")
    add_spacing(count = 2)
    add_button("Start Bot",callback=start)
    add_same_line()
    add_button("Stop Bot",callback = stop)
    add_same_line()
    add_button("Save Settings",callback=save_settings)
    add_logger("Information",log_level=0)
    log_info(f'Loaded Settings. x:{start_x} , y:{start_y} , volume threshold:{max_volume} , x offset:{offset} , Debug Mode:{debugmode}',logger="Information")

threading.Thread(target = Setup_title).start()
start_dearpygui()
