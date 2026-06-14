# Ibex RV32IM UVM 验证项目 - 详细技术实现

## 项目定位

这是一个基于 lowRISC Ibex 开源 RISC-V core 的前端验证项目，工程路径为：

`C:\Users\28724\Desktop\IC_EDA_Lite（精简版50G）\virtual\IC_EDA_Lite\share\ibex_rv32im_uvm_verification`

项目目标不是重新设计 Ibex，而是围绕 Ibex core 搭建一个面试可讲的验证平台：

- 用 `simple_system` 路径跑真实 RTL directed program，证明 DUT 能编译、运行指令、访问 memory 并正常结束。
- 搭建轻量 UVM scaffold，明确 test / env / sequence / item / scoreboard / coverage 的分层。
- 后续把 UVM scaffold 接到 DUT 的 memory interface 和 commit/RVFI monitor，实现 instruction-level checking。
- 官方 `core_ibex` UVM/riscv-dv/Spike flow 作为参考和扩展方向，而不是项目叙述主线。

<a id="ibex-project-parameters"></a>
## 项目关键参数

| 类别 | 当前工程参数 | 面试讲法 |
| --- | --- | --- |
| DUT wrapper | `ibex_simple_system` | 不是重新设计 CPU，而是在 simple system 上做 RTL bring-up 和 DV scaffold |
| ISA config | `RV32MFast`、`RV32BNone`、`RV32Zca` | RV32IMC-style baseline：M 扩展打开，bitmanip 关闭，compressed Zca 打开 |
| Register file | `RegFileFF` | FF regfile，适合本地仿真和移植 |
| Memory / bus | simple system 32-bit local memory/data path | 当前不夸大成完整 SoC/AXI interconnect 验证 |
| 默认关闭项 | I-cache、branch predictor、writeback stage、PMP、debug trigger 等本地 baseline 未打开 | 面试时说明这些是官方 Ibex/后续扩展方向 |
| Regression guard | `ProgramFile` 选择 `.vmem`，`TimeoutCycles=2000` | directed program 作为真实指令流激励，防止 hang 住 |

## DUT / RTL 结构

本地 RTL baseline 使用 Ibex 的 `examples/simple_system` wrapper。这个 wrapper 把 Ibex core 放在一个最小系统里，便于直接加载程序并运行。

```text
simple_system testbench
  └── ibex_simple_system
        ├── ibex_top / ibex_core
        │     ├── IF stage / prefetch / compressed decoder
        │     ├── ID stage / decoder / register file
        │     ├── EX block / ALU / mult-div
        │     ├── load-store unit
        │     ├── controller / CSR
        │     └── WB stage / tracer
        ├── RAM
        ├── timer
        └── simulator_ctrl
```

当前 testbench 中 Ibex 配置为：

```systemverilog
ibex_simple_system #(
  .RV32M(ibex_pkg::RV32MFast),
  .RV32B(ibex_pkg::RV32BNone),
  .RV32ZC(ibex_pkg::RV32Zca),
  .RegFile(ibex_pkg::RegFileFF),
  .SRAMInitFile(ProgramFile)
) dut (...);
```

| 配置项 | 选择 | 作用 |
| --- | --- | --- |
| `RV32MFast` | 快速乘除法实现 | 支持 RV32M multiply/divide 类指令 |
| `RV32BNone` | 关闭 bitmanip | 避免本地旧 RISC-V GCC/assembler 不支持 B/Zb 扩展 |
| `RV32Zca` | 支持 compressed 基础子集 | 覆盖 compressed decode 路径 |
| `RegFileFF` | FF register file | 仿真和移植最直接 |
| `SRAMInitFile` | 从 `.vmem` 初始化 RAM | directed program 作为激励源 |

## 本地 RTL Testbench

本地 RTL testbench 文件：

```text
rtl_tb/simple_system_smoke_tb.sv
rtl_tb/ibex_simple_system_files.f
```

`simple_system_tb_base` 是公共 testbench base，通过参数 `ProgramFile` 选择不同 `.vmem` 程序：

