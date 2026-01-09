import random
import time

class Player:
    def __init__(self,player_id,player_num):
        self.id = player_id   #id从0计数
        self.nickname = "no_name"
        self.life = 1
        self.bag = []
        self.location = "会客厅"
        self.killer = 0  #狼人标记
        self.distance = [0] * player_num  #列表中下标表示玩家id，数值表示距离
        self.magic_used = 1  #是否使用技能，未使用为1，使用后为0
        self.wechat = [[] for _ in range(player_num + 1)]   #私聊消息记录
        self.message_len = [0] * (player_num + 1)     #收到通知前消息变化量

    def check_phone(self):
        global player_list
        print(f"时间：{get_time()[0]}年{get_time()[1]}月{int(get_time()[2])}日 {get_time()[3]}:{get_time()[4]}")
        print("背包：",end="")
        for i in self.bag:
            print(f"“{i.name}”",end="")
        print("")
        #新消息检测👇
        obj_send = 0
        for i in self.message_len:
            if i:
                if obj_send == len(player_list) + 1:
                    print(f"来自公共群聊的新消息：")
                    print(self.wechat[obj_send][-i:])
                    self.message_len[obj_send] = 0
                else:
                    print(f"来自{player_list[obj_send].nickname}的新消息：")
                    print(self.wechat[obj_send][-i:])
                    self.message_len[obj_send] = 0
            obj_send += 1
        #消息发送部分👇
        nickname_list = []
        for i in player_list:
            print(i.nickname+" ",end="")
            nickname_list.append(i.nickname)
        print("公共群聊")
        nickname_list.append("公共群聊")
        print("")
        choice = input("输入玩家昵称开启聊天，输入其他退出手机")
        if choice in nickname_list:
            print("聊天已开启，输入exit退出聊天")
            obj_id = 0
            for i in player_list:
                if i.nickname == choice:
                    obj_id = i.id
            if choice == "公共群聊":
                obj_id = len(player_list)+ 1
            print("历史消息：-----")
            for i in self.wechat[obj_id]:
                print(i)
            print("新消息：------")
            inp = input()
            while inp != "exit":
                if choice == "公共群聊":
                    for i in player_list:
                        i.wechat[obj_id].append(f"{self.nickname}:"+inp)
                        i.message_len[obj_id] += 1
                        print(inp + f":{self.nickname}")
                        inp = input()
                else:
                    self.wechat[obj_id].append(f"{self.nickname}:"+inp) # 添加消息到自己消息列表中
                    player_list[obj_id].wechat[self.id].append(f"{self.nickname}:"+inp)# 添加消息到对方消息列表中
                    player_list[obj_id].message_len[self.id] += 1   #修改对方消息变化量
                    print(inp+f":{self.nickname}")
                    inp = input()

    def move(self):
        choice = ""
        while choice not in location_list:
            try:
                print(location_list)
                choice = input(f"{self.nickname}要去哪里？")
            except:
                choice = "null"
                print("输入错误，重新输入")
        self.location = choice
        # 下面跟进距离计算代码
        get_distance(self)


    def attack(self):
        global time_start, player_list, time_real_start
        if self.killer == 0 or int(time.time()-time_real_start) < 60:  # 开局前一小时以及普通人不能攻击
            print("不可攻击其他人物，跳过本回合")
            return
        killer_list_id = []
        get_distance(self)
        for i in range(0, len(self.distance)):
            if self.distance[i] <= 1:
                killer_list_id.append(i)
        killer_list_nickname = []
        for i in killer_list_id:
            for j in player_list:
                if j.id == i:
                    killer_list_nickname.append(j.nickname)
        print("可选目标为：", killer_list_nickname)
        choice = 0
        while choice not in [i for i in range(1, len(killer_list_nickname) + 1)]:
            try:
                choice = int(input(f"{self.nickname}要选择谁？"))
            except:
                choice = 0
                print("输入错误，重新输入")
        for i in player_list:
            if i.nickname == killer_list_nickname[choice - 1]:
                i.life = 0

class Item:
    def __init__(self,name,describe,time_item):
        self.name = name
        self.describe = describe
        self.get_time = time_item

