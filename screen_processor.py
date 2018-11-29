import pickle
from modelo_hash import NPModel, imgToFeatures
import numpy as np
from mss import mss

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
        self.from_top, self.from_left = 140*screen_height//1080, 132*screen_width//1920
        self.space_h, self.space_w = 345*screen_height//1080, 210*screen_width//1920
        self.height, self.width = 135*screen_height//1080, 180*screen_width//1920

    def process_ss(self, ss):
        '''Process a screenshot and returns predictions for cards.
            ss: RGB numpy matrix. Example shape: (1080, 1920, 3)'''

        cards = []
        scores = []
        for row in range(2):
            for col in range(6):
                #quatro cantos da carta
                top = self.from_top + row * self.space_h
                left = self.from_left + col * self.space_w
                bottom = top + self.height
                right = left + self.width

                #slice do monitor
                card, sl, st, score = robustCard(ss, top, bottom, left, right, self.md, verbose=False)
                cards.append(card)
                scores.append(score)

        return cards, scores
    
    def process_screen(self):
        with mss() as sct:
            im = sct.grab(sct.monitors[1])
        
        ss = numpy_flip(im)
        return self.process_ss(ss)