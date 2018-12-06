from screen_processor import ScreenProcessor, numpy_flip, save_debugg_screenshot
from concurrent.futures import ThreadPoolExecutor
from artibuff_scrape import Artibuff_Card
from tier_list_scrape import read_tier_text, Tier_List_Card
from market_scrape import get_prices
from canvas_selection import run_canvas
import os
import sys
import pickle
import webbrowser
import time
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
from mss import mss

path_root = os.path.dirname(sys.modules['__main__'].__file__)
def path(filename):
    global path_root
    return os.path.join(path_root, filename)

def OpenUrl(opt=''):
    if opt=='issue':
        webbrowser.open_new('https://github.com/eoakley/artifacthelper/issues')
    else:
        webbrowser.open_new('https://github.com/eoakley/artifacthelper')

def load_pickle(file_name="card_dict.pkl"):
    try:
        with open(file_name, 'rb') as handle:
            b = pickle.load(handle)
        return b
    except Exception as err:
        print("Error loading pickle")
        print(err)

def fix_dict(d):
    '''...And One for Me   ->    ...And One For Me'''
    if type(d) == str:
        return ' '.join([a.capitalize() for a in d.split(' ')])
    d2 = {}
    for key in d:
        key2 = ' '.join([a.capitalize() for a in key.split(' ')])
        d2[key2] = d[key]
    return d2
    
executor = ThreadPoolExecutor(40)

stats = fix_dict(load_pickle(path('resources/card_dict.pkl')))

tiers = fix_dict(read_tier_text(path('tier_list.txt')))

#tiers got updated, poor fix for now:

prices = None

sp = None

label_list = []
flag_swap = 1
coisas = []

launcher_x, launcher_y =  0, 0
overlay_x, overlay_y = 0, 0
x_drag, y_drag = None, None

flag_auto_hide = False

flag_auto_scan = False

bg_color = 'magenta'

btn_auto_scan = None

ss_path = path('screenshot_draft.png')
custom_grid_path = path("custom_grid.npy")

def compare_images(img, img2):
    dif = np.mean(np.abs(img.astype(int) - img2.astype(int)))
    return dif

########### TODO: need to update this
def get_draft_state(screen_width, screen_height):
    with mss() as sct:
        mon = sct.monitors[1]

        monitor = {
            "top": mon["top"] + 48*screen_height//1080,
            "left": mon["left"] + 1385*screen_width//1920,
            "width": 56*screen_width//1920,
            "height": 52*screen_height//1080,
            "mon": 1,
        }

        # Grab the data
        img = sct.grab(monitor)

        return numpy_flip(img)

def destroy_list(ll, root):
    #destroy list if exists:
    for ele in ll:
        try:
            ele.destroy()
        except tk.TclError as e:
            pass
    
    ll = []
    root.update()

def auto_hide(ll, root, screen_width, screen_height):
    global flag_auto_hide
    thresh = 5
    img2 = get_draft_state(screen_width, screen_height)
    
    while(1):
        #checks pixels
        img = get_draft_state(screen_width, screen_height)
        
        #compare
        dif = compare_images(img, img2)
        
        #mouse
        mx, my = root.winfo_pointerxy()
        
        inside = mx >= (1385-40)*screen_width//1920 and mx <= (1385 + 56 +20)*screen_width//1920 and my >= (48 -20)*screen_height//1080 and my <= (48 + 52+20)*screen_height//1080
        if dif > thresh and not inside:
            destroy_list(ll, root)
            img2 = img
            flag_auto_hide = False
            break
        
        #sleeps
        time.sleep(.2)