```systemverilog
module simple_system_tb_base #(
  parameter string ProgramFile = "programs/smoke.vmem"
);
  localparam int unsigned TimeoutCycles = 2000;

  logic io_clk;
  logic io_rst_n;

  ibex_simple_system #(
    .SRAMInitFile(ProgramFile)
  ) dut (...);

  initial begin
    repeat (TimeoutCycles) @(posedge dut.clk_sys);
    $fatal(1, "Timeout: %s did not request simulation finish", ProgramFile);
  end
endmodule
```

然后派生出多个 directed test top：

```systemverilog
module simple_system_smoke_tb;
  simple_system_tb_base #(.ProgramFile("programs/smoke.vmem")) tb();
endmodule

module simple_system_alu_tb;
  simple_system_tb_base #(.ProgramFile("programs/alu_directed.vmem")) tb();
endmodule
```

这个结构的好处：

- 同一个 DUT/testbench base 可以复用。
- 每个 test 只通过 `ProgramFile` 替换激励。
- timeout 统一放在 base testbench，防止程序跑飞或没有写 halt register 时仿真挂死。

## 激励如何发送

当前可运行 baseline 的激励不是 pin-level driver 直接打信号，而是 **software-driven stimulus**：

1. 手写小型 RISC-V 程序。
2. 汇编/转成 `.vmem` 或直接维护 `.vmem`。
3. testbench 通过 `SRAMInitFile` 把程序加载到 Ibex simple_system RAM。
4. reset 释放后，Ibex 从 boot address 开始取指执行。
5. 程序通过普通 load/store/branch/ALU 指令刺激 core 内部 pipeline、LSU、register file、branch path 和 memory system。
6. 程序结束时写 simulator control halt register，作为 pass/end-of-test 事件。

例如 `smoke.vmem` 的意图是：

```text
lui   x1, 0x20        // simulator control base
addi  x2, x0, 1       // x2 = 1
sw    x2, 8(x1)       // write halt bit
jal   x0, 0           // fallback loop if halt write fails
```

对应 `.vmem`：

```text
000200b7
00100113
0020a423
0000006f
```

当前 directed programs：

| 程序 | 主要激励 |
| --- | --- |
| `smoke.vmem` | boot、基本 addi/store、写 halt register |
| `alu_directed.vmem` | 简单整数运算，检查 ALU result 后 halt |
| `branch_directed.vmem` | taken loop branch，覆盖 branch path |
| `load_store_directed.vmem` | RAM store/load，覆盖 LSU 和 memory side effect |

这种激励方式更接近 CPU 验证常见模式：不是直接 force 内部信号，而是通过 instruction stream 让 core 自然执行，结果从 architectural state / memory side effect / halt 行为观察。

## 结果如何验证

当前 RTL baseline 的结果检查分三层：

### 1. End-of-test 检查

程序成功时会写 `simulator_ctrl` 的 halt register。Ibex simple_system 收到 halt 请求后结束仿真。若程序没有正确执行到 halt，testbench timeout：

```systemverilog
repeat (TimeoutCycles) @(posedge dut.clk_sys);
$fatal(1, "Timeout: %s did not request simulation finish", ProgramFile);
```

这能检查：

- core 是否正常取指。
- 程序是否跑到预期结束点。
- branch/load/store 是否没有导致程序跑飞。
- simulator control register 是否被正确写到。

### 2. Directed program 自检查

更复杂的 `.vmem` 程序在软件内部做 self-check：

- ALU test：计算结果与 expected value 比较。
- Branch test：通过 loop counter / branch path 确认 taken 行为。
- Load/store test：写 RAM 后再读回比较。

如果比较失败，程序不会写 halt register，而是进入 fallback loop，最终由 testbench timeout 报错。这样检查逻辑留在程序里，testbench 不需要知道每条指令的内部细节。

### 3. 后续 UVM scoreboard 目标

UVM scoreboard 规划检查更细粒度的 commit-level 信息：

