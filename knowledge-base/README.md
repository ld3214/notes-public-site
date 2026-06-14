[返回目录](../index.md)

# Knowledge Base

知识正文只保留四个大文件，避免过度拆散。每个文件顶部都有页内目录，具体题目从这里跳到精确 anchor。

## 四个主文件

| 文件 | 内容 |
| --- | --- |
| [ASIC Frontend](asic-frontend.md#asic-overview) | RTL、综合、STA、CDC、DFT、计算机体系结构、手撕题 |
| [Design Verification](design-verification.md#dv-overview) | testplan、coverage、scoreboard、debug、regression |
| [SystemVerilog / UVM](systemverilog-uvm.md#sv-overview) | SV 语法/OOP、SVA、UVM phase/factory/TLM/sequence/RAL |
| [Protocols](protocols.md#protocol-overview) | AXI、AXI-Lite、APB 等协议 |

## 高频复习入口

| 方向 | 重点 |
| --- | --- |
| ASIC / RTL | [时序与 STA](asic-frontend.md#timing-sta), [综合报告和逻辑深度](asic-frontend.md#synthesis-report-logic-depth), [同步 FIFO](asic-frontend.md#sync-fifo), [one-hot](asic-frontend.md#one-hot) |
| Architecture | [OoO 基础](asic-frontend.md#ooo-basics), [Cache 基础](asic-frontend.md#cache-basics) |
| 书籍整理 | [数字逻辑与体系结构高频框架](asic-frontend.md#book-dv-logic-architecture), [验证基础高频框架](design-verification.md#book-dv-fundamentals), [SV/Verilog 高频语法清单](systemverilog-uvm.md#book-sv-verilog-checklist), [UVM 高频问法清单](systemverilog-uvm.md#book-uvm-interview-checklist) |
| DV 方法论 | [Verification Plan](design-verification.md#verification-plan), [Functional Coverage](design-verification.md#functional-coverage), [Debug 方法](design-verification.md#debug-methods), [VIP checker vs Scoreboard](design-verification.md#vip-checker-scoreboard), [Formal Verification](design-verification.md#formal-verification) |
| Low Power | [低功耗、Clocking 与 UPF](asic-frontend.md#power-clocking-upf) |
| UVM 核心 | [UVM 总览](systemverilog-uvm.md#uvm-overview), [TLM](systemverilog-uvm.md#uvm-tlm), [Factory](systemverilog-uvm.md#uvm-factory), [Phase](systemverilog-uvm.md#uvm-phases), [UVM 高频问法清单](systemverilog-uvm.md#book-uvm-interview-checklist) |
| SV Coding | [task FSM](systemverilog-uvm.md#sv-task-fsm-find-first-one), [fork/join_none](systemverilog-uvm.md#sv-fork-join-none-row-count), [valid-ready task TB](systemverilog-uvm.md#sv-valid-ready-task-tb) |
| Sequence / RAL | [Virtual Sequence](systemverilog-uvm.md#uvm-virtual-sequence), [`m_sequencer` vs `p_sequencer`](systemverilog-uvm.md#uvm-sequencer-handles), [AXI DMA vseq 调用链](systemverilog-uvm.md#uvm-axi-dma-vseq-flow), [UVM RAL](systemverilog-uvm.md#uvm-ral) |
| Protocol | [AXI](protocols.md#axi), [valid/ready](protocols.md#axi-valid-ready), [outstanding](protocols.md#axi-outstanding), [interleaving](protocols.md#axi-interleaving), [AXI-Lite](protocols.md#axil), [APB](protocols.md#apb) |

## 使用规则

- 系统复习从本页进入。
- 真实面试问法看 [真实问题表](../actual-interviews/questions.md#actual-question-table)。
- 刷题看 [面试题库](../question-bank/question-bank.md#qb-asic-frontend)。
- 项目相关技术点优先回链到 [Projects / HR](../projects-hr/README.md)。
