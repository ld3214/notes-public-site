# ASIC/DV Notebook

这是总入口。想快速复习时，从这里开始；想新增材料时，先放 [Inbox](inbox.md)，再归档到对应模块。

## 今天优先看

| 场景 | 入口 |
| --- | --- |
| 复盘真实面试 | [真实问题表](actual-interviews/questions.md#actual-question-table) / [复盘看板](actual-interviews/questions.md#review-board) |
| 刷高频题 | [面试题库](question-bank/question-bank.md#qb-systemverilog-uvm) |
| 刷笔试题 | [2026 数字 IC 公司卷整理](question-bank/question-bank.md#qb-written-exams-2026-csdn) |
| 系统补知识 | [知识库导航](knowledge-base/README.md) |
| 准备项目讲述 | [项目故事库](projects-hr/projects-and-behavioral.md#project-stories) |
| 准备投递公司 | [公司 Site 清单](company-sites.md#chengdu-sites) |
| 查术语 | [Glossary](glossary.md) |

## 复习路线

1. **真实问题优先**：先看 [P0 复盘项](actual-interviews/questions.md#actual-p0)，把被问过的问题讲顺。
2. **项目表达**：准备 [AXI DMA UVM](projects-hr/projects-and-behavioral.md#star-axi-dma)、[INT8 NPU](projects-hr/projects-and-behavioral.md#star-int8-npu-tapeout)、[OoO RISC-V](projects-hr/projects-and-behavioral.md#star-ooo-riscv) 三个主项目。
3. **UVM/DV 高频**：重点看 [Virtual Sequence](knowledge-base/systemverilog-uvm.md#uvm-virtual-sequence)、[RAL](knowledge-base/systemverilog-uvm.md#uvm-ral)、[Scoreboard](knowledge-base/systemverilog-uvm.md#uvm-scoreboard)、[VIP checker vs Scoreboard](knowledge-base/design-verification.md#vip-checker-scoreboard)、[Coverage](knowledge-base/design-verification.md#functional-coverage)。
4. **协议和 RTL 手撕**：看 [AXI outstanding/interleaving](knowledge-base/protocols.md#axi-outstanding)、[同步 FIFO](knowledge-base/asic-frontend.md#sync-fifo)、[find first one](knowledge-base/asic-frontend.md#find-first-one)、[one-hot](knowledge-base/asic-frontend.md#one-hot)。
5. **书籍整理速刷**：看 [数字逻辑与体系结构](knowledge-base/asic-frontend.md#book-dv-logic-architecture)、[验证基础](knowledge-base/design-verification.md#book-dv-fundamentals)、[SV/Verilog 语法清单](knowledge-base/systemverilog-uvm.md#book-sv-verilog-checklist)、[UVM 高频问法](knowledge-base/systemverilog-uvm.md#book-uvm-interview-checklist)。

## 主目录

| 模块 | 内容 | 入口 |
| --- | --- | --- |
| Actual Interviews | 自己真实被问过的问题，保留原始问法 | [actual-interviews/README.md](actual-interviews/README.md) |
| Knowledge Base | ASIC 前端、DV、SystemVerilog/UVM、协议正文 | [knowledge-base/README.md](knowledge-base/README.md) |
| Question Bank | 通用题库和网上面经，适合刷题 | [question-bank/README.md](question-bank/README.md) |
| Projects / HR | 项目 STAR、英文回答、行为面 | [projects-hr/README.md](projects-hr/README.md) |
| Company Sites | 投递公司和城市 site 清单，成都 site 单独标注 | [company-sites.md](company-sites.md) |
| Glossary | 缩写和术语速查 | [glossary.md](glossary.md) |
| Inbox | 未归档材料暂存 | [inbox.md](inbox.md) |

## 知识库

- [ASIC Frontend](knowledge-base/asic-frontend.md#asic-overview)
- [Design Verification](knowledge-base/design-verification.md#dv-overview)
- [SystemVerilog / UVM](knowledge-base/systemverilog-uvm.md#sv-overview)
- [Protocols](knowledge-base/protocols.md#protocol-overview)
- [Cracking Digital VLSI Verification Interview 书籍整理入口](knowledge-base/README.md#高频复习入口)

## 题库

- [笔试题：2026 数字 IC 公司卷整理](question-bank/question-bank.md#qb-written-exams-2026-csdn)
- [ASIC Frontend](question-bank/question-bank.md#qb-asic-frontend)
- [Design Verification](question-bank/question-bank.md#qb-design-verification)
- [SystemVerilog / UVM](question-bank/question-bank.md#qb-systemverilog-uvm)
- [Protocols](question-bank/question-bank.md#qb-protocols)
- [DV 网上面经知识点汇总](question-bank/dv-online-digest.md#common-directions)

## 项目

- [AXI DMA UVM 验证项目](projects-hr/projects-and-behavioral.md#star-axi-dma) / [详细技术实现](projects-hr/axi-dma-uvm-details.md)
- [INT8 NPU 流片项目](projects-hr/projects-and-behavioral.md#star-int8-npu-tapeout) / [详细技术实现](projects-hr/int8-npu-tapeout-details.md)
- [OoO RISC-V 处理器项目](projects-hr/projects-and-behavioral.md#star-ooo-riscv) / [详细技术实现](projects-hr/ooo-riscv-details.md)
- [DDR4 Controller APB + AXI VIP 验证项目](projects-hr/projects-and-behavioral.md#star-ddr4-controller-apb-axi-vip) / [详细技术实现](projects-hr/ddr4-controller-apb-axi-vip-details.md#ddr4-controller-apb-axi-vip-details) / [NODIMM 配置](projects-hr/ddr4-controller-apb-axi-vip-details.md#ddr4-nodimm-test-config) / [高级场景](projects-hr/ddr4-controller-apb-axi-vip-details.md#ddr4-advanced-test-scenarios) / [checker 分工](projects-hr/ddr4-controller-apb-axi-vip-details.md#ddr4-vip-checker-scope)
- [Ibex RV32IM UVM / 官方 DV Bring-up 项目](projects-hr/projects-and-behavioral.md#star-ibex-rv32im-uvm) / [详细技术实现](projects-hr/ibex-rv32im-uvm-details.md)
- [APB-UART UVM 验证环境](projects-hr/projects-and-behavioral.md#star-apb-uart)
- [Async FIFO UVM 验证](projects-hr/projects-and-behavioral.md#star-async-fifo)
- [TVIP-AXI Crossbar 验证](projects-hr/projects-and-behavioral.md#star-tvip-axi)

## 模板

- [知识点模板](templates/topic-note-template.md)
- [面试题模板](templates/interview-question-template.md)
- [项目故事模板](templates/project-story-template.md)
