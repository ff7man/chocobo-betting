from operator import attrgetter
def race(chocobos):
    global wins,losses
    #remove bronze/lowest jockey
    chocobos2 = []
    lowest = 0
    findLowestJockey = False
    if findLowestJockey:
        lowest = 5
        for c in chocobos:
            if c.jockey < lowest:
                lowest = c.jockey
    for c in chocobos:
        if c.jockey != lowest:
            chocobos2.append(c)

    # we need to select 2 winners so,
    # if < 2 chocobos don't delete any
    if len(chocobos2) < 2:
        chocobos2 = chocobos

    # Sort by top speed, then jockey
    chocobos2.sort(key=attrgetter('topspeed','jockey'),reverse=True)

    # check if we predicted the correct winners
    success = 0
    if chocobos2[0].place <3:
        success +=1
    if chocobos2[1].place <3:
        success +=1
    if len(chocobos2)> 2:
        if chocobos2[2].place <3:
            success += 1
    if success >1:
        wins +=1
    else:
        losses += 1

class Chocobo:
    def __init__(self,name,ts,stamina,sprinting,jockey,course,order,place):
        self.topspeed = ts
        self.stamina = stamina
        self.sprinting = sprinting
        self.jockey = jockey
        self.name = name
        self.course = course
        self.order = order
        self.place = place
    def __str__(self):
        return "name=%s speed=%s stamina=%s sprinting=%s jockey=%s course=%s order=%s place=%s\n" % (self.name, self.topspeed, self.stamina, self.sprinting, self.jockey, self.course, self.order, self.place)
    def __repr__(self):
        return str(self)

def parse_csv(theFile):
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
                    stamina = sline[9]
                    end_stamina = sline[11]
                    sprinting = sline[12]
                    runspeed = sline[13]
                    intel = sline[14]
                    course = sline[17]
                    order = i-1
                    c = Chocobo(name,int(speed),stamina,int(sprinting),jockey,course,int(order),int(place))
                    chocobos.append(c)
        if len(chocobos) == 6:
            race(chocobos)

def run_rank(rank,thefile):
    global wins,losses,totalwins,totallosses
    wins = 0
    losses = 0
    parse_csv(thefile)
    avg = round(((wins / (wins + losses) * 100)),2)
    print(rank+"\t"+str(wins)+"\t"+str(losses)+"\t"+str(avg))
    totalwins += wins
    totallosses += losses

if __name__ == '__main__':
    global wins,losses,totalwins,totallosses
    win,losses,totalwins,totallosses = 0,0,0,0
    print("Class\tWins\tLosses\tAvg")
    run_rank("C","c1000.csv")
    run_rank("B","b1000.csv")
    run_rank("A","a1000.csv")
    run_rank("S","s1000.csv")
    avg = round(((totalwins / (totalwins + totallosses)) * 100),2)
    print("total\t"+str(totalwins)+"\t"+str(totallosses)+"\t"+str(avg))
