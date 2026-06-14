# OoO RISC-V 处理器项目 - 详细技术实现

## 项目概述

这是一个可综合的 out-of-order RISC-V 处理器项目，工程路径为：

`C:\Users\28724\Desktop\master\project\OoO`

设计目标是在 `rv32im` 指令子集上实现 3-wide frontend / dispatch / retire 的乱序执行处理器，并在 100 ns 级 memory latency 下通过 cache、store queue、MSHR 和 branch recovery 保持正确性与性能。

## 顶层架构

```text
Unified memory
  <-> mem_controller
        <-> I-cache / fetch / branch predictor
        <-> D-cache / SQ / load-store units

Frontend
  branch_predictor -> icache_prefetch -> fetch -> IF/D register

Rename / Allocate
  dispatch -> freelist -> map_table -> ROB -> RS -> SQ

Out-of-order Execute
  RS -> issue FIFO -> physical_regfile -> fu_all
      -> 3x ALU
      -> 2x MUL
      -> 2x Load/Store
      -> 1x Branch

Complete / Commit
  FU result -> complete_stage -> CDB wakeup/writeback -> ROB
  ROB head -> retire_stage -> AMT/freelist/SQ/D-cache
```

Lane convention in this project is `[2] = oldest`, `[0] = youngest`.

<a id="ooo-project-parameters"></a>
## 关键参数

| 参数 | 值 | 含义 |
| --- | --- | --- |
| `XLEN` | 32 | RV32 datapath |
| Dispatch / commit width | 3 | 每周期最多 dispatch / complete / retire 3 条 |
| `PR` | 6 | physical register index width，最多 64 个 physical registers |
| `ROBW` | 32 | ROB entries |
| `RSW` | 16 | reservation station entries |
| `LSQ` | 3 | store queue index width，8 entries |
| `MHSRS_W` | 8 | D-cache MSHR entries |
| `IS_FIFO_DEPTH` | 32 | per-FU issue FIFO depth |
| `BPW` | 32 | branch predictor table entries |
| FU layout | 8 FUs | 3 ALU + 2 LS + 2 MUL + 1 branch |
| `NUM_MEM_TAGS` | 15 | memory outstanding/tag tracking capacity |
| Unified memory size | `64*1024` bytes | test memory model size |
| Memory latency | `(100.0 / CLOCK_PERIOD + 0.49999)` cycles | project memory model latency rounded to cycles |

## 关键 RTL 文件

| 文件 | 作用 |
| --- | --- |
| `verilog/pipeline.sv` | 顶层连线，串起 frontend、rename、schedule、execute、complete、retire 和 cache |
| `verilog/dispatch.sv` | decode、rename input、ROB/RS/SQ allocation |
| `verilog/freelist.sv` | physical register allocation/free 和 branch recovery head 恢复 |
| `verilog/map_table.sv` | speculative AR -> PR 映射、ready bit、CDB wakeup |
| `verilog/arch_maptable.sv` | retired architectural map，用于 precise recovery |
| `verilog/rob.sv` | in-order commit、precise state、store retirement gating |
| `verilog/rs.sv` | operand wakeup、oldest-ready selection、FU FIFO backpressure |
| `verilog/issue.sv` / `issue_fifo.sv` | issue queue 和 PRF read index 生成 |
| `verilog/physical_regfile.sv` | physical register file，多读写端口服务 3-wide pipeline |
| `verilog/sq.sv` | store queue、load-store ordering、byte-granular forwarding |
| `verilog/dcache.sv` | nonblocking D-cache、3-way cache memory、MSHR、dirty writeback |
| `verilog/branch_predictor.sv` | BTB/type table、gshare counters、return-address stack |
| `test/pipeline_test.sv` | program-level testbench、writeback log、diagnostic snapshot |

## Rename / ROB / Precise Commit

这个设计用 physical register renaming 消除 WAW/WAR 假相关：

1. Dispatch 阶段从 freelist 为目的寄存器分配新 PR。
2. Map table 返回源寄存器当前 PR、ready bit 和旧 PR（`Told`）。
3. ROB 保存 in-flight instruction 的目的 AR、新 PR、旧 PR、store/branch metadata。
4. Complete stage 通过 CDB 广播完成的 PR tag 和 value。
5. Retire stage 只从 ROB head 开始按序提交，更新 architectural map，并把旧 PR 释放回 freelist。

关键点是“乱序执行，按序提交”。即使 younger instruction 先执行完，也必须等 older ROB entry 完成后才能 commit。这样才能支持 precise exception 和 branch recovery。

