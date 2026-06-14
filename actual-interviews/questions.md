# 真实问题索引

标签：`#actual-asked` `#interview-index`

## 页内目录

- [真实问题表](#actual-question-table)
- [复盘看板](#review-board)
- [P0](#actual-p0)
- [P1](#actual-p1)

---

<a id="actual-question-table"></a>
## 真实问题表

| 公司 | 轮次 | 原始问题 | 分类 | 优先级 | 复习链接 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| 紫光展锐 | 一面 | 讲项目 | 项目表达 | P0 | [项目故事库](../projects-hr/projects-and-behavioral.md#project-stories) | 待打磨 |
| 紫光展锐 | 一面 | memory compiler 设置 HVT | Memory / low power / timing | P0 | [Memory compiler / HVT](../knowledge-base/asic-frontend.md#memory-hvt) | 已建笔记 |
| 紫光展锐 | 一面 | scan chain | DFT | P0 | [Scan chain](../knowledge-base/asic-frontend.md#scan-chain) | 已建笔记 |
| 紫光展锐 | 一面 | 基础题 | RTL/ASIC 基础 | P1 | [ASIC 前端总览](../knowledge-base/asic-frontend.md#asic-overview) | 持续补充 |
| 紫光展锐 | 二面 HR | 本科情况 | HR / behavioral | P1 | [Behavioral 面试](../projects-hr/projects-and-behavioral.md#behavioral-interview) | 待整理 |
| 字节 | 一面 | 综合报告 | Synthesis | P0 | [综合报告和逻辑深度](../knowledge-base/asic-frontend.md#synthesis-report-logic-depth) | 已建笔记 |
| 字节 | 一面 | 逻辑深度 | Timing / micro-architecture | P0 | [综合报告和逻辑深度](../knowledge-base/asic-frontend.md#synthesis-report-logic-depth) | 已建笔记 |
| 字节 | 一面 | AXI | Protocol | P0 | [AXI](../knowledge-base/protocols.md#axi) | 待加深 |
| 字节 | 一面 | Interleaving | AXI advanced | P0 | [AXI interleaving](../knowledge-base/protocols.md#axi-interleaving) | 已建笔记 |
| 字节 | 一面 | Outstanding | AXI advanced | P0 | [AXI outstanding](../knowledge-base/protocols.md#axi-outstanding) | 已建笔记 |
| 字节 | 一面 | 手撕 find first one | RTL coding | P0 | [find first one](../knowledge-base/asic-frontend.md#find-first-one) | 已建笔记 |
| 字节 | 二面 | 详细拷打 OoO | Architecture | P0 | [OoO 基础](../knowledge-base/asic-frontend.md#ooo-basics) | 已建笔记 |
| 字节 | 二面 | 手撕同步 FIFO | RTL coding | P0 | [同步 FIFO](../knowledge-base/asic-frontend.md#sync-fifo) | 已建笔记 |
| 字节 | 二面 | 手撕检测 one-hot | RTL coding | P0 | [one-hot 检测](../knowledge-base/asic-frontend.md#one-hot) | 已建笔记 |
| 芯动科技 | 笔试 | task 找 first1 的位置，用 FSM 形式，四个状态 IDLE/SEARCH/DONE/SEARCHFAIL，enum 定义状态，每次调用 task 切换状态 | SystemVerilog coding / FSM / task | P0 | [task + FSM：find first 1](../knowledge-base/systemverilog-uvm.md#sv-task-fsm-find-first-one) | 已建笔记 |
| 芯动科技 | 笔试 | `fork/join_none` 并行计算二维数组 `bit q[M][N]` 每一行 1 的个数，并存到 array 里 | SystemVerilog concurrency / array | P0 | [fork/join_none 行并行统计](../knowledge-base/systemverilog-uvm.md#sv-fork-join-none-row-count) | 已建笔记 |
| 芯动科技 | 笔试 | valid-ready 握手：定义 transaction，task drive 发送，ready 随机拉高/拉低，monitor 收集，tb 发送 5 个 transaction `tx_q[5]` | SystemVerilog TB / protocol handshake | P0 | [valid-ready task TB](../knowledge-base/systemverilog-uvm.md#sv-valid-ready-task-tb) | 已建笔记 |
| 芯动科技 | 验证实习一面 | 怎么将信号驱动到 DUT？用 VIP 还是自己写 driver/BFM？ | UVM / driver / BFM / VIP | P0 | [芯动科技验证一面](../actual-interviews/asic.md#innosilicon-dv-intern) / [DMA 追问复盘](../projects-hr/axi-dma-uvm-details.md#axi-dma-innosilicon-followups) | 已整理 |
| 芯动科技 | 验证实习一面 | abort 注入怎么实现的？ | Error injection / abort / CSR | P0 | [芯动科技验证一面](../actual-interviews/asic.md#innosilicon-dv-intern) / [DMA 追问复盘](../projects-hr/axi-dma-uvm-details.md#axi-dma-innosilicon-followups) | 已整理 |
| 芯动科技 | 验证实习一面 | 整个 DMA 是多路一起搬运还是单独搬运？descriptor、burst、outstanding 怎么理解？ | AXI DMA / descriptor / outstanding | P0 | [芯动科技验证一面](../actual-interviews/asic.md#innosilicon-dv-intern) / [DMA 追问复盘](../projects-hr/axi-dma-uvm-details.md#axi-dma-innosilicon-followups) | 已整理 |
| 芯动科技 | 验证实习一面 | NPU 验证环境里 C model/DPI 怎么比对？检查粒度是什么？ | NPU verification / DPI C model | P1 | [INT8 NPU 项目](../projects-hr/projects-and-behavioral.md#star-int8-npu-tapeout) | 待继续打磨 |
| 芯动科技 | 验证实习一面 | CPU 项目有没有反汇编/commit log 之类的检查？ | CPU DV / log / reference check | P1 | [Ibex 验证项目](../projects-hr/projects-and-behavioral.md#star-ibex-rv32im-uvm) | 待继续打磨 |
| 芯动科技 | 验证实习一面 | 跨时钟域是怎么验证的？ | CDC verification | P1 | [CDC/RDC](../knowledge-base/asic-frontend.md#cdc-rdc) | 待继续打磨 |

<a id="review-board"></a>
## 复盘看板

<a id="actual-p0"></a>
### P0

- 项目表达。
- Memory compiler / HVT。
- Scan chain。
- Synthesis report / logic depth。
- AXI outstanding / interleaving。
- OoO。
- RTL coding：find first one、sync FIFO、one-hot。
- 芯动科技笔试 coding：task FSM、`fork/join_none`、valid-ready driver/monitor。
- 芯动科技验证一面：DUT 驱动路径、VIP vs 自写 BFM、DMA abort 注入、descriptor/outstanding 表达。

<a id="actual-p1"></a>
### P1

- 本科/经历解释。
- RTL/ASIC 基础题系统复盘。
- AXI 基础通道和 handshake 细节。
- NPU C model/DPI 比对粒度、CPU 验证 log/反汇编、CDC 验证表达。
