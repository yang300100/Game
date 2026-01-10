import random
import time
from random import choice


class Player:
    def __init__(self,player_id,conn,player_num):
        self.conn = conn  #玩家连接socket
        self.id = player_id   #id从0计数
        self.nickname = "no_name"
        self.life = 1
        self.bag = []
        self.location = "会客厅"
        self.killer = 0  #魔女标记
        self.distance = [0] * player_num  #列表中下标表示玩家id，数值表示距离
        self.magic_used = 1  #是否使用技能，未使用为1，使用后为0
        self.wechat = [[] for _ in range(player_num + 1)]   #私聊消息记录
        self.message_len = [0] * (player_num + 1)     #收到通知前消息变化量
        self.deadtime = []  #死亡时间记录

    def check_phone(self):
        global player_list
        send_to_player(self.id,f"时间：{get_time()[0]}年{get_time()[1]}月{int(get_time()[2])}日 {get_time()[3]}:{get_time()[4]}")
        send_to_player(self.id,"背包：")
        for i in self.bag:
            send_to_player(self.id,f"“{i.name}”")
        send_to_player(self.id,"")
        #新消息检测👇
        obj_send = 0
        for i in self.message_len:
            if i:
                if obj_send == len(player_list) + 1:
                    send_to_player(self.id,f"来自公共群聊的新消息：")
                    send_to_player(self.id,self.wechat[obj_send][-i:])
                    self.message_len[obj_send] = 0
                else:
                    send_to_player(self.id,f"来自{player_list[obj_send].nickname}的新消息：")
                    send_to_player(self.id,self.wechat[obj_send][-i:])
                    self.message_len[obj_send] = 0
            obj_send += 1
        #消息发送部分👇
        nickname_list = []
        for i in player_list:
            send_to_player(self.id,i.nickname+" ")
            nickname_list.append(i.nickname)
        send_to_player(self.id,"公共群聊")
        nickname_list.append("公共群聊")
        send_to_player(self.id,"")
        choose = get_message(self.id,"输入玩家昵称开启聊天，输入物品名称查看物品详情，输入“退出”退出手机\n")
        item_list = [i.name for i in self.bag]
        while choose != "退出":
            if choose in item_list:
                for i in self.bag:
                    if i.name == choose:
                        send_to_player(self.id,f"物品名称：{i.name}\n物品描述：{i.describe}\n获取时间：{i.get_time[0]}年{i.get_time[1]}月{i.get_time[2]}日 {i.get_time[3]}:{i.get_time[4]}\n物品类型：{i.type}")
            if choose in nickname_list:
                send_to_player(self.id,"聊天已开启，输入exit退出聊天")
                obj_id = 0
                for i in player_list:
                    if i.nickname == choose:
                        obj_id = i.id
                if choose == "公共群聊":
                    obj_id = len(player_list)+ 1
                send_to_player(self.id,"历史消息：-----")
                for i in self.wechat[obj_id]:
                    send_to_player(self.id,i)
                send_to_player(self.id,"新消息：------")
                inp = get_message(self.id)
                while inp != "exit":
                    if choose == "公共群聊":
                        for i in player_list:
                            i.wechat[obj_id].append(f"{self.nickname}:"+inp)
                            i.message_len[obj_id] += 1
                            send_to_player(self.id,inp + f":{self.nickname}")
                            inp = get_message(self.id)
                    else:
                        self.wechat[obj_id].append(f"{self.nickname}:"+inp) # 添加消息到自己消息列表中
                        player_list[obj_id].wechat[self.id].append(f"{self.nickname}:"+inp)# 添加消息到对方消息列表中
                        player_list[obj_id].message_len[self.id] += 1   #修改对方消息变化量
                        send_to_player(self.id,inp+f":{self.nickname}")
                        inp = get_message(self.id)
            choose = get_message(self.id,"输入玩家昵称开启聊天，输入物品名称查看物品详情，输入“退出”退出手机")

    def move(self):
        choose = ""
        while choose not in location_list:
            try:
                send_to_player(self.id,location_list)
                choose = get_message(self.id,f"{self.nickname}要去哪里？")
            except:
                choose = ""
                send_to_player(self.id,"输入错误，重新输入")
        self.location = choose
        # 下面跟进距离计算代码
        get_distance(self)
        #到达地点后，获取其中物品
        room_id = location_list.index(self.location)
        if not room_item[room_id]:
            send_to_player(self.id,f"你在{self.location}没有发现任何物品")
            return
        random_item = random.choice(room_item[room_id])
        if random_item.type == "物品":
            self.bag.append(random_item)
            room_item[room_id].remove(random_item)
            send_to_player(self.id,f"你在{self.location}发现了物品：“{random_item.name}”已添加至背包")
        else:
            self.bag.append(random_item)
            send_to_player(self.id,f"你在{self.location}发现了情报：“{random_item.name}”已添加至背包")

    def attack(self):
        global time_start, player_list, time_real_start
        if self.killer == 0 or int(time.time()-time_real_start) < 60:  # 开局前一小时以及普通人不能攻击
            send_to_player(self.id,"不可攻击其他人物，跳过本回合")
            return
        killer_list_id = []
        get_distance(self)
        killer_list_nickname = []
        for i in range(0, len(self.distance)):
            if self.distance[i] <= 1 and player_list[i].life == 1 and player_list[i].id != self.id:
                killer_list_id.append(i)
                killer_list_nickname.append(player_list[i].nickname)
        send_to_player(self.id,"可选目标为：")
        all_send = ""
        for i in killer_list_nickname:
            all_send = all_send.join(i+" ")
        send_to_player(self.id,all_send)
        if not killer_list_nickname:
            send_to_player(self.id,"攻击失败：附近无目标")
            return
        choose = ""
        while choose not in killer_list_nickname:
            choose = get_message(self.id,f"{self.nickname}要选择谁？")
        killer_choose = get_message(self.id,"选择杀人方式：徒手攻击/使用道具\n注：徒手攻击会造成较大的声音，并可能散落更多线索；使用道具则相对安静，但会留下有关使用道具的特殊线索\n")
        while killer_choose not in ["徒手攻击","使用道具"]:
            killer_choose = get_message(self.id,"输入有误，重新输入")
        item_name_list = []
        if killer_choose == "使用道具" and self.bag:
            send_to_player(self.id,"请提交使用的道具：")
            for i in self.bag:
                send_to_player(self.id,f"“{i.name}”")
                item_name_list.append(i.name)
            send_to_player(self.id,"")
            item_choose = ""
            while item_choose not in item_name_list:
                item_choose = get_message(self.id,"输入道具名称")
            for i in self.bag[:]:#遍历原列表副本，防止下标计数错误
                if i.name == item_choose and i.type == "情报":
                    send_to_player(self.id,"攻击失败：情报类物品不可用于攻击")
                    break
                am_or_pm = ""
                if i.name == item_choose and i.type == "物品":
                    if 6 < get_time()[3] < 12:
                        am_or_pm="上午"
                    elif 12 <= get_time()[3] < 19:
                        am_or_pm="下午"
                    elif 19 <= get_time()[3] <= 24:
                        am_or_pm="晚上"
                    elif 0 <= get_time()[3] <= 6:
                        am_or_pm="凌晨"
                    room_item[location_list.index(self.location)].append(Item(f"{choose}的尸体",f"被杀害的尸体，死亡时间大约在{get_time()[1]}月{get_time()[2]}日的{am_or_pm}",[2026,1,6,9,00,0],"情报")) #在现场留下尸体
                    room_item[location_list.index(self.location)].append(Item("凶器："+ i.name, i.describe, i.get_time, "情报")) #将使用后的道具留在现场，并添加凶器标签
                    #给所有距离小于15的玩家添加物品：奇怪的声音
                    for j in range(0,len(self.distance)):
                        if self.distance[j] <= 15 and player_list[j].id != self.id:
                            player_list[j].bag.append(Item("奇怪的声音",f"在{get_time()[1]}月{get_time()[2]}日{get_time()[3]}：{get_time()[4]}分时，你听到附近传来了一些奇怪的声音",get_time(),"情报"))
                    self.bag.remove(i)
                    send_to_player(self.id,f"道具“{i.name}”已使用")
                    for j in player_list:
                        if j.nickname == choose:
                            j.life = 0
                            j.deadtime = get_time()
                            break
                    break
        elif killer_choose == "使用道具" and not self.bag:
            send_to_player(self.id,"攻击失败：无道具")
        else:
            send_to_player(self.id,"使用徒手攻击")
            for j in range(0,len(self.distance)):
                if self.distance[j] <= 55 and player_list[j].id != self.id:
                    player_list[j].bag.append(Item("奇怪的声音",f"在{get_time()[1]}月{get_time()[2]}日{get_time()[3]}：{get_time()[4]}分时，你听到哪里传来了一些奇怪的声音",get_time(),"情报"))
            for j in player_list:
                if j.nickname == choose:
                    am_or_pm = ""
                    if 6 < get_time()[3] < 12:
                        am_or_pm="上午"
                    elif 12 <= get_time()[3] < 19:
                        am_or_pm="下午"
                    elif 19 <= get_time()[3] <= 24:
                        am_or_pm="晚上"
                    elif 0 <= get_time()[3] <= 6:
                        am_or_pm="凌晨"
                    room_item[location_list.index(self.location)].append(Item(f"{choose}的尸体",f"被杀害的尸体，死亡时间大约在{get_time()[1]}月{get_time()[2]}日的{am_or_pm}",[2026,1,6,9,00,0],"情报")) #在现场留下尸体
                    j.life = 0
                    j.deadtime = get_time()
                    break

