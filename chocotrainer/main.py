from ReadWriteMemory import ReadWriteMemory
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk
import sys
import math

import psutil
import pymem


class ChocoTrainer:
    def __init__(self,parent):
        pids = psutil.pids()
        for pid in pids:
            ps = psutil.Process(pid)
            if "ff7_en.exe" in ps.name():
                apples, base_address = pymem.process.base_address(pid)
                #base_address = "blah"
                print("%s running with pid: %d and base address: %s" % (ps.name(),ps.pid,base_address) )
            if "ePSXe.exe" in ps.name():
                base_address = "blah"
                #base_address = pymem.process.base_address(pid)
                print("%s running with pid: %d and base address: %s" % (ps.name(),ps.pid,base_address) )
        
        rwm = ReadWriteMemory()
        #pc
        self.process = rwm.get_process_by_name('ff7_en.exe')
        #epsxe
        #self.process = rwm.get_process_by_name('ePSXe.exe')
        self.process.open()
        #pc
        self.base = 0x400000
        self.s = self.base + 0xa71143
        #epsxe
        #self.base = 0x10b0000
        #self.s = self.base + 0xb395d7
        self.c10 = 0
        self.c11 = 0
        self.c12 = 0
        self.c13 = 0
        self.c14 = 0
        self.c15 = 0
        self.c16 = 0
        self.c17 = 0
        self.c20 = 0
        self.c21 = 0
        self.c22 = 0
        self.c23 = 0
        self.c24 = 0
        self.c25 = 0
        self.c26 = 0
        self.c27 = 0
        self.c30 = 0
        self.c31 = 0
        self.c32 = 0
        self.c33 = 0
        self.c34 = 0
        self.c35 = 0
        self.c36 = 0
        self.c37 = 0
        self.c40 = 0
        self.c41 = 0
        self.c42 = 0
        self.c43 = 0
        self.c44 = 0
        self.c45 = 0
        self.c46 = 0
        self.c47 = 0
        self.c50 = 0
        self.c51 = 0
        self.c52 = 0
        self.c53 = 0
        self.c54 = 0
        self.c55 = 0
        self.c56 = 0
        self.c57 = 0
        self.c60 = 0
        self.c61 = 0
        self.c62 = 0
        self.c63 = 0
        self.c64 = 0
        self.c65 = 0
        self.c66 = 0
        self.c67 = 0

        self.l_0 = tk.Label(parent, text='speed', font=('Microsoft Sans Serif', 16), bg='white')
        self.l_0.place(x=10, y=30, width=100, height=25)

        self.t_1 = tk.Label(parent, text='C1', font=('Microsoft Sans Serif', 16), bg='white')
        self.t_1.place(x = 145, y = 0, width = 25, height = 25)
        self.t_2 = tk.Label(parent, text='C2', font=('Microsoft Sans Serif', 16), bg='white')
        self.t_2.place(x=225, y=0, width=25, height=25)
        self.t_3 = tk.Label(parent, text='C3', font=('Microsoft Sans Serif', 16), bg='white')
        self.t_3.place(x=305, y=0, width=25, height=25)
        self.t_4 = tk.Label(parent, text='C4', font=('Microsoft Sans Serif', 16), bg='white')
        self.t_4.place(x=385, y=0, width=25, height=25)
        self.t_5 = tk.Label(parent, text='C5', font=('Microsoft Sans Serif', 16), bg='white')
        self.t_5.place(x=465, y=0, width=25, height=25)
        self.t_6 = tk.Label(parent, text='C6', font=('Microsoft Sans Serif', 16), bg='white')
        self.t_6.place(x=545, y=0, width=25, height=25)
        self.fields = []

        self.c10 = tk.StringVar()
        self.fields.append(self.c10)
        self.c1_0 = tk.Entry(parent, borderwidth='1px', textvariable=self.c10)
        self.c1_0.place(x=120, y=30, width=70, height=25)

        self.c11 = tk.StringVar()
        self.fields.append(self.c11)
        self.c1_1 = tk.Entry(parent, borderwidth='1px', textvariable=self.c11)
        self.c1_1.place(x=120, y=60, width=70, height=25)

        self.c12 = tk.StringVar()
        self.fields.append(self.c12)
        self.c1_2 = tk.Entry(parent, borderwidth='1px', textvariable=self.c12)
        self.c1_2.place(x=120, y=90, width=70, height=25)

        self.c13 = tk.StringVar()
        self.fields.append(self.c13)
        self.c1_3 = tk.Entry(parent, borderwidth='1px', textvariable=self.c13)
        self.c1_3.place(x=120, y=120, width=70, height=25)

        self.c14 = tk.StringVar()
        self.fields.append(self.c14)
        self.c1_4 = tk.Entry(parent, borderwidth='1px', textvariable=self.c14)
        self.c1_4.place(x=120, y=150, width=70, height=25)

        self.c15 = tk.StringVar()
        self.fields.append(self.c15)
        self.c1_5 = tk.Entry(parent, borderwidth='1px', textvariable=self.c15)
        self.c1_5.place(x=120, y=180, width=70, height=25)

        self.c16 = tk.StringVar()
        self.fields.append(self.c16)
        self.c1_6 = tk.Entry(parent, borderwidth='1px', textvariable=self.c16)
        self.c1_6.place(x=120, y=210, width=70, height=25)

        self.c17 = tk.StringVar()
        self.fields.append(self.c17)
        self.c1_7 = tk.Entry(parent, borderwidth='1px', textvariable=self.c17)
        self.c1_7.place(x=120, y=240, width=70, height=25)

        self.c20 = tk.StringVar()
        self.fields.append(self.c20)
        self.c2_0 = tk.Entry(parent, borderwidth='1px', textvariable=self.c20)
        self.c2_0.place(x=200, y=30, width=70, height=25)

        self.c21 = tk.StringVar()
        self.fields.append(self.c21)
        self.c2_1 = tk.Entry(parent, borderwidth='1px', textvariable=self.c21)
        self.c2_1.place(x=200, y=60, width=70, height=25)

        self.c22 = tk.StringVar()
        self.fields.append(self.c22)
        self.c2_2 = tk.Entry(parent, borderwidth='1px', textvariable=self.c22)
        self.c2_2.place(x=200, y=90, width=70, height=25)

        self.c23 = tk.StringVar()
        self.fields.append(self.c23)
        self.c2_3 = tk.Entry(parent, borderwidth='1px', textvariable=self.c23)
        self.c2_3.place(x=200, y=120, width=70, height=25)

        self.c24 = tk.StringVar()
        self.fields.append(self.c24)
        self.c2_4 = tk.Entry(parent, borderwidth='1px', textvariable=self.c24)
        self.c2_4.place(x=200, y=150, width=70, height=25)

        self.c25 = tk.StringVar()
        self.fields.append(self.c25)
        self.c2_5 = tk.Entry(parent, borderwidth='1px', textvariable=self.c25)
        self.c2_5.place(x=200, y=180, width=70, height=25)

        self.c26 = tk.StringVar()
        self.fields.append(self.c26)
        self.c2_6 = tk.Entry(parent, borderwidth='1px', textvariable=self.c26)
        self.c2_6.place(x=200, y=210, width=70, height=25)

        self.c27 = tk.StringVar()
        self.fields.append(self.c27)
        self.c2_7 = tk.Entry(parent, borderwidth='1px', textvariable=self.c27)
        self.c2_7.place(x=200, y=240, width=70, height=25)

        self.c30 = tk.StringVar()
        self.fields.append(self.c30)
        self.c3_0 = tk.Entry(parent, borderwidth='1px', textvariable=self.c30)
        self.c3_0.place(x=280, y=30, width=70, height=25)

        self.c31 = tk.StringVar()
        self.fields.append(self.c31)
        self.c3_1 = tk.Entry(parent, borderwidth='1px', textvariable=self.c31)
        self.c3_1.place(x=280, y=60, width=70, height=25)

        self.c32 = tk.StringVar()
        self.fields.append(self.c32)
        self.c3_2 = tk.Entry(parent, borderwidth='1px', textvariable=self.c32)
        self.c3_2.place(x=280, y=90, width=70, height=25)

        self.c33 = tk.StringVar()
        self.fields.append(self.c33)
        self.c3_3 = tk.Entry(parent, borderwidth='1px', textvariable=self.c33)
        self.c3_3.place(x=280, y=120, width=70, height=25)

        self.c34 = tk.StringVar()
        self.fields.append(self.c34)
        self.c3_4 = tk.Entry(parent, borderwidth='1px', textvariable=self.c34)
        self.c3_4.place(x=280, y=150, width=70, height=25)

        self.c35 = tk.StringVar()
        self.fields.append(self.c35)
        self.c3_5 = tk.Entry(parent, borderwidth='1px', textvariable=self.c35)
        self.c3_5.place(x=280, y=180, width=70, height=25)

        self.c36 = tk.StringVar()
        self.fields.append(self.c36)
        self.c3_6 = tk.Entry(parent, borderwidth='1px', textvariable=self.c36)
        self.c3_6.place(x=280, y=210, width=70, height=25)

        self.c37 = tk.StringVar()
        self.fields.append(self.c37)
        self.c3_7 = tk.Entry(parent, borderwidth='1px', textvariable=self.c37)
        self.c3_7.place(x=280, y=240, width=70, height=25)

        self.c40 = tk.StringVar()
        self.fields.append(self.c40)
        self.c4_0 = tk.Entry(parent, borderwidth='1px', textvariable=self.c40)
        self.c4_0.place(x=360, y=30, width=70, height=25)

        self.c41 = tk.StringVar()
        self.fields.append(self.c41)
        self.c4_1 = tk.Entry(parent, borderwidth='1px', textvariable=self.c41)
        self.c4_1.place(x=360, y=60, width=70, height=25)

        self.c42 = tk.StringVar()
        self.fields.append(self.c42)
        self.c4_2 = tk.Entry(parent, borderwidth='1px', textvariable=self.c42)
        self.c4_2.place(x=360, y=90, width=70, height=25)

        self.c43 = tk.StringVar()
        self.fields.append(self.c43)
        self.c4_3 = tk.Entry(parent, borderwidth='1px', textvariable=self.c43)
        self.c4_3.place(x=360, y=120, width=70, height=25)

        self.c44 = tk.StringVar()
        self.fields.append(self.c44)
        self.c4_4 = tk.Entry(parent, borderwidth='1px', textvariable=self.c44)
        self.c4_4.place(x=360, y=150, width=70, height=25)

        self.c45 = tk.StringVar()
        self.fields.append(self.c45)
        self.c4_5 = tk.Entry(parent, borderwidth='1px', textvariable=self.c45)
        self.c4_5.place(x=360, y=180, width=70, height=25)

        self.c46 = tk.StringVar()
        self.fields.append(self.c46)
        self.c4_6 = tk.Entry(parent, borderwidth='1px', textvariable=self.c46)
        self.c4_6.place(x=360, y=210, width=70, height=25)

        self.c47 = tk.StringVar()
        self.fields.append(self.c47)
        self.c4_7 = tk.Entry(parent, borderwidth='1px', textvariable=self.c47)
        self.c4_7.place(x=360, y=240, width=70, height=25)

        self.c50 = tk.StringVar()
        self.fields.append(self.c50)
        self.c5_0 = tk.Entry(parent, borderwidth='1px', textvariable=self.c50)
        self.c5_0.place(x=440, y=30, width=70, height=25)

        self.c51 = tk.StringVar()
        self.fields.append(self.c51)
        self.c5_1 = tk.Entry(parent, borderwidth='1px', textvariable=self.c51)
        self.c5_1.place(x=440, y=60, width=70, height=25)

        self.c52 = tk.StringVar()
        self.fields.append(self.c52)
        self.c5_2 = tk.Entry(parent, borderwidth='1px', textvariable=self.c52)
        self.c5_2.place(x=440, y=90, width=70, height=25)

        self.c53 = tk.StringVar()
        self.fields.append(self.c53)
        self.c5_3 = tk.Entry(parent, borderwidth='1px', textvariable=self.c53)
        self.c5_3.place(x=440, y=120, width=70, height=25)

        self.c54 = tk.StringVar()
        self.fields.append(self.c54)
        self.c5_4 = tk.Entry(parent, borderwidth='1px', textvariable=self.c54)
        self.c5_4.place(x=440, y=150, width=70, height=25)

        self.c55 = tk.StringVar()
        self.fields.append(self.c55)
        self.c5_5 = tk.Entry(parent, borderwidth='1px', textvariable=self.c55)
        self.c5_5.place(x=440, y=180, width=70, height=25)

        self.c56 = tk.StringVar()
        self.fields.append(self.c56)
        self.c5_6 = tk.Entry(parent, borderwidth='1px', textvariable=self.c56)
        self.c5_6.place(x=440, y=210, width=70, height=25)

        self.c57 = tk.StringVar()
        self.fields.append(self.c57)
        self.c5_7 = tk.Entry(parent, borderwidth='1px', textvariable=self.c57)
        self.c5_7.place(x=440, y=240, width=70, height=25)

        self.c60 = tk.StringVar()
        self.fields.append(self.c60)
        self.c6_0 = tk.Entry(parent, borderwidth='1px', textvariable=self.c60)
        self.c6_0.place(x=520, y=30, width=70, height=25)

        self.c61 = tk.StringVar()
        self.fields.append(self.c61)
        self.c6_1 = tk.Entry(parent, borderwidth='1px', textvariable=self.c61)
        self.c6_1.place(x=520, y=60, width=70, height=25)

        self.c62 = tk.StringVar()
        self.fields.append(self.c62)
        self.c6_2 = tk.Entry(parent, borderwidth='1px', textvariable=self.c62)
        self.c6_2.place(x=520, y=90, width=70, height=25)

        self.c63 = tk.StringVar()
        self.fields.append(self.c63)
        self.c6_3 = tk.Entry(parent, borderwidth='1px', textvariable=self.c63)
        self.c6_3.place(x=520, y=120, width=70, height=25)

        self.c64 = tk.StringVar()
        self.fields.append(self.c64)
        self.c6_4 = tk.Entry(parent, borderwidth='1px', textvariable=self.c64)
        self.c6_4.place(x=520, y=150, width=70, height=25)

        self.c65 = tk.StringVar()
        self.fields.append(self.c65)
        self.c6_5 = tk.Entry(parent, borderwidth='1px', textvariable=self.c65)
        self.c6_5.place(x=520, y=180, width=70, height=25)

        self.c66 = tk.StringVar()
        self.fields.append(self.c66)
        self.c6_6 = tk.Entry(parent, borderwidth='1px', textvariable=self.c66)
        self.c6_6.place(x=520, y=210, width=70, height=25)

        self.c67 = tk.StringVar()
        self.fields.append(self.c67)
        self.c6_7 = tk.Entry(parent, borderwidth='1px', textvariable=self.c67)
        self.c6_7.place(x=520, y=240, width=70, height=25)

        self.l_1 = tk.Label(parent, text='stamina', font=('Microsoft Sans Serif', 16), bg='white')
        self.l_1.place(x=10, y=60, width=100, height=25)

        self.l_2 = tk.Label(parent, text='stamina2', font=('Microsoft Sans Serif', 16), bg='white')
        self.l_2.place(x=10, y=90, width=100, height=25)

        self.l_3 = tk.Label(parent, text='run', font=('Microsoft Sans Serif', 16), bg='white')
        self.l_3.place(x=10, y=120, width=100, height=25)

        self.l_4 = tk.Label(parent, text='run2', font=('Microsoft Sans Serif', 16), bg='white')
        self.l_4.place(x=10, y=150, width=100, height=25)

        self.l_5 = tk.Label(parent, text='intel', font=('Microsoft Sans Serif', 16), bg='white')
        self.l_5.place(x=10, y=180, width=100, height=25)

        self.l_6 = tk.Label(parent, text='sprinting', font=('Microsoft Sans Serif', 16), bg='white')
        self.l_6.place(x=10, y=210, width=100, height=25)

        self.l_6 = tk.Label(parent, text='jockey', font=('Microsoft Sans Serif', 16), bg='white')
        self.l_6.place(x=10, y=240, width=100, height=25)

        def conv_byte(byte):
            #print("got: "+byte[0])
            return '%02x' % int(byte[0],16)
        def to_dec(val):
            return str(int(val,16))

        def get_val():
            count = 0
            for item in self.fields:
                item.set('get' + str(count))
                count += 1

            # gil
            #out = conv_byte(self.process.readByte(self.base+0xb1f283, 1))
            #out += conv_byte(self.process.readByte(self.base+0xb1f282, 1))
            #out += conv_byte(self.process.readByte(self.base+0xb1f281, 1))
            #out += conv_byte(self.process.readByte(self.base+0xb1f280, 1))
            #self.gil.set(to_dec(out))

            values = []
            for i in range(0,7):
             # speed
             sp = conv_byte(self.process.readByte(self.s+0xa4*i + 110, 1))
             sp2 = conv_byte(self.process.readByte(self.s+0xa4*i + 109, 1))
             values.append(to_dec(sp + sp2))

             # stamina
             sp = conv_byte(self.process.readByte(self.s+0xa4*i + 130, 1))
             sp2 = conv_byte(self.process.readByte(self.s+0xa4*i + 129, 1))
             values.append(to_dec(sp + sp2))

             # stamina2
             sp = conv_byte(self.process.readByte(self.s+0xa4*i + 126, 1))
             sp2 = conv_byte(self.process.readByte(self.s+0xa4*i + 125, 1))
             values.append(to_dec(sp + sp2))

             # run
             sp = conv_byte(self.process.readByte(self.s+0xa4*i + 108, 1))
             sp2 = conv_byte(self.process.readByte(self.s+0xa4*i + 107, 1))
             values.append(to_dec(sp + sp2))
             sp = conv_byte(self.process.readByte(self.s+0xa4*i + 100, 1))
             sp2 = conv_byte(self.process.readByte(self.s+0xa4*i + 99, 1))
             values.append(to_dec(sp + sp2))

             # intel
             sp = conv_byte(self.process.readByte(self.s+0xa4*i + 121, 1))
             values.append(to_dec(sp))

             # sprinting
             sp = conv_byte(self.process.readByte(self.s+0xa4*i + 97, 1))
             values.append(to_dec(sp))

             # jockey
             jockey = conv_byte(self.process.readByte(self.s + 0xa4 * i + 27, 1))
             values.append(to_dec(jockey))

            count = 0
            for item in self.fields:
                item.set(values[count])
                count += 1

        def int_tohex2(num):
            val = str(hex(num))[2:]
            if len(val) == 3:
                val = "0"+val
            byte1 = int(hex(int("0x"+val[0:2],16)),16)
            byte2 = int(hex(int("0x"+val[2:4],16)),16)
            bytes = []
            bytes.append(byte2)
            bytes.append(byte1)
            return bytes

        def int_tohex1(num):
            bytes = []
            bytes.append(num)
            return bytes

        def set_val():
            count = 0
            #for item in self.fields:
            #    item.set('set'+str(count))
            #    count+=1
            for item in self.fields:
                index = math.floor(count / 8)
                if count % 8 == 0:
                    num = int(item.get())
                    #num = num+1
                    self.process.writeByte(self.s + 0xa4*index + 109,int_tohex2(num))
                elif count % 8 == 7:
                    num = int(item.get())
                    self.process.writeByte(self.s + 0xa4 * index + 27, int_tohex1(num))
                elif count % 8 == 6:
                    num = int(item.get())
                    self.process.writeByte(self.s + 0xa4 * index + 97, int_tohex1(num))
                elif count % 8 == 5:
                    num = int(item.get())
                    self.process.writeByte(self.s + 0xa4 * index + 121, int_tohex1(num))
                elif count % 8 == 4:
                    num = int(item.get())
                    self.process.writeByte(self.s + 0xa4 * index + 99, int_tohex2(num))
                elif count % 8 == 3:
                    num = int(item.get())
                    self.process.writeByte(self.s + 0xa4 * index + 107, int_tohex2(num))
                elif count % 8 == 2:
                    num = int(item.get())
                    self.process.writeByte(self.s + 0xa4 * index + 129, int_tohex2(num))
                elif count % 8 == 1:
                    num = int(item.get())
                    self.process.writeByte(self.s + 0xa4 * index + 125, int_tohex2(num))
                else:
                    print("not sure")
                # item.set(values[count])
                count += 1


        self.getval_button = ttk.Button(parent, text='Get Values', command=get_val)
        self.getval_button.place(x=600, y=30, width=70, height=25)
        self.setval_button = ttk.Button(parent, text='Set Values', command=set_val)
        self.setval_button.place(x=600, y=60, width=70, height=25)

        self.j_l = tk.Label(parent, text='Jockey:', font=('Microsoft Sans Serif', 11), bg='white',anchor='w')
        self.j_l.place(x=600, y=170, width=80, height=20)
        self.j_b = tk.Label(parent, text='2 = Bronze', font=('Microsoft Sans Serif', 11), bg='white',anchor='w')
        self.j_b.place(x=600, y=190, width=80, height=20)
        self.j_s = tk.Label(parent, text='3 = Silver', font=('Microsoft Sans Serif', 11), bg='white',anchor='w')
        self.j_s.place(x=600, y=210, width=80, height=20)
        self.j_g = tk.Label(parent, text='1 = Gold', font=('Microsoft Sans Serif', 11), bg='white',anchor='w')
        self.j_g.place(x=600, y=230, width=80, height=20)
        self.j_p = tk.Label(parent, text='0 = Platinum', font=('Microsoft Sans Serif', 11), bg='white',anchor='w')
        self.j_p.place(x=600, y=250, width=80, height=20)

def main():
    root = tk.Tk()
    w = 700
    h = 280
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x = (sw - w) / 2
    y = (sh - h) / 2
    root.geometry('%dx%d+%d+%d' % (w, h, x, y))
    root.resizable(width=False, height=False)
    root.title('Choco Trainer')
    root.wm_iconbitmap('ff7.ico')
    root.configure(background='#000')
    image = Image.open('background.png')
    photo = ImageTk.PhotoImage(image)
    label = tk.Label(root, image=photo, bg='#000')
    label.image = photo
    label.pack()
    ChocoTrainer(root)

    root.mainloop()
    sys.exit(1)

if __name__ == '__main__':
    main()