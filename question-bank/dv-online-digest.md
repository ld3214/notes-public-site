# DV 面经知识点汇总

标签：`#dv` `#interview` `#systemverilog` `#uvm` `#coverage` `#debug`

## 页内目录

- [来源说明](#source-notes)
- [面经反复出现的考察方向](#common-directions)
- [优先级复习清单](#priority-list)
- [高频问题与回答骨架](#high-frequency-qa)
- [面试准备策略](#prep-strategy)
- [下一步可补的专项笔记](#next-notes)

---
<a id="source-notes"></a>
## 来源说明
这页是根据网上 DV 面经、题库和方法论资料整理出来的复习地图，不是逐字摘录。Reddit/个人面经只当趋势参考；真正准备时以你简历项目、职位 JD 和基础知识为主。

主要参考来源：

- [DV Interview Handbook - Topics](https://www.dvhandbook.online/topics.html)
- [DV Interview Handbook - Real Interviews](https://www.dvhandbook.online/interviews.html)
- [VLSI Web - Top 60 Design Verification Interview Questions](https://vlsiweb.com/design-verification-interview-questions/)
- [VLSI Verify - SystemVerilog Interview Questions](https://vlsiverify.com/interview-questions/systemverilog-interview-questions/)
- [VLSI Verify - UVM Interview Questions](https://vlsiverify.com/interview-questions/uvm-interview-questions/)
- [Verification Guide - UVM Interview Questions](https://verificationguide.com/uvm/uvm-interview-questions/)
- [Doulos - Coverage-Driven Verification Methodology](https://www.doulos.com/knowhow/systemverilog/uvm/easier-uvm/easier-uvm-deeper-explanations/coverage-driven-verification-methodology/)
- [VLSI Verify - UVM Scoreboard](https://vlsiverify.com/uvm/uvm-scoreboard/)
- [VLSI Verify - uvm_config_db](https://vlsiverify.com/uvm/uvm_config_db-in-uvm/)
- [Reddit - Google DV interview shared experience](https://www.reddit.com/r/chipdesign/comments/1pxxg5k/google_design_verification_dv_interview_process/)
- [Reddit - Nvidia DV interview discussion](https://www.reddit.com/r/chipdesign/comments/1re3i4m/nvidia_design_verification_interview/)

<a id="common-directions"></a>
## 面经反复出现的考察方向
| 方向 | 高频考点 | 面试官真正想看什么 |
| --- | --- | --- |
| SystemVerilog 基础 | data type、array/queue、interface、clocking block、fork/join、OOP | 你能不能准确写 testbench code，而不是只背 UVM 名词 |
| 随机化与约束 | `rand/randc`、inline constraint、`dist`、`solve before`、randomization fail debug | 能不能把场景转成合法刺激空间，并处理 corner case |
| Coverage | code vs functional coverage、covergroup/coverpoint/cross、coverage closure | 你是否知道“测到了什么”和“没测到什么” |
| SVA/Assertions | immediate vs concurrent、`|->` vs `|=>`、`$rose/$fell/$stable`、assertion coverage | 能不能把协议/时序规则写成自动检查 |
| UVM 架构 | agent、driver、monitor、sequencer、sequence、scoreboard、env、test | 能不能从 spec 搭一个可复用的验证环境 |
| UVM 机制 | factory、phase/objection、config_db、analysis port、TLM FIFO、virtual sequence | 是否理解 UVM 为什么这样组织，而不是只会套模板 |
| Scoreboard/Reference Model | in-order/out-of-order、predictor、ID 匹配、queue/associative array | 能否设计靠谱的 self-checking testbench |
| Testplan/Methodology | directed vs constrained random、feature list、coverage model、regression | 能不能从需求拆验证点并收敛验证 |
| Debug | seed reproduce、log/waveform、first failure、TB vs DUT、coverage hole analysis | 是否具备真实项目里定位问题的思路 |
| 项目与场景题 | FIFO/arbiter/FSM/protocol/interrupt/multi-clock/reset/low-power | 能不能把知识用到具体 design 上 |

<a id="priority-list"></a>
## 优先级复习清单
### P0：必须能稳定讲清楚

- SV 三种集合：dynamic array、associative array、queue。重点是 scoreboard 和 transaction buffering 的使用场景。
- SV randomization：`rand` vs `randc`、constraint、inline constraint、`dist`、`solve before`、randomization fail 怎么 debug。
- Functional coverage vs code coverage：一个来自 spec/testplan，一个来自 RTL execution；两者互补，不能互相替代。
- UVM testbench architecture：test/env/agent/sequencer/driver/monitor/scoreboard 的职责。
- UVM factory：registration macro、`type_id::create()`、type override、instance override。
- UVM phase and objection：build/connect/run/check/report，每个 phase 做什么，objection 为什么控制仿真结束。
- Monitor 到 scoreboard：monitor 把 pin-level activity 转成 transaction，经 analysis port/export 或 FIFO 给 scoreboard。
- Scoreboard：reference model/predictor 产生 expected，scoreboard 比较 expected vs actual。
- Debug flow：reproduce、看 log、定位 first error、开 waveform、trace transaction、区分 TB/DUT、缩小 testcase。

### P1：面试很容易追问

- Virtual interface 如何传入 UVM component：通常 top module 里 `set`，driver/monitor 在 `build_phase` 里 `get`。
- `uvm_config_db` precedence：build phase 中高层 set 优先；同 scope 下后 set 覆盖前 set。
- Virtual sequence/virtual sequencer：用于协调多个 agent sequencer，尤其是 SoC/protocol-level scenario。
- Analysis port/export/imp/TLM FIFO：为什么 monitor 不应该直接知道 scoreboard，如何解耦组件。
- In-order vs out-of-order scoreboard：顺序一致用 FIFO/queue；输出乱序或有 transaction ID 时用 associative array 匹配。
- Coverage closure：分析 coverage hole，确认是否 spec 支持、feature 是否 disabled、constraint 是否太弱、coverage model 是否写错。
- Directed vs constrained-random：directed 适合确定 corner case 或 bring-up；CRV 适合探索大状态空间。
- SVA implication：`|->` same-cycle consequent，`|=>` next-cycle consequent。

### P2：根据岗位和简历加深

- RAL：frontdoor/backdoor access、mirror/predict、register sequence。
- Protocol：AXI/APB valid-ready、outstanding、burst、backpressure、error response。
- Multi-clock/reset：CDC/RDC、async FIFO、reset sequencing、testbench 同步。
- Performance/SoC 场景：interrupt、cache/coherency、DMA、pipeline、arbiter、QoS。
- Coding：reverse bits、one-hot generation、constraint probability、FIFO checker、small class/OOP exercises。

<a id="high-frequency-qa"></a>
## 高频问题与回答骨架
<a id="dv-code-vs-functional-low"></a>
### 1. 如果 100% code coverage 但 functional coverage 很低，怎么办？

回答骨架：

1. 先说明两者测量对象不同：code coverage 看 RTL 是否被执行，functional coverage 看 spec feature 是否被命中。
2. 检查 functional coverage model 是否和 testplan/spec 对齐，是否有无效 bins 或过宽 auto bins。
3. 检查 test/constraint 是否真的能产生目标场景。
4. 检查 code coverage exclusion 是否合理，避免虚假的 100%。
5. 对 coverage hole 分类：未实现、被配置关闭、constraint 触达困难、coverage model 错误、真实缺测试。
6. 优先调 constraint/seed/regression，再为 hard-to-hit corner 写 directed test。

英文短答：

Code coverage and functional coverage measure different things. I would first review whether the functional coverage model matches the verification plan, then check whether the constraints and tests can actually reach the uncovered scenarios. I would also review code coverage exclusions, because 100% code coverage can still miss important spec-level behavior.

<a id="dv-fifo-verification"></a>
### 2. 如何从零验证一个 FIFO？

回答骨架：

- 读 spec：depth、width、sync/async、almost full/empty、overflow/underflow、reset 行为。
- Testplan：basic write/read、full、empty、simultaneous read/write、wrap-around、reset during traffic、backpressure。
- TB：driver 产生 write/read transaction，monitor 采集接口，scoreboard 用 queue 建 reference FIFO。
- Coverage：occupancy bins、full/empty transition、simultaneous op、overflow/underflow attempt、reset crossing。
- Assertions：full 不允许非法写，empty 不允许非法读，pointer/flag consistency，valid/ready rule。
- Debug：先 directed bring-up，再 CRV 加约束和 coverage closure。

<a id="dv-scoreboard-design"></a>
### 3. Scoreboard 怎么设计？

回答骨架：

- In-order design：input monitor transaction 经过 predictor 得到 expected，output monitor 给 actual，用 FIFO/queue 按顺序比较。
- Out-of-order design：expected 和 actual 按 transaction ID 存在 associative array，双方到齐再 compare。
- `check_phase` 检查 pending expected/actual 是否清空。
- Scoreboard 不应依赖 testcase 内部变量；数据应来自 monitor，保证可复用和 self-checking。

<a id="dv-coverage-driven"></a>
### 4. Coverage-driven verification 怎么讲？

回答骨架：

- 从 spec 生成 verification plan。
- 把 feature 转成 coverage model，而不是只列 directed tests。
- 搭 self-checking TB，确保 coverage 只有在测试通过时才有意义。
- 跑 regression、多 seed、merge coverage。
- 对 holes 做 root cause analysis，调约束或补 directed test。

<a id="dv-config-db-pitfalls"></a>
### 5. `uvm_config_db` 常见坑？

回答骨架：

- `set` 必须早于 `get`，常见是 top/test build 前设置，component 在 `build_phase` 获取。
- type parameter 必须完全匹配，例如 virtual interface 的参数化类型也要一致。
- path/scope 容易写错，`*` 虽方便但可能污染多个实例。
- `get()` 返回值必须检查，失败应该 fatal 或明确处理。
- 同一个 field 多处设置时要理解 precedence 和 last-set behavior。

<a id="prep-strategy"></a>
## 面试准备策略
- 每个知识点准备 30 秒短答和 2 分钟展开。
- 每个 UVM 机制都要能回答“为什么需要它”和“不用它会怎样”。
- 面试官给小 design 时，先讲 testplan，再讲 TB 架构，最后讲 coverage/checker/debug。
- 回答 coverage 问题时永远把 spec、testplan、coverage model、checker 四个词连起来。
- 回答 debug 问题时要体现工程习惯：seed、版本、log、waveform、first failure、minimal testcase。

<a id="next-notes"></a>
## 下一步可补的专项笔记
- `uvm_config_db` 和 virtual interface
- UVM analysis port / export / imp / FIFO
- Scoreboard 设计模式
- Coverage closure 实战流程
- FIFO 验证面试题
- AXI verification testplan