class Item:
    def __init__(self,name,describe,time_item,item_type):
        self.name = name    #物品名称       
        self.describe = describe    #描述
        self.get_time = time_item   #获取时间
        self.type = item_type #物品类型：情报/证据

class Shiro(Player):
    def __init__(self,player_id,conn,player_num):
        super().__init__(player_id,conn,player_num)
        self.name = "Shiro"
    def magic(self):
        self.magic_used = 0 #置0显示魔法已使用
        choose = 0
        while choose not in [1,2]:
            try:
                choose = int(get_message(self.id,"使用魔法：伪证 \n1.将一项证据显示为伪证  2.创造一个伪证"))
            except:
                choose = 0
                send_to_player(self.id,"输入有误，重新输入")
        if choose == 1:
            if not self.bag:
                self.magic_used = 1
                send_to_player(self.id,"魔法使用失败：背包中无物品")
            else:
                j=0
                for i in self.bag:
                    j+=1
                    send_to_player(self.id,f"{j}."+i.name)
                choose = 0
                while choose not in range(1,len(self.bag)+1):
                    try:
                        choose = int(get_message(self.id,"选择要显示为伪证的物品"))
                    except:
                        choose = 0
                        send_to_player(self.id,"输入有误，重新输入")
                self.bag[choose-1].name = "伪证：" + self.bag[choose-1].name
                send_to_player(self.id,"你选择的证据已添加“伪证“标签")
        else:
            send_to_player(self.id,"输入伪造物品的名字，描述以及获得时间")
            name = get_message(self.id,"为伪证命名")
            describe = get_message(self.id,"为伪证填写描述")
            time_false = []
            while len(time_false) != 12:
                time_false = get_message(self.id,"填写伪证的获取时间，格式为：202509010101（2025年9月1日1时1分）")
                if len(time_false) != 12:
                    send_to_player(self.id,"时间输入长度有误，重新输入")
                elif not time_false.isdigit():
                    send_to_player(self.id,"时间输入格式有误，重新输入")
                    time_false=[]
            time_li = [int(time_false[:4]),int(time_false[4:6]),int(time_false[6:8]),int(time_false[8:10]),int(time_false[10:])]
            false_item = Item("伪证："+name,describe,time_li,"情报")
            self.bag.append(false_item)
            send_to_player(self.id,"伪造完成，伪证已添加至背包")

