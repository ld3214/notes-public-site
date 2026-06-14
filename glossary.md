[返回目录](index.md)

# Glossary

术语速查按方向分组；详细解释仍回链到知识库、项目笔记或题库。

## ASIC / DV 基础

| 术语 | 全称 | 简短解释 | 相关笔记 |
| --- | --- | --- | --- |
| DUT | Design Under Test | 被验证/测试的设计模块 | |
| RTL | Register Transfer Level | 寄存器传输级设计描述 | |
| STA | Static Timing Analysis | 静态时序分析 | [时序与 STA](knowledge-base/asic-frontend.md#timing-sta) |
| CDC | Clock Domain Crossing | 跨时钟域信号传输，需同步电路避免亚稳态 | [CDC/RDC](knowledge-base/asic-frontend.md#cdc-rdc) / [Async FIFO UVM 验证](projects-hr/projects-and-behavioral.md#star-async-fifo) |
| BFM | Bus Functional Model | 把 transaction 转成总线 pin-level 行为，或作为 slave/master 响应协议请求的模型 | [验证基础高频框架](knowledge-base/design-verification.md#book-dv-fundamentals) |
| ABV | Assertion-Based Verification | 用 assertion/property 持续检查协议、时序和设计不变量的验证方法 | [验证基础高频框架](knowledge-base/design-verification.md#book-dv-fundamentals) / [SVA](knowledge-base/systemverilog-uvm.md#sva) |
| GLS | Gate-Level Simulation | 综合后网表仿真，用于检查 reset/X、timing annotation、DFT/clock gating/低功耗插入后的问题 | [验证基础高频框架](knowledge-base/design-verification.md#book-dv-fundamentals) |
| UPF | Unified Power Format | 描述 power domain、isolation、retention、level shifter 和 power state 的低功耗意图文件 | [低功耗、Clocking 与 UPF](knowledge-base/asic-frontend.md#power-clocking-upf) |
| DVFS | Dynamic Voltage and Frequency Scaling | 根据负载动态调整电压和频率的低功耗技术 | [低功耗、Clocking 与 UPF](knowledge-base/asic-frontend.md#power-clocking-upf) |
| Coverage Waiver | 覆盖率豁免 | 对结构不可达、第三方库、generated code 或非目标逻辑的 coverage hole 做有理由的排除 | [AXI DMA 项目 debug 记录](projects-hr/projects-and-behavioral.md#axi-dma-regression-debug-coverage) |

## SystemVerilog / UVM

| 术语 | 全称 | 简短解释 | 相关笔记 |
| --- | --- | --- | --- |
| UVM | Universal Verification Methodology | 基于 SystemVerilog 的验证方法学 | [UVM 总览](knowledge-base/systemverilog-uvm.md#uvm-overview) |
| TLM | Transaction-Level Modeling | UVM 中组件之间传递 transaction object 的通信机制 | [UVM TLM 通信](knowledge-base/systemverilog-uvm.md#uvm-tlm) |
| Factory | UVM Factory | UVM 中用于对象创建和类型替换的机制 | [UVM Factory 机制](knowledge-base/systemverilog-uvm.md#uvm-factory) |
| Objection | UVM Objection | 控制 run phase 是否可以结束的机制 | [UVM Phase 机制](knowledge-base/systemverilog-uvm.md#uvm-phases) |
| RAL | Register Abstraction Layer | UVM 中用于抽象 DUT register map、统一寄存器访问和维护 mirror/check 的机制 | [Register Model / UVM RAL](knowledge-base/systemverilog-uvm.md#uvm-ral) |
| Read-hash Scoreboard | AXI read-hash scoreboard | 用 byte address 做 key 的稀疏 expected memory image，比较 AXI write 后再 read 回来的数据一致性 | [AXI read-hash 实现](projects-hr/ddr4-controller-apb-axi-vip-details.md#ddr4-axi-read-hash-implementation) |
| Virtual Sequence | UVM Virtual Sequence | 协调多个 agent sequence 的系统级 sequence，常用于多接口场景 | [Virtual Sequence / Virtual Sequencer](knowledge-base/systemverilog-uvm.md#uvm-virtual-sequence) |
| Virtual Sequencer | UVM Virtual Sequencer | 保存 sub-sequencer、RAL model 和 config 等共享 handle 的 env 级协调器 | [Virtual Sequence / Virtual Sequencer](knowledge-base/systemverilog-uvm.md#uvm-virtual-sequence) |
| `m_sequencer` | UVM sequence built-in sequencer handle | sequence 被 `start()` 启动后由 UVM 设置的通用 sequencer handle | [`m_sequencer` vs `p_sequencer`](knowledge-base/systemverilog-uvm.md#uvm-sequencer-handles) |
| `p_sequencer` | UVM typed sequencer handle | 通过 `` `uvm_declare_p_sequencer`` 从 `m_sequencer` cast 出来的强类型 handle | [`m_sequencer` vs `p_sequencer`](knowledge-base/systemverilog-uvm.md#uvm-sequencer-handles) |
| Dynamic Array | 动态数组 | 运行时分配长度的连续数组 | [动态数组、关联数组、队列](knowledge-base/systemverilog-uvm.md#sv-arrays-queues) |
| Associative Array | 关联数组 | 以 key/value 方式存储的稀疏数组 | [动态数组、关联数组、队列](knowledge-base/systemverilog-uvm.md#sv-arrays-queues) |
| Queue | 队列 | 支持 push/pop 的有序动态集合 | [动态数组、关联数组、队列](knowledge-base/systemverilog-uvm.md#sv-arrays-queues) |
| Implicit Conversion | 隐式转换 | 编译器根据赋值、表达式或参数传递自动做的类型转换 | [Cast](knowledge-base/systemverilog-uvm.md#sv-class-casting) |
| Explicit Conversion | 显式转换 | 工程师写出目标类型的转换，如 `byte'(i)`、`$signed(x)`、`$cast()` | [Cast](knowledge-base/systemverilog-uvm.md#sv-class-casting) |
| fork/join_none | SV 并发语句 | 启动并发进程后立即继续执行，后续需要 `wait fork` 或其他同步方式等待结果 | [fork/join_none 行并行统计](knowledge-base/systemverilog-uvm.md#sv-fork-join-none-row-count) |
| valid-ready | 握手协议 | `valid && ready` 同周期为 1 时一次 transaction 完成 | [valid-ready task TB](knowledge-base/systemverilog-uvm.md#sv-valid-ready-task-tb) |
| Upcast | 向上转换 | 派生类 handle 赋给基类 handle，通常隐式合法 | [Class Cast](knowledge-base/systemverilog-uvm.md#sv-class-casting) |
| Downcast | 向下转换 | 基类 handle 转回派生类 handle，需要 `$cast()` 做运行时类型检查 | [Class Cast](knowledge-base/systemverilog-uvm.md#sv-class-casting) |

## Protocol / Interface

| 术语 | 全称 | 简短解释 | 相关笔记 |
| --- | --- | --- | --- |
| APB | Advanced Peripheral Bus | AMBA 低功耗低速总线，无 outstanding，用于外设寄存器访问 | [APB 协议](knowledge-base/protocols.md#apb) |
| AXI Burst | AXI burst transfer | 一次 address handshake 后连续传多个 beat；AXI4 `LEN`/`ALEN` 字段通常表示 beats-1 | [AXI DMA 参数](projects-hr/axi-dma-uvm-details.md#axi-dma-project-parameters) |
| AXI Outstanding | Outstanding transaction | master 在前一笔 transaction 完成前继续发起新 transaction，依靠 ID/ordering 规则追踪未完成请求 | [AXI outstanding](knowledge-base/protocols.md#axi-outstanding) |
| AXI QoS | AXI Quality of Service | AXI `ARQOS/AWQOS` 或扩展 user bits 表示的访问优先级，DDR controller 可映射到 LPR/VPR/HPR/NPW/VPW 调度队列 | [DDR4 高级测试场景分析](projects-hr/ddr4-controller-apb-axi-vip-details.md#ddr4-advanced-test-scenarios) |
| AXI Exclusive Access | AXI exclusive read/write | master 先 exclusive read 建立 monitor，再用匹配的 exclusive write 尝试原子更新；中间被其他访问破坏时应返回失败响应 | [DDR4 高级测试场景分析](projects-hr/ddr4-controller-apb-axi-vip-details.md#ddr4-advanced-test-scenarios) |
| UART | Universal Asynchronous Receiver/Transmitter | 异步串行通信接口，start bit + data + parity + stop bit 格式 | [APB-UART 验证环境](projects-hr/projects-and-behavioral.md#star-apb-uart) |
| AXI VIP | AXI Verification IP | 可复用的 AXI 协议验证组件，提供 master/slave agent 和 protocol checker | [TVIP-AXI Crossbar 验证](projects-hr/projects-and-behavioral.md#star-tvip-axi) |
| DFI | DDR PHY Interface | DDR controller 和 DDR PHY 之间的标准接口；DFI VIP 监控这一层，DDR4 Memory VIP 通常看 PHY 后的 JEDEC pin-level 信号 | [DDR4 VIP/checker 分工](projects-hr/ddr4-controller-apb-axi-vip-details.md#ddr4-vip-checker-scope) |
| JEDEC | Joint Electron Device Engineering Council | 定义 DDR4 等存储器标准；在 DDR 验证里常指 DDR4 pin-level 协议和 timing 规则 | [DDR4 VIP/checker 分工](projects-hr/ddr4-controller-apb-axi-vip-details.md#ddr4-vip-checker-scope) |
| DDR4 Memory VIP | DDR4 Verification IP | DDR4 存储器模型/VIP，检查 JEDEC pin-level command、bank/rank state、DQ/DQS 和 timing violation | [DDR4 VIP/checker 分工](projects-hr/ddr4-controller-apb-axi-vip-details.md#ddr4-vip-checker-scope) |
| NODIMM | No-DIMM DDR device mode | DDR 验证中不建 UDIMM/RDIMM DIMM wrapper，而是直接用 discrete DDR device VIP/agent 连接 controller/PHY 侧信号的模式 | [DDR4 NODIMM 测试配置](projects-hr/ddr4-controller-apb-axi-vip-details.md#ddr4-nodimm-test-config) |
| DDR ECC Poison | DDR ECC error injection | 通过 poison sideband 或 ECC poison 寄存器制造 correctable/uncorrectable ECC 行为，用于验证 error response、interrupt、status 和恢复路径 | [DDR4 高级测试场景分析](projects-hr/ddr4-controller-apb-axi-vip-details.md#ddr4-advanced-test-scenarios) |
| Crossbar | AXI Crossbar | 多 master 到多 slave 的 AXI 互联结构，含地址解码和 arbitration | [TVIP-AXI Crossbar 验证](projects-hr/projects-and-behavioral.md#star-tvip-axi) |
| Gray Code | 格雷码 | 相邻数值仅一位变化的编码，用于跨时钟指针同步 | [Async FIFO UVM 验证](projects-hr/projects-and-behavioral.md#star-async-fifo) |

## Architecture

| 术语 | 全称 | 简短解释 | 相关笔记 |
| --- | --- | --- | --- |
| OoO | Out-of-Order Execution | 指令可乱序执行、通常按序提交的微架构执行方式 | [OoO 基础](knowledge-base/asic-frontend.md#ooo-basics) |
| ROB | Reorder Buffer | OoO 中记录 in-flight 指令并按序提交的结构 | [OoO 基础](knowledge-base/asic-frontend.md#ooo-basics) |
| RS | Reservation Station | OoO 中等待操作数 ready 并选择指令发射到功能单元的结构 | [OoO RISC-V 处理器项目](projects-hr/projects-and-behavioral.md#star-ooo-riscv) |
| PRF | Physical Register File | register renaming 后存放 physical register value 的寄存器堆 | [OoO RISC-V 处理器项目](projects-hr/projects-and-behavioral.md#star-ooo-riscv) |
| LSQ | Load-Store Queue | OoO 中处理 load/store 顺序、forwarding 和 memory dependency 的结构 | [OoO 基础](knowledge-base/asic-frontend.md#ooo-basics) |
| MSHR | Miss Status Handling Register | nonblocking cache 中追踪未完成 cache miss 的结构 | [OoO RISC-V 处理器项目](projects-hr/projects-and-behavioral.md#star-ooo-riscv) |
| BTB | Branch Target Buffer | branch predictor 中记录 branch PC 与 target PC 的表 | [OoO RISC-V 处理器项目](projects-hr/projects-and-behavioral.md#star-ooo-riscv) |
| TLB | Translation Lookaside Buffer | 缓存虚拟地址到物理地址翻译结果的小型高速表 | [数字逻辑与体系结构高频框架](knowledge-base/asic-frontend.md#book-dv-logic-architecture) |
| Cache | Cache Memory | CPU 和主存之间的小容量高速存储，用于降低平均访存延迟 | [Cache 基础](knowledge-base/asic-frontend.md#cache-basics) |
| Cache Line | Cache Block | cache 和 memory 之间搬运的基本单位 | [Cache 基础](knowledge-base/asic-frontend.md#cache-basics) |
| AMAT | Average Memory Access Time | 平均访存时间，常用 `hit_time + miss_rate * miss_penalty` 表示 | [Cache 基础](knowledge-base/asic-frontend.md#cache-basics) |
| MESI | Modified/Exclusive/Shared/Invalid | 常见 cache coherence protocol 状态集合；E 状态支持 silent upgrade | [Cache 基础](knowledge-base/asic-frontend.md#cache-basics) |
| MOESI | Modified/Owned/Exclusive/Shared/Invalid | MESI 扩展，O 状态允许 dirty line 直接分享而不写回 memory | [Cache 基础](knowledge-base/asic-frontend.md#cache-basics) |
| TSO | Total Store Order | x86 的 memory consistency model，仅允许 store-load 重排 | [Cache 基础](knowledge-base/asic-frontend.md#cache-basics) |
| Memory Barrier | Fence | 强制 CPU/编译器不跨越此点重排 memory operation | [Cache 基础](knowledge-base/asic-frontend.md#cache-basics) |
| Snooping | Snooping Protocol | cache controller 监听共享总线上所有事务来维护 coherence | [Cache 基础](knowledge-base/asic-frontend.md#cache-basics) |
| Directory Protocol | Directory-based Coherence | 用集中目录记录各 cache 副本状态，支持大核数扩展 | [Cache 基础](knowledge-base/asic-frontend.md#cache-basics) |

## Project Terms

| 术语 | 全称 | 简短解释 | 相关笔记 |
| --- | --- | --- | --- |
| NPU | Neural Processing Unit | 面向神经网络推理/训练加速的专用处理器 | [INT8 NPU 流片项目](projects-hr/projects-and-behavioral.md#star-int8-npu-tapeout) |
| MAC | Multiply-Accumulate | 乘加运算单元，CNN 卷积加速中的核心计算结构 | [INT8 NPU 流片项目](projects-hr/projects-and-behavioral.md#star-int8-npu-tapeout) |
| DPI | Direct Programming Interface | SystemVerilog 与 C/C++ 之间互相调用的接口机制 | [INT8 NPU 流片项目](projects-hr/projects-and-behavioral.md#star-int8-npu-tapeout) |
| C model | C Golden Model | 用 C/C++ 写的参考模型，常用于和 RTL 结果比对 | [INT8 NPU 流片项目](projects-hr/projects-and-behavioral.md#star-int8-npu-tapeout) |
| GOPS | Giga Operations Per Second | 每秒十亿次操作，常用于衡量 NPU/DSP 计算吞吐 | [INT8 NPU 流片项目](projects-hr/projects-and-behavioral.md#star-int8-npu-tapeout) |
