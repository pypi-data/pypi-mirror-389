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

def mov_point(name):

    #取出需要导航到目的地的点位信息
    dst = next((f for f in pointlist if f["name"] == name), None)
    if dst:
        print(f"正在导航去{name}点")
        print(dst["x"], dst["y"], dst["theta"])
        IP.start_navigation_sync(dst["x"], dst["y"], dst["theta"], 0.5)
        print("导航完成")
        
    else:
        print("点位名称不存在")
def init():
    dst = next((f for f in pointlist if f["type"] == "anchor_point"), None)
    if dst:
        IP.tts_sync("开始重定位")
        IP.relocate_sync(dst["x"], dst["y"], dst["theta"])
        IP.tts_sync("重定位成功")
    else:
        print("不存在定位点")
        exit()
def say():
    print(pointlist)
    print("####################")
    dst = next((f for f in pointlist if f["type"] == "charge"), None)
    print(dst)
    print("11111")
    while True:
        IP.tts_sync("请给我下达下一步指令")
        # 等待5秒接收语音输入
        res = IP.asr_sync(8)
        print("你说的内容：", res)
        if "充电" in res:
            IP.tts_sync("好的，我要去充电了，请不要拦住我")
            IP.dock_charge_on_sync('testmop2',dst["x"], dst["y"], dst["theta"])
            IP.tts_sync("正在充电")
            time.sleep(10)
            IP.tts_sync("充电完成，正在回收")            
            IP.dock_charge_off_sync()
            
if __name__ == '__main__':
    IP.tts_sync("开始运行")
    set_map(map_id)
    init() 
    IP.tts_sync("初始化完成，开始导航")
    mov_point("目的地1") 
    say()
    IP.tts_sync("导航完成，程序结束")
    IP.close()
    exit()
    
 
    
         