| 检查项 | 说明 |
| --- | --- |
| PC | DUT commit PC 与 reference PC 一致 |
| GPR writeback | destination register index/value 与 reference model 一致 |
| Memory write | store address/data/byte enable 与预期一致 |
| Exception | illegal/misaligned/trap cause 与 reference 一致 |
| End state | 程序结束时 architectural state digest 一致 |

当前 scaffold 中 `ibex_scoreboard` 已有最小 PC compare 接口：

```systemverilog
function void write_commit(bit [31:0] dut_pc, bit [31:0] ref_pc);
  if (dut_pc !== ref_pc) begin
    `uvm_error(get_type_name(),
      $sformatf("PC mismatch: dut=0x%08x ref=0x%08x", dut_pc, ref_pc))
  end
endfunction
```

后续接 RVFI/commit monitor 后，这个接口会扩展成完整 commit item compare。

## UVM 结构

当前轻量 UVM scaffold 位于：

```text
uvm_tb/
  ibex_uvm_pkg.sv
  tb_top.sv
  env/
    ibex_env.sv
    ibex_scoreboard.sv
  seq/
    ibex_instr_item.sv
    ibex_smoke_seq.sv
  tests/
    ibex_base_test.sv
  cov/
    ibex_func_cov.sv
  ref/
    README.md
```

Package 统一 include：

```systemverilog
package ibex_uvm_pkg;
  import uvm_pkg::*;
  `include "uvm_macros.svh"

  `include "ibex_instr_item.sv"
  `include "ibex_smoke_seq.sv"
  `include "ibex_func_cov.sv"
  `include "ibex_scoreboard.sv"
  `include "ibex_env.sv"
  `include "ibex_base_test.sv"
endpackage
```

顶层：

```systemverilog
module tb_top;
  import uvm_pkg::*;
  import ibex_uvm_pkg::*;

  initial begin
    run_test("ibex_base_test");
  end
endmodule
```

### UVM 组件分工

| 组件 | 当前职责 | 后续扩展 |
| --- | --- | --- |
| `ibex_base_test` | 创建 env，控制 objection，证明 UVM scaffold 可运行 | 派生 smoke/alu/branch/load-store/random tests |
| `ibex_env` | 创建 scoreboard 和 functional coverage | 加 env_cfg、agent、virtual sequencer、reference model |
| `ibex_instr_item` | 描述一条 instruction stimulus：`instr_word` + `pc` | 扩展 opcode/rs/rd/imm/expected side effect |
| `ibex_smoke_seq` | 随机生成若干 instruction item | 后续生成 directed/random instruction stream 或 program image |
| `ibex_scoreboard` | 最小 PC compare 方法 | 扩展为 commit stream vs reference model compare |
| `ibex_func_cov` | 按 instruction opcode 采样 coverage | 加 cross coverage：instr type × operand corner × branch/load/store |

## UVM 激励怎么发

当前 `ibex_smoke_seq` 展示的是标准 UVM sequence/item 发送方式：

```systemverilog
repeat (16) begin
  item = ibex_instr_item::type_id::create("item");
  start_item(item);
  if (!item.randomize()) begin
    `uvm_error(get_type_name(), "Failed to randomize instruction item")
  end
  finish_item(item);
end
```

这个模式对应真实环境中的两种扩展方向：

### 方向 A：Instruction item -> program image

sequence 随机/定向生成 `ibex_instr_item`，再由 program builder 写入 memory image：

```text
ibex_smoke_seq
  -> ibex_instr_item stream
  -> program/memory image builder
  -> RAM preload
  -> Ibex executes instruction stream
```

优点：

- 适合 CPU verification。
- 激励通过真实 instruction stream 进入 DUT。
- 比 pin-level force 更接近真实软件执行场景。

### 方向 B：Virtual sequence 控制场景

后续 virtual sequence 不直接操作内部 RTL，而是协调：

- 选择 directed program 或随机 instruction stream。
- 初始化 memory。
- 配置 reset / timeout / end condition。
- 启动 reference model。
- 等待 halt / commit count / timeout。
- 收集 scoreboard 和 coverage 结果。

目标结构：

```text
ibex_base_vseq
  ├── load_program("alu_directed.vmem")
  ├── start_reference_model()
  ├── release_reset()
  ├── wait_for_halt_or_timeout()
  └── check_scoreboard()
