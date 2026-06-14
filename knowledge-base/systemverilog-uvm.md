[返回目录](../index.md)

# SystemVerilog / UVM 知识库

这个文件集中放 SV 数据结构、随机化、SVA 和 UVM 核心机制。

## 页内目录

- [SystemVerilog 总览](#sv-overview)
- [Blocking vs Non-blocking Assignment](#sv-blocking-nonblocking)
- [Cast：显式 / 隐式、向上 / 向下转换](#sv-class-casting)
- [SystemVerilog 笔试 Coding Patterns](#sv-coding-patterns)
- [动态数组、关联数组、队列](#sv-arrays-queues)
- [SV 随机化 / Constrained Random](#sv-randomization)
- [书籍整理：SV/Verilog 高频语法清单](#book-sv-verilog-checklist)
- [SVA](#sva)
- [UVM 总览](#uvm-overview)
- [书籍整理：UVM 高频问法清单](#book-uvm-interview-checklist)
- [`uvm_config_db` 用法](#uvm-config-db)
- [UVM TLM 通信](#uvm-tlm)
- [Analysis Port](#uvm-analysis-port)
- [UVM Factory 机制](#uvm-factory)
- [UVM Phase 机制](#uvm-phases)
- [Virtual Sequence / Virtual Sequencer / Sequence API](#uvm-virtual-sequence)
- [m_sequencer 和 p_sequencer](#uvm-sequencer-handles)
- [AXI DMA 项目：sequence / vsequence / virtual sequencer 调用链](#uvm-axi-dma-vseq-flow)
- [UVM 高级技巧（来自 AXI DMA 项目）](#uvm-advanced-patterns)
- [Register Model / UVM RAL](#uvm-ral)
- [面试回答速查（中文 + English）](#sv-uvm-interview-answers)

---
<a id="sv-overview"></a>
## SystemVerilog 总览
标签：`#systemverilog` `#dv` `#interview`

### 学习地图

- Data types
- [动态数组、关联数组、队列](#sv-arrays-queues)
- Interfaces and modports
- Classes and OOP
- [Class cast / upcast / downcast](#sv-class-casting)
- [Coding patterns: task / fork / valid-ready TB](#sv-coding-patterns)
- [Randomization](#sv-randomization)
- Constraints
- Mailbox/semaphore/event
- Assertions
- Coverage

### `logic` / `wire` / `reg` 的区别

| 类型 | 驱动规则 | 典型用途 |
| --- | --- | --- |
| `wire` | 只能由 `assign` 或端口驱动；多驱动需要 `wor`/`wand` | 组合逻辑的连线 |
| `reg` | 可以在 `always`/`initial` 里赋值；不代表物理寄存器 | 旧式 Verilog，RTL 内部状态 |
| `logic` | SV 新增，可以替代 `wire` 和 `reg`；只允许单一 driver | 推荐用于大多数 SV 信号声明 |

`logic` 是 SV 的推荐类型，比 `reg` 更语义清晰（和硬件寄存器无必然联系）。端口上用 `logic` 表示可连接内外驱动，而 `wire` 强调互连语义。

<a id="sv-blocking-nonblocking"></a>
## Blocking vs Non-blocking Assignment

| 特性 | Blocking `=` | Non-blocking `<=` |
| --- | --- | --- |
| 执行时机 | 当行立即执行，后续语句使用更新后的值 | RHS 在当前时间步开始时求值，LHS 在时间步结束时更新 |
| 适合场景 | `always_comb` 组合逻辑，`function` 内部 | `always_ff` 时序逻辑 |
| 典型问题 | 在 `always_ff` 里用 blocking：同一 always block 里先后赋值的顺序依赖会产生竞争 | 在 `always_comb` 里用 non-blocking：RHS 不立即更新，组合逻辑行为错误 |

```systemverilog
// 正确：always_ff 用 <=
always_ff @(posedge clk) begin
  a <= b;      // b 的值是 clk 沿时的 b，a 在时间步末更新
  c <= a;      // 这里的 a 仍是旧值，c 得到旧 a——符合寄存器行为
end

// 危险：always_ff 里用 =
always_ff @(posedge clk) begin
  a = b;       // a 立刻更新
  c = a;       // c 看到的是新 a，而不是旧 a——不是寄存器行为
end
```

面试口诀：**组合用 blocking，时序用 non-blocking，两者不混用。**

### `always_comb` / `always_ff` / `always_latch`

- `always_comb`：推断组合逻辑，敏感列表自动从 body 内读取的信号推导，工具检查是否有 latch inference。
- `always_ff`：推断触发器，必须带时钟边沿，工具检查是否意外推断出 latch。
- `always_latch`：明确推断 latch，在明确需要 latch 的场景（例如 level-sensitive gated register）使用，其余场合避免。

推荐始终用这三个显式关键字替代通用 `always`，因为工具会对 body 内容做额外 lint 检查，比 `always @(*)` 更安全。

---

<a id="sv-class-casting"></a>
## Cast：显式 / 隐式、向上 / 向下转换
标签：`#systemverilog` `#oop` `#cast` `#uvm` `#interview`

### 一句话定义

SystemVerilog 里的转换可以分两层：普通数据类型有**隐式转换**和**显式转换**；class handle 在继承体系里还有**向上转换（upcast）**和**向下转换（downcast）**。Upcast 通常是隐式合法的，downcast 必须用 `$cast()` 做运行时类型检查。

### 显式转换 vs 隐式转换

| 类型 | 谁触发 | 例子 | 面试重点 |
| --- | --- | --- | --- |
| 隐式转换 implicit conversion | 编译器根据赋值、表达式、端口连接、函数参数自动做 | `logic [7:0] a; int i; a = i;` 或 `base_h = child_h;` | 代码短，但可能发生截断、符号扩展、2-state/4-state 信息丢失 |
| 显式转换 explicit conversion | 工程师写出转换意图 | `byte'(i)`、`$signed(raw)`、`$cast(child_h, base_h)` | 意图清楚，但不代表一定没有信息损失，仍要理解目标类型 |

普通数据类型例子：

```systemverilog
int           i = 300;
byte unsigned b;
logic [7:0]   raw = 8'hff;
int signed    s;

// 隐式转换：int -> byte unsigned，结果会截断成低 8 bit
b = i;          // b = 8'h2c

// 显式转换：同样会截断，但读代码的人知道这是有意转换
b = byte'(i);

// 显式改变 signedness，再赋给更宽的 signed int
s = $signed(raw); // raw 被解释成 signed 8-bit，再符号扩展到 int
```

面试里要强调：**显式转换不是“更安全的魔法”，只是把意图写清楚；真正安全取决于你是否接受 width、signedness 和 2-state/4-state 的变化。**

### 核心关系

```systemverilog
class base_txn;
  virtual function void print_kind();
    $display("base_txn");
  endfunction
endclass

class err_txn extends base_txn;
  bit inject_error;

  virtual function void print_kind();
    $display("err_txn");
  endfunction
endclass

initial begin
  err_txn  e;
  base_txn b;
  err_txn  e2;

  e = new();

  // Upcast：derived -> base，隐式合法
  b = e;

  // b 的静态类型是 base_txn，因此不能直接访问 err_txn 的字段
  // b.inject_error = 1; // compile error

  // virtual method 仍然按真实对象类型 dispatch
  b.print_kind(); // prints "err_txn"

  // Downcast：base -> derived，必须运行时检查
  if ($cast(e2, b)) begin
    e2.inject_error = 1;
  end else begin
    $display("b is not an err_txn object");
  end
end
```

### Upcast：向上转换

Upcast 指把派生类对象句柄赋给基类句柄，属于 class handle 的隐式转换：

```systemverilog
err_txn  child = new();
base_txn base_h;

base_h = child;
```

特点：

- 编译期安全，因为派生类对象一定也是一种基类对象。
- 基类 handle 只能访问基类中声明过的字段和方法。
- 如果方法是 `virtual`，调用时会根据对象真实类型执行派生类 override 后的方法。
- UVM 中常见：driver、scoreboard 或 factory API 用 base item handle 保存不同派生 transaction。

### Downcast：向下转换

Downcast 指把基类 handle 转成更具体的派生类 handle，属于 class handle 的显式/动态转换：

```systemverilog
base_txn base_h;
err_txn  child_h;

if (!$cast(child_h, base_h)) begin
  `uvm_fatal("BAD_CAST", "base_h is not an err_txn")
end
```

为什么必须 `$cast()`：

- 基类 handle 可能实际指向 `base_txn`、`err_txn`，也可能指向另一个 sibling 派生类。
- 编译器只知道变量的静态类型，不一定知道运行时对象真实类型。
- `$cast(dst, src)` 会检查 `src` 指向的真实对象是否兼容 `dst` 类型；成功返回 1，失败返回 0。

### 静态类型 vs 动态类型

| 概念 | 含义 | 例子 |
| --- | --- | --- |
| 静态类型 static type | 变量声明时的类型，决定编译期能访问哪些成员 | `base_txn b;` 中 `b` 的静态类型是 `base_txn` |
| 动态类型 dynamic type | handle 实际指向对象的真实类型，决定 virtual method dispatch 和 `$cast` 是否成功 | `b = err_txn::new();` 后对象真实类型是 `err_txn` |

关键点：**field access 看静态类型，virtual method dispatch 看动态类型。**

### UVM 里的典型场景

**Factory override 后访问派生类字段**

```systemverilog
base_txn tr;
err_txn  err_tr;

tr = base_txn::type_id::create("tr");

if ($cast(err_tr, tr)) begin
  err_tr.inject_error = 1;
end
```

如果 factory override 把 `base_txn` 替换成 `err_txn`，`tr` 的静态类型仍是 `base_txn`，但真实对象可能是 `err_txn`。这时想访问派生类专有字段，就需要 `$cast`。

**`p_sequencer` 的本质**

`p_sequencer` 也是强类型访问的一种例子：它本质上把通用的 `m_sequencer` 转成用户声明的 sequencer 类型，方便访问自定义 sequencer 里的成员。

### 面试回答

中文：SV 里隐式转换是编译器在赋值、表达式或参数传递中自动做的转换，比如窄化/扩展、signedness 转换，class 里的 derived handle 赋给 base handle 也是一种隐式 upcast。显式转换是工程师写出目标类型，比如 `byte'(i)`、`$signed(x)` 或 class downcast 用 `$cast()`。Upcast 安全且通常隐式合法，但 upcast 后只能访问基类成员；downcast 要用 `$cast()` 检查运行时对象真实类型。UVM 中常见场景是 factory override 后，base item handle 实际指向 derived item，如果要访问派生类字段就需要 `$cast`。

English: In SystemVerilog, implicit conversions are performed automatically by the compiler during assignments, expressions, or argument passing, while explicit conversions are written by the engineer using casts such as `byte'(i)`, `$signed(x)`, or `$cast()` for class handles. Upcasting a derived handle to a base handle is normally implicit and safe, but the base handle can only access base-class members. Downcasting a base handle back to a derived handle should use `$cast()` because the runtime object may not be of that derived type.

### 常见追问

- Upcast 之后还能不能访问派生类字段？
  - 不能直接访问，因为变量静态类型是基类。要么把字段/方法放到基类接口里，要么 `$cast` 回派生类。
- 显式转换和隐式转换的区别？
  - 隐式转换由编译器自动做，代码更短但容易隐藏截断或 signedness 问题；显式转换由工程师写出目标类型，表达意图更清楚，但仍可能丢信息。
- `$cast` 失败会怎样？
  - function form 会返回 0，目标 handle 不应被继续当成有效派生类使用；面试里建议检查返回值并报错。
- 为什么 virtual function 不需要 downcast？
  - 因为 virtual method dispatch 根据对象真实类型调用 override 后的方法，这正是多态的价值。
- 什么时候不建议 downcast？
  - 如果代码大量依赖 downcast，通常说明 base class abstraction 设计不够好；优先考虑 virtual method、base field、config object 或接口抽象。

### 易错点

- 以为 base handle 指向 derived object 后就能直接访问 derived field。
- 以为显式转换一定安全，忽略了 width truncation 和 signedness 变化。
- 隐式把宽类型赋给窄类型，例如 `int` 到 `byte`，没有意识到高位会被截断。
- Downcast 不检查 `$cast` 返回值，失败后继续用派生类 handle。
- 忘记把需要多态的方法声明成 `virtual`，导致调用基类实现。
- 滥用 downcast，让可复用组件强依赖某个具体派生类。

---

<a id="sv-coding-patterns"></a>
## SystemVerilog 笔试 Coding Patterns
标签：`#systemverilog` `#coding-test` `#task` `#fork-join-none` `#valid-ready` `#interview`

这类笔试题通常不只考语法，而是考能不能把状态、并发、握手、transaction 和 monitor 组织成清楚的 testbench code。

### 复习入口

- [task + FSM：find first 1](#sv-task-fsm-find-first-one)
- [fork/join_none：并行统计二维数组每行 1 的个数](#sv-fork-join-none-row-count)
- [valid-ready：transaction / drive / monitor / tb](#sv-valid-ready-task-tb)

<a id="sv-task-fsm-find-first-one"></a>
### task + FSM：find first 1

题型：写一个 task 找输入向量中第一个 `1` 的位置，要求用状态机形式，四个状态 `IDLE`、`SEARCH`、`DONE`、`SEARCHFAIL`，用 `enum` 定义状态，每次调用 task 推进一次状态。

关键点：

- `enum` 定义状态，代码更清楚。
- `idx` 和 `state` 是跨 task 调用保留的状态变量。
- 每次调用 task 只检查一个 bit，模拟“step-by-step FSM”。
- 找到 1 后进入 `DONE`；扫完整个向量都没找到进入 `SEARCHFAIL`。

```systemverilog
module find_first1_task_fsm #(
  parameter int W = 8,
  parameter int IW = $clog2(W)
);
  typedef enum logic [1:0] {
    IDLE,
    SEARCH,
    DONE,
    SEARCHFAIL
  } state_t;

  state_t state;
  int unsigned idx;

  task automatic reset_fsm();
    state = IDLE;
    idx   = 0;
  endtask

  task automatic find_first1_step(
    input  logic [W-1:0] data,
    input  bit           start,
    output bit           done,
    output bit           fail,
    output logic [IW-1:0] pos
  );
    done = 1'b0;
    fail = 1'b0;
    pos  = '0;

    case (state)
      IDLE: begin
        if (start) begin
          idx   = 0;
          state = SEARCH;
        end
      end

      SEARCH: begin
        if (data[idx]) begin
          pos   = idx[IW-1:0];
          done  = 1'b1;
          state = DONE;
        end else if (idx == W-1) begin
          fail  = 1'b1;
          state = SEARCHFAIL;
        end else begin
          idx++;
        end
      end

      DONE: begin
        done = 1'b1;
        if (!start) state = IDLE;
      end

      SEARCHFAIL: begin
        fail = 1'b1;
        if (!start) state = IDLE;
      end
    endcase
  endtask

  initial reset_fsm();
endmodule
```

面试说法：这个版本不是一拍组合 priority encoder，而是把搜索过程拆成多次 task 调用，每次检查一位，所以状态变量必须保留在 task 外部或 static context 中。

<a id="sv-fork-join-none-row-count"></a>
### fork/join_none：并行统计二维数组每行 1 的个数

题型：给一个二维数组 `bit q[M][N]`，并行计算每一行里 `1` 的个数，结果存在一个数组中。

关键点：

- 每一行可以开一个并发进程独立统计。
- `fork ... join_none` 不等待子进程结束，后面如果要用结果，需要 `wait fork`。
- `for` loop 中启动 fork 时，必须用 `automatic int row = i;` 保存当前 loop index，否则所有进程可能看到同一个最终 `i`。

```systemverilog
module row_count_ones;
  parameter int M = 4;
  parameter int N = 8;

  bit q[M][N];
  int unsigned ones_per_row[M];

  task automatic count_one_row(input int row);
    ones_per_row[row] = 0;
    for (int col = 0; col < N; col++) begin
      ones_per_row[row] += q[row][col];
    end
  endtask

  initial begin
    // Example init
    foreach (q[i, j]) q[i][j] = $urandom_range(0, 1);

    for (int i = 0; i < M; i++) begin
      automatic int row = i;
      fork
        count_one_row(row);
      join_none
    end

    wait fork; // wait for all row-counting processes

    foreach (ones_per_row[i]) begin
      $display("row %0d has %0d ones", i, ones_per_row[i]);
    end
  end
endmodule
```

面试说法：`join_none` 适合启动后台并发任务，但如果后续要读结果，就必须同步等待。这个题最容易错在 fork 里直接用 loop variable `i`，应该用 `automatic` 临时变量锁住当前行号。

<a id="sv-valid-ready-task-tb"></a>
### valid-ready：transaction / drive / monitor / tb

题型：用 task 写 valid-ready 握手。定义 transaction，包含 valid、ready、data 等信息；driver 发送 transaction，ready 随机拉高/拉低，monitor 收集数据，testbench 发送 5 个 transaction：`tx_q[5]`。

更规范的写法是：`clk/rst_n/valid/ready/data` 放在 interface 里，transaction 主要保存 payload 和采样到的 handshake 信息。如果题目强制 transaction 里也包含 valid/ready，可以在 class 里保留 sampled fields。

```systemverilog
interface vr_if(input logic clk);
  logic        rst_n;
  logic        valid;
  logic        ready;
  logic [7:0]  data;
endinterface

class vr_transaction;
  rand bit [7:0] data;
  bit            valid;
  bit            ready;

  function new(bit [7:0] data = '0);
    this.data  = data;
    this.valid = 1'b0;
    this.ready = 1'b0;
  endfunction
endclass

module valid_ready_tb;
  logic clk;
  vr_if vif(clk);

  vr_transaction tx_q[5];
  vr_transaction rx_q[$];

  initial clk = 0;
  always #5 clk = ~clk;

  task automatic drive(input vr_transaction tx);
    @(posedge vif.clk);
    vif.valid <= 1'b1;
    vif.data  <= tx.data;

    do begin
      @(posedge vif.clk);
    end while (!vif.ready);

    vif.valid <= 1'b0;
    vif.data  <= '0;
  endtask

  task automatic random_ready();
    forever begin
      @(posedge vif.clk);
      if (!vif.rst_n) begin
        vif.ready <= 1'b0;
      end else begin
        vif.ready <= $urandom_range(0, 1);
      end
    end
  endtask

  task automatic monitor();
    forever begin
      @(posedge vif.clk);
      if (vif.rst_n && vif.valid && vif.ready) begin
        vr_transaction rx = new(vif.data);
        rx.valid = vif.valid;
        rx.ready = vif.ready;
        rx_q.push_back(rx);
      end
    end
  endtask

  initial begin
    vif.rst_n = 1'b0;
    vif.valid = 1'b0;
    vif.data  = '0;
    repeat (3) @(posedge clk);
    vif.rst_n = 1'b1;

    foreach (tx_q[i]) begin
      tx_q[i] = new(8'h10 + i);
    end

    fork
      random_ready();
      monitor();
    join_none

    foreach (tx_q[i]) begin
      drive(tx_q[i]);
    end

    repeat (5) @(posedge clk);
    $display("received %0d transactions", rx_q.size());
    $finish;
  end
endmodule
```

面试说法：

- Driver 保持 `valid` 和 `data`，直到看到 `ready`，握手在 `valid && ready` 同周期发生。
- Ready 可以由 receiver 随机 backpressure。
- Monitor 只在 `valid && ready` 时采样 transaction。
- 如果要更像 UVM，可以把 `drive()` 放到 driver，`monitor()` 放到 monitor，`rx_q` 换成 analysis port 或 mailbox。

### 面试回答

中文：这三个题覆盖了 SV 笔试里很常见的三个能力：第一，能用 `enum` 和 task 写出每次调用推进一步的 FSM；第二，能用 `fork/join_none` 启动并行任务，并知道 loop variable 要用 `automatic` 保存；第三，能把 valid-ready 握手拆成 transaction、driver、ready backpressure 和 monitor，明确只有 `valid && ready` 同周期才算传输成功。

English: These coding questions test three common SystemVerilog skills: implementing a step-by-step FSM using an enum and task, launching independent parallel jobs with `fork/join_none` while capturing loop variables with `automatic`, and modeling a valid-ready handshake with a transaction, driver, randomized ready backpressure, and monitor sampling only on `valid && ready`.

---

<a id="sv-arrays-queues"></a>
## 动态数组、关联数组、队列的区别
标签：`#systemverilog` `#dv` `#interview`

### 一句话定义

动态数组适合运行时决定长度的连续数组；关联数组适合用 key 做稀疏映射；队列适合需要频繁从头尾插入、删除、弹出的有序集合。

### 对比表

| 类型 | 声明例子 | 索引方式 | 大小 | 典型用途 |
| --- | --- | --- | --- | --- |
| 动态数组 dynamic array | `int da[];` | 连续整数索引 `0..size-1` | 运行时用 `new[n]` 分配，重新分配才改变大小 | 根据配置生成 N 个 item、保存一段连续数据 |
| 关联数组 associative array | `txn aa[int];` / `txn aa[string];` | key/value，key 可以是 `int`、`string`、`enum` 等常见类型 | 稀疏，按需创建元素 | scoreboard 中用 ID 查 transaction、统计不同 address 的访问 |
| 队列 queue | `int q[$];` | 连续整数索引，支持头尾操作 | 动态增长/收缩 | FIFO buffer、transaction stream、临时待处理列表 |

### 动态数组 Dynamic Array

```systemverilog
int data[];

initial begin
  data = new[4];
  foreach (data[i]) data[i] = i;

  // 扩容并保留旧数据
  data = new[8](data);
end
```

动态数组的长度在仿真运行时决定，但分配后长度固定。想改变大小通常需要重新 `new`，可以用 `new[new_size](old_array)` 保留旧内容。它适合表示一段连续、有固定当前长度的数据。

常用方法：

- `size()`：返回元素个数。
- `delete()`：删除整个数组内容，使 size 变成 0。

### 关联数组 Associative Array

```systemverilog
typedef class packet;
packet expected_by_id[int];

initial begin
  expected_by_id[10] = new();

  if (expected_by_id.exists(10)) begin
    $display("ID 10 exists");
  end

  expected_by_id.delete(10);
end
```

关联数组像 map/dictionary，不要求索引连续，只给实际出现的 key 分配元素。它特别适合 verification 里的 scoreboard、reference model、统计表。

常用方法：

- `num()`：当前元素数量。
- `exists(key)`：检查某个 key 是否存在。
- `delete(key)`：删除指定 key；不带参数时删除全部。
- `first(key)`、`last(key)`、`next(key)`、`prev(key)`：遍历 key。

### 队列 Queue

```systemverilog
int q[$];

initial begin
  q.push_back(1);
  q.push_back(2);
  q.push_front(0);

  void'(q.pop_front()); // FIFO 风格
  q.insert(1, 99);
  q.delete(1);
end
```

队列是有序、可变长的集合，适合表示 FIFO、pending transaction list、monitor 收到但 scoreboard 还没比较的数据。队列可以从前后两端 push/pop，也可以按 index 插入或删除。

常用方法：

- `push_back()`、`push_front()`
- `pop_back()`、`pop_front()`
- `insert(index, value)`
- `delete(index)`；不带参数时删除全部
- `size()`

### 面试回答

Dynamic array is a runtime-sized contiguous array. It is useful when the size is known during simulation but not at compile time. Associative array is a sparse key-value container, so it is good for scoreboards or lookup tables indexed by transaction ID or address. Queue is an ordered dynamic container with push and pop operations, so it is commonly used as a FIFO or pending transaction buffer.

### 常见追问

- 如果要用 transaction ID 查 expected packet，用什么？
  - 用关联数组，例如 `expected[id] = pkt;`，因为 ID 可能不连续。
- 如果要实现 monitor 到 scoreboard 的 FIFO，用什么？
  - 用 queue，或者更常见地用 `uvm_tlm_analysis_fifo`。单纯数据结构层面 queue 很适合。
- 动态数组和 queue 都能变长，区别是什么？
  - 动态数组偏向“重新分配后的一段连续数组”；queue 偏向“运行中持续 push/pop 的有序流”。

### 易错点

- 动态数组不是自动扩容容器，改变大小通常要重新 `new`。
- 关联数组的 key 不一定连续，不能假设 `0..num()-1` 都存在。
- Queue 可以随机访问，但如果语义是查 key，用关联数组更清楚。

---

<a id="sv-randomization"></a>
## SV 随机化 / Constrained Random
标签：`#systemverilog` `#dv` `#randomization` `#interview`

### 核心概念

SystemVerilog 随机化用于自动生成大量合法 stimulus。核心思想是：把需要变化的字段声明为 `rand` 或 `randc`，用 constraint 描述合法空间，然后调用 `randomize()` 让 solver 找到满足约束的一组值。

```systemverilog
class packet;
  rand bit [7:0] addr;
  rand bit [3:0] len;
  rand bit       is_write;

  constraint c_len  { len inside {[1:8]}; }
  constraint c_addr { addr[1:0] == 2'b00; }
endclass

initial begin
  packet p = new();

  if (!p.randomize() with { is_write == 1; addr inside {[8'h40:8'h7f]}; }) begin
    $fatal("Randomization failed");
  end
end
```

### `rand` 和 `randc`

| 关键字 | 含义 | 使用场景 |
| --- | --- | --- |
| `rand` | 每次 randomize 时在合法空间中随机选值 | 大多数随机字段 |
| `randc` | random cyclic，遍历完合法值前尽量不重复 | opcode、small enum、需要覆盖所有取值的小范围字段 |

`randc` 不适合特别大的取值空间，否则 solver 压力和状态维护成本会很高。

### 常见约束写法

```systemverilog
constraint c_basic {
  addr inside {[0:255]};
  len > 0;
  len <= 16;
}

constraint c_implication {
  is_write -> len <= 8;
}

constraint c_distribution {
  is_write dist {1 := 70, 0 := 30};
}

constraint c_order {
  solve is_write before len;
}
```

- `inside`：限制值属于集合或范围。
- `dist`：设置权重分布。
- `->`：条件约束，左边成立时右边必须成立。
- `solve ... before ...`：影响求解顺序，常用于让控制字段先决定数据字段。

### Randomization Hooks

```systemverilog
function void pre_randomize();
  // randomize 前准备，例如打开/关闭某些约束
endfunction

function void post_randomize();
  // randomize 后派生字段、打印、检查
endfunction
```

- `pre_randomize()` 在 solver 求解前自动调用。
- `post_randomize()` 在求解成功后自动调用。
- 不建议在 `post_randomize()` 里修改已经被 coverage/checker 依赖的随机字段，除非这是明确设计的一部分。

### 控制随机化

```systemverilog
p.c_len.constraint_mode(0); // 关闭某个 constraint
p.addr.rand_mode(0);        // 关闭某个变量的随机化
```

- `constraint_mode(0/1)`：关闭或打开 constraint block。
- `rand_mode(0/1)`：关闭或打开某个 random variable。
- Inline constraint `randomize() with { ... }` 适合 test/sequence 中做场景定制。

### 面试回答

SystemVerilog randomization uses `rand` variables and constraints to generate legal stimulus automatically. The solver chooses values that satisfy all active constraints, and `randomize()` returns success or failure. In verification, this is useful because we can explore many legal scenarios and corner cases without manually writing every directed test. I usually combine constrained random stimulus with functional coverage, so coverage tells me whether the random space has actually hit the intended scenarios.

### 常见追问

- `rand` 和 `randc` 的区别？
- `constraint` 怎么写？
- `pre_randomize` 和 `post_randomize` 有什么用？
- 如果 randomization fail 怎么 debug？

### Randomization Fail 怎么 Debug

- 检查 `randomize()` 返回值，失败时不要继续使用旧值。
- 简化 inline constraint，确认是不是 test 临时约束和 class 内部约束冲突。
- 临时关闭部分 constraint：`constraint_mode(0)`。
- 检查 `inside` 范围、条件约束、数组 size 约束是否互相矛盾。
- 打印随机前的配置字段，因为很多 constraint 依赖 non-rand configuration。

### 易错点

- 忘记检查 `randomize()` 的返回值。
- Inline constraint 和 class constraint 冲突。
- 把 `randc` 用在过大的空间上。
- 在 `post_randomize()` 里随意改随机字段，导致 coverage 和实际 stimulus 不一致。
- 约束写得太死，只能产生少量场景，functional coverage 上不去。

---

<a id="book-sv-verilog-checklist"></a>
## 书籍整理：SV/Verilog 高频语法清单
标签：`#book` `#systemverilog` `#verilog` `#interview`

这一节把《Cracking Digital VLSI Verification Interview》中 HDL 章节的典型问法压缩成复习清单。已有详细笔记的主题仍优先回链到对应章节。

### RTL/Verilog 语义

| 主题 | 速答口径 | 相关笔记 |
| --- | --- | --- |
| Blocking vs non-blocking | 组合逻辑用 blocking，时序逻辑用 non-blocking；在同一个时序 always 里用 blocking 容易造成仿真行为和寄存器意图不一致。 | [Blocking vs Non-blocking](#sv-blocking-nonblocking) |
| 同步/异步 reset | 同步 reset 只在 clock edge 生效；异步 reset 进入 sensitivity list，可立即 assert，释放最好同步。 | [CDC/RDC](asic-frontend.md#cdc-rdc) |
| `==` vs `===` | `==` 遇到 X/Z 可能得到 X；`===` 把 X/Z 当作可比较值，常用于 testbench 精确比较未知态。 | 本节 |
| task vs function | function 不消耗仿真时间并返回值；task 可以消耗时间、可有多个 output/inout，适合 driver/monitor 时序行为。 | [Coding Patterns](#sv-coding-patterns) |
| latch inference | 组合 always 中分支未覆盖或未给默认值会推断 latch。 | [综合与 Lint](asic-frontend.md#synthesis-lint) |
| `case/casez/casex` | `case` 精确匹配，`casez` 把 Z/? 当 don't-care，`casex` 连 X 也当 don't-care，RTL 中慎用 `casex`。 | 本节 |

### SV 数据类型与数组

| 主题 | 速答口径 |
| --- | --- |
| `reg` / `wire` / `logic` | `wire` 表互连，`reg` 是旧式过程赋值变量，`logic` 是 SV 推荐单驱动变量类型。 |
| `bit` vs `logic` | `bit` 是 2-state，只能 0/1；`logic` 是 4-state，可表达 X/Z，更适合 RTL/TB 信号。 |
| `logic [7:0]` vs `byte` | 都可表示 8 bit，但 `byte` 是 2-state signed integral type；`logic [7:0]` 是 4-state packed vector。 |
| packed vs unpacked | packed 维度是连续 bit 向量，可整体做算术/切片；unpacked 是元素集合，适合 array/memory。 |
| dynamic array | 运行时分配长度，适合长度运行时才知道但当前大小相对固定的集合。 |
| associative array | 稀疏 key-value，适合大地址空间 memory model 或 scoreboard 按 ID/address 查找。 |
| queue | 有序动态容器，支持 push/pop，适合 FIFO/pending list。 |
| struct vs union | struct 每个 field 独立占空间；union 多个 field 共享同一段存储。 |

### OOP 与接口

| 主题 | 速答口径 |
| --- | --- |
| class 成员默认可见性 | SystemVerilog class 成员默认 `public`，可显式声明 `local` 或 `protected`。 |
| forward declaration | 先声明 class 名，解决两个 class 相互引用或定义顺序问题。 |
| virtual / pure virtual | virtual 支持动态派发；pure virtual 只声明接口，派生类必须实现。 |
| abstract class | 包含 pure virtual method 或声明为 virtual class，不能直接实例化，用作接口/基类。 |
| interface | 封装一组信号和 task/function，连接 DUT 与 TB；modport 限定方向和可见性。 |
| clocking block | 给 TB 驱动/采样定义时钟和 skew，减少 race，常放在 interface 里。 |

### 随机化与并发

| 主题 | 速答口径 | 相关笔记 |
| --- | --- | --- |
| `pre_randomize()` / `post_randomize()` | randomize 前后 hook；前者准备配置，后者派生字段或检查结果，但不要随意破坏已求解字段。 | [SV 随机化](#sv-randomization) |
| hard vs soft constraint | hard 必须满足；soft 可被 inline/harder constraint 覆盖，适合默认约束。 | [SV 随机化](#sv-randomization) |
| `constraint_mode()` / `rand_mode()` | 前者开关 constraint block，后者开关某个 rand 字段。 | [SV 随机化](#sv-randomization) |
| `std::randomize()` | 对局部变量或非 class 字段随机化，适合临时生成值。 | [SV 随机化](#sv-randomization) |
| `fork/join` | 等所有分支结束；`join_any` 等任一分支结束；`join_none` 立即继续。 | [UVM 高级技巧](#uvm-advanced-patterns) |
| `wait fork` / `disable fork` | 等待当前作用域子进程结束；终止当前 fork 作用域下仍在运行的分支。 | [UVM 高级技巧](#uvm-advanced-patterns) |
| semaphore | 计数锁，用于控制共享资源访问数量。 | 本节 |
| mailbox | 线程间消息队列；bounded mailbox 可限制容量，unbounded 不限制。 | 本节 |
| event | 线程同步触发器，用 `-> ev` 触发，用 `@ev` 或 `wait(ev.triggered)` 等待。 | 本节 |

### 面试回答

中文：HDL 语法题要抓住“仿真语义”和“硬件意图”的差别。比如 blocking/non-blocking 不只是符号不同，而是调度区域和寄存器建模不同；`==`/`===` 不只是相等比较，而是 X/Z 处理不同；packed/unpacked、2-state/4-state、task/function、clocking block 都会影响 testbench 是否有 race、RTL 是否可综合、debug 是否可信。

English: For SystemVerilog and Verilog syntax questions, I focus on the difference between simulation semantics and hardware intent. Blocking versus non-blocking affects scheduling and register modeling. `==` and `===` differ in X/Z handling. Packed versus unpacked arrays, 2-state versus 4-state types, tasks versus functions, and clocking blocks all affect synthesizability, race avoidance, and debug quality.

### 常见追问

- 为什么 testbench 有时用 `===`？
  - 因为 TB 可能要检测 X/Z 是否真实出现，`===` 会逐 bit 比较 X/Z，而 `==` 可能返回 X。
- 为什么 RTL 中慎用 `casex`？
  - `casex` 把 X 也当 don't-care，可能掩盖未知态传播，导致仿真过于乐观。
- 为什么 fork loop 里常要 `automatic int idx = i`？
  - 每个并发分支需要保存当时的 loop index，否则所有分支可能看到同一个最终变量值。

### 易错点

- 用 2-state `bit` 保存可能为 X 的 DUT 信号，debug 时把未知态吞掉。
- `logic` 多驱动时以为工具会自动仲裁，实际会报错或产生不明确行为。
- 在 function 里写耗时语句。
- `post_randomize()` 改字段导致 constraint 求解结果和实际 stimulus 不一致。

---

<a id="sva"></a>
## SVA
标签：`#sva` `#systemverilog` `#dv` `#interview`

### 核心概念

**Immediate Assertion vs Concurrent Assertion**

| 维度 | Immediate Assertion | Concurrent Assertion |
| --- | --- | --- |
| 求值时机 | 像过程语句，执行到那行时立即求值 | 在时钟沿采样，检查时序属性 |
| 语法关键字 | `assert` | `assert property` / `assume property` / `cover property` |
| 使用位置 | `initial`、`always`、task/function 内部 | module、interface、program 级别 |
| 典型用途 | 检查当前值、一次性合法性检查 | 检查跨时钟周期的协议和时序规则 |

```systemverilog
// Immediate assertion（过程级别）
always_comb begin
  assert (count >= 0) else $error("count underflow");
end

// Concurrent assertion（时序属性）
assert property (
  @(posedge clk) disable iff (!rst_n)
  valid |-> ##[1:3] ready
) else $error("handshake timeout");
```

**Implication 运算符**

- `|->` (overlapping)：antecedent 成立的**同周期**开始检查 consequent。
- `|=>` (non-overlapping)：antecedent 成立后**下一个时钟周期**开始检查 consequent。

```systemverilog
// |->：req 拉高的同一周期内，ack 必须也为高
assert property (@(posedge clk) req |-> ack);

// |=>：req 拉高后，下一个周期 ack 必须为高
assert property (@(posedge clk) req |=> ack);

// 延迟窗口：req 拉高后 1 到 3 个周期内 grant 必须到来
assert property (@(posedge clk) req |-> ##[1:3] grant);
```

**常用时序函数**

| 函数 | 含义 |
| --- | --- |
| `$rose(sig)` | 信号在本周期上升沿（0→1）|
| `$fell(sig)` | 信号在本周期下降沿（1→0）|
| `$stable(sig)` | 信号相比上一个时钟周期未发生变化 |
| `$past(sig, n)` | n 个时钟周期之前的信号值 |
| `$onehot(vec)` | 向量恰好有一个 bit 为 1 |
| `$onehot0(vec)` | 向量最多一个 bit 为 1（允许全 0）|
| `$countones(vec)` | 向量中为 1 的 bit 数 |

```systemverilog
// 协议检查：valid 拉高后在 ready 到来之前 data 不能变化
assert property (
  @(posedge clk) disable iff (!rst_n)
  ($rose(valid) && !ready) |=> $stable(data)
);

// FSM 状态检查：state 必须 one-hot
assert property (
  @(posedge clk) disable iff (!rst_n)
  $onehot(state)
);
```

**disable iff**

`disable iff (!rst_n)` 在 reset 期间停止 assertion 采样，避免 reset 期间产生误报。这是 concurrent assertion 的标准写法。

**Assertion 在 DV 中适合检查什么**

- 协议合规：valid-ready 握手规则、burst 计数、response ID 匹配。
- 状态机：FSM state 必须 one-hot、非法状态转移检查。
- 时序规则：请求和响应之间的延迟约束、信号稳定性。
- 边界条件：FIFO 在 full 时不允许写、在 empty 时不允许读。
- 内部不变量：指针、计数器的值域约束。

```systemverilog
// FIFO 边界 assertion
assert property (
  @(posedge clk) disable iff (!rst_n)
  full |-> !wr_en
) else $error("Write to full FIFO");

assert property (
  @(posedge clk) disable iff (!rst_n)
  empty |-> !rd_en
) else $error("Read from empty FIFO");
```

### 面试回答

SVA has two types of assertions. Immediate assertions are evaluated like procedural statements at the time of execution, suitable for one-shot value checks. Concurrent assertions are evaluated at clock edges and can check temporal properties across multiple cycles, which is how you check protocol rules. The implication operator `|->` checks the consequent starting in the same cycle as the antecedent; `|=>` checks one cycle later. Common functions like `$rose`, `$fell`, and `$stable` let you check signal transitions relative to the previous clock edge. In a verification environment, I use assertions to check handshake rules, FSM state validity, timing relationships, and boundary conditions, because assertions run continuously in the background and catch violations immediately.

### 常见追问

- Immediate assertion 和 concurrent assertion 的区别？
  - Immediate 是过程语句，执行到当行立即求值；concurrent 绑定时钟沿，检查跨周期时序属性。
- `|->` 和 `|=>` 的区别？
  - `|->` antecedent 成立时，同周期开始检查 consequent；`|=>` 从下一个时钟周期开始检查。
- `$rose`、`$fell`、`$stable` 怎么用？
  - `$rose` 检测本周期上升沿；`$fell` 检测下降沿；`$stable` 检查信号与上一周期相比未变化，常用于 valid 信号保持期间 data 稳定性检查。
- Assertion 在 DV 中适合检查什么？
  - 协议握手规则、FSM one-hot 约束、时序延迟要求、FIFO 边界条件、信号稳定性——这些用 scoreboard 很难检查，但 assertion 能在违例发生的同一时刻直接报错。

---

<a id="uvm-overview"></a>
## UVM 总览
标签：`#uvm` `#dv` `#interview`

### 学习地图

- [UVM component hierarchy](#uvm-component-hierarchy)
- [Sequence item / sequence / sequencer / driver](#uvm-sequence-driver-flow)
- [Monitor / agent / env / test](#uvm-component-hierarchy)
- [TLM communication / analysis port](#uvm-tlm)
- [Scoreboard](#uvm-scoreboard)
- [Factory](#uvm-factory)
- [Config DB](#uvm-config-db)
- [Phases and objections](#uvm-phases)
- [Virtual sequence / virtual sequencer](#uvm-virtual-sequence)
- [Sequence API: `body()` / `start()` / `start_item()` / `finish_item()`](#uvm-sequence-api)
- [`m_sequencer` vs `p_sequencer`](#uvm-sequencer-handles)
- [Register model / RAL](#uvm-ral)

<a id="uvm-component-hierarchy"></a>
### UVM Testbench 组件职责

```
test
  └── env
        ├── agent (active)
        │     ├── sequencer   ← 控制 sequence 执行顺序
        │     ├── driver      ← 把 item 转成 pin-level stimulus
        │     └── monitor     ← 采集 DUT 接口，转成 transaction
        ├── scoreboard / checker
        └── coverage collector
```

| 组件 | 职责 |
| --- | --- |
| `uvm_test` | 顶层，负责配置 env、启动 sequence、控制仿真生命周期（objection）|
| `uvm_env` | 容纳 agent、scoreboard、coverage，是可复用验证环境的边界 |
| `uvm_agent` | 包含 sequencer + driver + monitor，封装一个接口的驱动和监测 |
| `uvm_sequencer` | 仲裁 sequence 对 driver 的访问，把 item 按顺序发给 driver |
| `uvm_driver` | 从 sequencer 拿 item，把它翻译成 DUT 接口上的 pin-level 信号 |
| `uvm_monitor` | 被动观察 DUT 接口，把 pin-level 信号打包成 transaction，通过 analysis port 广播 |
| Scoreboard | 接收 monitor 的 transaction，对比 expected（来自 reference model 或 predictor）和 actual |
| Coverage | 订阅 analysis port 上的 transaction，更新 functional coverage 数据 |

<a id="uvm-scoreboard"></a>
**Scoreboard / Checker 的职责**

Scoreboard 的核心是 self-checking：接收 monitor 发来的 actual transaction，同时从 reference model、predictor 或输入 monitor 生成 expected result，最后比较 expected 和 actual。简单 in-order 场景可以用 queue 顺序比较；out-of-order 场景通常按 transaction ID 或 address 用 associative array 匹配。

<a id="uvm-sequence-driver-flow"></a>
**Sequence / Sequencer / Driver 的关系**

- `uvm_sequence_item`：单条数据，driver 操作的最小单位。
- `uvm_sequence`：产生一组 item 的 generator，在 body() 中用 `start_item` + `finish_item` 发送 item。
- `uvm_sequencer`：中间层，序列化 sequence 对 driver 的访问；driver 通过 `get_next_item` 取 item，处理完后 `item_done`。

```
sequence.body()
  └─ start_item(item) ──→ sequencer.wait_for_grant()
  └─ finish_item(item) ──→ sequencer.send_request()
                                  ↓
                          driver.get_next_item(item)
                          ... drive pins ...
                          driver.item_done()
```

**Analysis Port：Monitor 到 Scoreboard 的解耦**

Monitor 不应该直接知道 scoreboard 的存在（否则复用性差）。Analysis port 提供广播机制：

```systemverilog
// Monitor
uvm_analysis_port #(my_txn) ap;

// 在 monitor 里 broadcast
ap.write(txn);

// Scoreboard 实现 write() 接口
class my_scoreboard extends uvm_scoreboard;
  uvm_analysis_imp #(my_txn, my_scoreboard) analysis_export;

  function void write(my_txn txn);
    // 比较 expected vs actual
  endfunction
endclass
```

<a id="uvm-config-db"></a>
## `uvm_config_db` 用法

最常见场景：在 top module 里把 virtual interface set 进去，在 driver/monitor 的 `build_phase` 里 get 出来。

```systemverilog
// top module
initial begin
  uvm_config_db #(virtual my_if)::set(null, "uvm_test_top.*", "vif", dut_if);
end

// driver build_phase
function void build_phase(uvm_phase phase);
  if (!uvm_config_db #(virtual my_if)::get(this, "", "vif", vif))
    `uvm_fatal("NO_VIF", "Virtual interface not found")
endfunction
```

常见坑：type 不匹配、path 写错、get 早于 set、忘记检查 get 返回值。

### 面试回答

A UVM testbench is organized in a hierarchy: the test creates the environment, which contains agents, a scoreboard, and coverage collectors. Each agent encapsulates a sequencer, a driver, and a monitor for one interface. The sequencer arbitrates sequence access to the driver; the driver converts sequence items into pin-level stimulus; the monitor captures pin-level activity and broadcasts transactions through analysis ports to the scoreboard and coverage collector. The scoreboard compares expected results from a reference model against actual DUT outputs. The factory, phase mechanism, config DB, and analysis port are the four key UVM mechanisms that make the environment reusable and configurable.

### 常见追问

- UVM testbench 的结构怎么讲？
  - Test → Env → Agent (sequencer/driver/monitor) + Scoreboard + Coverage。每一层职责清晰，通过 analysis port 和 config_db 解耦。
- Sequence 和 sequencer 的关系是什么？
  - Sequence 产生 item，sequencer 仲裁多个 sequence 对 driver 的访问，driver 通过 get_next_item / item_done 和 sequencer 交互。
- Factory 的作用是什么？
  - 让 test 可以用 type/instance override 替换 env 中的任意 component 或 object，而不改变 env 源码，提高复用性。
- `uvm_config_db` 怎么用？
  - 常用于把 virtual interface 传给 driver/monitor，或把配置 object 传给各级 component；set 必须早于 get，type 和 path 必须匹配，get 返回值必须检查。
- UVM phase 机制是什么？
  - 见 [UVM Phase 机制](#uvm-phases)。
- UVM TLM 通信是什么？
  - 见 [UVM TLM 通信](#uvm-tlm)。
- `m_sequencer` 和 `p_sequencer` 的区别？
  - 见 [`m_sequencer` 和 `p_sequencer`](#uvm-sequencer-handles)。

---

<a id="book-uvm-interview-checklist"></a>
## 书籍整理：UVM 高频问法清单
标签：`#book` `#uvm` `#interview`

### 方法学总览

| 主题 | 速答口径 |
| --- | --- |
| UVM 优点 | 标准化、可复用、可配置、支持 CRV、coverage、TLM、factory、phasing 和 register model。 |
| UVM 缺点 | 学习曲线陡、代码量大、debug 层次深，小模块可能显得重；需要团队规范才能发挥复用价值。 |
| TLM | 以 transaction object 连接组件，减少 pin-level 耦合。 |
| Analysis port vs TLM FIFO | Analysis port 是非阻塞广播；TLM FIFO 是点对点带缓存，支持 blocking/nonblocking get/put/peek。 |
| Transaction vs sequence item | Transaction 是抽象操作概念；`uvm_sequence_item` 是 UVM 中可被 sequence/driver 传递的 transaction 基类。 |

### Agent/Sequence/Driver

| 主题 | 速答口径 |
| --- | --- |
| Agent 组成 | Active agent 包含 sequencer、driver、monitor；passive agent 通常只有 monitor。 |
| Active vs passive | Active 会驱动 DUT 接口，passive 只监听接口，常用于 checker/coverage 或复用现有 stimulus。 |
| Sequencer/driver handshake | Sequence 用 `start_item/finish_item` 发 item；driver 用 `get_next_item/item_done` 或 `get/put` API 取 item 和返回响应。 |
| `get_next_item()` vs `try_next_item()` | 前者阻塞等待 item；后者非阻塞尝试获取，适合 slave BFM 或 error injection。 |
| `get()` vs `peek()` | `get()` 取出并移除，`peek()` 查看但不移除。 |
| Sequence arbitration | 多个 sequence 同时运行时，sequencer 根据 FIFO、priority、random、strict FIFO 等策略仲裁。 |
| `lock()` vs `grab()` | 都让 sequence 独占 sequencer；`grab()` 优先级更强，通常应谨慎使用，避免饿死其他 sequence。 |
| Response routing | driver 返回 response 时要带 sequence/item ID，确保回到正确 sequence。 |
| Virtual sequence | 协调多个 lower-level sequence，常用于多接口、寄存器配置 + 数据流 + IRQ 等系统场景。 |

### Factory/Phase/Config/RAL

| 主题 | 速答口径 |
| --- | --- |
| `new()` vs `create()` | `new()` 直接构造，绕过 factory；`type_id::create()` 经过 factory，支持 override。 |
| Type override vs instance override | Type override 替换某一类型所有创建；instance override 只替换某个层次路径下的实例。 |
| Object vs component override | Component 有层次路径，可做 instance override；普通 object/sequence 不在 component hierarchy 中，通常只能 type override 或通过上下文创建。 |
| Objection | 控制 run phase 是否结束；不 raise 可能提前结束，忘记 drop 可能挂住。 |
| Timeout | 可用 UVM timeout、watchdog sequence 或 `fork/join_any + disable fork` 防止仿真无限等待。 |
| Phase 顺序 | build 自顶向下创建，connect 自底/按层连接，run 耗时执行，check/report 收尾。 |
| `phase_ready_to_end()` | phase 将结束前的 hook，可用于等待 pending transaction drain，但不能滥用拖延仿真。 |
| `uvm_config_db` | 跨层传 virtual interface 和 config object；重点是 type、path、set/get 顺序和返回值检查。 |
| UVM RAL | 抽象 register map，统一读写、mirror、predict、frontdoor/backdoor 和 register coverage。 |
| Callback | 在不改原组件代码的情况下插入扩展行为，适合 error injection 或功能钩子，但过度使用会让控制流变隐蔽。 |
| `uvm_root` | UVM component tree 的单例根节点，`run_test()` 从这里创建并启动 test。 |

### 面试回答

中文：UVM 的核心价值是把验证环境标准化并提高复用性。Agent 封装一个接口，sequence 产生 transaction，driver 转成 pin-level 时序，monitor 采集 DUT 行为，scoreboard/reference model 做 self-checking，coverage 判断场景是否命中。Factory 负责可替换创建，phase 负责生命周期，config_db 负责配置传递，TLM/analysis port 负责组件解耦，RAL 负责寄存器抽象。

English: The value of UVM is standardization and reuse. An agent encapsulates one interface; sequences generate transactions; drivers convert them into pin-level behavior; monitors observe DUT activity; scoreboards and reference models perform self-checking; coverage tracks scenario closure. The factory enables replaceable construction, phases define lifecycle, config DB passes configuration, TLM decouples components, and RAL abstracts registers.

### 常见追问

- 为什么小 block 不一定需要完整 UVM？
  - UVM 复用价值在复杂接口、多人协作、长期维护和 regression 上更明显；简单组合/小模块可用轻量 TB。
- 为什么 monitor 用 analysis port？
  - Monitor 不需要知道谁接收 transaction，analysis port 广播给 scoreboard、coverage、logger，提高复用性。
- Factory override 为什么有时不生效？
  - 常见原因是用了 `new()`，类没注册，override 设置太晚，type/path 不匹配，或 create context 不对。
- Simulation 怎么结束？
  - run phase objection 归零后进入 extract/check/report/final；还要确保 pending transaction drain 和 timeout 机制正确。

### 易错点

- Driver 取到 item 后忘记 `item_done()`，sequence 卡住。
- Objection raise/drop 不成对，导致过早结束或永远不结束。
- `uvm_config_db` 用 `*` 过度匹配，让多个 agent 拿到错误 virtual interface。
- Scoreboard 只接 actual，没有明确 expected source。
- Callback 过度使用，debug 时找不到行为从哪里插入。

---

<a id="uvm-tlm"></a>
## UVM TLM 通信
标签：`#uvm` `#tlm` `#analysis-port` `#scoreboard` `#dv` `#interview`

### 一句话定义

TLM（Transaction-Level Modeling）通信是在 UVM 组件之间传递 transaction object 的机制。它让组件之间通过 port/export/imp/FIFO 通信，而不是直接调用彼此的内部函数，从而降低耦合、提高复用性。

### 为什么需要 TLM

在 UVM testbench 里，driver、monitor、scoreboard、coverage collector 应该各司其职：

- Monitor 只负责观察 interface，并把 pin-level activity 转成 transaction。
- Scoreboard 只负责比较 expected 和 actual。
- Coverage collector 只负责采样 functional coverage。

如果 monitor 直接调用 scoreboard 的函数，monitor 就依赖了 scoreboard 的具体实现，复用性会很差。TLM 的核心价值就是解耦 producer 和 consumer。

### 常见 TLM 通信类型

| 类型 | 方向 | 是否一对多 | 是否阻塞 | 常见用途 |
| --- | --- | --- | --- | --- |
| `uvm_analysis_port` | producer broadcast | 是 | 非阻塞 | monitor -> scoreboard / coverage subscriber |
| `uvm_analysis_imp` | consumer 实现 `write()` | 可接收 port | 非阻塞 | scoreboard/coverage 接收 transaction |
| `uvm_analysis_export` | 转接 | 取决于连接 | 非阻塞 | 层级穿透或连接 analysis FIFO |
| `uvm_blocking_put_port` | producer put | 通常一对一 | 阻塞 | producer 等 consumer 接收 |
| `uvm_blocking_get_port` | consumer get | 通常一对一 | 阻塞 | consumer 等数据到来 |
| `uvm_tlm_analysis_fifo` | analysis + FIFO 缓冲 | 可接 analysis port | get 阻塞 | monitor 和 scoreboard 解耦、缓存 transaction |

### Port / Export / Imp 怎么理解

| 概念 | 直觉理解 | 例子 |
| --- | --- | --- |
| port | “我要调用某种 TLM 接口” | monitor 的 `analysis_port.write(txn)` |
| export | “我把这个接口继续往外暴露/转接” | env 把 agent monitor 的 port 转接出去 |
| imp | “我真正实现这个接口” | scoreboard 实现 `write(txn)` |

最常见的 analysis 连接：

```systemverilog
// monitor
class my_monitor extends uvm_monitor;
  uvm_analysis_port #(my_txn) ap;

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    ap = new("ap", this);
  endfunction

  task run_phase(uvm_phase phase);
    my_txn txn;
    // collect transaction from interface
    ap.write(txn);
  endtask
endclass

// scoreboard
class my_scoreboard extends uvm_scoreboard;
  uvm_analysis_imp #(my_txn, my_scoreboard) analysis_imp;

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    analysis_imp = new("analysis_imp", this);
  endfunction

  function void write(my_txn txn);
    // compare/check transaction
  endfunction
endclass

// env connect_phase
mon.ap.connect(sb.analysis_imp);
```

<a id="uvm-analysis-port"></a>
## Analysis Port 的特点

- 一对多 broadcast：同一个 monitor transaction 可以同时发给 scoreboard、coverage collector、logger。
- 非阻塞：`write()` 是 function，不能消耗仿真时间。
- Producer 不知道 consumer 是谁：monitor 不需要知道后面接了 scoreboard 还是 coverage。
- 没有 backpressure：consumer 不能通过 analysis port 阻止 producer 发送。

如果 consumer 处理较慢或需要阻塞式读取，可以中间接 `uvm_tlm_analysis_fifo`。

### TLM FIFO

`uvm_tlm_analysis_fifo` 常用于 monitor 和 scoreboard 之间做缓冲：

```systemverilog
class my_scoreboard extends uvm_scoreboard;
  uvm_tlm_analysis_fifo #(my_txn) exp_fifo;
  uvm_tlm_analysis_fifo #(my_txn) act_fifo;

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    exp_fifo = new("exp_fifo", this);
    act_fifo = new("act_fifo", this);
  endfunction

  task run_phase(uvm_phase phase);
    my_txn exp, act;
    forever begin
      exp_fifo.get(exp); // blocking
      act_fifo.get(act); // blocking
      compare(exp, act);
    end
  endtask
endclass
```

连接方式：

```systemverilog
exp_mon.ap.connect(sb.exp_fifo.analysis_export);
act_mon.ap.connect(sb.act_fifo.analysis_export);
```

好处：monitor 还是非阻塞 broadcast，scoreboard 可以用 blocking `get()` 按自己的节奏取数据。

### Blocking vs Nonblocking TLM

| 类型 | 行为 | 典型 API | 场景 |
| --- | --- | --- | --- |
| Blocking | 没有数据或对方没准备好时等待 | `put()` / `get()` / `peek()` | FIFO、request/response、scoreboard 等待 transaction |
| Nonblocking | 立即返回 success/fail，不等待 | `try_put()` / `try_get()` / `can_put()` / `can_get()` | 不能卡住当前流程、polling |
| Analysis | 非阻塞广播，无返回 backpressure | `write()` | monitor -> subscriber |

### 面试回答

中文：UVM TLM 是组件之间传 transaction 的通信机制，核心是用 port/export/imp/FIFO 解耦组件。最常见的是 monitor 用 `uvm_analysis_port.write(txn)` 广播 transaction，scoreboard 或 coverage collector 用 `uvm_analysis_imp.write()` 接收；如果 scoreboard 需要缓存和阻塞式读取，可以接 `uvm_tlm_analysis_fifo`，monitor 非阻塞写入，scoreboard 用 `get()` 取。TLM 的价值是让 monitor 不依赖 scoreboard 的具体实现，提高 testbench 复用性。

English: UVM TLM is the transaction-level communication mechanism between components. It uses ports, exports, imps, and FIFOs to decouple producers and consumers. A common pattern is a monitor broadcasting transactions through an `uvm_analysis_port`, while a scoreboard or coverage collector receives them through an analysis imp. If buffering is needed, a `uvm_tlm_analysis_fifo` can be inserted so the monitor writes non-blockingly and the scoreboard gets transactions at its own pace.

### 常见追问

- Analysis port 和普通 function call 有什么区别？
  - Analysis port 通过 TLM 接口广播 transaction，producer 不知道 consumer 具体是谁，组件耦合更低。
- `analysis_port` 能不能阻塞？
  - 不能。`write()` 是 function，不消耗仿真时间，也没有 backpressure。
- 一个 analysis port 可以连多个 subscriber 吗？
  - 可以，这正是 broadcast 的常见用途，比如同时连 scoreboard 和 coverage collector。
- `uvm_analysis_imp` 和 `uvm_analysis_export` 区别？
  - imp 是真正实现 `write()` 的 consumer；export 更多是转接/暴露接口，本身不实现最终行为。
- 为什么要用 `uvm_tlm_analysis_fifo`？
  - 用于缓冲 transaction，让 producer 非阻塞发送，consumer 可以 blocking `get()`。

### 易错点

- 在 `write()` 里写耗时操作或 `#delay`，这是不允许的，因为 `write()` 是 function。
- Monitor 直接调用 scoreboard 内部函数，导致组件强耦合。
- 多个 analysis source 接同一个 `write()` 却不区分来源，scoreboard 不知道 transaction 从哪里来。
- 以为 analysis port 有 backpressure，实际上 consumer 无法阻止 producer 继续 `write()`。
- FIFO 没有在 `connect_phase` 正确连接到 `analysis_export`。

---

<a id="uvm-factory"></a>
## UVM Factory 机制
标签：`#uvm` `#factory` `#dv` `#interview`

### 一句话定义

UVM factory 是一个对象创建和替换机制：代码中通过 factory 创建 component/object，test 可以在不修改原始 testbench 代码的情况下，把某个类型替换成另一个派生类型。

### 为什么需要 Factory

在 DV 中，经常需要复用同一个 environment，但不同 test 想替换某些行为：

- 把普通 driver 换成 error injection driver。
- 把普通 sequence item 换成带额外约束的 item。
- 把某个 monitor/scoreboard 换成增强版本。

如果到处直接调用 `new()`，类型在代码里写死，就很难替换。Factory 的价值是把“创建什么类型”的决定延后到 test 配置阶段。

### 基本使用

```systemverilog
class my_driver extends uvm_driver #(my_item);
  `uvm_component_utils(my_driver)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction
endclass

class my_agent extends uvm_agent;
  `uvm_component_utils(my_agent)

  my_driver drv;

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    drv = my_driver::type_id::create("drv", this);
  endfunction
endclass
```

关键点：

- 类需要注册到 factory：component 用 `` `uvm_component_utils``，object 用 `` `uvm_object_utils``。
- 创建时用 `type_id::create()`，不要直接 `new()`。
- Component 的 `create` 需要传 `name` 和 `parent`；object 通常只需要 `name`。

### Type Override 和 Instance Override

```systemverilog
// 所有 my_driver 都替换成 error_driver
my_driver::type_id::set_type_override(error_driver::get_type());

// 只替换某个层级路径下的 drv
my_driver::type_id::set_inst_override(
  error_driver::get_type(),
  "env.agent.drv"
);
```

| Override 类型 | 影响范围 | 适合场景 |
| --- | --- | --- |
| Type override | 所有该类型的 factory create | 全局替换一种组件或 item |
| Instance override | 指定层级路径下的实例 | 只替换某个 agent 或某个 env 里的实例 |

Override 必须发生在目标对象被 `create()` 之前，通常放在 test 的 `build_phase` 里，并且在 `super.build_phase()` 或 env 创建之前安排好。

### 面试回答

UVM factory allows components and objects to be created through a registered type system instead of hard-coded constructors. The main benefit is override: a test can replace a base driver, monitor, sequence item, or other component with a derived implementation without changing the reusable environment. To make it work, classes must be registered with the factory macros and created using `type_id::create()` rather than `new()`.

### 常见追问

- Factory 和 polymorphism 的关系是什么？
  - Factory 提供创建时的类型替换，polymorphism 保证替换后的派生类仍能通过基类 handle 使用。
- Type override 和 instance override 区别？
  - Type override 全局替换；instance override 只替换指定层级路径。
- 为什么直接 `new()` 会让 factory override 失效？
  - 因为 `new()` 已经写死了构造类型，没有经过 factory 查表和替换。
- Component 和 object 的 factory create 有什么区别？
  - Component 有 UVM hierarchy，需要 `name` 和 `parent`；object 没有 hierarchy，通常只传 `name`。

### 易错点

- 忘记写 factory registration macro。
- 类名注册了，但创建时仍然使用 `new()`。
- Override 设置太晚，对象已经创建完成。
- Instance path 写错，导致 override 没有命中。
- 派生类没有继承原基类，factory override 类型不兼容。

---

<a id="uvm-phases"></a>
## UVM Phase 机制
标签：`#uvm` `#phase` `#dv` `#interview`

### 一句话定义

UVM phase 机制把 testbench 的生命周期拆成固定阶段，让所有 component 按统一顺序完成创建、连接、仿真运行、结果检查和报告。

### 常见 Phase 顺序

| Phase | 类型 | 主要用途 |
| --- | --- | --- |
| `build_phase` | function phase，零时间 | 创建 component，读取 config，搭建 hierarchy |
| `connect_phase` | function phase，零时间 | 连接 TLM port/export、analysis port、sequencer-driver |
| `end_of_elaboration_phase` | function phase，零时间 | 检查结构、打印 topology |
| `start_of_simulation_phase` | function phase，零时间 | 仿真开始前最后准备 |
| `run_phase` | task phase，可消耗时间 | 产生 stimulus、monitor、scoreboard 运行 |
| `extract_phase` | function phase，零时间 | 收集仿真结果 |
| `check_phase` | function phase，零时间 | 检查是否有 error、pending transaction |
| `report_phase` | function phase，零时间 | 输出 summary |
| `final_phase` | function phase，零时间 | 最终清理 |

### Function Phase vs Task Phase

- Function phase 不能消耗仿真时间，适合结构搭建和结果检查。
- Task phase 可以消耗时间，`run_phase` 是最常用的 task phase。
- 多个 component 的 `run_phase` 会并行执行。

### Objection 机制

`run_phase` 需要 objection 告诉 UVM “仿真还不能结束”。

```systemverilog
task run_phase(uvm_phase phase);
  phase.raise_objection(this);

  seq.start(env.agent.seqr);

  phase.drop_objection(this);
endtask
```

如果没有 objection，UVM 可能在 stimulus 还没跑完时结束 run phase。通常 test 或 top-level virtual sequence 负责 raise/drop objection，底层 driver/monitor 一般不随意控制整体仿真结束。

### Phase 中常做什么

```systemverilog
function void build_phase(uvm_phase phase);
  super.build_phase(phase);
  agent = my_agent::type_id::create("agent", this);
endfunction

function void connect_phase(uvm_phase phase);
  super.connect_phase(phase);
  agent.mon.ap.connect(sb.analysis_export);
endfunction

task run_phase(uvm_phase phase);
  phase.raise_objection(this);
  main_seq.start(agent.seqr);
  phase.drop_objection(this);
endtask
```

### 面试回答

UVM phases provide a standard lifecycle for the verification environment. In `build_phase`, components are created and configured. In `connect_phase`, TLM connections are made. In `run_phase`, time-consuming behavior such as sequences, drivers, monitors, and scoreboards runs. After simulation, extract, check, and report phases are used to collect and validate results. The objection mechanism controls when the run phase is allowed to finish.

### 常见追问

- 为什么 `build_phase` 里创建 component，而不是 constructor 里？
  - 因为 build phase 可以利用 factory override 和 config DB，而且符合 UVM 的统一搭建流程。
- `build_phase` 和 `connect_phase` 分别做什么？
  - Build 创建对象和读配置；connect 连接 TLM 通道。
- Objection 谁来 raise/drop？
  - 通常由 test 或 virtual sequence 控制整体 run phase 生命周期。
- 如果忘记 drop objection 会怎样？
  - 仿真可能一直不结束，直到 timeout。

### 易错点

- 在 function phase 里写会消耗时间的代码，例如 `#10`。
- 在对象已经创建之后才设置 factory override。
- 在 `connect_phase` 前试图连接还没创建好的 component。
- Objection raise/drop 不成对。
- 每个低层 component 都控制 objection，导致仿真结束条件混乱。

---

<a id="uvm-virtual-sequence"></a>
## Virtual Sequence / Virtual Sequencer / Sequence API
标签：`#uvm` `#sequence` `#virtual-sequence` `#sequencer` `#dv` `#interview`

### 一句话定义

Virtual sequence 用来协调多个 agent 上的 sequence，virtual sequencer 通常不直接连 driver，而是保存多个 sub-sequencer handle 和共享配置，让一个系统级 sequence 能统一控制多接口 stimulus。

### 普通 Sequence vs Virtual Sequence

| 类型 | 运行位置 | 主要职责 | 是否直接产生 pin-level item |
| --- | --- | --- | --- |
| 普通 sequence | 某个 agent sequencer 上 | 产生该接口的 transaction item | 是，通过该 agent driver 驱动 |
| virtual sequence | virtual sequencer 上，或用 null sequencer 启动后手动拿 handles | 协调多个普通 sequence、寄存器访问、reset/interrupt 等系统场景 | 通常不直接产生 pin-level item |
| virtual sequencer | env 级别的协调器 | 保存多个 agent sequencer handle、RAL model、env config 等共享资源 | 不直接连 driver |

例子：一个 DMA 场景可能需要先通过 APB 配寄存器，再让 AXI master 发 data traffic，同时 monitor interrupt。这个时候单个 AXI sequence 不够，需要 virtual sequence 协调 APB sequence、AXI sequence 和 interrupt checking。

### Virtual Sequencer 常见结构

```systemverilog
class dma_virtual_sequencer extends uvm_sequencer;
  `uvm_component_utils(dma_virtual_sequencer)

  apb_sequencer apb_sqr;
  axi_sequencer axi_sqr;
  dma_reg_block ral;
  dma_env_cfg   cfg;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction
endclass
```

在 `env.connect_phase` 中把各 agent 的 sequencer handle 接到 virtual sequencer：

```systemverilog
function void connect_phase(uvm_phase phase);
  super.connect_phase(phase);
  vseqr.apb_sqr = apb_agent.seqr;
  vseqr.axi_sqr = axi_agent.seqr;
  vseqr.ral     = ral;
endfunction
```

### Virtual Sequence 常见写法

```systemverilog
class dma_smoke_vseq extends uvm_sequence;
  `uvm_object_utils(dma_smoke_vseq)
  `uvm_declare_p_sequencer(dma_virtual_sequencer)

  task body();
    apb_cfg_seq cfg_seq;
    axi_data_seq data_seq;

    cfg_seq  = apb_cfg_seq::type_id::create("cfg_seq");
    data_seq = axi_data_seq::type_id::create("data_seq");

    // 先配置寄存器
    cfg_seq.start(p_sequencer.apb_sqr);

    // 再启动 AXI traffic
    data_seq.start(p_sequencer.axi_sqr);
  endtask
endclass
```

重点：virtual sequence 自己通常不调用 `start_item()` / `finish_item()` 发送 pin-level item，而是调用其他普通 sequence 的 `start(sub_sqr)`。

<a id="uvm-sequence-api"></a>
### `body()` 和 `start()` 的关系

| API | 谁调用 | 作用 |
| --- | --- | --- |
| `seq.start(sequencer)` | test、virtual sequence、parent sequence | 把 sequence 启动到某个 sequencer 上 |
| `body()` | UVM sequence 机制自动调用 | sequence 的主体任务，用户主要在这里写 stimulus 逻辑 |
| `pre_body()` / `post_body()` | UVM 自动调用 | `body()` 前后 hook，常用于 objection 或准备/清理 |

典型启动流程：

```text
test.run_phase()
  └─ vseq.start(env.vseqr)
        ├─ pre_body()
        ├─ body()
        │    ├─ cfg_seq.start(apb_sqr)
        │    └─ data_seq.start(axi_sqr)
        └─ post_body()
```

`start()` 不是“发送一个 transaction”，它是“启动一个 sequence”。真正发送 item 的是普通 sequence 里的 `start_item()` / `finish_item()`。

### `start_item()` 和 `finish_item()`

普通 sequence 产生 transaction item 时常见写法：

```systemverilog
task body();
  axi_item item;

  item = axi_item::type_id::create("item");

  start_item(item);
  if (!item.randomize() with {
    burst_len inside {[1:16]};
    addr[1:0] == 2'b00;
  }) begin
    `uvm_error("RAND", "item randomization failed")
  end
  finish_item(item);
endtask
```

含义：

- `start_item(item)`：向 sequencer 请求 grant，等 sequencer 允许这个 sequence 发送 item。
- `randomize()`：通常放在 `start_item()` 和 `finish_item()` 之间，因为拿到 grant 后再决定最终 item 内容。
- `finish_item(item)`：把 item 发送给 sequencer，driver 之后可以拿到这个 item。

### Driver 端对应流程

Driver 通常这样接收 sequence item：

```systemverilog
task run_phase(uvm_phase phase);
  forever begin
    seq_item_port.get_next_item(req);
    drive_one_transfer(req);
    seq_item_port.item_done();
  end
endtask
```

对应关系：

```text
sequence.start_item(item)
      ↓ request/grant arbitration
sequence.finish_item(item)
      ↓ send_request
driver.get_next_item(req)
      ↓ drive DUT pins
driver.item_done()
      ↓ sequence 可以继续下一个 item
```

### `uvm_do` 宏和显式写法

老代码里可能看到：

```systemverilog
`uvm_do(item)
```

它大致等价于 create、start_item、randomize、finish_item 的组合。但面试和项目里更推荐显式写法，因为更清楚、容易 debug，也方便插入 inline constraint、打印和错误处理。

### 面试回答

中文：Virtual sequence 用来描述系统级场景，它不直接驱动某个接口，而是协调多个 agent 上的普通 sequence。Virtual sequencer 通常放在 env 里，保存 APB/AXI 等 sub-sequencer handle、RAL model 和共享 config。普通 sequence 的 `start()` 用来启动 sequence，`body()` 是 sequence 主体；如果要发送 transaction item，就在普通 sequence 的 `body()` 里用 `start_item()` 等待 sequencer grant，randomize item，再用 `finish_item()` 发送给 driver。Driver 端通过 `get_next_item()` 拿 item，驱动完后调用 `item_done()`。所以 virtual sequence 解决“多接口协调”，`start_item/finish_item` 解决“单接口 item 发送”。

English: A virtual sequence describes a system-level scenario by coordinating multiple lower-level sequences on different agent sequencers. A virtual sequencer usually holds handles to sub-sequencers, the RAL model, and shared configuration. `start()` launches a sequence, and `body()` is where the sequence behavior is written. For a normal transaction sequence, `start_item()` waits for sequencer grant, the item is randomized, and `finish_item()` sends it to the driver. The driver receives it with `get_next_item()` and completes it with `item_done()`.

### 常见追问

- Virtual sequence 一定要 virtual sequencer 吗？
  - 不一定。有些环境会直接把 sub-sequencer handle/config 传给 virtual sequence。但大型 env 里 virtual sequencer 能集中管理 handles，结构更清晰。
- Virtual sequencer 为什么通常不连 driver？
  - 它是协调器，不代表某个真实接口；真正连 driver 的是各 agent sequencer。
- `start()` 和 `start_item()` 的区别？
  - `start()` 启动一个 sequence；`start_item()` 是 sequence 内部发送一个 item 前向 sequencer 请求 grant。
- `finish_item()` 之前为什么常放 randomize？
  - 因为 `finish_item()` 后 item 就会被送给 driver，发送前要完成随机化和字段设置。
- Virtual sequence 里能不能直接 `start_item()`？
  - 通常不这么做。Virtual sequence 一般不绑定具体 item/driver，而是启动 sub-sequence；普通 interface sequence 才直接产生 item。

### 易错点

- 把 virtual sequencer 当成会驱动 pin 的 sequencer。
- 在 virtual sequence 里硬编码 env 层级路径，导致复用性差。
- 忘记在 `connect_phase` 里连接 sub-sequencer handle。
- `start_item()` 后忘记 `finish_item()`，driver 永远拿不到 item。
- Driver `get_next_item()` 后忘记 `item_done()`，sequence 侧会被卡住。

---

<a id="uvm-sequencer-handles"></a>
## `m_sequencer` 和 `p_sequencer` 的区别
标签：`#uvm` `#sequencer` `#sequence` `#dv` `#interview`

### 一句话定义

`m_sequencer` 是 UVM sequence 内置的通用 sequencer handle；`p_sequencer` 是用户通过宏声明出来的强类型 sequencer handle，用来访问自定义 sequencer 的成员。

### `m_sequencer`

`m_sequencer` 来自 `uvm_sequence_base`，当 sequence 被 `start(sequencer)` 启动时，UVM 会自动设置它。

特点：

- 类型比较通用，通常是 `uvm_sequencer_base` 层级的 handle。
- 所有 sequence 都有。
- 适合 UVM 内部机制和通用 sequencer 操作。
- 不能直接访问自定义 sequencer 里的成员变量或子 sequencer。

### `p_sequencer`

`p_sequencer` 不是天然存在的变量，需要在 sequence 中用宏声明：

```systemverilog
class my_sequence extends uvm_sequence #(my_item);
  `uvm_object_utils(my_sequence)
  `uvm_declare_p_sequencer(my_sequencer)

  task body();
    // 可以访问 my_sequencer 中自定义的成员
    p_sequencer.cfg.print();
  endtask
endclass
```

这个宏的本质是把 `m_sequencer` cast 成你指定的 sequencer 类型。如果 sequence 启动在错误类型的 sequencer 上，cast 会失败，通常会报 UVM fatal。

### 对比表

| 项目 | `m_sequencer` | `p_sequencer` |
| --- | --- | --- |
| 是否内置 | 是，sequence 自带 | 否，需要 `` `uvm_declare_p_sequencer`` |
| 类型 | 通用 sequencer base 类型 | 用户指定的具体 sequencer 类型 |
| 能否访问自定义成员 | 不方便，需要手动 cast | 可以直接访问 |
| 耦合度 | 低 | 高，sequence 绑定到特定 sequencer 类型 |
| 常见用途 | 通用 sequence 机制 | virtual sequence 访问 virtual sequencer 中的子 sequencer/config |

### 什么时候用 `p_sequencer`

适合：

- Virtual sequence 需要通过 virtual sequencer 访问多个 agent sequencer。
- Sequence 确实需要 sequencer 中的 config、resource 或 helper method。

不适合：

- 普通 transaction sequence 只是产生 item。
- 可以通过 `uvm_config_db`、sequence field、constructor/config object 传入信息的场景。

过度使用 `p_sequencer` 会让 sequence 和某个 sequencer 类型强绑定，降低复用性。

### 面试回答

`m_sequencer` is the built-in generic sequencer handle inside a UVM sequence. It is set automatically when the sequence is started. `p_sequencer` is a typed handle declared by `uvm_declare_p_sequencer`, and it is basically a cast from `m_sequencer` to a user-defined sequencer type. The benefit is that the sequence can access custom sequencer fields, but the downside is tighter coupling and possible cast failure if the sequence runs on the wrong sequencer.

### 常见追问

- 为什么很多代码里不推荐随便用 `p_sequencer`？
  - 因为它让 sequence 依赖具体 sequencer 类型，复用性变差。
- `p_sequencer` 常在哪种场景最合理？
  - Virtual sequence 访问 virtual sequencer 里的多个 sub-sequencer。
- 如果 sequence start 在错误的 sequencer 上会怎样？
  - `p_sequencer` cast 失败，通常触发 UVM fatal。
- 不用 `p_sequencer` 怎么传配置？
  - 可以把 config object 作为 sequence 字段传入，或用 `uvm_config_db`/resource/config handle 管理。

### 易错点

- 以为 `p_sequencer` 是 UVM 自动存在的变量。
- 忘记写 `` `uvm_declare_p_sequencer(my_sequencer)``。
- 在普通 sequence 里为了方便访问 config 而滥用 `p_sequencer`。
- Sequence 被复用到另一个 sequencer 类型时才发现 cast failure。

---

<a id="uvm-axi-dma-vseq-flow"></a>
## AXI DMA 项目：sequence / vsequence / virtual sequencer 调用链
标签：`#uvm` `#sequence` `#virtual-sequence` `#sequencer` `#ral` `#axi-dma` `#project`

### 一句话定义

这个 AXI DMA 项目用 test 创建并启动 virtual sequence，virtual sequence 挂在 env 里的 `dma_virtual_sequencer` 上；virtual sequencer 保存 AXI-Lite sequencer、AXI memory sequencer、memory model、RAL model 和 IRQ interface 的 handle，vseq 通过 `p_sequencer` 统一访问这些资源。

### 项目里的调用链

```text
dma_*_test.run_phase()
  ├─ phase.raise_objection()
  ├─ seq = xxx_vseq::type_id::create("seq")
  └─ seq.start(env.vseqr)
        ↓ UVM 设置 sequence.m_sequencer = env.vseqr
        ↓ `uvm_declare_p_sequencer(dma_virtual_sequencer)` 把 m_sequencer cast 成 p_sequencer
      xxx_vseq.body()
        ├─ p_sequencer.mem.fill_incrementing(...)      // 预置 memory model 数据
        ├─ program_desc(...) / start_dma(...)           // 调 RAL frontdoor 写 CSR
        └─ wait_done() / wait_error()                   // 通过 irq_vif 等中断
```

这个项目中，`single_desc_transfer_test`、`multi_desc_transfer_test` 等 test 都是同一个模式：在 `run_phase` 里 create 对应 vseq，然后 `seq.start(env.vseqr)`。所以 **vsequence 是被 test 挂到 virtual sequencer 上的**，不是由 env 自动启动，也不是通过 default sequence 配置启动。

### Sequence 是怎么产生 stimulus 的

本项目主要有三类 stimulus 来源：

| 来源 | 代码位置 | 产生方式 | 最终作用 |
| --- | --- | --- | --- |
| DMA 场景 vseq | `dma_vseqs.svh` | test 通过 factory create 具体 vseq；vseq 的 `body()` 编排场景 | 配描述符、启动 DMA、等 IRQ |
| AXI-Lite CSR item | RAL + `dma_reg_adapter` | vseq 调 `rg.write/read()`；adapter 的 `reg2bus()` 生成 `dma_axil_item` | AXI-Lite driver 驱动 CSR 总线 |
| AXI memory response item | `dma_mem_error_resp_seq` | 可选 sequence 用 `start_item/finish_item` 发送 `dma_axi_mem_item` | slave BFM 用 `try_next_item()` 覆盖默认 response |

注意：正常搬运的数据不是由 AXI memory sequence 主动发出的。DMA DUT 是 AXI master，memory agent 是 slave BFM；vseq 只是预先调用 `p_sequencer.mem.fill_incrementing()` 填 memory model，之后由 DUT 发 AXI read/write，slave BFM 读写这个 memory model。

### Vsequence 怎么挂到 sequencer 上

基础类 `dma_base_vseq` 写法：

```systemverilog
class dma_base_vseq extends uvm_sequence;
  `uvm_object_utils(dma_base_vseq)
  `uvm_declare_p_sequencer(dma_virtual_sequencer)
endclass
```

test 中启动：

```systemverilog
seq = single_desc_transfer_vseq::type_id::create("seq");
seq.start(env.vseqr);
```

`start(env.vseqr)` 做两件关键事：

- UVM 把这个 sequence 的 `m_sequencer` 设成 `env.vseqr`。
- `` `uvm_declare_p_sequencer(dma_virtual_sequencer)`` 在 sequence 内得到强类型 `p_sequencer`，于是 vseq 可以访问 `p_sequencer.ral`、`p_sequencer.mem`、`p_sequencer.irq_vif` 等成员。

因此，`p_sequencer` 不是手动赋值的普通变量，而是 sequence 启动到正确 sequencer 后由 UVM/macro 机制建立的 typed handle。如果把这个 vseq start 到普通 AXI-Lite sequencer 上，`p_sequencer` cast 会失败。

### RAL frontdoor 如何转到 AXI-Lite sequencer

vseq 里并没有直接写：

```systemverilog
axil_seq.start(p_sequencer.axil_sqr);
```

而是通过 RAL：

```systemverilog
rg.write(status, value, UVM_FRONTDOOR, p_sequencer.ral.default_map, this);
```

env 在 `connect_phase` 里做了关键接线：

```systemverilog
cfg.ral.default_map.set_sequencer(axil_agent.sqr, reg_adapter);
```

所以 RAL frontdoor 访问会走：

```text
vseq.csr_write()
  └─ rg.write(..., p_sequencer.ral.default_map, this)
        └─ default_map 已绑定 axil_agent.sqr + reg_adapter
              └─ reg_adapter.reg2bus() 生成 dma_axil_item
                    └─ axil_agent.sqr → dma_axil_driver.get_next_item()
                          └─ drive_write()/drive_read() 驱动 AXI-Lite pin
```

这就是这个项目里“virtual sequence 统一编排系统场景，实际 CSR transaction 通过 RAL 映射到 AXI-Lite sequencer”的核心路径。

### Virtual sequencer 怎么保留所有 sequencer handle

`dma_virtual_sequencer` 本身只声明 handle，不创建 sub-sequencer：

```systemverilog
class dma_virtual_sequencer extends uvm_sequencer;
  dma_axil_sequencer    axil_sqr;
  dma_axi_mem_sequencer mem_sqr;
  dma_memory_model      mem;
  dma_ral_block         ral;
  virtual dma_irq_if    irq_vif;
endclass
```

env 负责创建 agent 和 virtual sequencer，然后在 `connect_phase` 把实际对象接进去：

```systemverilog
vseqr.axil_sqr = axil_agent.sqr;
vseqr.mem_sqr  = mem_agent.sqr;
vseqr.mem      = cfg.mem;
vseqr.ral      = cfg.ral;
vseqr.irq_vif  = cfg.irq_vif;
```

handle 的 ownership 关系要分清：

- `axil_agent.sqr` 和 `mem_agent.sqr` 由各自 agent 在 `build_phase` 创建。
- `vseqr` 由 env 在 `build_phase` 创建。
- `vseqr` 在 `connect_phase` 保存这些 handle，自己不 new sub-sequencer。
- vseq 被 `start(env.vseqr)` 后，通过 `p_sequencer.xxx` 使用这些 handle。

### 面试回答

中文：这个项目的 test 在 `run_phase` 里 create 具体 virtual sequence，然后 `seq.start(env.vseqr)` 把它启动到 env 的 virtual sequencer 上。`dma_base_vseq` 用 `` `uvm_declare_p_sequencer(dma_virtual_sequencer)``，所以 start 之后 vseq 可以通过 `p_sequencer` 访问 virtual sequencer 中保存的 `axil_sqr`、`mem_sqr`、`mem`、`ral` 和 `irq_vif`。CSR 访问不是手写 AXI-Lite sequence，而是 vseq 调 RAL 的 `write/read`；env 里 `default_map.set_sequencer(axil_agent.sqr, reg_adapter)` 把 RAL frontdoor 绑定到 AXI-Lite sequencer，adapter 再把 register operation 转成 `dma_axil_item` 给 driver。AXI memory agent 是 slave BFM，正常数据通过 shared memory model 预置和检查，memory sequencer 主要用于可选的 response/error injection。

English: In this AXI DMA environment, each test creates a virtual sequence in `run_phase` and starts it on `env.vseqr`. The base virtual sequence declares a typed `p_sequencer` for `dma_virtual_sequencer`, so after `start()` it can access the virtual sequencer's sub-sequencer handles, memory model, RAL model, and IRQ interface. CSR accesses are issued through RAL frontdoor operations; the RAL map is connected to the AXI-Lite sequencer with a register adapter, which converts register operations into AXI-Lite sequence items. The AXI memory agent works as a slave BFM, so normal data traffic comes from the DUT as AXI master, while the memory sequencer is mainly useful for optional response or error injection.

### 易错点

- 以为 vseq 里的 `csr_write()` 直接调用 AXI-Lite driver；实际路径是 RAL default map → adapter → AXI-Lite sequencer → driver。
- 以为 virtual sequencer 会创建 sub-sequencer；实际 sub-sequencer 由 agent 创建，virtual sequencer 只保存 handle。
- 以为 memory sequencer 会产生正常 AXI data traffic；这个项目里 DUT 是 AXI master，memory agent 是 slave BFM，正常数据来自 DUT 访问 memory model。
- 忘记 active/passive 配置影响 agent 是否创建 `sqr/driver`；如果 agent passive，相关 handle 可能是 null。

---

<a id="uvm-advanced-patterns"></a>
## UVM 高级技巧（来自 AXI DMA 项目）
标签：`#uvm` `#dv` `#advanced` `#axi` `#project`

这一节整理自一个完整的 AXI DMA UVM 验证项目，提炼项目中常见但面试容易被问到的 UVM 技巧。

### 1. Virtual Sequencer 持有共享资源

Virtual sequencer 不仅仅连接多个 sub-sequencer，还可以持有 testbench 里的共享对象：

```systemverilog
class dma_virtual_sequencer extends uvm_sequencer;
  dma_axil_sequencer  axil_sqr;  // AXI-Lite master
  dma_axi_mem_sequencer mem_sqr; // AXI memory slave
  dma_memory_model    mem;       // 共享 byte-addressable memory model
  dma_ral_block       ral;       // RAL register model
  virtual dma_irq_if  irq_vif;  // IRQ 接口，用于等待中断
endclass
```

Virtual sequence 通过 `p_sequencer` 直接访问这些资源：

```systemverilog
p_sequencer.mem.fill_incrementing(src_addr, num_bytes);
rg = p_sequencer.ral.default_map.get_reg_by_offset(addr, is_read);
@(posedge p_sequencer.irq_vif.clk);
```

设计要点：把所有 virtual sequence 需要的共享对象都放在 virtual sequencer 里，避免 virtual sequence 通过 config_db 或 global variables 获取。

### 2. fork/join_any + disable fork 实现超时等待

等待中断时，需要同时有一个 timeout 保护机制：

```systemverilog
task wait_irq(bit expect_error, int unsigned timeout_cycles = 20000);
  fork
    begin
      // 等 DMA 完成或出错
      do begin
        @(posedge p_sequencer.irq_vif.clk);
      end while (!p_sequencer.irq_vif.done && !p_sequencer.irq_vif.error);
    end
    begin
      // timeout 分支
      repeat (timeout_cycles) @(posedge p_sequencer.irq_vif.clk);
      `uvm_fatal(get_type_name(), "Timed out waiting for DMA interrupt")
    end
  join_any
  disable fork;  // 哪个分支先结束，就 kill 掉另一个
endtask
```

`fork/join_any`：任意一个分支结束后 continue；`disable fork`：杀掉同 scope 下所有还在运行的 fork 分支。这是 UVM sequence 中处理超时的标准模式。

### 3. Slave BFM Driver：响应 DUT Master

一般 agent 的 driver 是 active master（向 DUT 发 stimulus），但 AXI memory agent 的 driver 是 slave BFM——它要响应 DUT 作为 AXI master 发来的 read/write 请求。

架构特点：
- 每个 AXI channel 独立一个 task，在 `run_phase` 里用 `fork join` 并行运行：

```systemverilog
task run_phase(uvm_phase phase);
  fork
    write_address_channel();
    write_data_channel();
    write_response_channel();
    read_address_channel();
    read_response_channel();
  join
endtask
```

- `write_req_q`、`write_rsp_q`、`read_req_q`：用 queue 在各 task 之间传递请求，解耦 address 接受和 data/response 阶段。
- Semaphore `resp_lock`：保护 `try_next_item()` 调用，防止多个 channel task 并发冲突。

### 4. `try_next_item()` 实现非阻塞 Error Injection

普通 driver 用 `get_next_item()` 阻塞等待 sequence；但 slave BFM 大多数时候用默认 response，只有在 test 注入错误时才用非默认 response：

```systemverilog
protected task automatic get_next_response(input  axi_resp_t default_resp,
                                           output axi_resp_t use_resp);
  dma_axi_mem_item req;

  resp_lock.get();
  seq_item_port.try_next_item(req);  // 非阻塞：没有 item 时不等待
  if (req != null) begin
    use_resp = req.resp;             // 有 item：用 test 注入的 resp
    seq_item_port.item_done();
  end else begin
    use_resp = default_resp;         // 无 item：用默认 OKAY
  end
  resp_lock.put();
endtask
```

`try_next_item()` 的价值：driver 不用永久跑一个 "background sequence"。Test 通过按需发送带错误 resp 的 item 来注入，不需要时 driver 自动 fallback。

### 5. Scoreboard 内嵌 Covergroup（Outstanding tracking）

Scoreboard 不仅做数据比较，还可以内嵌 coverage：

```systemverilog
covergroup outstanding_cg with function sample(dma_axi_mem_dir_e dir,
                                               int unsigned outstanding);
  direction_cp: coverpoint dir { bins read  = {AXI_MEM_READ};
                                 bins write = {AXI_MEM_WRITE}; }
  depth_cp: coverpoint outstanding { bins one  = {1};
                                     bins low  = {[2:3]};
                                     bins high = {[4:7]};
                                     bins max  = {8}; }
  direction_x_depth: cross direction_cp, depth_cp;
endgroup
```

每当 monitor 报告一个完成的 AXI burst，scoreboard 的 `write()` 函数就采样一次，同时记录到目前为止的最大 outstanding depth。`outstanding_stress_test` 就是验证 outstanding depth 能达到 DMA 设计的最大窗口值。

### 6. RAL + Predictor + Adapter 接线模式

```systemverilog
// connect_phase 中的接线
cfg.ral.default_map.set_sequencer(axil_agent.sqr, reg_adapter);
cfg.ral.default_map.set_auto_predict(0);   // 关闭 auto predict，用 explicit predictor

reg_predictor.map     = cfg.ral.default_map;
reg_predictor.adapter = reg_adapter;
axil_agent.mon.ap.connect(reg_predictor.bus_in);  // monitor → predictor
```

- `set_auto_predict(0)`：关闭工具自动更新 mirror，由 explicit predictor 负责，更可控。
- Monitor 的 analysis port 接到 predictor 的 bus_in：每次总线上有实际访问，predictor 用 adapter.bus2reg() 换算成 register operation，再更新 model mirror。

---

<a id="uvm-ral"></a>
## Register Model / UVM RAL
标签：`#uvm` `#ral` `#register-model` `#dv` `#interview`

### 一句话定义

寄存器模型（UVM Register Abstraction Layer, RAL）是在 testbench 里建立一份 DUT register map 的抽象模型，让验证环境可以用统一 API 访问寄存器，而不是在每个 test 里手写 address、data、mask 和 bus transaction。

### 它解决什么问题

如果没有 register model，test 访问寄存器通常要直接写：

- 具体 address。
- 读写方向。
- byte enable / mask。
- bus protocol transaction。
- reset value 和 field bit position。
- expected value 的维护。

寄存器一多，这些信息会散落在 test、sequence、scoreboard 和 checker 里，很难维护。RAL 把这些内容集中成一个结构化模型：

```text
reg_block
  ├── reg CTRL
  │     ├── field enable [0]
  │     └── field mode   [3:1]
  ├── reg STATUS
  │     ├── field busy
  │     └── field error
  └── address map
```

### RAL 层次结构

RAL 通常分三层：

| DUT 概念 | UVM RAL 类 | 例子 |
| --- | --- | --- |
| 一个 register block | `uvm_reg_block` | DMA 的全部 CSR 寄存器组 |
| 一个 register | `uvm_reg` | `CTRL`、`STATUS`、`SRC_ADDR` |
| 一个 register field | `uvm_reg_field` | `CTRL.enable`、`STATUS.done` |

一个 DMA `CTRL` register 可以建模成：

```text
dma_reg_block
  └── ctrl_reg
        ├── enable      bit[0]
        ├── irq_en      bit[1]
        ├── soft_reset  bit[2]
        └── reserved    bit[31:3]
```

所以 RAL 的重点不是只保存地址，而是同时保存 address、field bit position、access policy、reset value 和 mirror state。

### 主要用途

| 用途 | 解释 |
| --- | --- |
| 统一寄存器访问 | test 可以调用 `reg.write()` / `reg.read()`，不用关心底层 APB/AXI/I2C transaction 细节 |
| 保存 register map | 记录每个 register 的 address、field、bit width、access type、reset value |
| Mirror value | 在 testbench 中维护一份“模型认为的寄存器值” |
| Predict | 当 bus monitor 看到一次真实写入时，更新 model 中的 mirror value |
| Check | 读回 DUT register 后和 mirror/expected value 比较 |
| Frontdoor access | 通过真实 bus interface 访问寄存器，接近真实软件行为 |
| Backdoor access | 绕过 bus，直接通过 HDL path 读写寄存器，速度快，适合初始化或检查 |
| Reuse | 同一份 register model 可被 test、sequence、scoreboard、coverage、firmware-like sequence 复用 |

### Frontdoor vs Backdoor

| 访问方式 | 含义 | 优点 | 风险/限制 |
| --- | --- | --- | --- |
| Frontdoor | 通过真实总线协议访问 register | 能验证 bus path、decoder、权限、side effect | 慢，需要 bus agent，受 protocol timing 影响 |
| Backdoor | 通过 HDL path 直接访问 register storage | 快，适合初始化、大量检查、debug | 不验证真实 bus path，可能绕过 side effect |

面试里可以这样说：frontdoor 更接近真实软件访问；backdoor 更适合仿真加速和 debug，但不能代替 frontdoor verification。

### Map 和 Adapter

RAL 要靠 `map` 知道每个寄存器在哪个地址：

```systemverilog
default_map = create_map("default_map", 'h0, 4, UVM_LITTLE_ENDIAN);

default_map.add_reg(ctrl,     'h00, "RW");
default_map.add_reg(status,   'h04, "RO");
default_map.add_reg(src_addr, 'h08, "RW");
default_map.add_reg(dst_addr, 'h0c, "RW");
default_map.add_reg(length,   'h10, "RW");
```

RAL 内部用 `uvm_reg_bus_op` 表示一次 register operation，但 APB/AXI-Lite driver 需要自己的 bus item，所以需要 adapter 做双向转换：

```text
uvm_reg_bus_op  <──>  axi_lite_item / apb_item
```

典型连接：

```systemverilog
ral.default_map.set_sequencer(axi_lite_agent.sqr, axi_lite_adapter);
```

意思是：之后 `ral.xxx.write/read()` 的 frontdoor 访问，都通过这个 sequencer 发出去，并用 adapter 转成 bus transaction。

### Mirror 和 Predict

- **Mirror value**：register model 里保存的当前期望值。
- **Prediction**：当 testbench 观察到一次寄存器读写后，更新 mirror value。
- **Explicit prediction**：test/sequence 调用 RAL API 后，模型根据这次操作主动更新 mirror。
- **Implicit prediction / auto prediction**：bus monitor 采集真实 transaction，经 adapter 转成 register operation，再由 predictor 更新 model。

如果 mirror 没维护好，后面的 `mirror()`、`check()` 或 scoreboard 比较就会误报。

### 常用 API

| API | 作用 | 典型使用 |
| --- | --- | --- |
| `write(status, data)` | 直接写 DUT register | 配置控制寄存器 |
| `read(status, data)` | 从 DUT register 读值 | polling status |
| `mirror(status, UVM_CHECK)` | 读 DUT 并和 mirror value 比较 | 寄存器一致性检查 |
| `predict(data)` | 手动更新 mirror | 硬件自动更新 status 后，testbench 更新模型预期 |
| `get_mirrored_value()` | 获取 RAL 当前认为的值 | scoreboard/reference 使用配置值 |
| `set(data)` | 设置 desired value，不一定立刻访问 DUT | 批量准备配置 |
| `update(status)` | 把 desired value 同步写到 DUT | `set()` 之后统一写入 |

`write/read` 是直接访问 DUT；`set/update` 是先改 RAL model 的 desired value，再由 `update()` 同步到 DUT。面试里可简单说：**write = 直接写；set + update = 先准备，再同步。**

### RAL、Sequence 和 Scoreboard 的关系

RAL 不替代 sequence，也不替代 scoreboard：

| 对象 | 主要职责 |
| --- | --- |
| Sequence / virtual sequence | 组织测试流程：初始化、配置寄存器、启动 DUT、等待 done/error、检查结果 |
| RAL | 抽象寄存器访问和维护 register-level mirror/check |
| Scoreboard | 做功能正确性检查，比如数据搬运、协议响应、端到端结果 |

例如 DMA 测试里，virtual sequence 先预置 source memory，再用 RAL 配置 `src_addr/dst_addr/length/control`，等待中断后由 scoreboard 或 memory model 检查 destination 数据。RAL 负责“寄存器配置和状态”，scoreboard 负责“DMA 搬运是否真的正确”。

### Adapter 和 Predictor

RAL 本身是 register-level 抽象，但 DUT 接口是 bus-level transaction，所以需要 adapter 做转换：

```text
reg.write()/read()
      ↓
uvm_reg_adapter
      ↓
bus transaction(APB/AXI/etc.)
      ↓
driver -> DUT
```

Predictor 则走反方向：

```text
bus monitor transaction
      ↓
uvm_reg_adapter.bus2reg()
      ↓
uvm_reg_predictor
      ↓
update register model mirror
```

在更完整的 UVM 环境里，常见做法是关闭 auto prediction，用 monitor + predictor 更新 mirror：

```systemverilog
ral.default_map.set_auto_predict(0);
reg_predictor.map     = ral.default_map;
reg_predictor.adapter = reg_adapter;
axil_agent.mon.ap.connect(reg_predictor.bus_in);
```

这样 mirror 来自真实 bus monitor transaction，而不是只相信 sequence 发起的意图，更适合检查实际总线行为。

### 面试回答

中文：寄存器模型的作用是把 DUT 的 register map 在 UVM testbench 中抽象出来，统一管理 address、field、reset value、access type 和 mirror value。这样 test 可以用 `reg.write()`、`reg.read()` 这类 register-level API，而不用每次手写底层 bus transaction。它还支持 frontdoor/backdoor access、mirror/check、prediction 和 register coverage。对复杂 SoC 或大量寄存器的模块来说，RAL 能提高复用性、减少 hard-code address，并且让寄存器测试、scoreboard 和 firmware-like sequence 更容易维护。

English: A UVM register model abstracts the DUT register map inside the testbench. It stores register addresses, fields, access policies, reset values, and mirrored values, and provides APIs such as `write()`, `read()`, `mirror()`, and `predict()`. The benefit is that tests can operate at register level instead of manually creating bus transactions. It also supports frontdoor/backdoor access, prediction, checking, and register coverage, which makes register verification more reusable and maintainable.

### 常见追问

- Register model 和普通 scoreboard 有什么关系？
  - RAL 主要维护 register-level expected/mirror state；scoreboard 可以使用 RAL 中的值作为 reference 的一部分，但 RAL 不等于完整功能 scoreboard。
- 为什么需要 frontdoor？
  - 因为 frontdoor 通过真实 bus path，可以验证 decoder、bus protocol、权限、side effect。
- 为什么还需要 backdoor？
  - Backdoor 快，适合初始化、debug、批量检查，但不能验证真实 bus path。
- `mirror()` 和 `read()` 区别？
  - `read()` 是读 DUT；`mirror()` 通常会读 DUT 并和 model mirror value 比较，重点在 check。
- `predict()` 是干什么的？
  - `predict()` 用来更新 RAL mirror，尤其适合硬件自动改变的 status/interrupt register，或由 predictor 根据 monitor 看到的 bus transaction 更新 mirror。
- `write/read` 和 `set/update` 区别？
  - `write/read` 直接访问 DUT；`set()` 只改 desired value，`update()` 再把 desired value 写到 DUT。
- RAL 为什么需要 adapter 和 map？
  - Map 记录 register 到地址的映射；adapter 把 `uvm_reg_bus_op` 转成 APB/AXI-Lite item，并把 bus item 转回 register operation。
- 什么是 register side effect？
  - 比如 read-clear、write-one-to-clear、write-only、read-only、sticky bit，这些都要在 model access policy 和 prediction 中正确处理。

### 易错点

- 以为 register model 只是“寄存器地址表”，忽略 mirror/predict/check。
- 以为有 RAL 就不用 sequence；实际 sequence 仍负责组织测试流程。
- 以为有 RAL 就不用 scoreboard；实际 RAL 做 register-level state，scoreboard 做功能级 end-to-end check。
- Backdoor 用得太多，导致 bus path 没有被充分验证。
- Register reset value、access type、volatile field 建模错误，造成误报。
- Auto prediction 和 explicit prediction 同时打开，可能导致 mirror 更新两次。
- 没有处理 read-clear、write-one-to-clear 这类 side effect。
---

<a id="sv-uvm-interview-answers"></a>
## 面试回答速查（中文 + English）
### 动态数组、关联数组、队列

中文：动态数组是运行时分配大小的连续数组，适合长度运行时才知道但当前长度相对固定的数据；关联数组是 key-value 稀疏映射，适合 scoreboard 里按 ID/address 查 transaction；队列是有序动态容器，支持 push/pop，适合 FIFO 或 pending transaction list。

English: A dynamic array is a runtime-sized contiguous array. An associative array is a sparse key-value container, useful for scoreboards indexed by ID or address. A queue is an ordered dynamic container with push/pop operations, useful as a FIFO or pending transaction buffer.

### SV 随机化

中文：SV 随机化用 `rand/randc` 声明随机字段，用 constraint 描述合法空间，调用 `randomize()` 让 solver 求解。它的价值是自动探索大量合法场景，再配合 functional coverage 判断有没有覆盖到目标 corner case。Debug randomization fail 时要检查返回值、约束冲突、inline constraint、`constraint_mode` 和配置字段。

English: SystemVerilog randomization uses `rand/randc` variables and constraints to generate legal stimulus. The solver finds values satisfying all active constraints. It is usually combined with functional coverage to explore legal scenarios and close coverage holes.

### Cast / upcast / downcast

中文：隐式转换由编译器自动完成，比如赋值时的宽度/符号转换，class 中派生类 handle 赋给基类 handle 也是隐式 upcast。显式转换由工程师写出目标类型，比如 `byte'(i)`、`$signed(x)` 或 `$cast()`。Upcast 后只能访问基类成员；downcast 必须用 `$cast()` 检查运行时对象类型，常见于 UVM factory override 后 base handle 实际指向 derived object 的场景。

English: Implicit conversions are performed automatically by the compiler, for example width/sign conversions in assignments or class upcasting from a derived handle to a base handle. Explicit conversions are written by the engineer, such as `byte'(i)`, `$signed(x)`, or `$cast()`. Downcasting should use `$cast()` to check the runtime object type.

### UVM factory

中文：UVM factory 是创建和替换对象的机制。类注册到 factory 后，用 `type_id::create()` 创建，test 就可以用 type override 或 instance override 把 base component/object 换成派生类，而不用改 env 源码。直接 `new()` 会绕过 factory，所以 override 不生效。

English: UVM factory creates registered objects/components and supports type or instance override. It lets a test replace a base implementation with a derived one without modifying the reusable environment. Direct `new()` bypasses the factory.

### UVM TLM 通信

中文：UVM TLM 用 port/export/imp/FIFO 在组件之间传 transaction，核心价值是解耦。最常见模式是 monitor 用 analysis port 广播 transaction，scoreboard/coverage 用 analysis imp 或 analysis FIFO 接收；如果需要缓存和阻塞式读取，就用 `uvm_tlm_analysis_fifo`。

English: UVM TLM passes transactions between components through ports, exports, imps, and FIFOs. The key benefit is decoupling. A monitor commonly broadcasts transactions through an analysis port, while a scoreboard or coverage collector receives them through an analysis imp or analysis FIFO.

### UVM phase / objection

中文：UVM phase 定义 testbench 生命周期：build 创建组件和读配置，connect 连接 TLM，run 执行耗时 stimulus/checking，check/report 做结束检查。Objection 用来控制 run phase 什么时候结束；如果不 raise，仿真可能过早结束；如果忘记 drop，仿真可能挂住。

English: UVM phases define the testbench lifecycle. Build creates and configures components, connect wires TLM connections, run performs time-consuming behavior, and check/report validate results. Objections control when run phase can end.

### Virtual sequence / virtual sequencer / sequence API

中文：Virtual sequence 用来协调多个 agent 的普通 sequence，适合多接口或系统级场景；virtual sequencer 保存 sub-sequencer handle、RAL model 和 config。`start()` 是启动 sequence，`body()` 是 sequence 主体；`start_item()` / `finish_item()` 是普通 sequence 发送 transaction item 给 driver 的流程。

English: A virtual sequence coordinates lower-level sequences across multiple agent sequencers. A virtual sequencer holds sub-sequencer handles, the RAL model, and shared configuration. `start()` launches a sequence, `body()` implements its behavior, and `start_item()` / `finish_item()` send transaction items to the driver.

### `m_sequencer` vs `p_sequencer`

中文：`m_sequencer` 是 sequence 自带的通用 sequencer handle；`p_sequencer` 是用宏声明出来的强类型 handle，本质上是把 `m_sequencer` cast 成指定 sequencer 类型。它方便访问自定义 sequencer 成员，但会让 sequence 和具体 sequencer 类型耦合更强。

English: `m_sequencer` is the built-in generic sequencer handle. `p_sequencer` is a typed handle declared with `uvm_declare_p_sequencer`, essentially a cast from `m_sequencer` to a user-defined sequencer type. It is convenient but increases coupling.

### Register model / UVM RAL

中文：寄存器模型把 DUT 的 register map 抽象到 testbench 中，统一管理 address、field、reset value、access policy 和 mirror value。test 可以用 register-level API 读写寄存器，不用手写底层 bus transaction；同时支持 frontdoor/backdoor、prediction、mirror/check 和 register coverage。

English: A UVM register model abstracts the DUT register map and provides register-level APIs for tests. It manages addresses, fields, reset values, access policies, and mirrored values, and supports frontdoor/backdoor access, prediction, checking, and register coverage.


