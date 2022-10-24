from ReadWriteMemory import ReadWriteMemory

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
 #print(thebytes)
 startbytes = thebytes
 thebytes = thebytes.split()
 nameVal = decodeMe(" ".join(thebytes[157:]))
 nameVal = nameVal.rstrip()
 stamina = thebytes[130]+thebytes[129]
 dec = int(stamina, 16)
 staminaValRaw = dec
 staminaVal = str(round(dec/10))
 stamina2 = thebytes[126]+thebytes[125]
 dec = int(stamina2, 16)
 stamina2ValRaw = dec
 stamina2Val = str(round(dec/10))
 dec = int(stamina2, 16)
 stamina2Val = "0x"+stamina2+"/10 = "+str(dec/10)
 unk1Val = thebytes[123]
 intelVal = thebytes[121]
 coopVal = thebytes[119]
 unk2Val = thebytes[117]
 accVal = thebytes[115]
 unk3Val = thebytes[113]
 speed = thebytes[110]+thebytes[109]
 dec = int(speed, 16)
 speedValRaw = dec
 speedVal = str(round(dec/34))
 rs = thebytes[108]+thebytes[107]
 dec = int(rs, 16)
 runSpeedVal = str(dec)
 unk4Val = thebytes[103]
 rs = thebytes[100]+thebytes[99]
 dec = int(rs, 16)
 runSpeed2Val = "0x"+rs+" = "+str(dec)
 sprintingVal = int(thebytes[97],16)
 first = " ".join(thebytes[0:91])
 otherVal = first
 classVal = "".join(thebytes[9:11])
 b152=str(int(thebytes[151],16))
 b27=str(thebytes[27])
 b104=str(thebytes[103]) # intel val
 b124=str(thebytes[123]) # intel type
 #print(b124+","+b104+","+b27+","+b152+","+str(nameVal)+","+str(speedVal)+","+str(speedValRaw)+","+str(staminaVal)+","+str(staminaValRaw)+","+str(stamina2ValRaw)+","+str(sprintingVal)+","+str(runSpeedVal)+","+str(intelVal)+","+str(coopVal)+","+str(accVal)+","+str(classVal))
 b2jockey = str(thebytes[1])
 b4choco = str(thebytes[3])
 b8 = str(thebytes[7])
 b22cam1=str("".join(thebytes[21:27]))
 b38cam2=str("".join(thebytes[37:42]))
 b62 = str("".join(thebytes[61:67]))
 # 4
 b73 = str(thebytes[72])
 # 4
 b81=str(thebytes[80])
 b85=str("".join(thebytes[85:88]))
 b90=str("".join(thebytes[89:91]))
 b104=str(thebytes[103])
 b114=str(thebytes[113])
 b118=str(thebytes[117])
 b124=str(thebytes[123])
 b141=str(thebytes[140])
 b146=str(thebytes[145])
 b152=str(thebytes[151])
 b156=str(thebytes[155])
 
 return(b156+","+b124+","+b104+","+b27+","+b152+","+str(nameVal)+","+str(speedVal)+","+str(speedValRaw)+","+str(staminaVal)+","+str(staminaValRaw)+","+str(stamina2ValRaw)+","+str(sprintingVal)+","+str(runSpeedVal)+","+str(intelVal)+","+str(coopVal)+","+str(accVal)+","+str(classVal)+","+b2jockey+","+b4choco+","+b8+","+b22cam1+","+b38cam2+","+b62+","+b73+","+b81+","+b85+","+b90+","+b104+","+b114+","+b118+","+b124+","+b141+","+b146+","+startbytes+",")
 
#print("Copying bytes from ff7_en.exe")
rwm = ReadWriteMemory()
process = rwm.get_process_by_name('ff7_en.exe')
process.open()
byteBuffer = process.readByte(0xE710FC,1600)
process.close()

allbytes =""
for x in byteBuffer:
 x = "{:02x} ".format(int(x,16))
 allbytes += x
allbytes = allbytes.rstrip()
allbytes = allbytes.upper()

sbytes = allbytes
sbytes = sbytes[213:]
#print(sbytes)
add = "mystery_typeb156,intel_adjb124,intel_typeb104,jockeyb28,order-b156,name,Top Speed,Raw Top Speed,Stamina,Raw Stamina,Raw Stamina2,Sprinting,Run Speed,Intelligence,Cooperation,Acceleration,Willingness to Sprint,b2-jockeyp,b4-chocop,b8,b22-camera1,b38-camera2,b62,b73,b81,b85,b90,b104,b114,b118,b124,b141,b146,all\n"
print(add)
for i in [1, 2, 3, 4, 5, 6, 7, 8]:
  tbytes = sbytes[0:492]
  a = parse(tbytes)
  print(a)
  sbytes = sbytes[492:]