```

## Monitor / Scoreboard 怎么验证结果

后续接 DUT 后，推荐使用 commit/RVFI monitor，而不是只看 pin-level bus：

```text
DUT commit/RVFI signals
  -> rvfi_monitor
  -> ibex_commit_item
  -> scoreboard
  -> compare with reference model / ISS
```

一个 commit item 应包含：

| 字段 | 作用 |
| --- | --- |
| `pc_rdata` / `pc_wdata` | 检查 PC progression 和 branch/jump target |
| `instr` | coverage 分类和 reference decode |
| `rd_addr` / `rd_wdata` | 检查 GPR writeback |
| `mem_addr` / `mem_wdata` / `mem_rdata` / `mem_wmask` | 检查 load/store side effect |
| `trap` / `exception cause` | 检查 illegal/misaligned/interrupt/trap |
| `order` | 确保 commit order 单调递增 |

Scoreboard 检查流程：

```text
rvfi_monitor.write(commit_item)
  -> scoreboard receives DUT commit
  -> reference model steps one instruction
  -> compare PC / rd write / memory / trap
  -> report UVM_ERROR on mismatch
```

对 directed program，也可以做 end-state compare：

```text
program finishes
  -> read final architectural digest
  -> compare expected register/memory values
  -> no mismatch and halt reached = PASS
