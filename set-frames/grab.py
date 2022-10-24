import pyautogui
import os
import time

def decodeMe(myin):
 a =""" !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~"""
 res = ""
 smy = myin.split(" ")
 for val in smy:
  dec = int(val, 16)
  if dec >= len(a):
   if dec != 255:
    print("replacing char: "+val+ " with space")
   dec = 0
  res += a[dec]
 return(res)
 
def parse(thebytes):
 startbytes = thebytes
 thebytes = thebytes.split()
 nameVal = decodeMe(" ".join(thebytes[157:])).rstrip()
 stamina = thebytes[130]+thebytes[129]
 dec = int(stamina, 16)
 staminaVal = str(int(dec/20))
 speed = thebytes[110]+thebytes[109]
 dec = int(speed, 16)
 speedVal = str(int(dec/34))
 sprintingVal = str(int(thebytes[97],16))
 if sprintingVal == 2:
     sprintingVal = 1
 b27=int(str(thebytes[27]))
 if b27==3:
     b27="s"
 if b27==2:
     b27="b"
 if b27==1:
     b27="g"
 if b27==0:
     b27="p"
     
 return(speedVal+","+staminaVal+","+nameVal+","+b27+","+sprintingVal+",")
 
fname = "C:\\Users\\mike\\Desktop\\rng\\bizhawk\\PSX\\ram\\Final Fantasy VII (USA) (Disc 3).bin"
# Wait for our ram dump to exists
wait2 = True
while wait2:
    if os.path.isfile(fname):
        wait2=False
        
# Before we parse ram we want to make sure we have a fresh ram dump
wait = True
while wait:
    ctime = int(time.time())
    ftime = int(os.path.getmtime(fname))
    if ctime-ftime < 30:
        print("new ram dump found")
        wait = False
    else:
        print("waiting for ram dump: current time: "+str(ctime)+ " modified time: "+str(ftime)+" difference: "+str(ctime-ftime))
        time.sleep(1)

print("screenshotting win order")
theargs=""
n=65
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
    
print("parsing ram dump")
data = ""
while True:
    try:
        with open(fname,"rb") as f:
            data = f.read()
    except PermissionError as e:
        print("permission failed..")
        time.sleep(0.5)
        continue
    break
print("read success")

# removing ram dump
os.remove(fname)

data = data[751031:]
data = data[0:984]

allbytes = ""
for x in data:
 x = "{:02X} ".format(int(hex(x),16))
 allbytes += x
allbytes = allbytes.rstrip()

remainbytes = allbytes
race = ""

for i in [1, 2, 3, 4, 5, 6]:
 race+=parse(remainbytes[0:492])
 remainbytes = remainbytes[492:]

race +=theargs

with open("C:\\Users\\mike\\Desktop\\rng\\count.txt","r") as f:
 counter = int(f.readline())
 race+=","+str(counter)
 
with open("C:\\Users\\mike\\Desktop\\rng\\count.txt","w") as f:
 counter+=1
 f.write(str(counter))
    
with open("C:\\Users\\mike\\Desktop\\rng\\result.csv","a") as f:
 f.write(race+"\n")
print("done")