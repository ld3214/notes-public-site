# DDR4 Controller APB + AXI VIP 验证项目 - 详细技术实现

<a id="ddr4-controller-apb-axi-vip-details"></a>

## 项目定位

这是一个基于 Synopsys DWC DDR54 验证环境整理出的 DDR4 controller 验证项目主线。项目重点不是自己实现 DDR4 物理协议 driver，而是使用现有 APB VIP 和 AXI4 VIP 作为上层 stimulus 入口：

- **APB VIP**：负责 DDR controller / PHY 相关寄存器配置和状态轮询。
- **AXI4 VIP**：负责向 DDR memory 地址空间产生 write/read burst 流量。
- **DDR controller**：负责把 AXI 请求转换成内部 HIF、DFI、PHY、DDR4 命令和数据行为。
- **Scoreboard / checker**：负责判断配置、协议、地址映射、数据完整性和 DDR4 command/timing 是否正确。

一句话讲：**APB 是配置入口，AXI 是数据入口，真正验证目标是 DDR controller 是否正确控制 DDR4。**

常用入口：[项目参数](#ddr4-project-parameters) / [NODIMM 配置](#ddr4-nodimm-test-config) / [高级测试场景](#ddr4-advanced-test-scenarios) / [VIP/checker 分工](#ddr4-vip-checker-scope) / [read-hash](#ddr4-axi-read-hash-implementation)

<a id="ddr4-project-parameters"></a>
## 项目关键参数

| 类别 | 当前工程参数 | 面试讲法 |
| --- | --- | --- |
| AXI 端口数 | `UMCTL2_A_NPORTS=4` | 当前生成配置有 4 个 active AXI master port |
| AXI 协议类型 | `UMCTL2_A_TYPE_0..3=3` | 4 个 active port 都按 AXI4 配置 |
| AXI width | data 256 bit / address 37 bit / ID 8 bit / LEN 8 bit / QoS 4 bit | 每个 port 的 data width 是 256 bit，AXI4 burst length 字段 8 bit |
| Burst length | `UMCTL2_A_LENW=8`，`SVT_AXI4_MAX_BURST_LENGTH=256` | AXI4 VIP 最大 burst 是 256 beats；AXI3 上限仍是 16 beats |
| Outstanding | `SVT_AXI_MAX_NUM_OUTSTANDING_XACT=256`，4 ports 时不降额 | 当前 VIP master 每口 outstanding limit 按 256 配置 |
| 4KB boundary | `UMCTL2_AXI_ADDR_BOUNDARY=12` | AXI transaction 不能跨 4KB boundary |
| Exclusive / user | `UMCTL2_EXCL_ACCESS=0`，`UMCTL2_AXI_USER_WIDTH=0` | exclusive access 关闭；user sideband 主要由 QoS/内部字段拼接 |
| APB | `paddr_width=32`，`pdata_width=32` | APB 用于寄存器配置和 polling；APB4 是否开启由 `DDRCTL_APB4_EN` 控制 |

<a id="ddr4-nodimm-test-config"></a>
## DDR4 NODIMM 测试配置

当前 NODIMM 测试对应的是 `test_ddr4` 路径：`runtest` 把它映射成 `protocol=ddr4`、`module_type=NODIMM`，编译时打开 `DWC_DDRCTL_MEM_DDR4_ON` 和 `DWC_DDRCTL_MEM_MODULE_TYPE_NODIMM_ON`，仿真时用 APB 配置 controller，用 AXI4 VIP 发 DDR memory traffic。

### 配置来源

| 配置层 | 文件 / 路径 | 作用 |
| --- | --- | --- |
| NODIMM defconfig | `ddr54/sim/testbench/defconfig/demo/ddr4/nodimm/DEMO_DDR4_4GB_3200MTs_1x72_x8_NODIMM_defconfig` | CINIT / testbench defconfig，描述 DDR4 NODIMM 颗粒、速率、rank、ECC support 和 init 策略 |
| protocol 映射 | `ddr54/sim/runtest` | `test_ddr4` 被识别为 `ddr4`，并设置 `module_type=NODIMM` |
| plusargs 生成 | `ddr54/sim/runtest.pm::parseDefConfigFile()` | 从 defconfig 提取 `DDR4_DEVICE_TYPE`、`DDR4_SG`、`NUM_RANKS` 等仿真参数 |
| DDR4 VIP config | `ddr54/sim/testbench/cfg/dwc_ddrctl_mem_sys_config.sv::gen_ddr4_mem_config()` | NODIMM 模式下创建普通 `svt_ddr` discrete device 配置，不走 UDIMM/RDIMM DIMM wrapper |
| RTL 常量参考 | `ddr54/src/DWC_ddrctl_cc_constants.svh` | 当前打包工程里的 controller 生成常量，用于和 defconfig 交叉核对 |

### 核心参数

| 项目 | 当前值 | 说明 |
| --- | --- | --- |
| DRAM protocol | DDR4 | `CONFIG_DWC_DDRCTL_CINIT_SDRAM_PROTOCOL_DDR4=y` |
| Module type | NODIMM | `CONFIG_DWC_DDRCTL_CINIT_MODULE_TYPE_NODIMM=y`，编译宏为 `DWC_DDRCTL_MEM_MODULE_TYPE_NODIMM_ON` |
| Defconfig 名称 | `DEMO_DDR4_4GB_3200MTs_1x72_x8_NODIMM` | 工程 demo 命名，表示 3200MT/s、1 rank、72-bit 组织、x8 device 的 NODIMM 场景 |
| Device type | `DWC_DDR4_4GB_X_8DQ` | `parseDefConfigFile()` 从 `SDRAM_CAPACITY_MBIT_0_4_GB` 和 `SDRAM_WIDTH_BITS_0_8_BITS` 拼出 |
| Speed grade | `DWC_DDR4_3200W` | DDR4-3200W |
| VIP tCK | `625ps` | `get_ddr4_speed_bin_str()` 将 `3200W` 映射为 `0_625`，UDIMM/RDIMM 配置里进一步转成 `625ps` |
| Rank | 1 rank | `CONFIG_DWC_DDRCTL_CINIT_NUM_RANKS_1_RANK=y`，APB init 里 `MSTR0_ACTIVE_RANKS=1` |
| Channel | single channel | `CONFIG_NUM_DCH=1`，`CHCTL_DUAL_CHANNEL_EN_AUX=n` |
| ECC support | enabled | `CONFIG_DWC_DDRCTL_CINIT_ECC_SUPPORT_ENABLE=y`；RTL 常量里也能看到 `MEMC_ECC_SUPPORT=1`、`MEMC_SIDEBAND_ECC_EN=1`、`DDRCTL_DDR_DRAM_ECC_WIDTH=8` |
| ECC functional mode | disabled by current init | `CONFIG_DWC_DDRCTL_CINIT_REGB_DDRC_CH0_ECCCFG0_ECC_MODE=0`；要讲清楚“支持 ECC”和“当前启用 ECC mode”不是一回事 |
| CRC / CA parity | disabled | `WR_CRC_ENABLE_AUX=n`、`RD_CRC_ENABLE_AUX=n`、`PARITY_ENABLE_AUX=n` |
| DDR4 preamble | default short setting | `DDR4_WR_PREAMBLE_AUX=n`，`MR4_RD_PREAMBLE=0` |
| Init speedup | enabled | `PRE_CKE_X1024=2`、`POST_CKE_X1024=2`、`DRAM_RSTN_X1024=2`，用于缩短仿真初始化时间 |
| PHY training | skipped | `CONFIG_CONFIG_DWC_SKIP_TRAINING=y`，适合快速仿真，不代表真实 bring-up 一定跳过 training |
| Memory VIP path | DDR4 discrete / NODIMM agent | `DWC_DDRCTL_MEM_MODULE_TYPE_NODIMM_ON` 下使用 `svt_ddr.uvm.pkg` 和 `dwc_ddrctl_svt_ddr4_agent`，不是 `svt_ddr_dimm_env` |

### plusargs 和编译宏口径

从 NODIMM defconfig 解析出来的关键仿真 plusargs 可以概括成：

```text
+DDR4_DEVICE_TYPE=DWC_DDR4_4GB_X_8DQ
+DDR4_SG=DWC_DDR4_3200W
+NUM_RANKS=1
```

编译脚本对 `test_ddr4` 共享 simv 打开的关键宏可以概括成：

```text
+define+DWC_DDRCTL_MEM_DDR4_ON
+define+DWC_DDRCTL_MEM_MODULE_TYPE_NODIMM_ON
+define+DWC_DDRCTL_MEM_NUM_RANKS=1
```

实际项目里还会根据 AXI/APB/DFI/PHY 选项加入其他宏，例如 `UMCTL2_A_AXI`、APB/AXI async clock 相关宏等。

### 和 RTL 生成常量的核对点

当前整理包里的 `DWC_ddrctl_cc_constants.svh` 显示：

| RTL 常量 | 当前值 | 需要怎么理解 |
| --- | --- | --- |
| `MEMC_DRAM_DATA_WIDTH` | 32 | controller 生成配置的数据位宽，不一定等同 defconfig 文件名里的 `1x72` 模块描述 |
| `MEMC_DRAM_ECC_WIDTH` | 8 | sideband ECC lane 宽度 |
| `MEMC_DRAM_TOTAL_DATA_WIDTH` | 40 | `32 + 8` |
| `MEMC_DFI_DATA_WIDTH` | 256 | DFI 数据总线宽度 |
| `MEMC_NUM_RANKS` | 2 | RTL 可能支持 2 rank；当前 NODIMM defconfig 只让 `ACTIVE_RANKS=1` |
| `MEMC_BURST_LENGTH` | 16 | controller 侧 burst length 生成参数 |
| `MEMC_FREQ_RATIO` | 4 | DFI/controller 频率比配置 |

如果后续 debug 出现 rank、data width、ECC lane 或 address map mismatch，要先确认三件事：当前 simv 是否真按 `test_ddr4` / NODIMM 编译，defconfig 是否通过 `parseDefConfigFile()` 转成了正确 plusargs，RTL 常量包是否来自同一版生成配置。

### 面试回答

中文 60 秒版：

> 我当前跑的是 DDR4 NODIMM 快速仿真配置。test group 走 `test_ddr4`，脚本会把 protocol 设成 `ddr4`、module type 设成 `NODIMM`，编译时打开 DDR4 和 NODIMM 相关宏。defconfig 是 `DEMO_DDR4_4GB_3200MTs_1x72_x8_NODIMM`，核心参数是 DDR4-3200W、x8 device、1 rank、single channel，VIP 侧 3200W 映射为 `tCK=625ps`。APB 负责把这些配置写进 controller/PHY 寄存器，AXI4 VIP 再产生 DDR memory write/read traffic。这个配置里 ECC support 是打开的，但 `ECCCFG0_ECC_MODE=0`，所以要区分“硬件支持 ECC”和“当前 test 是否启用 ECC 功能模式”；CRC、CA parity 都是关闭的，PHY training 也被 skip，用于加速仿真。

English 45 秒版：

> For the NODIMM regression, I use the `test_ddr4` path, which maps to `protocol=ddr4` and `module_type=NODIMM`. The defconfig is `DEMO_DDR4_4GB_3200MTs_1x72_x8_NODIMM`. It describes a DDR4-3200W, x8-device, one-rank, single-channel setup, and the DDR4 VIP maps the 3200W speed bin to a 625 ps clock period. APB is used as the CSR programming and polling path, while AXI4 VIP generates memory write/read traffic. ECC support exists in the configuration, but the current init value keeps `ECC_MODE` at zero, so this is not an ECC-enabled functional test. CRC, CA parity, and full PHY training are also disabled for a faster simulation flow.

### 常见坑

| 坑 | 正确说法 |
| --- | --- |
| 把 NODIMM 当成 UDIMM/RDIMM wrapper | NODIMM 走普通 DDR4 discrete device VIP agent；UDIMM/RDIMM 才走 DIMM-level `svt_ddr_dimm_env` |
| 看到 `ECC_SUPPORT_ENABLE=y` 就说正在测 ECC | 这只说明硬件/配置支持；当前 `ECCCFG0_ECC_MODE=0`，功能模式没有打开 |
| 只看 defconfig，不看 simv 编译宏 | defconfig 影响 CINIT 和 plusargs；VIP/env 路径还取决于 `runtest` 选择的 protocol/module type |
| 忽略 RTL constants | debug mismatch 时要核对 `DWC_ddrctl_cc_constants.svh` 里的 data width、rank、ECC、DFI width 和 defconfig 是否同源 |
| 把 skip training 当真实芯片行为 | 这里是 PVE 快速仿真配置；真实 bring-up/PHY training 策略要按 PHY 和板级需求另讲 |

## HTML 图解

已把之前画的 HTML 图加入到 notes 项目目录：

- [打开 APB + AXI VIP 验证 DDR4 Controller HTML 图解](ddr4-controller-apb-axi-vip-diagram.html)

如果 Markdown 预览器支持 raw HTML，也可以直接在本页内查看：

<iframe src="ddr4-controller-apb-axi-vip-diagram.html" title="APB + AXI VIP 验证 DDR4 Controller 图解" width="100%" height="760"></iframe>

## 工程对应位置

| 位置 | 作用 |
| --- | --- |
| `ddr54/sim/testbench/modules/ddr_uvm_pve_tb_top.sv` | testbench top，实例化 `svt_apb_if apb_if0`、`svt_axi_if axi_if`，并把 APB/AXI interface 接到 wrapper |
| `ddr54/sim/testbench/modules/dwc_ddrctl_ddr_chip_wrapper.sv` | DDR chip/controller wrapper，把 AXI/APB signal 连接到 DUT 侧 |
| `ddr54/sim/testbench/env/dwc_ddrctl_mss_env.sv` | UVM env 中 APB/AXI VIP env、sequencer、monitor、scoreboard 的连接 |
| `ddr54/sim/testbench/seq_lib/dwc_ddrctl_apb_seq_lib.sv` | APB master read/write sequence |
| `ddr54/sim/testbench/seq_lib/dwc_ddrctl_axi_master_seq_lib.sv` | AXI master basic/write/read/directed/random/streaming sequence |
| `ddr54/sim/testbench/tests/test_dwc_ddrctl_axi_directed.sv` | 典型 directed AXI write/read test |
| `ddr54/sim/runtest.pm` | 生成仿真脚本、plusargs、postprocess、`PASSED/FAILED` 结果文件 |

## 真实工程文件清单（DWC DDR54 VIP 工程）

> 以下来自 `ddr54_proj/ddr54/sim/` 目录的实际分析，对应 DDR4 + APB + AXI UVM 验证。

### 使用的 VIP（`sim/svt_model_list`）

| VIP 名称 | 版本 | 用途 |
| --- | --- | --- |
| `amba_system_env_svt` | T-2022.06 | APB + AXI SVT VIP（Synopsys AMBA） |
| `dfi_phy_svt` | U-2022.12 | DFI PHY 接口 VIP |
| `dfi_agent_svt` | U-2022.12 | DFI Agent VIP |
| `ddr_dimm_env_svt` | U-2022.12 | DDR4 DIMM 存储器模型 VIP |
| `ddr_controller_agent_svt` | U-2022.12 | DDR Controller Agent VIP |
| `ddr_data_lane_env_svt` | U-2022.12 | DDR 数据通道 VIP |

`testbench/dwc_ddrctl_pve_tb_svt_includes.svh` 中引入的 UVM 包：

```systemverilog
`include "svt_apb.uvm.pkg"                  // APB VIP
`include "svt_axi.uvm.pkg"                  // AXI VIP（`ifdef UMCTL2_A_AXI）
`include "svt_ddr.uvm.pkg"                  // DDR4 存储器模型（no-DIMM 模式）
// 或 `include "svt_ddr_dimm.uvm.pkg"       // DIMM 模式
`include "svt_dfi.uvm.pkg"                  // DFI VIP
```

DDR4 关键编译宏（`test_ddr4_shared_simv/test.sim_command`）：

```
+define+DWC_DDRCTL_MEM_DDR4_ON
+define+UMCTL2_A_AXI（使能 AXI 接口）
+define+DWC_DDRCTL_USE_AXI_ASYNC_CLKS=1
+define+DWC_DDRCTL_USE_APB_ASYNC_CLKS=1
+define+DWC_DDRCTL_MEM_MODULE_TYPE_NODIMM_ON（使用 svt_ddr.uvm.pkg）
```

### 顶层 Testbench

| 文件 | 说明 |
| --- | --- |
| `testbench/modules/ddr_uvm_pve_tb_top.sv` | TB 顶层，实例化所有 SV interface，调用 `run_test()` |
| `testbench/modules/ddr_chip.v` | DUT 封装，内含 AXI 端口 macro 定义 |
| `testbench/modules/dwc_ddrctl_wrapper.sv` | DDR controller 包装模块 |
| `testbench/compile.f` | 主编译文件列表（包含所有 VIP/TB 文件路径） |
| `testbench/dwc_ddrctl_pve_tb_svt_includes.svh` | 引入全部 SVT VIP pkg |

### APB 相关文件

| 文件 | 说明 |
| --- | --- |
| `testbench/env/apb/dwc_ddrctl_apb_master_mon_cb.sv` | APB Master Monitor Callback，继承 `svt_apb_master_monitor_callback`，输出 APB trace log |
| `testbench/env/dwc_ddrctl_reg2apb_adapter.sv` | RAL → APB 总线适配器，继承 `uvm_reg_adapter` |
| `testbench/cfg/dwc_ddrctl_apb_cfg.sv` | APB 配置类 |
| `testbench/seq_lib/dwc_ddrctl_apb_seq_lib.sv` | APB 寄存器读写序列库 |

### AXI 相关文件

| 文件 | 说明 |
| --- | --- |
| `testbench/env/axi/dwc_ddrctl_axi_master_seqr.sv` | AXI Master Sequencer，继承 `svt_axi_master_sequencer` |
| `testbench/env/axi/dwc_ddrctl_axi_master_transaction.sv` | AXI 事务封装 |
| `testbench/env/axi/dwc_ddrctl_axi_port_mon_cb.sv` | AXI 端口 Monitor Callback |
| `testbench/env/axi/dwc_ddrctl_axi_exa_ref_model.sv` | AXI Exclusive Access 参考模型 |
| `testbench/env/axi/dwc_ddrctl_xpi_mon.sv` | XPI（AXI→HIF 转换）接口监控 |
| `testbench/env/axi/dwc_ddrctl_xpi_id_checker.sv` | XPI ID 检查器 |
| `testbench/cfg/dwc_ddrctl_axi_master_cfg.sv` | AXI Master 端口配置 |
| `testbench/cfg/dwc_ddrctl_axi_system_cfg.sv` | AXI 系统配置，对应 `svt_axi_system_env` |
| `testbench/seq_lib/dwc_ddrctl_axi_master_seq_lib.sv` | AXI Master 激励序列库 |
| `testbench/seq_lib/dwc_ddrctl_axi_system_vseq_lib.sv` | AXI 系统级虚拟序列 |
| `testbench/interfaces/dwc_ddrctl_xpi_mon_if.sv` | XPI 监控接口 |

### DDR4 存储器模型文件

| 文件 | 说明 |
| --- | --- |
| `testbench/env/dwc_ddrctl_svt_ddr4_agent.sv` | DDR4 Agent，继承 `svt_ddr_agent` |
| `testbench/env/dwc_ddrctl_svt_ddr4_udimm_env.sv` | DDR4 UDIMM 环境，继承 `svt_ddr_dimm_env` |
| `testbench/env/dwc_ddrctl_svt_ddr4_rdimm_env.sv` | DDR4 RDIMM 环境 |
| `testbench/env/dwc_ddrctl_svt_ddr4_lrdimm_env.sv` | DDR4 LRDIMM 环境 |
| `testbench/env/dwc_ddrctl_svt_ddr4_3ds_env.sv` | DDR4 3DS 环境 |
| `testbench/cfg/dwc_ddrctl_svt_ddr4_config.sv` | DDR4 SVT 配置 |
| `testbench/env/dwc_ddrctl_svt_ddr_monitor_cb.sv` | DDR Monitor Callback |

### UVM 环境层次文件

| 文件 | 说明 |
| --- | --- |
| `testbench/env/dwc_ddrctl_mss_env.sv` | 顶层 MSS 环境，包含所有子环境 |
| `testbench/env/dwc_ddrctl_vip_env.sv` | VIP 包装层，实例化 `svt_apb_system_env`、`svt_axi_system_env` |
| `testbench/env/dwc_ddrctl_env.sv` | 控制器 env，含 AXI scoreboard、HIF agent |
| `testbench/env/dwc_ddrctl_dfi_env.sv` | DFI 接口环境 |
| `testbench/env/dwc_ddrctl_mem_sys_env.sv` | 存储器系统环境 |

### RAL 寄存器模型文件

| 文件 | 说明 |
| --- | --- |
| `testbench/env/ral/dwc_ddrctl_ral_pkg.sv` | RAL 主包 |
| `testbench/models/ral_DWC_ddrctl_axi_*_pkg.sv` | AXI 各端口寄存器模型（Port0~3） |
| `testbench/models/ral_DWC_ddrctl_map_REGB_ARB_PORT*_pkg.sv` | ARB PORT 寄存器 map |
| `testbench/models/ral_DWC_ddrctl_map_REGB_DDRC_CH0_pkg.sv` | DDRC Channel0 寄存器 map |

### DDR4 AXI 主要测试用例（`testbench/tests/`）

| 测试文件 | 场景 |
| --- | --- |
| `test_dwc_ddrctl_axi_basic.sv` | AXI 基本读写 |
| `test_dwc_ddrctl_axi_random.sv` | AXI 随机地址/burst |
| `test_dwc_ddrctl_axi_directed.sv` | 定向激励 |
| `test_dwc_ddrctl_axi_qos.sv` / `_qos_hpr.sv` / `_qos_lpr.sv` | QoS/优先级 |
| `test_dwc_ddrctl_axi_excl.sv` | Exclusive Access |
| `test_dwc_ddrctl_axi_excl_bypass.sv` | Exclusive bypass / 特殊路径 |
| `test_dwc_ddrctl_axi_wrap.sv` | WRAP burst |
| `test_dwc_ddrctl_axi_unalign.sv` | 非对齐访问 |
| `test_dwc_ddrctl_axi_streaming.sv` | 流式传输压力测试 |
| `test_dwc_ddrctl_axi_poison.sv` / `_rnd_poison.sv` | AXI poison / error response / interrupt |
| `test_dwc_ddrctl_axi_muti_ecc.sv` | DDR4/DDR5 multi-beat ECC RMW 场景 |
| `test_dwc_ddrctl_axi_lowpower.sv` | AXI hardware low-power + DDRC self-refresh |
| `test_dwc_ddrctl_axi_arbport_mask.sv` | Port arbiter mask / throttle |
| `test_dwc_ddrctl_axi_rand_port_disable.sv` | 动态 `PCTRL.port_en` disable/enable |
| `test_dwc_ddrctl_apb_timeout.sv` | APB 超时场景 |

<a id="ddr4-advanced-test-scenarios"></a>
## DDR4 高级测试场景分析

这些场景不是只看 AXI protocol 是否握手成功，而是把 AXI transaction 打进 DDR controller 的调度、仲裁、RMW/ECC、low-power 状态机和内部 scoreboard 链路里。共同流程一般是：先通过 `m_mss_initialize_subsystem` 做 APB/RAL 初始化，再在一个或多个 `m_mctl_axi_master_seqr[port]` 上启动对应 AXI sequence，最后由 AXI VIP checker、read-hash scoreboard、AXI-HIF scoreboard、HIF-DFI scoreboard、DDR/DFI monitor 和 ISR/postprocess 一起收敛结果。

### 场景总览

| 场景 | 主要 test / sequence | 激励重点 | 主要检查点 |
| --- | --- | --- | --- |
| QoS / priority | `test_dwc_ddrctl_axi_qos.sv`、`_qos_hpr.sv`、`_qos_lpr.sv`；`dwc_ddrctl_axi_qos_seq`、`dwc_ddrctl_axi_qos_dch1_seq` | 按 LPR/VPR/HPR/NPW/VPW 场景约束 `addr_user` 中的 QoS bits，并通过 `PCFGQOS0`、`PCFGWQOS0`、`PERFHPR1`、`PERFLPR1`、`PERFWR1` 配置优先级和 starvation/run-length | AXI-HIF 是否正确传递 priority/QoS；HIF-DFI perf recorder 统计 LPR/VPR/HPR command/response latency；read-hash 保证数据一致性 |
| Exclusive access | `test_dwc_ddrctl_axi_excl.sv`；`dwc_ddrctl_axi_rand_exa_seq`；`dwc_ddrctl_axi_exa_ref_model.sv` | 多 port 并发 exclusive read/write，覆盖 monitor under/over subscribe、same ID/different ID、exclusive 被 normal/exclusive transaction 打断 | Exclusive reference model 预测 `EXOKAY/OKAY` 行为；AXI-HIF 检查 exclusive 不跨非法 channel；read-hash 检查成功写入后的数据 |
| ECC 注错 / poison / 恢复 | `test_dwc_ddrctl_axi_poison.sv`、`_rnd_poison.sv`、`_muti_ecc.sv`；`dwc_ddrctl_axi_wrd_random_poison_seq`、`dwc_ddrctl_axi_muti_ecc_seq` | AXI poison transaction、`POISONCFG` interrupt/SLVERR 组合、ISR 等待 response 后清 interrupt；multi-beat ECC 下用 `WSTRB` mask 触发 RMW/ECC merge | Poison 场景看 `POISONCFG`、ISR、`SLVERR` 预测；ECC 场景看 `ECCCFG0/ECCCFG1/ECCSTAT/ECCERRCNT/ECCCTL/ECCPOISON*`、HIF-DFI ECC engine、read-hash skip/compare 策略 |
| 非对齐传输 | `test_dwc_ddrctl_axi_unalign.sv`；`dwc_ddrctl_axi_rand_unalign_seq` | 预留一段连续地址空间，固定一轮 write/read 的 burst size，再连续推进地址，制造可能落在 DDR burst 边界内/跨边界的 unaligned 访问 | AXI VIP 检查合法 AXI burst；read-hash 按 byte address + `WSTRB` 比较；AXI-HIF/HIF-DFI 检查拆分、mask、地址映射和 RMW 行为 |
| 多端口并发仲裁 | `test_dwc_ddrctl_axi_arbport_mask.sv`、`_rand_port_disable.sv`、`_streaming.sv` | 所有 AXI port 并发随机流量；随机拉 `pa_rmask/pa_wmask`；动态写 `PCTRL.port_en` disable/enable 单个或多个 port | read-hash 保证多端口数据不串；AXI-HIF 检查 XPI/port 转换；perf/PA monitor 看 queue depth、priority、mask 和 port enable 覆盖 |
| DDR4 低功耗状态 | `test_dwc_ddrctl_axi_lowpower.sv`，另有 `test_dwc_ddrctl_lowpower_*` 系列 | AXI hardware low-power request accept/deny、system/peripheral exit；所有 AXI port idle 后请求 DDRC 进入 self-refresh，再退出并继续发流量 | `cactive`/`cactive_ddrc` handshake、`PWRCTL/PWRTMG/STAT`、`operating_mode/selfref_state/selfref_type`、DFI low-power sideband monitor、退出后数据通路恢复 |

### QoS / Priority

QoS 测试的核心是让同一组 AXI random read/write 带上不同优先级语义，然后看 controller 是否按配置把请求映射到 LPR/VPR/HPR/NPW/VPW 队列和调度路径。

关键点：

| 点 | 说明 |
| --- | --- |
| 配置入口 | 每个 port 有 `REGB_ARB_PORTx.PCFGQOS0` / `PCFGWQOS0`，动态场景还会改 `PERFHPR1`、`PERFLPR1`、`PERFWR1` 的 max-starve 和 xact-run-length |
| 激励方式 | `dwc_ddrctl_axi_qos_seq` 给每笔 AXI transaction 加 QoS constraint policy；`_qos_hpr` / `_qos_lpr` 更偏向 HPR/LPR 定向压力 |
| 并发方式 | virtual sequence 对所有 active AXI ports fork 并发启动 QoS traffic |
| 需要防的坑 | QoS 压力容易让低优先级请求长时间 starving，所以 AXI system cfg 中部分 watchdog 被关掉；判断 pass/fail 不能只看单笔 ready latency |
| 结果判断 | 看 AXI-HIF priority 是否一致、HIF-DFI perf recorder 的 LPR/VPR/HPR 统计是否合理、数据 readback 是否正确 |

面试口径：

> QoS 场景不是简单随机 `ARQOS/AWQOS`。test 会先通过 APB/RAL 配 `PCFGQOS0/PCFGWQOS0`，定义 QoS bit 到 LPR/VPR/HPR/NPW/VPW 的映射；然后所有 AXI port 并发发带 QoS constraint 的 read/write。检查时一方面 read-hash 保证数据没有错，另一方面 AXI-HIF/HIF-DFI/perf recorder 看 priority 是否被 controller 正确传递和调度。

### Exclusive Access

Exclusive access 场景用于验证 DDR controller 对 AXI exclusive read/write monitor 的支持，以及当 exclusive monitor 被其他访问破坏时 response 是否符合预期。

覆盖点：

| 覆盖点 | 说明 |
| --- | --- |
| 成功路径 | exclusive read 记录 address/ID/size/length/port，后续匹配的 exclusive write 应成功 |
| 失败路径 | 在 exclusive read 和 write 之间插入 normal 或另一个 exclusive 访问，破坏 pending monitor |
| monitor 容量 | 根据 `UMCTL2_EXCL_ACCESS` 生成 under-subscribe、exact-subscribe、over-subscribe 场景 |
| 多 port | 每个 AXI port 都并发跑 exclusive sequence，再混入普通 random write/read |
| checker 兼容 | 工程有 `dwc_ddrctl_axi_exa_ref_model.sv` 做参考模型；AXI VIP 某些严格 control-signal 比较会被 downgrade，因为 DUT 的 exclusive 判定只要求关键字段匹配 |

当前配置注意点：项目参数里 `UMCTL2_EXCL_ACCESS=0`，所以当前 NODIMM 默认不是完整 exclusive monitor 配置。`test_dwc_ddrctl_axi_excl.sv` 仍会让 VIP 能发 exclusive-like transfer，用于检查无 monitor 或特定配置下的 expected response；如果面试追问“你真的测了 exclusive 成功路径吗”，要说明需要切到 `UMCTL2_EXCL_ACCESS>0` 的生成配置或回归条目。

### ECC 注错 / Poison / 恢复

这里要把三件事分开讲：当前 NODIMM defconfig 只是 `ECC_SUPPORT_ENABLE=y`，但默认 `ECCCFG0.ECC_MODE=0`；AXI poison 是 transaction sideband 的错误传播/中断测试；`test_dwc_ddrctl_axi_muti_ecc.sv` 才会显式把 multi-beat ECC/RMW 条件拉起来。

| 子场景 | 做什么 | 看什么 |
| --- | --- | --- |
| AXI poison 定向 | `test_dwc_ddrctl_axi_poison.sv` 选一组 port，发 poisoned read/write transaction；可根据 `POISONCFG.rd_poison_slverr_en` 期望 `SLVERR` | `POISONCFG`、AXI response、read-hash 对 poison/error 的 skip 策略 |
| AXI poison 随机 + ISR | `_rnd_poison.sv` 随机配置 `wr/rd_poison_intr_en` 和 `wr/rd_poison_slverr_en`，一个 port 发 poisoned traffic，其他 port 发普通 traffic | ISR 先登记 expected `AWPOISON_INTR/ARPOISON_INTR`，等待 AXI response 到达后再清中断，避免中断清除和 response 竞争 |
| Multi-beat ECC RMW | `_muti_ecc.sv` 关闭默认 ECC constraint，设置 `ecc_mode=4`，打开 data mask，用 `WSTRB` 随机 mask 某个 DRAM word，触发 RMW/ECC merge | `ECCCFG0/ECCCFG1`、HIF-DFI ECC engine、RMW merge、read-hash 数据一致性 |
| ECC poison 寄存器 | RTL/RAL 中存在 `ECCPOISONADDR0/1`、`ECCPOISONPAT0/2`、`ECCSTAT`、`ECCERRCNT`、`ECCCTL` | HIF-DFI normal ECC engine 会根据 poison 地址和 bit 配置预测 single-bit correctable 或 double-bit uncorrectable 行为 |

恢复路径怎么讲：

1. 对 correctable ECC，controller/scoreboard 期望数据被纠正后继续参与 readback compare，同时状态/计数器体现 corrected error。
2. 对 uncorrectable 或 poison/SLVERR，read-hash 不能盲目按正常数据比较，要根据 response/error 标志 skip 或期望 error response。
3. 中断类场景要等 AXI response 完成后再清 interrupt，否则可能出现同一 poisoned transaction 的 interrupt/response race。
4. 退出错误场景后继续发普通 write/read，用 read-hash 和 AXI-HIF/HIF-DFI 证明数据通路恢复正常。

面试口径：

> 我会把 ECC 相关场景拆成 AXI poison 和 DDR ECC RMW 两类。Poison 场景重点验证错误 sideband 是否转成 interrupt 或 `SLVERR`，并且 ISR 清中断要等 response 回来。ECC RMW 场景则通过打开 ECC mode、data mask 和特定 `WSTRB`，制造 read-modify-write，再看 HIF-DFI ECC engine 对 corrected/uncorrected error、poison bit 和 read-hash skip 策略的处理。

### 非对齐传输

非对齐测试不是直接发非法 AXI，而是在合法 AXI burst 的前提下，让请求地址和 DDR 内部 burst / data width / RMW 粒度产生不整齐关系。

流程：

1. address manager 先预留一段足够大的连续 system address，避免不同 sequence 互相踩地址。
2. 初始化一组 write/read transaction，固定本轮的 burst size 和起始地址。
3. 前半段连续 write，后半段连续 read，地址按每笔实际 block size 推进。
4. `dwc_ddrctl_axi_rand_unalign_seq` 每轮随机 burst length/size，使请求可能跨 DDR burst 边界、触发 byte-lane mask 或 RMW。
5. read-hash 按 byte 地址和 `WSTRB` 比较，AXI-HIF/HIF-DFI 检查地址拆分、mask 和数据 beat 顺序。

Debug 时如果失败，优先看 `WSTRB`、burst size、AXI address lower bits、HIF address、DDR column 地址和 read-hash 里的 byte address。

### 多端口并发仲裁

多端口场景覆盖的是 controller 前端 port arbiter 和 XPI/HIF 资源竞争，核心不是“多开几个 sequence”，而是让多个 port 在队列、mask、enable/disable、QoS 影响下同时竞争。

| 场景 | 触发方式 | 观察点 |
| --- | --- | --- |
| 普通多 port traffic | 所有 `m_mctl_axi_master_seqr[port]` fork 并发跑 `dwc_ddrctl_axi_wrd_random_seq` / streaming | port 间是否互不串数据；response/order 是否合理 |
| `pa_rmask/pa_wmask` | `test_dwc_ddrctl_axi_arbport_mask.sv` 等待若干 read/write complete 后随机拉 mask 信号 | 被 mask port 是否被 throttle，解除 mask 后是否恢复 |
| 动态 `port_en` | 随机写 `REGB_ARB_PORTx.PCTRL.port_en=0/1` | disable 时是否阻断新请求，enable 后是否继续服务 |
| QoS + 仲裁 | QoS tests 同时配置 priority 和 max-starve/run-length | 高优先级是否更快服务，低优先级是否不永久饿死 |

检查链路：AXI VIP 保证每个 port 的 protocol 合法；read-hash 保证多 port 写读不会互相污染；AXI-HIF scoreboard 看 port/QoS/ID/address 转换；HIF-DFI perf recorder 可以看 LPR/HPR queue depth、credit、latency。

### DDR4 低功耗状态

`test_dwc_ddrctl_axi_lowpower.sv` 同时测 AXI hardware low-power interface 和 DDRC low-power/self-refresh。它先打开 `hw_lp_en`，设置较短的 idle timeout 和 refresh 参数，然后每个 AXI port 依次覆盖 accept、peripheral exit、deny 三类低功耗 handshake，最后在非 DDR5 情况下做 AXI + DDRC 一起进入 self-refresh 的 case。

关键流程：

| Case | 流程 | 检查点 |
| --- | --- | --- |
| AXI LP accept + system exit | 先发少量 AXI traffic，确认 port idle，请求 LP entry，停留随机时间，再由 system 触发 exit | `cactive[port]`、低功耗 agent monitor、退出后 AXI traffic 正常 |
| AXI LP accept + peripheral exit | 进入 LP 后同时发新 AXI traffic 和 LP exit，让 peripheral activity 拉起退出 | `cactive` 是否因新事务恢复 |
| AXI LP deny | port busy 时请求 low-power，期望被拒绝 | 低功耗请求不应破坏正在进行的 AXI transaction |
| AXI + DDRC LP | 所有 port 进 LP，调用 `request_ddrc_lowpower_entry()`，等待 DDRC 进入 self-refresh，再 exit | `STAT.operating_mode`、`selfref_state`、`selfref_type`、`cactive_ddrc`、退出后普通 read/write |

DDR4 侧面试口径：

> DDR4 low-power 不只是 AXI clock gating。AXI port 先通过 hardware low-power handshake 进入 idle/clock removal 状态；当所有 port 都 idle 后，test 再请求 DDRC 进入 self-refresh，并通过 `STAT.operating_mode/selfref_state/selfref_type` 和 DFI low-power sideband monitor 检查状态。退出后还要继续发少量 AXI write/read，证明 controller 从 self-refresh 回到 normal mode 后数据路径恢复。

### 一句话总答

> 这些高级场景的共同点是都要跨层检查：AXI VIP 只保证入口协议，真正的结果要结合 RAL 配置、AXI-HIF 转换、HIF-DFI 调度、DDR4 timing/state、read-hash 数据一致性、ISR 和 postprocess。面试时我会按“激励怎么构造、配置改了哪些寄存器、checker 看哪一层、失败时先 debug 哪些信号”四步讲。

### UVM 环境层次总览

```text
ddr_uvm_pve_tb_top（顶层 SV module）
└── dwc_ddrctl_mss_env（MSS 顶层 UVM env）
    ├── dwc_ddrctl_vip_env（VIP 包装层）
    │   ├── svt_apb_system_env        ← Synopsys APB VIP
    │   ├── svt_axi_system_env        ← Synopsys AXI VIP
    │   ├── dwc_ddrctl_mem_sys_env
    │   │   └── dwc_ddrctl_svt_ddr4_udimm/rdimm/agent  ← DDR4 VIP
    │   └── dwc_ddrctl_dfi_env        ← DFI VIP
    ├── dwc_ddrctl_env（控制器 env）
    │   ├── dwc_ddrctl_axi_read_hash_sb（AXI scoreboard）
    │   ├── dwc_ddrctl_axi_exa_ref_model（Exclusive 参考模型）
    │   └── dwc_ddrctl_hif_agent
    └── dwc_ddrctl_reg_utilities（RAL + APB adapter）
        └── dwc_ddrctl_reg2apb_adapter（RAL→APB）
```

### UVM 环境层次详细讲解

#### 第一层：`ddr_uvm_pve_tb_top`（顶层 SV 模块，非 UVM 类）

这是整个验证环境的物理顶层，是一个普通 SystemVerilog `module`，不是 UVM 类。它做三件事：

1. **实例化所有 SV interface**：
   - `svt_apb_if apb_if0` — APB VIP 使用的接口，连接到 DUT 的 APB slave 端口
   - `svt_axi_if axi_if[N]` — AXI VIP 使用的接口，每个 AXI port 一个，连接 DUT AXI slave
   - `dwc_ddrctl_clkrst_if clkrst_if` — 时钟和复位接口
   - `dwc_ddrctl_dfi_*_if dfi_if` — DFI 接口，监控 controller 到 PHY 的命令/数据
   - `dwc_ddrctl_dut_probes dut_probes` — DUT 内部信号探针接口

2. **实例化 DUT（DDR Controller + PHY）**：通过 `dwc_ddrctl_ddr_chip_wrapper` 或 `ddr_chip` 把 SV interface 端口连接到 RTL 端口

3. **把所有 interface 放入 `uvm_config_db`，然后调用 `run_test()`**：
   ```systemverilog
   uvm_config_db#(virtual svt_apb_if)::set(null, "uvm_test_top.*", "apb_if", apb_if0);
   uvm_config_db#(virtual svt_axi_if)::set(null, "uvm_test_top.*", "axi_if", axi_if[0]);
   run_test();
   ```

---

#### 第二层：`dwc_ddrctl_mss_env`（MSS 顶层 UVM env）

MSS = Memory Sub-System。这是整个 UVM 验证环境的根节点，在 `build_phase` 里创建所有子环境和组件。关键成员：

| 成员 | 类型 | 作用 |
| --- | --- | --- |
| `m_vip_env` | `dwc_ddrctl_vip_env` | 所有 SVT VIP 的包装层 |
| `m_mctl_env` | `dwc_ddrctl_env` | 控制器 UVM env（HIF、scoreboard） |
| `m_mss_vseqr` | `dwc_ddrctl_mss_vseqr` | MSS 虚拟 sequencer，协调 APB/AXI/HIF 序列 |
| `m_reg_utilities` | `dwc_ddrctl_reg_utilities` | RAL 模型封装 + APB adapter |
| `m_phy_wrap` | `dwc_ddrctl_phy_wrap` | PHY UVM 组件包装 |
| `m_clkrst_gen` | `dwc_ddrctl_clkrst` | 时钟复位生成器 |
| `m_addr_mgr` | `dwc_ddrctl_addr_mgr` | 地址管理器（管理 AXI 地址到 DDR 地址映射） |
| `m_hif2dfi_sb_env` | `dwc_ddrctl_hif_dfi_sb_env` | HIF → DFI scoreboard 环境 |
| `m_perf_mon_env` | `dwc_ddrctl_perf_mon_env` | 性能监控环境 |

`connect_phase` 里会把 VIP sequencer 的句柄赋给 `m_mss_vseqr` 的对应字段，使虚拟 sequence 能调度 APB/AXI 双路流量。

---

#### 第三层 A：`dwc_ddrctl_vip_env`（VIP 包装层）

这一层的唯一目的是把所有 Synopsys SVT VIP 实例收拢在一个层级下，方便统一控制 verbosity 和 phase。

```
dwc_ddrctl_vip_env
├── svt_apb_system_env          ← APB VIP 系统级环境
│     ├── svt_apb_master_agent  ← APB Master agent（driver + monitor + sequencer）
│     └── svt_apb_slave_agent   ← APB Slave agent（可选）
│
├── svt_axi_system_env          ← AXI VIP 系统级环境（含多个 master port）
│     ├── svt_axi_master_agent[0]   ← AXI Port0 master
│     ├── svt_axi_master_agent[1]   ← AXI Port1 master
│     └── ...
│
├── dwc_ddrctl_mem_sys_env      ← DDR 存储器子系统环境
│     └── dwc_ddrctl_svt_ddr4_udimm_env  ← DDR4 UDIMM 存储器模型
│           └── svt_ddr_dimm_env / svt_ddr_agent  ← DDR4 VIP
│
└── dwc_ddrctl_dfi_env          ← DFI VIP 环境
      └── svt_dfi_phy_agent / svt_dfi_agent  ← DFI VIP
```

**`svt_apb_system_env`** 内部结构（Synopsys SVT APB VIP 标准结构）：
- `svt_apb_master_agent` 含 driver / monitor / sequencer
- driver 接收来自 sequence 的 `svt_apb_transaction`，转成 APB pin-level 信号
- monitor 观察真实 APB 总线，发布 `svt_apb_transaction` 到 analysis port
- `dwc_ddrctl_apb_master_mon_cb` callback 挂在 monitor 上，把 transaction 写入 APB trace log 并更新 RAL mirror

**`svt_axi_system_env`** 内部结构（Synopsys SVT AXI VIP 标准结构）：
- 每个 AXI port 一个 `svt_axi_master_agent`
- driver 将 `svt_axi_transaction` 转成 AW/W/B/AR/R 五通道 pin-level 信号
- monitor 观察真实 AXI bus，发布 observed transaction 到 analysis port
- `dwc_ddrctl_axi_port_mon_cb` callback 挂在 monitor 上，把 transaction 转发给 scoreboard

---

#### 第三层 B：`dwc_ddrctl_env`（控制器 UVM env）

这一层是自定义的控制器内部验证环境，关注控制器内部行为而非入口协议：

```
dwc_ddrctl_env
├── dwc_ddrctl_hif_agent[$]          ← HIF agent（观察 AXI→HIF 转换后的内部接口）
├── dwc_ddrctl_lowpower_agent        ← Low power agent（监控功耗控制信号）
├── dwc_ddrctl_miscsig_agent         ← 杂项信号 agent
├── dwc_ddrctl_isr_agent             ← 中断服务 agent
├── dwc_ddrctl_mon                   ← 控制器总 monitor
├── dwc_ddrctl_mrr_mon               ← Mode Register Read monitor
├── dwc_ddrctl_wdataram_mon          ← Write Data RAM monitor
├── dwc_ddrctl_hwffc_duration_mon    ← HW Frequency Change 时长 monitor
├── dwc_ddrctl_axi_read_hash_sb[]    ← AXI read-hash scoreboard（每 port 一个）
├── dwc_ddrctl_axi_hif_top_sb        ← AXI→HIF scoreboard
├── dwc_ddrctl_sbr_model[]           ← ECC Scrubber 参考模型
└── dwc_ddrctl_axi_exa_ref_model[]   ← AXI Exclusive Access 参考模型
```

**`dwc_ddrctl_hif_agent`** 的作用：
- HIF（Host Interface）是 AXI port 进入 controller 后第一个内部接口
- HIF agent 监控 AXI→HIF 地址/命令转换，是 AXI-HIF scoreboard 的数据来源

**`dwc_ddrctl_axi_read_hash_sb`** 的作用：
- 写路径：从 AXI write monitor 收到写地址和写数据，存入 hash table
- 读路径：从 AXI read monitor 收到读数据，与 hash table 中期望值比较
- 这是 end-to-end 数据完整性检查的核心

<a id="ddr4-vip-checker-scope"></a>
### VIP checker 和自定义 scoreboard 分工

这个项目里要把 **VIP 自带协议 checker** 和 **环境自建 scoreboard** 分清楚。VIP 主要保证接口协议合法，scoreboard 主要保证 DUT 的功能转换和数据一致性正确。

| 检查对象 | 来源 | 主要检查内容 |
| --- | --- | --- |
| APB VIP checker | Synopsys SVT APB VIP | APB `PSEL/PENABLE/PREADY/PSLVERR`、地址/数据 phase、APB4 strobe/protection 等协议合法性 |
| AXI VIP checker | Synopsys SVT AXI VIP | AXI five-channel valid/ready、burst length/size/type、ID/response/order、outstanding、`WLAST/RLAST` 等协议合法性 |
| DFI VIP / DFI monitor | Synopsys SVT DFI VIP + env adapter | Controller 到 PHY 的 DFI command/data、init/update、read/write latency、sideband/retry 等接口行为 |
| DDR4 Memory VIP | Synopsys SVT DDR4 VIP | PHY 输出后的 DDR4 JEDEC pin-level command、bank/rank state、DQ/DQS 数据行为和 DDR4 timing violation |
| AXI read-hash scoreboard | `env/sb/dwc_ddrctl_axi_read_hash.sv` | end-to-end 数据一致性：AXI write 写入的 byte 是否能在后续 AXI read 中按同地址读回 |
| AXI-HIF scoreboard | `env/sb/axi_hif_sb/` | AXI transaction 到内部 HIF command/response 的地址、长度、ID、QoS、burst 转换 |
| HIF-DFI scoreboard | `env/sb/hif_dfi_sb/` | HIF request 到 DFI command/data 的转换、rank/bank/row/col 映射、RMW/ECC/CRC 等行为 |

**关键边界**：

- DDR4 Memory VIP 接的是 PHY 之后的 DDR4 pin-level interface，不直接接 DFI。
- DFI 是 controller 和 PHY 之间的接口，主要由 DFI VIP / HIF-DFI scoreboard 监控。
- AXI read-hash scoreboard 不是 AXI VIP 自带功能，而是 PVE/UVM env 中自建的功能 scoreboard；它复用 AXI VIP monitor 采到的 `svt_axi_transaction`。
- `DDR PHY / wrapper` 不是自己写的逻辑，而是 Synopsys DWC DDR controller/PHY IP wrapper，负责把 controller 的 DFI 行为转换成 DDR4 物理引脚行为。

可以把链路记成：

```text
APB/AXI VIP
  -> DDR controller DUT
  -> DFI interface
  -> DDR PHY / wrapper
  -> DDR4 JEDEC pin-level interface
  -> DDR4 Memory VIP
```

<a id="ddr4-axi-read-hash-implementation"></a>
### AXI read-hash scoreboard 实现细节

`read-hash` 里的 hash 不是 CRC/MD5 这类算法，而是 **用 SystemVerilog associative array 建一个 sparse memory image**。工程源码里的核心结构类似：

```systemverilog
static bit [7:0] m_sb_mem_byte[DWC_DDRCTL_NUM_CHANNEL][dwc_ddrctl_a_addrw_t];
```

含义是：

```text
m_sb_mem_byte[channel][byte_addr] = expected_byte_data
```

检查流程：

1. AXI VIP monitor 观察真实 AXI bus，完整 transaction 结束后通过 `item_observed_port` 广播 `svt_axi_transaction`。
2. `dwc_ddrctl_mss_env` 把 AXI monitor 的 analysis port 接到 `m_axi_read_hash_sb[jj].m_stimulus_ap`。
3. Scoreboard 收到 transaction 后先处理 `rdwr_ordered_en`、同 port/跨 port 地址冲突、response 到达顺序等问题，确保按 controller 应处理的顺序更新 expected memory。
4. 对 write transaction，按 AXI burst 逐 byte 展开地址；只有 `WSTRB` 有效、`BRESP` 合法、非 poison/error 场景时，才执行 `m_sb_mem_byte[channel][byte_addr] = WDATA_byte`。
5. 对 read transaction，同样按 burst 逐 byte 展开地址；如果该 byte address 之前写过，就用 `RDATA_byte` 和 `m_sb_mem_byte[channel][byte_addr]` 比较。
6. 如果读到未写过地址，默认只统计 unknown/unwritten byte，不做 mismatch；如果开启 strict 模式则可报错。
7. ECC aliasing、OCPAR/OCECC、SLVERR/EXOKAY、exclusive access、WRAP burst、unaligned burst 都有相应 skip 或特殊处理。

一句话面试版：

> AXI read-hash scoreboard 复用 AXI VIP monitor 采到的 transaction。写路径按 burst 和 `WSTRB` 展开到 byte 地址，把成功写入的数据存进以 byte address 为 key 的 associative array；读路径再按同样的地址展开，把 `RDATA` 和 expected memory image 逐 byte 比较，因此它检查的是从 AXI 写入到 AXI 读回的 end-to-end data integrity。

---

#### 第三层 C：`dwc_ddrctl_reg_utilities`（RAL + APB adapter）

RAL（Register Abstraction Layer）是 UVM 提供的寄存器访问框架。本项目中：

```
dwc_ddrctl_reg_utilities
├── uvm_reg_block（RAL 寄存器模型，由 ral_pkg 生成）
│     ├── REGB_DDRC_CH0（控制器核心寄存器）
│     ├── REGB_ARB_PORT0/1/2/3（AXI Port 仲裁寄存器）
│     ├── REGB_ADDR_MAP0（地址映射寄存器）
│     └── REGB_FREQ0_CH0（频率相关寄存器）
│
└── dwc_ddrctl_reg2apb_adapter（RAL → APB 总线适配器）
      继承 uvm_reg_adapter
      reg2bus()：把 uvm_reg_bus_op 转成 svt_apb_transaction
      bus2reg()：把 svt_apb_transaction 转回 uvm_reg_bus_op
```

工作流程：
```
test 调用 reg_model.REGB_DDRC_CH0.MSTR.write(value)
  → uvm_reg_adapter.reg2bus()
  → 生成 svt_apb_transaction
  → APB VIP master sequencer 发出
  → APB bus 上出现 PADDR/PWDATA/PSEL/PENABLE
  → APB monitor 观察到 transaction
  → reg_predictor 更新 RAL mirror
```

---

#### 第四层：`dwc_ddrctl_mss_vseqr`（虚拟 Sequencer）

虚拟 sequencer 不驱动任何接口，只持有各 agent 的 sequencer 句柄：

```systemverilog
class dwc_ddrctl_mss_vseqr extends uvm_sequencer;
  svt_apb_master_sequencer    m_apb_seqr;        // APB VIP master seqr
  dwc_ddrctl_axi_master_seqr  m_axi_seqr[];      // AXI Master seqr（每 port）
  dwc_ddrctl_hif_sequencer    m_hif_seqr[];       // HIF seqr（每 channel）
  dwc_ddrctl_isr_sequencer    m_isr_seqr;         // ISR seqr
  ...
endclass
```

虚拟序列（`dwc_ddrctl_mss_vseq_base`）在 `m_mss_vseqr` 上运行，同时协调：
1. APB 配置序列（写 DDR controller/PHY 寄存器）
2. AXI 流量序列（发 DDR memory 读写请求）
3. ISR/Low-power 响应序列

---

#### 数据流总结：一个 AXI Write 经过的所有层

```
test (virtual sequence)
  │
  ├─ APB 路径（配置）
  │   dwc_ddrctl_mss_vseqr.m_apb_seqr
  │   → svt_apb_master_agent.driver
  │   → APB bus → DUT APB port
  │   → DUT 内部 CSR 寄存器更新
  │
  └─ AXI 路径（数据）
      dwc_ddrctl_mss_vseqr.m_axi_seqr[port]
        (实际类型 dwc_ddrctl_axi_master_seqr，继承 svt_axi_master_sequencer)
      → svt_axi_master_agent.driver
      → AXI bus AW+W+B → DUT AXI port
      → DUT 内部：AXI port → XPI → ARB → HIF
                  ↓
              dwc_ddrctl_hif_agent (monitor)
                  ↓
              DDRC scheduler
              ACT → WR → PRE/REF
                  ↓
              DFI interface
              dwc_ddrctl_dfi_env (monitor)
                  ↓
              PHY → DDR4 memory model
              dwc_ddrctl_svt_ddr4_agent (monitor/checker)

  检查链：
  AXI monitor → dwc_ddrctl_axi_port_mon_cb → axi_read_hash_sb (write side)
  HIF monitor → dwc_ddrctl_hif_agent         → axi_hif_top_sb
  DFI monitor → dwc_ddrctl_dfi_env           → hif_dfi_sb_env
```

---

## 验证环境架构

```text
UVM test / virtual sequence
  |
  |-- APB VIP master sequence
  |     |-- WRITE controller/PHY CSR
  |     |-- READ status register
  |     `-- polling init done / training done
  |
  |-- AXI VIP master sequence
  |     |-- WRITE burst: AW + W + B
  |     `-- READ  burst: AR + R
  |
  `-- monitors / scoreboards
        |-- APB monitor / RAL predictor
        |-- AXI protocol checker
        |-- AXI read-hash scoreboard
        |-- AXI-HIF scoreboard
        |-- HIF-DFI scoreboard
        `-- DDR/DFI VIP checker

DUT path:
  APB CSR config
  AXI memory request
    -> AXI port
    -> ARB / HIF
    -> DDRC scheduler
    -> DFI
    -> PHY
    -> DDR4 memory model
```

## APB VIP 技术实现

APB VIP 的角色类似软件驱动或 firmware：它不搬大数据，而是配置 DDR controller 的控制寄存器。

### APB VIP 发什么

APB write sequence 的本质是创建一个 APB transaction：

```systemverilog
`uvm_do_with(req, {
  xact_type == svt_apb_transaction::WRITE;
  address   == local::address;
  data      == local::data;
})
```

APB read sequence 类似：

```systemverilog
`uvm_do_with(req, {
  xact_type == svt_apb_transaction::READ;
  address   == local::address;
})
```

VIP driver 会把 transaction 转成 APB pin-level 信号：

| APB 信号 | 含义 |
| --- | --- |
| `PADDR` | register address |
| `PWDATA` | write data |
| `PWRITE` | 1 表示 write，0 表示 read |
| `PSEL` / `PENABLE` | APB setup/access phase 控制 |
| `PREADY` | slave ready |
| `PRDATA` | read data |
| `PSLVERR` | APB error response |

### APB 配什么

APB 配置的对象不是 DDR memory data，而是 controller/PHY 的 CSR：

| 配置类别 | 说明 |
| --- | --- |
| DDR 模式 | DDR4/DDR5/LPDDR 选择、rank、bus width、device density 等 |
| Timing | `tRCD`、`tRP`、`tRAS`、`tFAW`、`tRFC`、read/write turn-around 等 |
| Address map | AXI/system address 到 rank/bank group/bank/row/column 的映射 |
| Port/QoS | AXI port enable、priority、urgent、HPR/LPR 等 |
| Refresh/low power | auto-refresh、self-refresh、power-down 等 |
| DFI/PHY init | 触发 PHY training/init，并读取 init/training done 状态 |

### APB 检查什么

APB 相关检查主要分三层：

1. **APB VIP protocol checker**：检查 APB transfer 时序、握手、`PSLVERR`。
2. **RAL predictor / APB subscriber**：通过 APB monitor 看到真实 bus transaction，更新寄存器 mirror。
3. **test sequence 语义检查**：例如写完配置后 readback，或者 polling status 直到 init done。

## AXI4 VIP 技术实现

AXI VIP 的角色是 memory traffic generator。它发的是 DDR memory 地址空间的读写请求，不是 APB register 访问。

### AXI VIP 发什么

AXI write burst：

```text
AW channel: AWADDR, AWLEN, AWSIZE, AWBURST, AWID
W  channel: WDATA, WSTRB, WLAST
B  channel: BRESP
```

AXI read burst：

```text
AR channel: ARADDR, ARLEN, ARSIZE, ARBURST, ARID
R  channel: RDATA, RRESP, RLAST
```

典型 directed sequence 会显式设置 transaction 字段：

```systemverilog
l_wr_tran.xact_type    = svt_axi_transaction::WRITE;
l_wr_tran.addr         = l_bv_full_axi_addr;
l_wr_tran.burst_type   = svt_axi_transaction::INCR;
l_wr_tran.burst_length = l_n_axi_bl;
l_wr_tran.data[k]      = expected_pattern;
l_wr_tran.wstrb[k]     = all_byte_lanes_enabled;

execute_xact_and_proc_resp(l_wr_tran, wait_for_response);
```

### AXI 流量场景

| 场景 | 目的 |
| --- | --- |
| write then read same address | 最基本的数据完整性检查 |
| multi-port traffic | 验证 controller 多端口仲裁 |
| random address / burst | 覆盖地址映射、bank/page 行为 |
| QoS / priority | 验证 urgent、HPR/LPR、port priority |
| streaming traffic | 压力测试吞吐、队列、backpressure |
| same bank/page targeted traffic | 定向打 page hit、page miss、bank conflict |

## DDR4 协议在 controller 后面发生什么

AXI 看到的是线性 memory address，但 DDR4 实际组织不是平坦数组。controller 需要把地址拆成：

```text
AXI byte address
  -> system address
  -> rank / bank group / bank / row / column
```

### DDR4 基本命令

| 命令 | 作用 |
| --- | --- |
| `ACT` | activate，打开某个 bank 的某一行 row |
| `RD` | read，从已打开 row 的 column 读数据 |
| `WR` | write，向已打开 row 的 column 写数据 |
| `PRE` | precharge，关闭当前打开 row |
| `REF` | refresh，周期性刷新 DRAM cell |
| `MRS` | mode register set，配置 DRAM 内部模式 |

### Page hit / miss

如果目标 bank 的目标 row 已经打开：

```text
page hit:
  RD/WR column
```

如果目标 bank 打开的不是目标 row：

```text
page miss / bank conflict:
  PRE old row
  wait tRP
  ACT new row
  wait tRCD
  RD/WR column
```

如果 bank 当前没有打开 row：

```text
closed page:
  ACT row
  wait tRCD
  RD/WR column
```

### Timing 约束

controller 必须满足 DDR4 timing，否则即使 AXI protocol 完全正确，DDR4 侧仍然是错的。

| Timing | 含义 |
| --- | --- |
| `tRCD` | ACT 到 RD/WR 的最小间隔 |
| `tRP` | PRE 到下一次 ACT 的最小间隔 |
| `tRAS` | ACT 后 row 必须保持打开的最小时间 |
| `tFAW` | rolling window 内 ACT 数量限制 |
| `tRFC` | refresh 占用时间 |
| `tCCD` | column command 到 column command 的间隔 |
| read/write turn-around | 读写方向切换需要间隔，避免 DQ bus 冲突 |

## 为什么这不是“只验证 APB/AXI”

APB/AXI 只是入口协议。真正的目标是验证 DDR controller 的内部行为：

| 如果只验证 APB/AXI | DDR controller 验证还要看 |
| --- | --- |
| APB write/read 是否握手成功 | 寄存器配置是否真正让 controller 进入正确 DDR4 模式 |
| AXI AW/W/B/AR/R 是否合法 | AXI 请求是否被正确转成 HIF/DDR 命令 |
| AXI response 是否 OKAY | 数据是否写到正确 rank/bank/row/column |
| AXI read 是否返回数据 | 读回数据是否等于之前写入 pattern |
| AXI burst 是否满足协议 | DDR4 timing、refresh、page hit/miss 调度是否正确 |

所以一个 AXI transaction 全部 response OKAY，仍然可能因为地址映射、数据返回、DDR timing 或内部调度错误而 fail。

## Scoreboard 和 Checker 链路

### 1. APB monitor / register predictor

APB monitor 观察真实 APB transaction，并更新 RAL mirror 或 subscriber 状态。它能抓：

- test 以为写了寄存器，但真实 bus 没写到。
- readback 值和 expected 不一致。
- APB error response。
- init/training status 没有按预期变化。

### 2. AXI VIP checker

AXI VIP checker 负责入口协议：

- `VALID/READY` handshake 是否符合 AXI。
- burst length、burst size、address alignment 是否合法。
- `WLAST/RLAST` 是否正确。
- `BRESP/RRESP` 是否正常。
- 同 ID ordering、outstanding 行为是否符合规则。

### 3. Read-hash scoreboard

read-hash scoreboard 负责 end-to-end data integrity：

```text
AXI write observed:
  record expected memory bytes

AXI read observed:
  compare RDATA bytes against expected memory bytes
```

如果 write path、address mapping、data mask、read path 任意一层出错，最终都可能表现为 read data mismatch。

### 4. AXI-HIF scoreboard

AXI-HIF scoreboard 检查上层 AXI 请求是否正确转换成 controller 内部 HIF 请求：

- AXI address 是否变成正确 HIF address。
- read/write 方向是否正确。
- burst length / data beat 是否正确。
- port、priority、QoS 信息是否合理传递。

### 5. HIF-DFI scoreboard

HIF-DFI scoreboard 更接近 DDR4 协议侧：

- HIF RD/WR 是否调度成正确 DFI command。
- bank/row/column/rank 是否符合预测。
- page hit/page miss 行为是否合理。
- refresh、precharge、activate 时机是否满足配置。
- read/write data beat 是否和 DFI/DDR 侧一致。

### 6. Postprocess

`runtest.pm` 在仿真结束后做最终归纳：

1. 调 `checklog.pl` 扫 `test.log` / `compile.log`。
2. 如果没有 error，再检查完成字符串：`COMPLETED - done with Env`。
3. 如果有 timeout、scoreboard mismatch、UVM fatal/error，则生成 `FAILED`。
4. 如果所有检查通过，写 `PASSED` 和 `test.json`。

## 一次典型测试流程

```text
1. test_cfg randomize / select DDR4 config
2. mss_initialize_subsystem
3. APB VIP writes controller/PHY registers
4. APB VIP polls status until init/training done
5. AXI VIP starts write bursts on one or more ports
6. controller maps AXI address to rank/bank/row/column
7. controller schedules ACT/RD/WR/PRE/REF through DFI/PHY
8. AXI VIP starts read bursts from same/related addresses
9. read-hash compares expected vs actual RDATA
10. AXI-HIF and HIF-DFI scoreboard check internal conversion
11. postprocess scans log and emits PASSED/FAILED
```

## Debug 思路

| 失败现象 | 优先看哪里 | 可能原因 |
| --- | --- | --- |
| APB read/write fail | APB VIP log、RAL mirror、APB waveform | register address wrong、PREADY/PSLVERR、config sequence 顺序错 |
| init done 一直不来 | status polling、PHY/DFI init log | PHY training 未完成、timing/config 不合法、reset/clock 问题 |
| AXI protocol error | AXI VIP checker、AW/W/B/AR/R waveform | burst 参数非法、ID/order、`WLAST/RLAST`、ready/valid 规则问题 |
| AXI response OKAY 但数据错 | read-hash scoreboard、AXI monitor、memory model | 地址映射错、WSTRB/mask 错、read path 错、data beat 顺序错 |
| AXI-HIF mismatch | AXI-HIF scoreboard、HIF monitor | AXI 到 HIF 的地址/长度/方向/port 转换错 |
| HIF-DFI mismatch | HIF-DFI scoreboard、DFI monitor | DDR command 调度错、timing 违反、page/bank 行为错误 |
| postprocess failed | `test.log`、`compile.log`、`test.error` | UVM error/fatal、timeout、缺少 `COMPLETED - done with Env` |

## 面试回答要点

中文：

这个项目我会从 APB 和 AXI 两条路径讲。APB VIP 是控制路径，用来配置 DDR controller 和 PHY 的寄存器，包括 DDR4 模式、timing、地址映射、端口和 DFI/PHY 初始化。配置完成后通过 APB read polling 状态，确认 init/training done。然后 AXI4 VIP 作为数据路径，在一个或多个 AXI port 上发 write/read burst，通常先写入 pattern 再读回。

关键点是，这不是单纯验证 APB/AXI protocol。APB/AXI 只是 stimulus 入口，真正被验证的是 DDR controller 能否把 AXI memory transaction 正确映射到 DDR4 的 rank、bank group、bank、row、column，并正确调度 ACT、RD、WR、PRE、REF 等命令，同时满足 DDR4 timing 和 refresh 要求。结果检查也分层：APB/AXI VIP checker 保证入口协议合法，read-hash scoreboard 检查数据完整性，AXI-HIF scoreboard 检查上层请求到内部 HIF 的转换，HIF-DFI scoreboard 检查 DDR 命令和 timing，最后 postprocess 扫 log 并根据 completed 字符串给出 PASS/FAIL。

English:

In this DDR controller verification project, APB and AXI VIPs are used as the main stimulus entry points. The APB VIP programs the controller and PHY registers, such as DDR mode, timing parameters, address mapping, port configuration, refresh settings, and DFI/PHY initialization. After polling the status registers and confirming that initialization and training are complete, the AXI4 VIP generates memory traffic, typically write bursts followed by read bursts to the DDR memory address space.

The verification target is not just APB or AXI protocol compliance. Those protocols are only the front-door interfaces. The real goal is to verify that the DDR controller correctly maps AXI addresses to rank, bank group, bank, row and column, schedules DDR4 commands such as ACT, READ, WRITE, PRECHARGE and REFRESH, meets DDR4 timing constraints, and preserves data integrity. The checking is multi-layered: APB and AXI VIP checkers validate bus transactions, read-hash scoreboards compare written and read data, AXI-to-HIF and HIF-to-DFI scoreboards check internal conversion and DDR command behavior, and the postprocess script scans logs and the completion message to generate the final pass/fail result.

## 常见追问

| 追问 | 回答重点 |
| --- | --- |
| 你自己写 DDR4 driver 吗？ | 普通测试不写 DDR4 pin-level driver；使用 APB 配置和 AXI traffic，controller/PHY/VIP 处理 DDR4 侧。 |
| 那和验证 APB/AXI 有什么区别？ | APB/AXI 是入口，目标是 controller 后面的地址映射、DDR 命令调度、timing、refresh 和数据完整性。 |
| 为什么 AXI response OKAY 还可能 fail？ | OKAY 只说明 AXI 入口响应正常，不保证数据写到正确 DDR 地址或 DDR timing 正确。 |
| read-hash scoreboard 抓什么？ | 抓 end-to-end data integrity，比较写入 pattern 和读回 RDATA。 |
| HIF-DFI scoreboard 抓什么？ | 抓 controller 内部请求到 DDR/DFI 命令的转换和时序行为。 |
| APB polling 为什么重要？ | DDR/PHY 没初始化完成前，AXI memory traffic 没有稳定落点，可能产生无意义或非法行为。 |

## 可直接放简历的 bullets

- Used APB VIP as the CSR programming path to configure DDR4 controller/PHY registers, including timing, address mapping, port settings, refresh and DFI/PHY initialization.
- Used AXI4 VIP master sequences to generate directed and random DDR memory traffic, including write-then-read data integrity scenarios across AXI ports.
- Analyzed the verification path from AXI memory transactions through AXI port, HIF, DDRC scheduler, DFI, PHY and DDR4 memory model.
- Explained multi-layer checking with APB/AXI protocol checkers, read-hash scoreboard, AXI-HIF scoreboard, HIF-DFI scoreboard, DDR/DFI checkers and regression postprocess.

---

## Q: VIP 具体结构和怎么使用的

### VIP 整体架构

本工程使用 Synopsys DesignWare SVT VIP，针对 DWC_ddrctl_ddr54 做了定制封装，基于 UVM 框架。

```
ddr_uvm_pve_tb_top（顶层模块）
  └── dwc_ddrctl_pve_base_test（测试基类）
        └── dwc_ddrctl_mss_env（MSS 顶层 env）
              ├── dwc_ddrctl_vip_env（VIP 包装层）
              │     ├── svt_apb_system_env        ← APB VIP Master Env
              │     ├── svt_axi_system_env         ← AXI VIP System Env
              │     └── dwc_ddrctl_dfi_env         ← DFI Monitor Env
              ├── dwc_ddrctl_reg_utilities          ← RAL 寄存器模型
              └── dwc_ddrctl_mss_vseqr              ← 虚拟 Sequencer
```

### VIP 目录结构

| 目录 | 作用 |
| --- | --- |
| `scratch/pve/…/src/sverilog/vcs/` | 第三方 SVT VIP 库（只读，预编译），含 `svt_apb_*.sv`、`svt_axi_*.sv` |
| `testbench/modules/` | 顶层 SV 模块：例化 interface、连接 DUT、启动 UVM |
| `testbench/interfaces/` | SV Interface（物理信号桥接） |
| `testbench/cfg/` | 用户定制 VIP 配置对象（继承 `svt_*_configuration`） |
| `testbench/env/` | UVM Environment 层（`vip_env`、`mss_env`、`dfi_env` 等） |
| `testbench/seq_lib/` | Sequence 激励库（APB 读写序列、AXI 主机序列） |
| `testbench/env/ral/` | RAL 寄存器模型包 |
| `testbench/env/sb/` | 记分板（AXI↔HIF、HIF↔DFI） |
| `testbench/tests/` | 测试用例（继承 `dwc_ddrctl_pve_base_test`） |

### 顶层模块职责（`ddr_uvm_pve_tb_top`）

1. 例化所有 SV interface
2. 通过 `uvm_config_db::set()` 将 interface 传递给 UVM 环境
3. 调用 `run_test()`（测试名由命令行 `+UVM_TESTNAME` 传入）

### VIP 包装层职责（`dwc_ddrctl_vip_env`）

统一管理所有协议 VIP，在 `build_phase` 里：
- 从 `uvm_config_db` 取出 APB/AXI 配置对象
- `type_id::create()` 创建 `svt_apb_system_env`、`svt_axi_system_env`
- 通过 `uvm_config_db::set()` 将 `svt_*_configuration` 注入 VIP 内部

### Sequence 使用方式（APB 写为例）

```systemverilog
// 1. 继承 SVT base sequence
class dwc_ddrctl_apb_master_wr_sequence extends svt_apb_master_base_sequence;
  rand int address;
  rand int data;
  virtual task body();
    `uvm_do_with(req, {
      xact_type == svt_apb_transaction::WRITE;
      address   == local::address;
      data      == local::data;
    })
  endtask
endclass

// 2. 在 vseq 里创建并启动
apb_wr_seq.address = 32'h0000_0100;
apb_wr_seq.data    = 32'hDEAD_BEEF;
apb_wr_seq.start(m_mss_env.m_vip_env.m_svt_apb_system_env.master.sequencer);
```

### RAL 寄存器操作方式

```
test 调用 reg_model.REGB_DDRC_CH0.MSTR.write(value)
  → dwc_ddrctl_reg2apb_adapter.reg2bus()
  → 生成 svt_apb_transaction
  → APB VIP master sequencer 发出
  → APB monitor 观察 → reg_predictor 更新 RAL mirror
```

### 三大 VIP 对比

| 维度 | APB VIP | AXI VIP | DFI VIP |
| --- | --- | --- | --- |
| 角色 | 配置寄存器 | 数据传输主体 | 监控 DDR PHY 接口 |
| SVT 类 | `svt_apb_system_env` | `svt_axi_system_env` | `svt_dfi_*` |
| 配置类 | `dwc_ddrctl_apb_cfg` | `dwc_ddrctl_axi_system_cfg` | `dwc_ddrctl_dfi_cfg` |
| 序列基类 | `svt_apb_master_base_sequence` | `svt_axi_master_base_sequence` | 被动监控，无序列 |

### 运行一个测试

```bash
# 编译
vcs -sverilog -f compile.f

# 运行，指定测试名
./simv +UVM_TESTNAME=test_dwc_ddrctl_axi_basic +UVM_VERBOSITY=UVM_MEDIUM
```

新增测试：继承 `dwc_ddrctl_pve_base_test`，重写 `run_phase()`，在 `dwc_ddrctl_pve_test_pkg.sv` 里 `include` 即可。

---

## Q: Config 需要配置什么

工程有 5 类 Config 对象形成层次：

```
dwc_ddrctl_mss_cfg（顶层总配置）
├── dwc_ddrctl_apb_cfg
├── dwc_ddrctl_axi_system_cfg
│   └── dwc_ddrctl_axi_master_cfg[]（每端口）
├── dwc_ddrctl_dfi_cfg
└── dwc_ddrctl_mem_sys_config
    └── dwc_ddrctl_svt_ddr4_config
```

### APB Config（`dwc_ddrctl_apb_cfg`）

| 配置项 | 说明 |
| --- | --- |
| `master_cfg.is_active = 1` | Master 主动驱动总线 |
| `slave_cfg[i].is_active = 0` | Slave 被动（DUT 充当 slave） |
| `paddr_width = PADDR_WIDTH_32` | 地址线宽度 |
| `pdata_width = PDATA_WIDTH_32` | 数据线宽度 |
| `apb4_enable = DDRCTL_APB4_EN` | 是否启用 APB4（PPROT/PSTRB） |
| `slave_addr_ranges[i].start/end_addr` | 每个 APB slave 地址范围 |
| `slave_addr_ranges[i].slave_id` | slave 编号，用于地址路由 |
| slave 数量 | `NUM_APB_SLVS - NUM_PHY_INST`（是否含 PHY APB 由宏决定） |

### AXI System Config（`dwc_ddrctl_axi_system_cfg`）

系统级：

| 配置项 | 说明 |
| --- | --- |
| `num_masters` | `UMCTL2_A_NPORTS`（从 DUT 参数读取） |
| `num_slaves = 0` | 无 AXI slave，直连 DUT |
| `common_clock_mode = 0` | 每端口独立时钟 |
| watchdog timeout 全设 0 | 关闭看门狗，避免误报 |

每端口级（`master_cfg[i]`，全部从 DUT 参数 `m_mctl.get_val()` 读取）：

| 配置项 | 来源 |
| --- | --- |
| `addr_width` | `UMCTL2_A_ADDRW` |
| `data_width` | `UMCTL2_PORT_DW_i`（每端口可不同） |
| `id_width` | `UMCTL2_A_IDW` |
| `axi_interface_type` | AXI4 或 AXI3（由 `UMCTL2_A_TYPE_i` 决定） |
| `aruser/awuser/buser/ruser/wuser_enable = 1` | 启用 user 信号（Poison/Parity/QoS） |
| `addr_user_width` | `UMCTL2_AXI_USER_WIDTH + AXI_QOSW + 2` |
| `exclusive_access_enable` | 由 `UMCTL2_EXCL_ACCESS` 决定 |
| `locked_access_enable = 0` | 不支持 locked |
| `write_data_interleave_depth = 1` | 不支持写数据交织 |
| `num_outstanding_xact` | 按端口数自动缩放（≤5 用满；>10 用 1/4） |
| 空闲值 | OCCAP 未开时随机，开时用 LOW |
| 覆盖率开关 | toggle/state/transaction/protocol_checks 全开 |
| `use_tlm_generic_payload = 1` | 支持 TLM 通用负载 sequencer |
| `wysiwyg_enable = 1` | scoreboard 需要 |

> **关键原则**：所有涉及 DUT 结构的参数都通过 `dwc_ddrctl_cc::get_instance()` 动态读取，不硬编码，使同一套 TB 可适配不同 DUT 配置。

### DFI Config（`dwc_ddrctl_dfi_cfg`）

| 配置项 | 说明 |
| --- | --- |
| `m_b_enable_dfi_mon = 1` | 启用 DFI 协议监控 |
| `m_b_enable_dfi_mon_check_retry = 1` | 启用 CRC retry 黑盒检查 |
| `m_n_freq_ratio` | 频率比（1:1 / 1:2 / 1:4） |
| `m_b_bypass_initialization` | 是否跳过 DRAM 初始化 |
| `m_dfi_agent_configuration[]` | 每个 DFI 通道的 SVT agent 配置 |
| `m_n_dfi_t_cmd_lat[]` | 各通道命令延迟（用于 HIF→DFI scoreboard） |
| `m_n_check_retry_win_adj_clks` | retry 窗口裕量（DDRC 时钟数） |

### SDRAM 内存模型 Config（`dwc_ddrctl_mem_sys_config`）

| 配置项 | 说明 |
| --- | --- |
| `m_b_bypass_initialization` | 跳过 DRAM 初始化 |
| `m_b_use_short_init` | 短初始化序列（加速仿真） |
| `m_b_random_init_values` | 内存初始值随机还是全 0 |
| `m_b_address_mirror_en` | DDR4 地址镜像（RDIMM/LRDIMM） |
| `m_b_phy_training_en` | PHY training 是否使能 |
| `m_b_vip_coverage_en` | 所有器件 VIP 覆盖率开关 |

### DDR4 协议 Config（`dwc_ddrctl_svt_ddr4_config`）

继承 `svt_ddr_configuration`，用于 DDR 内存模型协议时序参数：

| 配置项 | 值 |
| --- | --- |
| `protocol_kind` | `DDR4` |
| `skip_init = 0` | 不跳过初始化 |
| `enable_transaction_reporting = 1` | log 中显示 DDR 事务 |
| `enable_transaction_tracing = 1` | 单独文件记录事务 |
| `enable_memcore_xml_gen = 1` | Protocol Analyzer XML 输出 |
| `enable_3ds_tccd_selct_thru_mrs = 1` | 频率切换时从 MR6 读 tCCD_L |

### 配置流向

```
测试用例 (test)
  → 创建 + 随机化 dwc_ddrctl_mss_cfg
  → uvm_config_db::set() 向下传递
      ↓
dwc_ddrctl_vip_env::build_phase
  → uvm_config_db::get() 取出 APB/AXI 配置
  → uvm_config_db::set() 传给 SVT VIP 内部
      ↓
svt_apb_system_env / svt_axi_system_env
  → 用配置创建 Agent (Driver + Monitor + Sequencer)
```

---

## Q: mss_env 是什么

**MSS = Memory Sub-System（内存子系统）**

`dwc_ddrctl_mss_env` 是整个 UVM 验证环境的**根节点 env**，是 `uvm_test` 下面的第一层 `uvm_env`。

### 它的定位：把所有子系统组装在一起

```
dwc_ddrctl_mss_env
├── m_vip_env          ← 所有对外协议 VIP（APB / AXI / DFI）
├── m_mctl_env         ← DDR controller 内部监控（HIF agent、scoreboard）
├── m_mss_vseqr        ← 虚拟 sequencer（激励调度中枢）
├── m_reg_utilities    ← RAL 寄存器模型
├── m_addr_mgr         ← 地址管理器（AXI 地址约束）
├── m_phy_wrap         ← PHY 包装（PHY training 等）
├── m_clkrst_gen       ← 时钟/复位生成器
└── m_hif2dfi_sb_env   ← HIF→DFI 记分板
```

职责分工：
- `build_phase`：把所有子组件 `type_id::create()` 出来，把配置分发给各子组件
- `connect_phase`：把各组件之间的 TLM port、RAL adapter、vseqr 句柄接起来
- 比喻：test 是项目经理，mss_env 是工地总包

---

## Q: UVM 验证环境搭建流程（如何搭建）

### 第一步：物理连接层 `ddr_uvm_pve_tb_top`（SV module）

1. 例化所有 SV Interface（AXI、APB、DUT probe、ISR、PA 等）
2. 连接时钟：`assign axi_if.master_if[i].aclk = clkrst_if0.axi_clk_gated[i]`
3. 通过 `uvm_config_db::set()` 把 interface 注入 UVM 环境
4. 调用 `run_test()`

### 第二步：Test 层 `build_phase`

1. **Factory Override**：用定制类替换 SVT 默认类（无需改 VIP 源码）
   ```systemverilog
   set_type_override_by_type(svt_axi_system_configuration::get_type(),
                             dwc_ddrctl_axi_system_cfg::get_type());
   set_type_override_by_type(svt_axi_master_transaction::get_type(),
                             dwc_ddrctl_axi_master_transaction::get_type());
   set_type_override_by_type(svt_axi_master_sequencer::get_type(),
                             dwc_ddrctl_axi_master_seqr::get_type());
   ```
2. `create_test_config()` → 随机化配置对象
3. create mss_env，注入 test_cfg
4. 为 vseqr 设置 default_sequence（指定该 test 跑哪个 vseq）

### 第三步：MSS Env `build_phase`

1. 从 config_db 取出 test_cfg
2. 向下广播各子组件需要的配置（APB cfg → APB VIP env，AXI cfg → vip_env，addr_mgr → all AXI sequencer）
3. 按顺序 create 所有子组件：vseqr / addr_mgr / reg_utilities / mctl_env / **vip_env** / sb_env / phy_wrap / clkrst_gen

### 第四步：VIP Env `build_phase`

1. create `svt_apb_system_env`（内部自动创建 APB master agent）
2. 为每端口 create `dwc_ddrctl_axi_port_mon_cb`（AXI monitor callback 对象）
3. 将 AXI 端口配置注入后 create `svt_axi_system_env`（内部自动创建各 port 的 AXI master agent）

### 第五步：connect_phase 挂 Callback

```systemverilog
// APB：把 mon_cb 挂到 APB monitor
svt_callbacks#(svt_apb_master_monitor, svt_apb_master_monitor_callback)
  ::add(m_svt_apb_system_env.master.monitor, m_apb_master_mon_cb);

// AXI：把 mon_cb 挂到每个 port 的 AXI monitor
foreach(m_axi_port_mon_cb[jj])
  svt_callbacks#(svt_axi_port_monitor, svt_axi_port_monitor_callback)
    ::add(m_axi_master_env.master[jj].monitor, m_axi_port_mon_cb[jj]);
```

### 第六步：虚拟 Sequencer connect_phase

从各 agent 取出 sequencer 句柄赋给 vseqr：
```systemverilog
m_svt_apb_master_sequencer = m_vip_env.m_svt_apb_system_env.master.sequencer;
m_mctl_axi_master_seqr[i]  = m_vip_env.m_axi_master_env.master[i].sequencer;
```

### run_phase 流程

```
vseqr 上的 default_sequence 启动
  → m_mss_initialize_subsystem（APB 写寄存器 + polling init done）
  → foreach AXI port → fork 并行跑 write-read 序列
  → wait fork → 所有端口完成
  → 统计覆盖率 → report PASS/FAIL
```

---

## Q: Callback 用来做什么

### 问题背景

SVT VIP 的 monitor 是封闭黑盒，源码不能改。但用户需要在"monitor 观察到事务"这个时机做额外的事情。Callback 就是在 VIP monitor 的关键时间点"插入自己的代码"的标准扩展接口。

### APB Monitor Callback 做的事

`dwc_ddrctl_apb_master_mon_cb` 重写 `output_port_cov()`：

| 功能 | 说明 |
| --- | --- |
| 生成 `dwc_ddrctl_apb.log` | 每条 APB 事务 → 记录时间/地址/数据/寄存器名/字段名 |
| 生成 `dwc_ddrctl_init_seq.c` | 写事务 → 自动生成伪 C 初始化代码，给 firmware 工程师参考 |
| 更新 RAL mirror | 通知 RAL predictor 真实总线写了什么，保持 mirror 和 DUT 同步 |

### AXI Monitor Callback 做的事

`dwc_ddrctl_axi_port_mon_cb` 重写多个时序点方法：

| callback 方法 | 触发时机 | 做的事 |
| --- | --- | --- |
| `write_address_phase_started()` | AWVALID 拉高 | 触发 `m_ev_xact_write_cmd_started` 事件 |
| `read_address_phase_ended()` | ARVALID+ARREADY | outstanding 计数 +1，触发事件 |
| `transaction_ended()` | B/R 最后一拍 | outstanding 计数 -1，向 analysis port 发布完整事务 |

`transaction_ended()` 里向 scoreboard 发布事务是最关键的：
```
AXI read 完成
  → m_ap_axi_rdwr_order.write(item)
  → axi_read_hash_sb.write()
  → 比对 RDATA 和期望值 → PASS/FAIL
```

### 一句话总结

| Callback | 核心目的 |
| --- | --- |
| APB mon_cb | monitor 看到事务 → 记日志 + 更新 RAL mirror + 生成初始化 C 代码 |
| AXI port mon_cb | monitor 看到事务 → 触发同步事件 + 把事务推给 scoreboard |