## Reservation Station / Issue

RS 接收最多 3 条 renamed instructions，并维护每个 entry 的：

- 源 PR tag
- operand ready bit
- ROB index
- FU type
- SQ tail position

Wakeup 通过 CDB 组合匹配完成：

```systemverilog
match_cdb = (pr == cdb.t0) || (pr == cdb.t1) || (pr == cdb.t2);
```

RS 每周期从 ready entries 中选择最多 3 条 oldest-ready instruction，同时检查：

- 目标 FU FIFO 是否可接受新 packet。
- Load 是否已经满足 `load_tail_ready`，避免越过地址未解析的 older stores。
- ROB index wraparound 下的 age 比较。

这个设计把“是否 ready”和“是否能进入对应 FU FIFO”分开，便于 debug structural stall 和 data dependency stall。

## Store Queue / Load Forwarding

SQ 是这个 OoO 项目的关键正确性结构之一。它负责：

- Dispatch 时为 store/load 分配 SQ tail position。
- Store execute 后写入地址、数据和 byte mask。
- Retire 时按 program order 把 store 送入 D-cache。
- Load 查询所有 older stores，判断是否要 stall 或 forwarding。

比较重要的实现点：

- 如果存在 older store address 未解析，load 必须 stall。
- 如果 older store 地址匹配，按 byte mask 做 byte-granular forwarding。
- SQ retirement 按 lane `[2] -> [1] -> [0]` 的 program order 处理。
- `load_tail_ready` 回传给 RS，阻止 load 在 memory dependency 不安全时 issue。

## D-cache / MSHR

D-cache 是 nonblocking wrapper，支持：

- 两路 load request。
- 三路 retiring store。
- 3-way set-associative cache memory。
- MSHR queue 追踪 miss。
- dirty victim writeback。
- store miss 合并到同一 dirty MSHR。
- branch recovery 时丢弃 speculative clean load MSHR，但保留不能丢的 store/dirty state。

访存路径的一个核心 trade-off 是：store 已经 commit 后不能被 branch recovery 丢掉；但是 wrong-path speculative load miss 可以被清理。这个项目在 `dcache.sv` 的 recovery logic 里对 MSHR 做 compact/drop 分类，避免 recovery 破坏已经退休的 store。

## Branch Prediction / Recovery

Branch predictor 由三部分组成：

- PC-indexed BTB / type table，记录 target 和指令类型。
- gshare-style PHT，使用 `word_PC_index xor global_history`。
- lightweight RAS，用于 call/return prediction。

Branch FU 在分支解析后更新 predictor；如果发现需要 precise recovery，信息通过 complete/ROB 到 retire stage，再触发：

- fetch PC redirect
- IF/D flush
- map table 恢复到 architectural map
- freelist head 恢复
- RS / issue FIFO / FU / SQ flush
- D-cache MSHR speculative clean load 清理

这个路径体现了 OoO 设计中最重要的正确性原则：恢复点必须和按序退休的 precise architectural state 对齐。

## 验证与调试

项目包含两类验证：

| 类型 | 文件/脚本 | 目的 |
| --- | --- | --- |
| Module testbench | `test/rob_test.sv`, `test/tb_rs_issue_fifo_1way.sv`, `test/mult_test.sv` | 单模块功能检查和覆盖率 |
| Program-level testbench | `test/pipeline_test.sv` | 跑 `programs/*.s` / `programs/*.c`，生成 `.out`、`.wb`、`.ppln` |
| Golden compare | `run_all_program.sh`, `python/comp.py` | 对比 P4 RTL 输出与 P3 golden `.wb` / `.out` |
| Latency sweep | `run_latency_sweep.sh` | 改 `MEM_LATENCY_IN_CYCLES`，观察 regression 通过情况 |
| Matrix stress | `run_matrix_mult_rec_latency_sweep.sh` | 专门扫 `matrix_mult_rec` 在不同 memory latency 下的行为 |
| Diagnostic logs | `+DIAG=...`, `+LS_DEBUG`, `+RETIRE_DEBUG`, `+FETCH_DEBUG` | 定位 no-retire、LS、fetch、retire stall |

`pipeline_test.sv` 里有 minimal / deep diagnostic snapshot：当长时间 no retire 或出现 timeout 时，会打印 frontend、ROB、RS、SQ、D-cache/MSHR、commit 和 recovery 状态。这对 OoO debug 很关键，因为单看 waveform 很容易被并行状态淹没。

