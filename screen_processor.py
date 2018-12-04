import pickle
from modelo_hash import NPModel, imgToFeatures
import numpy as np
import os
import sys
#from mss import mss
try:
    import win32gui
    import win32ui
except:
    from win32 import win32gui
    from pythonwin import win32ui
from ctypes import windll
from PIL import Image

path_root = os.path.dirname(sys.modules['__main__'].__file__)
def path(filename):
    global path_root
    return os.path.join(path_root, filename)

def scale_grid(scale, top, left):
    """Card grid seems to be fixed. Only thing that changes is its scale and position.
        Parameters: top left position and scale, returns top, left, bot, right positions of each card. """

    #card grid shape is (2, 6, 4)
    card_grid = np.array([[[0.        , 0.        , 0.1097561 , 0.14634146],
            [0.        , 0.17073171, 0.1097561 , 0.31707317],
            [0.        , 0.34146341, 0.1097561 , 0.48780488],
            [0.        , 0.51219512, 0.1097561 , 0.65853659],
            [0.        , 0.68292683, 0.1097561 , 0.82926829],
            [0.        , 0.85365854, 0.1097561 , 1.        ]],

        [[0.2804878 , 0.        , 0.3902439 , 0.14634146],
            [0.2804878 , 0.17073171, 0.3902439 , 0.31707317],
            [0.2804878 , 0.34146341, 0.3902439 , 0.48780488],
            [0.2804878 , 0.51219512, 0.3902439 , 0.65853659],
            [0.2804878 , 0.68292683, 0.3902439 , 0.82926829],
            [0.2804878 , 0.85365854, 0.3902439 , 1.        ]]])

    card_grid *= scale
    card_grid = card_grid.round().astype(int)

    card_grid[:, :, [0,2]] += top
    
    card_grid[:, :, [1,3]] += left

    return card_grid

def save_debugg_screenshot(ss, card_grid, borders):

    top_border, left_border, right_border = borders
    red = [255, 0, 0]
    #draw grid on screenshot for debugging
    for row in range(2):
        for col in range(6):
            #quatro cantos da carta
            top, left, bottom, right = card_grid[row, col, :]

            #paint square with red.
            #ss.shape = (1080, 1920, 3)
            ss[top:bottom, left, :] = red
            ss[top:bottom, right, :] = red
            ss[top, left:right, :] = red
            ss[bottom, left:right, :] = red


    green = [0, 255, 0]
    ss[top_border, :, :] = green
    ss[:, left_border, :] = green
    ss[:, right_border, :] = green


    #save screenshot
    ss_img = Image.fromarray(ss)
    ss_img.save(path('screen_shot_debugg.png'),"PNG")

def is_border(arr, verbose=False):
    """New logic to detect borders:
        Top 1% pixels (Green Channel only) should not be
        much greater than bottom 10% of pixels.
        Also global mean should be close to (0,0,0)
            which is black."""
    #arr.shape = (game_height, 3)

    #old logic
    #return np.max(arr) < 50 and np.mean(arr) < 50

    # print(arr.shape)
    top_1 = arr[arr >= np.percentile(arr, 99)]
    bottom_10 = arr[arr <= np.percentile(arr, 90)]

    threshold_diff_top_bot = 10
    threshold_mean_black = 20
    max_threshold = 40
    # print('\n\n')
    # print(top_1)
    # print(bottom_10)
    top_bot_val = np.abs(np.mean(top_1) - np.mean(bottom_10))
    top_bot_check = top_bot_val < threshold_diff_top_bot
    blackness_check = np.mean(arr) < threshold_mean_black
    max_check = np.max(arr) < max_threshold

    return top_bot_check and blackness_check and max_check, top_bot_val, np.mean(arr), np.max(arr)

