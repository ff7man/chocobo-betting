import pyautogui
n=65
theargs = ""
xpos = 745
for x in range(0,6):
    p = 150+(x*n)
    if pyautogui.locateOnScreen(image="C:\\users\\mike\\desktop\\rng\\b1.png",region=(xpos,p,40,n),confidence=0.9):
        ret="1"
    elif pyautogui.locateOnScreen(image="C:\\users\\mike\\desktop\\rng\\b2.png",region=(xpos,p,40,n),confidence=0.9):
        ret="2"
    elif pyautogui.locateOnScreen(image="C:\\users\\mike\\desktop\\rng\\b3.png",region=(xpos,p,40,n),confidence=0.9):
        ret="3"
    elif pyautogui.locateOnScreen(image="C:\\users\\mike\\desktop\\rng\\b4.png",region=(xpos,p,40,n),confidence=0.9):
        ret="4"
    elif pyautogui.locateOnScreen(image="C:\\users\\mike\\desktop\\rng\\b5.png",region=(xpos,p,40,n),confidence=0.9):
        ret="5"
    elif pyautogui.locateOnScreen(image="C:\\users\\mike\\desktop\\rng\\b6.png",region=(xpos,p,40,n),confidence=0.9):
        ret="6"
    else:
        ret="N"
    theargs+=str(ret)
print("Found: "+theargs)