class Shiro(Player):
    def __init__(self,player_id,player_num):
        super().__init__(player_id,player_num)
        self.name = "Shiro"
    def magic(self):
        self.magic_used = 0 #置0显示魔法已使用
        choice = 0
        while choice not in [1,2]:
            try:
                choice = int(input("使用魔法：伪证 \n1.将一项证据显示为伪证  2.创造一个伪证"))
            except:
                choice = 0
                print("输入有误，重新输入")
        if choice == 1:
            if not self.bag:
                self.magic_used = 1
                print("魔法使用失败：背包中无物品")
            else:
                j=0
                for i in self.bag:
                    j+=1
                    print(f"{j}."+i.name,end="  ")
                choice = 0
                while choice not in range(1,len(self.bag)+1):
                    try:
                        choice = int(input("选择要显示为伪证的物品"))
                    except:
                        choice = 0
                        print("输入有误，重新输入")
                self.bag[choice-1].name = "伪证：" + self.bag[choice-1].name
                print("你选择的证据已添加“伪证“标签")
        else:
            print("输入伪造物品的名字，描述以及获得时间")
            name = input("为伪证命名")
            describe = input("为伪证填写描述")
            time_false = []
            while len(time_false) != 12:
                time_false = input("填写伪证的获取时间，格式为：202509010101（2025年9月1日1时1分）")
                if len(time_false) != 12:
                    print("时间输入长度有误，重新输入")
                elif not time_false.isdigit():
                    print("时间输入格式有误，重新输入")
                    time_false=[]
            time_li = [int(time_false[:4]),int(time_false[4:6]),int(time_false[6:8]),int(time_false[8:10]),int(time_false[10:])]
            false_item = Item("伪证："+name,describe,time_li)
            self.bag.append(false_item)
            print("伪造完成，伪证已添加至背包")



class Person2(Player):
    def __init__(self,player_id,player_num):
        super().__init__(player_id,player_num)
        self.name = "Person2"
    def magic(self):
        pass

class Person3(Player):
    def __init__(self,player_id,player_num):
        super().__init__(player_id,player_num)
        self.name = "Person3"
    def magic(self):
        pass

class Person4(Player):
    def __init__(self,player_id,player_num):
        super().__init__(player_id,player_num)
        self.name = "Person4"
    def magic(self):
        pass

map_dict = {"医务室":0, "淋浴房":1, "日光房":2, "杂物处":3, "中庭":4, "接客室":5, "女厕":6, "会客厅":7, "玄关大厅":8, "审判庭入口过道":9,
            "食堂": 10, "厨房":11, "审判庭":12, "牢房":13, "焚烧炉":14, "惩罚室":15, "娱乐室":16, "工作室":17, "2F大厅":18, "图书室":19}

map_len = [
    # A  B  C  D  E  F  G  H  I  J  K  L  M  N  O  P  Q  R  S  T  楼层间距离20
    [ 0,15,15, 5,20,25,15,20,25,30,35,40,40,50,60,60,50,50,45,50], #A
    [15, 0,15,10, 5,10,15,15,15,20,25,30,30,40,50,50,40,40,35,40], #B
    [15,15, 0, 5,15,20, 5,10,15,20,25,30,30,40,50,50,40,40,35,40], #C
    [ 5,10, 5, 0, 5,10, 5,10,15,20,25,30,30,40,50,50,40,40,35,40], #D
    [20, 5,15, 5, 0, 5,15, 5, 5,10,15,20,20,30,40,40,30,30,25,30], #E
    [25,10,20,10, 5, 0,25,15, 5,10,15,20,20,30,40,40,30,30,25,30], #F
    [15,15, 5, 5,15,25, 0, 5,10,15,20,25,25,35,45,45,35,35,30,35], #G
    [20,15,10,10, 5, 5,10, 0, 5,10,15,20,20,30,40,40,30,30,25,30], #H
    [25,15,15,15, 5, 5,10, 5, 0, 5,10,15,15,25,35,35,25,25,20,25], #I
    [30,20,20,20,10,10,15,10, 5, 0, 5,10,10,30,40,40,30,30,25,30], #J
    [35,25,25,25,15,15,20,15,10, 5, 0, 5, 5,35,45,45,35,35,30,35], #K
    [40,30,30,30,20,20,25,20,15,10, 5, 0, 5,40,50,50,40,40,35,40], #L
    [40,30,30,30,20,20,25,20,15,10, 5, 5, 0,40,50,50,40,40,35,40], #M
    [50,40,40,40,30,30,35,30,25,30,35,40,40, 0,20,20,50,50,45,50], #N
    [60,50,50,50,40,40,45,40,35,40,45,50,50,20, 0,30,60,60,55,60], #O
    [60,50,50,50,40,40,45,40,35,40,45,50,50,20,30, 0,60,60,55,60], #P
    [50,40,40,40,30,30,35,30,25,30,35,40,40,50,60,60, 0,15, 5,15], #Q
    [50,40,40,40,30,30,35,30,25,30,35,40,40,50,60,60,15, 0, 5,15], #R
    [45,35,35,35,25,25,30,25,20,25,30,35,35,45,55,55, 5, 5, 0, 5], #S
    [50,40,40,40,30,30,35,30,25,30,35,40,40,50,60,60,15,15, 5, 0]  #T
]

