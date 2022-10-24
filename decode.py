a =""" !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~"""
res = ""
myin = input("Please enter a space separated string: ")
smy = myin.split(" ")
for val in smy:
 dec = int(val, 16)
 
 if dec >= len(a):
  if dec != 255:
   print("replacing char: "+val+ " with space")
  dec = 0
 res += a[dec]
print(res)