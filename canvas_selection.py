#based on
#http://code.activestate.com/recipes/577409-python-tkinter-canvas-rectangle-selection-box/
from screen_processor import scale_grid
import numpy as np
import webbrowser
import os
try:
	import tkinter as tk
except ImportError:
	import Tkinter as tk

class RectTracker:	
	def __init__(self, canvas):
		self.canvas = canvas
		self.item = None
		self.rectangles = []
		
	def draw(self, start, end, **opts):
		"""Draw the rectangle"""
		return self.canvas.create_rectangle(*(list(start)+list(end)), **opts)
		
	def autodraw(self, master, custom_grid_path, **opts):
		"""Setup automatic drawing; supports command option"""
		self.start = None
		self.canvas.bind("<Button-1>", self.__update, '+')
		self.canvas.bind("<B1-Motion>", self.__update, '+')
		self.canvas.bind("<ButtonRelease-1>", self.__stop, '+')
		self.rectopts = opts
		self.last_grid = None
		self.master = master
		self.custom_grid_path = custom_grid_path
		self.lb = None
		
	def destroy(self):
		if self.lb != None:
			self.lb.destroy()

	def __update(self, event):
		if not self.start:
			self.start = [event.x, event.y]
			return
		
		if self.item is not None:
			self.canvas.delete(self.item)

			#itera na lista de retanculos e apaga todos
			for rectangle in self.rectangles:
				self.canvas.delete(rectangle)
		self.item = self.draw(self.start, (event.x, event.y),  outline='green', **self.rectopts)

		#desenha todos retangulos do grid
		border_right = event.x
		border_scale =  border_right - self.start[0]
		border_top = self.start[1]
		border_top_scaled = int(border_top + 0.024118*border_scale)
		border_left = self.start[0]
		card_grid = scale_grid(border_scale, border_top_scaled, border_left)
		self.last_grid = card_grid, (border_scale, border_top_scaled, border_left), (border_top, border_left, border_right)
		for row in card_grid:
			for col in row:
				top, left, bottom, right = col
				rectangle = self.draw((left, top), (right, bottom), outline='red', **self.rectopts)
				self.rectangles.append(rectangle)
		
	def __stop(self, event):
		self.start = None
		self.canvas.delete(self.item)
		grid, scale_borders, borders = self.last_grid
		#SAVE TO FILE
		np.save(self.custom_grid_path, np.array(scale_borders + borders))
		txt = 'Grid selected manually and saved to file "'+ self.custom_grid_path + \
				'"\nIt will be loaded automatically when you scan cards.'
		print(txt)
		txt = 'Grid saved successfuly. ' + str(borders)
		#also shows this on screen
		#deleta if exists
		if self.lb != None:
			self.lb.destroy()
		self.lb = tk.Label(self.master, text=txt, justify='center', bg='#222', 
                    fg="#DDD", font=("Helvetica 14"), borderwidth=3, relief="solid")
		self.lb.place(x = 80, y = 10, width=400, height=40)

		#itera na lista de retangulos e apaga todos
		for rectangle in self.rectangles:
			self.canvas.delete(rectangle)
			self.rectangles = []
		self.item = None
		self.item2 = None

def clear_file(root, elements, custom_grid_path):
	try:
		os.remove(custom_grid_path)
	except:
		print('Could not remove file, maybe it doesnt exist:', custom_grid_path)
	txt = 'File Cleared'
	print('Deleted file', custom_grid_path)
	lb = tk.Label(root, text=txt, justify='center', bg='#222', 
				fg="#DDD", font=("Helvetica 14"), borderwidth=3, relief="solid")
	lb.place(x = 80, y = 10, width=400, height=40)
	elements.append(lb)

def close_canvas(root, geometry, objs):
	for obj in objs:
		obj.destroy()
	root.geometry(geometry)

def run_canvas(root, img_path, custom_grid_path):
	w, h = root.winfo_screenwidth(), root.winfo_screenheight()
	#root maximized
	old_geometry = root.winfo_geometry()
	root.geometry("%dx%d+%d+%d" % (w, h, 0, 0))

	elements = []
	#canvas full size
	canv = tk.Canvas(root, width=w, height=h)
	canv.place(x=0, y=0, width=w, height=h)
	
	rect = RectTracker(canv)
		
	photo = tk.PhotoImage(file=img_path)
	canv.create_image(0, 0, image=photo, anchor=tk.NW)
	canv.objholder = photo

	b3 = tk.Button(root, text="Clear File", command=lambda: clear_file(root, elements, custom_grid_path), bg='#CCC')
	b3.place(x = 500+120+10, y = 10, width=120, height=40)

	b2 = tk.Button(root, text="Save and Return", command=lambda: close_canvas(root, old_geometry, elements), bg='#CCC')
	b2.place(x = 500, y = 10, width=120, height=40)

	bh = tk.Button(root, text="Help", command=lambda: webbrowser.open_new('https://github.com/eoakley/artifacthelper/blob/master/screenshots/ScreenShot_Help.png'), bg='#CCC')
	bh.place(x = 500+120+10+120+10, y = 10, width=120, height=40)
	
	elements = [canv, b2, b3, bh, rect]

	# just for fun
	def cool_design(event):
		kill_xy()
		
		dashes = [3, 2]
		canv.create_line(event.x, 0, event.x, h, dash=dashes, width=2, fill='green', tags='no')
		canv.create_line(0, event.y, w, event.y, dash=dashes, width=2, fill='green', tags='no')
		
	def kill_xy(event=None):
		canv.delete('no')
	
	canv.bind('<Motion>', cool_design, '+')
		
	rect.autodraw(master=root, custom_grid_path=custom_grid_path, width=3)

	return canv
	

if __name__ == '__main__':

	root = tk.Tk()
	root.title("Artifact Helper - Card Region Selection")
	run_canvas(root, "screenshot_draft.png", "custom_grid.npy")
	root.mainloop()