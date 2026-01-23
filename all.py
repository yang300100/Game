import random
import time
import socket
import threading
import base64
import hashlib

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
        self.magic_used = 1  #魔法剩余使用次数
        self.wechat = [[] for _ in range(player_num + 1)]   #私聊消息记录
        self.message_len = [0] * (player_num + 1)     #收到通知前消息变化量
        self.deadtime = []  #死亡时间记录
        self.dead_location = ""  #死亡地点记录
        self.dead_item = "" #死因记录
        self.jump_speak = 0  #是否跳过发言环节，跳过为1，不跳过为0
        self.send_message = 0   # 在发言阶段，此值为0时说明未被发送消息，发送消息后置1
        self.last_attack_time = 0   #魔女杀人冷却

    def check_phone(self):
        global player_list
        send_to_player(self.id,f"时间：{get_time()[0]}年{get_time()[1]}月{int(get_time()[2])}日 {get_time()[3]}:{get_time()[4]}\n")
        send_to_player(self.id,"背包：\n")
        for i in self.bag:
            send_to_player(self.id,f"“{i.name}” ")
        send_to_player(self.id,"\n")
        #新消息检测
        obj_send = 0
        for i in self.message_len:
            if i:
                if obj_send == len(player_list) + 1:
                    send_to_player(self.id,f"来自公共群聊的新消息：\n")
                    send_to_player(self.id,self.wechat[obj_send][-i:])
                    self.message_len[obj_send] = 0
                else:
                    send_to_player(self.id,f"来自{player_list[obj_send].nickname}的新消息：\n")
                    send_to_player(self.id,self.wechat[obj_send][-i:])
                    self.message_len[obj_send] = 0
            obj_send += 1
        #消息发送部分
        nickname_list = []
        send_to_player(self.id,"可聊天对象：\n")
        name_str = ""
        for i in player_list:
            if i.id == self.id:
                continue
            name_str += i.nickname + " "
            nickname_list.append(i.nickname)
        nickname_list.append("公共群聊")
        send_to_player(self.id,name_str+"公共群聊\n")  
        choose = get_message(self.id,"输入玩家昵称开启聊天，输入物品名称查看物品详情，输入“退出”退出手机\n")
        item_list = [i.name for i in self.bag]
        while choose != "退出":
            if choose in item_list:
                for i in self.bag:
                    if i.name == choose:
                        send_to_player(self.id,f"物品名称：{i.name}\n物品描述：{i.describe}\n获取时间：{i.get_time[0]}年{i.get_time[1]}月{i.get_time[2]}日 {i.get_time[3]}:{i.get_time[4]}\n物品类型：{i.type}\n")
            if choose in nickname_list:
                send_to_player(self.id,"聊天已开始，输入exit退出聊天\n")
                obj_id = 0
                for i in player_list:
                    if i.nickname == choose:
                        obj_id = i.id
                if choose == "公共群聊":
                    obj_id = len(player_list)+ 1
                send_to_player(self.id,"历史消息：-----\n")
                for i in self.wechat[obj_id]:
                    send_to_player(self.id,i)
                send_to_player(self.id,"新消息：------\n")
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
                        send_to_player(self.id,inp+f":{self.nickname}\n")
                        inp = get_message(self.id)
            choose = get_message(self.id,"输入玩家昵称开启聊天，输入物品名称查看物品详情，输入“退出”退出手机\n")
    
    def move(self):
        global location_list,noa_picture_search
        choose = ""
        while any(obj.name == choose for obj in location_list):
            room_str = ""
            send_to_player(self.id,f"可选地点：")
            for i in location_list:
                room_str += i.name + " "
            send_to_player(self.id,room_str+"\n")
            choose = get_message(self.id,f"{self.nickname}要去哪里\n")
            if any(obj.name == choose for obj in location_list):
                send_to_player(self.id,"输入错误，重新输入\n")
        
        for i in range(5):
            send_to_player(self.id,f"\r正在前往{choose}的路上："+ "█" * (i + 1) * (20 // 5) + "░" * (20 - (i + 1) * (20 // 5)))
            time.sleep(1)
        self.location = choose
        get_distance(self)
        send_to_player(self.id,f"已到达{choose}\n")
        seen_people = set()
        
        send_to_player(self.id,f"正在搜寻房间中的物品...（搜寻物品时不会注意到外界情况）\n")
        for i in range(20):
            send_to_player(self.id,"\r搜索进度："+ "█" * (i + 1) * (20 // 20) + "░" * (20 - (i + 1) * (20 // 20)))
            time.sleep(1)
        send_to_player(self.id,"\n搜寻完成！\n")
        for i in range(len(self.distance)):  
            if self.distance[i] == 0 and i != self.id and i not in seen_people:
                self.bag.append(Item(f"与{player_list[i].nickname}的相遇",f"在{get_time()[1]}月{get_time()[2]}日{get_time()[3]}：{get_time()[4]}分时,你与{player_list[i].nickname}在{choose}相遇了",get_time(),"情报"))
                send_to_player(self.id,f"你在{choose}遇到了{player_list[i].nickname}\n获得情报：与{player_list[i].nickname}的相遇，已添加至背包\n")
                seen_people.add(i)
            time.sleep(1)
        #到达地点后，获取其中物品
        room_id = location_list.index(self.location)
        if not location_list[room_id].item:
            send_to_player(self.id,f"你在{self.location}没有发现任何物品\n")
            return
        random_item = random.choice(location_list[room_id].item)
        if random_item.type == "道具":
            random_item.get_time = get_time()
            self.bag.append(random_item)
            location_list[room_id].item.remove(random_item)
            send_to_player(self.id,f"你在{self.location}发现了道具：“{random_item.name}”已添加至背包\n")
            if random_item.name == "诺亚的画作":
                noa_picture_search = 1
        else:
            random_item.get_time = get_time()
            self.bag.append(random_item)
            send_to_player(self.id,f"你在{self.location}发现了情报：“{random_item.name}”已添加至背包\n")
    
    def attack(self):
        global time_start, player_list, time_real_start ,dead_list,location_list
        if (time.time() - self.last_attack_time) / 60 <= 3:
            send_to_player(self.id,"三分钟内不可再次杀人")
            return
        if self.killer == 0 or int(time.time()-time_real_start) < 60:  # 开局前一小时以及普通人不能攻击
            send_to_player(self.id,"不可攻击其他玩家，跳过本回合\n")
            return
        killer_list_id = []
        get_distance(self)
        killer_list_nickname = []
        for i in range(0, len(self.distance)):
            if self.distance[i] <= 1 and player_list[i].life == 1 and player_list[i].id != self.id:
                killer_list_id.append(i)
                killer_list_nickname.append(player_list[i].nickname)
        send_to_player(self.id,"可选目标为：")
        for i in killer_list_nickname:
            send_to_player(self.id,f"“{i}” ")
        send_to_player(self.id,"\n")
        if not killer_list_nickname:
            send_to_player(self.id,"攻击失败：附近无目标\n")
            return
        choose = ""
        while choose not in killer_list_nickname:
            choose = get_message(self.id,f"{self.nickname}要选择谁？\n")
        killer_choose = get_message(self.id,"选择杀人方式：徒手攻击/使用道具\n注：徒手攻击会造成较大的声音，并可能散落更多线索；使用道具则相对安静，但会留下有关使用道具的特殊线索\n")
        while killer_choose not in ["徒手攻击","使用道具"]:
            killer_choose = get_message(self.id,"输入有误，重新输入\n")
        item_name_list = []
        if killer_choose == "使用道具" and self.bag:
            send_to_player(self.id,"请提交使用的道具：")
            for i in self.bag:
                send_to_player(self.id,f"“{i.name}”")
                item_name_list.append(i.name)
            send_to_player(self.id,"\n")
            item_choose = ""
            while item_choose not in item_name_list:
                item_choose = get_message(self.id,"输入道具名称\n")
            for i in self.bag[:]:#遍历原列表副本，防止下标计数错误
                if i.name == item_choose and i.type == "情报":
                    send_to_player(self.id,"攻击失败：情报类物品不可用于攻击\n")
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
                    for j in location_list:
                        if j.name == self.lcoation:
                            j.item.append(Item(f"{choose}的尸体",f"被杀害的尸体，死亡时间大约在{get_time()[1]}月{get_time()[2]}日的{am_or_pm}",[2026,1,6,9,00,0],"情报"))
                            j.item.append(Item("凶器："+ i.name, i.describe, [2026,1,6,9,00,0], "情报"))
                    # room_item[location_list.index(self.location)].append(Item(f"{choose}的尸体",f"被杀害的尸体，死亡时间大约在{get_time()[1]}月{get_time()[2]}日的{am_or_pm}",[2026,1,6,9,00,0],"情报")) #在现场留下尸体
                    # room_item[location_list.index(self.location)].append(Item("凶器："+ i.name, i.describe, i.get_time, "情报")) #将使用后的道具留在现场，并添加凶器标签
                    #给所有距离小于15的玩家添加物品：奇怪的声音
                    for j in range(0,len(self.distance)):
                        if self.distance[j] <= 15 and player_list[j].id != self.id:
                            player_list[j].bag.append(Item("奇怪的声音",f"在{get_time()[1]}月{get_time()[2]}日{get_time()[3]}：{get_time()[4]}分时，你听到附近传来了一些奇怪的声音",get_time(),"情报"))
                    self.bag.remove(i)
                    send_to_player(self.id,f"道具“{i.name}”已使用\n")
                    for j in player_list:
                        if j.nickname == choose:
                            j.life = 0
                            j.deadtime = get_time()
                            dead_list.append(j.id)
                            j.dead_location = self.location
                            j.dead_item = i.name
                            self.last_attack_time = time.time()
                            break
                    break
        elif killer_choose == "使用道具" and not self.bag:
            send_to_player(self.id,"攻击失败：无道具\n")
        else:
            send_to_player(self.id,"使用徒手攻击\n")
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
                    # room_item[location_list.index(self.location)].append(Item(f"{choose}的尸体",f"被杀害的尸体，死亡时间大约在{get_time()[1]}月{get_time()[2]}日的{am_or_pm}",[2026,1,6,9,00,0],"情报")) #在现场留下尸体
                    for i in location_list:
                        if i.name == self.lcoation:
                            i.item.append(Item(f"{choose}的尸体",f"被杀害的尸体，死亡时间大约在{get_time()[1]}月{get_time()[2]}日的{am_or_pm}",[2026,1,6,9,00,0],"情报"))
                    j.life = 0
                    j.deadtime = get_time()
                    dead_list.append(j.id)
                    j.dead_location = self.location
                    j.dead_item = "徒手"
                    self.last_attack_time = time.time()
                    break

class Item:
    def __init__(self,name,describe,time_item,item_type):
        self.name = name    #物品名称       
        self.describe = describe    #描述
        self.get_time = time_item   #获取时间
        self.type = item_type #物品类型：情报/道具

class Room:
    def __init__(self,id,name,distance,wall,item):
        self.name = name
        self.id = id
        self.distance = distance
        self.wall = wall            # 0为没有墙壁
        self.item = item

class Ema(Player):
    def __init__(self, player_id, conn, player_num):
        super().__init__(player_id, conn, player_num)
        self.name = "Ema"
    def magic(self):
        pass

class Noa(Player):
    def __init__(self, player_id, conn, player_num):
        super().__init__(player_id, conn, player_num)
        self.name = "Noa"
        random.choice(location_list).item.append(Item("诺亚的画作","诺亚不使用魔法时绘制的画作，似乎并不想让别人看到",[2026,1,6,9,0,0],"道具"))
        global noa_picture_search
        noa_picture_search = 0
    def magic(self):
        if self.killer:
            pass
        else:
            pass


class Shiro(Player):
    def __init__(self,player_id,conn,player_num):
        super().__init__(player_id,conn,player_num)
        self.name = "Shiro"
    def magic(self):
        choose = 0
        while choose not in [1,2]:
            try:
                send_to_player(self.id,f"魔法剩余使用次数{self.magic_used}/1次\n")
                send_to_player(self.id,"使用魔法：伪证  请选择: \n")
                choose = int(get_message(self.id,"1.将一项证据显示为伪证  2.创造一个伪证\n"))
            except:
                choose = 0
                send_to_player(self.id,"输入有误，重新输入\n")
        if choose == 1:
            if not self.bag:
                self.magic_used = 1
                send_to_player(self.id,"魔法使用失败：背包中无物品\n")
            else:
                j=0
                for i in self.bag:
                    j+=1
                    send_to_player(self.id,f"{j}."+i.name)
                choose = 0
                while choose not in range(1,len(self.bag)+1):
                    try:
                        choose = int(get_message(self.id,"选择要显示为伪证的物品\n"))
                    except:
                        choose = 0
                        send_to_player(self.id,"输入有误，重新输入\n")
                self.bag[choose-1].name = "伪证：" + self.bag[choose-1].name
                send_to_player(self.id,"你选择的证据已添加“伪证“标签\n")
                self.magic_used = 0
        else:
            send_to_player(self.id,"输入伪造物品的名字，描述以及获得时间\n")
            name = get_message(self.id,"为伪证命名\n")
            describe = get_message(self.id,"为伪证填写描述\n")
            time_false = []
            while len(time_false) != 12:
                time_false = get_message(self.id,"填写伪证的获取时间，格式为：202509010101（2025年9月1日1时1分）\n")
                if len(time_false) != 12:
                    send_to_player(self.id,"时间输入长度有误，重新输入\n")
                elif not time_false.isdigit():
                    send_to_player(self.id,"时间输入格式有误，重新输入\n")
            time_li = [int(time_false[:4]),int(time_false[4:6]),int(time_false[6:8]),int(time_false[8:10]),int(time_false[10:])]
            false_item = Item("伪证："+name,describe,time_li,"情报")
            self.bag.append(false_item)
            send_to_player(self.id,"伪造完成，伪证已添加至背包\n")
            self.magic_used = 0

class Meruru(Player):
    def __init__(self,player_id,conn,player_num):
        super().__init__(player_id,conn,player_num)
        self.name = "Meruru"
    def magic(self):
        global player_list
        send_to_player(self.id,"使用魔法:验尸\n")
        send_to_player(self.id,f"魔法剩余使用次数{self.magic_used}/1次\n")
        choose = ""
        if dead_list:
            for i in dead_list:
                if player_list[i].dead_location != self.location:
                    send_to_player(self.id,"魔法使用失败：不在尸体发现地点\n")
                    return    
                else:
                    if self.magic_used:
                        self.magic_used = 0 #置0显示魔法已使用
                        send_to_player(self.id,"验尸中...\n")
                        time.sleep(5)
                        send_to_player(self.id,f"验尸完成！{player_list[i].nickname}的死亡时间为：{player_list[i].deadtime[1]}月{player_list[i].deadtime[2]}日{player_list[i].deadtime[3]}时{player_list[i].deadtime[4]}分,死于{player_list[i].dead_item}攻击\n")
                        choose = get_message(self.id,f"是否要伪造验尸报告？（是/否）\n")
                        while choose not in ["是","否"]:
                            choose = get_message(self.id,"输入有误，重新输入\n")
                        if choose == "是":
                            time_false = []
                            while len(time_false) != 12:
                                time_false = get_message(self.id,"填写伪造的死亡时间，格式为：202509010101（2025年9月1日1时1分）\n")
                                if len(time_false) != 12:
                                    send_to_player(self.id,"时间输入长度有误，重新输入\n")
                                elif not time_false.isdigit():
                                    send_to_player(self.id,"时间输入格式有误，重新输入\n")
                            dead_item = get_message(self.id,"填写玩家的死亡原因:")
                            player_list[i].dead_item = dead_item
                            self.bag.append(Item("梅露露的验尸报告",f"报告显示{player_list[i].nickname}的死亡时间为：{int(time_false[4:6])}月{int(time_false[6:8])}日{int(time_false[8:10])}时{int(time_false[10:])}分,死于{player_list[i].dead_item}攻击",get_time(),"情报"))
                            send_to_player(self.id,"伪造完成，验尸报告已添加至背包\n")
                            self.magic_used -= 1
                        else:
                            self.bag.append(Item("梅露露的验尸报告",f"报告显示{player_list[i].nickname}的死亡时间为：{player_list[i].deadtime[1]}月{player_list[i].deadtime[2]}日{player_list[i].deadtime[3]}时{player_list[i].deadtime[4]}分,死于{player_list[i].dead_item}攻击",get_time(),"情报"))
                            send_to_player(self.id,"验尸报告已添加至背包\n")
                            self.magic_used -= 1
        else:
            send_to_player(self.id,"魔法使用失败：暂未发现尸体\n")

class Anan(Player):
    def __init__(self,player_id,conn,player_num):
        super().__init__(player_id,conn,player_num)
        self.name = "Anan"
        self.magic_used = 3
    def magic(self):
        send_to_player(self.id,"你的魔法仅可在讨论环节使用\n")
        send_to_player(self.id,f"魔法剩余使用次数{self.magic_used}/3次\n")

class Miria(Player):
    def __init__(self,player_id,conn,player_num):
        super().__init__(player_id,conn,player_num)
        self.name = "Miria"
        self.magic_used = 2
    def magic(self):
        global player_list
        send_to_player(self.id,"使用魔法:互换\n")
        send_to_player(self.id,"选择一名玩家，与其互换背包与位置\n")
        send_to_player(self.id,f"魔法剩余使用次数{self.magic_used}/2次\n")
        send_to_player(self.id,"可选玩家列表\n")
        choose_str = ""
        for i in player_list:
            if i.life:
                choose_str += i.nickname + " "
        send_to_player(self.id,choose_str + "\n")
        aim = get_message(self.id,"你要与谁互换位置和背包\n")
        for i in player_list:
            if aim == i.nickname and i.life:
                self.bag, i.bag = i.bag, self.bag
                self.location, i.location = i.location, self.location
                get_distance(self)
                i.distance = get_distance(i)
                self.magic_used -= 1
                send_to_player(self.id,"交换完成\n")
                send_to_player(i.id,f"你与玩家{self.nickname}交换了位置与背包\n")
                return
        send_to_player(self.id,"魔法使用失败\n")


# def get_distance(player):
#     global player_list,location_list
#     start_address = location_list.index(player.location)
#     distance = []
#     for i in player_list:
#         end_address = location_list.index(i.location)
#         distance.append(map_len[start_address][end_address])
#     player.distance = distance
#     return distance

def get_distance(player):
    global player_list,location_list,max_player_num
    distance = [0] * max_player_num
    for i in location_list:
        if i.name == player.location:
            start_id = i.id
    for i in player_list:
        for j in location_list:
            if j.name == i.location:
                end_id = j.id
                distance[i.id] = location_list[start_id].distance[end_id]
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
    if USING_HTML:
        send_to_socket(conn, "人物列表：Shiro, Meruru, Anan, Miria\n")
        send_to_socket(conn, "请玩家选择人物：\n")
    else:
        conn.send("人物列表：Shiro, Meruru, Anan, Miria\n".encode(ENCODING))
        conn.send("请玩家选择人物：\n".encode(ENCODING))
    while True:
        print("人物遍历查询中")
        if USING_HTML:
            choose_people = recv_from_socket(conn)
        else:
            choose_people = conn.recv(BUFFER_SIZE).decode(ENCODING).strip()
        if choose_people in p_name_list:
            break
    print(choose_people)
    player_list.append(p_list[p_name_list.index(choose_people)](player_id,conn,player_num))
    player_list[player_id].nickname = player_name
    print("玩家人物创建完成")
    if USING_HTML:
        send_to_socket(conn, "人物创建完成\n")
    else:
        conn.send("人物创建完成\n".encode(ENCODING))

def activate(player,n):
    global player_list,dead_search,noa_picture_search #活动函数
    if n != 0:
        for i in range(n):#5次搜证机会,搜证期间不可攻击
            get_distance(player)
            send_to_player(player.id,"-"*10 + "\n")
            if player.life <=0:
                send_to_player(player.id,f"玩家{player.nickname}已经死亡，请等待游戏结束\n")
                continue
            send_to_player(player.id,f"{player.nickname}当前位置：{player.location}\n")
            send_to_player(player.id,"1.去别处看看 2.查看手机 \n3.发动魔法 ")
            choose = 0
            while choose not in [1,2,3]:
                try:
                    choose = int(get_message(player.id,f"\n请输入操作\n"))
                except:
                    choose = 0
                    send_to_player(player.id,"输入有误，重新输入\n")
            match choose:
                case 1:
                    player.move()
                case 2:
                    player.check_phone()
                case 3:
                    player.magic()
        player.location = "审判庭"  #搜证阶段结束后回到审判庭
        get_distance(player)
    else:
        while not dead_search:
            get_distance(player)
            send_to_player(player.id,"-"*30 + "\n")
            show_player(player)
            if player.life <=0:
                send_to_player(player.id,f"玩家{player.nickname}已经死亡，请等待游戏结束\n")
                continue
            if player.name == "Noa" and noa_picture_search:
                noa_picture_search = 0
                player.killer = 1
                send_to_player(player.id,"有人看到了你的画，你已成为魔女\n")
            send_to_player(player.id,f"{player.nickname}当前位置：{player.location}\n")
            send_to_player(player.id,"1.去别处看看 2.查看手机 \n3.发动魔法 ")
            if player.killer:
                send_to_player(player.id,"4.攻击（游戏开始的前一小时不能攻击）")
            choose = 0
            while choose not in [1,2,3,4]:
                try:
                    choose = int(get_message(player.id,f"\n请输入操作\n"))
                except:
                    choose = 0
                    send_to_player(player.id,"输入有误，重新输入\n")
            match choose:
                case 1:
                    player.move()
                case 2:
                    player.check_phone()
                case 3:
                    player.magic()
                case 4:
                    player.attack()
            get_distance(player)
            for i in player.distance:
                if not i and player_list[i].life == 0 and not player.killer:
                    dead_search = 1 #尸体被发现，跳出循环
                    send_to_player(player.id,"你发现了一具尸体，进入搜证阶段\n")
                    send_to_player(player.id,f"玩家{player.nickname}在{player.location}发现了一具尸体，进入搜证阶段\n")
                    break

speech_finish = 0
def end_speak(player):
    global player_list
    send_to_player(player.id,"请等待所有玩家搜证完成")
    while any(item.location != "审判庭" for item in player_list):
        pass
    send_to_player(player.id,"所有玩家已来到'审判庭',开始讨论")
    end_speech = 0
    speech_finish = 0
    while end_speech < len(player_list):
        end_speech = 0
        for i in range(len(player_list)):
            while not speech_finish:
                if  player_list[i].life == 0:
                    send_to_player(i,"你已死亡，跳过发言环节\n")
                    end_speech += 1
                    speech_finish = 1
                
                if i == player.id and i.name == "Anan" and i.magic_used > 0:
                    send_to_player(player.id,"你可以发动魔法，输入一名玩家的昵称，使得此玩家出示证据后跳过发言一次\n")
                    send_to_player(player.id,"可选玩家：")
                    name_str = ""
                    choose_list = []
                    for j in player_list:
                        if j.id != player.id and j.life == 1:
                            name_str += j.nickname + " "
                            choose_list.append(j)
                    send_to_player(player.id,name_str+"\n")
                    choose = get_message(player.id,"请输入玩家昵称,输入空即为放弃使用魔法\n")
                    for k in choose_list:
                        if k.nickname == choose:
                            k.jump_speak = 1
                            send_to_player(player.id,f"你使用魔法成功，使玩家{choose}提交证据后跳过发言一次\n")
                            player.magic_used -= 1

                if i == player.id and player.bag:
                    item_list = []
                    send_to_player(i,"请玩家选择你要提交的证据，随后发言：\n")
                    for j in player.bag:
                        send_to_player(i,f"“{j.name}” ")
                        item_list.append(j.name)
                    send_to_player(i,"\n")
                    speech = get_message(i,"请输入你要提交的证据,输入其他跳过发言：\n")
                    if speech in item_list:
                        send_to_player(player.id,f"玩家{player.nickname}提交了证据：“{speech}”\n")
                        it = player.bag[item_list.index(speech)]#取出物品对象
                        send_to_player(player.id,f"名称：{it.name}\n描述：{it.describe}\n获取时间：{it.get_time[1]}月{it.get_time[2]}日 {it.get_time[3]}:{it.get_time[4]}\n类型：{it.type}\n")
                        player.bag.remove(item_list.index(speech))
                        if player.jump_speak:
                            send_to_player(player.id,"Anan:[闭嘴]")
                            send_to_player(player.id,"-"*10 +f"{player.nickname}发言结束"+"-"*10+"\n")
                            speech_finish = 1
                            player.jump_speak = 0
                        else:
                            message = get_message(i,"请输入你的发言内容:\n")
                            send_to_player(player.id,f"{player.nickname}：{message}\n")
                            send_to_player(player.id,"-"*10 +f"{player.nickname}发言结束"+"-"*10+"\n")
                            speech_finish = 1
                    else:
                        send_to_player(i,"跳过发言环节\n")
                        end_speech += 1
                        speech_finish = 1
                if i == player.id and not player.bag:
                    send_to_player(i,"你没有证据可提交，跳过发言环节\n")
                    end_speech += 1
                    speech_finish = 1

                if i != player.id and not player.send_message:
                    player.send_message = 1
                    send_to_player(player.id,"请等待其他玩家发言\n")
            speech_finish = 0
            player.send_message = 0
    send_to_player(player.id,"所有玩家全部跳过发言，进入总结阶段，总结阶段中每名玩家只能发言一次\n")
    for i in range(len(player_list)):
        while not speech_finish:
            if player_list[i].life == 0:
                send_to_player(i,"你已死亡，跳过发言环节\n")
                speech_finish = 1
                continue
            if i == player.id:
                message = get_message(i,"请输入你的总结发言内容:\n")
                send_to_player(player.id,f"{player_list[i].nickname}：{message}\n")
                send_to_player(player.id,"-"*10 +f"{player.nickname}总结发言结束"+"-"*10+"\n")
                speech_finish = 1
            elif i != player.id and not player.send_message:
                player.send_message = 1
                send_to_player(i,"请等待其他玩家发言\n")
        speech_finish = 0
        player.send_message = 0

def game_start(player):
    global ticket,player_list
    print("-"*11,"游戏开始","-"*11,"\n")
    # 第一阶段-自由活动直到尸体被发现
    while any(item.killer == 1 and item.life > 0 for item in player_list) or any(item.killer == 0 and item.life > 0 for item in player_list):
        send_to_player(player.id,"自由活动开始,所有玩家可自行探索")
        activate(player,0)#参数0表示不指定次数，检测到尸体后跳出循环
        #尸体被发现，进入搜证阶段
        #第二阶段-搜证阶段，每人5次行动机会
        activate(player,5)#参数5表示指定行动次数
        send_to_player(player.id,"搜证阶段结束，进入发言阶段\n")
        #第三阶段-发言阶段，所有证据讨论完成后再进行一轮补充说明，最后结束进入投票
        end_speak(player)
        send_to_player(player.id,"发言阶段结束，进入投票阶段\n")
        #第四阶段-投票阶段
        send_to_player(player.id,"请玩家进行投票，输入你要投票的玩家昵称\n")
        answer = get_message(player.id,"投票开始，输入你要投票的玩家昵称：")
        list_str = ""
        for i in player_list:
            list_str += i.nickname +" "
        send_to_player(player.id,f"{list_str}\n")
        while answer not in [i.nickname for i in player_list]:
            get_message(player.id,"输入有误，重新输入\n")
        ticket[[i.nickname for i in player_list].index(answer)] += 1
        send_to_player(player.id,f"你投票给了玩家{answer}\n")
        while sum(ticket) < len(player_list):
            send_to_player(player.id,"请等待其他玩家投票\n")
        max_vote = max(ticket)
        player_list[ticket.index(max_vote)].life = 0
        send_to_player(player.id,f"玩家{player_list[ticket.index(max_vote)].nickname}被处刑")
    
    if any(item.killer == 1 and item.life > 0 for item in player_list):
        send_to_player(player.id,"游戏结束,魔女胜利,所有玩家均被杀死或魔女化")
    else:
        send_to_player(player.id,"游戏结束,魔女失败,场上不存在魔女化的玩家")



def get_message(player_id,message=""):
    global player_list   
    player = player_list[player_id]
    if USING_HTML:
        if message:
            send_to_player(player.id,message)
        data = player.conn.recv(BUFFER_SIZE)
        if not data:
            return ""
        return parse_websocket_msg(data).strip()
    else:
        if message:
            send_to_player(player.id,message)
        while True:
            recv_data = player.conn.recv(BUFFER_SIZE).decode(ENCODING).strip()
            if recv_data:
                print(f"[收到消息] 来自玩家【{player.nickname}】(ID:{player.id}) 的消息：{recv_data}")
                return recv_data


def broadcast(message, exclude_conn=[]):
    global player_list
    with lock:  # 加锁保证线程安全
        for i in player_list:
            if i.id not in exclude_conn:
                try:
                    if USING_HTML:
                        send_to_socket(i.conn, message)
                    else:
                        i.conn.send(message.encode(ENCODING))
                except:
                    remove_player_by_conn(i)

def send_to_player(player_id, message):
    global player_list,lock
    with lock:
        if player_id in [i for i in range(len(player_list))]:
            conn = player_list[player_id].conn
        if USING_HTML:
            try:
                conn.send(pack_websocket_msg(message))
            except:
                remove_player_by_conn(player_list[player_id])
        else:
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
            broadcast(f"[系统公告] 玩家【{player.name}】已退出游戏！当前在线人数：{len(player_list)-1}\n")
            # 从全局列表删除玩家对象，自动释放所有属性
            player_list.remove(player)
            # 关闭socket连接
            try:
                player.conn.close()
            except:
                pass

def websocket_handshake(client_socket, client_data):
    key = None
    lines = client_data.split('\r\n')
    for line in lines:
        if line.startswith('Sec-WebSocket-Key:'):
            key = line.split(': ')[1].strip()
            break
    if not key:
        return False
    magic_string = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    sha1 = hashlib.sha1((key + magic_string).encode('utf-8'))
    sec_key = base64.b64encode(sha1.digest()).decode('utf-8')
    response = f"HTTP/1.1 101 Switching Protocols\r\n" \
               f"Upgrade: websocket\r\n" \
               f"Connection: Upgrade\r\n" \
               f"Sec-WebSocket-Accept: {sec_key}\r\n\r\n"
    client_socket.send(response.encode(ENCODING))
    return True

def parse_websocket_msg(data):
    if not data:
        return ""
    opcode = data[0] & 0x0F
    payload_len = data[1] & 0x7F
    mask = data[1] & 0x80
    if opcode != 1:
        return ""
    if payload_len == 126:
        payload_len = int.from_bytes(data[2:4], byteorder='big')
        mask_key = data[4:8]
        payload_data = data[8:8+payload_len]
    elif payload_len == 127:
        payload_len = int.from_bytes(data[2:10], byteorder='big')
        mask_key = data[10:14]
        payload_data = data[14:14+payload_len]
    else:
        mask_key = data[2:6]
        payload_data = data[6:6+payload_len]
    decoded = bytearray()
    for i in range(payload_len):
        decoded.append(payload_data[i] ^ mask_key[i % 4])
    return decoded.decode(ENCODING, errors='ignore').strip()

def pack_websocket_msg(msg):
    if not msg:
        return b""
    data = msg.encode(ENCODING)
    payload_len = len(data)
    frame = bytearray()
    frame.append(0x81)
    if payload_len <= 125:
        frame.append(payload_len)
    elif payload_len <= 65535:
        frame.append(126)
        frame.extend(payload_len.to_bytes(2, byteorder='big'))
    else:
        frame.append(127)
        frame.extend(payload_len.to_bytes(8, byteorder='big'))
    frame.extend(data)
    return bytes(frame)

def recv_from_socket(conn):
    data = conn.recv(BUFFER_SIZE)
    if not data:
        return ""
    return parse_websocket_msg(data)

def send_to_socket(conn, message):
    try:
        conn.send(pack_websocket_msg(message))
    except:
        pass

def handle_client(conn, addr):
    global player_id_counter, player_list,max_player_num,killer_id
    player_name = ""
    if USING_HTML:
        try:
            # ====== 第一步：完成WebSocket握手 ======
            handshake_data = conn.recv(1024).decode(ENCODING, errors='ignore')
            if not websocket_handshake(conn, handshake_data):
                print(f"[异常] {addr} WebSocket握手失败")
                conn.close()
                return
            print(f"[成功] {addr} WebSocket握手完成")
            send_to_socket(conn, "请输入你的游戏昵称：\n")
            player_name = recv_from_socket(conn).strip()
            while not player_name:
                send_to_socket(conn, "昵称不能为空！请重新输入：\n")
                player_name = recv_from_socket(conn).strip()
            with lock:
                create_player(player_id_counter,player_name,conn,max_player_num)
                player_id_counter += 1
                player = player_list[player_id_counter-1]

            welcome_msg = f"[系统公告] 玩家【{player.nickname}】(ID:{player.id}) 加入游戏！\n"
            broadcast(welcome_msg,[player.id])
            send_to_player(player.id,f"加入成功！你的玩家ID：{player.id}\n当前在线人数：{len(player_list)}/{max_player_num}\n")
            print(f"[系统] 新玩家连接：{addr} → 【{player.nickname}】(ID:{player.id})")

            # 等待所有玩家加入
            send_to_player(player.id,f"等待玩家全部加入，当前加入{len(player_list)}/{max_player_num}\n")
            while len(player_list) < max_player_num:
                time.sleep(2)
                send_to_player(player.id,f"等待中...{len(player_list)}/{max_player_num}\n")

            # 随机分配魔女
            player_list[killer_id].killer = 1
            if killer_id == player.id:
                send_to_player(killer_id, "恭喜你，你成为了【魔女】！请隐藏身份完成猎杀\n")
            send_to_player(player.id,"所有玩家已加入，游戏正式开始！\n一名玩家已成为魔女，猎杀开始！\n")
            game_start(player)
        except Exception as e:
            print(f"[异常-在handle_client函数中] 玩家【{player_name}】异常：{e}")
        finally:
            if conn:
                try:
                    for p in player_list:
                        if p.conn == conn:
                            remove_player_by_conn(p)
                            break
                except:
                    pass
    else:
        try:
            conn.send("请输入你的游戏昵称：\n".encode(ENCODING))
            player_name = conn.recv(BUFFER_SIZE).decode(ENCODING).strip()
            while not player_name:
                conn.send("昵称不能为空！请重新输入：\n".encode(ENCODING))
                player_name = conn.recv(BUFFER_SIZE).decode(ENCODING).strip()
            with lock:
                create_player(player_id_counter,player_name,conn,max_player_num)
                player_id_counter += 1
                player = player_list[player_id_counter-1]

            welcome_msg = f"[系统公告] 玩家【{player.nickname}】(ID:{player.id}) 加入游戏！\n"
            broadcast(welcome_msg,[0])
            player.conn.send(f"加入成功！你的玩家ID：{player.id}\n当前在线人数：{len(player_list)}\n".encode(ENCODING))
            print(f"[系统] 新玩家连接：{addr} → 【{player.nickname}】(ID:{player.id})")
            send_to_player(player.id,f"等待玩家全部加入，当前加入{len(player_list)}/{max_player_num}\n")
            send_to_player(player.id,"-"*30+"\n")
            send_to_player(player.id,f"等待玩家全部加入，当前加入{len(player_list)}/{max_player_num}\n")
            while len(player_list) < max_player_num:
                time.sleep(2)
                send_to_player(player.id,f"等待中...{len(player_list)}/{max_player_num}\n")

            # 随机分配魔女
            player_list[killer_id].killer = 1
            if killer_id == player.id:
                send_to_player(killer_id, "恭喜你，你成为了【魔女】！请隐藏身份完成猎杀\n")
            send_to_player(player.id,"所有玩家已加入，游戏正式开始！\n一名玩家已成为魔女，猎杀开始！\n")
            game_start(player)
        except Exception as e:
            print(f"[异常-在handle_cilent函数中] 玩家【{player_name}】异常：{e}")
        finally:
            if conn:
                remove_player_by_conn(conn)

def main():
    global HOST, PORT, max_player_num , USING_HTML,killer_id
    """服务端主函数：启动监听，接收客户端连接"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(max_player_num)
    print(f"=====================================")
    print(f"游戏通信服务端已启动")
    print(f"监听地址：{HOST}:{PORT}")
    print("本机ip:",socket.gethostbyname(socket.gethostname()))
    print(f"等待玩家连接中...")
    print(f"=====================================")


    max_player_num = int(input("输入玩家数量"))
    killer_id = random.randint(0,max_player_num-1)
    
    print(f"设置最大玩家数量为：{max_player_num}\n等待连接中")
    USING_HTML = int(input("是否使用HTML格式进行消息传输？0-否，1-是"))
    if USING_HTML:
        print("已启用HTML格式进行消息传输")
    else:
        print("未启用HTML格式进行消息传输")
    while True:
        conn, addr = server_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        client_thread.start()


def show_player(player):
    print("-"*10+"玩家信息"+"-"*10)
    print(f"玩家ID：{player.id}")
    print(f"玩家昵称：{player.nickname}")
    print(f"玩家位置：{player.location}")
    print(f"玩家生命状态：{'存活' if player.life == 1 else '死亡'}")
    print(f"玩家是否为魔女：{'是' if player.killer == 1 else '否'}")
    print(f"玩家背包物品：")
    for item in player.bag:
        print(f"  - {item.name}: {item.describe} (获取时间：{item.get_time}, 类型：{item.type})")
    print(f"玩家距离列表：{player.distance}")

#全局变量：
USING_HTML = 0                  # 是否使用HTML格式进行消息传输
HOST = "0.0.0.0"                # 服务器IP地址
PORT = 9999                     # 服务器端口
BUFFER_SIZE = 1024              # 发送数据最大值
ENCODING = "utf-8"              # 发送数据编码格式
player_id_counter = 0           # 在创建玩家时计算玩家id
lock = threading.Lock()         # 线程锁定义，保证多线程操作玩家字典时不冲突
max_player_num = 0              # 设置最大游玩人数，达到最大游玩人数之后开始主程序执行
dead_search = 0                 # 死者是否被发现，0-未被发现，1-已被发现
player_list = []                # 全局玩家列表
dead_list = []                  # 全局死亡玩家列表(id)
ticket = [0] * len(player_list) # 投票计数列表，索引对应玩家id，值对应票数
location_list = []  # 地点列表，用于计算对应地点之间的距离
p_list = [Shiro, Meruru, Anan, Miria] #人物类存储列表
p_name_list = ["Shiro", "Meruru", "Anan", "Miria"]    # 人物类名称列表
time_start = [2026,1,6,9,00,0]  # 游戏的起始游戏时间
time_real_start = time.time()   # 获取真实时间戳，用于计算时间流逝

# A  B  C  D  E  F  G  H  I  J  K  L  M  N  O  P  Q  R  S  T  楼层间距离20
location_list.append(Room(1 ,"医务室",[ 0,20,15, 5,20,25,15,20,25,30,35,40,40,50,60,60,50,50,45,50],[0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],[Item("绷带","一节绷带",get_time(),"道具"),Item("安眠药","一瓶安眠药",get_time(),"道具")])) #A
location_list.append(Room(2 ,"淋浴房",[20, 0,20,15,10,15,20,20,20,25,30,35,35,45,55,55,45,45,40,45],[0,0,1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],[Item("物品","道具类",get_time(),"道具"),Item("物品","情报类",get_time(),"情报")])) #B
location_list.append(Room(3 ,"日光房",[15,20, 0, 5,15,20, 5,10,15,20,25,30,30,40,50,50,40,40,35,40],[1,1,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],[Item("物品","道具类",get_time(),"道具"),Item("物品","情报类",get_time(),"情报")])) #C
location_list.append(Room(4 ,"杂物处",[ 5,15, 5, 0, 5,10, 5,10,15,20,25,30,30,40,50,50,40,40,35,40],[1,1,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],[Item("物品","道具类",get_time(),"道具"),Item("物品","情报类",get_time(),"情报")])) #D
location_list.append(Room(5 ,"中庭",[20,10,15, 5, 0, 5,15, 5, 5,10,15,20,20,30,40,40,30,30,25,30],[1,1,1,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],[Item("物品","道具类",get_time(),"道具"),Item("物品","情报类",get_time(),"情报")])) #E
location_list.append(Room(6 ,"接客室",[25,15,20,10, 5, 0,25,15, 5,10,15,20,20,30,40,40,30,30,25,30],[1,1,1,1,1,0,1,1,0,1,1,1,1,1,1,1,1,1,1,1],[Item("物品","道具类",get_time(),"道具"),Item("物品","情报类",get_time(),"情报")])) #F
location_list.append(Room(7 ,"女厕",[15,20, 5, 5,15,25, 0, 5,10,15,20,25,25,35,45,45,35,35,30,35],[1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1,1,1,1],[Item("物品","道具类",get_time(),"道具"),Item("物品","情报类",get_time(),"情报")])) #G
location_list.append(Room(8 ,"会客厅",[20,20,10,10, 5, 5,10, 0, 5,10,15,20,20,30,40,40,30,30,25,30],[1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,1,1,1],[Item("物品","道具类",get_time(),"道具"),Item("物品","情报类",get_time(),"情报")])) #H
location_list.append(Room(9 ,"玄关大厅",[25,20,15,15, 5, 5,10, 5, 0, 5,10,15,15,25,35,35,25,25,20,25],[1,1,1,1,1,0,1,0,0,0,1,1,1,1,1,1,1,1,1,1],[Item("物品","道具类",get_time(),"道具"),Item("物品","情报类",get_time(),"情报")])) #I
location_list.append(Room(10,"审判庭入口过道",[30,25,20,20,10,10,15,10, 5, 0, 5,10,10,30,40,40,30,30,25,30],[1,1,1,1,1,1,1,1,0,0,0,1,0,1,1,1,1,1,1,1],[Item("物品","道具类",get_time(),"道具"),Item("物品","情报类",get_time(),"情报")])) #J
location_list.append(Room(11,"食堂",[35,30,25,25,15,15,20,15,10, 5, 0, 5, 5,35,45,45,35,35,30,35],[1,1,1,1,1,1,1,1,1,0,0,0,1,1,1,1,1,1,1,1],[Item("物品","道具类",get_time(),"道具"),Item("物品","情报类",get_time(),"情报")])) #K
location_list.append(Room(12,"厨房",[40,35,30,30,20,20,25,20,15,10, 5, 0, 5,40,50,50,40,40,35,40],[1,1,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1],[Item("物品","道具类",get_time(),"道具"),Item("物品","情报类",get_time(),"情报")])) #L
location_list.append(Room(13,"审判庭",[40,35,30,30,20,20,25,20,15,10, 5, 5, 0,40,50,50,40,40,35,40],[1,1,1,1,1,1,1,1,1,0,1,1,0,1,1,1,1,1,1,1],[Item("物品","道具类",get_time(),"道具"),Item("物品","情报类",get_time(),"情报")])) #M
location_list.append(Room(14,"牢房",[50,45,40,40,30,30,35,30,25,30,35,40,40, 0,20,20,50,50,45,50],  [1,1,1,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1],[Item("物品","道具类",get_time(),"道具"),Item("物品","情报类",get_time(),"情报")])) #N
location_list.append(Room(15,"焚烧炉",[60,55,50,50,40,40,45,40,35,40,45,50,50,20, 0,30,60,60,55,60],[1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1],[Item("物品","道具类",get_time(),"道具"),Item("物品","情报类",get_time(),"情报")])) #O
location_list.append(Room(16,"惩罚室",[60,55,50,50,40,40,45,40,35,40,45,50,50,20,30, 0,60,60,55,60],[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1],[Item("物品","道具类",get_time(),"道具"),Item("物品","情报类",get_time(),"情报")])) #P
location_list.append(Room(17,"娱乐室",[50,45,40,40,30,30,35,30,25,30,35,40,40,50,60,60, 0,15, 5,15],[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1,0,1],[Item("物品","道具类",get_time(),"道具"),Item("物品","情报类",get_time(),"情报")])) #Q
location_list.append(Room(18,"工作室",[50,45,40,40,30,30,35,30,25,30,35,40,40,50,60,60,15, 0, 5,15],[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,1],[Item("物品","道具类",get_time(),"道具"),Item("物品","情报类",get_time(),"情报")])) #R
location_list.append(Room(19,"2F大厅",[45,40,35,35,25,25,30,25,20,25,30,35,35,45,55,55, 5, 5, 0, 5],[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0],[Item("物品","道具类",get_time(),"道具"),Item("物品","情报类",get_time(),"情报")])) #S
location_list.append(Room(20,"图书室",[50,45,40,40,30,30,35,30,25,30,35,40,40,50,60,60,15,15, 5, 0],[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0],[Item("物品","道具类",get_time(),"道具"),Item("物品","情报类",get_time(),"情报")])) #T

if __name__ == "__main__":
    main()