```

## Functional Coverage

当前 `ibex_func_cov` 已经按 opcode 做基础分类：

```systemverilog
covergroup instr_cg;
  opcode_cp: coverpoint opcode {
    bins alu_reg = {7'b0110011};
    bins alu_imm = {7'b0010011};
    bins load    = {7'b0000011};
    bins store   = {7'b0100011};
    bins branch  = {7'b1100011};
    bins jal     = {7'b1101111};
    bins jalr    = {7'b1100111};
  }
endgroup
```

后续 coverage plan：

| Coverage | Bins |
| --- | --- |
| Instruction group | ALU reg/imm、load、store、branch、JAL、JALR、CSR、M extension |
| Operand corner | zero、all ones、sign bit、same rs/rd、x0 source/destination |
| Branch behavior | taken/not taken、forward/backward target、back-to-back branch |
| Load/store | byte/half/word、signed/unsigned、aligned/misaligned、same-address RAW |
| Pipeline event | stall、flush、branch redirect、exception flush |
| End condition | normal halt、timeout、expected trap |

Coverage subscriber 接收 monitor 发来的 instruction/commit item，不应该直接从 sequence 采样。这样 coverage 反映的是 DUT 实际执行过的指令，而不是“曾经生成过”的指令。

## Reference Model 策略

项目可以分阶段实现 reference checking：

### Phase 1：Directed self-check

程序内部做 expected result compare，失败则不 halt，testbench timeout 报错。

适合 smoke bring-up，简单稳定。

### Phase 2：轻量 SV reference model

只实现项目覆盖范围内的 RV32I/M/C 子集：

- PC 更新。
- GPR writeback。
- load/store memory side effect。
- branch/jump target。
- illegal/misaligned trap。

适合面试项目，因为能讲清楚 scoreboard 如何比对。

### Phase 3：Spike / ISS compare

用 Spike commit log 或 DPI cosim 做 golden model：

- riscv-dv 生成随机程序。
- RTL 和 Spike 执行同一 binary。
- scoreboard/checker 比较 commit trace。

适合扩展到官方 `core_ibex` flow，但工具链依赖更重。

## 当前已实现与待完善

| 模块 | 当前状态 | 后续完善 |
| --- | --- | --- |
| RTL directed regression | 已有 smoke/ALU/branch/load-store `.vmem` 和 Makefile target | 增加 multiply/divide、CSR、exception directed programs |
| UVM package/test/env | 已有最小 scaffold，可 compile/run | 加 env_cfg、agent、virtual sequencer |
| Sequence/item | 已有 `ibex_instr_item` 和 `ibex_smoke_seq` | 让 sequence 生成合法 instruction/program image |
| Scoreboard | 已有 PC compare 方法 | 接 commit monitor，扩展 GPR/memory/trap compare |
| Coverage | 已有 opcode covergroup | 从 monitor 采样并增加 cross coverage |
| Reference model | 规划中 | 先做轻量 SV model，再接 Spike |

## 面试讲法

中文：

这个项目我把 Ibex 放在一个最小 simple_system 里验证。RTL 结构上，DUT 包含 Ibex core、RAM、timer 和 simulator control。激励不是直接 force 内部信号，而是用 `.vmem` 预加载 RISC-V directed program，让 core 通过真实取指执行来刺激 ALU、branch、load/store 和 memory path。结果检查分两层：程序内部做 self-check，成功后写 simulator control halt register；如果没有写 halt，testbench timeout 报错。UVM 方面，我搭了一个轻量 scaffold，包括 base test、env、instruction item、sequence、scoreboard 和 functional coverage。sequence 通过标准 `start_item/randomize/finish_item` 生成 instruction item，后续会转成 program image 或由 virtual sequence 控制 memory preload。scoreboard 规划从 RVFI/commit monitor 接收 commit item，与 reference model 比较 PC、寄存器写回、memory side effect 和 exception。coverage 现在先按 opcode 分类，后续从实际 commit stream 采样 instruction type、operand corner、branch taken、load/store alignment 和 flush/stall。

English:

In this project, I verified the lowRISC Ibex core in a minimal simple_system setup. The RTL baseline instantiates the Ibex core together with RAM, a timer, and a simulator-control block. Instead of forcing internal signals, I use software-driven stimulus: directed RISC-V programs are preloaded as VMEM images, and the core naturally fetches and executes them. The directed programs check ALU, branch, and load/store behavior internally and write the simulator halt register on success; otherwise the testbench timeout reports a failure.

On the UVM side, I built a lightweight scaffold with a base test, environment, instruction sequence item, smoke sequence, scoreboard, and functional coverage collector. The sequence uses the standard `start_item`, `randomize`, and `finish_item` flow to generate instruction items. The next step is to convert these items into program images or drive them through a virtual sequence that controls memory preload and reset. The scoreboard is intended to consume commit/RVFI monitor items and compare PC, register writeback, memory side effects, and exceptions against a reference model or ISS. Coverage is collected from executed instruction items, starting with opcode bins and later extending to operand corners, branch behavior, load/store alignment, stalls, and flushes.

## 可追问点

- 为什么 CPU 验证更适合 instruction-stream stimulus，而不是 pin-level force。
- `.vmem` directed program 如何作为激励进入 DUT。
- 程序 self-check 和 scoreboard check 的区别。
- 为什么 coverage 应该从 monitor/commit stream 采样，而不是从 sequence 采样。
- RVFI/commit monitor 需要采哪些字段。
- Scoreboard 如何比较 PC、GPR writeback 和 memory side effect。
- 为什么先做 simple_system baseline，再扩展到官方 UVM/riscv-dv/Spike flow。

## 简历 bullets

- Built a runnable Ibex RV32IMC simple_system verification baseline using directed VMEM programs for smoke, ALU, branch, and load/store scenarios.
- Structured a lightweight UVM environment with base test, environment, instruction sequence item, sequence, scoreboard, and opcode functional coverage.
- Used software-driven instruction-stream stimulus instead of direct internal forcing, allowing the DUT to exercise fetch, decode, execute, branch, load/store, and memory paths naturally.
- Planned commit/RVFI-based scoreboard checking for PC, register writeback, memory side effects, exceptions, and end-of-test architectural state.
- Defined a phased verification strategy from directed self-checking programs to UVM monitor-based checking and later ISS/Spike comparison.
