from ReadWriteMemory import ReadWriteMemory
def patchBytes(a,b):
 rwm = ReadWriteMemory()
 process = rwm.get_process_by_name('ff7_en.exe')
 process.open()
 process.writeByte(a,b) #c1
 process.writeByte(a+0xa4,b) #c2
 process.writeByte(a+0xa4+0xa4,b) #c3
 process.writeByte(a+0xa4+0xa4+0xa4,b) #c4
 process.writeByte(a+0xa4+0xa4+0xa4+0xa4,b) #c5
 process.writeByte(a+0xa4+0xa4+0xa4+0xa4+0xa4,b) #c6
 process.writeByte(a+0xa4+0xa4+0xa4+0xa4+0xa4+0xa4,b) #c7
 process.close()
def main():
 patchBytes(0xe711b0,[0x1D]) #TopSpeed
 patchBytes(0xe711b1,[0x0A]) #TopSpeed
 patchBytes(0xe711c0,[0xd3]) #Stamina
 patchBytes(0xe711c1,[0x09]) #Stamina
 patchBytes(0xe711c4,[0xd3]) #Stamina
 patchBytes(0xe711c5,[0x09]) #Stamina
 patchBytes(0xe711ae,[0xA5]) #RunSpeed
 patchBytes(0xe711af,[0x06]) #RunSpeed
 patchBytes(0xe711a6,[0xA5]) #RunSpeed
 patchBytes(0xe711a7,[0x06]) #RunSpeed
 patchBytes(0xe711a4,[0x00]) #Sprinting
 patchBytes(0xe711bc,[0x64]) #Intel
 patchBytes(0xe711aa,[0x02]) #Inteltype
 patchBytes(0xe711b4,[0x06]) #b114
 patchBytes(0xe7114a,[0xA5]) #b8
 patchBytes(0xe711d4,[0xD8]) #b146
main()
