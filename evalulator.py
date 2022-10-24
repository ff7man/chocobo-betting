from operator import attrgetter
import copy
count = 0
def merge(c1,c2):
    for i in range(len(c1)):
        c1[i].val = i
    for i in range(len(c2)):
        c2[i].val = i
    for i in range(len(c1)):
        for y in c2:
            if c1[i].name == y.name:
                c1[i].val += y.val
    return c1

def race(chocobos):
    #remove bronze/lowest jockey
    chocobos2 = []
    lowest = 0

    course = ""
    for c in chocobos:
        if c.place != 0:
            course = c.course

    for c in chocobos:
        if c.jockey != lowest:
            chocobos2.append(c)

    # we need to select 2 winners so,
    # if < 2 chocobos don't delete any
    if len(chocobos2) < 2:
        chocobos2 = chocobos

    chocobos3 = copy.deepcopy(chocobos2)
    # Sort by top speed, then jockey
    chocobos2.sort(key=attrgetter('topspeed','jockey'),reverse=True)
    # Sort by intel and run speed
    chocobos3.sort(key=attrgetter('runspeed'), reverse=True)
    #chocobos4 = copy.deepcopy(chocobos2)
    #chocobos4.sort(key=attrgetter('intel'), reverse=True)
    # check if we predicted the correct winners

    #chocobos2 = merge(chocobos2,chocobos3).copy()
    #chocobos2 = merge(chocobos2,chocobos4).copy()

    notchocobos2 = copy.deepcopy(chocobos2)
    for i in range(len(notchocobos2)):
        notchocobos2[i].val = float(i)
    nothing = 0
    for i in range(len(chocobos2)):
        chocobos2[i].val = float(i)
        # if we are a top runner bump it up
        for j in range(len(chocobos3)):
            if chocobos2[i].name == chocobos3[j].name:
                if j == 0:
                    chocobos2[i].val -= 3
                if j == 1:
                    chocobos2[i].val -= 2
                if j == 2:
                    chocobos2[i].val -= 0.5
                if j == 3:
                    chocobos2[i].val += 0
                if j == 4:
                    chocobos2[i].val += 1
                if j == 5:
                    chocobos2[i].val += 2

        # if we are smart bump it up
        if chocobos2[i].intel == 100:
            chocobos2[i].val -= 2
        # adjust for jockey course advantage/disadvantage
        if "2003" in course:
            if chocobos2[i].jockey == 3:
                chocobos2[i].val += 0.5
                if chocobos2[i].sprinting == 2:
                    chocobos2[i].val += .5
            elif chocobos2[i].jockey == 2:
                chocobos2[i].val -= 0.5
                if chocobos2[i].sprinting == 2:
                    chocobos2[i].val -= .5
            else:
                nothing +=1
        else:
            if chocobos2[i].jockey == 3:
                chocobos2[i].val -= 0.5
                if chocobos2[i].sprinting == 2:
                    chocobos2[i].val -= .5
            elif chocobos2[i].jockey == 2:
                chocobos2[i].val += 0.5
                if chocobos2[i].sprinting == 2:
                    chocobos2[i].val += .5
            else:
                nothing +=1
    chocobos2.sort(key=lambda x: (x.val,-x.topspeed, -x.jockey))
    success = 0
    if chocobos2[0].place <3:
        success +=1
    if chocobos2[1].place <3:
        success +=1
    if len(chocobos2)> 2:
        if chocobos2[2].place <3:
            success += 1
    #print("Predicted: "+str(chocobos2))
    #input("Hello")
    if success >1:
        return 1
    else:
        #print("og: "+str(notchocobos2))
        #print("predicted: "+str(chocobos2))
        chocobos2.sort(key=attrgetter('place'))
        #print("actual: "+str(chocobos2))
        #input("here")
        return 2

class Chocobo:
    def __init__(self,name,ts,stamina,sprinting,jockey,jockey2,course,order,place,intel,runspeed):
        self.topspeed = ts
        self.stamina = stamina
        self.sprinting = sprinting
        self.jockey = jockey
        self.jockey2 = jockey2
        self.name = name
        self.course = course
        self.order = order
        self.place = place
        self.intel = intel
        self.runspeed = int(runspeed)
        self.rss = int(runspeed)+int(ts)
        self.val = float(0)
    def __str__(self):
        return "name=%s speed=%s stamina=%s sprinting=%s jockey=%s ogjockey=%s course=%s order=%s place=%s intel=%s rs=%s rss=%s val=%s\n" % (self.name, self.topspeed, self.stamina/10, self.sprinting, self.jockey, self.jockey2, self.course, self.order, self.place, self.intel, self.runspeed, self.rss, self.val)
    def __repr__(self):
        return str(self)

def parse_csv(theFile):
    wins = 0
    losses = 0
    with open(theFile) as f:
        data = f.read()
    sdata = data.split("win-order,")
    for x in sdata:
        chocobos = []
        if "order-b152" in x:
            lines = x.split("\n")
            chocobos = []
            for i in range(0,len(lines)):
                if i >0 and i <7:
                    sline = lines[i].split(",")
                    name = sline[6]
                    place = sline[0]
                    jockey = int(sline[5])
                    # bronze -> silver -> gold -> plat
                    if jockey == 0: #plat
                        jockey = 3
                    elif jockey == 1: #gold
                        jockey = 2
                    elif jockey == 2: #bronze
                        jockey = 0
                    elif jockey == 3: #silver
                        jockey = 1
                    else:
                        print("not a jockey")
                    speed = sline[7]
                    stamina = sline[10]
                    end_stamina = sline[11]
                    sprinting = sline[12]
                    runspeed = sline[13]
                    intel = sline[14]
                    course = sline[17]
                    order = i-1
                    c = Chocobo(name,int(speed),int(stamina)/2,int(sprinting),jockey,jockey,course,int(order),int(place),int(intel),int(runspeed))
                    chocobos.append(c)
        if len(chocobos) == 6:
            res = race(chocobos)
            if res == 1:
             wins +=1
            elif res == 2:
             losses +=1
            else:
             print("how")
    return wins,losses

def run_rank(rank,thefile):
    w,l = parse_csv(thefile)
    avg = round(((w / (w + l) * 100)),2)
    print(rank+"\t"+str(w)+"\t"+str(l)+"\t"+str(avg))
    return w,l

if __name__ == '__main__':
    tw,tl = 0,0
    print("Class\tWins\tLosses\tAvg")
    w,l = run_rank("C","c1000.csv")
    tw += w
    tl += l
    w,l = run_rank("B","b1000.csv")
    tw += w
    tl += l
    w,l = run_rank("A","a1000.csv")
    tw += w
    tl += l
    w,l = run_rank("S","s1000.csv")
    tw += w
    tl += l
    avg = round(((tw / (tw + tl)) * 100),2)
    print("total\t"+str(tw)+"\t"+str(tl)+"\t"+str(avg))
