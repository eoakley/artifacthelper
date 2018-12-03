import pickle
from modelo_hash import NPModel, imgToFeatures
import numpy as np
#from mss import mss
try:
    import win32gui
    import win32ui
except:
    from win32 import win32gui
    from pythonwin import win32ui
from ctypes import windll
from PIL import Image

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

def get_card_positions(ss, screen_width, screen_height, verbose=0):
    #objective: bounding boxes of the drafting cards region
    #l left r right, t top b bottom

    bottom_border = int(screen_height*0.8)
    #assuming ss.shape = (1080,1920,3)

    #from one third of the screen to the left, find left border of the cards
    for i in range(screen_width//3, 0, -1):
        #check maximum R, G, B values on a line the top of the screen (0) to bottom_bar
        arr = np.max(ss[:bottom_border, i, :])
        if np.max(arr) < 45 and np.mean(arr) < 25:
            #if maximum values are all below threshold, save this position and break
            left_border = i
            if verbose:
                print('Found left border at', i)
                print('With max and mean:', np.max(arr), np.min(arr))
                print('')
            break

    #from 2/3 of screen to right, find right border of the card region
    for i in range(screen_width*2//3, screen_width, 1):
        arr = np.max(ss[:bottom_border, i, :])
        #if verbose:
            #print('>> ', i, ' >> ', 'With max and mean:', np.max(arr), np.min(arr))
        if np.max(arr) < 50 and np.mean(arr) < 50:
            right_border = i
            if verbose:
                print('Found right border at', i)
                print('With max and mean:', np.max(arr), np.min(arr))
                print('')
            break

    #from 1/3 to top, find top border
    for i in range(screen_height//4, 0, -1):
        arr = np.max(ss[i, :, :])
        if np.max(arr) < 60 and np.mean(arr) < 60:
            top_border = i
            if verbose:
                print('Found top border at', i)
                print('With max and mean:', np.max(arr), np.min(arr))
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
    #left, top, right, bot = win32gui.GetClientRect(hwnd)
    left, top, right, bot = win32gui.GetWindowRect(hwnd)
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
    #result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 1)
    result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 0)
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
    def __init__(self, model_path, label_dict_path, screen_width, screen_height):
        self.baseline = pickle.load(open(model_path, 'rb'))
        self.label_to_name = pickle.load(open(label_dict_path, 'rb'))
        self.md = NPModel(self.baseline, self.label_to_name)
        self.card_grid = []
        self.borders = None
        #self.screen_width = screen_width
        #self.screen_height = screen_height

    def process_ss(self, ss):
        '''Process a screenshot and returns predictions for cards.
            ss: RGB numpy matrix. Example shape: (1080, 1920, 3)'''

        #uses previously detected card grid if we have one.
        if len(self.card_grid) > 0:
            card_grid, borders = self.card_grid, self.borders
        else:
            card_grid, borders = get_card_positions(ss, self.screen_width, self.screen_height, verbose=False)

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
            self.card_grid = card_grid
            self.borders = borders

        #print(cards, card_grid)
        return cards, scores, card_grid, borders
    
    def process_screen(self):
        ss = grab_artifact()

        self.screen_width = ss.shape[1]
        self.screen_height = ss.shape[0]
        
        #old code
        #with mss() as sct:
        #    im = sct.grab(sct.monitors[1])
        #ss = numpy_flip(im)

        #print("Screenshot shape:", ss.shape)
        return ss, self.process_ss(ss)