class Person2(Player):
    def __init__(self,player_id,conn,player_num):
        super().__init__(player_id,conn,player_num)
        self.name = "Person2"
    def magic(self):
        pass

class Person3(Player):
    def __init__(self,player_id,conn,player_num):
        super().__init__(player_id,conn,player_num)
        self.name = "Person3"
    def magic(self):
        pass

class Person4(Player):
    def __init__(self,player_id,conn,player_num):
        super().__init__(player_id,conn,player_num)
        self.name = "Person4"
    def magic(self):
        pass

map_dict = {"医务室":0, "淋浴房":1, "日光房":2, "杂物处":3, "中庭":4, "接客室":5, "女厕":6, "会客厅":7, "玄关大厅":8, "审判庭入口过道":9,
            "食堂": 10, "厨房":11, "审判庭":12, "牢房":13, "焚烧炉":14, "惩罚室":15, "娱乐室":16, "工作室":17, "2F大厅":18, "图书室":19}

map_len = [
    # A  B  C  D  E  F  G  H  I  J  K  L  M  N  O  P  Q  R  S  T  楼层间距离20
    [ 0,20,15, 5,20,25,15,20,25,30,35,40,40,50,60,60,50,50,45,50], #A
    [20, 0,20,15,10,15,20,20,20,25,30,35,35,45,55,55,45,45,40,45], #B
    [15,20, 0, 5,15,20, 5,10,15,20,25,30,30,40,50,50,40,40,35,40], #C
    [ 5,15, 5, 0, 5,10, 5,10,15,20,25,30,30,40,50,50,40,40,35,40], #D
    [20,10,15, 5, 0, 5,15, 5, 5,10,15,20,20,30,40,40,30,30,25,30], #E
    [25,15,20,10, 5, 0,25,15, 5,10,15,20,20,30,40,40,30,30,25,30], #F
    [15,20, 5, 5,15,25, 0, 5,10,15,20,25,25,35,45,45,35,35,30,35], #G
    [20,20,10,10, 5, 5,10, 0, 5,10,15,20,20,30,40,40,30,30,25,30], #H
    [25,20,15,15, 5, 5,10, 5, 0, 5,10,15,15,25,35,35,25,25,20,25], #I
    [30,25,20,20,10,10,15,10, 5, 0, 5,10,10,30,40,40,30,30,25,30], #J
    [35,30,25,25,15,15,20,15,10, 5, 0, 5, 5,35,45,45,35,35,30,35], #K
    [40,35,30,30,20,20,25,20,15,10, 5, 0, 5,40,50,50,40,40,35,40], #L
    [40,35,30,30,20,20,25,20,15,10, 5, 5, 0,40,50,50,40,40,35,40], #M
    [50,45,40,40,30,30,35,30,25,30,35,40,40, 0,20,20,50,50,45,50], #N
    [60,55,50,50,40,40,45,40,35,40,45,50,50,20, 0,30,60,60,55,60], #O
    [60,55,50,50,40,40,45,40,35,40,45,50,50,20,30, 0,60,60,55,60], #P
    [50,45,40,40,30,30,35,30,25,30,35,40,40,50,60,60, 0,15, 5,15], #Q
    [50,45,40,40,30,30,35,30,25,30,35,40,40,50,60,60,15, 0, 5,15], #R
    [45,40,35,35,25,25,30,25,20,25,30,35,35,45,55,55, 5, 5, 0, 5], #S
    [50,45,40,40,30,30,35,30,25,30,35,40,40,50,60,60,15,15, 5, 0]  #T
]

