# Hermes Narrative Engine (HNE)

**互动恐怖/悬疑叙事引擎**
适配平台：Hermes Agent by Nous Research
版本：v1.0
项目路径：`/home/kay/hermes-narrative-engine/`

---

## 项目总览

HNE 是一套构建在 Hermes Agent 之上的模块化互动叙事系统。利用 Hermes 的 Skills System、Persistent Memory、Cross-Session 记忆、子代理 (subagent)、MCP 工具链等原生能力，实现可热插拔的多类型互动恐怖/悬疑故事体验。

---

## 设计原则

1. **选择驱动** ── 玩家通过每轮给出的 A/B/C/D 选项推进故事，不依赖自然语言指令
2. **隐形检定** ── 所有检定在后台执行，玩家只看到叙事结果，不看到数字
3. **类型隔离** ── 不同故事类型（克苏鲁/中式怪谈/科幻/废土）拥有完全独立的 state、prompt、检定体系
4. **多结局 + 可回退** ── 每个故事至少 3 种结局，玩家可回退到之前的关键分支节点重新选择
5. **独立 NPC** ── NPC 作为独立实体与玩家并行行动，双向影响，可能死亡/背叛/发疯
6. **跨会话持久** ── 状态、角色卡、NPC 关系跨 Telegram 会话保留
# test
