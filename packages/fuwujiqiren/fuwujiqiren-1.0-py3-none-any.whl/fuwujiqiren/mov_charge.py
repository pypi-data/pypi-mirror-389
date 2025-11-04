import creabot
import time

IP_id="192.168.197.144"
IP = creabot.Creabot(IP_id)
map_id='testmop2'
charger_name='充电桩1'
set_speak='电量低，请充电'
pointlist=None
step=False


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
        init()
    else:
        print("目标地图未找到")
        exit()

def init():
    dst = next((f for f in pointlist if f["type"] == "anchor_point"), None)
    if dst:
        IP.tts_sync("开始重定位")
        IP.relocate_sync(dst["x"], dst["y"], dst["theta"])
    else:
        print("不存在定位点")

def speak(sk):
    while  True:
        IP.tts_sync("请给我下达下一步指令")
        res = IP.asr_sync(5)
        print('识别结果：',res)
        if sk in res:
            IP.tts_sync('好的，我要去充电了，请不要拦住我')
            return True
        else:
            IP.tts_sync(f"我听到你说：{res},未识别指令")

def mov_charge(name):
    dst = next((f for f in pointlist if f["name"] == name), None)
    # print("开始向充电桩移动")
    # IP.start_navigation_sync(dst['x'], dst['y'], dst['theta'], 0.5)
    print('开始上桩')
    step=IP.dock_charge_on_sync(map_id,dst['x'],dst['y'],dst['theta'])
    if step :
        time.sleep(10)
        IP.dock_charge_off_sync()


if __name__ == '__main__':
    IP.tts_sync("开始运行")
    set_map(map_id)
    while  not step:
        step=speak(set_speak)
    mov_charge(charger_name)    