room_item = [
    [Item("绷带","可用于止血或捆绑", [2026,1,6,9,00,0]),Item("安眠药","对玩家使用后可以使其放弃挣扎", [2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0])], #医务室
    [Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),], #淋浴房
    [Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),], #日光房
    [Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),], #杂物处
    [Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),], #中庭
    [Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),], #接客室
    [Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),], #女厕
    [Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),], #会客厅
    [Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),], #玄关大厅
    [Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),], #审判庭入口过道
    [Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),], #食堂
    [Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),], #厨房
    [Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),], #审判庭
    [Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),], #牢房
    [Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),], #焚烧炉
    [Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),], #惩罚室
    [Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),], #娱乐室
    [Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),], #工作室
    [Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),], #2F大厅
    [Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),Item("","",[2026,1,6,9,00,0]),]  #图书室
]

def get_distance(player):
    global player_list,map_dict,map_len
    start_address = map_dict[player.location]
    distance = []
    for i in player_list:
        end_address = map_dict[i.location]
        distance.append(map_len[start_address][end_address])
    player.distance = distance
    return distance

def time_up(month,date,hour,minute,second):
    time_now = time_start.copy()
    time_now[1] = time_start[1] + month
    time_now[2] = time_start[2] + date
    time_now[3] = time_start[3] + hour
    time_now[4] = time_start[4] + minute
    time_now[5] = time_start[5] + second
    if time_now[5] >= 60:
        time_now[5] -= 60
        time_now[4] += 1
    if time_now[4] >= 60:
        time_now[4] -= 60
        time_now[3] += 1
    if time_now[3] >= 24:
        time_now[3] -= 24
        time_now[2] += 1
    if time_now[2] > 31:
        time_now[2] -= 31
        time_now[1] += 1
    if time_now[1] > 12:
        time_now[1] -= 12
        time_now[0] += 1
    return time_now

def get_time():
    global time_real_start
    time_change = time.time() - time_real_start
    time_now = time_up((int(time_change)//86400) % 31,(int(time_change)//3600) % 24,(int(time_change) // 60) % 60,int(time_change) % 60,0)
    return time_now

def create_player():
    global player_list
    num = int(input("请输入游玩人数："))
    print("-"*30)
    for i in range(1,num+1):
        print("1.Shiro 2.Person2 3.Person3 4.Person4")
        choice_people = 0
        while choice_people not in [1, 2, 3, 4]:
            try:
                choice_people = int(input(f"请玩家{i}选择人物："))
                player_list.append(p_list[choice_people - 1](i-1,num))
                player_list[i - 1].nickname = input(f"请玩家{i}输入昵称")
            except:
                choice_people = 0
                print("选择有误，重新输入")
    print("人物创建完成")
    print(f"当前共{len(player_list)}名玩家参与游戏")
    killer = random.randint(0,num-1)
    player_list[killer].killer = 1
    print("一名玩家已成为魔女")

def activate():
    global player_list  #活动函数
    for i in player_list:
        get_distance(i)
        print("-"*10)
        if i.life <=0:
            print(f"玩家{i.nickname}已经死亡，请等待游戏结束")
            continue
        print(f"{i.nickname}当前位置：{i.location}\n1.去别处看看 2.查看手机 3.发动魔法")
        if i.killer:
            print("4.攻击（游戏开始的前一小时不能攻击）")
        choice = 0
        while choice not in [1,2,3,4]:
            try:
                choice = int(input(f"玩家{i.nickname}进行操作"))
            except:
                choice = 0
                print("输入有误，重新输入")
        match choice:
            case 1:
                i.move()
            case 2:
                i.check_phone()
            case 3:
                i.magic()
            case 4:
                i.attack()

def game_start():
    #开始阶段，创建玩家对象，选择人物
    global player_list,dead_search
    create_player()
    print("-"*11,"游戏开始","-"*11)
    # 第一阶段-自由活动直到尸体被发现
    while not dead_search:
        activate()
        player_list_search = []
        for i in player_list:       # 尸体发现与否判断
            get_distance(i)
            if not i.killer or i.life:
                player_list_search.append(i)
        for i in player_list_search:
            for j in i.distance:
                if j == 0 and player_list[j].life == 0:
                    dead_search = 1
    #第二阶段-搜证阶段，每人5次行动机会
    for i in range(5):
        activate()
    #第三阶段-发言阶段，所有证据讨论完成后再进行一轮补充说明，最后结束进入投票
    #第四阶段-投票阶段


dead_search = 0 # 死者是否背发现，0-未被发现，1-已被发现
player_list = []
location_list = ["医务室","淋浴房","日光房","杂物处","中庭","接客室","女厕","会客厅","玄关大厅","审判庭入口过道",
                "食堂","厨房","审判庭","牢房","焚烧炉","惩罚室","娱乐室","工作室","2F大厅","图书室"]
p_list = [Shiro, Person2, Person3, Person4]
time_start = [2026,1,6,9,00,0]
time_real_start = time.time()
if __name__ == "__main__":
    game_start()
    