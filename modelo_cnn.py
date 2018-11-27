import cv2
import numpy as np

def imgToFeatures(img):
    #resiza ela
    #print(img.shape)
    
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    return cv2.resize(img, (180,135))/256

def pathToFeatures(path):
    #resiza ela
    img_original = cv2.imread(path)
    return imgToFeatures(img_original)

class ModeloDeck:
    def __init__(self, label_to_name=None, model=None):
        self.label_to_name = label_to_name
        self.model = model
        
    def predict_1d(self, features, raw=False):
        preds = self.model.predict_proba(features.reshape(1, 135, 180, 3))
        if raw:
            return preds
        return self.label_to_name[np.argmax(preds)]
        
    def predict_path(self, path, raw=False):
        #le imagem
        img_original = cv2.imread(path)
        
        features = imgToFeatures(img_original)
        
        return self.predict_1d(features, raw)
    
    def predict_rgb(self, img, raw=False):
        
        features = imgToFeatures(img)
        
        return self.predict_1d(features, raw)
    
    