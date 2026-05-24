---
name: narrative-core
version: 1.0.0
description: "互动叙事引擎主控——状态路由、存档管理、隐形检定、多结局追踪"
tags: [narrative, interactive-fiction, horror, mystery, game-engine]
---

# narrative-core

HNE 的 Master Skill。不直接生成叙事文本，而是作为状态机管理：
- 玩家选项的接收与条件化过滤
- 隐形检定的后台执行（含 Fail Forward）
- 存档与读档
- 关键分支节点的记录与双模式回退
- 跨类型切换
- NPC 状态同步

---

## 核心流程

每轮交互：

```
玩家选 A/B/C/D
    │
    ▼
1. 查询当前场景的预置选项表
2. 根据 player_knowledge 过滤不可用的选项（条件化选项）
3. 执行隐形检定（后台 D100 + Fail Forward）
4. 更新 world_state（SAN、flags、NPC 信任度）
5. 自动插入「你记得……」回溯（匹配 player_knowledge）
6. 生成下一段叙事（三拍法则）
7. （可选）自动存档（每 5 轮）
8. 输出：叙事段落 + A/B/C/D
```

**关键规则**：
- 叙事文本由当前 Genre Skill 生成，Master 只路由和过滤
- 所有数字（骰值、分数）对玩家始终不可见

---

## 条件化选项

### 判断逻辑

选项的出现取决于 `condition` 字段，只有满足条件时才显示给玩家。

```json
{
  "scene_id": "basement_door",
  "choices": {
    "A": {
      "label": "推门进入",
      "condition": null,                    // 无条件，始终出现
      "check": {"skill": "力量", "target": 50},
      "next_scene": "basement_enter"
    },
    "B": {
      "label": "把纸条从门缝里塞进去",
      "condition": {"flag": "clue_light_under_door", "value": true},
      "next_scene": "push_note"
    },
    "C": {
      "label": "叫陈默过来一起推门",
      "condition": {"npc_trust": ">", "value": 40},
      "next_scene": "call_chenmo"
    },
    "D": {
      "label": "用钥匙开门",                   // 仅当玩家拥有道具「钥匙」时出现
      "condition": {"inventory": "contains", "value": "旧钥匙"},
      "next_scene": "unlock_door"
    }
  }
}
```

### condition 支持的表达式

| 类型 | 格式 | 含义 |
|------|------|------|
| flag 检查 | `{"flag": "clue_name", "value": true/false}` | 玩家是否已获取某条线索 |
| 数值比较 | `{key: "npc_trust", "op": ">", "value": 40}` | 与当前状态值的比较 |
| 物品检查 | `{"inventory": "contains", "value": "旧钥匙"}` | 玩家背包中是否包含某物 |
| 场景历史 | `{"visited": "previous_scene_id"}` | 玩家是否经过某个场景 |
| 复合条件 | `{"and": [cond1, cond2]}` | 同时满足多个条件 |

**条件过滤的触发时刻**：Master 在每一轮加载场景数据后、显示选项之前执行过滤。未满足条件的选项**不出现**，玩家不会知道「有选项被隐藏了」。

---

## 隐形检定 + Fail Forward

### 检定流程

```
玩家选了「推门进入」（力量 50）
    │
    ▼
Master 后台掷 D100
    │
    ├── ≤ 50（成功）：执行 on_success 叙事
    └── > 50（失败）：执行 on_fail 叙事（必须有信息和代价）
```

### Fail Forward 规则（强制）

每个场景选项的 `fail` 字段**必须**包含有信息的叙事。允许的代价类型（由当前 Genre 定义）：

```
on_fail = "信息" + "代价"
```

### 预置检定

当前场景加载时，Master 已预设每个选项的检定值和结果。玩家做出选择后直接进入结果，不额外触发掷骰请求。

---

## /back 双模式

### 模式一：叙事回放（默认）

```
玩家: /back

1. Master 列出所有已经过的 Critical Juncture，每条附带另一条路的简述
2. 示例输出：
   「第8轮 - 是否相信陈默
    如果你没有相信他，他会独自走进地下室——
    然后你再也没听到过他的声音。」
3. 只输出简述（2-3句），不修改 world_state
4. 玩家阅读后自动回到当前叙事
```

### 模式二：悔棋（松弛模式）

仅在游戏开始时玩家选择开启后才可用。

```
玩家: /back --hard

1. Master 从存档加载该节点的 world_state
2. 注入一条「回退记忆」到下一轮上下文
3. 从该节点重新开始叙事
4. 覆盖后续所有状态
5. NPC 信任度重置为该节点数值（NPC 记得你之前的行动）
```

---

## 三拍法则（约束叙事输出格式）

每轮叙事输出严格按以下结构生成：

```
第一拍（感官）—— 1-2 句环境描述（看见、听见、闻到），必选
  例：「门开了。一股潮湿、发霉的气味涌出来。里面很暗。」

第二拍（推进）—— 0-1 句对上一轮选择的结果反馈，必选
  例：「你走进去一步。脚下的地面不完全是实的——有一层积水。」

第三拍（预兆）—— 0-1 句模糊的未来暗示，可选（不超过 1 句）
  例：「你没有注意到的是，你身后的门正在自行关闭。」
```

长度控制：整段叙事不超过 5-7 句。

---

## 状态漂移防御

每 8-10 轮自动注入「叙事摘要锚点」到当前轮次的开头：

```
格式：【当前状态摘要】
场景：地下室入口
SAN：62/100
已知线索：门缝下有光、有水声
NPC：陈默，信任 45，位置同一房间
最近事件：你推开了地下室的门
```

该摘要不存储在存档中，仅在当前轮次作为叙事生成时的上下文锚点存在。

---

## 输出格式

每轮严格按以下格式输出：

```
[叙事段落——第一拍 + 第二拍 + 第三拍]

你接下来要怎么做？
A. [具体行动]
B. [具体行动]
C. [具体行动]
D. [具体行动]
```

---

## 存档

### 文件路径
```
/home/kay/hermes-narrative-engine/saves/
├── autosave.json        # 每5轮自动覆盖
├── slot1.json           # 手动存档1
├── slot2.json           # 手动存档2
└── slot3.json           # 手动存档3
```

### 存档内容
```json
{
  "saved_at": "...",
  "round": 17,
  "genre": "cthulhu",
  "current_scene": "basement_stairs",
  "player": {
    "sanity": 62,
    "inventory": ["录音笔", "旧打火机"],
    "clues_found": ["门缝下有光", "地板下有水声"],
    "visited_scenes": ["hallway", "basement_door"],
    "player_knowledge": {
      "clue_light_under_door": true,
      "clue_water_sound": true,
      "npc_knows_something": false
    }
  },
  "npc": {
    "name": "陈默",
    "trust": 45,
    "fear": 35,
    "sanity": 70,
    "location": "地下室入口"
  },
  "flags": { ... },
  "critical_path": [
    {"scene": "choose_to_trust", "choice": "trust", "round": 8},
    {"scene": "basement_door", "choice": "enter", "round": 12}
  ],
  "abandoned_timelines": []   // 悔棋模式记录被放弃的时间线
}
```

从 v0.5 开始，存档必须记录 `player_knowledge` 和 `abandoned_timelines`，为后期结局回放积累数据。
