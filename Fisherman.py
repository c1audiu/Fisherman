import pyautogui,numpy,cv2,pyaudio,audioop,threading,random,ctypes,time,win32gui,win32con
from PIL import ImageGrab,ImageOps
from dearpygui.core import *
from dearpygui.simple import *
from numpy import *
import random

#Coords for fishing spots
coords = []
#Sound Volume
total = 0
#Current Bot State
STATE = "IDLE"
#Coords for important image locations
start_x = 1284 
start_y = 739
bounding_box = (start_x - 60, start_y,start_x,start_y+1)   
max_volume = 0

#Generates the areas used for casting
def generate_coords(sender,data):
    global coords,STATE
    amount_of_choords = get_value("Amount Of Spots")
    for n in range(int(amount_of_choords)):
        n = n+1
        temp = []
        log_info(f'[spot:{n}]|Press Enter When Hovered over area you want',logger="Information")
        input()
        x,y = pyautogui.position()
        temp.append(x)
        temp.append(y)
        coords.append(temp)
        log_info(f'Position:{n} Saved. | {x,y}',logger="Information")
        STATE = "CASTING"
    time.sleep(5)

#Scans the current input volume
def check_volume():
    global total,STATE,max_volume
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,channels=2,rate=44100,input=True,frames_per_buffer=1024)
    current_section = 0
    while 1:
        total=0
        for i in range(0,2):
            data=stream.read(1024)
            if True:
                reading=audioop.max(data, 2)
                total=total+reading
                if total > max_volume and STATE != "SOLVING" and STATE != "DELAY" and STATE != "CASTING":
                    do_minigame()

#Cast the hook to random location selected
def cast_hook_to_coords():
    global STATE
    spot = random.choice(coords)
    x,y = spot
    pyautogui.moveTo(x,y,tween=pyautogui.linear)
    time.sleep(0.2)
    pyautogui.mouseDown()
    time.sleep(random.randint(1,2))
    pyautogui.mouseUp()
    print(f"Casted to:{x,y}")
    time.sleep(1.0)
    STATE = "CAST"

#Runs the casting function
def cast_hook():
    global STATE    
    while 1:
        time.sleep(1)
        if STATE == "CASTING":
            cast_hook_to_coords()
        else:
            time.sleep(10)

#Uses the color of a area to determine when to hold or let go of a mouse. Is calibrated by modifying boundingbox on line 16 as well as the 80 on like 93          
def do_minigame():
    global STATE
    STATE = "SOLVING"
    log_info(f'Attempting Minigame',logger="Information")
    pyautogui.mouseDown()
    pyautogui.mouseUp()
    while 1:
        value = 0
        image = ImageGrab.grab(bounding_box)
        GrayImage = ImageOps.grayscale(image)
        a = array(GrayImage.getcolors())
        for x in a:
            value = x[0] + x[1]
        if value > 110:
            #log_info(f'Mouse Down',logger="Information") Debugging Tool. Uncomment to see how the solver is working
            pyautogui.mouseDown()
        elif value < 80 or total == 0:
            STATE = "CASTING"
            break
        else:
            #log_info(f'Mouse Up',logger="Information") Debugging Tool. Uncomment to see how the solver is working
            pyautogui.mouseUp()

#Starts the bots threads
def start(data,sender):
    global max_volume
    max_volume = get_value("Set Volume Threshold")
    if len(coords) == 0:
        log_info(f'Please Select Fishing Coords first',logger="Information")
        return
    else:
        threading.Thread(target = check_volume).start()
        log_info(f'Volume Scanner Started',logger="Information")
        threading.Thread(target = cast_hook).start()
        log_info(f'Hook Manager Started',logger="Information")
#Updates Bot Volume
def save_volume(sender,data):
    global max_volume
    max_volume = get_value("Set Volume Threshold")
    log_info(f'Max Volume Updated to :{max_volume}',logger="Information")

#Title Tracking
def Setup_title():
    while 1:
        set_main_window_title(f"Fisherman | Albion Online Bot | Status:{STATE} | Current Volume:{max_volume} \ {total} |")
        time.sleep(1)

#Settings
set_main_window_size(700,500)
set_style_window_menu_button_position(0)
set_theme("Red")
set_global_font_scale(1)
set_main_window_resizable(False)

#Creates the DearPyGui Window
with window("Fisherman Window",width = 687,height = 460):
    set_window_pos("Fisherman Window",0,0)
    add_input_int("Amount Of Spots",max_value=10,min_value=0)
    add_input_int("Set Volume Threshold",max_value=100000,min_value=0)
    add_button("Set Fishing Spots",width=130,callback=generate_coords)
    add_button("Set Maximum Volume",callback=save_volume)
    add_button("Start Bot",callback=start)
    add_logger("Information",log_level=0)

threading.Thread(target = Setup_title).start()
start_dearpygui()
