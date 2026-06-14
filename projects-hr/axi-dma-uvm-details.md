# AXI DMA UVM 验证项目 - 详细技术实现

## 项目概述

这是一个完整的AXI DMA控制器UVM验证环境，基于开源`aignacio/axi_dma` RTL设计。项目验证了AXI-Lite CSR编程、AXI4主设备数据搬移、descriptor-based传输、中断处理、错误注入和abort功能。

<a id="axi-dma-project-parameters"></a>
## 项目关键参数

| 类别 | 当前工程参数 | 面试讲法 |
| --- | --- | --- |
| AXI 地址 / 数据 / ID | `AXI_ADDR_WIDTH=32`，`AXI_DATA_WIDTH=32`，`AXI_TXN_ID_WIDTH=8` | 32-bit AXI4 memory datapath，8-bit transaction ID |
| AXI burst length | `AXI_ALEN_WIDTH=8`，CSR `DMA_CONTROL.max_burst[9:2]` 默认 `8'hff` | `max_burst` 配的是 AXI `ALEN`；`8'hff` 等价最大 256 beats，`8'h00` 是 single-beat |
| 支持 burst 类型 | sequence/item 约束覆盖 `AXI_INCR`、`AXI_FIXED` | 验证侧覆盖 incrementing 和 fixed burst；wrap burst 不是当前项目主线 |
| Outstanding window | `DMA_RD_TXN_BUFF=8`，`DMA_WR_TXN_BUFF=8` | DMA master 最多允许 8 个 read 和 8 个 write outstanding；scoreboard 覆盖 depth 1、2-3、4-7、8 |
| Descriptor / FIFO | `DMA_NUM_DESC=2`，`DMA_FIFO_DEPTH=16`，`DMA_BYTES_WIDTH=32` | 两个 descriptor slot，stream FIFO 16 deep，byte count 字段 32 bit |
| 边界与异常 | `DMA_EN_UNALIGNED=1`，`DMA_MAX_BURST_EN=1`，timeout `16383` | 覆盖 unaligned transfer、4KB boundary split、backpressure、SLVERR/DECERR、abort |

## 页内目录

