# ASIC 实际面试记录

标签：`#actual-interview` `#actual-asked` `#asic` `#frontend` `#rtl` `#axi` `#dft`

## 页内目录

- [记录原则](#record-rule)
- [紫光展锐 / Unisoc](#unisoc)
- [字节 / ByteDance](#bytedance)
- [芯动科技 / Innosilicon](#innosilicon)
- [提炼出的优先级](#priority-review)
- [项目回答结构](#project-answer-structure)

---
<a id="record-rule"></a>
## 记录原则
这里保存我自己真实遇到的 ASIC/RTL/DV 面试问题。每次面试后尽量补三类信息：

- 原始问题：面试官具体问了什么。
- 知识点归类：对应 ASIC 前端、协议、DFT、架构、手撕代码哪一类。
- 复盘动作：哪些问题要补笔记、补代码、补英文回答。

<a id="unisoc"></a>
## 紫光展锐 / Unisoc
标签：`#company-unisoc`

### 一面

标签：`#round-1`

原始问题：

- 讲项目。
- memory compiler 设置 HVT。
- scan chain。
- 其他都很基础。

知识点归类：

| 问题 | 分类 | 要补的能力 | 复习链接 |
| --- | --- | --- | --- |
| 讲项目 | 项目表达 | 能用 2 分钟讲清背景、职责、技术点、结果、难点 | [项目故事库](../projects-hr/projects-and-behavioral.md#project-stories) |
| memory compiler 设置 HVT | Memory compiler / low power / timing | 理解 SRAM macro option、HVT/LVT/SVT trade-off、PPA 影响 | [Memory compiler / HVT](../knowledge-base/asic-frontend.md#memory-hvt) |
| scan chain | DFT | 理解 scan flop、scan enable、scan in/out、ATPG、为什么需要 scan chain | [Scan chain](../knowledge-base/asic-frontend.md#scan-chain) |
| 基础题 | RTL/ASIC 基础 | 常见 RTL、时序、综合、低功耗概念要稳定 | [ASIC 前端总览](../knowledge-base/asic-frontend.md#asic-overview) |

复盘动作：

- 准备一个固定项目讲法：架构图 -> 我的工作 -> 关键 bug/难点 -> 结果。
- 补 memory compiler 中 threshold voltage option 的意义。
- 补 scan chain 的 60 秒回答。

### 二面 HR

标签：`#round-2` `#hr`

原始问题：

- 简单询问本科情况。

复盘动作：

- 准备本科经历和研究生/项目选择之间的逻辑。
- 准备为什么找 ASIC/DV、为什么这个岗位、未来 2-3 年规划。

<a id="bytedance"></a>
## 字节 / ByteDance
标签：`#company-bytedance`

### 一面

标签：`#round-1`

原始问题：

- 综合报告。
- 逻辑深度。
- AXI。
- Interleaving。
- Outstanding。
- 手撕：find first one。

知识点归类：

| 问题 | 分类 | 要补的能力 | 复习链接 |
| --- | --- | --- | --- |
| 综合报告 | Synthesis / timing | 会看 area、timing、WNS/TNS、critical path、cell usage、memory/macro、constraint 是否合理 | [综合报告和逻辑深度](../knowledge-base/asic-frontend.md#synthesis-report-logic-depth) |
| 逻辑深度 | Timing / micro-architecture | 能解释为什么逻辑级数影响频率，以及如何 pipeline/retime/拆组合逻辑 | [综合报告和逻辑深度](../knowledge-base/asic-frontend.md#synthesis-report-logic-depth) |
| AXI | Protocol | 五通道、valid-ready、burst、ID、response、backpressure | [AXI](../knowledge-base/protocols.md#axi) |
| Interleaving | AXI advanced | 理解 read data interleaving / write data ordering 相关规则和 ID 关系 | [AXI interleaving](../knowledge-base/protocols.md#axi-interleaving) |
| Outstanding | AXI advanced | 理解多个未完成 transaction、ID tracking、reorder buffer/scoreboard 思路 | [AXI outstanding](../knowledge-base/protocols.md#axi-outstanding) |
| find first one | RTL coding | 能写 priority encoder，注意 width、无 1 情况、break/flag 写法 | [find first one](../knowledge-base/asic-frontend.md#find-first-one) |

复盘动作：

- 准备一页“怎么看综合报告”。
- 把 AXI outstanding/interleaving 和 scoreboard 类比起来记。
- 手写 find first one 的组合逻辑版本和参数化版本。

### 二面

标签：`#round-2`

原始问题：

- 详细拷打 OoO。
- 手撕：同步 FIFO。
- 手撕：检测 one-hot。

知识点归类：

| 问题 | 分类 | 要补的能力 | 复习链接 |
| --- | --- | --- | --- |
| OoO | 计算机体系结构 / 微架构 | ROB、reservation station、rename、issue/execute/commit、precise exception、load-store queue | [OoO 基础](../knowledge-base/asic-frontend.md#ooo-basics) |
| 同步 FIFO | RTL coding | 指针、full/empty、计数器或额外 bit、同周期读写、reset | [同步 FIFO](../knowledge-base/asic-frontend.md#sync-fifo) |
| 检测 one-hot | RTL coding | `x != 0 && (x & (x-1)) == 0`，以及 `$onehot()`/`$onehot0()` | [one-hot 检测](../knowledge-base/asic-frontend.md#one-hot) |

复盘动作：

- OoO 要准备从 in-order pipeline 到 OoO 的完整解释。
- 同步 FIFO 至少手写 1 个可综合版本，明确 full/empty 规则。
- one-hot 检测准备 RTL 写法、SVA 写法、内建函数写法。

<a id="innosilicon"></a>
## 芯动科技 / Innosilicon
标签：`#company-innosilicon` `#coding-test` `#systemverilog` `#rtl-coding`

### 笔试 / Coding Test

标签：`#written-test`

原始问题：

- task 找 first1 的位置，里面状态机的形式，四个状态 `IDLE`、`SEARCH`、`DONE`、`SEARCHFAIL`，用 enum 定义状态，每次调用 task 切换状态。
- `fork/join_none` 并行计算，一个二维数组 `bit q[M][N]`，计算每一行 1 的个数并且存在一个 array 里面。
- valid-ready 握手，用 task 写：定义一个 transaction，里面包含 valid、clk、rst_n、ready、`[7:0] data`；一个 task drive 发送；ready 随机拉高拉低；一个 monitor 收集数据；一个 tb 发送五个 transaction `tx_q[5]`。

知识点归类：

| 问题 | 分类 | 要补的能力 | 复习链接 |
| --- | --- | --- | --- |
| task + FSM 找 first1 | SV task / FSM / enum | 能写出每次调用推进一步的状态机，区分组合 priority encoder 和 step FSM | [task + FSM：find first 1](../knowledge-base/systemverilog-uvm.md#sv-task-fsm-find-first-one) |
| `fork/join_none` 行并行统计 1 的个数 | SV concurrency / array | 理解 `join_none` 不等待、`wait fork` 同步、fork 中 loop index 要用 `automatic` 保存 | [fork/join_none 行并行统计](../knowledge-base/systemverilog-uvm.md#sv-fork-join-none-row-count) |
| valid-ready driver / monitor / tb | SV testbench / handshake | 能写 transaction、driver task、随机 ready backpressure、monitor 采样和 5 笔 transaction 发送 | [valid-ready task TB](../knowledge-base/systemverilog-uvm.md#sv-valid-ready-task-tb) |

复盘动作：

- 把 `fork/join_none` 的 automatic loop index 当成必背坑点。
- valid-ready 题要明确：只有 `valid && ready` 同周期才算一次 transaction，monitor 也只在此时采样。
- task FSM 题要说明这是 multi-call step FSM，不是单周期组合 priority encoder。

<a id="innosilicon-dv-intern"></a>
### 验证实习一面（2026-06-03）

标签：`#round-1` `#dv-intern` `#uvm` `#axi-dma` `#project-deep-dive`

原始问题：

- 怎么将信号驱动到 DUT？是用 VIP 还是自己写的？
- abort 注入怎么实现的？
- 整个 DMA 是多路一起搬运还是单独搬运？
- AXI-Lite 写配置和 AXI4 memory data path 在验证环境里怎么分工？
- Outstanding 是外部 testbench 发起，还是 DMA 内部自己拆出来？
- 未对齐长度/地址时，WSTRB 或 byte enable 怎么保证只有有效 byte 被写入？
- NPU 项目里 C model / DPI 是怎么和 RTL 对齐的？是每一步都比，还是只比最终结果？
- CPU 项目有没有反汇编、commit log 或 reference model 之类的检查？
- 跨时钟域部分是怎么验证的？

知识点归类：

| 问题 | 分类 | 面试复盘重点 | 复习链接 |
| --- | --- | --- | --- |
| 信号怎么驱动到 DUT，VIP 还是自写 | UVM driver / BFM / VIP | 明确说 AXI-Lite master agent 和 AXI memory slave BFM 是自己写的；driver 从 sequence/RAL adapter 取得 transaction 后驱动 interface | [DMA 追问复盘](../projects-hr/axi-dma-uvm-details.md#axi-dma-innosilicon-followups) |
| abort 注入怎么实现 | Abort / error injection | 优先讲 frontdoor 写 `CONTROL.abort`；只有白盒 fault injection 才讲 `force/release` 内部信号 | [DMA 追问复盘](../projects-hr/axi-dma-uvm-details.md#axi-dma-innosilicon-followups) |
| DMA 多路一起搬运还是单独搬运 | Descriptor / outstanding / burst | 区分 descriptor slot、物理 DMA channel、AXI outstanding；不要把“多 descriptor”和“多路并行搬运”混在一起 | [DMA 追问复盘](../projects-hr/axi-dma-uvm-details.md#axi-dma-innosilicon-followups) |
| Outstanding 谁来发 | AXI protocol | Testbench 只配置 transfer 和 backpressure；DMA 作为 AXI master 内部把长 transfer 拆成多个 burst/outstanding 请求 | [AXI outstanding](../knowledge-base/protocols.md#axi-outstanding) |
| 未对齐 / WSTRB | AXI byte lane | 说明每个 WSTRB bit 对应一个 byte；未对齐 transfer 只写有效 byte，memory model/scoreboard 要按 byte 级检查 | [AXI-Lite 与 CSR 编程](../knowledge-base/protocols.md#axil) |
| NPU C model / DPI | Golden reference | 讲清 early debug 可以 per-layer/instruction-level compare；regression 中可做 result-level/end-to-end compare；量化 shift/bias/saturation 要和 RTL 对齐 | [INT8 NPU 项目](../projects-hr/projects-and-behavioral.md#star-int8-npu-tapeout) |
| CPU 验证 log / 反汇编 | CPU DV | 承认项目中主要是 directed program + log；下次补强为 commit monitor/reference model/RVFI 方向 | [Ibex 验证项目](../projects-hr/projects-and-behavioral.md#star-ibex-rv32im-uvm) |
| CDC 验证 | CDC / formal / async FIFO | 不要只说“不确定”；应说明 CDC lint/formal、async FIFO assertions、clock ratio randomization 和 post-silicon 风险 | [CDC/RDC](../knowledge-base/asic-frontend.md#cdc-rdc) |

录音中可提炼的项目表达：

- DMA 验证环境里，AXI-Lite 是 CSR 控制路径，用于写 descriptor、length、burst、go/abort 等寄存器；AXI4 memory 侧是 DUT 主动发起读写，testbench 的 memory slave BFM 被动响应。
- 这个项目没有使用商业 VIP，主要是自己写 AXI-Lite master agent、AXI memory slave BFM、monitor、scoreboard 和 RAL adapter/predictor；另一个 TVIP-AXI crossbar 项目才是使用开源 AXI VIP 的例子。
- Backpressure 通过 memory slave BFM 随机延迟 ready/response 来实现，不是 testbench 主动往 DUT 塞 data stream。
- 对 unaligned transfer，要把“传输长度不是 4-byte 整数”和“AXI beat 仍按 data width 传输”区分开，真正决定哪些 byte 生效的是 WSTRB / byte enable。
- NPU 项目中比较有价值的表达是：4x4 MAC 计算不是瓶颈，真正难点是 memory bandwidth、multi-bank 数据拼接、卷积窗口地址映射、读写冲突仲裁和 C model 量化对齐。
- CDC 问题要准备更成熟的说法：外部低频、内部高频之间通过 async FIFO/CDC synchronizer 跨域；验证上需要 CDC tool、formal assertion、clock ratio/random phase test 和 silicon bring-up 共同兜底。

下次回答提醒：

- 不要只说“我强行把信号拉高”。先讲合法验证路径：sequence/RAL/frontdoor 配置 -> driver 驱动 interface -> DUT 响应；如果确实是白盒错误注入，再说明 force 的使用边界。
- 面试官问“多路”时先反问/澄清：是问多个 descriptor slot、多个 AXI outstanding，还是多个物理 DMA channel。澄清后再答，能显得更专业。
- CPU 验证不要停在“看 waveform / 打 log”，要主动补一句：如果继续完善，会加 commit monitor、反汇编 log、reference model 或 RVFI-style check。

<a id="priority-review"></a>
## 从这些记录提炼出的优先级
### P0：马上补

- 项目讲述：ASIC/DV 岗通用开场。
- Synthesis report：WNS/TNS、critical path、logic depth、area、power、constraint。
- AXI：outstanding、interleaving、ID、ordering、backpressure。
- RTL 手撕：find first one、sync FIFO、one-hot detector。
- SV 笔试 coding：task FSM、`fork/join_none` 并发、valid-ready driver/monitor。
- 芯动科技验证一面：DMA 驱动路径、VIP vs BFM、abort 注入、descriptor/outstanding 表达。
- DFT scan chain：scan mode、scan enable、scan in/out、ATPG。

### P1：继续加深

- Memory compiler：SRAM macro 配置、HVT/LVT/SVT、read/write margin、PPA trade-off。
- OoO：rename、ROB、RS、LSQ、commit、flush、exception。
- Timing optimization：pipeline、balance logic、retiming、multi-cycle/false path 的边界。
- NPU C model/DPI、CPU 验证 log/反汇编、CDC 验证方法。

<a id="project-answer-structure"></a>
## 可直接背的项目回答结构
1. 项目目标：这个设计/验证环境解决什么问题。
2. 架构：模块划分、接口、数据流。
3. 我的职责：我具体写了哪些 RTL/TB/script/test。
4. 难点：一个真实 bug、timing issue、coverage hole 或 debug 过程。
5. 结果：功能通过、coverage、频率、面积、性能、代码规模、自动化收益。
6. 反思：如果重做，会怎么改。

