#!/usr/bin/env python3
"""
NPC 主动消息轮询器
监控 world_state.json，当剧情推进时，让 NPC 主动联系玩家
"""

import json
import time
import hashlib
import requests
import os
import sys

WORLD_STATE_PATH = "/home/kay/hermes-narrative-engine/world_state.json"
NPC_BOT_TOKEN = "8996235257:AAH983MNRHm7YGe5tRogX1koez1g7jhPiws"
PLAYER_CHAT_ID = "7486260300"  # 你的 Telegram ID

TELEGRAM_API = f"https://api.telegram.org/bot{NPC_BOT_TOKEN}"

last_hash = ""
last_event = ""
cooldown_rounds = 0  # 防止连续发送

def get_world_state():
    try:
        with open(WORLD_STATE_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def send_npc_message(text):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        "chat_id": PLAYER_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        r = requests.post(url, json=payload, timeout=5)
        return r.ok
    except Exception as e:
        print(f"发送失败: {e}")
        return False

def evaluate_npc_reaction(state):
    """根据 world_state 判断 NPC 是否需要主动说话"""
    event = state.get("recent_event", "")
    scene = state.get("current_scene", "")
    npc_state = state.get("npc", {})
    trust = npc_state.get("trust", 50)
    flags = state.get("flags", {})
    
    messages = []
    
    # 场景初次进入时 NPC 的反应
    if scene == "basement_door" and not flags.get("npc_reacted_basement"):
        messages.append("你到了吗。我在地下室入口这边。\n\n这扇门……我搬进来那天就想打开它了。但我没开。\n\n不是打不开。是我不想一个人开。")
    
    elif scene == "basement_stairs" and not flags.get("npc_reacted_stairs"):
        messages.append("这下面的空气不对。不是潮湿的那种——是那种……\n\n我在西北矿区的竖井里闻到过类似的气味。那次下去之后，有两个人再没上来。")
    
    # 发现线索时 NPC 的反应
    if "水声" in event and not flags.get("npc_reacted_water"):
        messages.append("你听到了吗——水声。\n\n这栋房子下面不应该有地下水。我看过地质图，这片是岩层，不是含水层。\n\n下面有东西。")
    
    # 信任度高时 NPC 主动分享
    if trust > 60 and not flags.get("npc_shared_secret"):
        messages.append("有件事我一直没跟你说。\n\n我买这栋房子之前，在矿区见过一张照片。当时我在一个废弃的勘探队营地里找到的——那张照片上的建筑，和这栋房子一模一样。\n\n我不知道那支勘探队在找什么。但照片背面写了一行字。\n\n「他们已经不在地面上了。」")
    
    # 信任度低时 NPC 保持沉默
    if trust < 20 and not flags.get("npc_distrust_warning"):
        messages.append("你有些事情没跟我说。\n\n我闻得出来。就像我能闻出地下室那股气味不是来自任何正常的地方。\n\n你最好想清楚再告诉我。")
    
    # 长时间没互动时
    if cooldown_rounds > 5 and trust > 30:
        messages.append("你在想什么？\n\n我不是在催你。我只是觉得——如果我们分头行动，有些事情可能会更快弄清楚。")
    
    return messages

def main():
    global last_hash, last_event, cooldown_rounds
    
    print("NPC 主动消息轮询器启动中……")
    time.sleep(3)  # 等 Hermes 启动完成
    print("开始轮询 world_state.json")
    
    while True:
        state = get_world_state()
        if state:
            current_hash = hashlib.md5(json.dumps(state, sort_keys=True).encode()).hexdigest()
            
            if current_hash != last_hash:
                last_hash = current_hash
                last_event = state.get("recent_event", "")
                
                # NPC 评估是否要说话
                messages = evaluate_npc_reaction(state)
                for msg in messages:
                    send_npc_message(msg)
                    time.sleep(1)  # 避免多条消息连发
        
        time.sleep(8)  # 每 8 秒轮询一次

if __name__ == "__main__":
    main()