room_item = [
    [Item("绷带","可用于止血或捆绑",[2026,1,6,9,00,0],"道具"),Item("安眠药","对玩家使用后可以使其放弃挣扎",[2026,1,6,9,00,0],"道具"),Item("毒药","可用于杀人",[2026,1,6,9,00,0],"道具")], #医务室
    [Item("隔音很好的墙壁","这间屋子的墙壁隔音很好，外边更不容易听到屋子里的声音",[2026,1,6,9,00,0],"情报"),Item("破碎的镜子","淋浴房中年久失修的镜子已经碎裂，玻璃渣散落一地",[2026,1,6,9,00,0],"道具")], #淋浴房
    [Item("test1","情报类物品",[2026,1,6,9,00,0],"情报"),Item("test2","道具类物品",[2026,1,6,9,00,0],"道具"),Item("test3","道具类物品",[2026,1,6,9,00,0],"道具")], #日光房
    [Item("test1","情报类物品",[2026,1,6,9,00,0],"情报"),Item("test2","道具类物品",[2026,1,6,9,00,0],"道具"),Item("test3","道具类物品",[2026,1,6,9,00,0],"道具")], #杂物处
    [Item("test1","情报类物品",[2026,1,6,9,00,0],"情报"),Item("test2","道具类物品",[2026,1,6,9,00,0],"道具"),Item("test3","道具类物品",[2026,1,6,9,00,0],"道具")], #中庭
    [Item("test1","情报类物品",[2026,1,6,9,00,0],"情报"),Item("test2","道具类物品",[2026,1,6,9,00,0],"道具"),Item("test3","道具类物品",[2026,1,6,9,00,0],"道具")], #接客室
    [Item("test1","情报类物品",[2026,1,6,9,00,0],"情报"),Item("test2","道具类物品",[2026,1,6,9,00,0],"道具"),Item("test3","道具类物品",[2026,1,6,9,00,0],"道具")], #女厕
    [Item("test1","情报类物品",[2026,1,6,9,00,0],"情报"),Item("test2","道具类物品",[2026,1,6,9,00,0],"道具"),Item("test3","道具类物品",[2026,1,6,9,00,0],"道具")], #会客厅
    [Item("test1","情报类物品",[2026,1,6,9,00,0],"情报"),Item("test2","道具类物品",[2026,1,6,9,00,0],"道具"),Item("test3","道具类物品",[2026,1,6,9,00,0],"道具")], #玄关大厅
    [Item("test1","情报类物品",[2026,1,6,9,00,0],"情报"),Item("test2","道具类物品",[2026,1,6,9,00,0],"道具"),Item("test3","道具类物品",[2026,1,6,9,00,0],"道具")], #审判庭入口过道
    [Item("test1","情报类物品",[2026,1,6,9,00,0],"情报"),Item("test2","道具类物品",[2026,1,6,9,00,0],"道具"),Item("test3","道具类物品",[2026,1,6,9,00,0],"道具")], #食堂
    [Item("test1","情报类物品",[2026,1,6,9,00,0],"情报"),Item("test2","道具类物品",[2026,1,6,9,00,0],"道具"),Item("test3","道具类物品",[2026,1,6,9,00,0],"道具")], #厨房
    [Item("test1","情报类物品",[2026,1,6,9,00,0],"情报"),Item("test2","道具类物品",[2026,1,6,9,00,0],"道具"),Item("test3","道具类物品",[2026,1,6,9,00,0],"道具")], #审判庭
    [Item("test1","情报类物品",[2026,1,6,9,00,0],"情报"),Item("test2","道具类物品",[2026,1,6,9,00,0],"道具"),Item("test3","道具类物品",[2026,1,6,9,00,0],"道具")], #牢房
    [Item("test1","情报类物品",[2026,1,6,9,00,0],"情报"),Item("test2","道具类物品",[2026,1,6,9,00,0],"道具"),Item("test3","道具类物品",[2026,1,6,9,00,0],"道具")], #焚烧炉
    [Item("test1","情报类物品",[2026,1,6,9,00,0],"情报"),Item("test2","道具类物品",[2026,1,6,9,00,0],"道具"),Item("test3","道具类物品",[2026,1,6,9,00,0],"道具")], #惩罚室
    [Item("test1","情报类物品",[2026,1,6,9,00,0],"情报"),Item("test2","道具类物品",[2026,1,6,9,00,0],"道具"),Item("test3","道具类物品",[2026,1,6,9,00,0],"道具")], #娱乐室
    [Item("test1","情报类物品",[2026,1,6,9,00,0],"情报"),Item("test2","道具类物品",[2026,1,6,9,00,0],"道具"),Item("test3","道具类物品",[2026,1,6,9,00,0],"道具")], #工作室
    [Item("test1","情报类物品",[2026,1,6,9,00,0],"情报"),Item("test2","道具类物品",[2026,1,6,9,00,0],"道具"),Item("test3","道具类物品",[2026,1,6,9,00,0],"道具")], #2F大厅
    [Item("test1","情报类物品",[2026,1,6,9,00,0],"情报"),Item("test2","道具类物品",[2026,1,6,9,00,0],"道具"),Item("test3","道具类物品",[2026,1,6,9,00,0],"道具")]  #图书室
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

def create_player(player_id,player_name,conn,player_num):
    global player_list,p_name_list
    print(1)
    conn.send("Shiro Person2 Person3 Person4".encode(ENCODING))
    conn.send("请玩家选择人物：".encode(ENCODING))
    while True:
        print(2)
        choose_people = conn.recv(BUFFER_SIZE).decode(ENCODING).strip()
        if choose_people in p_name_list:
            break
    print(choose_people)
    player_list.append(p_list[p_name_list.index(choose_people)](player_id,conn,player_num))
    player_list[player_id].nickname = player_name
    # send_to_player(player_id,"人物创建完成")
    print("玩家人物创建完成")
    conn.send("人物创建完成".encode(ENCODING))

def activate(player):
    global player_list  #活动函数
    while True:
        get_distance(player)
        send_to_player(player.id,"-"*10)
        if player.life <=0:
            send_to_player(player.id,f"玩家{player.nickname}已经死亡，请等待游戏结束")
            continue
        send_to_player(player.id,f"{player.nickname}当前位置：{player.location}\n1.去别处看看 2.查看手机 3.发动魔法")
        if player.killer:
            send_to_player(player.id,"4.攻击（游戏开始的前一小时不能攻击）")
        choose = 0
        while choose not in [1,2,3,4]:
            try:
                choose = int(get_message(player.id,f"玩家{player.nickname}进行操作"))
            except:
                choose = 0
                send_to_player(player.id,"输入有误，重新输入")
        match choose:
            case 1:
                player.move()
            case 2:
                player.check_phone()
            case 3:
                player.magic()
            case 4:
                player.attack()

def game_start():
    #开始阶段，创建玩家对象，选择人物
    global player_list,dead_search
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
p_name_list = ["Shiro", "Person2", "Person3", "Person4"]
time_start = [2026,1,6,9,00,0]
time_real_start = time.time()

def get_message(player_id,message=""):
    global player_list
    player = player_list[player_id]
    if message:
        send_to_player(player.id,message)
    while True:
        recv_data = player.conn.recv(BUFFER_SIZE).decode(ENCODING).strip()
        if recv_data:
            return recv_data

import socket
import threading

HOST = "192.168.16.112"
PORT = 9999
BUFFER_SIZE = 1024
ENCODING = "utf-8"

# 玩家ID自增器，保证每个玩家ID唯一
player_id_counter = 0
# 线程锁：保证多线程操作玩家字典时不冲突（线程安全必备）
lock = threading.Lock()
max_player_num = 1#这里设置游玩人数
def broadcast(message, exclude_conn=None):
    global player_list
    with lock:  # 加锁保证线程安全
        for i in player_list:
            if i.id not in exclude_conn:
                try:
                    i.conn.send(message.encode(ENCODING))
                except:
                    remove_player_by_conn(i)

def send_to_player(player_id, message):
    global player_list,lock
    with lock:
        if player_id in [i for i in range(len(player_list))]:
            conn = player_list[player_id].conn
            try:
                conn.send(message.encode(ENCODING))
            except:
                remove_player_by_conn(player_list[player_id])

def remove_player_by_conn(player):
    global player_list,lock
    with lock:
        if player in player_list:
            print(f"[系统] 玩家【{player.name}】(ID:{player.id}) 已掉线/退出游戏")
            # 广播玩家退出的系统公告
            broadcast(f"[系统公告] 玩家【{player.name}】已退出游戏！当前在线人数：{len(player_list)-1}")
            # 从全局列表删除玩家对象，自动释放所有属性
            player_list.remove(player)
            # 关闭socket连接
            try:
                player.conn.close()
            except:
                pass

def handle_client(conn, addr):
    global player_id_counter, player_list,max_player_num
    player_name = ""
    try:
        conn.send("请输入你的游戏昵称：".encode(ENCODING))
        player_name = conn.recv(BUFFER_SIZE).decode(ENCODING).strip()
        while not player_name:  # 昵称不能为空
            conn.send("昵称不能为空！请重新输入：".encode(ENCODING))
            player_name = conn.recv(BUFFER_SIZE).decode(ENCODING).strip()
        with lock:
            create_player(player_id_counter,player_name,conn,max_player_num)
            player_id_counter += 1

        # send_to_player(player_id_counter-1,"test1")
        print(player_list)
        player = player_list[player_id_counter-1]

        # 3. 通知所有人：新玩家加入
        welcome_msg = f"[系统公告] 玩家【{player.nickname}】(ID:{player.id}) 加入游戏！当前在线人数：{len(player_list)}"
        broadcast(welcome_msg,[0])
        player.conn.send(f"✅ 登录成功！你的玩家ID：{player.id}\n当前在线人数：{len(player_list)}".encode(ENCODING))
        print(f"[系统] 新玩家连接：{addr} → 【{player.nickname}】(ID:{player.id})")

        # =========================================================
        # ✅ ✅ ✅ 【你的游戏核心逻辑插入点 - 重中之重】✅ ✅ ✅
        # 说明：从这里开始，就是【玩家的消息循环】
        # 玩家在客户端输入的任何内容/操作指令，都会被服务端接收到，存到 recv_data 变量中
        # 你只需要在这里写：
        # 1. 判断玩家发来的消息/指令是什么（比如：出牌、投票、刀人、发言）
        # 2. 执行你的游戏规则（比如：判定出牌是否合法、计算血量、切换回合）
        # 3. 用 broadcast() 广播游戏结果/全局消息，用 send_to_player() 给指定玩家发私聊消息
        # =========================================================
        send_to_player(0,"消息发送")
        game_start()


    except Exception as e:
        print(f"[异常-在handle_cilent函数中] 玩家【{player_name}】异常：{e}")
    finally:
        if conn:
            remove_player_by_conn(conn)


def main():
    """服务端主函数：启动监听，接收客户端连接"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(100) 
    print(f"=====================================")
    print(f"游戏通信服务端已启动")
    print(f"监听地址：{HOST}:{PORT}")
    print(f"等待玩家连接中...")
    print(f"=====================================")

    while True:
        conn, addr = server_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        client_thread.start()


if __name__ == "__main__":
    main()