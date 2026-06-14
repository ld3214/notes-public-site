[返回目录](../index.md)

# Protocols 知识库

这个文件集中放 AXI/APB 等协议复习内容。

## 页内目录

- [协议总览](#protocol-overview)
- [AXI](#axi)
- [AXI valid/ready handshake](#axi-valid-ready)
- [AXI Outstanding Transaction](#axi-outstanding)
- [AXI Interleaving](#axi-interleaving)
- [AXI-Lite 与 CSR 编程](#axil)
- [APB](#apb)
- [面试回答速查（中文 + English）](#protocol-interview-answers)

---
<a id="protocol-overview"></a>
## 协议总览
标签：`#protocol` `#asic` `#dv`

## 常见协议

- AXI
- AHB
- APB
- PCIe
- I2C
- SPI
- UART

## 记录重点

- Channel/signal
- Transaction flow
- Handshake
- Ordering
- Backpressure
- Corner cases
- Verification scenarios

---

<a id="axi"></a>
## AXI
标签：`#protocol` `#axi` `#dv` `#asic` `#interview`

## 核心概念

AXI (Advanced eXtensible Interface) 是 AMBA 协议族中面向高性能、高带宽场景的总线协议，支持乱序、outstanding 和 burst 传输。

**五个独立 Channel**

| Channel | 方向 | 主要信号 | 用途 |
| --- | --- | --- | --- |
| AW (Write Address) | Master → Slave | AWADDR, AWLEN, AWSIZE, AWBURST, AWID | 发出写地址和 burst 参数 |
| W (Write Data) | Master → Slave | WDATA, WSTRB, WLAST | 发出写数据 |
| B (Write Response) | Slave → Master | BRESP, BID | Slave 确认写完成并报告状态 |
| AR (Read Address) | Master → Slave | ARADDR, ARLEN, ARSIZE, ARBURST, ARID | 发出读地址和 burst 参数 |
| R (Read Data) | Slave → Master | RDATA, RRESP, RLAST, RID | Slave 返回读数据 |

五个 channel 互相独立，可以同时传输，是 AXI 高吞吐的基础。

<a id="axi-valid-ready"></a>
**Valid / Ready 握手规则**

AXI 用 valid/ready 握手控制每个 channel 上的传输：

- 发送方拉高 VALID，表示数据/地址有效。
- 接收方拉高 READY，表示可以接收。
- **同一周期 VALID 和 READY 都为高时，传输完成（handshake）。**
- 发送方不能等 READY 才拉高 VALID（会死锁）。
- 接收方可以在 VALID 之前就拉高 READY（不违反协议）。

**Read Transaction 流程**

```
Master                     Slave
  AR channel: ARVALID + ARADDR/ARID/ARLEN  →
                                           ← ARREADY
  (handshake 完成，地址被接受)

                                           ← R channel: RVALID + RDATA/RID/RLAST
  RREADY  →
  (逐 beat 返回数据，直到 RLAST=1 表示 burst 结束)
```

**Write Transaction 流程**

```
Master                     Slave
  AW channel: AWVALID + AWADDR/AWID/AWLEN →
                                          ← AWREADY
  W channel: WVALID + WDATA + WLAST      →  (可与 AW 同时或之后发)
                                          ← WREADY
  (WLAST 拉高时最后一 beat 传完)

                                          ← B channel: BVALID + BRESP/BID
  BREADY →
```

**关键参数**

- **AXLEN**：burst 长度 - 1（AXI4 最大 255，即 256 beats）。
- **AXSIZE**：每 beat 传输的字节数（log2 编码）。
- **AXBURST**：burst 类型。
  - `FIXED`：地址固定，用于 FIFO 类 peripheral。
  - `INCR`：地址递增，最常用。
  - `WRAP`：地址在边界内回绕，用于 cache line 对齐访问。
- **AXID**：transaction ID，用于 outstanding 和 out-of-order 追踪。

**AXI3 vs AXI4 主要区别**

| 差异点 | AXI3 | AXI4 |
| --- | --- | --- |
| Burst 最大长度 | 16 beats | 256 beats |
| Write data interleaving | 支持（W channel 可不同 ID 交错）| 不再支持（同时只有一条 write data 流） |
| ID 宽度 | 任意 | Master ID 通常更灵活 |
| Exclusive access | 支持 | 支持 |

**验证关注点**

- Valid/ready 握手：发送方不能等待 READY 才拉高 VALID（规范明确禁止）。
- Burst 计数：WLAST 的位置必须和 AWLEN 一致。
- Response 匹配：BRESP/RRESP 中的 ID 必须和对应 request 的 ID 一致。
- Outstanding transaction：master 可以在前一个未完成时继续发新地址；slave/interconnect 需要用 ID 追踪顺序。
- Backpressure：slave 通过 ARREADY/RREADY 等控制流量。

## 面试回答

AXI has five independent channels: write address, write data, write response, read address, and read data. Each channel uses a valid/ready handshake — the transfer completes only when both valid and ready are high in the same cycle. An important rule is that the sender must not wait for ready before asserting valid. Read and write transactions are independent and can overlap. AXI supports outstanding transactions, meaning a master can issue multiple transactions before earlier ones complete, using transaction IDs to match responses. For verification, I would check handshake rules through assertions, verify burst count and WLAST position, track IDs in the scoreboard for out-of-order response checking, and stress test backpressure scenarios.

## 常见追问

- AXI 有哪五个 channel？
  - AW（写地址）、W（写数据）、B（写响应）、AR（读地址）、R（读数据）。
- Valid/ready handshake 的规则是什么？
  - VALID 和 READY 同周期都高时传输完成；发送方不能等 READY 才拉 VALID；接收方可以在 VALID 之前拉 READY。
- Read transaction 和 write transaction 的流程？
  - Read：AR channel 发地址 → R channel 返回数据（burst，RLAST 标记结束）。Write：AW 发地址 + W 发数据（WLAST 标记结束）→ B 响应。
- Outstanding transaction 是什么？
  - Master 在前一个 transaction 完成之前就发出新 transaction；用 ID 追踪每个 pending request，response 按 ID 匹配回去。
- AXI 和 APB 的区别？
  - AXI：五通道、高带宽、支持 burst/outstanding/out-of-order，适合高性能 master（CPU、DMA）；APB：简单两 phase、低带宽、单 transfer，适合低速外设（GPIO、UART）。

<a id="axi-outstanding"></a>
## Outstanding Transaction
Outstanding transaction 指 master 在已有请求尚未完成时继续发出新的读/写请求。这样可以提高总线利用率和吞吐，但需要用 ID、计数器、buffer 或 scoreboard 追踪每个未完成请求。

面试回答：

AXI supports outstanding transactions, meaning a master can issue multiple transactions before earlier ones complete. The interconnect and slave must track IDs and ordering rules so responses return to the correct transaction. From a verification perspective, I would create scenarios with multiple outstanding reads/writes, backpressure, different IDs, same IDs, and delayed responses, then use a scoreboard indexed by transaction ID to check data and ordering.

<a id="axi-interleaving"></a>
## Interleaving
Interleaving 指不同 transaction 的 data/response 在时间上交错出现。面试中通常重点不是死背规则，而是说明你理解 ID、ordering、backpressure 和 scoreboard 检查方式。

验证关注点：

- Same ID 的 ordering 是否保持。
- Different ID 是否允许乱序或交错，取决于通道和协议版本/配置。
- Outstanding depth 达到上限时是否正确 backpressure。
- Response 是否能和 request ID 正确匹配。
- Scoreboard 是否能处理 out-of-order return。

---

<a id="axil"></a>
## AXI-Lite 与 CSR 编程
标签：`#protocol` `#axi-lite` `#csr` `#dv` `#asic` `#interview`

## AXI-Lite 是什么

AXI-Lite 是 AXI4 的轻量化子集，专门面向**寄存器级访问**（CSR 编程）。和 AXI4 相比，它去掉了 burst、ID、outstanding、WLAST 等复杂特性，每次只传输单个 data beat。

**AXI-Lite vs AXI4 vs APB 对比**

| 特性 | AXI-Lite | AXI4 | APB |
| --- | --- | --- | --- |
| Burst | 无（单 beat） | 支持，最多 256 beats | 无 |
| Transaction ID | 无 | 有，支持 out-of-order | 无 |
| Outstanding | 无（一次一个） | 支持多个 pending | 无 |
| WLAST | 无（默认最后一 beat） | 有 | 无 |
| 通道数 | 5 个（同 AXI4） | 5 个 | 无独立通道 |
| 适合场景 | CSR 寄存器访问、控制路径 | 高带宽数据搬移 | 低速外设 |

## 五个信号组（Channel）

AXI-Lite 保留了 AXI4 的五个通道结构，但信号大幅精简：

**Write Address Channel（AW）**

| 信号 | 方向 | 含义 |
| --- | --- | --- |
| `AWADDR` | Master → Slave | 写目标地址（通常 4 字节对齐） |
| `AWPROT` | Master → Slave | Protection type（一般填 0 或 AXI_SECURE） |
| `AWVALID` | Master → Slave | 地址有效 |
| `AWREADY` | Slave → Master | Slave 可以接受地址 |

**Write Data Channel（W）**

| 信号 | 方向 | 含义 |
| --- | --- | --- |
| `WDATA` | Master → Slave | 写数据（宽度固定，32 或 64 bit） |
| `WSTRB` | Master → Slave | Byte enable，每 bit 对应一个 byte；全 1 表示全部有效 |
| `WVALID` | Master → Slave | 数据有效 |
| `WREADY` | Slave → Master | Slave 可以接受数据 |

（AXI-Lite 无 WLAST，单 beat 即为最后一拍）

**Write Response Channel（B）**

| 信号 | 方向 | 含义 |
| --- | --- | --- |
| `BRESP` | Slave → Master | 写响应码（OKAY=0, SLVERR=2, DECERR=3） |
| `BVALID` | Slave → Master | 响应有效 |
| `BREADY` | Master → Slave | Master 准备好接受响应 |

**Read Address Channel（AR）**

| 信号 | 方向 | 含义 |
| --- | --- | --- |
| `ARADDR` | Master → Slave | 读目标地址 |
| `ARPROT` | Master → Slave | Protection type |
| `ARVALID` | Master → Slave | 地址有效 |
| `ARREADY` | Slave → Master | Slave 可以接受地址 |

**Read Data Channel（R）**

| 信号 | 方向 | 含义 |
| --- | --- | --- |
| `RDATA` | Slave → Master | 读返回数据 |
| `RRESP` | Slave → Master | 读响应码 |
| `RVALID` | Slave → Master | 数据有效 |
| `RREADY` | Master → Slave | Master 准备好接受数据 |

## Write Transaction 时序

AW 和 W 通道可以**同时**发出，不要求 AW 先于 W。两个 handshake 都完成后，slave 才能发 B response。

```
Cycle:    1       2       3       4       5
AWVALID:  1   →   0(握手完) ...
AWREADY:      1
WVALID:   1   →   0(握手完) ...
WREADY:         1
BVALID:                   1
BREADY:   1                       0
```

Driver 实现要点（来自真实代码）：

```systemverilog
// AW 和 W 同时拉高
vif.awvalid <= 1'b1;
vif.wvalid  <= 1'b1;
vif.bready  <= 1'b1;  // 提前拉高，随时准备接收 B

// 分别等待 AW 和 W handshake（哪个先完成就哪个先拉低）
while (!(aw_done && w_done)) begin
  @(posedge clk);
  if (!aw_done && vif.awvalid && vif.awready) begin
    vif.awvalid <= 1'b0;
    aw_done = 1'b1;
  end
  if (!w_done && vif.wvalid && vif.wready) begin
    vif.wvalid <= 1'b0;
    w_done = 1'b1;
  end
end

// 再等 B response
do @(posedge clk); while (!vif.bvalid);
tr.resp = vif.bresp;
```

## Read Transaction 时序

```
Cycle:    1       2       3
ARVALID:  1   →   0(握手完)
ARREADY:      1
RVALID:               1
RREADY:   1               0
```

Driver 实现：先等 AR handshake，再等 R valid。注意 ARREADY 可能在 ARVALID 同周期到来（zero-wait slave）或几个周期后到来（busy slave）。

```systemverilog
vif.arvalid <= 1'b1;
vif.rready  <= 1'b1;

// 等 AR handshake
do @(posedge clk); while (!(vif.arvalid && vif.arready));
vif.arvalid <= 1'b0;

// 等 R 数据
do @(posedge clk); while (!vif.rvalid);
tr.data = vif.rdata;
tr.resp = vif.rresp;
```

## Monitor 实现要点

AXI-Lite 的 AW 和 W 通道**独立握手**，monitor 必须分别 latch，在 B handshake 时合并发布完整 write transaction：

```systemverilog
// AW handshake → latch 地址
if (vif.awvalid && vif.awready)
  awaddr_q = vif.awaddr;

// W handshake → latch 数据
if (vif.wvalid && vif.wready) begin
  wdata_q = vif.wdata;
  wstrb_q = vif.wstrb;
end

// B handshake → 三路信息都到齐，发布 transaction
if (vif.bvalid && vif.bready) begin
  tr.dir  = DMA_WRITE;
  tr.addr = awaddr_q;   // 用 latched 值
  tr.data = wdata_q;
  tr.resp = vif.bresp;
  ap.write(tr);
end
```

Read monitor 同理：在 AR handshake 时 latch ARADDR（因为 master 可能在 R valid 到来前就撤销了 ARADDR），在 R handshake 时发布。

## CSR 编程（AXI-Lite 在 DMA 验证中的应用）

AXI-Lite 是 DMA controller 的 CSR 控制通道，通过它完成：

1. **Descriptor 编程**：写 SRC_ADDR、DST_ADDR、NUM_BYTES、CFG（enable/read_mode/write_mode）到各 descriptor 寄存器。
2. **启动 DMA**：写 CONTROL 寄存器的 GO bit（以及 max_burst 参数）。
3. **读状态**：读 STATUS 寄存器查看 done/error 标志；读 ERROR_STATS 查看错误类型。
4. **Abort**：写 CONTROL 寄存器的 ABORT bit。

典型 CSR 编程序列（DMA single descriptor 传输）：

```
axil_write(DMA_DESC_SRC_ADDR_OFFSET[0], 0x0000_1000)
axil_write(DMA_DESC_DST_ADDR_OFFSET[0], 0x0000_4000)
axil_write(DMA_DESC_NUM_BYTES_OFFSET[0], 256)
axil_write(DMA_DESC_CFG_OFFSET[0],  {enable=1, rd_mode=INCR, wr_mode=INCR})
axil_write(DMA_CONTROL_OFFSET, {max_burst=0xFF, abort=0, go=1})
→ 等 IRQ done
axil_read(DMA_STATUS_OFFSET) → 验证 done bit
```

## AXI-Lite 在 RAL 中的角色

AXI-Lite master agent 是 UVM RAL 的 frontdoor 总线：

```
test/virtual sequence
      ↓  reg.write() / reg.read()
dma_reg_adapter.reg2bus()  → 把 register op 转成 dma_axil_item
      ↓
axil_agent.driver          → 驱动 AXI-Lite 接口
      ↓
axil_agent.monitor.ap      → 监测真实 bus transaction
      ↓
uvm_reg_predictor          → 调用 adapter.bus2reg() 更新 RAL mirror
```

**Adapter 实现关键**：

```systemverilog
// reg → bus：register op 转成 AXI-Lite item
function uvm_sequence_item reg2bus(const ref uvm_reg_bus_op rw);
  dma_axil_item tr = ...;
  tr.dir  = (rw.kind == UVM_WRITE) ? DMA_WRITE : DMA_READ;
  tr.addr = rw.addr[31:0];
  tr.data = rw.data;
  tr.strb = rw.byte_en;
  return tr;
endfunction

// bus → reg：AXI-Lite item 反向转成 register op（供 predictor 用）
function void bus2reg(uvm_sequence_item bus_item, ref uvm_reg_bus_op rw);
  $cast(tr, bus_item);
  rw.kind   = (tr.dir == DMA_WRITE) ? UVM_WRITE : UVM_READ;
  rw.addr   = tr.addr;
  rw.data   = tr.data;
  rw.status = (tr.resp == AXI_OKAY) ? UVM_IS_OK : UVM_NOT_OK;
endfunction
```

## 面试回答

AXI-Lite is a simplified subset of AXI4 that supports only single-beat transfers with no burst, no ID, and no outstanding. It uses the same five-channel structure with valid/ready handshake. For a write transaction, the AW and W channels can be issued simultaneously; the slave responds on the B channel after accepting both. For a read, the master sends an address on AR, and the slave returns data on R. In DMA verification, AXI-Lite is the CSR programming path: the test programs descriptor registers (source/destination address, byte count, mode, enable) and then triggers the DMA via the CONTROL register. In UVM, the AXI-Lite agent is the frontdoor bus for the RAL model, with an adapter converting register-level operations to AXI-Lite transactions, and a predictor updating the register mirror from monitor observations.

## 常见追问

- AXI-Lite 和 AXI4 最大的区别是什么？
  - AXI-Lite 无 burst（单 beat）、无 ID、无 outstanding，不支持乱序；适合 CSR 访问，不适合高带宽数据搬移。
- AXI-Lite write transaction 中，AW 和 W 谁先谁后？
  - 协议不规定顺序，可以同时发，也可以 AW 先或 W 先；slave 必须等两个 handshake 都完成才能发 B response。
- Monitor 为什么要 latch AWADDR 和 ARADDR？
  - AW handshake 和 B handshake 不在同一周期；AR handshake 和 R handshake 也不在同一周期。Master 在 handshake 完成后会撤销 AWADDR/ARADDR，monitor 必须在 handshake 时 latch，否则发布 transaction 时地址已经变了。
- WSTRB 是什么，为什么需要？
  - Byte enable，每 bit 对应 WDATA 中的一个 byte（AXI_DATA_WIDTH/8 个 bit）。1 表示该 byte 有效，slave 写入；0 表示该 byte 无效，slave 忽略。用于 sub-word 访问，例如只写 32-bit 寄存器中的某个 byte。
- BRESP 有哪几种？
  - `OKAY (2'b00)`：成功；`EXOKAY (2'b01)`：exclusive access 成功（AXI-Lite 通常不用）；`SLVERR (2'b10)`：slave error；`DECERR (2'b11)`：decode error（地址不存在）。

## 易错点

- AW 和 W 通道独立，master 不能假设 slave 会等 AW 先到才处理 W（反过来也不行）。
- Monitor 忘记在 AW/AR handshake 时 latch 地址，导致 predictor 收到的 transaction 地址错误。
- WSTRB 全 0 通常是非法行为（AXI-Lite item constraint 应保证 `strb != 0`）。
- BREADY 忘记拉高：driver 不应该等 BVALID 才拉高 BREADY，否则每次写都多一个周期延迟，对 CSR 密集访问影响明显。
- 把 AXI-Lite 当 APB 记：两者都是简单单 beat 传输，但 AXI-Lite 用 valid/ready 握手、五个通道，APB 用 PSEL/PENABLE 两 phase。

---

<a id="apb"></a>
## APB
标签：`#protocol` `#apb` `#dv` `#asic` `#interview`

## 核心概念

APB (Advanced Peripheral Bus) 是 AMBA 协议族中面向低功耗、低带宽外设的简单总线，设计为最小逻辑面积和最低功耗，不支持 burst、outstanding 或流水线。

**主要信号**

| 信号 | 方向 | 含义 |
| --- | --- | --- |
| `PCLK` | 时钟 | APB 总线时钟 |
| `PRESETn` | 复位 | 低有效复位 |
| `PSEL` | Master → Slave | 选择目标 slave，高有效 |
| `PENABLE` | Master → Slave | 使能信号，区分 SETUP 和 ACCESS phase |
| `PADDR` | Master → Slave | 访问地址 |
| `PWRITE` | Master → Slave | 1=write，0=read |
| `PWDATA` | Master → Slave | 写数据 |
| `PRDATA` | Slave → Master | 读数据 |
| `PREADY` | Slave → Master | Slave 就绪，低时 master 等待，高时 transfer 完成 |
| `PSLVERR` | Slave → Master | 错误标志（APB3 新增） |

**Transfer 两 Phase**

每笔 APB transfer 分为两个 phase：

```
Cycle:     1         2        3(可选, PREADY=0 时扩展)
           SETUP    ACCESS    WAIT
PSEL:      1         1         1
PENABLE:   0         1         1
PREADY:    -         0 → 1     1（slave 就绪后拉高）
```

- **SETUP phase（第 1 周期）**：PSEL 拉高，PENABLE 保持低，地址/控制信号建立。
- **ACCESS phase（第 2 周期起）**：PENABLE 拉高，若 PREADY=1 则 transfer 完成；若 PREADY=0 则 slave 插入等待周期，直到 PREADY=1。
- Transfer 完成后，PSEL 和 PENABLE 拉低（idle state），或立刻开始下一笔 transfer 的 SETUP phase。

**时序图**

```
          ____      ________      ________
PCLK   __|    |____|        |____|        |
         ______________________________
PSEL   _|                              |__
         ________________
PENABLE_|                |________________   (PREADY=1 的情况)
         ____________________________
PADDR  _|____ADDR_________|____________|__
         ____________________________
PWRITE _|____1(write)_____|____________|__

                          ↑
                   ACCESS phase，PREADY=1，transfer 完成
```

**APB 为什么适合低带宽外设**

- 协议极简：无 burst、无 outstanding、无乱序，状态机只有 IDLE/SETUP/ACCESS 三个状态。
- 面积功耗小：逻辑简单，不需要 buffer 或复杂 arbiter。
- 足够满足 GPIO、UART、SPI、I2C、timer 等低速外设的带宽需求。
- 通常挂在 APB bridge 后面，主系统用高性能总线（AXI/AHB），APB bridge 将访问转换成 APB 时序。

**验证关注点**

- SETUP phase 持续且只有 1 个周期（除非 slave 插 wait）。
- PENABLE 在 PSEL 之后的第一个时钟沿拉高。
- PREADY=0 时数据和控制信号必须保持稳定。
- 写：PWDATA 在 ACCESS phase 有效；读：PRDATA 在 PREADY=1 的 ACCESS phase 采样。
- PSLVERR：在 ACCESS phase 结束时（PREADY=1 同周期）有效，不能提前或延迟。

## 面试回答

APB is a simple, low-power peripheral bus designed for low-bandwidth peripherals. Each transfer has two phases: a SETUP phase where PSEL is asserted and the address and control signals are set up, and an ACCESS phase where PENABLE is raised. If the slave is ready, PREADY goes high and the transfer completes; otherwise the slave holds PREADY low to insert wait states. APB does not support burst, outstanding, or out-of-order transfers. It is typically connected to the main high-performance bus through an APB bridge. Compared to AXI, APB is much simpler: fewer signals, simpler state machine, and appropriate for peripherals like UART, GPIO, and timers that do not need high throughput.

## 常见追问

- APB transfer 分为哪几个 phase？
  - SETUP phase（PSEL=1，PENABLE=0，建立地址和控制）和 ACCESS phase（PENABLE=1，PREADY=1 时 transfer 完成，PREADY=0 时插入等待）。
- `PSEL`、`PENABLE`、`PREADY` 分别代表什么？
  - `PSEL`：选中某个 slave；`PENABLE`：进入 ACCESS phase；`PREADY`：slave 就绪，高时本周期 transfer 完成。
- APB 为什么适合低带宽外设？
  - 协议简单（IDLE/SETUP/ACCESS 三态）、无 burst/outstanding、面积功耗小，足以满足 GPIO、UART 等低速外设需求，连在 APB bridge 后面与高速主线解耦。
---

<a id="protocol-interview-answers"></a>
## 面试回答速查（中文 + English）
### AXI-Lite 与 CSR 编程

中文：AXI-Lite 是 AXI4 的单 beat 子集，用于 CSR 寄存器访问，没有 burst、ID 和 outstanding。写操作分三个通道：AW（地址）、W（数据 + byte enable）、B（响应）；读操作分两个通道：AR（地址）、R（数据 + 响应）。AW 和 W 可以同时发出，slave 等两个 handshake 都完成再给 B 响应。Monitor 必须在 AW/AR handshake 时 latch 地址，因为 master 之后会撤销地址信号。在 DMA 验证中，AXI-Lite agent 是 RAL 的 frontdoor 总线，通过 reg_adapter 在 register-level 和 AXI-Lite transaction 之间做转换。

English: AXI-Lite is a single-beat subset of AXI4 for register access, with no burst, no ID, and no outstanding. A write uses the AW, W, and B channels; a read uses AR and R. The AW and W channels can be issued simultaneously. A monitor must latch the address at the AR/AW handshake because the master will de-assert the address before the response arrives. In a UVM environment, the AXI-Lite agent serves as the RAL frontdoor bus, with an adapter converting register operations to bus transactions and a predictor updating the register mirror.

### AXI outstanding

中文：AXI outstanding 指 master 可以在前一个 transaction 完成前继续发起多个 transaction，提高吞吐。系统需要用 ID、buffer、计数器或 scoreboard 追踪未完成请求，并保证 response 能正确匹配 request，同时遵守 ordering 规则。

English: AXI outstanding transactions allow a master to issue multiple transactions before earlier ones complete. The system tracks IDs and ordering so each response matches the correct request.

### AXI interleaving

中文：AXI interleaving 指不同 transaction 的 data/response 在时间上交错出现。面试时重点是说明 ID tracking、same ID ordering、different ID 乱序/交错、backpressure 和 scoreboard 检查，而不是只背协议名词。

English: AXI interleaving means data or responses from different transactions may be interleaved in time. Verification should check ID tracking, ordering rules, backpressure, and out-of-order scoreboard behavior.

