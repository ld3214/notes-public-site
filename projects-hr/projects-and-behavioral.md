[返回目录](../index.md)

# Projects / HR

## 目录

**项目故事**
- [项目故事库](#project-stories)
- [AXI DMA UVM 验证项目](#star-axi-dma)
  - [Regression debug 与 coverage closure](#axi-dma-regression-debug-coverage)
  - [芯动科技验证面试追问](axi-dma-uvm-details.md#axi-dma-innosilicon-followups)
- [INT8 NPU 流片项目](#star-int8-npu-tapeout)
- [OoO RISC-V 处理器项目](#star-ooo-riscv)
- [DDR4 Controller APB + AXI VIP 验证项目](#star-ddr4-controller-apb-axi-vip)
- [Ibex RV32IM UVM / 官方 DV Bring-up 项目](#star-ibex-rv32im-uvm)
- [APB-UART UVM 验证环境](#star-apb-uart)
- [Async FIFO UVM 验证](#star-async-fifo)
- [TVIP-AXI Crossbar 验证](#star-tvip-axi)

**面试准备**
- [STAR 模板](#star-template)
- [Behavioral 面试](#behavioral-interview)
- [英文回答模板](#english-answer-template)

---

<a id="project-stories"></a>
## 项目故事库

| 项目 | 技术点 | 可证明的能力 | 相关 STAR | 详细笔记 |
| --- | --- | --- | --- | --- |
| AXI DMA UVM 验证环境 | UVM env/agent/RAL/virtual seq/slave BFM/scoreboard | 独立搭建完整 UVM testbench，覆盖 AXI protocol、register model、error injection、coverage | [AXI DMA 项目故事](#star-axi-dma) | [详细技术实现](axi-dma-uvm-details.md) / [芯动追问](axi-dma-uvm-details.md#axi-dma-innosilicon-followups) |
| INT8 NPU 流片项目 | Verilog RTL / 4x4 MAC array / SRAM buffer / UVM + DPI C model / DC / STA / P&R | 从微架构、RTL、验证到综合后端收敛的端到端芯片项目经验 | [INT8 NPU 流片项目](#star-int8-npu-tapeout) | [详细技术实现](int8-npu-tapeout-details.md) |
| OoO RISC-V 处理器项目 | RV32IM / register renaming / ROB / RS / SQ / branch predictor / nonblocking cache / DC synthesis | 设计可综合乱序处理器，掌握 precise commit、branch recovery、memory ordering 和性能调试 | [OoO RISC-V 处理器项目](#star-ooo-riscv) | [详细技术实现](ooo-riscv-details.md) |
| DDR4 Controller APB + AXI VIP 验证项目 | DWC DDR54 / APB VIP / AXI4 VIP / DDR4 controller / HIF-DFI scoreboard | 能用 APB 配置 DDR controller 寄存器、用 AXI4 产生 DDR memory traffic，并解释 DDR4 controller 的多层检查链路 | [DDR4 Controller APB + AXI VIP 验证项目](#star-ddr4-controller-apb-axi-vip) | [详细技术实现](ddr4-controller-apb-axi-vip-details.md#ddr4-controller-apb-axi-vip-details) |
| Ibex RV32IM UVM / 官方 DV Bring-up 项目 | lowRISC Ibex / RV32IMC / simple_system / `.vmem` directed tests / UVM scaffold / scoreboard / coverage | 基于开源处理器搭建可运行 RTL baseline，并规划 instruction-level UVM 验证结构、激励发送和结果检查方法 | [Ibex RV32IM UVM 项目](#star-ibex-rv32im-uvm) | [详细技术实现](ibex-rv32im-uvm-details.md) |
| APB-UART UVM 验证环境 | APB slave / UART RX/TX / UVM env / coverage / error injection | 搭建 APB-UART 完整 UVM 验证环境，覆盖 config/parity/frame/overrun 等错误场景 | [APB-UART UVM 验证环境](#star-apb-uart) | - |
| Async FIFO UVM 验证 | Async FIFO / 格雷码指针 / SV OOP testbench / UVM env / cross-clock verification | 基于 UVM Primer 搭建异步 FIFO 双版本 testbench，掌握跨时钟验证方法 | [Async FIFO UVM 验证](#star-async-fifo) | - |
| TVIP-AXI (UVM AXI VIP) | AXI4 VIP / UVM agent / crossbar / multi-master contention / backpressure | 基于开源 AXI VIP 搭建 multi-master AXI crossbar 验证环境，掌握 AXI protocol 验证 | [TVIP-AXI Crossbar 验证](#star-tvip-axi) | - |

---

<a id="star-axi-dma"></a>
## AXI DMA UVM 验证项目

### 一句话概括

为一个 AXI DMA 控制器 RTL 从零搭建了完整 UVM 验证环境，覆盖 CSR 编程、数据搬移、burst 模式、backpressure、outstanding 压力测试、error injection 和 abort 等十余个测试场景，实现内存数据完整性 self-check。

### 项目关键参数

| 类别 | 参数 | 面试口径 |
| --- | --- | --- |
| AXI datapath | 32-bit address / 32-bit data / 8-bit ID | `AXI_ADDR_WIDTH=32`、`AXI_DATA_WIDTH=32`、`AXI_TXN_ID_WIDTH=8` |
| Burst length | CSR `max_burst[9:2]` 配置 AXI `ALEN`，默认 `8'hff` | 最大 256 beats；`8'h00` 表示 single-beat |
| Outstanding | read/write 各 8 笔 | `DMA_RD_TXN_BUFF=8`、`DMA_WR_TXN_BUFF=8`，scoreboard 覆盖 depth 1/2-3/4-7/8 |
| Descriptor / FIFO | 2 个 descriptor slot，stream FIFO depth 16 | `DMA_NUM_DESC=2`、`DMA_FIFO_DEPTH=16` |
| Corner cases | INCR/FIXED burst、unaligned、4KB boundary split、OKAY/SLVERR/DECERR | slave BFM + shared memory model + scoreboard 自检查 |

### Situation

DUT 是一个支持 descriptor-based、AXI-Lite CSR 编程、AXI4 master 读写、INCR/FIXED burst 模式的 DMA 控制器。DUT 有两路独立 DMA descriptor，支持最多 8 个 outstanding AXI transaction，并通过中断输出 done/error 状态。验证需要覆盖正常传输、边界条件（4KB boundary split、unaligned address）、错误响应、abort 和 outstanding 深度验证。

### Task

独立负责 UVM 验证环境搭建：
- 从读 spec 出发拆 verification plan。
- 设计 testbench 架构，选择合适的 agent、scoreboard、RAL 和 virtual sequence 模式。
- 实现所有测试用例并验证 coverage 目标。

### Action

**架构设计：**

```
test
  └── env
        ├── axil_agent (active)   ← AXI-Lite master，用于 CSR 编程和 RAL frontdoor
        ├── mem_agent (active)    ← AXI slave BFM，响应 DMA AXI master 读写
        ├── scoreboard            ← 数据完整性检查 + outstanding coverage
        └── virtual_sequencer     ← 持有 sub-sequencer + memory model + RAL + irq_vif
```

**关键技术选择和理由：**

1. **Slave BFM driver**：mem_agent 的 driver 不是 active master，而是一个 AXI slave，按 DMA master 请求从 shared memory model 读写数据，并支持可配置的 ready delay 和 response delay，用于 backpressure 和 outstanding 测试。

2. **`try_next_item()` error injection**：不需要 always-on background sequence。Test 通过向 mem_agent sequencer 发送带 SLVERR/DECERR 的 item，driver 非阻塞取用；无注入时 fallback 到 cfg.default_resp（AXI_OKAY）。这样 error 注入和正常流量解耦。

3. **Virtual sequencer 持有共享资源**：virtual sequencer 不仅连接两个 sub-sequencer，还持有 shared memory model、RAL block 和 IRQ virtual interface，让 virtual sequence 的 body 可以直接调用 `p_sequencer.mem.fill_incrementing()`、RAL frontdoor `write/read()` 和 `p_sequencer.irq_vif` 等资源，无需在 sequence 里硬编码 env 层级。

4. **RAL + explicit predictor**：关闭 auto prediction，使用 `uvm_reg_predictor` 连接 axil monitor 的 analysis port，保证每次真实 bus transaction 都更新 mirror value，而不是依赖 sequence 调用时的隐式更新。

5. **Scoreboard 内嵌 coverage**：在 scoreboard 的 `write()` 方法（接收 monitor transaction）中同步采样 outstanding coverage（read/write 方向 × depth bins 的 cross coverage），实现 coverage 和 checker 统一在一处，避免遗漏。

6. **`fork/join_any + disable fork`**：IRQ 等待函数同时跑"等中断"和"timeout"两个分支，任意一个结束后 kill 掉另一个，防止仿真挂死。

### Scoreboard 检查逻辑（UVM DMA project 补充）

1. **CSR 检查链路（镜像比对）**

- Scoreboard 通过 AXI-Lite monitor 收到已完成 transaction，并据此维护本地镜像状态（control 和 descriptor 相关字段）。
- 写 transaction 到来时更新镜像（含 WSTRB 粒度合并）；读 transaction 到来时按镜像计算 expected readback，再与实际读值比较。
- 对 `DMA_STATUS` 和 `DMA_ERROR_STATS` 还会做语义检查（done/error、error_source、error_trigger 一致性）。
- 这条链路是 monitor 驱动的镜像检查，不依赖 driver 内部变量直读。

2. **Memory 检查链路（source/dst 一致性）**

- 测试先在 shared memory model 预置 source 数据（工程里多数用可预期的 incrementing pattern，便于 debug）。
- DMA start（enable 上升沿）时，scoreboard 生成 expected copy：按 descriptor + rd/wr mode 计算每个待检查 dst byte 的期望值。
- DMA complete（enable 下降沿）时，scoreboard 从 memory model 读取 dst byte，逐字节比较 expected vs got。
- 关键点：`mem.read_byte()` 是直接读 memory model（不再发总线事务）；但该 model 的内容由 AXI memory slave BFM 在真实 AXI 握手过程中更新/提供，因此仍然间接反映总线行为。

3. **错误路径与压力路径检查**

- 默认把非 `AXI_OKAY` 响应视为错误；在 error-injection 测试中可打开 `allow_error_responses`，改为检查 STATUS/ERROR_STATS 并丢弃 pending copy check。
- Scoreboard 同时统计 read/write outstanding 峰值，并采样 outstanding coverage；压力测试可要求峰值达到配置上限。

### Error case 测试如何检查（按用例）

| Test | 注入方式 | 主要检查点 | Pass 判据 |
| --- | --- | --- | --- |
| `error_response_test` | `default_read_resp = AXI_SLVERR` | `wait_error` 中断、`DMA_STATUS`、`DMA_ERROR_STATS`、scoreboard 记录 read error | 触发 error 中断；STATUS.error=1；ERROR_STATS.error_trig=1；error_src 指向 read side |
| `decerr_response_test` | `default_read_resp = AXI_DECERR` | 同上（read 方向） | 同上（只是在 read 侧注入 DECERR） |
| `write_error_response_test` | `default_write_resp = AXI_SLVERR` | `wait_error` 中断、`DMA_STATUS`、`DMA_ERROR_STATS`、scoreboard 记录 write error | 触发 error 中断；STATUS.error=1；ERROR_STATS.error_trig=1；error_src 指向 write side |
| `write_decerr_response_test` | `default_write_resp = AXI_DECERR` | 同上（write 方向） | 同上（只是在 write 侧注入 DECERR） |
| `invalid_cfg_test` | 配置 `desc.valid=1` 且 `num_bytes=0` 后 start | `wait_error`、STATUS done/error 组合、ERROR_STATS 的 config error 语义 | 触发 error 中断；STATUS.done=1 且 STATUS.error=1；ERROR_STATS.error_trig=1 且 error_type=configuration |

补充说明：

- 这些 error test 的核心不是检查 dst 数据是否和 src 一致，而是检查错误是否被 DUT 正确上报到 interrupt 和 CSR。
- 在允许 error response 的测试中，scoreboard 会在看到非 OKAY 后丢弃 pending copy check，避免把 error path 当作普通 copy mismatch 误报。
- 错误方向由 scoreboard 在 memory monitor transaction 中记录（read 或 write），再用于 ERROR_STATS.error_src 语义比对。

**测试用例覆盖：**

| 场景 | 方法 |
| --- | --- |
| CSR 读写正确性 | RAL frontdoor write/read + 直接 AXI-Lite transaction |
| Descriptor 传输 | desc0 数据搬移 self-check；desc1 做 CSR/RAL write/readback 覆盖，并将 desc1-only DMA completion 记录为 known issue |
| Burst sweep（max_burst 0~255） | 循环改参数，验证不同 burst 长度下数据正确 |
| Unaligned address（offset 1/2/3） | 非字对齐 src/dst，验证 WSTRB 和数据对齐处理 |
| 4KB boundary split | src = 0x0ff0，跨 boundary 的 burst 分割 |
| Backpressure | 随机化 ready/response delay，验证 DUT 对 backpressure 的容忍 |
| Outstanding stress | min burst（每次 1 beat）产生多请求压力；delayed response corner 单独记录为 known issue |
| FIXED burst mode | AXI FIXED burst，验证 DUT 对非 INCR 模式的处理 |
| Error injection | read/write SLVERR 和 DECERR 注入，验证 STATUS.error 和 ERROR_STATS 寄存器正确置位 |
| Abort | 传输进行中写 abort bit，验证 DMA 能干净停止 |
| Random/high-address toggle | random mixed transfer 覆盖 burst/size/address 组合；high address sweep 补 AXI address 和 descriptor toggle |

### Result

- 20 个 regression test 全部跑通，最新 merged report 中 `UVM_ERROR/UVM_FATAL = 0`。
- RAL/AXI-Lite CSR frontdoor 访问稳定，AXI memory slave BFM 支持 OKAY/SLVERR/DECERR response、ready delay、response delay 和 backpressure 配置。
- 最新 Questa HTML merged coverage：Total `91.98%`，statement `96.36%`，branch `96.25%`，FEC condition `79.33%`，toggle `79.95%`，covergroup/assertion `100%`。
- code-only filtered coverage 从 `85.79%` 提升到 `88.44%`；主要提升来自 descriptor CSR pattern sweep 和 high-address toggle directed test。
- 剩余 coverage hole 主要是 defensive/error/协议 stall 组合，不属于普通数据搬移场景的功能失败，需要进一步按“补 test / 记录 known issue / 合理 waiver”分类处理。

### 面试版 60 秒回答（中文）

我做的是一个 AXI DMA 控制器的 UVM 验证项目。DUT 通过 AXI-Lite 做 CSR 配置，通过 AXI4 master 访问 memory，当前数据通路是 32-bit address、32-bit data、8-bit ID；burst length 由 CSR 里的 `max_burst` 配置，最大可以到 256 beats，read/write outstanding window 各 8 笔。我从零搭了 UVM 环境，包括 AXI-Lite master agent、RAL model、AXI memory slave BFM、shared memory model、scoreboard 和 virtual sequencer。scoreboard 会根据 descriptor 从 memory model 取 expected data，DMA 完成后逐 byte 比较 destination，同时统计 outstanding depth。测试上我覆盖了 CSR 读写、descriptor 搬运、burst sweep、backpressure、unaligned address、4KB boundary split、FIXED burst、outstanding stress、SLVERR/DECERR error injection 和 abort。error injection 里我用 `try_next_item()` 让 slave BFM 可以非阻塞地接收 test 注入的 error response；等待 interrupt 的地方用 `fork/join_any` 加 timeout，避免 regression 卡死。最后 20 个 regression test 跑通，merged coverage total 到 `91.98%`，covergroup/assertion 达到 `100%`。

### 面试版 60 秒回答（英文）

I built a complete UVM verification environment for an AXI DMA controller. The testbench includes an AXI-Lite master agent for CSR programming through a RAL model, an AXI memory slave BFM that responds to DMA read/write requests using a shared memory model, and a scoreboard that checks data integrity and tracks AXI outstanding depth. I used a virtual sequencer to centralize access to the sub-sequencers, memory model, RAL model, and IRQ interface, which kept the virtual sequences clean and concise. For error injection, I used `try_next_item()` so the driver could non-blockingly accept error responses from a test sequence without needing a permanent background sequence. For timeout protection in IRQ waiting tasks, I used `fork/join_any` plus `disable fork`. The environment covered more than ten test scenarios including burst sweep, backpressure, unaligned transfers, 4KB boundary splits, outstanding stress, and error/abort paths.

> **详细技术实现笔记**: [axi-dma-uvm-details.md](axi-dma-uvm-details.md) — 包含 [RAL / memory model / scoreboard 深入实现](axi-dma-uvm-details.md#axi-dma-ral-mem-scoreboard)、UVM组件代码、测试用例实现细节、覆盖率模型设计、仿真脚本、调试技巧和面试追问准备。

<a id="axi-dma-regression-debug-coverage"></a>
### Regression debug 与 coverage closure 记录

**Bring-up 背景**

AXI DMA UVM 环境 bring-up 时，regression 一开始出现多个 `UVM_FATAL` timeout。定位后发现问题不是 RAL/AXI-Lite CSR access 卡住，而是 DMA start 之后等不到 `done/error` interrupt。

**Fatal 修复记录**

| 现象 | 定位 | 处理 |
| --- | --- | --- |
| RAL CSR write/read 曾经卡住 | AXI-Lite driver 没有明确 request/response 闭环 | RAL frontdoor 统一访问 CSR，driver 在完成 B/R response 后 `item_done()`，adapter 用完成后的 item 返回 status |
| `multi_desc_transfer_test` timeout | desc0 copy OK，desc1-only DMA 不产生完成 interrupt | regression 中保留 desc1 CSR/RAL readback 覆盖，不把 desc1-only DMA 当作 passing path |
| `fixed_mode_transfer_test` timeout | 1024B fixed/fixed 超过 AXI fixed burst 合理刺激范围 | 改为 16-beat fixed burst，覆盖 fixed mode 但避免非法/不稳定长 fixed transfer |
| `backpressure_transfer_test` timeout | ready delay + 大 transfer 容易填满小 FIFO | 缩小 transfer size，并降低 ready delay |
| `outstanding_stress_test` timeout | response delay 压住 read/write drain，DUT 长时间不前进 | 改成零响应延迟下的 single-beat 多请求压力，保留 outstanding 行为覆盖 |

**UVM/testbench 修复记录**

| 问题 | Root cause | 修复 |
| --- | --- | --- |
| 普通 sequence 和 virtual sequence 边界不清 | virtual sequence 直接承担过多 pin-level transaction 生成，agent sequencer/driver 的职责不清晰 | 普通 sequence 放在对应 agent sequencer 上产生 transaction；virtual sequence 只做系统级调度、RAL access、reset/interrupt/error 场景协调 |
| CSR sequence 过复杂且容易和 RAL mirror 脱节 | 已经有 RAL，却还手写大量 CSR transaction 细节 | CSR 编程统一改为 RAL frontdoor；通过 adapter/predictor 保证 bus transaction 和 mirror 同步 |
| AXI-Lite/RAL 访问曾经卡住 | write/read response 没有形成完整 request-response 闭环 | AXI-Lite driver 对每次 write/read 都返回 response item，RAL adapter 用完成后的 item 更新 status/data |
| AXI memory slave sequence 误用为必须后台流量 | memory agent 是 slave BFM，应响应 DUT master 请求，而不是主动持续发 pin-level item | driver 使用 `try_next_item()` 非阻塞接收可选 error override；无 override 时按 cfg 默认返回 OKAY |
| error test 被 scoreboard 当成失败 | scoreboard 默认把非 OKAY response 都报错 | error response test 中打开 `allow_error_responses`，并分别覆盖 read/write SLVERR 与 DECERR |

**RTL bug 修复记录（2026-05-28）**

| Bug | Root cause | RTL fix |
| --- | --- | --- |
| DMA 在非法配置下只 `done`，没有 `error` | `dma_fsm` 只检查是否存在 enabled 且 `num_bytes != 0` 的 descriptor，没有把 enabled zero-byte descriptor 视为 configuration error | 在 `dma_fsm.sv` 增加 configuration error latch；enabled descriptor 的 `num_bytes == 0` 时进入 DONE 并置 `dma_status.error` / `dma_error_stats` |
| `dma_error_stats.error_type` 编码和 CSR 文档相反 | `dma_pkg.svh` 中 enum 顺序是 `CFG=0, OPE=1`，但寄存器说明为 `0=Operation, 1=Configuration` | 调整 enum 为 `DMA_ERR_OPE=0, DMA_ERR_CFG=1` |
| Questa 编译报 `DMA_PROGRESS_TIMEOUT is undefined` | 新增宏只放在 `dma_pkg.svh`，但 Questa filelist 按独立 compilation unit 编译模块，`dma_fsm.sv` 看不到该宏 | 在 `sim/filelists/dut.f` 和 `dut_core_cov.f` 补 `+define+DMA_PROGRESS_TIMEOUT=16383` |
| 内部 FIFO overflow/underflow 不会上报到 CSR | `dma_axi_if` 的 tracking FIFO 和 `dma_func_wrapper` 的主 data FIFO 的 `error_o()` 都悬空 | 将内部 FIFO `error_o` 汇总到 `axi_dma_err` / `dma_error`，并按 read/write 侧设置 `error_src` |
| 首个错误可能被后续错误覆盖 | `err_lock` 只在错误发生当拍置位，后续无错误时又释放 | 将 error latch 保护改为“已有 `dma_error_ff.valid` 后不再覆盖”，直到 clear |
| RUN 状态无进展时 testbench 只能等到 timeout | FSM 只等待 `pending_desc || axi_pend_txn` 变低，没有 progress watchdog；若 AXI/FIFO 状态机卡住，不会产生 done/error | 在 `dma_axi_if` 输出 AXI progress pulse，在 `dma_fsm` 增加可配置 `DMA_PROGRESS_TIMEOUT` watchdog，超时后报 operation error |
| clear 后内部 AXI tracking FIFO 可能残留旧状态 | `dma_axi_if` 内部 request/error FIFO 的 `clear_i` 固定为 0 | 将这些 FIFO 接到 `clear_dma_i`，并在 clear 时复位 pending counter、write lock、beat counter 和 AW sticky 状态 |

**Coverage 分析记录**

最新 merged coverage 显示：普通功能路径已经被覆盖得比较充分，没到 100% 主要不是因为 regression 失败，而是 FEC condition 和 toggle 中还存在很多防御性、结构性或极窄时序组合。

| 指标 | 最新结果 | 分析 |
| --- | --- | --- |
| Total coverage | `91.98%` | HTML merged total，包含 covergroup/assertion/code coverage |
| Code-only filtered | `88.44%` | 只看 RTL file 的 code coverage，因此低于 HTML total |
| Statement | `96.36%` | 普通执行路径基本覆盖，剩余多为异常/防御性路径 |
| Branch | `96.25%` | 分支覆盖较高，说明主要状态和控制路径已 hit |
| FEC condition | `79.33%` | 最大短板，集中在 progress timeout、FIFO full、abort+full、clear+valid stall 等组合 |
| Toggle | `79.95%` | 已通过 CSR pattern sweep 明显提升，但仍有 tie-off/结构常量/少见 descriptor bit 未完全翻转 |
| Covergroup/assertion | `100%` | 当前功能覆盖模型和 AXI assertion pass coverage 已关闭 |

| 模块 | 观察 |
| --- | --- |
| `dma_axi_if.sv` | 剩余 FEC hole 包括 `err_lock_ff` 与 `dma_error_ff.valid` 的互斥组合、`rvalid && fifo full && abort`、`rlast && !rready`，以及 clear 时 AR/AW/W valid 被 ready stall 的清理路径 |
| `dma_fsm.sv` | `progress_timeout`、`local_error_ff.valid` 在 RUN 中触发的组合仍未命中；zero-byte descriptor 现在在 CFG 阶段直接报错，因此 RUN 阶段再次看到 `num_bytes==0` 的条件属于较难/近似不可达组合 |
| `dma_streamer.sv` | 4KB wrap/overflow 检测、`last_txn_ff`、`dma_req_ff.valid` 的少见组合未完全 hit，需要更刻意的 boundary/debug test |
| `dma_fifo.sv` | FIFO full/overflow 条件没有完全 hit；普通合法传输不会故意写满内部 FIFO 后继续写 |
| AXI sideband/tie-off | AXI ID/user/prot/cache/qos/region、固定 size、低位对齐地址等结构性信号很多是常量，不应该靠随机 test 硬翻转 |

**Coverage 补充记录（2026-05-28）**

| 补充项 | 做法 | 作用 |
| --- | --- | --- |
| `high_addr_toggle_test` | 对 desc0/desc1 交替使用高位 source/destination address，并切换 INCR/FIXED mode | 补 AXI address 高位、descriptor index 和 mode toggle |
| `decerr_response_test` / `write_decerr_response_test` | 在已有 SLVERR 基础上增加 read/write DECERR response | 补 AXI response type 和错误路径覆盖 |
| `random_mixed_transfer_test` | 通过 constrained random sweep address、num_bytes、max_burst | 扩展正常传输空间，避免只有 directed case |
| `csr_all_regs_test` descriptor pattern sweep | idle 状态下通过 RAL/CSR 对两个 descriptor 写 `ffff_ffff -> 0 -> 5555_5555 -> aaaa_aaaa -> 0` | 补 `dma_desc_i`、wrapper、streamer、FSM 输入向量 toggle；这是合法 CSR 路径，不是关闭 toggle |
| Toggle waiver | 对 AXI optional sideband、tie-off、高位未使用/固定对齐信号做有理由的 waiver | 不关闭全局 toggle，只忽略结构固定且不可达的 bins |

**Coverage closure 方法**

1. 先区分 **真实设计覆盖率** 和 **工具噪声**：third-party/generated code、tie-off、高位未使用 bus 应该用 waiver 或单独报告处理。
2. 对手写 DMA core 看 statement/branch/condition；toggle coverage 只作为后期补充目标。
3. 对真实 hole 分类：可达但缺 test 就补 directed/random test；约束/配置挡住就放宽 constraint 或增加配置 sweep；当前 RTL 不支持的 corner 记录为 known issue；结构不可达则 waive/exclude 并写清楚 reason。
4. 不为了追 100% 人工制造不符合 spec 的非法 stimulus；如果需要覆盖 defensive path，应单独放到 debug/error regression，并让 scoreboard 明确知道这是 expected error。
5. 默认 regression 应先保证稳定通过；known-fail corner 单独保留 debug test 或 issue。

**面试回答**

中文：在这个 AXI DMA 项目里，我遇到过 regression fatal 和 coverage 偏低的问题。我先从 log 找 first fatal，确认 RAL/AXI-Lite CSR access 都已经返回 `UVM_IS_OK`，真正的问题是 DMA start 后部分场景等不到 interrupt。然后我修了 RTL 的非法配置 error、内部 FIFO error 汇总、error latch、clear 清理和 progress watchdog 等问题，让 20 个 regression test 全部通过。Coverage 方面，最新 merged total 到 `91.98%`，statement/branch 都在 `96%+`，covergroup/assertion 是 `100%`；剩下主要是 FEC condition 和 toggle。我没有简单关闭 toggle，而是增加 high-address test、DECERR test、random mixed test，并在 `csr_all_regs_test` 里通过 RAL/CSR 写 descriptor pattern，code-only coverage 从 `85.79%` 提到 `88.44%`。最后对 AXI optional sideband、tie-off 和不可达 defensive path 做 waiver/known issue 分类，而不是为了追 100% 去制造不符合 spec 的场景。

English: In this AXI DMA project, I debugged both regression fatal issues and low coverage. I first located the first timeout in the log and confirmed that RAL frontdoor CSR accesses were completing successfully, so the issue was not the AXI-Lite path but DMA completion. I fixed RTL issues such as invalid-configuration error reporting, internal FIFO error propagation, error latching, clear cleanup, and a progress watchdog. After that, all 20 regression tests passed with no UVM errors or fatals. For coverage, the latest merged total reached 91.98%, with statement and branch coverage above 96% and covergroups/assertions at 100%. The remaining holes were mainly FEC conditions and toggle bins. Instead of disabling toggle coverage globally, I added high-address, DECERR, random mixed, and CSR descriptor pattern-sweep tests, which improved code-only coverage from 85.79% to 88.44%. For optional AXI sideband signals, tied-off fields, and structurally unreachable defensive paths, I documented waiver or known-issue reasoning rather than forcing illegal stimulus just to reach 100%.

### 可追问点

- 技术细节：slave BFM 各 channel 如何并行、semaphore 如何保护 `try_next_item()`、RAL predictor 如何接线
- 难点：AXI slave BFM 要正确计算 beat address（INCR 递增、FIXED 不变），WLAST 要和 AWLEN 对应
- Trade-off：auto predict 还是 explicit predict、coverage 放在 scoreboard 还是独立 subscriber
- 如果重做：加 SVA 对 valid/ready handshake 做协议断言、加 backdoor access 加速初始化

---

<a id="star-int8-npu-tapeout"></a>
## INT8 NPU 流片项目

标签：`#project` `#npu` `#cnn` `#rtl` `#uvm` `#dpi` `#cmodel` `#tapeout` `#dc` `#apr` `#sta`

### 一句话概括

基于 Verilog 设计并验证一个面向 CNN 推理加速的 INT8 量化 NPU，从 RTL 微架构、UVM + DPI C model 验证、代码覆盖率收敛，到 DC 综合、STA、P&R、后仿频率收敛和 2026.05 流片完成，覆盖了 ASIC 前端到后端交付的完整链路。

### 项目关键参数

| 类别 | 参数 | 面试口径 |
| --- | --- | --- |
| 指令格式 | 48-bit instruction，4-bit opcode | 支持 CONV、POOL、ADD、STORE、LOAD_ACT、LOAD_WT、LOAD_BS、AVG_POOL、CLASSIFIER 9 类 opcode |
| SRAM | activation SRAM 32-bit x 1024，weight SRAM 32-bit x 256 | activation 约 4 KB，weight 约 1 KB；TB 还有更大的文件数组用于 preload |
| 计算阵列 | 4 个 `conv_unit_single` lane | 每 lane 是 4-input INT8 MAC tree + 4 个 32-bit accumulator，满载约 16 个 INT8 multiply/cycle |
| 卷积参数 | kernel/core dim 2 bit，image dim log 3 bit，channel field 5 bit，stride 1 bit | channel 按 channels/4 编码，最多 128 channels；stride 支持 1/2 |
| 时钟口径 | 外部接口 10 MHz，内部目标 200 MHz；当前 RTL/qsim testbench core clock 是 100 MHz | 面试时把 tapeout 目标频率和本地仿真 clock 区分开 |

### 工程路径

| 类型 | 路径 | 用途 |
| --- | --- | --- |
| Core 验证环境 | `C:\Users\28724\Desktop\IC_EDA_Lite（精简版50G）\virtual\IC_EDA_Lite\share\NPU_cmodel` | RTL、UVM testbench、DPI/C model、Python golden model、Questa 仿真 |
| 完整流片工程 | `C:\Users\28724\Desktop\master\project\6350_NPU_final` | RTL、DC、PrimeTime、Innovus APR、memory compiler、post-layout simulation、stream out |

验证环境目录要点：

- `rtl/`：NPU/TPU RTL source。
- `uvm/`：UVM 验证环境和 Questa simulation setup。
- `uvm/cmodel/`：DPI 对接的 C model collateral。
- `python/`：instruction generation 和 golden-model utilities。
- `qsim_rtl/`：参考 RTL testbench flow。

完整工程目录要点：

- `dc/`：逻辑综合，含各模块 DC 脚本与 report。
- `pt_dc/`、`pt_apr/`：综合后和布局布线后的 STA。
- `innovus3/`：APR/P&R。
- `memory_compiler/`：SRAM macro 生成。
- `qsim_dc/`、`qsim_apr/`、`qsim_apr_chip/`：不同阶段 gate-level/post-layout 仿真。
- `stream_out/`：最终版图输出相关文件。

### Situation

项目目标是实现一个面向 CNN inference 的 INT8 量化 NPU。外部读写接口工作在 10 MHz，内部计算频率目标为 200 MHz。设计需要支持 load/store、可配置卷积、最大池化、均值池化、classifier 等 9 类指令，并通过两条无数据相关指令并行发射提高吞吐率。

### Task

负责/参与 RTL 设计、core 级 UVM 验证、C model 对接、覆盖率和回归闭环，以及后续综合、STA、P&R 约束收敛相关工作。项目需要在面积约束内完成时序收敛，并最终达到 tapeout 条件。

### Action

**1. NPU 指令与控制流**

- 设计面向 CNN 推理的 instruction flow，支持 load/store、convolution、max pooling、average pooling、classifier 等 9 类指令。
- 支持两条无数据相关指令并行发射，提升 load/store 与 compute 之间的重叠度。
- 处理外部 10 MHz 读写和内部 200 MHz 计算域之间的吞吐匹配与控制节奏。

**2. 4x4 MAC 阵列与 INT8 计算**

- 搭建 4x4 MAC 阵列，每周期并行完成 16 次 INT8 multiply-accumulate。
- 在 accumulator 路径中集成 bias addition、ReLU activation 和 max-pooling compare logic。
- 理论峰值性能达到 6.4 GOPS，单张输入图片端到端分类延迟约 3 ms。

**3. 片上存储层次与访问仲裁**

- 设计 16 KB unified buffer 和 1 KB weight SRAM 作为片上存储层次。
- 处理外部数据写入、内部计算读取、权重读取和结果写回之间的访问仲裁。
- 通过 buffer reuse 和 SRAM arbitration 缓解 feature map、weight 和 intermediate result 之间的带宽冲突。

**4. 卷积窗口地址映射与多 bank 拼接**

- 实现二维 feature map 坐标到 SRAM physical address 的映射。
- 设计多 bank 数据拼接逻辑，把不同 bank 中的数据对齐成 MAC array 需要的窗口输入。
- 支持 boundary padding、invalid pixel mask 和 window data alignment，保证不同卷积窗口位置下输入数据正确送入 MAC 阵列。

**5. UVM + DPI C model 验证平台**

- 基于 UVM 搭建 core 级验证环境，通过 driver/monitor/scoreboard 完成 instruction-level 和 result-level checking。
- 通过 DPI 接口对接 C model，使用 C model 作为 golden reference，对 RTL 计算结果做 end-to-end compare。
- 建立 coverage collection 和 regression 闭环，代码覆盖率收敛至 90%+。
- 定位并修复 CSA 加法链路和 input buffer 相关 bug。

**6. 综合、STA、P&R 和流片收敛**

- 完成 RTL design、functional simulation、logic synthesis、STA 和 P&R constraint closure。
- 后仿最高可收敛频率约 214 MHz，满足 200 MHz 内部计算频率目标。
- 在 1.31 mm x 1.11 mm chip area constraint 下完成设计，并于 2026.05 完成流片。

### Result

- 支持 9 类 NPU 指令，包含可配置 convolution、pooling、classifier、load/store 等 CNN inference 关键操作。
- 4x4 MAC array 每周期 16 次 INT8 乘加，理论峰值性能 6.4 GOPS。
- 单张输入图片端到端分类延迟约 3 ms。
- UVM + DPI C model 验证闭环跑通，代码覆盖率收敛至 90%+。
- 修复 CSA adder path 和 input buffer bug。
- 后仿频率约 214 MHz，在 1.31 mm x 1.11 mm 面积约束下完成 tapeout。

### 面试版 2 分钟回答（中文）

我做过一个 INT8 量化 NPU 流片项目，目标是加速 CNN inference。这个 NPU 外部读写频率是 10 MHz，内部计算目标是 200 MHz，支持 load/store、可配置卷积、max pooling、average pooling、classifier 等 9 类指令，并支持两条没有数据相关的指令并行发射来提高吞吐率。

在计算架构上，我搭建了 4x4 MAC 阵列，每周期可以并行做 16 次 INT8 乘加，并在 accumulator 中集成 bias addition、ReLU 和 max pooling compare logic，理论峰值大约 6.4 GOPS，单张图片端到端分类延迟约 3 ms。存储方面，我设计了 16 KB unified buffer 和 1 KB weight SRAM，并处理外部写入、内部计算读取和结果写回之间的仲裁，缓解 feature map、weight 和 intermediate result 之间的带宽冲突。

比较有挑战的是卷积窗口数据准备。我实现了二维 feature map 坐标到 SRAM 物理地址的映射，以及多 bank 数据拼接逻辑，支持 padding、invalid pixel mask 和窗口数据对齐，保证不同卷积窗口位置下的数据都能正确送入 MAC 阵列。

验证方面，我基于 UVM 搭建了 core 级验证平台，通过 DPI 接口对接 C model，把 C model 作为 golden reference 做指令级和结果级比对，并建立 coverage 和 regression 闭环。最后代码覆盖率收敛到 90% 以上，也定位并修复了 CSA 加法链路和 input buffer 的 bug。项目后续完成了 DC 综合、STA、P&R 和后仿收敛，后仿最高频率约 214 MHz，并在 2026 年 5 月完成流片。

### 面试版 60 秒回答（英文）

I worked on an INT8 quantized NPU tapeout project for CNN inference. The design runs external read/write traffic at 10 MHz and the internal compute core at 200 MHz. It supports nine instruction types, including load/store, configurable convolution, max pooling, average pooling, and classifier operations, and it can issue two independent instructions in parallel to improve throughput.

Architecturally, I built a 4-by-4 MAC array that performs 16 INT8 multiply-accumulate operations per cycle. The accumulator path also integrates bias addition, ReLU activation, and max-pooling comparison logic. The peak performance is about 6.4 GOPS, and the end-to-end latency for classifying one input image is around 3 ms. I also designed the on-chip memory hierarchy with a 16 KB unified buffer and a 1 KB weight SRAM, including arbitration between external writes, internal compute reads, and result writeback.

For verification, I built a UVM environment and connected a C model through DPI as the golden reference. The scoreboard performs both instruction-level and result-level comparison, and the regression flow closed code coverage to over 90%. We found and fixed bugs in the CSA adder path and input buffer. The project completed RTL simulation, synthesis, STA, P&R, post-layout timing closure at around 214 MHz, and taped out in May 2026.

> **详细技术实现笔记**: [int8-npu-tapeout-details.md](int8-npu-tapeout-details.md) — 包含完整 RTL 设计代码、UVM+DPI 验证环境、Python golden model、DC/STA/P&R 后端脚本、性能指标分析和调试经验。

### 可追问点

- 微架构：为什么选择 4x4 MAC array，INT8 accumulator bit-width 如何考虑，bias/ReLU/pooling 放在 accumulator 路径的 trade-off。
- 指令并行发射：如何判断两条指令没有数据相关，遇到 load/store 和 compute 冲突时如何 stall 或仲裁。
- 存储系统：16 KB unified buffer 和 1 KB weight SRAM 如何分工，bank conflict 如何处理，读写仲裁优先级怎么定。
- 卷积窗口：feature map 二维坐标如何映射到 SRAM address，padding 和 invalid pixel mask 如何影响 MAC 输入。
- 验证：DPI C model 如何和 UVM scoreboard 对接，instruction-level compare 和 result-level compare 分别检查什么。
- Debug：CSA 加法链路 bug 和 input buffer bug 的现象、定位方法、修复方式。
- 后端：DC/STA/P&R 中最关键的 timing path 是什么，214 MHz 后仿频率如何判断收敛。

### 可直接放简历的 bullets

- Designed an INT8 quantized CNN inference NPU in Verilog with 9 instruction types, dual-issue support for independent instructions, a 4x4 MAC array, 16 KB unified buffer, and 1 KB weight SRAM.
- Implemented convolution window address mapping, multi-bank data alignment, padding mask handling, and SRAM arbitration for feature maps, weights, and intermediate results.
- Built a UVM verification environment with DPI-connected C model golden reference for instruction-level and result-level checking; closed code coverage to 90%+ and fixed CSA adder path and input buffer bugs.
- Completed RTL simulation, synthesis, STA, P&R, and post-layout timing closure; achieved about 214 MHz post-layout frequency under a 1.31 mm x 1.11 mm area constraint and taped out in May 2026.

---

<a id="star-ooo-riscv"></a>
## OoO RISC-V 处理器项目

标签：`#project` `#ooo` `#riscv` `#rtl` `#microarchitecture` `#rob` `#rs` `#sq` `#cache` `#synthesis`

### 一句话概括

实现一个可综合的 3-wide out-of-order RV32IM 处理器，包含 register renaming、freelist/map table、32-entry ROB、16-entry reservation station、store queue、branch predictor、I/D cache、MSHR 和 precise branch recovery，并通过 program-level regression 与 Design Compiler synthesis flow 做验证和收敛。

### 项目关键参数

| 类别 | 参数 | 面试口径 |
| --- | --- | --- |
| ISA / datapath | RV32IM，`XLEN=32` | 32-bit datapath，项目重点是 OoO microarchitecture |
| Width | 3-wide dispatch / complete / retire | ROB head 最多每周期按序 retire 3 条 |
| Rename / ROB / RS | 64 physical registers，32-entry ROB，16-entry RS | `PR=6`、`ROBW=32`、`RSW=16` |
| Memory ordering | store queue 8 entries，D-cache MSHR 8 entries | `LSQ=3`、`MHSRS_W=8`，支持 cache miss latency hiding 和 load/store dependency check |
| Execution resources | 8 个 FU | 3 ALU + 2 load/store + 2 multiplier + 1 branch；per-FU issue FIFO depth 32 |
| Memory model | 64 KiB unified memory，15 memory tags，约 100 ns latency | `MEM_SIZE_IN_BYTES=64*1024`、`NUM_MEM_TAGS=15` |

### 工程路径

| 类型 | 路径 | 用途 |
| --- | --- | --- |
| OoO 工程 | `C:\Users\28724\Desktop\master\project\OoO` | RTL、testbench、program regression、synthesis report、final report |
| 顶层结构图 | `pipeline_flow.md` | 记录 frontend、rename、schedule、execute、commit 和 recovery 数据流 |
| 详细笔记 | `projects-hr/ooo-riscv-details.md` | 面试技术展开、关键模块、debug 和 synthesis 信息 |

### Situation

项目目标是从简单 in-order pipeline 扩展到可综合的 out-of-order RISC-V core。相比普通五级流水线，OoO 需要同时解决 instruction-level parallelism、register renaming、乱序执行、按序提交、memory dependency、branch misprediction recovery 和 cache miss latency hiding。项目 memory model 引入约 100 ns latency，因此必须通过 I/D cache、MSHR 和 store queue 来降低访存阻塞对性能的影响。

### Task

负责/参与 OoO core 的微架构设计、RTL 集成、模块验证、program-level regression、pipeline hang debug 和 synthesis flow。重点是保证“乱序执行但 architectural state 精确”，并让复杂并行结构在 branch recovery、store/load ordering、cache miss 和多发射场景下保持正确。

### Action

**1. Rename / ROB / precise commit**

- 使用 freelist + map table 为目的寄存器分配 physical register，消除 WAW/WAR 假相关。
- ROB 保存 in-flight instruction 的目的寄存器、新旧 PR、complete bit、store/branch metadata。
- ROB head 最多按序 retire 3 条 completed instructions，retire 时更新 architectural map，并释放旧 PR。
- Branch recovery 时恢复 map table 和 freelist，flush speculative pipeline state，保证 precise architectural state。

**2. Reservation station / issue / CDB wakeup**

- RS 支持最多 3 条 dispatch，维护 operand ready bit、source PR、ROB index、FU type 和 SQ tail position。
- CDB 广播最多 3 个完成 tag/value，RS 和 map table 同步 wakeup。
- 每周期选择最多 3 条 oldest-ready instructions，并检查 FU FIFO backpressure。
- Issue path 连接 physical register file，再发送到 3 个 ALU、2 个 load/store、2 个 multiplier 和 1 个 branch FU。

**3. Store queue / load-store ordering**

- Store 在 dispatch 分配 SQ entry，execute 后写入 address/data/byte mask，retire 后才进入 D-cache。
- Load 查询 older stores；如果 older store address 未解析则 stall，如果地址匹配则做 byte-granular forwarding。
- SQ 通过 `load_tail_ready` 回压 RS，避免 younger load 越过 unresolved older store。
- Retiring stores 按 lane `[2] -> [1] -> [0]` 的 program order 送入 cache，保持 memory ordering。

**4. Cache / MSHR / memory latency hiding**

- Frontend 使用 I-cache / prefetch path 支持 3-wide fetch。
- D-cache 是 nonblocking wrapper，支持两路 load、三路 retiring store、3-way cache memory、MSHR queue、dirty writeback 和 store-miss merge。
- Branch recovery 时丢弃 speculative clean load MSHR，但保留已经 commit 或 dirty 的 store state，避免 recovery 破坏内存正确性。

**5. Branch predictor / recovery path**

- Branch predictor 使用 BTB/type table、gshare-style PHT 和 lightweight return-address stack。
- Branch FU 解析后更新 predictor；如果需要 recovery，信息经 complete/ROB/retire 路径触发 frontend redirect。
- Recovery 同时 flush IF/D、RS、issue FIFO、FU、SQ，并恢复 rename state。

**6. 验证和 debug infrastructure**

- 用 `test/pipeline_test.sv` 跑 `programs/*.s` / `programs/*.c`，生成 `.out`、`.wb`、`.ppln`。
- 用 `run_all_program.sh` 对比 P4 RTL 输出和 P3 golden `.wb` / `.out`。
- 增加 no-retire diagnostic snapshot，打印 ROB/RS/SQ/cache/MSHR/recovery 状态，定位 pipeline hang。
- 用 latency sweep 脚本调整 `MEM_LATENCY_IN_CYCLES`，观察 cache/memory subsystem 在不同 latency 下的行为。

### Result

- 完成 3-wide OoO RV32IM processor RTL，核心结构包括 32-entry ROB、16-entry RS、64-entry physical register file、8-entry SQ、8-entry D-cache MSHR 和 8 个 functional units。
- 建立 program-level regression 和 golden compare flow，可对多种 assembly/C benchmark 生成 writeback trace 并比对。
- 建立 focused diagnostic flow，用于 debug no-retire、branch recovery、load/store ordering 和 cache miss hang。
- Design Compiler synthesis report 显示 full pipeline 在 ASAP7 library 下 timing met：clock period `9800 ps`，worst reported slack `MET 0.20 ps`，total cell area 约 `57442`。

### 面试版 2 分钟回答（中文）

我做过一个 3-wide out-of-order RISC-V 处理器项目，目标是实现一个可综合的 RV32IM core。这个设计在 fetch、dispatch、complete 和 retire 侧都是最多 3 条，并包含 register renaming、freelist、map table、ROB、reservation station、physical register file、store queue、branch predictor、I-cache、nonblocking D-cache 和 MSHR。

这个项目最核心的问题是保持 precise state。我的理解是，OoO 不是乱序提交，而是 ready 的指令可以乱序执行，但必须通过 ROB 按 program order commit。Dispatch 阶段为目的寄存器分配新的 physical register，map table 保存 speculative mapping，ROB 记录每条 in-flight instruction 的新旧 PR、complete bit、store/branch 信息。Retire 阶段只从 ROB head 开始提交，提交后更新 architectural map 并释放旧 PR。这样遇到 branch mispredict 时，就可以恢复 map table 和 freelist，flush RS、issue FIFO、FU、SQ 等 speculative state，再把 fetch redirect 到正确 PC。

另一个重点是 memory ordering。我实现了 store queue：store 在 dispatch 时分配 entry，execute 后写入地址、数据和 byte mask，但只有 retire 后才真正进入 D-cache。Load 会查询所有 older stores，如果地址还没解析就 stall；如果地址匹配就按 byte 做 forwarding；如果不相关才访问 cache。这样可以支持 OoO 的 load/store 执行，同时保证 program order 的 memory correctness。

为了处理 100 ns 级 memory latency，项目里有 I-cache、3-way D-cache、MSHR、dirty writeback 和 store-miss merge。验证上，我用 program-level testbench 跑 assembly/C 程序，生成 `.wb` 和 `.out`，再和 golden trace 比对；同时加了 no-retire diagnostic snapshot，遇到 hang 时可以直接看 ROB head、RS ready、SQ/cache stall、MSHR 和 recovery 状态。最后这个 full pipeline 也走了 Design Compiler synthesis，ASAP7 report 里 9800 ps clock period 下 timing met。

### 面试版 60 秒回答（英文）

I implemented a synthesizable three-wide out-of-order RV32IM processor. The core uses register renaming with a freelist and map table, a 32-entry ROB for in-order commit, a 16-entry reservation station for oldest-ready issue, a physical register file, and eight functional units including ALUs, load/store units, multipliers, and a branch unit.

The key challenge was maintaining precise state. Instructions can execute out of order, but they retire in program order through the ROB. On branch recovery, the frontend is redirected, the speculative map table is restored from the architectural map, the freelist head is recovered, and speculative structures such as the RS, issue queues, FUs, and SQ are flushed.

I also designed the memory-ordering path with a store queue. Loads check older stores, stall on unresolved store addresses, and use byte-granular store-to-load forwarding when addresses match. The cache subsystem includes an I-cache, a nonblocking three-way D-cache, MSHRs, dirty writeback, and store-miss merging. I built program-level regression scripts to compare writeback traces against golden outputs and added diagnostic logs for no-retire and pipeline hang debugging. The design was synthesized with an ASAP7 flow and met timing at a 9800 ps clock period.

> **详细技术实现笔记**: [ooo-riscv-details.md](ooo-riscv-details.md) — 包含顶层架构、关键参数、ROB/RS/SQ/cache/recovery 设计、验证 debug flow、综合结果和面试追问。

### 可追问点

- OoO：为什么是乱序执行、按序提交，而不是乱序提交。
- Rename：freelist、map table、architectural map table 和 old PR release 的关系。
- ROB：precise exception / branch recovery 为什么需要 ROB head commit。
- RS：如何做 CDB wakeup，如何选 oldest-ready instruction。
- SQ：load 如何处理 unresolved older store，store-to-load forwarding 如何按 byte mask 做。
- D-cache：MSHR 如何支持 nonblocking miss，dirty store miss 为什么要 merge。
- Branch recovery：为什么 D-cache 不能简单全清，哪些 speculative state 可以丢，哪些 committed/dirty state 不能丢。
- Debug：no-retire hang 如何从 ROB head、RS、SQ/cache stall 和 CDB 方向定位。
- Synthesis：clock period、area、slack report 如何解读。

### 可直接放简历的 bullets

- Implemented a synthesizable 3-wide out-of-order RV32IM processor with register renaming, freelist/map table, 32-entry ROB, 16-entry reservation station, physical register file, and precise in-order retirement.
- Designed memory-ordering logic with an 8-entry store queue, byte-granular store-to-load forwarding, unresolved-store load stalling, and ordered store commit into a nonblocking D-cache.
- Built a cache subsystem with I-cache, 3-way D-cache, MSHRs, dirty writeback, store-miss merging, and branch-recovery-aware speculative load cleanup.
- Developed program-level regression and debug infrastructure comparing `.wb` / `.out` traces against golden references, with focused diagnostic logs for ROB/RS/SQ/cache/recovery stalls.
- Synthesized the full pipeline using an ASAP7 Design Compiler flow; timing met at a 9800 ps clock period with total cell area around 57.4k.

---

<a id="star-ddr4-controller-apb-axi-vip"></a>
## DDR4 Controller APB + AXI VIP 验证项目

标签：`#project` `#ddr4` `#memory-controller` `#apb` `#axi` `#uvm-vip` `#scoreboard`

### 一句话概括

基于 Synopsys DWC DDR54 验证环境理解并整理 DDR4 controller 的 APB + AXI VIP 验证主线：通过 APB VIP 配置 controller/PHY 寄存器，通过 AXI4 VIP 产生 DDR memory 读写流量，再用 APB/AXI checker、read-hash、AXI-HIF、HIF-DFI、DDR/DFI checker 和 postprocess 判断结果是否正确。

### 项目关键参数

| 类别 | 参数 | 面试口径 |
| --- | --- | --- |
| AXI ports | 当前生成配置 4 个 active AXI4 master port | `UMCTL2_A_NPORTS=4`，`UMCTL2_A_TYPE_0..3=3` 表示 AXI4 |
| AXI width | 每口 256-bit data，37-bit address，8-bit ID，8-bit LEN，4-bit QoS | `UMCTL2_PORT_DW_i=256`、`UMCTL2_A_ADDRW=37`、`UMCTL2_A_IDW=8`、`UMCTL2_A_LENW=8` |
| Burst / boundary | AXI4 max burst 256 beats，4KB boundary | `SVT_AXI4_MAX_BURST_LENGTH=256`，`UMCTL2_AXI_ADDR_BOUNDARY=12` |
| Outstanding | VIP master outstanding 默认 256 | 因为 4 ports <= 5，`num_outstanding_xact=SVT_AXI_MAX_NUM_OUTSTANDING_XACT` |
| APB config path | 32-bit address / 32-bit data APB master | APB4 是否开启由 `DDRCTL_APB4_EN` 控制，不把它说死 |

### Situation

DUT 是 DDR4/DDR5/LPDDR 可配置的 DDR controller 验证环境。对 DDR4 普通数据通路来说，test writer 不需要自己手写 DDR4 pin-level driver，而是面对 controller 的上层接口：

- APB 作为 CSR/control path，用于配置 DDR controller 和 PHY 相关寄存器。
- AXI4 作为 memory traffic path，用于向 DDR memory 地址空间发 write/read burst。
- controller 内部负责把 AXI 请求转换成 HIF/DFI/PHY/DDR4 侧的命令和数据行为。

### Task

把这个项目中“APB 配置 + AXI 搬数据”的验证使用场景讲清楚，重点不是验证 APB/AXI 总线本身，而是用 APB/AXI 作为入口验证 DDR controller 是否正确控制 DDR4。

### Action

**1. APB VIP 用法：配置 controller 和 PHY**

- test 初始化阶段通过 APB VIP 写寄存器，例如 DDR 模式、timing、地址映射、端口使能、refresh、DFI/PHY init 相关配置。
- APB sequence 本质是产生 `svt_apb_transaction::WRITE` / `READ`，字段包括 `address` 和 `data`。
- APB read 用于 polling status，例如 init done、training done、DFI ready。DDR 没 ready 前不应该启动普通 AXI traffic。

**2. AXI VIP 用法：产生 DDR memory traffic**

- AXI VIP master sequence 在每个 AXI port 上产生 write/read burst。
- directed sequence 会显式设置 `xact_type`、`addr`、`burst_type`、`burst_length`、`data`、`wstrb`，常见场景是 write pattern 后从同一地址 read back。
- random/stress sequence 会变化地址、burst、ID、QoS、端口并发，用来打 controller 仲裁、队列、bank/page 行为。

**3. DDR4 协议侧由 controller 自动完成**

APB/AXI 只是入口，controller 后面仍然要遵守 DDR4 协议：

- AXI/system address 被映射成 `rank / bank group / bank / row / column`。
- 对 page miss，controller 需要调度 `ACT -> RD/WR -> PRE`；对 page hit，可以复用已打开 row。
- controller 还要自动插入 refresh，并满足 `tRCD`、`tRP`、`tRAS`、`tFAW`、`tRFC`、read/write turn-around 等 timing。

**4. 结果检查链路**

| 检查层 | 检查内容 | 作用 |
| --- | --- | --- |
| APB VIP checker / predictor | APB read/write 握手、`PSLVERR`、寄存器 mirror/readback | 确认配置事务和寄存器访问正确 |
| AXI VIP checker | AXI AW/W/B/AR/R 五通道、burst、ID、response、`WLAST/RLAST` | 确认流量入口协议合法 |
| AXI read-hash scoreboard | 写入 pattern 与读回 `RDATA` | 检查 end-to-end data integrity |
| AXI-HIF scoreboard | AXI memory transaction 到 HIF 请求的转换 | 检查地址、长度、方向、优先级、数据是否被 controller 转对 |
| HIF-DFI scoreboard / DDR checker | HIF 请求到 DFI/DDR4 命令和数据 | 检查 DDR4 command/timing/data 行为是否符合预测 |
| `runtest.pm` postprocess | `checklog.pl` 扫 log，并要求 `COMPLETED - done with Env` | 汇总 UVM error/fatal、scoreboard mismatch、timeout，生成最终 PASS/FAIL |

### Result

- 明确了自己不需要手写 DDR4 pin-level protocol driver；普通测试主要写 APB register sequence、AXI traffic sequence 和检查配置。
- 能区分“验证 APB/AXI 协议”与“通过 APB/AXI 验证 DDR controller”：后者真正关注地址映射、bank/row/page 行为、refresh、timing 和数据完整性。
- 整理了 APB + AXI VIP 验证 DDR4 controller 的可视化说明页，便于面试时从 stimulus、DDR4 协议、scoreboard 三层解释项目。

> **详细技术实现笔记**: [ddr4-controller-apb-axi-vip-details.md](ddr4-controller-apb-axi-vip-details.md#ddr4-controller-apb-axi-vip-details) — 包含 APB/AXI VIP 使用方式、DDR4 command/timing 解释、scoreboard/checker 链路、debug 方法和 HTML 图解。

### 面试版 2 分钟回答（中文）

这个项目是一个 DDR controller 的验证环境。我理解的主线是：普通 DDR4 数据通路验证并不是直接手写 DDR4 command driver，而是通过 controller 的上层接口来产生激励。APB VIP 负责做寄存器配置，比如 DDR4 模式、timing、地址映射、端口使能和 DFI/PHY 初始化；配置完成后通过 APB read polling init done 或 training done。DDR ready 之后，再用 AXI4 VIP 在各个 AXI port 上发 write/read burst，比如先向某个 DDR memory address 写入 pattern，再从同一地址读回来。

真正被验证的不是 APB/AXI 总线本身，而是 controller 接到 AXI 请求后，能不能正确把 system address 映射成 DDR4 的 rank、bank group、bank、row、column，并按 DDR4 协议调度 ACT、RD、WR、PRE、REF 等命令，同时满足 tRCD、tRP、tRAS、tFAW、refresh 等 timing。结果检查也不是单一的 readback，而是多层的：APB/AXI VIP checker 保证入口协议合法，read-hash scoreboard 检查写入和读回数据一致，AXI-HIF scoreboard 检查上层 AXI 请求到内部 HIF 请求的转换，HIF-DFI/DDR checker 检查 controller 发到内存侧的命令和 timing。最后 postprocess 扫 test log，确认没有 UVM error/fatal、没有 scoreboard mismatch，并且出现 `COMPLETED - done with Env`，才认为 test passed。

### 面试版 60 秒回答（英文）

In this DDR controller project, the main verification flow uses APB and AXI VIPs as the stimulus entry points. The APB VIP is used for CSR programming: DDR mode, timing, address mapping, port configuration, refresh settings, and DFI/PHY initialization. After polling the status registers and confirming that initialization and training are done, the AXI4 VIP generates memory traffic, typically write bursts followed by read bursts to the same DDR address space.

The goal is not just to verify APB or AXI protocol compliance. Those protocols are only the front-door interfaces. The real target is the DDR controller behavior: address mapping to rank, bank group, bank, row and column; scheduling ACT, READ, WRITE, PRECHARGE and REFRESH commands; meeting DDR4 timing constraints; and preserving data integrity. The checking is multi-layered: APB and AXI VIP checkers validate the bus transactions, read-hash scoreboards compare written and read data, AXI-to-HIF and HIF-to-DFI scoreboards check internal conversion and DDR command behavior, and the postprocess script scans logs and the completion message to produce the final pass/fail result.

### 可追问点

- 为什么普通 test 不需要写 DDR4 pin-level driver？
- APB 配置路径和 AXI 数据路径的本质区别是什么？
- AXI 地址如何映射到 DDR4 rank/bank/row/column？
- AXI protocol pass 为什么不等于 DDR controller pass？
- read-hash、AXI-HIF、HIF-DFI scoreboard 分别抓哪一类 bug？
- 如果 AXI 写和读 response 都是 OKAY，但数据错了，可能是哪一层的问题？
- UVM env 五层结构各自的职责是什么？
- 虚拟 sequencer 和虚拟 sequence 的分工？
- RAL adapter（reg2apb）在整个寄存器访问链路中处于哪个位置？

### 可直接放简历的 bullets

**中文版（适合中文简历或面试简历讲述）：**

- 基于 Synopsys DWC DDR54 工业级验证平台，分析并掌握 DDR4 controller 的 APB + AXI UVM 验证主线：通过 Synopsys SVT APB VIP（`svt_apb_system_env`）进行 DDR controller/PHY CSR 配置，通过 SVT AXI VIP（`svt_axi_system_env`）产生多端口 DDR memory 读写流量，验证 controller 地址映射、DDR4 命令调度与数据完整性。
- 深入理解五层 UVM 环境架构（`ddr_uvm_pve_tb_top` → `dwc_ddrctl_mss_env` → `dwc_ddrctl_vip_env` → `dwc_ddrctl_env` / `dwc_ddrctl_reg_utilities`），能准确描述 APB/AXI/DDR4/DFI VIP 的内部 driver-monitor-sequencer 结构及各 agent 职责。
- 掌握基于 `uvm_reg_adapter`（`dwc_ddrctl_reg2apb_adapter`）的 RAL-to-APB 寄存器访问链路：RAL write/read 调用经 `reg2bus()` 转为 `svt_apb_transaction`，APB monitor 观察后经 predictor 更新 mirror，实现配置通路的完整可观测性。
- 分析多层 scoreboard 检查链路：APB/AXI VIP protocol checker 保证入口合规，read-hash scoreboard（`dwc_ddrctl_axi_read_hash_sb`）检查 end-to-end 数据完整性，AXI-HIF scoreboard（`dwc_ddrctl_axi_hif_top_sb`）检查地址/命令转换，HIF-DFI scoreboard（`dwc_ddrctl_hif_dfi_sb_env`）检查 DDR4 command/timing 调度行为。
- 梳理工程中 200+ 个测试用例的覆盖方向，包括 AXI basic/random/directed/QoS/exclusive/streaming 等场景，以及 APB timeout、ECC error injection、low-power 状态机和 HWFFC/SWFFC 频率切换等专项测试。

**English version (for English resume or international interviews):**

- Analyzed and mastered the DDR4 controller APB + AXI UVM verification flow in the Synopsys DWC DDR54 industrial verification platform; used Synopsys SVT APB VIP (`svt_apb_system_env`) for DDR controller/PHY CSR programming and SVT AXI VIP (`svt_axi_system_env`) to generate multi-port DDR memory traffic.
- Understood the five-level UVM environment hierarchy (`ddr_uvm_pve_tb_top` → `dwc_ddrctl_mss_env` → `dwc_ddrctl_vip_env` → `dwc_ddrctl_env` / `dwc_ddrctl_reg_utilities`), including the internal driver-monitor-sequencer structure of APB, AXI, DDR4, and DFI VIPs, and the role of each agent.
- Studied the RAL-to-APB register access chain via `uvm_reg_adapter` (`dwc_ddrctl_reg2apb_adapter`): RAL write/read calls are converted to `svt_apb_transaction` through `reg2bus()`, observed by the APB monitor, and used by the register predictor to update the mirror value.
- Analyzed the multi-layer scoreboard and checker chain: APB/AXI VIP protocol checkers for bus compliance; read-hash scoreboard for end-to-end data integrity; AXI-to-HIF scoreboard for address, command, and direction conversion; HIF-to-DFI scoreboard for DDR4 command scheduling, timing, and page-hit/miss behavior.
- Mapped 200+ test cases across AXI basic, random, QoS, exclusive access, streaming, and directed scenarios, plus APB timeout, ECC error injection, low-power, and HW/SW frequency-change tests.

---

<a id="star-ibex-rv32im-uvm"></a>
## Ibex RV32IM UVM / 官方 DV Bring-up 项目

标签：`#project` `#ibex` `#riscv` `#rv32imc` `#rtl` `#uvm` `#scoreboard` `#coverage`

### 一句话概括

基于 lowRISC Ibex 开源 RISC-V core 搭建面向简历展示的 RV32IMC 验证项目：用 `simple_system` RTL wrapper 运行 directed `.vmem` 程序作为真实指令流激励，并搭建轻量 UVM scaffold，规划 sequence、monitor、scoreboard、coverage 和 reference model 的 instruction-level checking 流程。

### 项目关键参数

| 类别 | 参数 | 面试口径 |
| --- | --- | --- |
| Core config | `RV32MFast` + `RV32BNone` + `RV32Zca` + `RegFileFF` | RV32IMC-style baseline：支持 M 和 compressed Zca，不开 bitmanip |
| Wrapper | Ibex `examples/simple_system` | core + RAM + timer + simulator_ctrl，适合作 directed `.vmem` sanity regression |
| Bus / memory | 32-bit local memory/data path | 当前不是完整 SoC interconnect 验证，而是 simple_system bring-up |
| Disabled features | no I-cache、branch predictor、writeback stage、PMP in local config | 这些是后续可扩展点，不在当前项目里夸大 |
| Regression guard | `TimeoutCycles=2000` per program | 通过 program self-check、halt/status 和后续 scoreboard 规划验证结果 |

### 工程路径

| 类型 | 路径 | 用途 |
| --- | --- | --- |
| 项目根目录 | `C:\Users\28724\Desktop\IC_EDA_Lite（精简版50G）\virtual\IC_EDA_Lite\share\ibex_rv32im_uvm_verification` | 顶层 Makefile、docs、programs、local RTL/UVM scaffold |
| 本地 RTL baseline | `rtl_tb/`、`programs/` | Ibex `simple_system` wrapper、directed `.vmem` 程序、smoke/ALU/branch/load-store regression |
| 轻量 UVM scaffold | `uvm_tb/`、`docs/uvm_architecture_plan.md` | 自定义 UVM test/env/sequence/item/scoreboard/coverage 架构规划 |
| 参考环境 | `ibex/dv/uvm/core_ibex/` | lowRISC 官方 UVM + riscv-dv + Spike cosim flow，作为后续扩展参考 |

### Situation

Ibex 是 lowRISC 开源的 32-bit RISC-V core。为了把它整理成适合 ASIC DV 面试讲解的个人项目，我没有直接照搬完整官方 regression，而是先构建一个小而清晰的验证平台：DUT 使用 `ibex_simple_system`，激励通过 RISC-V 程序进入 core，结果通过程序 self-check、halt 行为和后续 UVM scoreboard 进行验证。

### Task

项目目标不是简单“能 clone Ibex”，而是做出一个面试可讲的 DV project：

- 搭建一个本地可稳定运行的 Ibex RTL directed regression，作为 sanity baseline。
- 搭建轻量 UVM testbench scaffold，体现 test、env、sequence item、sequence、scoreboard、coverage 的分层。
- 说明激励如何从 `.vmem` directed program 或 UVM sequence 进入 DUT。
- 规划 monitor / scoreboard / reference model 如何比较 PC、寄存器写回、memory side effect 和 exception。

### Action

**1. 本地 RTL sanity regression**

- 使用 Ibex `examples/simple_system` wrapper，包含 core、RAM、timer 和 simulator-control halt register。
- 编写/组织 `programs/*.vmem`，覆盖 smoke boot、ALU、branch loop、load/store 等基础程序。
- 顶层 Makefile 提供 `make smoke`、`make alu`、`make branch`、`make load-store`、`make regress`，作为任何环境问题前的最小可运行 baseline。

**2. 轻量 UVM 架构规划**

目标 UVM 结构按“简历可讲、可逐步实现”设计：

```text
test
  └── env
        ├── instr/mem agent or bus monitor
        ├── commit trace monitor
        ├── scoreboard
        ├── coverage collector
        └── virtual sequencer
```

验证重点不是完整 SoC 集成，而是 instruction-level checking：用 DUT commit trace 和 ISS / reference model 对比，覆盖 instruction type、operand corner、branch direction、load/store alignment、exception、stall/flush 等场景。

**3. 激励发送方式**

- 当前可运行路径采用 software-driven stimulus：把 RISC-V directed program 预加载为 `.vmem`，Ibex 从 RAM 取指执行。
- `smoke.vmem` 负责 boot 和 halt；`alu_directed.vmem` 覆盖整数运算；`branch_directed.vmem` 覆盖 taken branch；`load_store_directed.vmem` 覆盖 RAM store/load。
- UVM scaffold 中 `ibex_smoke_seq` 展示标准 `start_item()` / `randomize()` / `finish_item()` 发送 `ibex_instr_item` 的方式，后续这些 item 可转换成 program image 或由 virtual sequence 控制 preload/reset/run。

**4. 结果检查与 coverage**

- Directed program 内部做 self-check：例如 ALU result、branch path、load/store readback；失败则不写 halt register，testbench timeout 报错。
- Testbench 统一用 halt register + timeout 判断 pass/fail，避免程序跑飞导致仿真挂死。
- Scoreboard 规划从 RVFI/commit monitor 接收 commit item，比对 DUT 和 reference model 的 PC、GPR writeback、memory side effect 和 exception。
- `ibex_func_cov` 已有 opcode coverage bins，后续从 monitor/commit stream 采样 instruction type、operand corner、branch taken、load/store alignment、stall/flush。

**5. 官方 flow 作为扩展参考**

官方 `core_ibex` UVM/riscv-dv/Spike flow 已作为参考环境接入 Makefile，用来对齐真实工业级 Ibex DV 架构；但项目面试主线放在本地 RTL baseline 和轻量 UVM 结构，而不是工具链 debug。

### Result

- 本地 Ibex simple_system directed regression 形成稳定 baseline：smoke、ALU、branch、load/store 可通过 Makefile 一键运行。
- 轻量 UVM scaffold 已包含 base test、env、instruction item、sequence、scoreboard 和 functional coverage collector。
- 激励路径清晰：directed `.vmem` 作为真实 instruction stream 进入 core；UVM sequence 作为后续自动生成 program image 的入口。
- 检查路径清晰：当前用 self-check + halt/timeout；后续扩展为 commit monitor + scoreboard + reference model。
- Coverage 规划覆盖 instruction group、operand corner、branch behavior、load/store alignment、stall/flush 和 exception。

### 面试版 2 分钟回答（中文）

我做了一个基于 lowRISC Ibex 的 RV32IMC 验证项目。RTL 侧我使用 Ibex 的 `simple_system` wrapper，里面包含 Ibex core、RAM、timer 和 simulator control。激励不是直接 force 内部信号，而是把 directed RISC-V 程序做成 `.vmem` 预加载到 RAM，让 core 自然取指执行。当前有 smoke、ALU、branch、load/store 四类 directed program，并用 Makefile 做一键 regression。

结果检查分两层：当前 directed program 自己检查 ALU result、branch path、load/store readback，成功后写 simulator halt register；如果没有走到 halt，testbench timeout 报错。UVM 侧我搭了轻量 scaffold，包括 base test、env、instruction item、smoke sequence、scoreboard 和 opcode coverage。sequence 用标准 `start_item/randomize/finish_item` 发送 instruction item，后续可以转成 program image 或由 virtual sequence 控制 preload/reset/run。scoreboard 规划从 RVFI/commit monitor 接 commit item，与 reference model 比较 PC、寄存器写回、memory side effect 和 exception。

从面试角度，这个项目重点体现的是 CPU 验证思路：用 instruction stream 做激励，用 architectural state/commit stream 做检查，用 functional coverage 追 instruction group、operand corner、branch、load/store 和 flush/stall，而不是只讲工具链 debug。

> **详细技术实现笔记**: [ibex-rv32im-uvm-details.md](ibex-rv32im-uvm-details.md) — 包含 DUT/simple_system RTL 结构、directed `.vmem` 激励、UVM scaffold、sequence 如何发送 item、scoreboard/coverage 如何验证结果、RVFI/ISS 扩展计划和面试追问。

### 面试版 60 秒回答（英文）

I built an Ibex RV32IMC verification project based on the open-source lowRISC Ibex core. On the RTL side, I used the Ibex simple_system wrapper, which contains the Ibex core, RAM, timer, and simulator-control block. The stimulus is software-driven: directed RISC-V programs are preloaded as VMEM images, and the core naturally fetches and executes them. I currently have smoke, ALU, branch, and load/store directed tests in a Makefile regression.

For checking, the directed programs perform self-checks and write the simulator halt register on success; otherwise the testbench timeout reports a failure. On the UVM side, I built a lightweight scaffold with a base test, environment, instruction item, smoke sequence, scoreboard, and opcode functional coverage. The sequence uses the standard `start_item`, `randomize`, and `finish_item` flow. The next step is to connect a commit/RVFI monitor so the scoreboard can compare PC, register writeback, memory side effects, and exceptions against a reference model or ISS.

### 可追问点

- 为什么 CPU 验证适合用 instruction stream 作为激励。
- `.vmem` program 如何进入 Ibex simple_system 的 RAM。
- 程序 self-check、halt register 和 testbench timeout 分别检查什么。
- UVM sequence 中 `start_item/randomize/finish_item` 如何生成 instruction item。
- 为什么 coverage 应该从 monitor/commit stream 采样，而不是从 sequence 采样。
- RVFI/commit monitor 需要采 PC、rd writeback、memory side effect、exception 等哪些字段。
- Scoreboard 如何和 reference model / ISS 比较 architectural state。
- 如果继续完善：接入 RVFI monitor、实现轻量 reference model、扩展 functional coverage、再接官方 riscv-dv/Spike flow。

### 可直接放简历的 bullets

- Built a runnable Ibex RV32IMC simple_system verification baseline using directed VMEM programs for smoke, ALU, branch, and load/store scenarios.
- Structured a lightweight UVM environment with base test, environment, instruction sequence item, smoke sequence, scoreboard, and opcode functional coverage.
- Used software-driven instruction-stream stimulus to exercise fetch, decode, execute, branch, load/store, and memory paths naturally.
- Planned commit/RVFI-based scoreboard checking for PC, register writeback, memory side effects, exceptions, and end-of-test architectural state.
- Defined a phased verification strategy from directed self-checking programs to UVM monitor-based checking and later ISS/Spike comparison.

---

<a id="star-apb-uart"></a>
## APB-UART UVM 验证环境

标签：`#project` `#apb` `#uart` `#uvm` `#dv` `#coverage` `#error-injection`

### 一句话概括

为 APB-UART IP 搭建完整 UVM 验证环境，覆盖 UART config/protocol、data compare、parity error、frame error、overrun error 等 6 个测试场景，并收集 functional coverage。

### Situation

DUT 是一个 APB-slave 接口的 UART 控制器，支持可编程 baud rate、parity、frame 格式配置，以及 RX/TX 数据通路。验证需要覆盖正常收发、寄存器配置、各种 error 注入场景，并收集 coverage 确认配置空间全覆盖。

### Task

搭建 UVM testbench，覆盖 UART 功能点和 error 路径，建立 coverage model，确保所有配置组合和 error 条件都被触发。

### Action

**Testbench 架构：**

- `apb_uart_top.sv`：DUT 顶层，例化 APB slave interface 和 UART RX/TX。
- UVM env 包含 APB agent（active master）、UART RX/TX monitor/predictor、scoreboard 和 coverage collector。
- 通过 APB 配置 UART baud/parity/enable，再通过 UART RX/TX 发送数据并检查结果。

**测试用例：**

| 测试 | 目标 |
| --- | --- |
| `apbuart_config_test` | 配置 UART 寄存器，验证 baud rate / parity / enable 生效 |
| `apbuart_data_compare_test` | 发送已知数据，RX 端接收后 scoreboard 比对 |
| `apbuart_parity_error_test` | 注入 parity error，验证 status 寄存器正确置位 |
| `apbuart_frame_error_test` | 注入 frame error（stop bit 错误），验证 error 上报 |
| `apbuart_free_error_test` | 注入 overrun/framing 组合错误，验证 error 优先级和处理 |
| `apbuart_rec_drv_test` / `apbuart_rec_readreg_test` | 寄存器读写回归，验证 APB 访问正确性 |

**Coverage：**

- Covergroup 采样 UART 配置空间（baud rate bins、parity enable/type、data bits、stop bits）。
- Error coverage：parity error / frame error / overrun 是否都被触发过。
- 仿真后生成 URG coverage report（`urgReport/`）。

### Result

- 6 个测试全部通过，UART 配置、数据收发、error 上报均验证正确。
- Functional coverage 达到 100%（配置空间全覆盖）。
- 项目来自 `IC_EDA_Lite/share/apb-uart-uvm-env`，包含完整 Questa 仿真 flow 和 coverage report。

### 面试版 60 秒回答（英文）

I built a UVM verification environment for an APB-UART controller. The testbench has an APB active master agent for register programming and a UART monitor/predictor for RX/TX data checking. I implemented six test scenarios covering register configuration, data loopback comparison, parity error injection, frame error injection, overrun error handling, and register readback. The scoreboard compares transmitted and received data, and a functional coverage model ensures all configuration combinations and error conditions are exercised. All tests passed and coverage reached 100%.

### 可追问点

- APB 协议：APB vs AXI-Lite 的区别，APB transfer 的 write/read 时序
- UART protocol：start bit / data / parity / stop bit 格式，baud rate 如何分频
- Error 注入：如何在 UVM sequence 中注入 parity/frame error，error status 如何清除
- Coverage：covergroup 如何定义 cross coverage（baud × parity × data_bits）

---

<a id="star-async-fifo"></a>
## Async FIFO UVM 验证

标签：`#project` `#async-fifo` `#cdc` `#uvm` `#systemverilog` `#gray-code` `#cross-clock`

### 一句话概括

基于 UVM Primer 实现异步 FIFO 的双版本 testbench（SystemVerilog OOP 版 + UVM 版），覆盖指针同步、空满判断、数据完整性等验证点，掌握跨时钟域验证方法。

### Situation

DUT 是一个异步 FIFO，读写时钟域独立，使用格雷码指针跨时钟同步，通过 `rptr_empty` / `wptr_full` 判断空满状态。需要验证跨时钟数据正确性、指针同步正确性、空满标志时序，以及 reset 和边界条件。

### Task

搭建两套 testbench：一套纯 SystemVerilog OOP（理解 UVM 之前的基础），一套完整 UVM 环境（factory/phase/objection/coverage），对比两种方法的差异，掌握 UVM 的优势。

### Action

**DUT 关键点：**

- `async_fifo.sv`：顶层，例化 `fifomem`、`sync_r2w`、`sync_w2r`、`rptr_empty`、`wptr_full`。
- 格雷码指针：`rptr` / `wptr` 在各自时钟域是二进制，跨时钟同步前转为格雷码（`sync_r2w` / `sync_w2r` 做两级 FF 同步）。
- 空满判断：比较同步后的指针（格雷码 → 二进制），而非直接比较。

**SV OOP testbench（`Async_FIFO_Verification/`）：**

- 手写 testbench：`tb_top.sv`，直接例化 DUT，用 `initial` block 生成时钟和激励。
- 用 `mailbox` / `event` 做组件间通信，用 `assertion` 检查协议。
- 优点：简单直观；缺点：复用性差，scoreboard/coverage 需要手写，多测试场景管理困难。

**UVM testbench：**

- `env`：包含 `input_agent`（写侧）、`output_agent`（读侧）、`scoreboard`、`coverage subscriber`。
- `input_agent`：active driver 发送写数据，`monitor` 采样写事务。
- `output_agent`：passive monitor 采样读事务，送 scoreboard 比对。
- Coverage：covergroup 采样 FIFO 深度、读写时钟频率比、空满标志、reset 行为。

**跨时钟验证要点：**

- 在 Questa 中设置不同读写时钟频率比（1:1、2:1、3:2 等），验证数据正确性。
- 检查格雷码同步延迟（2 个 FF）是否导致空满判断的保守性（full 提前置位，empty 提前置位是正常的）。
- 用 assertion 检查 `wready` / `rvalid` 与指针的时序关系。

### Result

- 双版本 testbench 均通过仿真，数据完整性无错误。
- 覆盖跨时钟场景：同频、读写异频、背靠背读写、几乎满/几乎空边界。
- 理解 SV OOP testbench 与 UVM 的差异：UVM 的 factory/phase/objection/config_db 在复杂项目中优势明显。
- 项目来自 `IC_EDA_Lite/share/fifo_uvm`，包含完整 UVM Primer 学习笔记。

### 面试版 60 秒回答（英文）

I verified an asynchronous FIFO using both a SystemVerilog OOP testbench and a UVM testbench to compare the two approaches. The DUT uses Gray-code pointers synchronized across clock domains, with empty/full flags derived from the synchronized pointers. The SV testbench helped me understand the fundamentals—clock generation, mailbox-based communication, and basic assertions. The UVM environment added a proper scoreboard, coverage subscriber, and reusable agents. I tested various clock frequency ratios and verified that the Gray-code synchronization latency correctly causes conservative full/empty assertions. This project gave me a solid understanding of CDC verification and why UVM is valuable for complex testbench reuse.

### 可追问点

- CDC：为什么格雷码可以安全跨时钟同步，二进制指针为什么不行
- 空满判断：同步指针比较时，为什么 full 会"提前"置位（保守策略）
- UVM 对比：SV OOP testbench 的局限性，UVM factory/phase 解决了什么问题
- Coverage：如何 cover 跨时钟场景，clock frequency ratio 如何建模

---

<a id="star-tvip-axi"></a>
## TVIP-AXI (UVM AXI4 VIP) Crossbar 验证

标签：`#project` `#axi` `#vip` `#uvm` `#crossbar` `#multi-master` `#backpressure` `#contention`

### 一句话概括

基于开源 TVIP-AXI UVM VIP，搭建 AXI4 crossbar 多 master/slave 验证环境，覆盖 multi-master contention、outstanding、backpressure、BRESP error 等场景，掌握 AXI protocol 验证和 VIP 使用方法。

### Situation

需要验证一个 AXI crossbar（多 master → 多 slave 互联），验证重点包括：multi-master 并发访问的 arbitration、outstanding transaction 管理、slave backpressure 处理、crossbar 地址解码正确性，以及 error response 传播。

### Task

使用现成的 AXI4 VIP（`tvip-axi`）作为 master/slave agent，搭建 crossbar 验证环境，编写 virtual sequence 控制多 master 并发场景，并通过 scoreboard 和 coverage 确认传输正确性。

### Action

**环境架构（`uvm_axi/sample/env/`）：**

- 使用 `tvip-axi` 提供的 `tvip_axi_master_agent` 和 `tvip_axi_slave_agent`。
- Crossbar DUT 连接多个 master agent（initiator 侧）和多个 slave agent（target 侧）。
- `xbar_virtual_sequence` 并行启动多个 master sequence，制造 contention。
- Scoreboard 通过 `analysis_export` 收集 master 侧 request 和 slave 侧 response，按 address 比对数据。

**测试场景（`uvm_axi/sample/tb/`）：**

| 测试 | 目标 |
| --- | --- |
| `test_xbar_contention.sv` | 多 master 同时访问同一 slave，验证 crossbar arbitration（round-robin 或 fixed priority） |
| `test_xbar_mixed_delay.sv` | 不同 master 有不同 AW/AR/W ready delay，验证 outstanding 管理 |
| `test_xbar_bresp_backpressure.sv` | slave 返回 SLVERR，验证 crossbar 正确传播 BRESP 到对应 master |
| `test_xbar_same_id_thread.sv` | 同一 master 使用相同 ID 发起多笔 transaction，验证 ordering 保证 |

**VIP 使用要点：**

- `tvip_axi_master_agent` 的 `tvip_axi_master_sequence` 支持配置 `addr/burst/len/id/awready_delay/wready_delay` 等参数。
- Slave agent 的 `tvip_axi_slave_sequence` 可配置 `resp_delay` 和 `resp_type`（OKAY/SLVERR/DECERR），用于 backpressure 和 error 注入。
- 通过 `analysis_port` 获取 transaction 句柄，在 scoreboard 中做 data/response 比对。

**第三方 RTL（`third_party/verilog-axi/axi_crossbar/`）：**

- Crossbar 使用 `axi_crossbar.v` 作为 DUT，支持可配置 master/slave 数量和地址映射。
- `axi_ram.v` 作为 slave 侧 memory model，可直接用于简单场景（无需 VIP slave agent）。

### Result

- 4 个测试场景全部通过，crossbar arbitration、outstanding、backpressure、error propagation 均验证正确。
- 掌握了 AXI VIP 的使用方法：master/slave agent 配置、sequence 参数化、analysis_port 收集 transaction。
- 理解了 AXI crossbar 验证的关键点：address decoding、ID 管理、outstanding 深度、response 路由。
- 项目来自 `IC_EDA_Lite/share/uvm_axi`，VIP 源码在 `src/`，sample 环境在 `sample/`。

### 面试版 60 秒回答（英文）

I used the open-source `tvip-axi` UVM VIP to verify an AXI crossbar with multiple masters and slaves. The testbench instantiates `tvip_axi_master_agent` for initiators and `tvip_axi_slave_agent` for targets, with a scoreboard that collects transactions from both sides and checks data integrity and response codes. I wrote virtual sequences to launch parallel master sequences and create contention, and I used the slave agent's response configuration to inject backpressure and error responses. The four test scenarios covered multi-master arbitration, mixed ready delays, BRESP backpressure propagation, and same-ID transaction ordering. This project gave me hands-on experience with AXI protocol verification and how to use and extend a third-party AXI VIP.

### 可追问点

- AXI protocol：outstanding transaction 如何管理 ID，同一 ID 的 transaction 是否保证 ordering
- Crossbar：arbitration 策略（round-robin / priority），如何避免 starvation
- VIP 使用：`tvip_axi_master_sequence` 的关键参数，如何通过 analysis_port 做 scoreboard 比对
- Error 处理：SLVERR vs DECERR 的区别，crossbar 如何把 slave 的 error response 路由回正确的 master
- 第三方 RTL：`axi_crossbar.v` 的地址解码逻辑，如何配置 address map

---

<a id="star-template"></a>
## STAR 模板

### Title

一句话概括这个故事。

### Situation

背景是什么？

### Task

你的目标/职责是什么？

### Action

你具体做了什么？

### Result

结果是什么？最好包含量化结果、验证结果或学到的经验。

### 面试版 60 秒回答

待补充。

### 可追问点

- 技术细节：
- 团队协作：
- Trade-off：
- 如果重做会怎么改：

---

<a id="behavioral-interview"></a>
## Behavioral 面试

### 常见题目

- Tell me about yourself.
- Why ASIC/DV?
- Tell me about a challenging bug you debugged.
- Tell me about a time you worked with ambiguity.
- Tell me about a conflict or disagreement.

### 回答策略

先用中文把经历讲顺，再压缩成 60 秒英文版本。重点不是背稿，而是让每个故事都有清楚的背景、你的动作和结果。

---

<a id="english-answer-template"></a>
## 英文回答模板

### 技术问题回答结构

1. Define the concept.
2. Explain why it matters.
3. Give a concrete example.
4. Mention common pitfalls or trade-offs.

### 常用句型

- "The key difference is..."
- "In a verification environment, I would check this by..."
- "A common corner case is..."
- "From a debug perspective, I would first..."
- "This matters because..."

### 中英结合规则

- 笔记里先写中文回答，保证逻辑准确。
- 再写 English answer，用自然面试表达，不逐字硬翻。
- 项目经历至少准备中文 2 分钟版、英文 60 秒版。
