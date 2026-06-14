# 面试题库

这里集中放 ASIC/DV 面试题。具体知识点可以链接回主题笔记。

## 页内目录

- [ASIC Frontend](#qb-asic-frontend)
- [Design Verification](#qb-design-verification)
- [SystemVerilog / UVM](#qb-systemverilog-uvm)
- [Protocols](#qb-protocols)
- [书籍题单：Cracking Digital VLSI Verification Interview](#qb-cracking-dv-book)
- [笔试题：2026 数字 IC 公司卷整理](#qb-written-exams-2026-csdn)

---

<a id="qb-cracking-dv-book"></a>
## 书籍题单：Cracking Digital VLSI Verification Interview

来源：`cracking-digital-vlsi-verification-interview-interview-success(1).pdf`。这里按复习用途转述整理，不逐字搬运原书；详细知识点回链到知识库对应 anchor。

| 方向 | 典型问法 | 速答口径 | 详细笔记 |
| --- | --- | --- | --- |
| 数制/编码 | Gray code 为什么有用？ | 相邻状态只变 1 bit，适合 async FIFO pointer 等 CDC 场景，降低多 bit 同时跨域采样风险。 | [CDC/RDC](../knowledge-base/asic-frontend.md#cdc-rdc) / [数字逻辑框架](../knowledge-base/asic-frontend.md#book-dv-logic-architecture) |
| 数制/编码 | Parity bit 怎么用？ | 奇偶校验通过增加 1 bit 让数据中 1 的个数满足奇/偶规则，可检测单 bit 错误但不能定位或纠正。 | [数字逻辑框架](../knowledge-base/asic-frontend.md#book-dv-logic-architecture) |
| 组合逻辑 | NAND/NOR 为什么叫 universal gate？ | NAND 或 NOR 都能组合出 NOT、AND、OR，因此能构造任意布尔逻辑。 | [数字逻辑框架](../knowledge-base/asic-frontend.md#book-dv-logic-architecture) |
| 组合逻辑 | Priority encoder 和普通 encoder 区别？ | 普通 encoder 假设只有一个输入有效；priority encoder 允许多个输入有效，并按固定优先级输出最高优先级输入。 | [数字逻辑框架](../knowledge-base/asic-frontend.md#book-dv-logic-architecture) / [find first one](../knowledge-base/asic-frontend.md#find-first-one) |
| 组合逻辑 | Ripple carry adder 和 CLA 区别？ | Ripple carry 简单但 carry 逐位传播；CLA 提前计算 generate/propagate，速度更快但面积更大。 | [数字逻辑框架](../knowledge-base/asic-frontend.md#book-dv-logic-architecture) |
| 时序逻辑 | Latch 和 flip-flop 有什么区别？ | Latch 是 level-sensitive，enable 有效期间透明；FF 是 edge-triggered，只在时钟沿采样。 | [时序与 STA](../knowledge-base/asic-frontend.md#timing-sta) / [数字逻辑框架](../knowledge-base/asic-frontend.md#book-dv-logic-architecture) |
| 时序逻辑 | Setup/hold/skew 怎么讲？ | Setup 是时钟沿前稳定要求，hold 是时钟沿后保持要求；skew 是时钟到达不同寄存器的时间差，会影响 timing margin。 | [时序与 STA](../knowledge-base/asic-frontend.md#timing-sta) |
| 时序逻辑 | 同步复位和异步复位怎么取舍？ | 同步复位时序更容易收敛；异步复位可立即进入 reset，但释放建议同步，避免 recovery/removal 风险。 | [CDC/RDC](../knowledge-base/asic-frontend.md#cdc-rdc) |
| FSM | Mealy 和 Moore 区别？ | Moore 输出只依赖状态，毛刺更好控；Mealy 输出依赖状态和输入，状态可能更少但要注意输入毛刺。 | [数字逻辑框架](../knowledge-base/asic-frontend.md#book-dv-logic-architecture) |
| ASIC flow | 典型 ASIC/SOC 设计流程怎么讲？ | Spec/architecture -> RTL -> lint/CDC -> synthesis/DFT/STA -> P&R -> GLS/signoff；每一步说明检查目标。 | [数字逻辑框架](../knowledge-base/asic-frontend.md#book-dv-logic-architecture) |
| 架构 | RISC 和 CISC 区别？ | RISC 指令简单规整、利于 pipeline；CISC 指令复杂、编码可变，通常通过微操作执行。 | [数字逻辑与体系结构](../knowledge-base/asic-frontend.md#book-dv-logic-architecture) |
| 架构 | Big endian 和 little endian 是什么？ | 多字节数据在内存中的 byte 顺序不同；little endian 低有效 byte 放低地址，big endian 相反。 | [数字逻辑与体系结构](../knowledge-base/asic-frontend.md#book-dv-logic-architecture) |
| Pipeline | 三类 pipeline hazard 怎么处理？ | Structural 用资源复制/仲裁，data 用 forwarding/stall，control 用 branch prediction/flush。 | [数字逻辑与体系结构](../knowledge-base/asic-frontend.md#book-dv-logic-architecture) |
| Cache | Direct-mapped、set-associative 和 fully-associative 怎么比？ | 直接映射最简单但 conflict miss 多；组相联折中；全相联冲突少但比较和替换硬件最复杂。 | [Cache 基础](../knowledge-base/asic-frontend.md#cache-basics) |
| Cache | Write-through 和 write-back 区别？ | Write-through 每次写也更新下一级，简单但带宽大；write-back 只在 dirty eviction 时写回，性能好但控制复杂。 | [Cache 基础](../knowledge-base/asic-frontend.md#cache-basics) |
| Cache | Coherence 和 consistency 区别？ | Coherence 管同一地址多个副本；consistency 管不同地址 memory operation 的全局可见顺序。 | [Cache 基础](../knowledge-base/asic-frontend.md#cache-basics) |
| 虚拟内存 | TLB 和 page fault 怎么讲？ | TLB 缓存虚拟地址到物理地址翻译；page fault 表示页表无有效映射或权限错误，需要 OS 处理。 | [数字逻辑与体系结构](../knowledge-base/asic-frontend.md#book-dv-logic-architecture) |
| DV 基础 | Directed test 和 CRV 怎么取舍？ | Directed 适合 bring-up、明确 corner case、bug 复现；CRV 适合大状态空间探索，需要 coverage 和 self-checking。 | [验证基础高频框架](../knowledge-base/design-verification.md#book-dv-fundamentals) |
| DV 基础 | Self-checking test 是什么？ | TB 自动判断 pass/fail，monitor 采集 actual，scoreboard/reference model 生成 expected 并比较。 | [验证基础高频框架](../knowledge-base/design-verification.md#book-dv-fundamentals) |
| DV 基础 | Transaction-based verification 有什么好处？ | 用 transaction 抽象一次操作，debug 和组件通信更清楚，driver/monitor/scoreboard 不必直接耦合 pin-level 细节。 | [验证基础高频框架](../knowledge-base/design-verification.md#book-dv-fundamentals) |
| DV 基础 | Reference model 什么时候需要？ | 输出复杂或不易手算时，用 golden/reference model 生成 expected result，比如 CPU、DMA、codec、NPU。 | [验证基础高频框架](../knowledge-base/design-verification.md#book-dv-fundamentals) |
| DV 基础 | 怎么判断验证完成？ | Functional coverage closure、code coverage 合理 waiver、assertion clean、regression pass、关键场景 review 通过。 | [验证基础高频框架](../knowledge-base/design-verification.md#book-dv-fundamentals) / [Functional Coverage](../knowledge-base/design-verification.md#functional-coverage) |
| DV 基础 | GLS 为什么重要？ | GLS 可发现综合后网表、reset/X、timing annotation、scan/clock-gating/低功耗插入后的问题。 | [验证基础高频框架](../knowledge-base/design-verification.md#book-dv-fundamentals) |
| Formal | Formal 和 simulation 区别？ | Formal 用 property/assumption 证明状态空间内行为；simulation 跑具体 test/seed，两者互补。 | [Formal Verification](../knowledge-base/design-verification.md#formal-verification) |
| Low Power | 动态功耗和静态功耗怎么降？ | 动态功耗靠 clock gating、降低 activity、DVFS；静态漏电靠 power gating、HVT、memory sleep。 | [低功耗、Clocking 与 UPF](../knowledge-base/asic-frontend.md#power-clocking-upf) |
| Low Power | UPF 主要描述什么？ | 描述 power domain、isolation、retention、level shifter、power switch 和 power state table。 | [低功耗、Clocking 与 UPF](../knowledge-base/asic-frontend.md#power-clocking-upf) |
| Verilog | Blocking 和 non-blocking 区别？ | Blocking 立即更新，适合组合；non-blocking 时间步末更新，适合时序寄存器。 | [Blocking vs Non-blocking](../knowledge-base/systemverilog-uvm.md#sv-blocking-nonblocking) |
| Verilog | `==` 和 `===` 区别？ | `==` 遇到 X/Z 可能得到 X；`===` 把 X/Z 当成可比较值，适合 TB 精确检查未知态。 | [SV/Verilog 高频语法清单](../knowledge-base/systemverilog-uvm.md#book-sv-verilog-checklist) |
| SV | packed 和 unpacked array 区别？ | Packed 是连续 bit 向量，适合切片/算术；unpacked 是元素集合，适合 memory/array。 | [SV/Verilog 高频语法清单](../knowledge-base/systemverilog-uvm.md#book-sv-verilog-checklist) |
| SV | Clocking block 有什么用？ | 在 interface 中定义 TB 采样和驱动 skew，减少 DUT/TB race。 | [SV/Verilog 高频语法清单](../knowledge-base/systemverilog-uvm.md#book-sv-verilog-checklist) |
| SV | `pre_randomize()` 和 `post_randomize()` 怎么用？ | 随机化前后 hook；前者准备配置，后者派生字段或检查结果，不应破坏已求解字段。 | [SV 随机化](../knowledge-base/systemverilog-uvm.md#sv-randomization) |
| SV | `fork/join_any` 和 `disable fork` 常用于什么？ | 等任一分支完成后继续，并 kill 其他分支，常用于 timeout/watchdog。 | [UVM 高级技巧](../knowledge-base/systemverilog-uvm.md#uvm-advanced-patterns) |
| SVA | Immediate 和 concurrent assertion 区别？ | Immediate 过程执行到即检查；concurrent 在时钟采样，可检查跨周期时序属性。 | [SVA](../knowledge-base/systemverilog-uvm.md#sva) |
| UVM | Active agent 和 passive agent 区别？ | Active 有 sequencer/driver/monitor，会驱动接口；passive 通常只有 monitor，只观察。 | [UVM 高频问法清单](../knowledge-base/systemverilog-uvm.md#book-uvm-interview-checklist) |
| UVM | Analysis port 和 TLM FIFO 区别？ | Analysis port 非阻塞广播；TLM FIFO 是带缓存的点对点通道，可 blocking/nonblocking get/put/peek。 | [UVM 高频问法清单](../knowledge-base/systemverilog-uvm.md#book-uvm-interview-checklist) / [UVM TLM 通信](../knowledge-base/systemverilog-uvm.md#uvm-tlm) |
| UVM | Sequencer-driver handshake 怎么讲？ | Sequence 用 `start_item/finish_item` 发送 item；driver 用 `get_next_item/item_done` 取 item 并完成驱动。 | [UVM 高频问法清单](../knowledge-base/systemverilog-uvm.md#book-uvm-interview-checklist) |
| UVM | `new()` 和 `create()` 区别？ | `new()` 直接构造，绕过 factory；`type_id::create()` 支持 factory override。 | [UVM Factory 机制](../knowledge-base/systemverilog-uvm.md#uvm-factory) |
| UVM | Objection 机制干什么？ | 控制 run phase 何时结束；不 raise 会提前结束，忘 drop 会卡住。 | [UVM Phase 机制](../knowledge-base/systemverilog-uvm.md#uvm-phases) |
| UVM | RAL 有什么价值？ | 抽象 register map，统一 frontdoor/backdoor 读写、mirror、predict、check 和 register coverage。 | [Register Model / UVM RAL](../knowledge-base/systemverilog-uvm.md#uvm-ral) |

---

<a id="qb-written-exams-2026-csdn"></a>
## 笔试题：2026 数字 IC 公司卷整理

来源：[CSDN 专栏：2026 年 IC 设计各大厂面试题目带答案解析](https://blog.csdn.net/qq_39735003/category_13155497.html)（含分页）。下面是按复习用途重写整理的题型和答题要点，不逐字搬运原卷；需要看完整选项、代码参考答案时，点原文回查。

### 公司卷索引

| 公司 / 文章 | 方向 | 高频考点 | 代码 / 主观题 |
| --- | --- | --- | --- |
| [小米](https://blog.csdn.net/qq_39735003/article/details/160157587) | SoC / 总线 | AHB 信号、multicycle、`input delay`、hold 修复、异步复位、FIFO 指针 | 保持违例修复、AHB/APB、异步 FIFO |
| [华为海思](https://blog.csdn.net/qq_39735003/article/details/160157487) | SoC / AXI | Verilog 阻塞/非阻塞、CDC、clock gating、FIFO、序列检测、AXI | FIFO、序列检测器、时序约束 |
| [乐鑫](https://blog.csdn.net/qq_39735003/article/details/160157898) | IoT / SV | SV `logic`、UVM root、上采样低通、后仿真、CDC、BER、`==`/`===`、PVT | `1011` 重叠序列检测；组合逻辑资源估算 |
| [联发科](https://blog.csdn.net/qq_39735003/article/details/160158546) | IC + 编程混合 | DFF 波形、组合/时序电路、IC 流程、逻辑推理、C/Python 基础 | Verilog 序列检测器；表达式/文件/树深度编程 |
| [壁仞科技笔试](https://blog.csdn.net/qq_39735003/article/details/160224961) | GPU / Chiplet | 异步 FIFO、GPU 算力、CTS、HBM/GDDR、UVM、Chiplet、jitter、BF16、CXL | CPU pipeline、PPA、分时启动 |
| [紫光展锐](https://blog.csdn.net/qq_39735003/article/details/160225001) | SoC / 验证 | D/A 计算、C++ OOP、三极管、Verilog time、hold 修复、验证方法学 | 选择/多选综合基础 |
| [禾赛科技](https://blog.csdn.net/qq_39735003/article/details/160225095) | 激光雷达芯片 | 同步时序、Verilog、CDC、FPGA/LUT、存储层次、功耗优化 | 简答/编程题偏数字电路工程应用 |
| [华为](https://blog.csdn.net/qq_39735003/article/details/160225137) | 大厂通用卷 | Verilog、时序逻辑、状态机、CDC、DDR4 电平、卡诺图、功耗 | 单选、多选、简答/编程综合 |
| [荣耀](https://blog.csdn.net/qq_39735003/article/details/160227576) | 手机 SoC | 编码/补码、Verilog、时序、状态机、低功耗、亚稳态、工艺节点 | 选择题为主 |
| [大疆创新](https://blog.csdn.net/qq_39735003/article/details/160227710) | 芯片可靠性 / 系统 | ATPG 故障模型、电迁移、setup/hold、奈奎斯特采样、cache/存储体系 | 故障模型与系统基础辨析 |
| [星宸科技](https://blog.csdn.net/qq_39735003/article/details/160312221) | 数字电路 + 体系结构 | C 水仙花数、DFF 时序、STA 计算、CPI/MIPS、逻辑代数化简 | C 代码补全、STA 计算、性能加速比 |
| [芯海科技](https://blog.csdn.net/qq_39735003/article/details/160312953) | 设计 + 验证 | DFF 最高频率、组合/时序识别、UVM 可复用、SV 语法、CDC、竞争冒险 | 20 道单选综合 |
| [泰凌微](https://blog.csdn.net/qq_39735003/article/details/160345348) | MCU / 工具链 | Verilog/SV 可综合语句、变量命名、Vim/Linux、FIFO、OOP、`timescale`、`chmod` | 语法与工具基础 |
| [MPS 芯源](https://blog.csdn.net/qq_39735003/article/details/160345857) | 电源芯片 / 后端 | 50% 占空比 5 分频、P&R 流程、MUX 实现 XOR、recovery/removal、latch vs DFF | 5 分频；后端流程；时序概念 |
| [商汤](https://blog.csdn.net/qq_39735003/article/details/160635686) | AI / 体系结构 | FIFO 深度、pre-full 延迟、正则表达式、流水线冲突、博弈题 | FIFO 深度计算；流水线冲突分析 |
| [艾为电子](https://blog.csdn.net/qq_39735003/article/details/160636122) | 模拟/数模芯片 | 数制转换、CMOS 逻辑、布尔代数、K-map、格雷码、计数器、亚稳态 | Verilog/VHDL 5 分频 |
| [海光](https://blog.csdn.net/qq_39735003/article/details/160668588) | CPU / 验证 | 异步 FIFO、逻辑化简、故障观测、setup slack、CMOS 延时、UVM | 单选 + UVM/时序多选 |
| [兆易创新](https://blog.csdn.net/qq_39735003/article/details/160668780) | 存储/MCU | SVA implication 波形、MUX 逻辑、序列检测计数、按键消抖、skew/jitter | `101101` 重叠序列检测；可配置消抖 |
| [数字 IC 验证 88 题](https://blog.csdn.net/qq_39735003/article/details/160691109) | DV / UVM | SV 数组/线程、task/function、OOP、factory、sequence、coverage、assertion、形式验证 | 验证问答题集合 |
| [中兴微电子](https://blog.csdn.net/qq_39735003/article/details/160744614) | 通信芯片 | RTL 仿真、低功耗、CDC、异步 FIFO、工具链、FPGA 时钟、ASIC 流程 | 两级同步器；时钟门控 |
| [紫光国微](https://blog.csdn.net/qq_39735003/article/details/160746529) | 安全芯片 / FPGA | 异步复位同步释放、setup 修复、异步 FIFO、低功耗、Moore/Mealy | 异步复位同步释放；奇数分频 |
| [韦尔股份](https://blog.csdn.net/qq_39735003/article/details/160746812) | CIS / ISP | 阻塞/非阻塞、CMOS 图像传感器噪声、异步 FIFO、ISP 流程、数模接口 | 边沿检测；同步 FIFO |
| [澜起科技](https://blog.csdn.net/qq_39735003/article/details/160764630) | DDR / PCIe | PCIe Retimer、DDR4 校准、SerDes NRZ/PAM4、DFT scan、setup slack、CDC、低功耗 | 异步复位同步释放；4 拍去毛刺；Scan chain |
| [国科微](https://blog.csdn.net/qq_39735003/article/details/160765199) | 视频 / 存储 | 视频去块滤波、NAND WAF、latch 推断、ISP、异步 FIFO、LDPC/磨损均衡 | 5 分频 50% 占空比；20ms 按键消抖 |
| [龙芯中科](https://blog.csdn.net/qq_39735003/article/details/160766806) | CPU / 互联 | 格雷码转换、AXI outstanding、MESI、同步/异步 FIFO、testbench 思路 | 格雷码转换验证；FIFO 空满判断 |
| [飞腾信息](https://blog.csdn.net/qq_39735003/article/details/160771134) | CPU / 总线 | 流水线冒险、MESI、异步 FIFO、setup/hold、UVM driver、AHB/AXI、低功耗 | 上升沿检测；同步 FIFO；项目难点 |
| [瑞芯微](https://blog.csdn.net/qq_39735003/article/details/160831278) | 多媒体 SoC | 低功耗、STA、CDC、AHB、异步 FIFO、AXI、Verilog 可综合性 | 同步 FIFO；3 分频 |
| [全志科技](https://blog.csdn.net/qq_39735003/article/details/160898919) | 应用处理器 SoC | multicycle、poly 电阻、`input delay`、复位、补码、MTBF、时钟质量、AHB/APB、低功耗 | 50% 三分频；16-bit/8-bit 除法器 |
| [晶晨股份](https://blog.csdn.net/qq_39735003/article/details/160899398) | 视频 SoC | CTS、hold 修复、CMOS 功耗、视频解码低功耗、AHB/APB、异步 FIFO | 50% 三分频；16-bit/8-bit 除法器 |
| [北京君正](https://blog.csdn.net/qq_39735003/article/details/160899633) | RISC-V / NPU | multicycle、RISC-V ISA、异步 FIFO、setup/hold、`volatile`、AHB/APB、NPU 低功耗 | 异步 FIFO；Moore 型 `1011` 序列检测 |
| [寒武纪](https://blog.csdn.net/qq_39735003/article/details/160934597) | AI 加速器 | 时序约束、工艺、状态机、数制、复位、MLU 张量核、混合精度、DVFS | 客观题综合 |
| [壁仞科技面试](https://blog.csdn.net/qq_39735003/article/details/160934805) | GPU / 封装 | 异步时钟路径、方块电阻、`input delay`、Moore、补码、BR100、2.5D CoWoS | 波形与基础时序题 |
| [天数智芯](https://blog.csdn.net/qq_39735003/article/details/160934880) | GPGPU | `set_false_path`、CDC、GPU 峰值算力、GPGPU vs ASIC、天枢架构、setup/hold | 4 路固定优先级仲裁器；MAC |
| [瀚博半导体](https://blog.csdn.net/qq_39735003/article/details/160935018) | AI 推理 / GPU | `set_clock_groups -asynchronous`、C++ `static`、指针/引用、VUCA、CDC、低功耗 | 4 拍去毛刺；序列检测器；推理 vs 训练 |
| [燧原科技](https://blog.csdn.net/qq_39735003/article/details/160935144) | AI 训练/推理 | AHB 响应、`input delay`、CDC、异步 FIFO、降采样低通、BN、MAC、训推一体 | FIFO 深度 + 异步 FIFO；MAC；BN 简答 |
| [摩尔线程](https://blog.csdn.net/qq_39735003/article/details/160935366) | GPU | `set_false_path`、AXI、半导体工艺、状态机、MUSA/花港、C++、低功耗 | 4 拍去毛刺 |
| [沐曦集成](https://blog.csdn.net/qq_39735003/article/details/160935505) | GPU | 逻辑综合、setup slack、CDC、复位、状态机、SIMT、曦云 C 系列、MXMACA | 50% 三分频 |
| [中微半导](https://blog.csdn.net/qq_39735003/article/details/160948097) | MCU | multicycle、异步复位、逻辑化简、setup/hold、亚稳态、异步 FIFO、MCU 外设 | 异步 FIFO |
| [航顺芯片](https://blog.csdn.net/qq_39735003/article/details/160948677) | MCU | ARM Cortex-M3 中断、MCU 启动、通信接口、Verilog 赋值、CDC、低功耗 | MCU 低功耗与总线简答 |
| [芯旺微电子](https://blog.csdn.net/qq_39735003/article/details/161025204) | MCU | 亚稳态、两级同步器、setup/hold、异步 FIFO、低功耗 | 基础时序/CDC 简答 |
| [国民技术](https://blog.csdn.net/qq_39735003/article/details/161025598) | MCU / 安全芯片 | STA、Verilog 归约、逻辑化简、CDC、异步 FIFO、ARM MCU、面积优化 | 单比特去毛刺 |
| [数字 IC 经典问题集](https://blog.csdn.net/qq_39735003/article/details/161122107) | 综合复习 | 竞争冒险、亚稳态、setup/hold、同步/异步逻辑、STA/DTA、FPGA/ASIC、CMOS、CDC、低功耗 | 口述题集合 |
| [鑫存储](https://blog.csdn.net/qq_39735003/article/details/161233690) | DRAM | DRAM 读流程、`tRCD`、`tREFI`、1T1C、refresh、CDC、MBIST、数模混合 | DRAM 原理简答 |
| [芯邦科技](https://blog.csdn.net/qq_39735003/article/details/161233926) | Flash / UWB | NAND/NOR、ECC、wear leveling、UWB TOF/TDOA、CDC、setup/hold | 8-bit LFSR |
| [江苏华存](https://blog.csdn.net/qq_39735003/article/details/161494030) | PCIe / NVMe / NAND | PCIe Switch/Root Complex、NVMe queue、NAND 层级、CDC、setup/hold 修复 | PCIe/NVMe/NAND 简答 |
| [江波龙](https://blog.csdn.net/qq_39735003/article/details/161494125) | SSD / UFS | NAND spare/OOB、NVMe AQA、UFS、端接匹配、SSD IOPS、NAND vs eMMC | SSD 读命令数据流 |
| [佰维存储](https://blog.csdn.net/qq_39735003/article/details/161524128) | 存储 | setup/hold、Flash/SSD、CDC、低功耗 | 存储方向基础题 |
| [德明利](https://blog.csdn.net/qq_39735003/article/details/161524206) | NAND 控制器 | 多通道、FTL GC、亚稳态、异步 FIFO、DMA、ECC、FW/HW 协同 | 建立/保持；Flash 控制器简答 |
| [紫光同创](https://blog.csdn.net/qq_39735003/article/details/161535356) | FPGA | LUT、CLB、进位链、布局布线、setup/hold、亚稳态、异步复位 | FPGA 基础与时序题 |
| [复旦微电](https://blog.csdn.net/qq_39735003/article/details/161753082) | MCU / SoC | Cortex-M 中断、NAND Flash、CDC、亚稳态、异步 FIFO、MCU 低功耗 | 建立/保持；MCU/NAND 简答 |
| [专栏总览](https://blog.csdn.net/qq_39735003/article/details/161234013) | 求职方法论 | 笔试难度、时序思维、代码规范、项目经验、真题征集 | 用作复习路线参考 |

### 高频考点清单

| 考点 | 笔试常见问法 | 速答口径 | 详细笔记 |
| --- | --- | --- | --- |
| Multicycle path | setup 设为 N，hold 应设多少？ | 常见 SDC 口径：`set_multicycle_path -setup N` 后，hold 通常设为 `N-1`，否则 hold 检查会被错误放松。 | [时序与 STA](../knowledge-base/asic-frontend.md#timing-sta) |
| `input delay` | 外部器件 delay + PCB delay + clock uncertainty 怎么算？ | `set_input_delay` 通常填外部器件输出延迟 + 板级走线延迟；clock uncertainty 单独约束，不混入 input delay。 | [时序与 STA](../knowledge-base/asic-frontend.md#timing-sta) |
| Setup / hold 修复 | setup/hold violation 分别怎么修？ | setup：降频、pipeline、重构组合逻辑、换快 cell；hold：数据路径插 buffer/延迟单元或调整 skew，降频无效。 | [时序与 STA](../knowledge-base/asic-frontend.md#timing-sta) |
| 异步复位 | 异步复位是否能直接用？ | 常用设计是 async assert, sync deassert；释放沿靠近时钟会触发 recovery/removal 风险。 | [CDC/RDC](../knowledge-base/asic-frontend.md#cdc-rdc) |
| 亚稳态 / MTBF | 两级同步器为什么有效但不能 100% 消除？ | 多给一级恢复时间，故障概率指数下降；亚稳态恢复时间是概率分布，理论上无法降到 0。 | [CDC/RDC](../knowledge-base/asic-frontend.md#cdc-rdc) |
| 异步 FIFO | 为什么指针用 gray code？空满怎么判？ | 二进制多 bit 跳变跨域会采到非法中间值；gray 每次只变 1 bit。空在读域判，满在写域判，先同步对方 gray pointer。 | [CDC/RDC](../knowledge-base/asic-frontend.md#cdc-rdc) / [同步 FIFO](../knowledge-base/asic-frontend.md#sync-fifo) |
| Moore / Mealy | 输出依赖状态还是输入？ | Moore 输出只依赖当前状态，毛刺更好控；Mealy 输出依赖状态和输入，可能状态更少但输入毛刺要小心。 | [SystemVerilog 笔试 Coding Patterns](../knowledge-base/systemverilog-uvm.md#sv-coding-patterns) |
| DFT scan chain | scan chain 用来解决什么？ | 把普通 flop 串成 scan flop 链，提高内部节点可控性/可观察性，用于 ATPG 制造测试，不是用来修 STA 时序违例。 | [Scan chain](../knowledge-base/asic-frontend.md#scan-chain) |
| AHB / APB | AHB 和 APB 典型区别？ | AHB 面向高性能系统互联，支持流水线/突发；APB 面向低速外设，简单、低功耗、无流水线，常挂在 bridge 后。 | [APB](../knowledge-base/protocols.md#apb) |
| AXI / ready-valid | 握手什么时候完成？ | `VALID && READY` 同周期完成；source 不应等 READY 才拉 VALID，否则可能死锁。 | [AXI valid/ready handshake](../knowledge-base/protocols.md#axi-valid-ready) |
| SV 相等运算 | `==` 和 `===` 有什么区别？ | `==` 遇到 X/Z 会得到 X；`===` 把 X/Z 当作可比较值，逐 bit case equality。 | [Blocking vs Non-blocking Assignment](../knowledge-base/systemverilog-uvm.md#sv-blocking-nonblocking) |
| UVM 层次 | UVM 顶层根节点是什么？ | `uvm_root` 是 UVM component tree 的单例根节点；用户 test 在它下面。 | [UVM Component Hierarchy](../knowledge-base/systemverilog-uvm.md#uvm-component-hierarchy) |
| 低功耗 | 动态/静态功耗怎么降？ | 动态功耗近似 `P = C V^2 f`：clock gating、DVFS、operand isolation；静态漏电重点看 power gating、HVT、温度。 | [时序与 STA](../knowledge-base/asic-frontend.md#timing-sta) |
| 高速接口 | Retimer 和 Repeater 区别？ | Retimer 有 CDR，恢复时钟并重新定时，可打断抖动累积；Repeater 多偏模拟放大/均衡，不完整恢复时钟。 | [Protocols](../knowledge-base/protocols.md#protocol-overview) |
| Flash / UWB | 芯邦类存储/通信题怎么答？ | NAND 读写按 page、擦除按 block；ECC 检测/纠错 bit error；wear leveling 均衡 P/E 次数；UWB 常用 TOF/TDOA 测距。 | [Protocols](../knowledge-base/protocols.md#protocol-overview) |
| DRAM / SSD | 存储厂商卷常问什么？ | DRAM 看 1T1C、activate/read/precharge、refresh、`tRCD/tREFI`；SSD 看 NAND page/block、FTL、GC、wear leveling、ECC、NVMe queue。 | [Protocols](../knowledge-base/protocols.md#protocol-overview) |
| GPU / AI 芯片 | AI/GPU 公司特色题怎么答？ | 常见是峰值算力、SIMT/GPGPU vs ASIC、MAC array、BN 推理融合、HBM/GDDR、低功耗/PPA；回答要把吞吐、带宽、灵活性和能效一起讲。 | [Cache 基础](../knowledge-base/asic-frontend.md#cache-basics) |
| SVA / 波形断言 | `|->` 和 `|=>` 怎么判断？ | `|->` 是 overlapped implication，同周期开始检查 consequent；`|=>` 是 non-overlapped，下一周期开始检查。 | [SVA](../knowledge-base/systemverilog-uvm.md#sva) |
| FPGA 基础 | FPGA 厂商卷常问什么？ | LUT 实现组合逻辑，CLB 包含 LUT/FF/进位链，布局布线影响关键路径；FPGA 时钟要走专用 clock resource。 | [ASIC Frontend](../knowledge-base/asic-frontend.md#asic-overview) |
| 后端 / DFT / 可靠性 | 后端相关客观题如何归类？ | CTS、P&R、ATPG stuck-at/transition/path-delay、scan chain、电迁移、skew/jitter 都是“实现与可测试性”方向，不要混成 RTL 功能题。 | [Scan chain](../knowledge-base/asic-frontend.md#scan-chain) |

### 代码题速记

| 题型 | 常见要求 | 写题骨架 |
| --- | --- | --- |
| 4 拍去毛刺 | 输入稳定超过 4 个时钟后更新输出 | 保存上一拍输入；输入与输出不同则计数，计满再更新；输入回到原值则清计数。 |
| 20ms 按键消抖 | 50MHz 时钟，可配置稳定时长 | 计数阈值 = `CLK_FREQ * debounce_ms / 1000`；输入变化后先计数，稳定到阈值才更新输出。 |
| 异步复位同步释放 | `async_rst_n` 输入，输出 `sync_rst_n` | 两级 flop，敏感表 `posedge clk or negedge async_rst_n`；assert 立即清零，deassert 逐拍移入 1。 |
| 两级同步器 | 单 bit CDC 同步 | 目的时钟域串两级 flop；只用于单 bit 慢变化电平，快到慢脉冲要展宽或握手。 |
| 异步 FIFO | 深度 16、宽度 8，空满正确 | bin pointer + gray pointer；gray 跨域两拍同步；读域判 empty，写域判 full。 |
| 同步 FIFO | 单 clock FIFO，空满正确 | `mem + wr_ptr + rd_ptr + count`；同周期读写时 count 不变；明确读延迟和 reset 行为。 |
| `1011` 序列检测 | 支持重叠检测，输出 1 拍 pulse | 状态表示已匹配前缀 `""/1/10/101/1011`；命中后根据新输入跳到最长可复用前缀。 |
| `101101` 序列检测计数 | 支持重叠检测并累计次数 | FSM 输出 pulse 后继续保留最长后缀前缀；计数器只在 pulse 周期加 1。 |
| 上升沿检测 | 输入同步后检测 rising edge | 先打一拍 `din_d`，输出 `pulse = din & ~din_d`；跨域输入先同步再边沿检测。 |
| 50% 三分频 | 输入 clk，输出占空比 50% | 上升沿和下降沿各生成一个三分频相位，再组合得到 1.5 个输入周期高、1.5 个输入周期低。 |
| 50% 五分频 / 奇数分频 | 奇数 N 分频，占空比 50% | 上升沿计数生成一个相位，下降沿生成半周期偏移相位，再组合；普通单沿计数只能得到非 50% 占空比。 |
| 除法器 | 16-bit unsigned / 8-bit unsigned | 用 shift-subtract 时序算法：移位、比较 divisor、减法、写 quotient bit，最后输出 remainder。 |
| 固定优先级仲裁器 | 4 路 req，输出 one-hot grant | `if req[0] ... else if req[1] ...` 或 priority case；明确无请求时 grant 全 0。 |
| MAC 单元 | `acc = acc + A * B`，带 load/en | 乘法组合或寄存，acc 时序累加；`load` 初始化，`en` 控制累加；注意位宽扩展。 |
| 8-bit LFSR | 多项式 `x^8 + x^6 + x^5 + x^4 + 1` | feedback = bit7 ^ bit5 ^ bit4 ^ bit3；复位种子不能为 0；`en` 高时移位更新。 |
| 时钟门控单元 | 空闲时关闭模块时钟 | 工程中用 ICG cell，不用普通组合逻辑直接生成 clock；enable 需锁存/稳定，避免毛刺。 |
| 格雷码转换验证 | binary/gray 互转 + testbench | `gray = bin ^ (bin >> 1)`；验证可遍历输入，检查相邻 gray 只有 1 bit 变化以及反转换正确。 |

### 复习顺序

1. 先刷共性题：multicycle、setup/hold、复位、CDC、异步 FIFO、DFF 波形、低功耗。
2. 再刷手撕题：去毛刺、异步复位同步释放、异步 FIFO、序列检测、三分频、除法器、仲裁器、MAC、LFSR。
3. 最后按公司特色补：澜起看 PCIe/DDR/SerDes/DFT；燧原/天数/瀚博看 AI/GPU/BN/MAC；君正看 RISC-V/NPU；晶晨看视频 SoC 低功耗；芯邦看 Flash/UWB。

---

<a id="qb-asic-frontend"></a>
## ASIC Frontend

| 问题 | 简短答案 | 详细笔记 | 熟练度 |
| --- | --- | --- | --- |
| Setup time 和 hold time 的区别是什么？ | Setup：时钟沿前数据必须稳定的最短时间（路径太长→违例）；Hold：时钟沿后数据必须继续稳定的最短时间（路径太短→违例）；Hold 违例不能靠降频解决。 | [时序与 STA](../knowledge-base/asic-frontend.md#timing-sta) |  |
| 两级 synchronizer 的作用是什么？ | 给第一个触发器足够时间从 metastable 状态恢复，第二级采样稳定值；只适用于单 bit 慢变化信号，不能保证多 bit 完整性。 | [CDC/RDC](../knowledge-base/asic-frontend.md#cdc-rdc) |  |
| Memory compiler 里设置 HVT 是什么意思？ | HVT memory macro leakage 更低但速度更慢，适合非 timing-critical 或低功耗场景；选择要结合 timing/power/area report。 | [Memory compiler / HVT](../knowledge-base/asic-frontend.md#memory-hvt) / [紫光展锐面经](../actual-interviews/asic.md#unisoc) |  |
| Scan chain 是什么，为什么需要？ | Scan chain 把 scan flop 串起来，在 test mode 下 shift in/out ATPG pattern，提高内部寄存器可控性和可观察性。 | [Scan chain](../knowledge-base/asic-frontend.md#scan-chain) / [紫光展锐面经](../actual-interviews/asic.md#unisoc) |  |
| 怎么看综合报告？ | 先看 WNS/TNS 和 critical path，再看 logic depth、fanout、area/power/cell usage 和约束是否合理。 | [综合报告和逻辑深度](../knowledge-base/asic-frontend.md#synthesis-report-logic-depth) / [字节面经](../actual-interviews/asic.md#bytedance) |  |
| 逻辑深度为什么影响频率？ | 一个周期内组合逻辑级数越深，path delay 越大，越容易 setup violation；常用 pipeline、拆 mux、重构 datapath 优化。 | [综合报告和逻辑深度](../knowledge-base/asic-frontend.md#synthesis-report-logic-depth) / [字节面经](../actual-interviews/asic.md#bytedance) |  |
| OoO 的核心机制是什么？ | OoO 允许 ready 指令乱序执行，但通过 ROB 按序提交；rename 消除假相关，RS/issue queue 等待 operand ready，LSQ 处理访存相关。 | [OoO 基础](../knowledge-base/asic-frontend.md#ooo-basics) / [字节面经](../actual-interviews/asic.md#bytedance) |  |
| OoO 为什么需要 ROB？ | ROB 让指令虽然可以乱序执行，但必须按 program order commit，从而保证 precise exception、branch recovery 和 architectural state 一致。 | [OoO 基础](../knowledge-base/asic-frontend.md#ooo-basics) |  |
| Cache 的 tag/index/offset 分别是什么？ | Index 选择 cache set，tag 和 set 内各 way 比较判断 hit/miss，offset 选择 cache line 内的 byte/word。 | [Cache 基础](../knowledge-base/asic-frontend.md#cache-basics) |  |
| Direct-mapped 和 set-associative cache 有什么区别？ | Direct-mapped 每个 memory block 只能放一个位置，硬件简单但 conflict miss 多；set-associative 可放到同一 set 的多个 way 中，是性能和复杂度折中。 | [Cache 基础](../knowledge-base/asic-frontend.md#cache-basics) |  |
| Write-through 和 write-back cache 有什么区别？ | Write-through 每次写 cache 同时写下一级，简单但带宽压力大；write-back 先只写 cache，dirty line eviction 时再写回，性能好但控制复杂。 | [Cache 基础](../knowledge-base/asic-frontend.md#cache-basics) |  |
| Cache coherence 和 memory consistency 的区别？ | Coherence 关注同一地址在多个 cache 副本间的一致性；consistency 关注不同地址 memory operation 的全局可见顺序。 | [Cache 基础](../knowledge-base/asic-frontend.md#cache-basics) |  |
| NPU 项目中 4x4 MAC array 怎么讲？ | 4x4 MAC array 每周期并行完成 16 次 INT8 乘加，accumulator 路径集成 bias、ReLU 和 max-pooling compare，核心价值是提升 CNN convolution throughput。 | [INT8 NPU 流片项目](../projects-hr/projects-and-behavioral.md#star-int8-npu-tapeout) |  |
| NPU 项目中 unified buffer 和 weight SRAM 的作用？ | 16 KB unified buffer 存 feature map 和 intermediate result，1 KB weight SRAM 存权重；仲裁外部写入、内部计算读取和结果写回，缓解带宽冲突。 | [INT8 NPU 流片项目](../projects-hr/projects-and-behavioral.md#star-int8-npu-tapeout) |  |

<a id="qb-design-verification"></a>
## Design Verification

| 问题 | 简短答案 | 详细笔记 | 熟练度 |
| --- | --- | --- | --- |
| Functional coverage 和 code coverage 的区别？ | Functional coverage 由工程师根据 spec 手写，测量功能场景是否命中；code coverage 由工具自动统计 RTL 执行情况（line/branch/toggle/FSM）；两者互补，均需关注。 | [Functional Coverage](../knowledge-base/design-verification.md#functional-coverage) |  |
| 如何 debug 一个 regression failure？ | 固定 seed 复现 → 找 first failure（不是最后一个 error）→ 在 first failure 附近开 waveform → trace transaction（driver→monitor→scoreboard）→ 区分 TB/DUT 问题 → 最小化 testcase。 | [Debug 方法](../knowledge-base/design-verification.md#debug-methods) |  |
| 如何从零验证一个 FIFO？ | 先读 spec 拆 testplan，再搭 driver/monitor/scoreboard，用 queue 做 reference FIFO，并覆盖 full/empty/simultaneous/reset/overflow/underflow。 | [FIFO 验证](dv-online-digest.md#dv-fifo-verification) |  |
| 什么是 coverage-driven verification？ | 从 spec 建 verification plan，把 feature 转成 coverage model，通过 CRV/regression/coverage hole analysis 收敛验证。 | [Coverage-driven verification](dv-online-digest.md#dv-coverage-driven) |  |
| 100% code coverage 但 functional coverage 很低怎么办？ | 检查 coverage model 是否对齐 spec、约束是否能触达目标场景、code coverage exclusion 是否合理，再分析并关闭 coverage holes。 | [Code coverage vs functional coverage](dv-online-digest.md#dv-code-vs-functional-low) |  |
| Scoreboard 怎么设计？ | In-order 用 FIFO/queue 顺序比较；out-of-order 用 transaction ID 和 associative array 匹配 expected/actual。 | [Scoreboard 设计](dv-online-digest.md#dv-scoreboard-design) |  |
| Directed test 和 constrained-random test 怎么取舍？ | Directed 适合 bring-up 和明确 corner case；CRV 适合探索大状态空间，并用 coverage 判断是否 hit 到目标。 | [Verification Plan](../knowledge-base/design-verification.md#verification-plan) |  |
| 如何 debug intermittent regression failure？ | 固定 seed 复现，记录版本和命令，看 first failure，缩小 testcase，区分 TB race、DUT bug、constraint/initialization 问题。 | [Debug 方法](../knowledge-base/design-verification.md#debug-methods) |  |
| UVM regression fatal 修完后，coverage 还是低，怎么分析？ | 先按模块/覆盖类型拆 report；generated code、tie-off bus、第三方库和 toggle hole 应 waive 或单独报告，真正属于 DUT feature 的 hole 才回到 testplan 补 test。 | [AXI DMA 项目 debug 记录](../projects-hr/projects-and-behavioral.md#axi-dma-regression-debug-coverage) |  |
| AXI DMA 项目的 scoreboard 具体怎么检查数据？ | DMA start 时 scoreboard 根据 AXI-Lite monitor shadow 的 descriptor，从 shared memory model snapshot source bytes；DMA complete 时读取 destination bytes 逐 byte 比较；error/abort 场景会丢弃 pending copy，避免误报。 | [AXI DMA scoreboard 检查](../projects-hr/axi-dma-uvm-details.md#axi-dma-scoreboard-checks) |  |
| AXI DMA 项目里的 memory model 是怎么接到 DUT 和 scoreboard 的？ | `dma_memory_model` 是共享 byte-addressable sparse memory；vseq 用它 preload source，AXI memory slave BFM 在真实 AXI handshake 中读/写它，scoreboard 再从同一实例做 expected/got byte compare。 | [AXI DMA memory model](../projects-hr/axi-dma-uvm-details.md#axi-dma-memory-model) |  |
| AXI DMA 项目的 burst length 和 outstanding 怎么讲？ | Memory datapath 是 32-bit addr/data、8-bit ID；CSR `max_burst[9:2]` 配 AXI `ALEN`，默认 `8'hff` 表示 256 beats；DUT read/write outstanding window 各 8 笔，scoreboard 覆盖 depth 到 8。 | [AXI DMA 项目关键参数](../projects-hr/axi-dma-uvm-details.md#axi-dma-project-parameters) |  |
| UVM 里如何用 DPI C model 做 golden reference？ | UVM testbench 通过 DPI 调用 C model，根据同一指令和输入生成 expected result；scoreboard 比较 RTL monitor 收到的 actual 和 C model expected，可做 instruction-level 与 result-level check。 | [INT8 NPU 流片项目](../projects-hr/projects-and-behavioral.md#star-int8-npu-tapeout) |  |
| INT8 NPU 项目的具体微架构参数怎么讲？ | 指令宽度 48 bit、opcode 4 bit；activation SRAM macro 为 32-bit x 1024，weight SRAM macro 为 32-bit x 256；4 个 conv lane，每 lane 4-input INT8 MAC tree + 4 个 32-bit accumulator。 | [INT8 NPU 项目关键参数](../projects-hr/int8-npu-tapeout-details.md#int8-npu-project-parameters) |  |
| NPU 项目里 coverage 和 regression 闭环怎么讲？ | 将指令类型、卷积窗口、padding、pooling、buffer access、corner case 等纳入 coverage，回归中持续跑 C model compare，分析 coverage hole 并补 directed/random case，最终代码覆盖率收敛到 90%+。 | [INT8 NPU 流片项目](../projects-hr/projects-and-behavioral.md#star-int8-npu-tapeout) |  |
| DDR4 controller 项目里 APB + AXI VIP 是怎么用来验证的？ | APB VIP 负责配置 controller/PHY 寄存器并 polling init/training done；AXI4 VIP 负责产生 DDR memory write/read burst；真正检查的是地址映射、DDR4 command/timing、数据完整性和多层 scoreboard。 | [DDR4 Controller APB + AXI VIP 详细技术实现](../projects-hr/ddr4-controller-apb-axi-vip-details.md#ddr4-controller-apb-axi-vip-details) |  |
| 你这个 DDR4 NODIMM 测试配置是什么？ | `test_ddr4` 映射到 `protocol=ddr4`、`module_type=NODIMM`；defconfig 是 `DEMO_DDR4_4GB_3200MTs_1x72_x8_NODIMM`，核心是 DDR4-3200W、x8 device、1 rank、single channel。ECC support 打开但 `ECC_MODE=0`，CRC/parity/training 都按快速仿真关闭或跳过。 | [DDR4 NODIMM 测试配置](../projects-hr/ddr4-controller-apb-axi-vip-details.md#ddr4-nodimm-test-config) |  |
| DDR4 项目有哪些高级 test 场景？ | QoS 场景配 `PCFGQOS/PCFGWQOS/PERF*` 后并发发带优先级的 AXI traffic；Exclusive access 用 exclusive read/write 和 normal/exclusive 干扰检查 monitor 行为；ECC/poison 看 `POISONCFG`、ISR、`SLVERR` 和 multi-beat ECC RMW；unalign 看 byte address/`WSTRB`；多端口看 port arbiter mask、`PCTRL.port_en`、QoS；low-power 看 AXI LP handshake、DDRC self-refresh 和退出后恢复。 | [DDR4 高级测试场景分析](../projects-hr/ddr4-controller-apb-axi-vip-details.md#ddr4-advanced-test-scenarios) |  |
| DDR4 controller AXI VIP 的端口、burst、outstanding 参数怎么讲？ | 当前生成配置有 4 个 AXI4 port，每口 256-bit data、37-bit addr、8-bit ID/LEN；AXI4 max burst 256 beats，4KB boundary，VIP outstanding limit 默认 256。 | [DDR4 项目关键参数](../projects-hr/ddr4-controller-apb-axi-vip-details.md#ddr4-project-parameters) |  |
| DDR4 Memory VIP 会自动检查时序吗？ | 会。DDR4 Memory VIP 在 PHY 后的 JEDEC pin-level 检查 command、bank/rank state、DQ/DQS 和 `tRCD/tRP/tRAS/tRFC` 等 timing；但不替代 AXI read/write 数据一致性 scoreboard。 | [DDR4 VIP/checker 分工](../projects-hr/ddr4-controller-apb-axi-vip-details.md#ddr4-vip-checker-scope) / [VIP checker vs Scoreboard](../knowledge-base/design-verification.md#vip-checker-scoreboard) |  |
| AXI read-hash scoreboard 是 AXI VIP 自带的吗？ | 不是。AXI VIP 自带 AXI protocol checker；read-hash 是 env 自建功能 scoreboard，复用 AXI VIP monitor transaction，按 byte address 建 expected memory image 并和 RDATA 逐 byte 比较。 | [AXI read-hash 实现](../projects-hr/ddr4-controller-apb-axi-vip-details.md#ddr4-axi-read-hash-implementation) |  |
| DDR PHY / wrapper 是自己写的吗？ | 不是。这里是 Synopsys DWC DDR controller/PHY IP wrapper，把 controller 的 DFI 行为转换成 DDR4 JEDEC pin-level 信号，再接 DDR4 Memory VIP。 | [DDR4 VIP/checker 分工](../projects-hr/ddr4-controller-apb-axi-vip-details.md#ddr4-vip-checker-scope) |  |
| 怎么将信号驱动到 DUT？VIP 还是自己写 driver/BFM？ | 先分清接口方向：AXI-Lite 控制路径由自写 master agent/RAL frontdoor 驱动 CSR；AXI4 memory 侧 DUT 是 master，TB 是自写 slave BFM，被动响应 DUT 请求并随机插 ready/response delay。 | [DMA 追问复盘](../projects-hr/axi-dma-uvm-details.md#axi-dma-innosilicon-followups) / [芯动科技验证一面](../actual-interviews/asic.md#innosilicon-dv-intern) |  |
| DMA abort 注入怎么实现？ | 正常 abort 应通过 frontdoor 写 `CONTROL.abort`，检查 no-new-request、pending cleanup、IRQ/status/error stats；`force/release` 内部信号只适合白盒 fault injection，不替代 CSR abort path。 | [DMA 追问复盘](../projects-hr/axi-dma-uvm-details.md#axi-dma-innosilicon-followups) / [芯动科技验证一面](../actual-interviews/asic.md#innosilicon-dv-intern) |  |
| CPU 验证项目被问到反汇编/commit log 怎么答？ | 先诚实说明已有 directed program、VMEM preload、log/waveform 检查；再补充工业化改进方向：commit monitor、反汇编 log、reference model/RVFI-style checking 和 coverage。 | [Ibex 验证项目](../projects-hr/projects-and-behavioral.md#star-ibex-rv32im-uvm) / [芯动科技验证一面](../actual-interviews/asic.md#innosilicon-dv-intern) |  |

<a id="qb-systemverilog-uvm"></a>
## SystemVerilog / UVM

| 问题 | 简短答案 | 详细笔记 | 熟练度 |
| --- | --- | --- | --- |
| Blocking 和 non-blocking assignment 的区别？ | Blocking (`=`)：当行立即求值并更新，适合 `always_comb` 组合逻辑；Non-blocking (`<=`)：RHS 在时钟沿采样，LHS 在 time step 末尾更新，避免竞争，适合 `always_ff` 时序逻辑；混用会导致仿真/综合行为不一致。 | [Blocking vs Non-blocking Assignment](../knowledge-base/systemverilog-uvm.md#sv-blocking-nonblocking) |  |
| 手撕 find first one 怎么写？ | 本质是 priority encoder，从指定方向扫描，遇到第一个 1 输出 index 和 valid；无 1 时 valid=0。 | [find first one](../knowledge-base/asic-frontend.md#find-first-one) / [字节面经](../actual-interviews/asic.md#bytedance) |  |
| 手撕同步 FIFO 要注意什么？ | 同 clock 下用 mem、wr_ptr、rd_ptr、count；明确 full/empty、同周期读写、reset、读延迟。 | [同步 FIFO](../knowledge-base/asic-frontend.md#sync-fifo) / [字节面经](../actual-interviews/asic.md#bytedance) |  |
| 怎么检测 one-hot？ | 可用 `(x != 0) && ((x & (x-1)) == 0)`，或 SV 内建 `$onehot(x)`；`$onehot0` 允许全 0。 | [one-hot 检测](../knowledge-base/asic-frontend.md#one-hot) / [字节面经](../actual-interviews/asic.md#bytedance) |  |
| 动态数组、关联数组、队列的区别？ | 动态数组是运行时定长连续数组；关联数组是 key-value 稀疏映射；队列是支持 push/pop 的有序动态集合。 | [动态数组、关联数组、队列](../knowledge-base/systemverilog-uvm.md#sv-arrays-queues) |  |
| SV 随机化的基本机制是什么？ | 用 `rand/randc` 声明随机字段，用 constraint 限制合法空间，调用 `randomize()` 由 solver 求解。 | [SV 随机化](../knowledge-base/systemverilog-uvm.md#sv-randomization) |  |
| task + FSM 找 first1 的位置怎么写？ | 用 enum 定义 `IDLE/SEARCH/DONE/SEARCHFAIL`，状态和 index 跨 task 调用保存；每次调用 task 检查一位，找到则 DONE，扫完无 1 则 SEARCHFAIL。 | [task + FSM：find first 1](../knowledge-base/systemverilog-uvm.md#sv-task-fsm-find-first-one) / [芯动科技笔试](../actual-interviews/asic.md#innosilicon) |  |
| `fork/join_none` 并行统计二维数组每行 1 的个数要注意什么？ | 每行开一个并发进程统计，`join_none` 后如果要读结果需要 `wait fork`；fork 内必须用 `automatic int row = i` 保存 loop index。 | [fork/join_none 行并行统计](../knowledge-base/systemverilog-uvm.md#sv-fork-join-none-row-count) / [芯动科技笔试](../actual-interviews/asic.md#innosilicon) |  |
| 用 task 写 valid-ready driver/monitor TB 怎么写？ | Driver 拉高 valid 并保持 data 到 ready 为 1；ready 由 receiver 随机 backpressure；monitor 只在 `valid && ready` 同周期采样 transaction；tb 依次发送 `tx_q[5]`。 | [valid-ready task TB](../knowledge-base/systemverilog-uvm.md#sv-valid-ready-task-tb) / [芯动科技笔试](../actual-interviews/asic.md#innosilicon) |  |
| SV 的显式转换和隐式转换有什么区别？ | 隐式转换由编译器在赋值/表达式/参数传递中自动做，可能隐藏截断或 signedness 问题；显式转换由工程师写出目标类型，如 `byte'(i)`、`$signed(x)`、`$cast()`。 | [Cast：显式 / 隐式、向上 / 向下转换](../knowledge-base/systemverilog-uvm.md#sv-class-casting) |  |
| SV class 的 upcast 和 downcast 有什么区别？ | Upcast 是派生类 handle 赋给基类 handle，隐式合法但只能访问基类成员；downcast 是基类 handle 转回派生类 handle，要用 `$cast()` 检查运行时对象类型。 | [Cast：显式 / 隐式、向上 / 向下转换](../knowledge-base/systemverilog-uvm.md#sv-class-casting) |  |
| UVM factory 的作用是什么？ | 通过 factory 注册和 `type_id::create()` 创建对象，使 test 可以用 type/instance override 替换实现而不改 env。 | [UVM Factory 机制](../knowledge-base/systemverilog-uvm.md#uvm-factory) |  |
| UVM TLM 通信是什么？ | 用 port/export/imp/FIFO 在组件之间传 transaction，解耦 producer 和 consumer；常见模式是 monitor analysis port 广播，scoreboard/coverage 接收。 | [UVM TLM 通信](../knowledge-base/systemverilog-uvm.md#uvm-tlm) |  |
| UVM phase 机制是什么？ | UVM 用固定 phase 管理 testbench 生命周期，包括 build/connect/run/check/report 等，并用 objection 控制 run phase 结束。 | [UVM Phase 机制](../knowledge-base/systemverilog-uvm.md#uvm-phases) |  |
| `m_sequencer` 和 `p_sequencer` 的区别？ | `m_sequencer` 是内置通用 handle；`p_sequencer` 是声明出的强类型 handle，可访问自定义 sequencer 但耦合更高。 | [`m_sequencer` 和 `p_sequencer`](../knowledge-base/systemverilog-uvm.md#uvm-sequencer-handles) |  |
| 寄存器模型 / UVM RAL 有什么用？ | 把 DUT register map 抽象到 testbench，统一管理 address/field/reset/access/mirror，支持 frontdoor/backdoor、prediction、mirror/check 和 register coverage。 | [Register Model / UVM RAL](../knowledge-base/systemverilog-uvm.md#uvm-ral) |  |
| RAL frontdoor 和 backdoor 的区别？ | Frontdoor 通过真实 APB/AXI-Lite bus 访问寄存器，能验证 bus path 但较慢；backdoor 直接走 HDL path，快但不能替代 bus path 验证。 | [Register Model / UVM RAL](../knowledge-base/systemverilog-uvm.md#uvm-ral) |  |
| RAL mirror 和 predict 是什么？ | Mirror 是 RAL 模型里认为的寄存器值；predict 是更新 mirror 的动作，可由 sequence 手动调用，也可由 monitor + predictor 根据真实 bus transaction 更新。 | [Register Model / UVM RAL](../knowledge-base/systemverilog-uvm.md#uvm-ral) |  |
| RAL 为什么需要 adapter 和 map？ | Map 记录 register 到地址的映射；adapter 在 `uvm_reg_bus_op` 和 APB/AXI-Lite sequence item 之间转换，让 RAL frontdoor 能走真实 bus sequencer。 | [Register Model / UVM RAL](../knowledge-base/systemverilog-uvm.md#uvm-ral) |  |
| AXI DMA 项目的 RAL frontdoor 是怎么接到 AXI-Lite agent 的？ | `dma_ral_block.default_map.set_sequencer(axil_agent.sqr, reg_adapter)`；vseq 调 `rg.write/read()`，adapter 把 `uvm_reg_bus_op` 转成 `dma_axil_item`，AXI-Lite monitor 再通过 predictor 更新 RAL mirror。 | [AXI DMA RAL 具体实现](../projects-hr/axi-dma-uvm-details.md#axi-dma-ral-model) |  |
| Virtual sequence 和 virtual sequencer 的作用？ | Virtual sequence 协调多个 agent 上的普通 sequence；virtual sequencer 保存 sub-sequencer/RAL/config handle，适合多接口系统级场景。 | [Virtual Sequence / Virtual Sequencer](../knowledge-base/systemverilog-uvm.md#uvm-virtual-sequence) |  |
| `start()`、`body()`、`start_item()`、`finish_item()` 的关系？ | `start()` 启动 sequence，UVM 自动执行 `body()`；普通 sequence 在 `body()` 里用 `start_item()` 等 grant，randomize 后 `finish_item()` 发送 item 给 driver。 | [Sequence API](../knowledge-base/systemverilog-uvm.md#uvm-virtual-sequence) |  |
| 这个 AXI DMA UVM 项目的 sequence 是怎么挂到 sequencer 上的？ | Test 在 `run_phase` create 具体 vseq，再 `seq.start(env.vseqr)`；vseq 通过 `p_sequencer` 访问 virtual sequencer 保存的 RAL、memory model、IRQ 和 sub-sequencer handle；CSR item 由 RAL frontdoor + adapter 转到 AXI-Lite sequencer/driver。 | [AXI DMA sequence/vsequence 调用链](../knowledge-base/systemverilog-uvm.md#uvm-axi-dma-vseq-flow) |  |
| AXI slave BFM driver 和 active master driver 有什么区别？ | Slave BFM 不主动发 stimulus，而是响应 DUT master 请求；各 AXI channel 独立 task 并行运行；用 `try_next_item()` 非阻塞接受 test 注入的 error response，无注入时 fallback 到默认 OKAY。 | [UVM 高级技巧](../knowledge-base/systemverilog-uvm.md#uvm-advanced-patterns) |  |
| `fork/join_any` 和 `fork/join` 的区别，以及 `disable fork` 的作用？ | `join`：等所有分支结束；`join_any`：任意一个分支结束就 continue，常配 `disable fork` kill 其余分支；`join_none`：不等，立即继续。IRQ 超时等待用 `fork/join_any + disable fork`。 | [UVM 高级技巧](../knowledge-base/systemverilog-uvm.md#uvm-advanced-patterns) |  |
| `uvm_config_db` 常见坑有哪些？ | `set/get` 顺序、scope path、type mismatch、过度使用 `*`、忘记检查 `get()` 返回值都很常见。 | [`uvm_config_db` 用法](../knowledge-base/systemverilog-uvm.md#uvm-config-db) / [面经坑点](dv-online-digest.md#dv-config-db-pitfalls) |  |
| Analysis port 在 UVM 中有什么作用？ | Monitor 通过 analysis port 非阻塞 broadcast transaction，scoreboard/coverage subscriber 订阅，从而解耦 producer 和 consumer。 | [Analysis Port](../knowledge-base/systemverilog-uvm.md#uvm-analysis-port) |  |
| `|->` 和 `|=>` 的区别？ | `|->` 检查同周期 consequent；`|=>` 检查下一周期 consequent。 | [SVA](../knowledge-base/systemverilog-uvm.md#sva) |  |

<a id="qb-protocols"></a>
## Protocols

| 问题 | 简短答案 | 详细笔记 | 熟练度 |
| --- | --- | --- | --- |
| AXI-Lite 和 AXI4 的主要区别是什么？ | AXI-Lite 无 burst（单 beat）、无 ID、无 outstanding；五通道结构和 valid/ready 握手与 AXI4 相同；适合 CSR 寄存器访问，不适合高带宽数据搬移。 | [AXI-Lite 与 CSR 编程](../knowledge-base/protocols.md#axil) |  |
| AXI-Lite write transaction 中，AW 和 W 通道谁先谁后？ | 协议不规定顺序，可以同时发；slave 等两个 handshake 都完成才发 B response；monitor 需要分别 latch AW 地址和 W 数据，在 B handshake 时合并发布 transaction。 | [AXI-Lite 与 CSR 编程](../knowledge-base/protocols.md#axil) |  |
| Monitor 为什么要 latch AWADDR 而不是直接用 B 时刻的 AWADDR？ | AW handshake 和 B handshake 不在同一周期；master 在 AW handshake 完成后会撤销 AWADDR，B 到来时地址已经无效；必须在 AW 握手时 latch，read 的 ARADDR 同理。 | [AXI-Lite 与 CSR 编程](../knowledge-base/protocols.md#axil) |  |
| AXI valid/ready handshake 规则是什么？ | VALID 和 READY 同周期都高时传输完成；发送方不能等 READY 才拉高 VALID（否则可能死锁）；接收方可以在 VALID 之前就拉高 READY。 | [AXI valid/ready handshake](../knowledge-base/protocols.md#axi-valid-ready) |  |
| AXI outstanding transaction 是什么？ | Master 在前一个 transaction 完成前继续发起多个 transaction，slave/interconnect 用 ID/ordering 规则追踪未完成请求。 | [AXI outstanding](../knowledge-base/protocols.md#axi-outstanding) / [字节面经](../actual-interviews/asic.md#bytedance) |  |
| AXI interleaving 是什么？ | 多个 transaction 的 data/response 可能按 ID 和协议规则交错返回，验证时要检查 ordering、ID tracking 和 backpressure。 | [AXI interleaving](../knowledge-base/protocols.md#axi-interleaving) / [字节面经](../actual-interviews/asic.md#bytedance) |  |
| DMA 是多路一起搬运还是单独搬运？ | 先澄清“多路”含义：descriptor slot 可以存多笔配置，物理数据通道未必并行；长 transfer 会被 DMA 内部拆成多个 AXI burst/outstanding 请求，testbench 配置场景和 backpressure，但 outstanding 是 DUT master 行为。 | [DMA 追问复盘](../projects-hr/axi-dma-uvm-details.md#axi-dma-innosilicon-followups) / [芯动科技验证一面](../actual-interviews/asic.md#innosilicon-dv-intern) |  |
| 未对齐 transfer 里 WSTRB 怎么理解？ | AXI beat 仍按 data width 传输，但 WSTRB 每 bit 对应一个 byte lane，只有置 1 的 byte 有效；scoreboard/memory model 最好按 byte 粒度检查未对齐首尾 beat。 | [DMA 追问复盘](../projects-hr/axi-dma-uvm-details.md#axi-dma-innosilicon-followups) / [AXI-Lite 与 CSR 编程](../knowledge-base/protocols.md#axil) |  |