- [项目关键参数](#axi-dma-project-parameters)
- [验证环境架构](#验证环境架构)
- [RAL / Memory Model / Scoreboard 深入实现](#axi-dma-ral-mem-scoreboard)
  - [寄存器模型 RAL 具体实现](#axi-dma-ral-model)
  - [Memory model 具体实现](#axi-dma-memory-model)
  - [Scoreboard 如何检查](#axi-dma-scoreboard-checks)
- [关键技术实现](#关键技术实现)
- [测试用例实现](#测试用例实现)
- [Regression Debug 与 Coverage Closure 实战](#regression-debug-与-coverage-closure-实战)
- [芯动科技验证面试追问复盘](#axi-dma-innosilicon-followups)

## 验证环境架构

### 目录结构
```
axi_dma_uvm_verification/
├── rtl/                    # DUT RTL代码
│   ├── dma_core/          # 核心DMA控制器
│   ├── csr/              # 控制状态寄存器
│   └── bus/              # AXI总线接口
├── uvm/                   # UVM验证环境
│   ├── interfaces/       # 接口定义
│   ├── src/             # UVM组件
│   │   ├── agents/      # 代理组件
│   │   ├── env/         # 环境组件
│   │   ├── ral/         # 寄存器抽象层
│   │   └── sequences/   # 序列
│   └── top/             # 顶层testbench
├── docs/                 # 文档
└── sim/                 # 仿真脚本
```

### UVM组件详解

#### 1. 接口定义
- `dma_axil_if.sv`: AXI-Lite接口，用于CSR编程
- `dma_axi_mem_if.sv`: AXI4接口，用于DMA数据搬移
- `dma_irq_if.sv`: 中断接口

#### 2. 代理组件
- **AXI-Lite Master Agent** (`dma_axil_agent.svh`)
  - 用于CSR寄存器编程
  - 支持RAL frontdoor访问
  - 包含driver、monitor、sequencer

- **AXI Memory Slave Agent** (`dma_axi_mem_agent.svh`)
  - 作为AXI slave响应DMA读写请求
  - 支持可配置的ready delay和response delay
  - 支持error response注入

#### 3. 寄存器抽象层
- `dma_ral_pkg.svh`: 完整的DMA寄存器模型，详细见 [RAL 具体实现](#axi-dma-ral-model)
- `dma_reg_adapter.svh`: 寄存器适配器
- 支持 explicit predictor，通过 AXI-Lite monitor 的 analysis port 更新 RAL mirror

#### 4. 内存模型
- `dma_memory_model.svh`: 共享 byte-addressable memory model，详细见 [Memory model 具体实现](#axi-dma-memory-model)
- 支持preload、readback、数据比对
- 提供`fill_incrementing()`、`check_copy()`等实用方法

#### 5. 环境组件
- `dma_env.svh`: 顶层验证环境
- `dma_scoreboard.svh`: 记分板，检查 CSR readback、数据完整性、error response 和 outstanding，详细见 [Scoreboard 如何检查](#axi-dma-scoreboard-checks)
- `dma_virtual_sequencer.svh`: 虚拟序列器，持有共享资源

<a id="axi-dma-ral-mem-scoreboard"></a>
## RAL / Memory Model / Scoreboard 深入实现

这一节是面试时最应该讲细的部分：这个项目不是只“有一个 scoreboard”，而是把 CSR 控制路径、AXI memory 数据路径和 error/outstanding 压力路径都接到了可自检的模型上。

### 总体连接图

```text
dma_base_test
  ├─ cfg.mem = dma_memory_model::create("mem")
  └─ cfg.ral = dma_ral_block::create("ral"); cfg.ral.build()

dma_env.build_phase()
  ├─ axil_agent  ← cfg.csr_vif
  ├─ mem_agent   ← cfg.mem_vif + cfg.mem + delay/resp config
  ├─ sb.mem      ← cfg.mem
  ├─ sb.allow_error_responses      ← cfg.allow_error_responses
  ├─ sb.require_full_outstanding   ← cfg.check_full_outstanding
  ├─ vseqr.mem / vseqr.ral / vseqr.irq_vif ← cfg resources
  └─ reg_predictor + dma_reg_adapter

dma_env.connect_phase()
  ├─ cfg.ral.default_map.set_sequencer(axil_agent.sqr, reg_adapter)
  ├─ cfg.ral.default_map.set_auto_predict(0)
  ├─ axil_agent.mon.ap → reg_predictor.bus_in
  ├─ axil_agent.mon.ap → sb.axil_ap
  └─ mem_agent.mon.ap  → sb.mem_ap
```

解释口径：

- RAL 负责“test 如何通过真实 AXI-Lite frontdoor 编程 CSR”，并用 explicit predictor 保证 mirror 来自真实 bus monitor。
- Memory model 负责“AXI memory slave BFM 如何给 DUT 返回读数据、接收写数据”，同时给 vseq preload 和 scoreboard compare 提供同一个共享数据源。
- Scoreboard 负责“看到 CSR 写入后建立 expected copy，看到 DMA complete 后逐 byte 比较 destination memory，并对 error/outstanding 做语义检查”。

<a id="axi-dma-ral-model"></a>
### 寄存器模型 RAL 具体实现

源码位置：

- `uvm/src/ral/dma_ral_pkg.svh`
- `uvm/src/ral/dma_reg_adapter.svh`
- `uvm/src/env/dma_env.svh`
- `uvm/src/sequences/dma_vseqs.svh`

`dma_ral_block` 继承 `uvm_reg_block`，在 `build()` 中创建 little-endian CSR map：

```systemverilog
default_map = create_map("csr_map", 0, (`AXI_DATA_WIDTH/8), UVM_LITTLE_ENDIAN);
```

寄存器模型覆盖的主要 register/field：

| RAL class / field | CSR 含义 | Access |
| --- | --- | --- |
| `dma_control_reg.go` | 启动 DMA | RW |
| `dma_control_reg.abort` | abort 当前传输 | RW |
| `dma_control_reg.max_burst` | 限制 burst 长度 | RW |
| `dma_status_reg.version` | 固定版本号，reset value `16'hcafe` | RO |
| `dma_status_reg.done` | DMA 完成状态 | RO |
| `dma_status_reg.error` | DMA 错误状态 | RO |
| `dma_error_addr` | 错误地址 | RO |
| `dma_error_stats.error_type` | operation/configuration error 类型 | RO |
| `dma_error_stats.error_src` | read/write error 来源 | RO |
| `dma_error_stats.error_trig` | 是否触发过 error | RO |
| `dma_desc_src_addr[i]` | descriptor source address | RW |
| `dma_desc_dst_addr[i]` | descriptor destination address | RW |
| `dma_desc_num_bytes[i]` | descriptor byte count | RW |
| `dma_desc_cfg[i].write_mode/read_mode/enable` | write/read burst mode 和 descriptor enable | RW |

每个 descriptor 相关寄存器都用数组建模：

```systemverilog
for (int unsigned i = 0; i < DMA_NUM_DESC; i++) begin
  dma_desc_src_addr[i]   = dma_rw32_reg::type_id::create(...);
  dma_desc_dst_addr[i]   = dma_rw32_reg::type_id::create(...);
  dma_desc_num_bytes[i]  = dma_rw32_reg::type_id::create(...);
  dma_desc_cfg[i]        = dma_desc_cfg_reg::type_id::create(...);
  default_map.add_reg(dma_desc_src_addr[i],  DMA_DESC_SRC_ADDR_OFFSET[i],  "RW");
  default_map.add_reg(dma_desc_dst_addr[i],  DMA_DESC_DST_ADDR_OFFSET[i],  "RW");
  default_map.add_reg(dma_desc_num_bytes[i], DMA_DESC_NUM_BYTES_OFFSET[i], "RW");
  default_map.add_reg(dma_desc_cfg[i],       DMA_DESC_CFG_OFFSET[i],       "RW");
end
```

#### RAL frontdoor 访问链路

Virtual sequence 不直接手写 AXI-Lite pin-level transaction，而是先按地址找 RAL register，再走 `rg.write()` / `rg.read()`：

```systemverilog
rg = p_sequencer.ral.default_map.get_reg_by_offset(addr, is_read);
rg.write(status, value, UVM_FRONTDOOR, p_sequencer.ral.default_map, this);
rg.read(status, value, UVM_FRONTDOOR, p_sequencer.ral.default_map, this);
```

完整调用链是：

```text
dma_base_vseq.csr_write/csr_read()
  → csr_reg_by_addr(addr)
  → rg.write/read(... UVM_FRONTDOOR ...)
  → ral.default_map
  → dma_reg_adapter.reg2bus()
  → dma_axil_item
  → axil_agent.sqr / dma_axil_driver
  → dma_axil_if
  → DUT CSR AXI-Lite port
```

`dma_reg_adapter` 做两件事：

1. `reg2bus()`：把 `uvm_reg_bus_op` 转成 `dma_axil_item`，包括 `dir`、`addr`、`data`、`strb`。如果 byte enable 为 0，就 fallback 到全 strobe。
2. `bus2reg()`：把完成后的 `dma_axil_item` 转回 RAL operation，用 `tr.resp` 决定 `UVM_IS_OK` 或 `UVM_NOT_OK`。

这里 `provides_responses = 0` 是一个关键实现点：AXI-Lite driver 会在同一个 request item 里填回 `bresp/rresp` 和 read data，然后 `item_done()`；RAL adapter 直接消费这个完成后的 item，不需要单独 response queue。

#### 为什么用 explicit predictor

`dma_env.connect_phase()` 中关闭 auto prediction：

```systemverilog
cfg.ral.default_map.set_auto_predict(0);
reg_predictor.map     = cfg.ral.default_map;
reg_predictor.adapter = reg_adapter;
axil_agent.mon.ap.connect(reg_predictor.bus_in);
```

含义是：RAL mirror 不靠 sequence 发起操作时“假定成功”来更新，而是由 AXI-Lite monitor 观察到真实 bus transaction 后，经 `uvm_reg_predictor` 更新 mirror。这样更接近工业验证方式，因为 mirror 反映的是总线上真正发生的访问。

AXI-Lite monitor 也有两个细节：

- 写通道 AW 和 W 独立到达，所以 monitor 在 AW handshake latch `awaddr`，在 W handshake latch `wdata/wstrb`，到 B handshake 才发布完整 write transaction。
- 读通道在 AR handshake latch `araddr`，到 R handshake 时发布 read transaction，避免 master 在 R 返回前撤掉地址导致 monitor 读错。

<a id="axi-dma-memory-model"></a>
### Memory model 具体实现

源码位置：

- `uvm/src/common/dma_memory_model.svh`
- `uvm/src/agents/axi_memory/dma_axi_mem_driver.svh`
- `uvm/src/agents/axi_memory/dma_axi_mem_monitor.svh`
- `uvm/src/sequences/dma_vseqs.svh`

`dma_memory_model` 是一个 byte-addressable sparse memory，用关联数组实现：

```systemverilog
protected bit [7:0] mem[longint unsigned];
```

核心 API：

| API | 作用 |
| --- | --- |
| `clear()` | 清空所有已写地址 |
| `write_byte(addr, data)` / `read_byte(addr)` | byte 粒度读写；未写过的地址读 0 |
| `write_bus_word(addr, data, strb)` | 按 WSTRB 更新对应 byte lane |
| `read_bus_word(addr)` | 把连续 byte 拼成 AXI data word |
| `fill_incrementing(base_addr, num_bytes, seed)` | 给 source memory 预置递增 pattern |
| `compare_range(src, dst, num_bytes, mismatch)` | 简单 range compare helper |

这个 memory model 是共享实例，不是 driver/scoreboard 各自 new 一份：

```text
dma_base_test.build_phase()
  → cfg.mem = dma_memory_model::type_id::create("mem")

dma_env.build_phase()
  → mem_cfg.mem = cfg.mem
  → sb.mem = cfg.mem

dma_env.connect_phase()
  → vseqr.mem = cfg.mem
```

因此同一份 `cfg.mem` 同时被三类组件使用：

| 使用者 | 如何使用 |
| --- | --- |
| Virtual sequence | 在启动 DMA 前调用 `p_sequencer.mem.fill_incrementing(src_addr, num_bytes)` 预置 source bytes |
| AXI memory slave BFM | DUT 发 AXI read 时调用 `read_bus_word()` 返回 RDATA；DUT 发 AXI write 时调用 `write_bus_word()` 更新 memory |
| Scoreboard | DMA start 时从 source address snapshot expected bytes；DMA complete 时从 destination address 读出 got bytes |

AXI memory driver 是 slave BFM，不是主动 master。它只响应 DUT 作为 AXI master 发出的 AR/AW/W：

```systemverilog
// write data channel
cfg.mem.write_bus_word(beat_addr(req.addr, beat, req.size, req.burst),
                       vif.wdata, vif.wstrb);

// read response channel
vif.rdata <= cfg.mem.read_bus_word(beat_addr(req.addr, beat, req.size, req.burst));
```

`beat_addr()` 同时支持 INCR 和 FIXED burst：

```systemverilog
if (burst == AXI_FIXED) return base;
return base + (beat * bytes);
```

这就是为什么 memory model 必须是 byte-addressable：未对齐 transfer、小于 word 的 transfer、以及 WSTRB 局部写都不能用 32-bit word 粗略比较，否则容易把 byte lane bug 漏掉或误报。

<a id="axi-dma-scoreboard-checks"></a>
### Scoreboard 如何检查

源码位置：

- `uvm/src/env/dma_scoreboard.svh`
- `uvm/src/env/dma_env.svh`
- `uvm/src/agents/axi_lite/dma_axil_monitor.svh`
- `uvm/src/agents/axi_memory/dma_axi_mem_monitor.svh`

Scoreboard 有两个 analysis input：

```systemverilog
uvm_analysis_imp_mem  #(dma_axi_mem_item, dma_scoreboard) mem_ap;
uvm_analysis_imp_axil #(dma_axil_item,     dma_scoreboard) axil_ap;
```

连接关系：

```text
axil_agent.mon.ap → sb.axil_ap
mem_agent.mon.ap  → sb.mem_ap
```

#### 1. CSR shadow 和 readback 检查

`write_axil()` 每次收到 AXI-Lite monitor 发布的完整 transaction：

- 如果是 write：更新 scoreboard 本地 shadow。
- 如果是 read：根据 shadow 计算 expected readback，并和实际 `tr.data` 比较。

本地 shadow 包括：

```systemverilog
protected dma_desc_state_s desc_state[DMA_NUM_DESC];
protected bit [31:0]       control_mirror;
```

`desc_state` 保存每个 descriptor 的 `src_addr`、`dst_addr`、`num_bytes`、`valid`、`rd_mode`、`wr_mode`。写寄存器时用 `apply_reg_wstrb()` 做 byte-enable 合并：

```systemverilog
merged = current;
for (int unsigned i = 0; i < 4; i++) begin
  if ((i < (`AXI_DATA_WIDTH/8)) && strb[i]) begin
    merged[i*8 +: 8] = data[i*8 +: 8];
  end
end
```

读寄存器时 `get_expected_axil_read()` 计算 expected：

- `DMA_CONTROL`：比对 `control_mirror`。
- `DMA_STATUS`：只 mask 低 16-bit version，expected `32'h0000_cafe`；done/error 另外做语义检查。
- descriptor register：从 `desc_state[desc]` 取 expected。

对状态寄存器还有额外语义检查：

- `check_status_read()`：error-response 场景下要求 `STATUS.error=1`；noop transfer 要求 done 且无 error；invalid config 要求 done 和 error 同时置位。
- `check_error_stats_read()`：检查 `ERROR_STATS.error_trig`、`error_type`、`error_src` 是否符合 config error 或 read/write AXI error。

#### 2. DMA copy expected 什么时候建立

Scoreboard 不是等传输结束才从 source 读 expected；它在看到 `DMA_CONTROL.go` 从 0 变 1 时建立 snapshot。

`handle_control_write()` 通过 control mirror 检测边沿：

```systemverilog
old_enable  = control_mirror[0];
new_control = apply_reg_wstrb(control_mirror, data, strb);
new_enable  = new_control[0];
abort       = new_control[1];

if (!old_enable && new_enable) begin
  start_transfer();
end

if (new_enable && abort) begin
  drop_expected_copies("DMA abort");
end
else if (old_enable && !new_enable) begin
  complete_transfer();
end
```

`start_transfer()` 做三件事：

1. 清掉 stale expected copy。
2. 检查是否存在 enabled zero-byte descriptor；如果有，标记 `invalid_cfg_transfer_active`，不建立普通 copy check。
3. 对每个 enabled 且 `num_bytes != 0` 的 descriptor 调 `queue_expected_copy(desc)`。

#### 3. 数据完整性如何逐 byte 检查

`queue_expected_copy()` 会把 source memory 的期望 byte snapshot 到 `dma_expected_copy` 里：

```systemverilog
copy.src_addr  = desc_state[desc].src_addr;
copy.dst_addr  = desc_state[desc].dst_addr;
copy.num_bytes = desc_state[desc].num_bytes;
copy.rd_mode   = desc_state[desc].rd_mode;
copy.wr_mode   = desc_state[desc].wr_mode;
```

然后对每个 byte 计算 source/destination byte address：

```systemverilog
src_byte_addr = copy.src_addr +
  ((copy.rd_mode == DMA_MODE_FIXED) ? (i % bytes_per_beat) : i);
dst_byte_addr = copy.dst_addr +
  ((copy.wr_mode == DMA_MODE_FIXED) ? (i % bytes_per_beat) : i);
```

如果是 FIXED mode，多个 byte/beat 可能落到同一个 destination byte lane；scoreboard 用 `find_dst_index()` 去重，同一 dst address 后来的 expected data 覆盖前面的 expected data，相当于模拟“最后一次写入 wins”。

DMA 完成时，vseq 会 `clear_dma()`，即写 `CONTROL.go=0`。scoreboard 看到 enable 下降沿后调用 `complete_transfer()`，再逐 byte 比较：

```systemverilog
got = mem.read_byte(copy.dst_addrs[i]);
if (got !== copy.exp_data[i]) begin
  `uvm_error(...)
end
```

这里的 `got` 来自同一个 shared memory model，而 memory model 的 destination 内容是在 DUT 真实 AXI write handshake 时由 memory slave BFM 写进去的。因此这个检查不是“sequence 自己写完自己读”，而是端到端验证：

```text
vseq preload source memory
  → RAL frontdoor program descriptor
  → DUT AXI master reads source through slave BFM
  → DUT AXI master writes destination through slave BFM
  → BFM updates shared memory model
  → scoreboard compares expected snapshot vs destination bytes
```

#### 4. Error response 时为什么不报 copy mismatch

`write_mem()` 接收 memory monitor 发布的 completed burst transaction。如果 `tr.resp != AXI_OKAY`：

- 记录 `observed_error_responses++`。
- 记录 `last_error_dir = tr.dir`，后面检查 `ERROR_STATS.error_src`。
- 如果当前 test 没有打开 `allow_error_responses`，直接 `uvm_error`。
- 如果 test 明确允许 error response，就调用 `drop_expected_copies("AXI error response")`。

这避免了一个常见误报：error path 下 DMA 本来就可能没有完成完整 copy，如果 scoreboard 继续检查 destination memory，就会把 expected error 测试误报成 data mismatch。

相关 test 配置：

| Test | 配置 | Scoreboard 行为 |
| --- | --- | --- |
| `error_response_test` | `cfg.allow_error_responses=1`, `cfg.default_read_resp=AXI_SLVERR` | 允许 read SLVERR，丢弃 pending copy，检查 STATUS/ERROR_STATS |
| `decerr_response_test` | `cfg.default_read_resp=AXI_DECERR` | 同上，覆盖 DECERR |
| `write_error_response_test` | `cfg.default_write_resp=AXI_SLVERR` | 允许 write SLVERR，检查 error source 为 write |
| `write_decerr_response_test` | `cfg.default_write_resp=AXI_DECERR` | 同上，覆盖 write DECERR |

#### 5. Outstanding 怎么统计和检查

AXI memory monitor 在 AR/AW accept 时维护 outstanding counter：

```systemverilog
rd_outstanding++;
tr.outstanding_after_accept = rd_outstanding;

wr_outstanding++;
tr.outstanding_after_accept = wr_outstanding;
```

等 RLAST/B response 完成后，monitor 把 transaction 通过 `ap.write(tr)` 送到 scoreboard，再递减 outstanding。

Scoreboard 在 `write_mem()` 里：

- 用 `outstanding_cg.sample(tr.dir, tr.outstanding_after_accept)` 采样 functional coverage。
- 更新 `max_read_outstanding` / `max_write_outstanding`。
- 如果 `require_full_outstanding` 打开，就在 complete/check phase 检查是否达到 `DMA_RD_TXN_BUFF` / `DMA_WR_TXN_BUFF`。

covergroup 是 read/write 方向和 depth 的 cross：

```systemverilog
direction_cp: coverpoint dir {
  bins read  = {AXI_MEM_READ};
  bins write = {AXI_MEM_WRITE};
}

depth_cp: coverpoint outstanding {
  bins one  = {1};
  bins low  = {[2:3]};
  bins high = {[4:7]};
  bins max  = {8};
}

direction_x_depth: cross direction_cp, depth_cp;
```

面试回答可以这样收束：

> 我的 scoreboard 有三条检查链路。第一条是 CSR shadow/readback：AXI-Lite monitor 把真实 CSR transaction 发给 scoreboard，scoreboard 用 WSTRB-aware mirror 检查 readback，并对 STATUS/ERROR_STATS 做语义检查。第二条是 DMA copy check：DMA start 时按 descriptor 从 shared memory model snapshot expected bytes，DMA complete 时逐 byte 比较 destination memory；这个 memory model 的内容来自 DUT 真实 AXI read/write handshake。第三条是 error/outstanding：memory monitor 上报每个 completed burst，scoreboard 记录非 OKAY response、决定是否丢弃 pending copy，并统计 read/write outstanding depth 和 coverage。

## 关键技术实现

### 1. Slave BFM设计
AXI memory slave agent的driver实现为slave BFM，关键特性：
```systemverilog
task dma_axi_mem_driver::run_phase(uvm_phase phase);
  forever begin
    vif.drive_slave_idle();
    wait (!vif.rst);

    fork
      write_address_channel();
      write_data_channel();
      write_response_channel();
      read_address_channel();
      read_response_channel();
      @(posedge vif.rst);
    join_any
    disable fork;
  end
endtask
```

### 2. Error Injection机制
通过`try_next_item()`实现非阻塞error注入：
```systemverilog
protected task automatic get_next_response(input  axi_resp_t default_resp,
                                           output axi_resp_t use_resp);
  dma_axi_mem_item req;

  seq_item_port.try_next_item(req);
  if (req != null) begin
    use_resp = req.resp;      // 有 error injection item 时使用它
    seq_item_port.item_done();
  end else begin
    use_resp = default_resp;  // 无 item 时 fallback 到 OKAY/默认响应
  end
endtask
```

### 3. 虚拟序列器资源共享
虚拟序列器持有所有关键资源引用：
```systemverilog
class dma_virtual_sequencer extends uvm_sequencer;
    // 子序列器
    dma_axil_sequencer axil_sqr;
    dma_axi_mem_sequencer mem_sqr;
    
    // 共享资源
    dma_memory_model mem;
    dma_ral_block ral;
    virtual dma_irq_if irq_vif;
    
    // 实用方法
    function void preload_memory(bit [31:0] base_addr, int size);
        mem.fill_incrementing(base_addr, size);
    endfunction
endclass
```

### 4. 中断等待超时保护
使用`fork/join_any + disable fork`防止仿真挂死：
```systemverilog
task wait_for_irq(output bit timed_out, input int timeout_cycles = 1000);
    fork
        begin: irq_wait
            @(posedge vif.irq);
            timed_out = 0;
        end
        
        begin: timeout
            #(timeout_cycles);
            timed_out = 1;
        end
    join_any
    disable fork;  // 确保只有一个分支执行
endtask
```

## 测试用例实现

### 1. CSR读写测试
```systemverilog
class csr_rw_test extends dma_base_test;
    task body();
        // 读取version寄存器
        uvm_reg_data_t version;
        ral.DMA_STATUS.mirror(status, UVM_CHECK);
        version = ral.DMA_STATUS.version.get();
        
        // 写入control寄存器
        ral.DMA_CONTROL.go.set(1'b1);
        ral.DMA_CONTROL.update(status);
    endtask
endclass
```

### 2. 单描述符传输测试
```systemverilog
class single_desc_transfer_test extends dma_base_test;
    task body();
        // 预加载源内存
        p_sequencer.mem.fill_incrementing(SRC_ADDR, TRANSFER_SIZE);
        
        // 编程描述符
        ral.DMA_DESC_SRC_ADDR[0].set(SRC_ADDR);
        ral.DMA_DESC_DST_ADDR[0].set(DST_ADDR);
        ral.DMA_DESC_NUM_BYTES[0].set(TRANSFER_SIZE);
        ral.DMA_DESC_CFG[0].enable.set(1'b1);
        ral.update(status);
        
        // 启动DMA
        ral.DMA_CONTROL.go.set(1'b1);
        ral.DMA_CONTROL.update(status);
        
        // 等待中断
        wait_for_irq(timed_out);
        
        // 数据检查由 scoreboard 根据 monitor transaction 和 memory model 自动完成
        // vseq 只负责配置、启动和等待 done/error。
    endtask
endclass
```

### 3. Burst Sweep测试
```systemverilog
class burst_sweep_transfer_test extends dma_base_test;
    task body();
        for (int burst = 0; burst <= 255; burst++) begin
            // 设置max_burst
            ral.DMA_CONTROL.max_burst.set(burst);
            ral.DMA_CONTROL.update(status);
            
            // 执行传输
            run_single_transfer();
            
            // 检查结果由 scoreboard/report phase 汇总；
            // vseq 负责覆盖不同 max_burst 配置。
        end
    endtask
endclass
```

### 4. 未对齐地址测试
```systemverilog
class unaligned_transfer_test extends dma_base_test;
    task body();
        bit [31:0] unaligned_addrs[] = '{1, 2, 3};
        foreach (unaligned_addrs[i]) begin
            // 设置未对齐地址
            src_addr = BASE_ADDR + unaligned_addrs[i];
            dst_addr = BASE_ADDR + 0x1000 + unaligned_addrs[i];
            
            // 执行传输
            run_transfer(src_addr, dst_addr);
            
            // 检查WSTRB正确性
            check_wstrb_pattern();
        end
    endtask
endclass
```

### 5. Outstanding压力测试
```systemverilog
class outstanding_stress_test extends dma_base_test;
    task body();
        // 配置最大response delay
        p_sequencer.mem_agent_cfg.max_resp_delay = 100;
        
        // 使用最小burst长度（1 beat）
        ral.DMA_CONTROL.max_burst.set(0);
        
        // 执行大尺寸传输，迫使outstanding窗口填满
        run_transfer(..., LARGE_SIZE);
        
        // outstanding 深度由 scoreboard/coverage 统计；
        // test 配置要求达到设计窗口时，在 scoreboard 中检查。
    endtask
endclass
```

## 覆盖率模型

### 功能覆盖率点
```systemverilog
covergroup dma_cg;
    // 描述符选择
    desc_sel: coverpoint desc_index {
        bins desc0 = {0};
        bins desc1 = {1};
        bins both  = {2};
    }
    
    // 传输大小
    xfer_size: coverpoint transfer_size {
        bins small     = {[1:16]};
        bins cacheline = {[17:64]};
        bins page      = {[65:4096]};
        bins large     = {[4097:65536]};
    }
    
    // 地址对齐
    alignment: coverpoint {src_addr[1:0], dst_addr[1:0]} {
        bins aligned     = {0};
        bins unaligned_1 = {1};
        bins unaligned_2 = {2};
        bins unaligned_3 = {3};
    }
    
    // AXI响应类型
    resp_type: coverpoint axi_resp {
        bins okay  = {AXI_OKAY};
        bins slverr = {AXI_SLVERR};
        bins decerr = {AXI_DECERR};
    }
    
    // Outstanding深度
    outstanding_depth: coverpoint outstanding_cnt {
        bins depth[9] = {[0:8]};
    }
    
    // Cross coverage
    outstanding_x_resp: cross outstanding_depth, resp_type;
    alignment_x_size: cross alignment, xfer_size;
endgroup
```

### 断言检查
```systemverilog
// AXI协议断言
property axi_valid_ready_handshake;
    @(posedge clk) disable iff (!rst_n)
    (valid && !ready) |=> valid until ready;
endproperty

assert_axi_handshake: assert property (axi_valid_ready_handshake);

// 中断断言
property irq_asserted_on_done;
    @(posedge clk) disable iff (!rst_n)
    (status_reg.done && !prev_done) |-> ##[1:2] irq;
endproperty

assert_irq_done: assert property (irq_asserted_on_done);
```

## 仿真流程

### 1. 编译DUT
```bash
# 使用Questa
vlog -work work +define+AXI_ADDR_WIDTH=32 +define+AXI_DATA_WIDTH=32 \
     -f sim/filelists/dut.f
```

### 2. 编译Testbench
```bash
vlog -work work -sv +incdir+$UVM_HOME/src $UVM_HOME/src/uvm_pkg.sv \
     -f sim/filelists/tb.f
```

### 3. 运行测试
```bash
# 运行CSR读写测试
vsim -c work.tb_top +UVM_TESTNAME=csr_rw_test -do "run -all; quit"

# 运行单描述符传输测试
vsim -c work.tb_top +UVM_TESTNAME=single_desc_transfer_test -do "run -all; quit"

# 运行回归测试
vsim -c work.tb_top +UVM_TESTNAME=regression_test -do "run -all; quit"
```

### 4. 覆盖率收集
```bash
# 启用覆盖率收集
vsim -c work.tb_top +UVM_TESTNAME=coverage_test -coverage -do "run -all; coverage save -onexit coverage.ucdb; quit"

# 生成覆盖率报告
vcover report -html coverage.ucdb -output coverage_report
```

## Regression Debug 与 Coverage Closure 实战

### 1. Bring-up 问题定位

早期 regression 的第一个问题不是编译错误，而是多个 test 在等待 DMA `done/error` interrupt 时 timeout。Debug 顺序是：

1. 先看 log 中的 first failure，而不是最后一个 error summary。
2. 确认 RAL frontdoor CSR write/read 都能返回 `UVM_IS_OK`，排除 AXI-Lite/RAL 路径卡死。
3. 再沿着 DMA start 后的 `go`、descriptor、AXI request、memory response、IRQ 状态往后 trace。
4. 区分 testbench 问题和 DUT 问题：如果是 response item/scoreboard policy 缺失，就修 UVM；如果是 DUT 没产生 expected error/done，就修 RTL。

### 2. Testbench 修复点

| 问题 | 修复方式 |
| --- | --- |
| 普通 sequence 和 virtual sequence 职责混在一起 | 普通 sequence 只在对应 agent sequencer 上产生 transaction；virtual sequence 负责 RAL 编程、reset/interrupt、普通 sequence 调度 |
| 已有 RAL 但 sequence 仍手写复杂 CSR transaction | CSR 编程统一走 RAL frontdoor，减少 hard-code address 和 mirror mismatch |
| AXI-Lite/RAL 曾经卡住 | driver 对每次 read/write 都产生 response item，adapter 用完成后的 item 填回 status/data |
| AXI memory slave 被误当作主动流量源 | memory agent driver 作为 slave BFM 响应 DUT master 请求；`try_next_item()` 只用于可选 error override |
| expected error 被 scoreboard 当失败 | error test 打开 `allow_error_responses`，分别覆盖 read/write SLVERR 和 DECERR |

### 3. RTL Bug 修复点

| Bug | Root cause | Fix |
| --- | --- | --- |
| invalid config 只 done 不 error | FSM 只判断是否存在 nonzero descriptor，没有把 enabled zero-byte descriptor 视为错误 | `dma_fsm` 增加 config error latch，并驱动 STATUS.error / ERROR_STATS |
| ERROR_STATS error type 编码反了 | enum 顺序和 register map 说明不一致 | 调整 `DMA_ERR_OPE` / `DMA_ERR_CFG` 编码 |
| `DMA_PROGRESS_TIMEOUT` 编译 undefined | Questa filelist 独立 compilation unit 下模块看不到宏 | 在 DUT filelist 中补 `+define+DMA_PROGRESS_TIMEOUT=16383` |
| 内部 FIFO overflow/underflow 没上报 | 多个 FIFO 的 `error_o` 悬空 | 将 internal FIFO error 汇总到 DMA error path |
| 首个 error 可能被后续 error 覆盖 | error latch 保护不完整 | `dma_error_ff.valid` 置位后保持，直到 clear |
| AXI/FIFO 卡住时只靠 UVM timeout | FSM 没有 progress watchdog | `dma_axi_if` 输出 progress pulse，`dma_fsm` 增加 watchdog timeout error |
| clear 后 tracking state 可能残留 | 内部 request/error FIFO 没接 clear | FIFO 和 pending counter/write lock/beat counter/sticky valid 在 clear 时复位 |

### 4. Coverage 结果与未到 100% 的原因

最新 Questa merged report：

| 指标 | 结果 |
| --- | --- |
| Total coverage | `91.98%` |
| Code-only filtered coverage | `88.44%` |
| Statement | `96.36%` |
| Branch | `96.25%` |
| FEC condition | `79.33%` |
| Toggle | `79.95%` |
| Covergroup / assertion | `100%` |

没有到 100% 的主要原因：

1. **FEC condition 是主短板**：剩余 hole 集中在 `progress_timeout`、`local_error_ff.valid`、`FIFO full`、`abort + rvalid + full`、`clear + AR/AW/W valid stall` 等组合。这些不是普通数据搬移自然会 hit 的路径。
2. **部分防御性路径需要极端协议时序**：例如 clear 当拍刚好遇到 AR/AW/W valid 且 ready stall，需要非常刻意的 slave delay 和 CSR clear 时序，不适合混入普通 passing regression。
3. **部分结构信号是常量或 tie-off**：AXI optional sideband、ID/user/prot/cache/qos/region、固定 size、对齐地址低位等不应该为了 toggle 而写非法 stimulus。
4. **合法配置已经挡住了某些错误组合**：例如 enabled zero-byte descriptor 已在 CFG 阶段报 config error，因此 RUN 阶段再覆盖 `num_bytes==0` 的条件接近不可达。
5. **FIFO overflow/underflow 属于 defensive error path**：正常约束下 BFM 不应该持续非法压垮内部 FIFO；如果要覆盖，应作为单独 error/debug test，并让 scoreboard 预期该错误。

### 5. Coverage 补充动作

| 补充动作 | 目的 | 结果 |
| --- | --- | --- |
| 增加 `random_mixed_transfer_test` | 用 constrained random 扩展 address/size/max_burst 组合 | 扩展正常功能空间 |
| 增加 `high_addr_toggle_test` | 交替 desc0/desc1，扫高位 src/dst address 和 INCR/FIXED mode | 补 descriptor/AXI address toggle |
| 增加 read/write DECERR test | 在 SLVERR 之外覆盖 DECERR response | 补 AXI error response 类型 |
| 增强 `csr_all_regs_test` | idle 状态下通过 RAL/CSR 写 `ffff_ffff -> 0 -> 5555_5555 -> aaaa_aaaa -> 0` | code-only coverage 从 `85.79%` 涨到 `88.44%`，toggle 从 `70.13%` 涨到 `79.95%` |
| 加结构性 toggle waiver | 对 AXI optional/tie-off/固定对齐信号做有理由排除 | 不关闭全局 toggle，只忽略不可达 bins |

面试里可以强调：coverage closure 不是盲目追 100%，而是把 hole 分成 real missing test、constraint issue、DUT bug、known issue 和 structural waiver。真正的目标是“每个 spec feature 都被验证并且每个未覆盖项都有解释”。

## 调试技巧

### 1. 波形调试
```systemverilog
// 在测试中设置波形dump
initial begin
    $dumpfile("dma_wave.vcd");
    $dumpvars(0, tb_top);
end

// 或者使用Questa命令
// vsim -view vsim.wlf -do "add wave *; run -all"
```

### 2. UVM消息控制
```systemverilog
// 设置消息冗余度
uvm_report_server::set_verbosity_level(UVM_MEDIUM);

// 特定组件消息控制
axil_agent.set_report_verbosity_level_hier(UVM_HIGH);
mem_agent.set_report_verbosity_level_hier(UVM_LOW);
```

### 3. 寄存器调试
```systemverilog
// 打印寄存器值
ral.DMA_STATUS.print();
ral.DMA_CONTROL.print();

// 比较mirror和desired值
ral.mirror(status, UVM_CHECK);
ral.update(status, UVM_BACKDOOR);
```

## 项目经验总结

### 技术收获
1. **完整UVM环境搭建**: 从零搭建包含agent、env、RAL、scoreboard的完整验证环境
2. **AXI协议深入理解**: 掌握AXI-Lite和AXI4协议细节，包括burst类型、outstanding、response处理
3. **高级UVM特性应用**: 使用virtual sequencer、explicit predictor、analysis port等高级特性
4. **覆盖率驱动验证**: 设计功能覆盖率模型，实现覆盖率闭环

### 调试经验
1. **AXI握手时序**: 确保valid/ready握手符合协议要求
2. **指针同步问题**: 格雷码指针在跨时钟域同步时的时序要求
3. **中断竞争条件**: 中断产生和清除的时序关系
4. **内存数据完整性**: 确保源和目标内存数据完全一致

### 最佳实践
1. **模块化设计**: 各UVM组件职责清晰，便于复用
2. **配置灵活性**: 通过config_db提供灵活的配置选项
3. **错误注入机制**: 支持多种错误注入方式，提高验证完备性
4. **自动化回归**: 建立自动化回归测试流程，提高验证效率

<a id="axi-dma-innosilicon-followups"></a>
## 芯动科技验证面试追问复盘

这一节用于回答 2026-06-03 芯动科技验证实习一面中围绕 AXI DMA UVM 项目的追问。

### 1. 怎么将信号驱动到 DUT？VIP 还是自己写的？

中文版回答：

我这个 DMA 验证环境没有用商业 VIP，AXI-Lite master agent 和 AXI memory slave BFM 都是自己写的。控制路径上，test/virtual sequence 通过 RAL frontdoor 发起寄存器访问，RAL adapter 把 register operation 转成 AXI-Lite sequence item，AXI-Lite driver 再把 AW/W/B 或 AR/R 握手驱动到 interface 上。数据搬运路径上，DUT 自己是 AXI4 master，testbench 这边不是主动发数据，而是一个 AXI memory slave BFM，被动接收 DUT 发出的 AR/AW/W 请求，再从 shared memory model 返回 RDATA 或写入 memory model。为了验证 backpressure，我在 slave BFM 里随机插 ready delay 和 response delay。

回答关键词：

- AXI-Lite：主动 master agent，用于 CSR/RAL frontdoor。
- AXI4 memory：被动 slave BFM，响应 DUT master。
- 没用商业 VIP；自己写 driver/monitor/BFM/scoreboard。
- Backpressure 通过 ready/response delay 实现。

容易说错：

- 不要把 memory slave BFM 说成“主动往 DUT 发送 data”。更准确的说法是：DUT 发读请求，BFM 返回读数据；DUT 发写请求，BFM 接收写数据并更新 memory model。
- 不要把这个项目和 TVIP-AXI crossbar 项目混在一起。DMA 项目是自写 BFM；crossbar 项目才是使用开源 AXI VIP。

### 2. abort 注入怎么实现？

中文版回答：

我会把 abort 分成两类说明。正常 DMA abort 测试应该走 frontdoor：在传输进行中，通过 AXI-Lite/RAL 写 `CONTROL.abort` bit，然后检查 DUT 是否停止继续发起新的 AXI transaction，已经 pending 的 transaction 是否被正确 drain 或清理，最后检查 `STATUS`、`ERROR_STATS`、interrupt 和 scoreboard 状态。这个路径最接近真实软件行为。

如果是为了覆盖很难从外部触发的内部错误，也可以在白盒验证中用 `force/release` 临时拉高内部 fault/abort-like 信号，但这属于 fault injection，不应该替代正常 CSR abort path。使用 `force` 时要有明确的 cleanup，test 结束或 reset 后必须 `release`，并且 scoreboard 要把这个场景标记为 expected error。

面试回答顺序：

1. 先讲 frontdoor CSR abort：`RAL/AXI-Lite write CONTROL.abort`。
2. 再讲检查点：no new request、pending cleanup、IRQ/status/error stats、scoreboard 不误报。
3. 最后补充：白盒 `force/release` 只用于特殊 fault injection。

### 3. 整个 DMA 是多路一起搬运还是单独搬运？

中文版回答：

这个问题要先澄清“多路”指什么。如果指物理数据通道，我这个 DUT 不是多个独立 DMA channel 同时并行搬，而是一个 AXI master datapath 根据 descriptor 配置执行搬运。如果指 descriptor slot，DUT 有两个 descriptor 配置槽，可以存两笔传输配置；testbench 主要把 desc0 作为完整数据 copy path 来验证，desc1 做 CSR/RAL readback 和配置覆盖，并把 desc1-only completion 作为 known issue 记录。如果指 AXI outstanding，那么一笔较长 transfer 会被 DUT 内部拆成多个 AXI burst，在前一个 burst response 回来之前继续发起后续请求，从而形成 outstanding。

简短版：

- Descriptor slot：可以配置多笔传输任务。
- Physical channel：不是多个独立 DMA 数据通道并行搬。
- AXI outstanding：长 transfer 被拆成多个 burst，请求可以同时 pending。
- Testbench：只配置 descriptor 和 backpressure，不直接“发 outstanding”；outstanding 是 DUT AXI master 行为。

### 4. outstanding 是谁发起的？怎么验证？

中文版回答：

Outstanding 不是 testbench 直接发给 DUT 的信号，而是 DUT 作为 AXI master 在数据搬运时自己发起多个未完成 transaction。Testbench 通过配置大 transfer size、较小 max burst、以及 memory slave BFM 的 response delay 来创造压力，让 DUT 在前一笔还没返回时继续发后续 AR/AW 请求。Monitor 统计发出的 request 和返回的 response，scoreboard 维护 pending counter 或按 ID/方向记录 outstanding depth，并在 coverage 中采样深度 bins。

检查点：

- outstanding depth 是否能达到设计目标。
- 达到上限后 DUT 是否 backpressure/停止继续发新请求。
- response 回来后 pending counter 是否正确减少。
- error response 或 abort 时 pending 状态是否能清理干净。

### 5. 未对齐 transfer 和 WSTRB 怎么讲？

中文版回答：

AXI 总线每个 beat 仍然按 data width 传，比如 32-bit data bus 一拍是 4 byte；但对于起始地址或传输长度不对齐的情况，并不是所有 byte lane 都有效。WSTRB 每一 bit 对应 WDATA 中的一个 byte，1 表示该 byte 有效、slave 应该写入，0 表示该 byte 无效、slave 应忽略。因此 5 byte transfer 可能被拆成两个 beat，首尾 beat 通过 WSTRB 只选择有效 byte。验证时 memory model 和 scoreboard 最好按 byte 粒度检查，而不是只按 32-bit word 比较。

### 6. 如果面试官追问“为什么不用 VIP？”

中文版回答：

这个项目的目标之一是展示我能理解 AXI valid-ready、burst、response 和 backpressure 的底层机制，所以我选择自己写一个轻量 AXI-Lite master agent 和 AXI memory slave BFM。这样我能控制 ready delay、response delay、error response 和 memory model 行为，也方便 debug。实际工业项目里，如果团队已有成熟 AXI VIP，我会优先复用 VIP 做协议合法性检查和覆盖，再把自己的 scoreboard、RAL、testplan 和场景约束接到 VIP 的 transaction/analysis port 上。

## 面试要点

### 技术深度问题
1. **AXI协议细节**: outstanding transaction管理、burst类型区别、response类型
2. **UVM架构设计**: virtual sequencer作用、RAL predictor实现、analysis port使用
3. **验证完备性**: 如何确保覆盖所有corner case、错误注入策略
4. **性能优化**: 如何提高仿真速度、减少内存占用

### 项目经验问题
1. **遇到的最大挑战**: 可能是outstanding深度验证、错误注入机制设计等
2. **团队协作**: 如何与设计工程师协作、问题定位流程
3. **质量保证**: 如何确保验证质量、覆盖率目标达成
4. **持续改进**: 如果重做项目，会做哪些改进

### 扩展思考
1. **协议断言**: 如何添加SVA断言提高验证效率
2. **形式验证**: 哪些部分适合使用形式验证
3. **VIP集成**: 如何集成商业VIP提高验证效率
4. **跨平台验证**: 如何支持不同仿真器
