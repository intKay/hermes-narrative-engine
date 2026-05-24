# 多频道部署指南

## 架构概览

```
叙事群聊（你和叙述者 Bot 两人）
    ↓ world_state.json（叙述者每轮更新）
NPC A 私聊 ← → NPC B 私聊 ← → NPC C 私聊
（各自独立，互不知道对方的存在）
```

**需要的资源：**
- 1 个 Telegram Bot Token → 叙述者
- N 个 Telegram Bot Token → 每个 NPC 各一个
- N+1 个 Hermes Profile

---

## 第一步：创建 Telegram Bot

在 Telegram 中打开 @BotFather，对每个需要创建的 Bot 执行：

```
/newbot
→ 输入名字（如 "HNE 叙述者"）
→ 输入用户名（如 "hne_narrator_bot"）
→ 拿到 token：123456:ABCdef...
```

重复以上步骤，为每个 NPC 各创建一个 Bot：

| 角色 | 建议用户名 | 用途 |
|------|-----------|------|
| 叙述者 | `hne_narrator_bot` | 在叙事群聊中发送故事 |
| 陈默 | `hne_chenmo_bot` | 与你私聊的 NPC |
| 李伟 | `hne_liwei_bot` | 与你私聊的 NPC |
| （更多） | ... | ... |

---

## 第二步：创建 Hermes Profile

每个 Bot 需要一个独立的 Hermes profile：

```bash
# 叙述者 profile
hermes profile create narrator

# 每个 NPC 各一个 profile
hermes profile create npc_chenmo
hermes profile create npc_liwei
# ...更多 NPC 以此类推
```

---

## 第三步：配置 Gateway（每个 profile 绑定一个 Bot）

```bash
# 配置叙述者（绑定叙事群聊）
hermes --profile narrator gateway setup
# → 输入叙述者 Bot 的 token
# → 创建一个群聊，把叙述者 Bot 拉入
# → 在群聊中输入 /sethome 设为 home channel

# 配置 NPC 陈默
hermes --profile npc_chenmo gateway setup
# → 输入陈默 Bot 的 token
# → 直接与你私聊（不需要群聊）
# → 在私聊中输入 /sethome 设为 home channel

# 配置 NPC 李伟（同上）
hermes --profile npc_liwei gateway setup
```

**注意**：每个 profile 的 `gateway setup` 是独立的。叙述者的 home channel = 叙事群聊，NPC 的 home channel = 你们的私聊。

---

## 第四步：为每个 NPC 配置人格

每个 NPC profile 需要加载自己的人格定义。在 NPC profile 的配置中设一个自定义 system prompt，指向 NPC 人格文件：

```bash
# 以陈默为例
# 编辑 ~/.hermes/profiles/npc_chenmo/personality.md
# 填入以下内容并让 NPC profile 加载它
```

各个 NPC 的 prompt 文件参考 `NPC-TEMPLATE.md` 编写，存放在项目目录中：

```
hermes-narrative-engine/npc/
├── NPC-TEMPLATE.md          # NPC 人格模板（参考用）
├── chenmo-personality.md    # 陈默的人格定义
├── liwei-personality.md     # 李伟的人格定义
└── shared-state-protocol.md # 共享状态读写协议
```

---

## 第五步：为 NPC 加载 world_state 感知能力

每个 NPC profile 需要通过某种方式持续读取 `world_state.json`。由于 Hermes 本身不提供「定时轮询」功能，有两种方案：

### 方案 A：NPCScript（推荐，最简单）

每个 NPC profile 启动时加载一个 shell 脚本作为 `cronjob`，每 10 秒轮询一次：

```bash
# 在 NPC profile 下创建一个 cron 任务
# 脚本只做一件事：检测 world_state.json 的变化
hermes --profile npc_chenmo cron create --every 10s \
  --script /home/kay/hermes-narrative-engine/npc/npc-poll.sh
```

脚本内容（`npc-poll.sh`）：
```bash
#!/bin/bash
# 检查 world_state.json 是否更新
# 如果 recent_event 字段变了，触发 NPC 响应
LAST_HASH_FILE="/tmp/npc_chenmo_last_hash"
CURRENT_HASH=$(md5sum /home/kay/hermes-narrative-engine/world_state.json 2>/dev/null | cut -d' ' -f1)

if [ -f "$LAST_HASH_FILE" ]; then
    LAST_HASH=$(cat "$LAST_HASH_FILE")
    if [ "$CURRENT_HASH" != "$LAST_HASH" ]; then
        # world_state 已更新，NPC 应该检查是否需要说话
        echo "WORLD_STATE_UPDATED"
    fi
fi
echo "$CURRENT_HASH" > "$LAST_HASH_FILE"
```

### 方案 B：由叙述者转发（更可控）

每轮叙事结束后，叙述者在 `world_state.json` 更新时，主动向每个 NPC Bot 发一条通知（通过 HTTP 或文件信号）。NPC Bot 收到信号后才响应。

---

## 第六步：启动所有进程

```bash
# 终端 1：叙述者
hermes --profile narrator gateway run

# 终端 2：NPC 陈默
hermes --profile npc_chenmo gateway run

# 终端 3：NPC 李伟
hermes --profile npc_liwei gateway run
```

所有网关启动后：

1. 你在 **叙事群聊** 中看到故事 + A/B/C/D 选项
2. 选完选项后，故事推进，`world_state.json` 更新
3. NPC 检测到更新后，根据角色设定决定是否**在私聊中主动联系你**
4. 你也可以随时**主动私聊 NPC**，问他问题或分享信息

---

## 如何避免角色冲突

在这个架构下，角色冲突天然不存在，因为：

| 为什么不会冲突 | 原因 |
|--------------|------|
| 叙述者只在叙事群聊 | 不会跑到 NPC 私聊里说话 |
| 陈默只能在陈默的私聊 | 不会跑到叙事群聊或李伟的私聊里 |
| 李伟同理 | 与陈默隔离 |
| 各 Bot 先判断聊天上下文再响应 | 私聊消息 = 玩家对该 NPC 说话，不涉及任何角色混淆 |

**唯一的风险**：玩家在叙事群聊中说的话，NPC 看不到。所以如果你想让 NPC 知道你说过某句话，需要去 NPC 的私聊里再说一遍。这是**设计意图**——你知道的信息和 NPC 知道的信息天然不对称。
