a =""" !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~"""
#myin = "MIKE!"
myin = input("Please enter a string: ")
res = ""
for b in myin:
 pos = a.find(b)
 hexN = '{0:x}'.format(int(pos)).upper()
 if len(hexN) == 1:
  hexN = "0"+hexN
 res +=hexN
print(res)
res2 ="".join(reversed([res[i:i+2] for i in range(0, len(res), 2)]))
print("reverse: "+res2)