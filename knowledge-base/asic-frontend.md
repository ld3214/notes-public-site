[返回目录](../index.md)

# ASIC Frontend 知识库

这个文件集中放 ASIC 前端、综合、时序、DFT、RTL 手撕、computer architecture 和真实面试提炼知识点。

## 页内目录

- [ASIC 前端总览](#asic-overview)
- [时序与 STA](#timing-sta)
- [CDC/RDC](#cdc-rdc)
- [综合与 Lint](#synthesis-lint)
- [ASIC 面试专项知识点](#asic-interview-topics)
- [Memory compiler 设置 HVT](#memory-hvt)
- [Scan chain](#scan-chain)
- [综合报告和逻辑深度](#synthesis-report-logic-depth)
- [Computer Architecture 面试重点](#computer-architecture)
- [OoO 基础](#ooo-basics)
- [Cache 基础](#cache-basics)
- [书籍整理：数字逻辑与体系结构高频框架](#book-dv-logic-architecture)
- [低功耗、Clocking 与 UPF](#power-clocking-upf)
- [手撕 find first one](#find-first-one)
- [手撕同步 FIFO](#sync-fifo)
- [手撕 one-hot 检测](#one-hot)
- [面试回答速查（中文 + English）](#asic-interview-answers)

---
<a id="asic-overview"></a>
## ASIC 前端总览
## 学习地图

- RTL design
- FSM/datapath/control logic
- Low power design
- Lint
- Synthesis
- STA
- CDC/RDC
- DFT 基础
- Computer architecture: pipeline / OoO / cache

## 面试表达

ASIC frontend focuses on translating architectural intent into synthesizable RTL, then checking functionality, timing, clock-domain behavior, reset behavior, and implementation readiness before backend handoff.


## 真实面经入口

- [实际被问到的问题](../actual-interviews/questions.md#actual-question-table)
- [ASIC 面试专项知识点](#asic-interview-topics)

## 面经暴露出的重点

- 项目讲述要稳定、结构化。
- Memory compiler / HVT / PPA trade-off 要会讲。
- DFT scan chain 要准备 60 秒回答。
- 综合报告、critical path、logic depth 要会分析。
- AXI outstanding/interleaving 是高频深入点。
- RTL 手撕题要准备 priority encoder、sync FIFO、one-hot detector。
- OoO 需要从 rename、ROB、RS、LSQ、commit 讲成体系。
- Cache 要能讲清 hit/miss、tag/index/offset、write policy、AMAT 和 coherence 基础。
## 待补充

- 常见 RTL coding style
- Blocking/non-blocking assignment
- FSM 设计
- Timing closure 基础

---

<a id="timing-sta"></a>
## 时序与 STA
标签：`#asic` `#sta` `#interview`

## 核心概念

Static timing analysis (STA) 是在不仿真的情况下，通过分析所有时序路径的延迟来判断电路能否在目标频率下正常工作。

**Setup time 和 hold time**

| 概念 | 定义 | 违例后果 |
| --- | --- | --- |
| Setup time | 时钟上升沿之前，数据必须稳定的最短时间 | 数据来得太晚，触发器可能采样到错误值 |
| Hold time | 时钟上升沿之后，数据必须继续稳定的最短时间 | 数据变化太快，触发器可能采样到新值而不是旧值 |

Setup 违例：组合路径太长，数据在时钟沿前未稳定。修复方式：减小组合逻辑级数（插 pipeline、优化 datapath）、降低频率、换更快的单元。

Hold 违例：路径太短，数据在时钟沿后马上变化。修复方式：插 buffer 延长路径。降低频率无法解决，因为 hold 要求与时钟周期无关。

**关键度量指标**

- WNS (Worst Negative Slack)：所有路径中最差的负 slack，代表最严重的 setup violation。
- TNS (Total Negative Slack)：所有 violating path 的 slack 之和，代表整体 timing 压力。
- Critical path：slack 最小（最负）的路径，是优化首要目标。

**Clock skew**

同一个时钟在不同寄存器到达时刻的差异。Positive skew（目标 FF 比源 FF 时钟到达晚）有助于 setup；negative skew 则压缩 setup margin。Hold check 时 skew 影响相反。

**False path 和 Multicycle path**

- False path：物理存在但功能上数据永远不会传递的路径。设成 false path 后 STA 不对其做 timing check，避免误报。例如跨时钟域的单向控制信号、test mode path。
- Multicycle path：需要多个时钟周期才能完成的路径。通过 set_multicycle_path 告诉工具放宽 setup/hold 要求，避免不必要的过度优化。

**STA 流程**

1. 定义约束：时钟、IO delay、false path、multicycle path。
2. 寄生参数提取（RC extraction）。
3. 分析 setup 和 hold，找出所有 violating path。
4. 根据 critical path 做针对性优化。

## 面试回答

Setup time is the minimum time data must be stable before the clock edge for the flip-flop to capture it correctly. Hold time is the minimum time data must remain stable after the clock edge. A setup violation means the combinational path is too long, so the fix is to reduce logic depth or pipeline the path. A hold violation means the path is too short, so you add buffers — lowering the clock frequency does not help because hold requirements are independent of the clock period.

For STA, I would first check WNS and TNS in the timing report to understand the severity of violations. Then I would inspect the critical path to determine whether the issue is due to long logic depth, high fanout, slow cells, memory access latency, or incorrect constraints such as missing false paths or overly strict multicycle paths.

## 常见追问

- Setup time 和 hold time 的区别是什么？
  - Setup 要求数据在时钟沿之前稳定（路径太长导致违例）；hold 要求数据在时钟沿之后继续稳定（路径太短导致违例）。
- 为什么 hold violation 通常不能通过降低频率解决？
  - Hold 检查只依赖路径本身的延迟，与时钟周期无关；降低频率不会改变路径延迟，hold 违例依然存在。
- 什么是 clock skew？
  - 同一时钟信号在不同目标 FF 到达时刻的差异，会影响 setup 和 hold margin。
- 什么是 false path 和 multicycle path？
  - False path 是功能上永远不会传数据的路径，排除出 timing 检查；multicycle path 是设计允许用多个周期完成的路径，需要放宽约束。

## 易错点

- 把 hold violation 当作 setup violation 处理，插流水线反而可能让 hold 更难满足。
- False path 设错方向（from/to 写反），导致真实路径漏检。
- Multicycle path 只改了 setup，忘记同步修改 hold check offset。
- Clock skew 过大时，即使单路径 timing OK，hold check 仍可能失败。
- 过度依赖 WNS/TNS，忽略 critical path 背后的约束问题（如缺少 false path）。

---

<a id="cdc-rdc"></a>
## CDC/RDC
标签：`#asic` `#cdc` `#interview`

## 核心概念

**Clock Domain Crossing (CDC)**

当信号从一个时钟域传递到另一个时钟域时，如果没有适当处理，目标域的触发器可能在 setup 或 hold 违例的情况下采样，导致 metastability。Metastability 不能被完全消除，但可以通过足够的时间让触发器自行恢复，从而将概率降低到可接受水平。

**单 bit CDC：两级同步器 (Two-flip-flop synchronizer)**

```systemverilog
always_ff @(posedge clk_dst or negedge rst_n_dst) begin
  if (!rst_n_dst) begin
    sync_ff1 <= 1'b0;
    sync_ff2 <= 1'b0;
  end else begin
    sync_ff1 <= data_src;   // 第一级可能 metastable
    sync_ff2 <= sync_ff1;   // 第二级有足够时间恢复
  end
end
```

两级同步器的作用：给第一个触发器足够时间从 metastable 状态恢复，第二级采样到稳定值的概率非常高。

两级同步器的局限：
- 只适合单 bit 信号。
- 无法保证多 bit 信号的完整性（各 bit 可能在不同时刻被采样）。
- 增加 2 个时钟周期的延迟。
- 无法处理频率比差距很大时的 data loss 问题。

**多 bit CDC 处理方式**

| 方法 | 原理 | 适用场景 |
| --- | --- | --- |
| Gray code + 两级同步器 | 相邻值只有 1 bit 变化，即使采样错误也只差 1 个状态 | 指针类计数器（async FIFO read/write pointer） |
| Async FIFO | 数据存在同步 memory 中，指针用 gray code 跨域同步 | 大量数据的跨时钟域传输 |
| Handshake | 发送方发 request，接收方 ACK 同步回来确认，再发下一个 | 低速、非频繁的多 bit 数据传输 |

**Async FIFO 为什么能工作**

- 数据写入/读出在各自时钟域操作，没有跨域数据路径。
- Write pointer 转成 Gray code 后同步到 read domain，用于判断 empty。
- Read pointer 转成 Gray code 后同步到 write domain，用于判断 full。
- Gray code 保证指针递增时只有 1 bit 变化，不会因为 metastability 导致错误的多 bit 状态。

**Reset Domain Crossing (RDC)**

Reset 信号本身也可能跨时钟域，产生 RDC 问题：
- 不同域的 reset 去掉时间不同 → 部分电路先工作，接口信号可能无效。
- Async assert（任何时候都能立刻 assert reset）、sync deassert（去复位要同步到目标时钟域沿上）是安全 reset 的设计模式。
- Reset synchronizer：先异步 assert，经两级 FF 同步后 deassert，保证去复位与时钟对齐。

## 面试回答

CDC happens when a signal crosses from one clock domain to another, risking metastability if setup or hold requirements are violated. For a single-bit signal, a two-flop synchronizer gives the first flip-flop enough time to resolve metastability before the second samples it. For multi-bit signals, gray code encoding works for counters like FIFO pointers, because only one bit changes per increment. For wider data, an asynchronous FIFO is the standard solution: data is stored in a synchronous memory, and only the gray-coded pointers cross domains. For reset domain crossing, I would use an async-assert sync-deassert reset synchronizer to ensure clean deassertion aligned to the target clock.

## 常见追问

- 单 bit CDC 和 multi-bit CDC 分别怎么处理？
  - 单 bit：两级同步器；多 bit：gray code（指针）或 async FIFO（数据总线）或握手协议。
- 两级 synchronizer 能解决什么，不能解决什么？
  - 能：降低 metastability MTBF 到可接受水平，适用单 bit 慢变化信号。不能：保证多 bit 原子性、消除 data loss、处理高速频繁变化信号。
- Async FIFO 为什么适合跨时钟域传输数据？
  - 数据读写在各自域完成，只有 gray code 指针跨域，指针每次只变 1 bit，避免多 bit 采样不一致。
- Reset domain crossing 有什么风险？
  - 不同域去复位时序不同，可能导致接口信号在一个域已经有效但另一个域还在 reset，产生协议违例或数据损坏。

## 易错点

- 把两级同步器用在多 bit 数据上：各 bit 可能在不同周期被采样，导致数据错误。
- Gray code 只能用于单调递增/递减的计数场景，不能用于任意多 bit 总线。
- Async FIFO 中 binary 转 gray code 必须在本域完成，gray code 再同步到对端。
- 忘记对 full/empty 信号本身做保守处理（gray code 同步有 2 周期延迟，可能导致 full/empty 稍微保守）。
- RDC 问题容易被忽视，reset 去掉的顺序如果设计错误会导致难以复现的初始化 bug。

---

<a id="synthesis-lint"></a>
## 综合与 Lint
标签：`#asic` `#rtl` `#synthesis` `#lint`

## 核心概念

**综合流程**

综合 (synthesis) 将 RTL 描述转换为目标工艺库的门级网表：
1. RTL elaboration：解析 HDL，展开参数和 generate。
2. Generic mapping：映射到工艺无关的通用逻辑门。
3. Technology mapping：按时序、面积、功耗约束映射到标准单元库。
4. Optimization：timing-driven 优化，包括 logic restructuring、buffer insertion、cell sizing。

约束文件 (SDC) 是综合的核心输入：时钟定义、IO delay、false/multicycle path 都从这里读取。约束错误会导致综合产生错误优化结果或误报违例。

**不可综合的常见 RTL 写法**

| 写法 | 原因 |
| --- | --- |
| `initial` block（非 FPGA 场景） | 没有对应的硬件初始化电路 |
| `#delay`（`#10`） | 纯仿真时间控制，综合工具无法映射 |
| `$display`、`$finish` 等系统函数 | 仿真专用任务 |
| `real` 浮点类型 | 没有对应的数字电路 |
| `fork/join` 中的并发进程（部分情况） | 需要确认综合工具支持 |

**Latch inference（Latch 推断）**

在 `always_comb` 中，如果不是所有条件分支都赋值某个信号，综合工具会推断出 latch 来保持信号值：

```systemverilog
// 会产生 latch：sel=0 时 y 的值从哪来？
always_comb begin
  if (sel)
    y = a;
  // 缺少 else：y 在 sel=0 时保持旧值 → latch
end

// 正确做法：覆盖所有情况
always_comb begin
  y = '0;        // 先赋默认值
  if (sel)
    y = a;
end
```

Latch 的问题：对 timing 和功耗分析造成困难，容易引入毛刺和时序违例，通常应避免（除非有意设计 gated latch 用于低功耗）。

**casez 和 casex 的风险**

- `casex`：将 case expression 和 case item 中的 X 和 Z 都视为 don't care。在综合中可能隐藏真实的 X 值 propagation，仿真中也容易掩盖 bug。
- `casez`：只将 Z（以及 `?`）视为 don't care，X 不参与 don't care 匹配，相对安全。
- 推荐：使用 `unique case` 或 `priority case` 加完整分支，让工具明确推断出优先级或并行逻辑，并在仿真时检查 unique/priority 违例。

**Combinational loop**

组合逻辑的输出直接或间接反馈到自身的输入，没有寄存器隔离 → 产生振荡或亚稳态，工具无法做 timing analysis：

```systemverilog
// 危险：y 的输出参与了自身的 always_comb 计算
assign y = a & y;  // combinational loop
```

避免方式：确保组合逻辑的输入和输出之间没有循环路径；用 `always_comb` 让工具自动检测 loop，发现则报 error 或 warning。

**Lint 检查的常见问题**

- 信号宽度不匹配（port connection/assignment width mismatch）。
- 未使用的信号或未驱动的信号（undriven net）。
- 多驱动（multiple drivers on same net）。
- 不完整的 case/if-else，导致 latch inference。
- 敏感列表不完整（`always @(a)` 遗漏了依赖信号，仿真/综合行为不一致）。
- Blocking assignment 用在 `always_ff` 里（应用 non-blocking）。

## 面试回答

RTL synthesis converts an HDL description into a gate-level netlist by mapping to technology cells under timing, area, and power constraints. Common non-synthesizable constructs include time delays, initial blocks, and simulation system functions. Latches are unintentionally inferred when not all branches of a conditional statement assign the output — the fix is to either add a default assignment or cover all cases. I prefer `casez` with full coverage or `unique case` over `casex`, since `casex` treats X as don't care in both the expression and items, which can mask real bugs. Lint is run before synthesis to catch width mismatches, missing drivers, multiple drivers, and latch inference early.

## 常见追问

- 什么样的 RTL 不可综合？
  - 带时间延迟的语句（`#delay`）、`initial` block、`real` 类型、仿真系统任务（`$display` 等）通常不可综合。
- Latch 是怎么被 inferred 出来的？
  - 在 `always_comb` 中，某个输出信号在部分条件下没有被赋值，工具为了保持值，推断出 latch。先写默认值可以避免。
- `casez` 和 `casex` 有什么风险？
  - `casex` 把 X 也当 don't care，仿真中 X 可能错误匹配到某一分支，掩盖 bug；`casez` 相对安全，但仍建议用 `unique case` 配合完整分支。
- 如何避免 combinational loop？
  - 确保 `always_comb` 的输出不在输入敏感列表范围内形成循环；使用 `always_comb` 让工具自动检测，lint 工具也会检查此类问题。

## 易错点

- `always_ff` 里用 blocking assignment，综合和仿真行为不一致。
- 敏感列表漏写信号，用 `always_comb` 替代 `always @(*)` 可避免此问题。
- 误以为 `unique case` 只影响综合，实际上仿真也会检查 unique 违例。
- `casex` 在仿真时将 X 值"消化"掉，真实 X 传播 bug 可能被遮掩。
- 在 generate/for loop 中意外生成 combinational loop，尤其是参数化设计。

---

<a id="asic-interview-topics"></a>
## ASIC 面试专项知识点
标签：`#asic` `#interview` `#rtl` `#synthesis` `#dft` `#architecture`

这页从真实面试问题中提炼 ASIC 前端高频知识点，偏复习清单和回答骨架。

<a id="memory-hvt"></a>
## 1. Memory compiler 设置 HVT
### 核心概念

Memory compiler 用于生成 SRAM/register file 等 memory macro。生成时通常可以选择容量、位宽、bank、mux、读写端口、低功耗选项、timing/power 相关 cell option 等。HVT 指 high threshold voltage，高阈值器件 leakage 小但速度慢；LVT 速度快但 leakage 大；SVT 介于两者之间。

### 面试回答

Memory compiler can generate memory macros with different PPA trade-offs. Choosing HVT usually reduces leakage power, but it may increase delay and hurt timing. So I would use HVT for memories that are not timing critical or for low-power modes, while timing-critical paths may need SVT/LVT or a faster macro configuration. The final choice should be checked with timing, power, and area reports.

### 常见追问

- 为什么 HVT 省功耗？
- HVT 对 setup timing 有什么影响？
- 如果 memory path timing fail，除了换 LVT 还能怎么做？
- Memory macro 和 standard cell 在综合/布局中有什么区别？

<a id="scan-chain"></a>
## 2. Scan chain
### 核心概念

Scan chain 是 DFT 技术，把普通 flop 替换成 scan flop，并在 test mode 下串成 shift chain。这样 ATPG 可以把内部寄存器当作可控制、可观察的节点，提高制造测试覆盖率。

### 面试回答

A scan chain converts sequential elements into controllable and observable scan flops in test mode. During shift mode, test patterns are shifted in through scan_in under scan_enable, and captured responses are shifted out through scan_out. This helps ATPG detect manufacturing defects such as stuck-at and transition faults. In functional mode, scan flops behave like normal flops.

### 常见追问

- Scan enable 的作用是什么？
- Scan chain 和 functional path 的区别？
- ATPG 是什么？
- Scan chain 对 timing/area/power 有什么影响？

<a id="synthesis-report-logic-depth"></a>
## 3. 综合报告和逻辑深度
### 看综合报告的重点

- Timing：WNS、TNS、violating paths、critical path。
- Logic depth：critical path 上有多少级组合逻辑。
- Area：cell area、macro area、组合/时序单元比例。
- Power：dynamic/leakage/internal/switching。
- Cell usage：是否用了过多 high drive、buffer、低阈值单元。
- Constraints：clock、IO delay、false path、multicycle path 是否合理。

### 逻辑深度怎么解释

逻辑深度是一个时钟周期内信号经过的组合逻辑级数。级数越深，path delay 越大，越容易造成 setup violation。优化方式包括加 pipeline、拆分复杂组合逻辑、提前计算、减少 mux 层级、调整状态机/数据通路结构、retiming 或改约束。

### 面试回答

When reading a synthesis report, I first check timing summary such as WNS and TNS, then inspect the critical path to understand whether the violation is caused by long logic depth, large fanout, memory access, or constraint issues. If the path has too many combinational levels, I would consider pipelining, restructuring the datapath, reducing mux depth, or retiming, depending on the design latency requirement.

<a id="computer-architecture"></a>
## 4. Computer Architecture 面试重点
标签：`#computer-architecture` `#microarchitecture` `#ooo` `#cache` `#interview`

## 学习地图

- [OoO 基础](#ooo-basics)
- [Cache 基础](#cache-basics)

Computer architecture 面试通常不是考“背术语”，而是看你能不能把性能瓶颈、硬件结构和正确性约束连起来讲。ASIC/DV 岗重点是：OoO 怎么在保持 architectural state 正确的同时提高 ILP；cache 怎么利用 locality 降低平均访存延迟；以及这些机制如何被验证。

<a id="ooo-basics"></a>
## 4.1 OoO 基础
### 核心概念

Out-of-order execution 允许指令不按 program order 执行，以提高 ILP（instruction-level parallelism）；但最终 commit 通常仍按 program order，保证 precise architectural state。

核心目标：

- 让已经 ready 的年轻指令绕过被 cache miss、data dependency 或长延迟运算卡住的老指令。
- 用 rename 消除假相关，让更多指令并行等待和执行。
- 用 ROB 按序提交，保证异常、interrupt、branch mispredict 时 architectural state 可恢复。

常见组件：

| 组件 | 作用 | 面试关键词 |
| --- | --- | --- |
| Register renaming | 把 architectural register 映射到 physical register，消除 WAW/WAR 假相关 | RAT / PRF / free list |
| Reservation station / issue queue | 保存等待执行的指令，operand ready 后发射到执行单元 | wakeup / select |
| Reorder buffer (ROB) | 记录 in-flight 指令，按 program order commit | precise exception / rollback |
| Load-store queue (LSQ) | 追踪 load/store 顺序、地址相关、store-to-load forwarding | memory dependency |
| Branch predictor / recovery | 猜测控制流，mispredict 后 flush younger instructions 并恢复 rename state | checkpoint / squash |

## Dependency 类型

| Dependency | 含义 | OoO 怎么处理 |
| --- | --- | --- |
| RAW (Read After Write) | 真相关，后指令需要前指令结果 | 必须等待 producer ready，然后 wakeup |
| WAR (Write After Read) | 假相关，后写可能覆盖前读 | register renaming 消除 |
| WAW (Write After Write) | 假相关，两个写同一个 architectural register | register renaming 消除 |

## 典型流程

```text
Fetch -> Decode/Rename -> Dispatch -> Issue -> Execute -> Writeback -> Commit
```

1. Rename 阶段分配 physical register，并把源寄存器映射到 producer。
2. Dispatch 把指令放入 ROB 和 issue queue。
3. Operand ready 后 issue 到执行单元。
4. Execute 完成后 writeback result，唤醒依赖它的指令。
5. ROB 头部指令完成且无异常时按序 commit。

## 为什么需要按序 Commit

执行可以乱序，但 architectural state 必须像程序顺序执行一样可解释。按序 commit 能保证：

- Precise exception：异常发生时，异常之前的指令都已提交，异常之后的指令都没提交。
- Branch recovery：分支预测失败时，只需要清掉 younger instructions，并恢复 checkpoint。
- Interrupt/debug 更容易处理，因为 architectural state 只在 commit 点更新。

## LSQ 为什么复杂

Load/store 不是普通 ALU 指令，因为 memory address 可能晚些才算出来，而且不同地址可能无关、同地址必须保持正确顺序。

关键点：

- Store buffer / store queue 保存尚未 commit 的 store。
- Load 要检查更老 store 是否地址相同；如果相同且 store data ready，可以 forwarding。
- 如果 load 提前执行后发现和更老 store 冲突，需要 replay 或 flush。
- Memory ordering rule 取决于 ISA memory model。

### 面试回答

中文：OoO 的目标是提高 ILP，让已经 ready 的指令可以绕过被 cache miss 或长延迟操作卡住的老指令先执行。但为了保证 architectural state 正确，结果通常通过 ROB 按 program order commit。Rename 把 architectural register 映射到 physical register，消除 WAW/WAR 假相关；reservation station 或 issue queue 等待 operand ready 后发射；ROB 保证 precise exception 和 rollback；LSQ 处理 load/store 的顺序、forwarding 和 memory dependency。

English: OoO improves performance by allowing ready instructions to execute before older stalled instructions, while the ROB commits results in program order to preserve precise architectural state. Register renaming removes false dependencies, reservation stations track operand readiness, and the load-store queue handles memory ordering, store-to-load forwarding, and dependency checks.

### 常见追问

- 为什么需要 ROB？
  - 为了按序 commit、保证 precise exception，并在 branch mispredict/exception 时恢复状态。
- Rename 解决哪几种 dependency？
  - 解决 WAW 和 WAR 假相关，不解决 RAW 真相关。
- Precise exception 怎么保证？
  - 只在 ROB head 按序提交 architectural state；异常点之后的 younger instructions 没有提交，可以 flush。
- Load/store 为什么比普通 ALU 指令更复杂？
  - 因为地址可能晚算出，load 可能和更老 store 有同地址依赖，需要 LSQ 做检查、forwarding、replay。

### 易错点

- 说 OoO 是“乱序提交”。大多数通用 OoO core 是乱序执行、按序提交。
- 认为 rename 解决所有 dependency；它只解决假相关，RAW 仍要等数据 ready。
- 忽略 LSQ 和 memory ordering，导致 OoO 解释只停留在 ALU 指令。

<a id="cache-basics"></a>
## 4.2 Cache 基础
标签：`#computer-architecture` `#cache` `#memory-hierarchy` `#interview`

## 一句话定义

Cache 是位于 CPU core 和 main memory 之间的小容量高速存储，利用 temporal locality 和 spatial locality，把最近或相邻的数据留在更近的位置，从而降低 average memory access time。

## 为什么需要 Cache

CPU 频率远高于主存访问速度。如果每次 load/store 都直接访问 DRAM，pipeline 会频繁等待。Cache 通过保存常用数据，让大多数访问命中在 L1/L2/L3 中，只在 miss 时访问更低层 memory。

## 基本术语

| 术语 | 含义 |
| --- | --- |
| Cache line / block | cache 和 memory 之间搬运的基本单位，常见 32B/64B |
| Hit | 访问的数据在 cache 中 |
| Miss | 访问的数据不在 cache 中，需要从下一级取回 |
| Hit rate | 命中比例 |
| Miss penalty | miss 后访问下一级 memory 的额外延迟 |
| Tag / index / offset | 地址拆分字段，用于定位 set、line 内偏移和比较是否命中 |

## 地址拆分

以 byte address 为例：

```text
|        tag        |      index      |  block offset  |
```

- Offset：选择 cache line 内的 byte/word。
- Index：选择 cache 中的 set。
- Tag：和 set 内 line 的 tag 比较，判断是不是目标 memory block。

例子：32KB cache、64B line、4-way set associative。

- line offset = log2(64) = 6 bit。
- 总 line 数 = 32KB / 64B = 512 lines。
- set 数 = 512 / 4 = 128 sets，index = log2(128) = 7 bit。
- 剩余高位是 tag。

## Mapping 方式

| 类型 | 结构 | 优点 | 缺点 |
| --- | --- | --- | --- |
| Direct-mapped | 每个 memory block 只能放一个位置 | 硬件简单、hit latency 低 | conflict miss 多 |
| Fully associative | 可以放任意位置 | conflict miss 少 | tag 比较硬件昂贵 |
| Set-associative | 每个 block 映射到一个 set，可在 set 内多个 way 中选择 | 性能和复杂度折中 | 需要 replacement policy |

## Miss 类型

| Miss 类型 | 原因 | 常见优化 |
| --- | --- | --- |
| Compulsory miss | 第一次访问，cache 中不可能已有 | prefetch、larger line |
| Capacity miss | 工作集大于 cache 容量 | larger cache、blocking/tiling |
| Conflict miss | 多个 block 映射到同一个 set/line | higher associativity、better indexing |
| Coherence miss | 多核中其他 core 修改/失效了本 cache line | coherence protocol 设计和优化 |

## Write Policy

| Policy | 含义 | Trade-off |
| --- | --- | --- |
| Write-through | 写 cache 的同时写下一级 memory | 简单、一致性直观，但带宽压力大 |
| Write-back | 先只写 cache，line eviction 时再写回 | 带宽省、性能好，但需要 dirty bit 和一致性处理 |
| Write-allocate | write miss 时把 line 拉进 cache 再写 | 适合后续还会访问该 line |
| No-write-allocate | write miss 直接写下一级，不分配 cache line | 适合 streaming write |

## AMAT

Average Memory Access Time:

```text
AMAT = hit_time + miss_rate * miss_penalty
```

多级 cache 可以递归理解：

```text
AMAT = L1_hit_time + L1_miss_rate * (L2_hit_time + L2_miss_rate * memory_penalty)
```

面试时不要只背公式，要能解释：降低 miss rate、降低 miss penalty 或降低 hit time 都能改善 AMAT，但这三者常有 trade-off。例如提高 associativity 可能降低 conflict miss，但会增加 hit latency 和 tag compare 成本。

## Cache Coherence 概述

多核系统里，每个 core 可能有自己的 private cache。如果多个 cache 持有同一 memory block 的副本，需要 coherence protocol 保证：对同一地址的写最终对所有 core 可见，且各 core 看到的值是一致的。

两种主要实现方式：
- **Snooping**：每个 cache controller 监听共享总线上的所有事务，直接响应。延迟低，但总线带宽是瓶颈，通常用于小核数（≤8）系统。
- **Directory-based**：用一个集中目录记录哪些 cache 持有某 line 的副本，由目录发 invalidate/fetch 消息。可扩展到大核数，但目录本身有访问延迟。

---

## MESI 协议

### 四个状态

| 状态 | 含义 | Dirty? | 独占? |
| --- | --- | --- | --- |
| **Modified (M)** | 本 cache 独占，已修改，memory 中数据是旧的 | Yes | Yes |
| **Exclusive (E)** | 本 cache 独占，干净，与 memory 一致 | No | Yes |
| **Shared (S)** | 多个 cache 可能共有副本，干净 | No | No |
| **Invalid (I)** | 本 cache 中此 line 无效 | — | — |

### 总线事务

| 事务 | 触发条件 | 含义 |
| --- | --- | --- |
| BusRd | 处理器 read miss | 请求读 line，不打算修改 |
| BusRdX | 处理器 write miss | 请求读 line 并获得独占权 |
| BusUpgr | 处理器 write hit on S | 已有 line，请求 invalidate 其他副本（无需搬数据） |
| BusWB | 被替换的 M line eviction | 将 dirty data 写回 memory |

### 状态转换（本 cache 视角）

**Processor side（本 cache 发起）**

```text
I --[Pr Read]-->  E (若无其他 cache 持有) 或 S (若有其他持有)
I --[Pr Write]--> M (发 BusRdX，invalidate 其他)
S --[Pr Write]--> M (发 BusUpgr，invalidate 其他)
E --[Pr Write]--> M (安静升级，无需总线事务)
M --[Pr Read/Write]--> M (hit，无总线事务)
```

**Bus side（监听到其他 cache 的事务）**

```text
S --[BusRdX from other]--> I  (对方要写，必须 invalidate 本副本)
S --[BusUpgr from other]--> I (同上)
M --[BusRd from other]-->  S  (必须先把数据提供给请求方 + 写回 memory，或直接 cache-to-cache transfer)
M --[BusRdX from other]--> I  (同上，但对方拿到独占权)
E --[BusRd from other]-->  S  (有人也想读，降为 shared)
E --[BusRdX from other]--> I  (有人要写，失效)
```

### 关键设计点

- **Silent upgrade E→M**：E 状态写无需广播，因为没有其他副本，这是 MESI 相比 MSI 的主要优化。
- **Intervention / cache-to-cache transfer**：M line 被其他 core 读时，持有者直接将数据转发，避免两次访问 memory。
- **Snoop stall**：总线事务期间，若 cache controller 正在处理自己的 miss，需要 stall 等待总线仲裁。

---

## MOESI 协议

MOESI 在 MESI 基础上增加 **Owned (O)** 状态，解决 M line 被分享时必须先 writeback 的问题。

### 五个状态

| 状态 | 含义 | Dirty? | 内存是否最新? |
| --- | --- | --- | --- |
| **Modified (M)** | 独占、已修改，memory 旧 | Yes | No |
| **Owned (O)** | 被多个 cache 共享，但本 cache 持有最新版本（dirty shared），memory 旧 | Yes | No |
| **Exclusive (E)** | 独占、干净，memory 最新 | No | Yes |
| **Shared (S)** | 多个 cache 共享，干净，memory 最新 | No | Yes |
| **Invalid (I)** | 无效 | — | — |

### 与 MESI 的核心区别

MESI 中：M line 收到 BusRd（其他 core 要读）→ 必须先 writeback → 降为 S。这会产生一次额外的 memory write。

MOESI 中：M line 收到 BusRd → 不写回 memory，直接降为 **O**；请求方的 line 为 **S**。O line 负责日后 eviction 时写回 memory（ownership 转移）。

```text
M --[BusRd from other]--> O   (持有者保留 dirty 数据，对方得 S)
O --[BusRd from other]--> O   (继续持有 ownership，新请求方得 S)
O --[Pr Write]-----------> M  (发 BusUpgr，invalidate 所有 S 副本)
O --[eviction]-----------> BusWB + I (写回 memory)
S --[eviction]-----------> I  (干净，直接丢弃，无需写回)
```

### 适用场景

AMD 处理器（Opteron/Zen 系列）广泛使用 MOESI。优势在于 producer-consumer 场景下减少 memory traffic：P0 写数据，P1/P2 读数据时，dirty line 通过 cache-to-cache transfer 分享，不触碰 memory。

---

## Cache Consistency / Memory Consistency Model

Coherence 和 Consistency 是两个不同层次的概念：

| 概念 | 关注点 | 例子 |
| --- | --- | --- |
| **Coherence** | 同一地址在多 cache 间的最终一致性 | MESI/MOESI 保证同一 line 的值最终统一 |
| **Consistency** | 不同地址的 memory operation 对各 core 的可见顺序 | 一个 core 先写 A 再写 B，另一个 core 是否一定先看到 A 的更新？ |

### Sequential Consistency (SC)

最直观的模型：所有 core 的 memory operation 按某个全局顺序排列，每个 core 自己的操作按 program order 出现在该序列中。

```text
Core 0:  A=1, B=1
Core 1:  while(B==0); print(A)   // SC 保证一定打印 1
```

代价：硬件不能做任何乱序优化，性能差。现代 CPU 不实现严格 SC。

### Total Store Order (TSO) — x86

x86 使用的模型，接近 SC 但放宽了 store-load 顺序：

- **Store → Load 可以重排**（本 core 的 load 可以读到尚未提交的旧值，因为 store 进了 store buffer 还没 flush）。
- Store → Store、Load → Load、Load → Store 不可重排。

```text
Core 0:           Core 1:
  store A = 1       store B = 1
  load  r0 = B      load  r1 = A

// TSO 下可能出现 r0=0 且 r1=0（两个 store 都在 buffer 里）
// SC 下不可能
```

### Relaxed / Weak Models — ARM / POWER

ARM (AArch64) 和 POWER 采用更宽松的模型，几乎所有方向的重排都允许（Store-Store、Load-Load、Load-Store、Store-Load 均可重排），大幅提升 out-of-order 执行效率，但程序员/编译器必须显式插入 barrier。

### Memory Barrier / Fence

| 指令 | 架构 | 作用 |
| --- | --- | --- |
| `MFENCE` | x86 | 完整 fence：所有方向不重排 |
| `SFENCE` | x86 | store fence：store 不重排 |
| `LFENCE` | x86 | load fence：load 不重排 |
| `DMB ISH` | ARM | Inner Shareable domain 的数据 barrier |
| `DSB` | ARM | 比 DMB 更强，等待所有访存完成 |
| `ISB` | ARM | Instruction sync barrier，清空 pipeline |
| `sync` / `lwsync` | POWER | 全序 / 轻量同步 |

### 四种重排类型

| 重排 | 含义 | x86 是否允许 | ARM 是否允许 |
| --- | --- | --- | --- |
| Load → Load | 后来的 load 先于之前的 load 可见 | No | Yes |
| Store → Store | 后来的 store 先于之前的 store 可见 | No | Yes |
| Load → Store | load 之后的 store 先于 load 可见 | No | Yes |
| Store → Load | store 之后的 load 先于 store 可见 | **Yes** | Yes |

### Coherence 和 Consistency 的关系

- Coherence protocol（MESI/MOESI）是 consistency model 的底层机制，保证对同一地址最终可见。
- 但即使有 coherence，不同地址的操作仍然可能以不同顺序到达各 core 的可见点 → 需要 memory model 约束。
- 编程时：锁（mutex）内部通常包含 barrier，保证临界区内外的访存不越过锁边界；无锁编程需要显式 atomic + memory_order 指定。

---

## DV / ASIC 关注点

- Hit/miss path 是否正确返回数据。
- Tag/index/valid/dirty 更新是否正确。
- Replacement policy 是否不会选 invalid/locked line 错误。
- Write-back eviction 是否写回 dirty line。
- Flush/invalidate 指令是否正确影响 cache state。
- **Coherence 状态机**：每个合法事务下的状态转换是否正确（M→O、S→I、E→M 等）。
- **Snoop / intervention**：M 或 O line 被请求时，是否正确提供数据并写回或转移 ownership。
- **BusUpgr vs BusRdX**：hit-on-S 时是否用 upgrade 而非 full RdX，避免多余的数据传输。
- **Memory barrier 效果**：在多核 testbench 中，两个 core 的访存顺序是否符合目标 consistency model。
- Cache miss、backpressure、uncached access、error response 是否会让 pipeline 正确 stall/replay/flush。

## 面试回答

中文：Cache 是 CPU 和 memory 之间的小容量高速存储，利用 temporal locality 和 spatial locality 降低平均访存延迟。地址拆分为 tag/index/offset，set-associative 是 conflict miss 和硬件复杂度的折中。写策略上 write-back 性能好但需要 dirty bit。多核下需要 coherence protocol：MESI 用四个状态保证同一 line 的一致性，E 状态可以 silent upgrade 到 M；MOESI 增加 O 状态，M line 被共享时直接降为 O 而不写回 memory，减少 traffic。Coherence 之上还有 memory consistency model，描述不同地址操作的可见顺序：x86 是 TSO（只允许 store-load 重排），ARM 是 relaxed model，需要显式 barrier。DV 里重点验证状态机转换、snoop/intervention 正确性、dirty eviction 和 barrier 效果。

English: A cache is a small fast memory that exploits locality to reduce AMAT. The address is split into tag, index, and offset; set-associative mapping trades hardware cost for fewer conflict misses. MESI uses four states: Modified (dirty, exclusive), Exclusive (clean, exclusive), Shared (clean, potentially shared), Invalid. The E state enables silent M upgrade without a bus transaction. MOESI adds Owned, allowing a dirty line to be shared without a writeback — the owner provides data directly and retains responsibility for eventual writeback. Above coherence sits the memory consistency model: x86 uses TSO (only store-load reordering), while ARM uses a relaxed model requiring explicit barriers. In DV, key checks include correct state transitions on each bus event, snoop/intervention behavior for M/O lines, dirty eviction, and memory barrier effectiveness.

## 常见追问

- Direct-mapped 和 set-associative 的区别？
  - Direct-mapped 每个 block 只有一个位置；set-associative 可以在同一个 set 的多个 way 中选择，降低 conflict miss。
- Cache line 为什么不是只取一个 byte？
  - 因为空间局部性，程序通常会访问相邻地址，一次取一整 line 可以摊薄 miss penalty。
- Write-back 为什么需要 dirty bit？
  - 因为只有被修改过的 line eviction 时需要写回，干净 line 可以直接丢弃。
- Coherence 和 consistency 区别？
  - Coherence 关注同一地址多个副本的一致性；consistency 关注不同地址 memory operation 的可见顺序。
- MOESI 相比 MESI 的核心优势？
  - M line 被其他 core 读时，MESI 必须先写回 memory 再降为 S；MOESI 直接降为 O，由 O 负责 ownership，省掉了一次 memory write，适合 producer-consumer 场景。
- x86 TSO 下为什么 store-load 可以重排？
  - store 先进 store buffer，还没刷到 cache；此时后续 load 可能读到旧值。加 MFENCE 可以强制 drain store buffer。
- 无锁编程为什么需要 memory_order？
  - 编译器和 CPU 都可能在 consistency model 允许的范围内乱序；memory_order 告诉编译器/硬件在哪里插 barrier，确保操作的可见顺序符合算法语义。

## 易错点

- 把 cache hit latency、miss rate、miss penalty 混成一个概念。
- 忽略 tag/index/offset 和 associativity 的关系。
- 认为 write-back 每次 store 都写 memory；实际上通常 eviction dirty line 时才写回。
- 把 coherence 和 consistency 混为一谈。

<a id="book-dv-logic-architecture"></a>
## 书籍整理：数字逻辑与体系结构高频框架
标签：`#book` `#digital-logic` `#architecture` `#interview`

这一节来自《Cracking Digital VLSI Verification Interview》的技术章节整理，重点是把零散问法归类成可复习的知识地图，而不是逐题背答案。

### Digital Logic 复习地图

| 方向 | 要会讲什么 | 面试口径 |
| --- | --- | --- |
| 数制与编码 | binary/hex/BCD、1's/2's complement、Gray code、parity、ASCII | Gray code 每次只变 1 bit，常用于 CDC 指针；parity 用奇偶校验检测单 bit error；2's complement 是有符号整数主流表示。 |
| 基本门与 MUX | NAND/NOR universal gate、XOR、MUX 实现逻辑、X/Z 传播 | NAND/NOR 可以组合出 NOT/AND/OR；2:1 MUX 本质是 `sel ? a : b`，很多组合逻辑可转成选择结构。 |
| 组合逻辑 | mux/demux、encoder/decoder、priority encoder、adder、ring oscillator | Priority encoder 要说明优先级和无请求情况；ripple adder 延迟随 bit 数线性增长，CLA 用生成/传递信号缩短 carry path。 |
| 时序逻辑 | latch vs flip-flop、setup/hold、clock skew、race、counter、reset | Latch level-sensitive，FF edge-triggered；setup 路径太长，hold 路径太短；异步复位建议 async assert、sync deassert。 |
| FSM | Moore/Mealy、状态数与 FF 数、state encoding | Moore 输出只依赖状态，毛刺更好控；Mealy 输出依赖状态和输入，可能状态更少但输入毛刺要谨慎。 |
| ASIC/SOC flow | spec、architecture、RTL、lint、CDC、synthesis、DFT、STA、P&R、GLS、signoff | 回答流程题要从需求到 signoff 串起来，并说明每一步发现什么类型的问题。 |

### Computer Architecture 复习地图

| 方向 | 要会讲什么 | 面试口径 |
| --- | --- | --- |
| ISA/架构风格 | RISC vs CISC、Von Neumann vs Harvard、endianness | RISC 指令简单、长度规整、利于 pipeline；CISC 指令复杂、编码可变；endianness 只影响多字节数据在 memory 中的 byte 顺序。 |
| Memory hierarchy | SRAM/DRAM、register、cache、main memory、virtual memory | SRAM 快但面积大，常用于 cache；DRAM 密度高但要 refresh，常作主存。 |
| Pipeline | structural/data/control hazard、forwarding、stall、flush | Structural 是资源冲突，data 是依赖未满足，control 是分支/跳转导致取错路径。 |
| Addressing mode | immediate、register、base+offset、indirect | 讲清 operand 从哪里来，以及地址计算是否需要 ALU/寄存器读。 |
| Cache | locality、hit/miss、mapping、replacement、write policy、coherence | Temporal locality 是近期用过还会用，spatial locality 是邻近地址也可能被用。 |
| Virtual memory | virtual/physical address、page table、TLB、page fault | TLB 缓存 VA 到 PA 翻译；page fault 由 OS 处理，可能从 storage 调页或报告非法访问。 |
| Interrupt/exception | interrupt、exception、vectored interrupt | Interrupt 多由外部事件触发，exception 多由当前指令触发；vectored interrupt 直接跳到对应 handler 地址。 |
| 高性能 CPU | superscalar、in-order vs OoO、branch prediction、memory mapped I/O | Superscalar 每周期可发射多条指令；OoO 提高利用率但要保证按序提交和精确异常。 |

### 面试回答

中文：这类基础题不要孤立背概念，最好按“编码/组合逻辑/时序逻辑/FSM/ASIC flow”和“ISA/pipeline/cache/virtual memory/interrupt/OoO”两张地图回答。比如问 Gray code，就联系到异步 FIFO 指针；问 setup/hold，就联系 STA 修复；问 cache，就从 locality、tag/index/offset、mapping、write policy、coherence 逐层展开。这样回答会显得你不是只记结论，而是能把基础知识放回真实 RTL 和验证场景。

English: For digital logic and computer architecture interview questions, I would organize the answer by topic instead of memorizing isolated facts. Digital logic covers encoding, combinational logic, sequential logic, FSMs, and the ASIC flow. Architecture covers ISA style, pipelining, memory hierarchy, cache, virtual memory, interrupts, and out-of-order execution. The key is to connect each concept to a real design or verification scenario, such as gray code for async FIFO pointers, setup/hold for STA, and cache locality for performance.

### 常见追问

- Gray code 为什么常用于异步 FIFO？
  - 相邻值只变 1 bit，跨域同步指针时不会因为多 bit 同时变化而采到非法中间值。
- Ripple carry adder 和 carry look-ahead adder 区别？
  - Ripple 简单但 carry 逐 bit 传播，延迟随位宽增长；CLA 提前计算 generate/propagate，面积更大但速度更快。
- Pipeline hazard 怎么分类和处理？
  - Structural 用资源复制/仲裁，data 用 forwarding/stall，control 用 branch prediction/flush。
- RISC 和 CISC 最大区别？
  - RISC 倾向简单规整指令和 load/store 架构，便于 pipeline；CISC 指令更复杂，可能一条指令完成多个微操作。

### 易错点

- 把 Gray code 当成纠错码；它主要减少相邻状态转换的多 bit 采样风险，不负责纠错。
- 只背 Moore/Mealy 定义，不说明毛刺、状态数和输入时序风险。
- 说 cache hit/miss 但不会拆 tag/index/offset。
- 讲 interrupt/exception 时混淆外部异步事件和指令自身导致的同步异常。

---

<a id="power-clocking-upf"></a>
## 低功耗、Clocking 与 UPF
标签：`#low-power` `#clocking` `#upf` `#interview`

### 一句话定义

低功耗设计是在功能正确之外，通过 clock gating、power gating、multi-voltage、DVFS 和 UPF 描述来控制动态功耗与静态漏电，同时确保跨电源域、跨时钟域和复位行为仍然安全。

### 功耗组成

| 类型 | 近似来源 | 主要影响因素 | 常见手段 |
| --- | --- | --- | --- |
| Dynamic power | 节点翻转充放电 | `C * V^2 * f * activity` | clock gating、降低切换率、DVFS、operand isolation |
| Short-circuit power | PMOS/NMOS 短暂同时导通 | 输入 transition、cell sizing | 优化 slew、合理 cell 选择 |
| Static/leakage power | 器件关断时漏电 | 工艺、温度、Vt、面积 | power gating、HVT cell、memory sleep/shutdown |

### 常见低功耗技术

| 技术 | 核心思想 | DV/RTL 关注点 |
| --- | --- | --- |
| Clock gating | 模块空闲时关 clock，减少无意义翻转 | 使用 ICG cell，不用普通组合逻辑直接 gate clock；enable 要稳定，避免 glitch。 |
| Power gating | 空闲时切断电源域，降低 leakage | isolation、retention、power-up/down sequence、reset/init 状态都要验证。 |
| Multi-voltage domain | 不同模块用不同电压 | 需要 level shifter；低压域到高压域、高压域到低压域规则不同。 |
| DVFS | 动态调整电压和频率 | 切换期间要保证 clock/reset/PLL lock/firmware handshake 安全。 |
| UPF | 用外部文件描述 power intent | UPF 中定义 power domain、isolation、retention、level shifter 和电源状态表。 |

### Clocking 面试关注

- Gated clock 应由综合/后端插入 ICG cell，RTL 里通常写 clock enable 风格。
- Generated clock、divided clock、clock mux 都要在 STA 里约束清楚。
- 跨 clock domain 的信号仍按 CDC 处理，不能因为两个 clock 有来源关系就默认安全。
- Clock skew、jitter、uncertainty 都会影响 setup/hold margin。

### 面试回答

中文：CMOS 功耗主要分动态功耗和静态漏电。动态功耗和 `C * V^2 * f * activity` 相关，所以常用 clock gating、降低切换率和 DVFS；静态漏电和工艺、温度、阈值电压相关，所以常用 power gating、HVT cell 或 memory sleep。低功耗验证不能只看功能，还要检查 isolation、retention、level shifter、power sequence、reset sequence 和 UPF power state table 是否正确。

English: CMOS power mainly consists of dynamic power and leakage power. Dynamic power depends on capacitance, voltage, frequency, and switching activity, so techniques such as clock gating, activity reduction, and DVFS are effective. Leakage power depends on process, temperature, and threshold voltage, so power gating, HVT cells, and memory sleep modes are commonly used. In verification, low-power intent must be checked through isolation, retention, level shifters, power sequencing, reset behavior, and UPF power states.

### 常见追问

- Clock gating 为什么不能用普通组合逻辑直接 AND clock？
  - 普通组合逻辑可能产生毛刺，导致额外 clock edge；工程中用 ICG cell 或综合识别的 clock enable。
- UPF 主要描述什么？
  - Power domain、power switch、isolation、retention、level shifter、power state table 等 power intent。
- DVFS 切换时要验证什么？
  - 电压/频率切换 handshake、PLL lock、clock stable、reset/idle 状态、跨域通信暂停与恢复。

### 易错点

- 只说 `P = C V^2 f`，忘记 activity factor 和 leakage。
- 把 clock gating 当成关电源；它只减少 clock 翻转，不消除 leakage。
- Power domain 关闭后忘记隔离输出，导致 X 传播到仍上电的 domain。
- Retention flop 恢复后未验证保存状态是否和 power-down 前一致。

---

<a id="find-first-one"></a>
## 5. 手撕题：find first one
### 思路

这是 priority encoder。通常从 LSB 到 MSB 或从 MSB 到 LSB 扫描，遇到第一个 1 输出 index，并给 valid 标志。

```systemverilog
module find_first_one #(
  parameter int W = 32,
  parameter int IW = $clog2(W)
) (
  input  logic [W-1:0] in,
  output logic         valid,
  output logic [IW-1:0] index
);
  always_comb begin
    valid = 1'b0;
    index = '0;
    for (int i = 0; i < W; i++) begin
      if (!valid && in[i]) begin
        valid = 1'b1;
        index = i[IW-1:0];
      end
    end
  end
endmodule
```

注意：如果 W 不是 2 的幂，`IW` 仍可表示最大 index；面试时要说明无 1 时 valid=0，index 无意义或置 0。

<a id="sync-fifo"></a>
## 6. 手撕题：同步 FIFO
### 关键点

- 同一个 clock 下读写。
- 用 memory array 存数据。
- 用 write pointer、read pointer 和 count 判断 full/empty。
- 同周期 read/write 时 count 是否变化取决于是否真正发生 push/pop。

```systemverilog
module sync_fifo #(
  parameter int W = 8,
  parameter int DEPTH = 16,
  parameter int AW = $clog2(DEPTH)
) (
  input  logic         clk,
  input  logic         rst_n,
  input  logic         wr_en,
  input  logic [W-1:0] wr_data,
  input  logic         rd_en,
  output logic [W-1:0] rd_data,
  output logic         full,
  output logic         empty
);
  logic [W-1:0] mem [DEPTH];
  logic [AW-1:0] wr_ptr, rd_ptr;
  logic [$clog2(DEPTH+1)-1:0] count;

  wire do_wr = wr_en && !full;
  wire do_rd = rd_en && !empty;

  assign full  = (count == DEPTH);
  assign empty = (count == 0);
  assign rd_data = mem[rd_ptr];

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      wr_ptr <= '0;
      rd_ptr <= '0;
      count  <= '0;
    end else begin
      if (do_wr) begin
        mem[wr_ptr] <= wr_data;
        wr_ptr <= (wr_ptr == DEPTH-1) ? '0 : wr_ptr + 1'b1;
      end
      if (do_rd) begin
        rd_ptr <= (rd_ptr == DEPTH-1) ? '0 : rd_ptr + 1'b1;
      end
      unique case ({do_wr, do_rd})
        2'b10: count <= count + 1'b1;
        2'b01: count <= count - 1'b1;
        default: count <= count;
      endcase
    end
  end
endmodule
```

面试时要主动说明：这个版本是 async-read 风格的简单 FIFO；如果目标 memory 是 sync-read SRAM，`rd_data` 需要寄存，empty/read latency 要重新定义。

<a id="one-hot"></a>
## 7. 手撕题：one-hot 检测
### RTL 写法

```systemverilog
assign is_onehot  = (x != '0) && ((x & (x - 1'b1)) == '0);
assign is_onehot0 = ((x & (x - 1'b1)) == '0);
```

### SystemVerilog 内建函数

```systemverilog
assign is_onehot  = $onehot(x);
assign is_onehot0 = $onehot0(x);
```

### SVA 写法

```systemverilog
assert property (@(posedge clk) disable iff (!rst_n) $onehot(state));
```

`$onehot` 要求恰好一个 bit 为 1；`$onehot0` 允许全 0 或恰好一个 bit 为 1。
---

<a id="asic-interview-answers"></a>
## 面试回答速查（中文 + English）
### Memory compiler 设置 HVT

中文：Memory compiler 生成 SRAM 或 register file 这类 memory macro 时，可以选择不同的器件阈值和 PPA 配置。HVT 是高阈值，优点是 leakage 更低，缺点是速度更慢、delay 更大。所以如果 memory 不在 critical path 上，或者目标是低功耗，可以考虑 HVT；如果 timing 很紧，就可能需要 SVT/LVT 或更快的 macro option。最后要结合 timing、power、area report 判断。

English: Memory compiler can generate memory macros with different PPA trade-offs. Choosing HVT usually reduces leakage power, but it may increase delay and hurt timing. I would use HVT for memories that are not timing critical or for low-power modes, while timing-critical paths may need SVT/LVT or a faster macro configuration.

### Scan chain

中文：Scan chain 是一种 DFT 技术，把普通触发器替换成 scan flop，并在 test mode 下串成链。测试时通过 scan_enable 进入 shift mode，把 ATPG pattern 从 scan_in 移入，再 capture DUT response，最后从 scan_out 移出。它的核心价值是提高内部寄存器的可控性和可观察性，用于检测 stuck-at、transition fault 等制造缺陷。

English: A scan chain converts sequential elements into controllable and observable scan flops in test mode. Test patterns are shifted in through scan_in under scan_enable, captured responses are shifted, then shifted out through scan_out. This helps ATPG detect manufacturing faults.

### 综合报告和逻辑深度

中文：看综合报告我会先看 WNS/TNS 和 violating path，再看 critical path 的起点终点、logic depth、fanout、cell delay、net delay 和约束是否合理。逻辑深度越深，一个周期内组合延迟越大，频率越难提高。常见优化包括加 pipeline、拆复杂 mux、提前计算、降低 fanout、重构 datapath 或 retiming。

English: When reading a synthesis report, I first check WNS/TNS and the critical paths, then inspect whether the issue comes from long logic depth, fanout, cell delay, net delay, memory access, or constraints. If the path has too many combinational levels, I would consider pipelining, restructuring the datapath, reducing mux depth, or retiming.

### OoO

中文：OoO 通过让 ready 的指令先执行来提高并行度，但最终通常通过 ROB 按 program order commit，从而保持精确异常和架构状态一致。Rename 用来消除 WAW/WAR 假相关，reservation station/issue queue 等待操作数 ready，LSQ 处理 load/store 的顺序、转发和依赖检查。

English: OoO improves performance by allowing ready instructions to execute before older stalled instructions, while the ROB commits results in program order. Register renaming removes false dependencies, reservation stations track operand readiness, and the LSQ handles memory ordering and forwarding.

### Cache

中文：Cache 是 CPU 和 memory 之间的小容量高速存储，利用 temporal locality 和 spatial locality 降低平均访存延迟。地址通常拆成 tag、index、offset：index 选 set，tag 判断命中，offset 选 line 内数据。Direct-mapped 简单但 conflict miss 多，set-associative 是常见折中。Write-through 简单但带宽压力大；write-back 性能更好但需要 dirty bit 和 eviction 写回。多核系统还要考虑 coherence，例如 MESI 通过 invalidation/writeback 保证同一 cache line 的副本一致。

English: A cache is a small fast memory between the CPU and main memory. It exploits temporal and spatial locality to reduce average memory access time. The address is split into tag, index, and offset. Set associativity reduces conflict misses compared with direct mapping. Write-through is simpler but uses more bandwidth, while write-back requires dirty tracking and eviction handling. In multicore systems, coherence protocols such as MESI keep copies of the same cache line consistent.

### 数字逻辑与体系结构高频框架

中文：数字逻辑基础可以按编码、组合逻辑、时序逻辑、FSM 和 ASIC flow 来讲；体系结构可以按 ISA、pipeline、cache、virtual memory、interrupt 和 OoO 来讲。面试里最好把概念和场景连起来，例如 Gray code 对应 async FIFO pointer，setup/hold 对应 STA 修复，pipeline hazard 对应 forwarding/stall/flush，cache locality 对应 hit/miss 和 AMAT。

English: Digital logic basics can be organized into encoding, combinational logic, sequential logic, FSMs, and the ASIC flow. Architecture topics can be organized into ISA, pipeline, cache, virtual memory, interrupts, and out-of-order execution. Strong interview answers connect each concept to a concrete design or verification use case.

### 低功耗与 UPF

中文：动态功耗和电容、电压平方、频率、翻转率相关，常用 clock gating、DVFS、降低 activity；静态漏电和工艺、温度、阈值电压相关，常用 power gating、HVT 和 memory sleep。UPF 描述 power domain、isolation、retention、level shifter 和 power state table，低功耗验证要覆盖 power sequence、reset sequence 和跨电源域信号。

English: Dynamic power depends on capacitance, voltage squared, frequency, and activity, while leakage depends on process, temperature, and threshold voltage. UPF captures power domains, isolation, retention, level shifters, and power states. Low-power verification must check sequencing and cross-domain behavior.

### 手撕 RTL：find first one / FIFO / one-hot

中文：find first one 本质是 priority encoder，要说明扫描方向、valid 和无 1 情况；同步 FIFO 要说明 mem、读写指针、full/empty、count 或额外 bit、同周期读写规则；one-hot 可以用 `(x != 0) && ((x & (x - 1)) == 0)`，或者 SystemVerilog 的 `$onehot()`。

English: Find-first-one is a priority encoder with a valid flag. A synchronous FIFO needs memory, read/write pointers, full/empty logic, and clear same-cycle read/write behavior. One-hot can be checked with `(x != 0) && ((x & (x - 1)) == 0)` or `$onehot()`.


