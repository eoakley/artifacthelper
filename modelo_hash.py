import numpy as np
import dhash
from PIL import Image
import pickle

def imgToFeatures(img):
    #resiza ela
    return dhash.dhash_int(Image.fromarray(img))

class NPModel:
    def __init__(self, baseline, label_to_name):
        """Baseline should be shaped (306, 135, 180, 3).
            BRG(opencv) not RGB!"""
        self.baseline = baseline
        self.label_to_name = label_to_name
        self.n_images = 306
        
    def predict_1d(self, X, raw=False):
        """Loops and compares over all images."""

        #holds the predictions
        preds = np.zeros(self.n_images)

        hash_img = imgToFeatures(X)
        #compare with each image in baseline
        for j, base in enumerate(self.baseline):
            preds[j] = dhash.get_num_bits_different(base,hash_img)

        if raw:
            return np.min(preds), self.label_to_name[np.argmin(preds)]
        else:
            return self.label_to_name[np.argmin(preds)]
        
    def predict(self, X, raw=False):
        """Loops and compares over all images."""

        #holds the predictions
        preds = np.zeros((X.shape[0], self.n_images))

        #for each image in X
        for i, img in enumerate(X):
            if i%12==0: print(i, 'of', X.shape[0], end='\r')
            
            hash_img = imgToFeatures(img)
            #compare with each image in baseline
            for j, base in enumerate(self.baseline):
                preds[i][j] = dhash.get_num_bits_different(base,hash_img)
        
        if raw:
            return preds
        else:
            return self.label_to_name[np.argmin(preds, axis=1)]