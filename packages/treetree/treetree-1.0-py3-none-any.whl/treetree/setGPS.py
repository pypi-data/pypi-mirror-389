import creabot
import time

IP_id = "192.168.197.144"
IP = creabot.Creabot(IP_id)
map_id = 'testmop2'
charger_name = '充电桩1'
recycle_name = '回收1'
set_speak_m = None
set_speak_n = None
pointlist = None


def set_map(name):
    global pointlist
    maplist = IP.list_map()
    targetmap = next((f for f in maplist if f["name"] == name), None)
    if targetmap:
        print("###########")
        mapid = targetmap["id"]
        IP.set_map(mapid)
        pointlist = IP.list_map_point(mapid)
        print(f"'初始化成功,成功设置地图：'{name}")
    else:
        print("目标地图未找到")
        exit()


def init():
    dst = next((f for f in pointlist if f["type"] == "anchor_point"), None)
    if dst:
        IP.tts_sync("开始重定位")
        IP.relocate_sync(dst["x"], dst["y"], dst["theta"])
        IP.tts_sync("重定位成功")
    else:
        print("不存在定位点")


def mov_point(m):
    dst = next((f for f in pointlist if f["name"] == m), None)
    if dst:
        print(f"正在导航去{m}点")
        IP.start_navigation_sync(dst["x"], dst["y"], dst["theta"], 0.5)
        return True
    else:
        print("点位名称不存在")
        return False


def set_in():
    while not IP.exist_object():
        IP.tts_sync("请将需要递送的物品放入仓内")
        if IP.is_door_open():
            time.sleep(6)
        else:
            IP.door_ctrl(1)
            IP.light_ctrl(1)
    IP.tts_sync("已取得物品")
    IP.door_ctrl(0)
    IP.light_ctrl(0)
    time.sleep(5)
    return True


def set_out():
    while IP.exist_object():
        IP.tts_sync("您的物品已送达，请取走")
        if IP.is_door_open():
            time.sleep(6)
        else:
            IP.door_ctrl(1)
            IP.light_ctrl(1)
    IP.tts_sync("物品已取出")
    IP.door_ctrl(0)
    IP.light_ctrl(0)
    time.sleep(5)
    return True
if __name__ == '__main__':
    IP.tts_sync("开始运行")
    set_map(map_id)
    init()
    mov_point("目的地1")
    if not IP.exist_object():
        set_in()
    mov_point("目的地2")
    if IP.exist_object():
        set_out()
    mov_point('回收1')
    IP.tts_sync("任务完成")
    IP.tts_sync("结束运行")