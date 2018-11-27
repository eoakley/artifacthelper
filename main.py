from screen_processor import ScreenProcessor
import sys
import os

sp = ScreenProcessor(os.path.join(os.path.dirname(sys.modules['__main__'].__file__), 'model/cnn_v4.h5'), os.path.join(os.path.dirname(sys.modules['__main__'].__file__), 'model/label_to_name.pkl'))

from tkinter import *

def btnProcessScreen(T):
    s = sp.process_screen()
    for a,b in zip(s[0], s[1]):
        T.insert('1.0', str(round(b,3)).rjust(8) + ' : ' + a + '\n')
    
from tkinter import *

def btnProcessScreen(v):
    s = sp.process_screen()
    txt = ''
    for a,b in zip(s[0], s[1]):
        #T.insert('1.0', str(round(b,3)).rjust(8) + ' : ' + a + '\n')
        txt += str(round(b,3)).rjust(8) + ' : ' + a + '\n'
    v.set(txt)
        
    
def main():
    root = Tk() 
    root.title("Artifact Helper")
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry("550x250+%d+%d" % (screen_width/2-275, screen_height/2-125))
    root.configure(background='gray')
    root.lift()
    root.call('wm', 'attributes', '.', '-topmost', '1')

    #T = Text(root, height=12, width=60)
    #T.pack()
    
    v = StringVar()
    Label(root, textvariable=v).pack()

    
    b = Button(root, text="Go", command=lambda: btnProcessScreen(v))
    b.pack()

    
    
    
    mainloop()
    