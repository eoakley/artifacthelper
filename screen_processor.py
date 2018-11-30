import pickle
from modelo_hash import NPModel, imgToFeatures
import numpy as np
from mss import mss

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

    left_border = -1
    right_border = -1
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
        if verbose:
            print('>> ', i, ' >> ', 'With max and mean:', np.max(arr), np.min(arr))
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

        return scale_grid(scale, top, left_border)
    except Exception as e:
        print(e)
        print("Borders not found! Try different threshold.")
        return []

def numpy_flip(im):
    """ Most efficient Numpy version as of now. 
    Not the most effective of all."""
    frame = np.array(im, dtype=np.uint8)
    return np.flip(frame[:, :, :3], 2)

def robustCard(ss, top, bottom, left, right, md, verbose=False):
    sm = 999999
    best_pred = 'Empty Card'
    a,b = -2,2
    for sl in range(a,b):
        for st in range(a,b):
            card = ss[top+st:bottom+st, left+sl:right+sl, :]

            diff, pred = md.predict_1d(card, raw=True)

            if diff < sm:
                sm = diff
                best_pred = pred
            if verbose:
                print('    >', diff, pred)
    if sm >= 25:
        best_pred = 'Empty Card'
    return best_pred, 0, 0, sm

class ScreenProcessor:
    def __init__(self, model_path, label_dict_path, screen_width, screen_height):
        self.baseline = pickle.load(open(model_path, 'rb'))
        self.label_to_name = pickle.load(open(label_dict_path, 'rb'))
        self.md = NPModel(self.baseline, self.label_to_name)
        self.screen_width = screen_width
        self.screen_height = screen_height

    def process_ss(self, ss):
        '''Process a screenshot and returns predictions for cards.
            ss: RGB numpy matrix. Example shape: (1080, 1920, 3)'''

        card_grid = get_card_positions(ss, self.screen_width, self.screen_height)

        #error on card grid detection
        if len(card_grid) == 0:
            return [], [], []

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

        return cards, scores, card_grid
    
    def process_screen(self):
        with mss() as sct:
            im = sct.grab(sct.monitors[1])
        
        ss = numpy_flip(im)
        return ss, self.process_ss(ss)