def btnProcessScreen(ll_cur, root, screen_width, screen_height, auto_scan=False):
    global flag_auto_hide, sp, flag_swap

    #auto hide disabled for now
    #if not flag_auto_hide:
        #executor.submit(auto_hide, ll_cur, root, screen_width, screen_height)
        #flag_auto_hide = True
        
    #load custom grid
    if os.path.exists(custom_grid_path):
        custom_grid = list(np.load(custom_grid_path))
        sp.custom_grid = custom_grid

    ss, (cards, scores, card_grid, borders) = sp.process_screen()

    ll = []
    #destroy_list(ll, root)

    # from_top, from_left = 139*screen_height//1080, 68*screen_width//1920
    # space_h, space_w = 344*screen_height//1080, 211*screen_width//1920
    
    #if all cards are empty cards or error in process screen,
    #show error in UI
    if len(cards) == 0 or cards.count('Empty Card') == 12:
        label_height = 80
        label_width = 240

        txt = "Error detecting cards.\nAre you on draft screen?\nTry Customizing Grid."
        #save ss for debugg
        if len(card_grid) > 1:
            save_debugg_screenshot(ss, card_grid, borders)
            txt += "\nSaved screenshot_debugg.png \non installation dir."
            label_height=160
            label_width=340
            
        l = tk.Label(root, text=txt, justify='center', bg='#222', 
                    fg="#DDD", font=("Helvetica 14"), borderwidth=3, relief="solid")
        
        l.place(x = screen_width//2-label_width, y = 120, width=label_width, height=label_height)
        
        ll.append(l)

        destroy_list(ll_cur, root)
        for ele in ll:
            ll_cur.append(ele)
        return None

    #save_debugg_screenshot(ss, card_grid, borders)
    for row in range(2):
        for col in range(6):
            #quatro cantos da carta
            top, left, bottom, right = card_grid[row, col, :]
            card_width = right-left
            
            card_name = fix_dict(cards[row*6+col])
            card_score = scores[row*6+col]

            if card_name == 'Empty Slot' or card_name == 'Empty Card':
                continue
                
            try:
                wr = stats[card_name]['str']
            except:
                wr = ''

            try:
                tier = tiers[card_name]
            except:
                tier = ''

            try:
                price = prices[card_name]['sell_price']
            except:
                price = ''
                
            if card_name not in stats.keys():
                print('Card not found:', card_name)
                continue
                
            elif card_name not in tiers.keys():
                tier = '?'
                
            max_len_name = 20
            card_name_str = card_name
            if len(card_name) > max_len_name:
                card_name_str = card_name[:max_len_name-2] + '..'
            txt = card_name_str.rjust(20) + '\n' + str(wr).rjust(20) + '\n' + (str(tier)  + ' ' + price).rjust(20)
            l = tk.Label(root, text=txt, justify='right', bg='#222', 
                      fg="#DDD", font=("Helvetica 10 bold"), borderwidth=3, relief="solid")
            
            # print(row, col, 'label start x:' ,left+card_width)
            l.place(anchor='ne', x = left+card_width, y = top, width=145, height=61)
            
            ll.append(l)

    destroy_list(ll_cur, root)
    for ele in ll:
        ll_cur.append(ele)
    return
                
def auto_scan(ll, root, screen_width, screen_height):
    global flag_swap
    """Automatic scan for new cards"""
    while(1):
        if flag_auto_scan == False or flag_swap == 0:
            #print("Closing auto scan")
            break

        #print("Auto Scanning")
        btnProcessScreen(ll, root, screen_width, screen_height)
        
        #sleeps
        time.sleep(0.5)

def call_auto_scan(ll, root, screen_width, screen_height, btn_auto_scan):
    global flag_auto_scan
    flag_auto_scan = not flag_auto_scan
    #print("Auto Scan is on?", flag_auto_scan)
    if flag_auto_scan:
        btn_auto_scan['text'] = '[on] Auto Scan'
    else:
        btn_auto_scan['text'] = '[off] Auto Scan'

    if flag_auto_scan == False:
        return

    executor.submit(auto_scan, ll, root, screen_width, screen_height)

def call_run_canvas(root):
    print('Screenshot of the game')
    try:
        ss = sp.grab_artifact()
    except:
        print('Could not SS the game.')

    #save ss to file

    im = Image.fromarray(ss)
    im.save(ss_path)
    
    print("SS saved to file", ss_path)

    print('Launching Grid Selector')
    executor.submit(run_canvas, root, ss_path, custom_grid_path)

def StartMove(event):
    #print("ini move")
    global x_drag,y_drag
    x_drag = event.x
    y_drag = event.y

def StopMove(root,event):
    #print("end move")
    global x_drag,y_drag,overlay_x,overlay_y
    x_drag = None
    y_drag = None
    overlay_x, overlay_y = root.winfo_x(), root.winfo_y()

def OnMotion(root, event):
    #print("on motion")
    global x_drag,y_drag
    deltax = event.x - x_drag
    deltay = event.y - y_drag
    x = root.winfo_x() + deltax
    y = root.winfo_y() + deltay
    root.geometry("+%s+%s" % (x, y))


def swap_window(root, screen_width, screen_height, first_time=False):
    global coisas, flag_swap, flag_auto_hide, label_list, sp, launcher_x , launcher_y, overlay_x, overlay_y, prices, btn_auto_scan
    flag_auto_hide = False

    #print("Last position:")
    #print(root.winfo_x(), root.winfo_y())
    
    #clean stuff
    destroy_list(coisas, root)
    destroy_list(label_list, root)
    
    if flag_swap == 0:
        # SCAN OVERLAY WINDOW
        launcher_x , launcher_y = root.winfo_x(), root.winfo_y()

        root.call('wm', 'attributes', '.', '-topmost', '1')
        root.call('wm', 'attributes', '.', '-transparentcolor', bg_color)
        root.title("Artifact Helper")
        print("Creating overlay with size:", screen_width, screen_height)
        root.geometry("%dx%d+%d+%d" % (screen_width, screen_height, overlay_x,overlay_y))
        root.configure(background=bg_color)
        root.lift()
        root.overrideredirect(1) #Remove border        

        logo = ImageTk.PhotoImage(Image.open(path('resources/banner_1.png')))
        btnImgScan = ImageTk.PhotoImage(Image.open(path('resources/btn_scan_1.png')))
        btnImgMove = ImageTk.PhotoImage(Image.open(path('resources/btn_move.png')))

        lg = tk.Label(root, image=logo, borderwidth=0, relief="solid")
        lg.image = logo
        lg.place(x = 400, y = 1, width=816, height=105)
        coisas.append(lg)

        top_border = 60
        left_space = 860
        b = tk.Button(root, text="Scan Cards", command=lambda: btnProcessScreen(label_list, root, screen_width, screen_height), bg='#CCC', relief='flat', borderwidth=0)
        b.config(image=btnImgScan)
        b.image = btnImgScan
        b.place(x = left_space-96, y = top_border-32, width=166, height=57)
        coisas.append(b)

        btn_auto_scan = tk.Button(root, text='[off] Auto Scan', command=lambda: call_auto_scan(label_list, root, screen_width, screen_height, btn_auto_scan), bg='#CCC')
        if flag_auto_scan:
            btn_auto_scan['text'] = '[on] Auto Scan'
        else:
            btn_auto_scan['text'] = '[off] Auto Scan'
        btn_auto_scan.place(x = left_space+160+20-5-5-3, y = 4+3, width=130, height=25)
        coisas.append(btn_auto_scan)

        # b2 = tk.Button(root, text="?", command=lambda: OpenUrl(), bg='#CCC')
        # b2.place(x = left_space+313, y = 4, width=20, height=25)
        # coisas.append(b2)

        b3 = tk.Button(root, text="X", command = lambda: swap_window(root, screen_width, screen_height), bg='#CCC')
        b3.place(x = left_space+334-3, y = 4+3, width=20, height=25)
        coisas.append(b3)

        grip = tk.Button(root, text="<>", bg='#CCC')
        grip.place(x = left_space+286+20-3-2, y = 4+3, width=25, height=25)
        grip.config(image=btnImgMove)
        grip.image = btnImgMove
        grip.bind("<ButtonPress-1>", StartMove)
        grip.bind("<ButtonRelease-1>", lambda event: StopMove(root,event))
        grip.bind("<B1-Motion>", lambda event: OnMotion(root,event))

        coisas.append(grip)

        #label that lets you know if its using custom grid or not
        txt = ''
        if os.path.exists(custom_grid_path):
            print('Custom Grid file exists:', custom_grid_path)
            txt = 'Custom Grid Loaded.'

            custom_grid_lb = tk.Label(root, text=txt, justify='left', bg='#1d1d1d',
                        fg="#ff3b3b", font=("Helvetica 10 bold"), borderwidth=0, relief="solid")
                
            custom_grid_lb.place(x = left_space-120+38, y = 4, width=140, height=22)
            coisas.append(custom_grid_lb)


        flag_swap = 1
    else:
        #LAUNCHER WINDOW
        root.call('wm', 'attributes', '.', '-topmost', '0')
        root.title("Artifact Helper")

        #sp global
        sp = ScreenProcessor(path('resources/dhash_v1.pkl'), path('resources/label_to_name.pkl'))

        root.geometry("800x340+%d+%d" % (launcher_x , launcher_y))
        root.configure(background="#333")
        root.overrideredirect(0) # border 
        root.resizable(False, False)

        if not first_time:
            #root.lower()
            pass
        
        logo = ImageTk.PhotoImage(Image.open(path('resources/launcher_bg.png')))
        btnImgScan = ImageTk.PhotoImage(Image.open(path('resources/btn_launch_overlay.png')))
        btnImgGrid = ImageTk.PhotoImage(Image.open(path('resources/btn_launch_grid.png')))

        lg = tk.Label(root, image=logo, borderwidth=0, relief="solid")
        lg.image = logo
        lg.place(x = 0, y = 1, width=800, height=600)
        coisas.append(lg)

        b = tk.Button(root, text="Launch Overlay", command=lambda: swap_window(root, screen_width, screen_height), bg='#CCC', relief='flat', borderwidth=0)
        b.config(image=btnImgScan)
        b.image = btnImgScan #gc hack
        b.place(x = 84, y = 171, width=205, height=57)
        coisas.append(b)

        b_selector = tk.Button(root, text="Select Custom Grid", command=lambda: call_run_canvas(root), bg='#CCC', relief='flat', borderwidth=0)
        b_selector.config(image=btnImgGrid)
        b_selector.image = btnImgGrid #gc hack
        b_selector.place(x = 84+205+40, y = 171, width=205, height=57)
        coisas.append(b_selector)
        
        b2 = tk.Button(root, text="?", command=lambda: OpenUrl(), bg='#CCC')
        b2.place(x = 776, y = 5, width=20, height=25)
        coisas.append(b2)

        b3 = tk.Button(root, text="Report Problem", command=lambda: OpenUrl('issue'), bg='#CCC')
        b3.place(x = 660, y = 5, width=110, height=25)
        coisas.append(b3)

        if first_time:
            try:
                prices = fix_dict(get_prices())
            except:
                print("Could not get prices. Try again later.")
        
        flag_swap = 0

def main():
    global launcher_x , launcher_y

    root = tk.Tk()
    root.iconbitmap(path('favicon.ico'))

    screen_width = root.winfo_screenwidth() # width of the screen
    screen_height = root.winfo_screenheight() 
    launcher_x , launcher_y = screen_width/2-400,screen_height/2-300
    
    swap_window(root, screen_width, screen_height, first_time=True)
    
    root.mainloop()

if __name__ == "__main__":
    #run
    main()