## 综合结果

已有 `synth/pipeline.rep` 显示：

| 指标 | 结果 |
| --- | --- |
| Library | ASAP7 `asap7sc7p5t_merged_RVT_FF_nldm_211120` |
| Clock period | `9800 ps` |
| Number of cells | `499343` |
| Sequential cells | `58879` |
| Total cell area | `57442.064671` |
| Timing | worst reported slack `MET 0.20 ps` |

这说明该 RTL 不只是行为仿真模型，而是按项目 flow 走过 Design Compiler synthesis，并生成了 gate-level netlist / timing / area report。

## 常见面试追问

### 1. 这个 OoO core 为什么需要 ROB？

ROB 让执行可以乱序，但 commit 必须按 program order。它记录每条 in-flight 指令的 destination、旧 physical register、完成状态、store/branch metadata。只有 ROB head 完成后才能退休，这样 branch mispredict 或 exception 时可以丢掉 younger instructions，并恢复 architectural map 和 freelist。

### 2. Rename 如何消除 WAW/WAR？

每次写 architectural register 时分配新的 physical register。后续读这个 AR 会读到最新 PR；旧 PR 只有等覆盖它的 instruction commit 后才释放。这样不同写者不会争同一个 architectural register storage，WAW/WAR 变成 PR 生命周期管理问题。

### 3. Load 为什么不能随便越过 store？

如果 older store 地址还没算出来，younger load 不知道是否同地址，必须等待。若地址已知且匹配，load 可以从 SQ forwarding；若不匹配，load 才能访问 D-cache。这个项目用 `load_tail_ready` 和 byte-granular forwarding 处理这个约束。

### 4. Branch recovery 怎么保证 precise state？

Recovery 由 retired/precise side 触发，而不是随便在 branch FU 处直接全局改状态。恢复时 map table 回到 architectural map，freelist 回到正确 head，ROB/RS/issue/FU/SQ 清空 speculative state，fetch redirect 到正确 PC，D-cache 只丢 wrong-path clean load MSHR。

### 5. Debug OoO hang 的方法？

先看是否 no-retire，再沿 ROB head 追：head 是否 completed、是否被 store/SQ/cache stall、RS 是否有 ready entry、FU FIFO 是否 backpressure、CDB 是否广播、branch recovery 是否反复 flush。这个项目 testbench 的 deep diagnostic snapshot 正是按这个方向组织的。

## 面试版英文回答

I implemented a synthesizable out-of-order RISC-V processor. The core is three-wide at fetch, dispatch, completion, and retirement. It uses register renaming with a freelist and map table, a 32-entry ROB for in-order commit, a 16-entry reservation station for oldest-ready issue, a physical register file, and eight functional units: three ALUs, two load/store units, two multipliers, and one branch unit.

One important part of the project was maintaining precise state. Instructions can execute out of order, but the ROB commits them in program order. On branch recovery, the frontend is redirected, the speculative map table is restored from the architectural map, the freelist head is recovered, and speculative structures such as the RS, issue queues, FUs, and SQ are flushed. For memory ordering, I implemented a store queue with byte-granular store-to-load forwarding and load stalling when older store addresses are unresolved.

The cache system includes an instruction cache, a nonblocking data cache, MSHRs, dirty writeback, and store-miss merging. I also built program-level regression scripts that compare writeback traces and output files against golden references, plus diagnostic logging for no-retire and pipeline hang debugging. The design was synthesized with the ASAP7 flow; the pipeline report shows timing met at a 9800 ps clock period with about 57.4k total cell area.

## 可直接放简历的 bullets

- Implemented a synthesizable 3-wide out-of-order RV32IM processor with register renaming, freelist/map table, 32-entry ROB, 16-entry reservation station, physical register file, and in-order precise commit.
- Designed memory-ordering logic with an 8-entry store queue, byte-granular store-to-load forwarding, unresolved-store load stalling, and ordered retiring stores into a nonblocking D-cache.
- Built a nonblocking cache subsystem with I-cache, 3-way D-cache, MSHRs, dirty writeback, store-miss merging, and branch-recovery-aware speculative load cleanup.
- Developed program-level regression and debug infrastructure comparing `.wb` / `.out` traces against golden outputs, with focused diagnostic logs for ROB/RS/SQ/cache/recovery stalls.
- Synthesized the full pipeline using an ASAP7 Design Compiler flow; timing met at a 9800 ps clock period with total cell area around 57.4k.
