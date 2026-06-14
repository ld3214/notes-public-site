[返回目录](../index.md)

# Design Verification 知识库

这个文件集中放 DV flow、testplan、coverage、scoreboard、debug 和 regression。

## 页内目录

- [DV 总览](#dv-overview)
- [Verification Plan](#verification-plan)
- [Functional Coverage](#functional-coverage)
- [Debug 方法](#debug-methods)
- [书籍整理：验证基础高频框架](#book-dv-fundamentals)
- [VIP checker vs Scoreboard](#vip-checker-scoreboard)
- [Formal Verification](#formal-verification)
- [面试回答速查（中文 + English）](#dv-interview-answers)

---
<a id="dv-overview"></a>
## DV 总览
标签：`#dv` `#interview`

## 学习地图

- Verification plan
- Testbench architecture
- Directed test
- Constrained random verification
- Functional coverage
- Code coverage
- Assertions
- Scoreboard/reference model
- Debug and regression

## 面试表达

Design Verification is about proving that the design behaves as intended under realistic and corner-case scenarios, using a combination of stimulus generation, checking, coverage, assertions, and systematic debug.


## 面经高频入口

- [DV 面经知识点汇总](../question-bank/dv-online-digest.md#common-directions)
- [Verification Plan](#verification-plan)
- [Functional Coverage](#functional-coverage)
- [Debug 方法](#debug-methods)

## 高频能力模型

- 能从 spec 拆 verification plan。
- 能解释 testbench architecture 和各组件职责。
- 能用 constrained random + coverage closure 收敛验证。
- 能设计 self-checking scoreboard/reference model。
- 能用 assertion 捕捉协议和时序规则。
- 能系统 debug regression failure。
## 待补充

- 一个完整 DV flow 怎么讲
- Verification plan 怎么写
- Coverage closure 怎么做

---

<a id="verification-plan"></a>
## Verification Plan
标签：`#dv` `#testplan` `#interview`

## 核心概念

Verification plan（testplan）是从 spec 出发，系统列出"要验证什么"、"怎么验证"和"怎么判断验证完成"的文档。它是 coverage model 和测试用例的基础，也是 DV 工程师和设计工程师对齐的主要沟通工具。

**为什么需要 Verification Plan**

- 防止重要 feature 被遗漏。
- 让 functional coverage model 有据可查，每个 coverpoint 都能对应 spec 里的一个功能点。
- 提供 pass/fail 判断依据，避免"跑完没 error 就算通过"的不严谨做法。
- 为 regression 策略、优先级排序提供框架。

**Verification Plan 的典型内容**

1. **Feature list**：从 spec 拆出所有需要验证的功能，例如正常读写、边界地址、burst 类型、错误响应、reset 行为、低功耗状态等。

2. **Test scenarios**：每个 feature 对应哪些测试场景，包括 happy path、corner case、error injection、concurrent stimulus。

3. **Checkers / Assertions**：每个场景用什么方式检查正确性——scoreboard 比较、property assertion、output signal check、protocol checker。

4. **Functional coverage model**：把 feature 转成 covergroup/coverpoint/cross。每个 bin 对应 spec 里可数的一种状态或事件。

5. **Pass/fail criteria**：什么叫"通过"？功能正确 + coverage 达标 + assertion 无违例 + regression 通过率满足要求。

6. **Regression strategy**：哪些 test 进 nightly regression、哪些只在 feature 开发时跑、seed 管理策略、覆盖率 merge 和报告。

**从 spec 到 testplan 的步骤（以 FIFO 为例）**

1. 读 spec：depth、width、sync/async、almost full/empty、overflow/underflow、reset。
2. 拆 feature：basic write、basic read、full/empty、simultaneous read-write、wrap-around、reset during traffic、backpressure。
3. 写 coverage model：occupancy bins（0, 1, half, full-1, full）、full/empty flag、同时读写 bins。
4. 写 assertion：full 时 write 不允许写入数据、empty 时 read 输出无效、指针回绕一致性。
5. 写 scoreboard/reference model：用 queue 建 reference FIFO，逐笔比较读出数据。
6. 确定 regression：directed bring-up test + constrained random test，coverage closure 目标。

## 面试回答

A verification plan starts from the specification and lists all features to be verified, the corresponding test scenarios, the checking strategy, the functional coverage model, and the pass/fail criteria. For each feature in the spec, I would create a coverpoint in the coverage model so that coverage results can be traced back to specific design requirements. Verification is considered sufficient when all functional coverage bins are closed, all assertions pass, and the regression meets the agreed pass rate. If coverage cannot be closed, I would analyze each hole to determine whether the scenario is unreachable by design, blocked by a constraint, or missing a directed test.

## 常见追问

- Testplan 和 coverage model 怎么对应？
  - Testplan 里每个 feature 对应 coverage model 里的一个或多个 coverpoint；bin 表示 feature 的不同子状态或事件，跑完后通过 bin 命中情况判断 feature 是否被覆盖到。
- 如何判断验证已经足够？
  - Functional coverage 目标达成 + assertions 无违例 + regression pass rate 满足要求 + 关键 feature 有 directed test 验证 + 设计工程师确认边界条件正确。
- 如果 coverage 上不去怎么办？
  - 先分析 hole 是因为 constraint 太严、seed 不够多、feature 被配置关闭、coverage model 写错，还是真实缺测试；然后针对性调 constraint、加 directed test 或修 coverage model。

---

<a id="functional-coverage"></a>
## Functional Coverage
标签：`#dv` `#coverage` `#systemverilog` `#interview`

## 核心概念

**Functional coverage vs Code coverage**

| 维度 | Functional Coverage | Code Coverage |
| --- | --- | --- |
| 测量对象 | Spec 中的功能场景是否被命中 | RTL 代码是否被执行 |
| 定义者 | DV 工程师根据 spec 手写 | 仿真工具自动统计 |
| 类型 | Covergroup / coverpoint / cross | Line、branch、toggle、FSM、condition |
| 100% 的含义 | 所有定义的功能场景都被命中 | 所有 RTL 行/分支/信号翻转都被触发 |
| 局限 | 没写到的场景不会被统计 | 代码被执行不等于功能逻辑正确 |

两者互补，不能互相替代。100% code coverage + 0% functional coverage = 跑了很多仿真但没覆盖到目标场景；100% functional coverage + 没 checker = 覆盖了场景但不知道对不对。

**Covergroup / Coverpoint / Cross**

```systemverilog
covergroup fifo_cg @(posedge clk);
  // Coverpoint：观察 occupancy，按 bins 分桶
  cp_occ: coverpoint occupancy {
    bins empty    = {0};
    bins partial  = {[1:DEPTH-1]};
    bins full     = {DEPTH};
  }

  // Coverpoint：读写操作类型
  cp_op: coverpoint {wr_en, rd_en} {
    bins write_only = {2'b10};
    bins read_only  = {2'b01};
    bins both       = {2'b11};
    bins idle       = {2'b00};
  }

  // Cross：覆盖 occupancy × operation 的组合
  cx_occ_op: cross cp_occ, cp_op;
endgroup
```

- **Covergroup**：采样单元，绑定到时钟或调用时机。
- **Coverpoint**：观察一个表达式，按 bins 分类计数。
- **Cross coverage**：自动生成两个 coverpoint 的笛卡尔积，检查所有组合是否都被命中。
- **Bins**：每个 bin 代表 coverpoint 取值空间的一个子集，命中一次计数加 1。

**Bins 类型**

```systemverilog
coverpoint data {
  bins zero      = {0};
  bins small     = {[1:10]};
  bins medium[]  = {[11:100]};     // auto bins，每个值独立一个 bin
  bins large     = {[101:255]};
  ignore_bins x  = {8'hFF};        // 忽略，不统计也不影响 coverage
  illegal_bins y = {8'hFE};        // 命中则报错
}
```

**Code coverage 常见类型**

| 类型 | 看什么 | 常见误区 |
| --- | --- | --- |
| Line / statement coverage | 每行 RTL 是否执行过 | 执行过不代表结果正确。 |
| Branch coverage | `if/else`、`case` 分支是否都走到 | `default` 或 error branch 可能是设计上不可达，需要说明 waiver。 |
| Condition / expression coverage | 复合布尔表达式中的每个条件组合 | 覆盖率低可能暴露 stimulus 不足，也可能暴露表达式冗余。 |
| Toggle coverage | 信号 bit 是否发生 0/1 翻转 | tie-off、reserved bit、unused bus 需要合理豁免。 |
| FSM coverage | 状态、状态转移是否覆盖 | 非法状态转移不应强行覆盖，应由 assertion/checker 捕捉。 |

**Coverage Closure 流程**

1. 跑初始 regression，收集 coverage report（各 coverpoint 命中率和 holes）。
2. 对每个 hole 分析原因：
   - 场景在 spec 里根本不可达（illegal_bins 或 ignore_bins 处理）。
   - 约束太严，random test 碰不到（放宽 constraint 或加 dist 权重）。
   - Coverage model 写错（bin 范围不合理，或场景定义有误）。
   - 确实缺少 directed test（需要手写 directed test 补充）。
3. 迭代：调整 constraint、增加 seed、补 directed test，重跑 regression。
4. Merge coverage 数据，生成最终 report。

## 面试回答

Functional coverage is user-defined and measures whether specification-level scenarios have been exercised. It uses covergroups, coverpoints, and cross coverage in SystemVerilog. Each coverpoint observes an expression and counts how many bins have been hit. Cross coverage checks combinations of multiple coverpoints. Code coverage, in contrast, is tool-generated and measures whether RTL constructs such as lines, branches, and toggles have been executed. They are complementary: code coverage catches dead code, functional coverage catches uncovered spec behavior. Coverage closure is an iterative process of analyzing holes, adjusting constraints or adding directed tests, and re-running regression until all meaningful bins are hit.

## 常见追问

- Functional coverage 和 code coverage 的区别？
  - Functional coverage 来自 spec，由工程师手写，反映场景覆盖；code coverage 由工具自动统计 RTL 执行情况，反映代码覆盖。两者互补，均需关注。
- Covergroup、coverpoint、cross coverage 怎么用？
  - Covergroup 定义采样时机；coverpoint 观察一个表达式并按 bins 分类统计；cross coverage 检查两个或多个 coverpoint 所有组合是否都被命中。
- Coverage closure 的流程是什么？
  - 运行 regression 收集 report → 分析 hole 原因（不可达/约束太严/model 错误/真实缺测） → 针对性调 constraint / 补 directed test / 修 model → 重跑合并 coverage → 迭代直到目标达成。

## 易错点

- 把 coverpoint 的 bins 写得太细（auto bins 太多），coverage 数据量大但没有意义。
- Coverage 上去了但 checker 不够，"覆盖到了但没验证对错"。
- 使用 `@(posedge clk)` 但忘记 `disable iff (!rst_n)`，reset 期间也在采样，命中的 bins 可能无效。
- Cross coverage bin 过多但大部分是不可达组合，导致 report 里 coverage 永远上不到 100%，应使用 `ignore_bins` 排除。
- 认为 100% functional coverage = 验证完成，忽略了 coverage model 本身是否完整覆盖 spec。

---

<a id="debug-methods"></a>
## Debug 方法
标签：`#dv` `#debug` `#interview`

## 核心思路

DV debug 的核心是**系统化缩小范围**：先确认能复现 → 找到第一个错误 → 判断是 TB 问题还是 DUT 问题 → 定位到具体信号或逻辑 → 最小化 testcase 方便定案。

避免两个常见误区：
- 盲目看最后一个 error：最后的 error 往往是第一个 error 的级联效应，找第一个 error 才能找到根本原因。
- 直接改代码：在没弄清根本原因之前修改 RTL 或 TB，很可能掩盖真正的 bug 或引入新问题。

## 常用 Debug 路线

**Step 1：Reproduce（复现）**

```
# 固定 seed 和版本，确保同样命令能复现同样失败
sim_run +ntb_random_seed=<seed> -snapshot=<design_version>
```

记录：RTL 版本（git hash）、TB 版本、仿真命令、seed。如果不能复现，先排查是否是时序竞争、OS 调度或环境差异问题。

**Step 2：Check log and locate first failure**

- 看 log 找第一个 error/failure，而不是最后一个。
- 记录 first failure 的仿真时间点（timestamp）。
- 确认是 assertion violation、scoreboard mismatch、timeout、still pending transaction 还是 UVM fatal。

**Step 3：Open waveform around first failure**

- 在 first failure 时间前后开 waveform（通常加 `-10ns` ~ `-100ns` 的窗口）。
- 检查接口信号的时序：valid/ready handshake 是否正确、data 是否有效、控制信号是否按协议到来。
- 观察 DUT 内部关键信号（如果有 probe 或 access）。

**Step 4：Trace transaction**

从接口到内部逐层追踪：

```
Driver → DUT interface → DUT internal → DUT output interface → Monitor → Scoreboard
```

- Driver 送出的 stimulus 是否正确？（检查 driver log 和 interface waveform）
- Monitor 采集到的是什么？（检查 monitor log）
- Scoreboard 的 expected 和 actual 分别是什么？（检查 scoreboard log）
- 是 expected 生成错误，还是 actual 采集错误，还是 DUT 输出本身错误？

**Step 5：Distinguish TB issue vs DUT issue**

- TB issue：driver 发了错误 stimulus、monitor 采集时机错误、constraint 不合理产生非法 input、scoreboard 的 reference model 逻辑有 bug。
- DUT issue：在正确 stimulus 下输出错误结果，查 RTL 逻辑、timing 或 boundary condition。

区分方法：先用 directed test 排除 constraint/random 因素，用已知正确的 stimulus 单步验证 DUT 行为。

**Step 6：Minimize testcase**

找到 failure 后，把 testcase 缩到最小——最少的 stimulus、最短的仿真时间、只触发这一个 bug。好处：方便和设计工程师对齐，方便 regression 复检，避免其他 noise 干扰。

**Debug Checklist**

- [ ] seed 固定，能稳定复现。
- [ ] 找到 first failure 而不是最后一个 error。
- [ ] 在 first failure 附近开 waveform。
- [ ] 区分 TB 问题和 DUT 问题。
- [ ] 确认是否有已知 bug / open issue 可以解释这个现象。
- [ ] Testcase 最小化后能 standalone 复现。
- [ ] 修复后在原来 failing seed 上验证已 pass。

## 面试回答

My debug flow starts with reproducing the failure using the exact same seed, RTL version, and simulation command. Then I locate the first failure in the log rather than the last error, because later errors are often cascaded effects. I open the waveform around that timestamp and trace the transaction through the driver, monitor, and scoreboard to determine whether the issue is in the testbench, the constraint, or the DUT. If it is in the DUT, I inspect the RTL around the relevant signals. Once I understand the root cause, I minimize the testcase to isolate the bug as clearly as possible before discussing with the design engineer.

## 常见追问

- 怎么判断是 TB 问题还是 DUT 问题？
  - 用 directed test 发已知正确的 stimulus，观察 DUT 响应；或检查 scoreboard 的 expected 生成逻辑是否和 spec 一致。
- Intermittent failure 怎么 debug？
  - 固定 seed 先确认能复现；如果 seed 固定仍然随机出现，检查 TB race condition（例如异步 event、always block sensitivity 问题）或仿真工具 non-deterministic 行为。
- Coverage hole 分析怎么做？
  - 对每个 hole 判断：场景是否不可达（ignore）、constraint 太严（放宽）、coverage model 写错（修 model）、还是真实缺测试（补 directed test）。

---

<a id="book-dv-fundamentals"></a>
## 书籍整理：验证基础高频框架
标签：`#book` `#dv` `#testbench` `#interview`

### 一句话定义

验证基础题主要考察你能否从 spec 出发，选择合适 stimulus、checker、coverage、reference model 和 debug 方法，把“跑了仿真”变成“有证据证明功能正确”。

### 核心概念表

| 主题 | 要会讲什么 | 面试口径 |
| --- | --- | --- |
| Directed testing | 手写特定输入验证明确场景 | Bring-up、corner case、bug reproduction 很适合 directed test，但覆盖大状态空间效率低。 |
| Constrained random verification | 在合法约束内随机生成 stimulus | 适合探索大输入空间，必须配合 functional coverage 和 self-checking environment。 |
| Self-checking test | testbench 自动判断 pass/fail | 不能只看 waveform；driver 送 stimulus，monitor 采 transaction，scoreboard/reference model 自动比较。 |
| Coverage-driven verification | 用 coverage hole 反向驱动测试补充 | Coverage 不是目标本身，必须和 checker/assertion 一起看。 |
| Assertion-based verification | 用 property 持续检查协议或时序规则 | Assertion 适合捕捉局部协议、时序和不变量，能把 bug 定位到发生点附近。 |
| Transaction | 一次抽象操作 | 例如一次 bus read/write、一笔 packet、一次 DMA descriptor；transaction-level debug 比 pin-level 更高效。 |
| BFM | Bus Functional Model | 把 transaction 转成 pin-level 协议，或在 slave 侧响应 DUT master 请求。 |
| Reference model | Golden model / expected model | 当输出不容易手算时，用模型生成 expected result，scoreboard 比较 actual。 |
| Completeness | 验证完成标准 | Functional coverage 达标、code coverage 有合理 waiver、assertion clean、regression pass、关键 directed tests pass。 |
| GLS | Gate-Level Simulation | 综合后网表仿真，用于检查 reset、X propagation、timing annotation、scan/DFT 或低功耗插入后的问题。 |

### 从零验证一个模块的答题骨架

1. 读 spec，列 feature、合法输入、非法输入、reset、异常和性能要求。
2. 写 verification plan，把 feature 映射到 tests、coverage、checker/assertion。
3. 搭 testbench：driver/BFM、monitor、scoreboard、coverage collector、reference model。
4. 先跑 directed bring-up，再跑 constrained random/regression。
5. 分析 failures 和 coverage holes，补约束、seed、directed test 或修 coverage model。
6. 用 closure criteria 判断是否足够：coverage、assertion、regression、waiver、review 都要闭环。

### 面试回答

中文：Directed test 和 constrained random 不是二选一。Directed test 适合 bring-up、明确 corner case 和 bug 复现；constrained random 适合探索大状态空间。真正有效的验证环境应该 self-checking，由 monitor 采集 DUT 行为，scoreboard/reference model 自动比较 expected 和 actual，再用 functional coverage 判断 spec 场景是否被覆盖。验证完成通常看 functional coverage closure、code coverage 合理 waiver、assertion clean、regression pass 以及关键场景 review 通过。

English: Directed tests and constrained random tests are complementary. Directed tests are good for bring-up, clear corner cases, and bug reproduction, while constrained random testing explores a large legal state space. A strong verification environment should be self-checking: monitors observe DUT behavior, scoreboards or reference models compare expected and actual results, and functional coverage tracks whether specification scenarios have been exercised. Verification completeness is based on coverage closure, clean assertions, passing regressions, meaningful code coverage waivers, and review of key scenarios.

### 常见追问

- Reference model 什么时候需要？
  - 当 expected behavior 复杂、输出空间大或需要 cycle/transaction-level 对比时，例如 CPU、codec、DMA、NPU。
- BFM 和 driver 有什么关系？
  - Driver 通常是 UVM 组件，BFM 是把 transaction 转成真实接口时序的协议行为模型；项目里二者可能合并，也可能 driver 调用 interface BFM task。
- 为什么 100% coverage 仍不等于验证完成？
  - Coverage model 可能漏写场景，checker 可能不完整，waiver 可能不合理，所以还要看 spec review、assertion、scoreboard 和 bug trend。
- GLS 为什么还要跑？
  - RTL 仿真看功能，GLS 可以发现综合、reset/X、timing annotation、scan/clock gating/低功耗插入后的问题。

### 易错点

- 把 verification plan 写成 testcase list，缺少 feature、checker 和 coverage 的映射。
- 只看 waveform 人工判断，没有 self-checking pass/fail。
- 追求 coverage 数字，忽略 coverage hole 是否真的对应 spec risk。
- Reference model 和 DUT 使用同一份错误假设，导致两边一起错。

---

<a id="vip-checker-scoreboard"></a>
## VIP checker vs Scoreboard
标签：`#dv` `#uvm` `#scoreboard` `#vip` `#interview`

### 一句话定义

VIP checker 通常检查接口协议和时序是否满足 spec；scoreboard/reference model 检查 DUT 的功能转换、数据一致性和端到端结果是否正确。

### 核心区别

| 维度 | VIP checker | Scoreboard / reference model |
| --- | --- | --- |
| 关注层级 | 协议接口层 | 功能行为层 / end-to-end |
| 输入来源 | pin-level interface 或 VIP monitor | 一个或多个 monitor 的 transaction |
| 典型检查 | handshake、timing、burst、ID、response、协议状态机 | expected vs actual、地址映射、数据一致性、跨接口转换 |
| 谁提供 | 第三方 VIP 或公司内部 VIP 常自带 | 通常由项目 env 自建或定制 |
| 典型误区 | 认为 VIP pass 就代表 DUT 功能正确 | 只比较数据，不处理乱序、错误响应和特殊配置 |

### DDR4 controller 项目例子

| 组件 | 检查什么 |
| --- | --- |
| AXI VIP | AXI valid/ready、五通道、burst、ID、outstanding、response/order 等协议合法性 |
| APB VIP | APB 配置访问的两 phase、`PREADY/PSLVERR`、APB4 strobe/protection 等 |
| DFI VIP | Controller 到 PHY 的 DFI command/data、init/update、latency、sideband 等 |
| DDR4 Memory VIP | PHY 输出后的 DDR4 JEDEC pin-level command、rank/bank 状态、DQ/DQS、`tRCD/tRP/tRAS/tRFC/tFAW` 等 timing |
| AXI read-hash scoreboard | AXI write/read 的 end-to-end 数据一致性 |
| AXI-HIF / HIF-DFI scoreboard | AXI 到 HIF、HIF 到 DFI 的地址、命令、数据和内部转换正确性 |

### Read-hash scoreboard 例子

`read-hash` 里的 hash 不是加密哈希，而是用 associative array 做 sparse memory image：

```systemverilog
bit [7:0] expected_mem[channel][byte_addr];
```

写 transaction 到来时，scoreboard 按 AXI burst、`AWSIZE/AWLEN/AWBURST` 和 `WSTRB` 展开到 byte 地址，把成功写入的数据存进 `expected_mem`。读 transaction 到来时，再按同样规则展开地址，把 `RDATA` 的每个 byte 与 `expected_mem[channel][byte_addr]` 比较。对未写过地址、`SLVERR`、ECC aliasing、poison/parity error、WRAP burst 和 unaligned access，要有明确 skip 或特殊处理策略。

### 面试回答

中文：

VIP checker 和 scoreboard 的边界要分清。VIP checker 主要保证接口协议合法，比如 AXI 的 valid/ready、burst、ID、response，或者 DDR4 memory VIP 对 JEDEC command/timing 的检查。但这些 checker 不一定知道系统级 expected data。像 DDR4 controller 项目里，AXI read-hash scoreboard 是 env 自建的功能检查：它复用 AXI VIP monitor 采到的 transaction，写路径按 byte address 和 `WSTRB` 更新 expected memory image，读路径再逐 byte 比较 `RDATA` 和 expected data，用来检查端到端数据一致性。

English:

VIP checkers and scoreboards cover different layers. VIP checkers validate protocol-level behavior, such as AXI handshakes, burst rules, IDs, responses, or DDR4 JEDEC command and timing rules. A scoreboard checks the functional intent of the DUT. In the DDR4 controller project, the AXI read-hash scoreboard is not part of the AXI VIP. It consumes transactions observed by the AXI VIP monitor, stores successful write data in a byte-addressed sparse memory image, and compares later read data against that expected image byte by byte.

### 常见追问

- Mem VIP 会自动检查 DDR4 时序吗？
  - 会。DDR4 Memory VIP 在 JEDEC pin-level 检查 command、bank/rank state、DQ/DQS 和 timing violation；但它不替代 AXI 读写数据一致性 scoreboard。
- AXI read-hash 是 AXI VIP 自带的吗？
  - 不是。AXI VIP 自带的是 AXI 协议 checker；read-hash 是项目 UVM env 中的功能 scoreboard，只是复用 AXI VIP monitor 输出的 transaction。
- DDR4 VIP 直接接 DFI 吗？
  - 不直接接。DFI 是 controller 到 PHY 的接口；DDR4 Memory VIP 看到的是 PHY/wrapper 转换后的 DDR4 JEDEC pin-level 信号。
- 为什么要处理 order/conflict？
  - 多 port、outstanding、read/write response 乱序时，scoreboard 必须按 controller 应处理的顺序更新 expected memory，否则会把合法乱序误报成数据 mismatch。

### 常见错误

- 把 VIP checker pass 误认为端到端功能一定正确。
- 把 read-hash 理解成 CRC/hash 校验算法，而不是 byte-addressed associative array memory image。
- 写 scoreboard 时忽略 `WSTRB`、unaligned burst、WRAP burst、错误响应和未初始化地址。
- DDR/DFI/PHY 层次混淆：DFI VIP 看 controller-PHY 接口，DDR4 Memory VIP 看 PHY 后面的 JEDEC pin-level 行为。

---

<a id="formal-verification"></a>
## Formal Verification
标签：`#formal` `#dv` `#assertion` `#interview`

### 一句话定义

Formal verification 用数学方法在状态空间中证明 property 是否成立，不依赖随机 stimulus；它属于静态验证思路，常用于控制逻辑、协议规则、等价性和难以随机打到的 corner case。

### Formal vs Dynamic Simulation

| 维度 | Formal Verification | Dynamic Simulation |
| --- | --- | --- |
| 输入方式 | property/constraint/assumption | directed 或 constrained-random stimulus |
| 覆盖范围 | 在可证明深度/状态空间内穷举 | 只覆盖实际跑到的 test/seed |
| 优点 | 能证明无某类 bug，适合 corner case | 可扩展到大系统，能跑真实场景和软件流 |
| 限制 | 状态空间爆炸，约束写错会 vacuous pass | 无法穷举，漏测取决于 stimulus 和 coverage |
| 常见用途 | property checking、equivalence checking、deadlock/liveness、protocol checks | block/IP/SOC regression、performance、software-driven scenarios |

### 常见 formal 方法

- **Model checking**：对 RTL + property 做状态空间搜索，证明 assertion 是否恒成立。
- **Equivalence checking**：证明两个设计在功能上等价，例如 RTL vs gate netlist，或优化前后 RTL。
- **Formal apps**：CDC/RDC、lint-like protocol checks、deadlock、X-prop、connectivity 等工具化应用。

### 面试回答

中文：Formal verification 不靠写很多 test 去覆盖场景，而是把设计行为写成 property，并在约束条件下证明 property 是否总成立。它适合控制逻辑、协议、不变量、死锁检查和等价性验证，优点是能覆盖随机仿真很难打到的 corner case；限制是状态空间容易爆炸，对大数据通路或完整 SoC 不一定可扩展，而且 assumption 写错可能导致 vacuous pass。所以实际项目通常 formal 和 simulation 配合使用。

English: Formal verification proves properties mathematically under a set of assumptions instead of relying on simulation stimulus. It is useful for control logic, protocols, invariants, deadlock checks, and equivalence checking. The advantage is exhaustive reasoning within the bounded or proven state space, which can catch corner cases that simulation may miss. The main limitations are scalability and the risk of incorrect assumptions or vacuous proofs, so formal is usually used together with dynamic simulation.

### 常见追问

- Formal 是 static 还是 dynamic？
  - 更偏 static，不需要像仿真那样跑具体 stimulus waveform，而是对状态空间和 property 做证明。
- Formal 证明通过后还需要 coverage 吗？
  - 需要看证明范围、assumption、vacuity 和 formal coverage；同时系统级场景仍可能需要 simulation coverage。
- Formal 的最大限制是什么？
  - 状态空间爆炸和约束建模难度，尤其是大存储、大数据通路、完整 SoC 级场景。

### 易错点

- 把 formal 当成“自动替代仿真”的万能工具。
- 只看 property pass，不检查 assumption 是否过强。
- 忽略 vacuous pass：antecedent 从未成立，property 也会显示 pass。
- 对 data-heavy 模块强行做全状态证明，导致工具无法收敛。

---

<a id="dv-interview-answers"></a>
## 面试回答速查（中文 + English）
### Coverage-driven verification

中文：Coverage-driven verification 是从 spec 出发建立 verification plan，再把 feature 转成 coverage model。测试不是只为了跑过，而是要不断看 coverage hole，调整 constraint、seed、directed test 和 checker，直到关键 feature 被覆盖并且测试通过。功能覆盖率必须和 checker/scoreboard/assertion 一起看，否则“覆盖到了但没检查对错”没有意义。

English: Coverage-driven verification starts from the specification and verification plan, then converts features into a coverage model. Tests are used to close coverage holes through constraints, seeds, directed cases, and checkers. Coverage is meaningful only when the environment is self-checking.

### Functional coverage vs code coverage

中文：Code coverage 看 RTL 代码有没有被执行，比如 line、branch、toggle、FSM；functional coverage 看 spec 里的功能场景有没有被命中，是用户定义的。100% code coverage 不代表功能都测到了，100% functional coverage 也不代表 RTL 每个分支都跑到了，两者互补。

English: Code coverage measures exercised RTL structure, such as line, branch, toggle, and FSM coverage. Functional coverage is user-defined and measures whether specification-level scenarios were hit. They are complementary and cannot replace each other.

### Debug regression failure

中文：Debug regression failure 我会先固定 seed 复现，记录 RTL/TB 版本和仿真命令；然后看 log 找 first failure，而不是最后一个 error；接着在 waveform 里 trace transaction，从 driver、monitor、scoreboard 到 DUT interface 判断是 TB 问题、constraint 问题还是 DUT 问题；最后缩小 testcase，方便和 designer 对齐。

English: I would first reproduce the failure with the same seed and versions, then locate the first failure in the log, inspect the waveform around that time, trace the transaction through driver, monitor, scoreboard, and DUT interface, and finally minimize the testcase.

### Directed vs constrained random

中文：Directed test 适合 bring-up、明确 corner case 和 bug 复现；constrained random 适合探索大状态空间。两者都要放在 self-checking testbench 中，用 scoreboard/reference model 判断对错，用 functional coverage 判断是否覆盖到 spec 场景。

English: Directed tests are useful for bring-up, clear corner cases, and bug reproduction, while constrained random tests explore a larger legal state space. Both should run in a self-checking environment with scoreboards and coverage.

### Formal verification

中文：Formal verification 通过 property 和 assumption 对状态空间做数学证明，适合协议、不变量、死锁、等价性和难以随机打到的 corner case。它不替代仿真，主要限制是状态空间爆炸和 assumption/vacuity 风险。

English: Formal verification proves properties under assumptions and is useful for protocols, invariants, deadlock checks, equivalence, and hard-to-hit corner cases. It complements simulation rather than replacing it.