def get_card_positions(ss, game_width, game_height, verbose=False):
    #objective: bounding boxes of the drafting cards region
    #l left r right, t top b bottom

    bottom_cut = int(game_height*0.85)
    bottom_cut_top = int(game_height*0.70)
    #assuming ss.shape = (1080,1920,3)

    #should only run once
    print("Detecting grid once...", ss.shape)

    #from one third of the screen to the left, find left border of the cards
    for i in range(game_width//3, 0, -1):
        arr = ss[bottom_cut_top:bottom_cut, i, 1]
        check, top_bot_val, mean_val, max_val = is_border(arr, verbose=verbose)
        if check:
            left_border = i
            if verbose:
                print('Found left border at', i)
                print('With top_bot_val, mean, max:', top_bot_val, mean_val, max_val)
                print('')
            break

    #from 1/2 of screen to right, find right border of the card region
    for i in range(game_width//2, game_width, 1):
        arr = ss[bottom_cut_top:bottom_cut, i, 1]
        check, top_bot_val, mean_val, max_val = is_border(arr, verbose=verbose)
        if check:
            right_border = i
            if verbose:
                print('Found right border at', i)
                print('With top_bot_val, mean, max:', top_bot_val, mean_val, max_val)
                arr = ss[bottom_cut_top:bottom_cut, i-2, 1]
                check, top_bot_val, mean_val, max_val = is_border(arr, verbose=verbose)
                print('Found right border at', i-2)
                print('With top_bot_val, mean, max:', top_bot_val, mean_val, max_val)
                arr = ss[bottom_cut_top:bottom_cut, i-5, 1]
                check, top_bot_val, mean_val, max_val = is_border(arr, verbose=verbose)
                print('Found right border at', i-5)
                print('With top_bot_val, mean, max:', top_bot_val, mean_val, max_val)
                print('')
            break

    #from 1/4 to top, find top border
    for i in range(game_height//4, 0, -1):
        arr = ss[i, :, 1]
        check, top_bot_val, mean_val, max_val = is_border(arr, verbose=verbose)
        if check:
            top_border = i
            if verbose:
                print('Found top border at', i)
                print('With top_bot_val, mean, max:', top_bot_val, mean_val, max_val)
                print('')
            break

    try:
        #scale calculation
        scale = right_border - left_border

        image_header = 0.024118

        #position from top
        top = int(top_border + image_header*scale)

        return scale_grid(scale, top, left_border), (top_border, left_border, right_border)
    except Exception as e:
        print(e)
        print("Borders not found! Try different threshold.")
        return [], [0,0,0]

def numpy_flip(im):
    """ Most efficient Numpy version as of now. 
    Not the most effective of all."""
    frame = np.array(im, dtype=np.uint8)
    return np.flip(frame[:, :, :3], 2)

def robustCard(ss, top, bottom, left, right, md, verbose=False):
    sm = 999999
    best_pred = 'Empty Card'
    a,b = -0,7
    for sl in range(a,b,3):
        for st in range(a,b,3):
            card = ss[top+st:bottom+st, left+sl:right+sl, :]

            diff, pred = md.predict_1d(card, raw=True)
            #print(sl, st, diff, pred)

            if diff < sm:
                sm = diff
                best_pred = pred
            if verbose:
                print('    >', diff, pred)
    if sm >= 30:
        best_pred = 'Empty Card'
    return best_pred, 0, 0, sm

def grab_artifact():
    #grabs image of the game. new code, does not take full monitor screenshot like before
    try:
        hwnd = win32gui.FindWindow(None, 'Artifact')
    except Exception as e:
        print(e)
        print("No window named Artifact. Is the game running?")

    # Change the line below depending on whether you want the whole window
    # or just the client area. 
    left, top, right, bot = win32gui.GetClientRect(hwnd)
    #left, top, right, bot = win32gui.GetWindowRect(hwnd)
    w = right - left
    h = bot - top

    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC  = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()

    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)

    saveDC.SelectObject(saveBitMap)

    # Change the line below depending on whether you want the whole window
    # or just the client area. 
    result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 1)
    #result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 0)
    try:
        assert result == 1
    except Exception as e:
        print(e)
        print('Grab did not work. Maybe missing depedencies?')

    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)

    im = Image.frombuffer(
        'RGB',
        (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
        bmpstr, 'raw', 'BGRX', 0, 1)

    ss = np.array(im)
    return ss

class ScreenProcessor:
    def __init__(self, model_path, label_dict_path, verbose=False):
        self.baseline = pickle.load(open(model_path, 'rb'))
        self.label_to_name = pickle.load(open(label_dict_path, 'rb'))
        self.md = NPModel(self.baseline, self.label_to_name)
        self.card_grid = []
        self.borders = None

    def process_ss(self, ss, verbose=False):
        '''Process a screenshot and returns predictions for cards.
            ss: RGB numpy matrix. Example shape: (1080, 1920, 3)'''

        #uses previously detected card grid if we have one.
        if len(self.card_grid) > 0:
            card_grid, borders = self.card_grid, self.borders
        else:
            card_grid, borders = get_card_positions(ss, self.game_width, self.game_height, verbose=verbose)

        #error on card grid detection
        if len(card_grid) == 0:
            return [], [], [], borders

        cards = []
        scores = []
        for row in range(2):
            for col in range(6):
                #quatro cantos da carta
                #print(card_grid[row, col, :])
                top, left, bottom, right = card_grid[row, col, :]

                #slice do monitor
                card, sl, st, score = robustCard(ss, top, bottom, left, right, self.md, verbose=False)
                cards.append(card)
                scores.append(score)

        #if detected grid correctly, uses this grid for the rest of the program instance
        if cards.count('Empty Card') != len(cards):
            #at least one image was not empy, so it must have worked.
            print("It worked! At least one card is not empty.")
            self.card_grid = card_grid
            self.borders = borders

        print(cards, borders)
        return cards, scores, card_grid, borders
    
    def process_screen(self):
        ss = grab_artifact()

        self.game_width = ss.shape[1]
        self.game_height = ss.shape[0]
        
        #old code
        #with mss() as sct:
        #    im = sct.grab(sct.monitors[1])
        #ss = numpy_flip(im)

        #print("Screenshot shape:", ss.shape)
        return ss, self.process_ss(ss)

if __name__ == "__main__":
    from PIL import Image
    sp = ScreenProcessor('resources/dhash_v1.pkl', 'resources/label_to_name.pkl')
    ss = Image.open('D:\Google Drive\Jupyter\Artifact\Helper (dev)\ss_1080_2.jpg')
    ss = np.array(ss.convert('RGB'))

    print(ss.shape)

    sp.game_width = ss.shape[1]
    sp.game_height = ss.shape[0]

    #print("Screenshot shape:", ss.shape)
    cards, scores, card_grid, borders = sp.process_ss(ss, verbose=True)

    save_debugg_screenshot(ss, card_grid, borders)
