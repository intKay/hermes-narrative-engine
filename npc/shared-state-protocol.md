# 共享状态读写协议

## 概述

叙述者（Bot A）和 NPC（Bot B）通过文件系统共享 `world_state.json` 来同步剧情进展。

## 文件路径

```
/home/kay/hermes-narrative-engine/world_state.json
```

## 写者 / 读者（多私聊架构）

| 角色 | 权限 | 说明 |
|------|------|------|
| 叙述者（Bot A，叙事群聊） | 读写 | 每轮叙事后更新 |
| NPC 陈默（Bot B，私聊） | 只读 | 每 5-10 秒轮询一次，检测 `recent_event` 变化 |
| NPC 李伟（Bot C，私聊） | 只读 | 同上 |
| NPC 林雪（Bot D，私聊） | 只读 | 同上 |

**每个 NPC 独立轮询**，各自维护自己的上次哈希值。互不干扰。

## 状态文件格式

```json
{
  "version": 1,
  "updated_at": "2026-05-24T15:30:00+08:00",
  "genre": "cthulhu",
  "current_scene": "basement_door_01",
  "round": 17,
  "player": {
    "sanity": 62,
    "inventory": ["旧打火机", "半截蜡烛"],
    "clues_found": ["地下室地板下有水声"]
  },
  "npc": {
    "name": "陈默",
    "trust": 45,
    "fear": 35,
    "sanity": 70,
    "location": "地下室入口",
    "status": "跟随中"
  },
  "flags": {
    "basement_door_opened": true,
    "light_flickered": false,
    "heard_whisper": true
  },
  "recent_event": "玩家推开了地下室的门，门轴发出尖锐的响声。",
  "available_choices": ["A: 走下楼梯", "B: 喊一声有人吗", "C: 让陈默先下去", "D: 关上门退回去"]
}
```

## 读取时机（NPC Bot）

NPC Bot 每 5-10 秒读取一次 `world_state.json`。当以下情况发生时触发行动：

1. `recent_event` 字段更新（叙述者刚刚推进了剧情）
2. `available_choices` 中出现与 NPC 角色设定相关的选项（如选项 C 涉及 NPC）
3. NPC 内部的随机心跳检定通过（约 30% 概率）

## NPC 信任度说明

`npc.trust` 是 0-100 的整数，影响 NPC 的行为模式：

| 信任值范围 | NPC 行为 |
|-----------|---------|
| 80-100 | 主动分享信息，愿意承担风险帮助玩家 |
| 50-79 | 配合玩家行动，如实回答问题 |
| 20-49 | 有所保留，可能隐瞒关键信息 |
| 0-19 | 可能主动欺骗、私自行动或脱离队伍 |

信任度变迁由叙述者基于玩家与 NPC 的互动更新，不依赖对话轮次。

## 写入约束

- 叙述者每次更新时只覆写整个文件（文件小，无并发问题）
- 不在高频率循环中更新（只在每轮叙事结束时更新一次）
- NPC 永远不写入此文件

## 扩展

如果后续需要更复杂的同步（如 NPC 也需要写入某些状态），可升级为基于 SQLite 的状态共享，但当前阶段文件系统 JSON 已足够。
