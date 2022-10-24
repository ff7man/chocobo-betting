import pyautogui
#import numpy as np
#import cv2
#import pytesseract
#from PIL import Image
success = pyautogui.screenshot("temp.png",region=(740,150, 40, 450))

n =65
#150+(x*n)
#740,150 -> 40,150
for x in range(0,6):
 #print(x)
 #success = pyautogui.screenshot("s"+str(x)+".png",region=(740,150, 40, 450))
 p = 150+(x*n)
 #print("740,"+str(p)+",40,76")
 success = pyautogui.screenshot("matchs"+str(x)+".png",region=(740,p, 40, 65))
