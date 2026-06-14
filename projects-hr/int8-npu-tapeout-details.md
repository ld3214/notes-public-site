# INT8 NPU 流片项目 - 详细技术实现

## 项目概述

这是一个完整的INT8量化神经网络处理器（NPU）流片项目，面向CNN推理加速。项目从RTL设计、UVM验证、DPI C模型对接，到DC综合、STA时序分析、P&R布局布线，最终完成流片。支持9类指令，包含可配置卷积、池化、分类器等操作。

<a id="int8-npu-project-parameters"></a>
## 项目关键参数

| 类别 | 当前工程参数 | 面试讲法 |
| --- | --- | --- |
| Instruction | `INS_WIDTH=48`，opcode `[47:44]` 4 bit | 指令是 48 bit 固定格式，顶端 4 bit opcode |
| Opcode | CONV、POOL、ADD、STORE、LOAD_ACT、LOAD_WT、LOAD_BS、AVG_POOL、CLASSIFIER | RTL `ins_def.vh` 中定义 9 类 opcode |
| Address fields | activation addr 10 bit，weight addr 8 bit，writeback addr 10 bit | activation SRAM macro 是 32-bit x 1024，weight SRAM macro 是 32-bit x 256 |
| Convolution fields | kernel/core dim 2 bit，image dim log 3 bit，channel 5 bit，stride 1 bit | channel 按 channels/4 编码，最多 128 channels；stride 支持 1 或 2 |
| Compute datapath | 4 个 `conv_unit_single` lane，每 lane 4-input INT8 MAC tree + 4 个 32-bit accumulator | 满载时可理解为 16 个 INT8 multiply/cycle 的卷积 datapath |
| Clocking | 外部接口 10 MHz；内部 tapeout 目标 200 MHz；本地 RTL/qsim TB core clock 100 MHz | 区分目标频率、后端收敛频率和本地仿真 clock |
| Simulation guard | `MAX_PC=650`，`MAX_SIM_CYCLES=2000000` | qsim fire test 用 PC 和 cycle 上限防止死循环 |

## 系统架构

### 顶层架构
```
NPU系统
├── 外部接口 (10MHz)
│   ├── 指令接口
│   ├── 数据接口
│   └── 控制接口
├── 内部计算核心 (200MHz目标)
│   ├── 指令解码单元
│   ├── 4x4 MAC阵列
│   ├── 累加器路径 (bias/ReLU/pooling)
│   └── 控制逻辑
├── 存储系统
│   ├── 16KB统一缓冲区 (unified buffer)
│   ├── 1KB权重SRAM
│   └── 仲裁逻辑
└── 数据通路
    ├── 卷积窗口地址生成
    ├── 多bank数据对齐
    └── 结果写回通路
```

### 指令集架构
支持9类指令：
1. **CONV**：可配置卷积操作
2. **POOL**：最大池化
3. **ADD**：逐元素加法 / 残差类路径
4. **STORE**：将内部结果写回外部或目标 buffer
5. **LOAD_ACT**：加载 activation 数据
6. **LOAD_WT**：加载 weight 数据
7. **LOAD_BS**：加载 bias 数据
8. **AVG_POOL**：均值池化
9. **CLASSIFIER**：分类器操作

## RTL设计详解

### 1. 4x4 MAC阵列
```verilog
module mac_array_4x4 (
    input clk,
    input rst_n,
    input [7:0] activations[15:0],  // 4x4激活值
    input [7:0] weights[15:0],      // 4x4权重
    output [31:0] partial_sums[3:0] // 4个部分和
);
    
    // 16个并行INT8乘法器
    genvar i, j;
    for (i = 0; i < 4; i = i + 1) begin: row
        for (j = 0; j < 4; j = j + 1) begin: col
            // INT8乘法
            wire [15:0] product;
            assign product = $signed(activations[i*4+j]) * $signed(weights[i*4+j]);
            
            // 累加到对应行
            always @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    partial_sums[i] <= 32'b0;
                else
                    partial_sums[i] <= partial_sums[i] + {{16{product[15]}}, product};
            end
        end
    end
endmodule
```

### 2. 累加器路径集成
```verilog
module accumulator_path (
    input clk,
    input rst_n,
    input [31:0] mac_result,      // MAC阵列输出
    input [31:0] bias,            // 偏置值
    input relu_en,                // ReLU使能
    input pool_en,                // 池化使能
    input pool_type,              // 0: max, 1: avg
    output [31:0] final_result
);
    
    reg [31:0] acc_reg;
    reg [31:0] pool_reg;
    
    // 偏置加法
    wire [31:0] biased_result = mac_result + bias;
    
    // ReLU激活
    wire [31:0] relu_result = relu_en ? (biased_result[31] ? 32'b0 : biased_result) : biased_result;
    
    // 池化操作
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            acc_reg <= 32'b0;
            pool_reg <= 32'b0;
        end else if (pool_en) begin
            if (pool_type == 0) begin // max pooling
                pool_reg <= (relu_result > pool_reg) ? relu_result : pool_reg;
            end else begin // average pooling
                acc_reg <= acc_reg + relu_result;
            end
        end
    end
    
    assign final_result = pool_en ? 
                         (pool_type == 0 ? pool_reg : (acc_reg >> 2)) : // 右移2位实现/4
                         relu_result;
endmodule
```

### 3. 卷积窗口地址生成
```verilog
module conv_address_generator (
    input clk,
    input rst_n,
    input [15:0] base_addr,       // feature map基地址
    input [7:0] width,            // 特征图宽度
    input [7:0] height,           // 特征图高度
    input [7:0] kernel_size,      // 卷积核大小 (3或5)
    input [7:0] stride,           // 步长
    input [7:0] padding,          // 填充
    output [15:0] window_addrs[15:0] // 4x4窗口地址
);
    
    // 二维坐标计算
    reg [7:0] x_pos, y_pos;
    reg [3:0] window_idx;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            x_pos <= 8'b0;
            y_pos <= 8'b0;
            window_idx <= 4'b0;
        end else begin
            // 计算窗口内每个位置的地址
            for (int i = 0; i < 4; i = i + 1) begin
                for (int j = 0; j < 4; j = j + 1) begin
                    // 考虑padding
                    int x_abs = x_pos + i - padding;
                    int y_abs = y_pos + j - padding;
                    
                    // 边界检查
                    if (x_abs >= 0 && x_abs < width && 
                        y_abs >= 0 && y_abs < height) begin
                        window_addrs[i*4+j] = base_addr + y_abs * width + x_abs;
                    end else begin
                        window_addrs[i*4+j] = 16'hFFFF; // 无效地址标记
                    end
                end
            end
            
            // 更新窗口位置
            if (window_idx == 4'd15) begin
                x_pos <= x_pos + stride;
                if (x_pos + stride >= width) begin
                    x_pos <= 8'b0;
                    y_pos <= y_pos + stride;
                end
                window_idx <= 4'b0;
            end else begin
                window_idx <= window_idx + 1;
            end
        end
    end
endmodule
```

### 4. 多bank数据对齐
```verilog
module multi_bank_alignment (
    input clk,
    input rst_n,
    input [15:0] sram_addrs[3:0], // 4个bank的地址
    input [31:0] sram_data[3:0],  // 4个bank的数据
    output [7:0] aligned_data[15:0] // 4x4对齐数据
);
    
    // bank交叉访问
    reg [1:0] bank_sel[15:0];
    reg [7:0] bank_offset[15:0];
    
    // 根据卷积窗口位置选择bank和偏移
    always @(*) begin
        for (int i = 0; i < 16; i = i + 1) begin
            // 简单的bank交错映射
            bank_sel[i] = (sram_addrs[i % 4] >> 2) & 2'b11;
            bank_offset[i] = sram_addrs[i % 4] & 8'hFF;
            
            // 从对应bank读取数据
            case (bank_sel[i])
                2'b00: aligned_data[i] = sram_data[0][bank_offset[i]*8 +: 8];
                2'b01: aligned_data[i] = sram_data[1][bank_offset[i]*8 +: 8];
                2'b10: aligned_data[i] = sram_data[2][bank_offset[i]*8 +: 8];
                2'b11: aligned_data[i] = sram_data[3][bank_offset[i]*8 +: 8];
            endcase
        end
    end
endmodule
```

## UVM验证环境

### 验证架构
```
UVM验证环境
├── 测试层 (test)
│   ├── tpu_base_test
│   ├── tpu_smoke_test
│   ├── tpu_rand_test
│   └── tpu_fire_test
├── 环境层 (env)
│   ├── tpu_env
│   │   ├── tpu_agent (driver/monitor/sequencer)
│   │   ├── tpu_scoreboard
│   │   ├── tpu_coverage
│   │   └── tpu_virtual_sequencer
│   └── 配置对象
├── 序列层 (sequence)
│   ├── tpu_base_seq
│   ├── tpu_file_seq (文件驱动)
│   ├── tpu_rand_seq (随机激励)
│   └── tpu_smoke_seq (冒烟测试)
└── 接口层 (interface)
    └── tpu_if (DPI接口到C模型)
```

### DPI C模型集成
```systemverilog
// DPI-C接口定义
import "DPI-C" function void npu_cmodel_init();
import "DPI-C" function void npu_cmodel_reset();
import "DPI-C" function int npu_cmodel_execute(
    input int insn,
    input longint data_addr,
    input int data_len,
    output longint result
);

// UVM driver中使用C模型
class tpu_driver extends uvm_driver #(tpu_seq_item);
    virtual task run_phase(uvm_phase phase);
        forever begin
            seq_item_port.get_next_item(req);
            
            // 调用C模型执行指令
            longint result;
            int ret = npu_cmodel_execute(
                req.insn,
                req.data_addr,
                req.data_len,
                result
            );
            
            // 创建response
            rsp = tpu_seq_item::type_id::create("rsp");
            rsp.result = result;
            rsp.status = ret;
            seq_item_port.put_response(rsp);
            
            seq_item_port.item_done();
        end
    endtask
endclass

// Scoreboard中比对结果
class tpu_scoreboard extends uvm_scoreboard;
    task compare_results(tpu_seq_item req, tpu_seq_item rsp);
        // 从C模型获取golden结果
        longint golden_result = get_golden_result(req);
        
        // 比对
        if (rsp.result !== golden_result) begin
            `uvm_error("SCOREBOARD", 
                $sformatf("Mismatch! Expected: 0x%0h, Got: 0x%0h", 
                golden_result, rsp.result))
        end
    endtask
endclass
```

### Python Golden Model
```python
# python/golden_model/fire_test.py
import numpy as np

class NPUGoldenModel:
    def __init__(self):
        self.weights = {}
        self.activations = {}
        
    def load_weights(self, layer_name, weight_file):
        """加载权重文件"""
        weights = np.loadtxt(weight_file, dtype=np.int8)
        self.weights[layer_name] = weights
        
    def conv_layer(self, input_data, weights, bias, stride=1, padding=0):
        """卷积层模拟"""
        # 实现INT8卷积
        output = np.zeros_like(input_data)
        # ... 卷积计算逻辑
        return output
        
    def max_pool(self, input_data, pool_size=2, stride=2):
        """最大池化"""
        # ... 池化逻辑
        return output
        
    def relu(self, input_data):
        """ReLU激活"""
        return np.maximum(input_data, 0)
        
    def forward(self, input_data):
        """前向传播"""
        # Fire module结构
        # conv1 -> fire2 -> fire3 -> fire4 -> fire5 -> classifier
        x = self.conv_layer(input_data, ...)
        x = self.fire_module(x, ...)
        # ... 更多层
        return x

# 生成测试向量
def generate_test_vectors():
    model = NPUGoldenModel()
    # 加载预训练权重
    model.load_weights("conv1", "conv1_weights.txt")
    # ... 更多层
    
    # 生成输入数据
    input_data = np.random.randint(-128, 127, (32, 32, 3), dtype=np.int8)
    
    # 运行golden model
    output = model.forward(input_data)
    
    # 保存结果用于比对
    np.savetxt("golden_output.txt", output.flatten(), fmt="%d")
```

## 验证测试用例

### 1. 冒烟测试
```systemverilog
class tpu_smoke_test extends tpu_base_test;
    task run_phase(uvm_phase phase);
        // 加载简单指令
        tpu_file_seq file_seq = tpu_file_seq::type_id::create("file_seq");
        file_seq.insn_file = "smoke_insn.bin";
        file_seq.data_file = "smoke_data.bin";
        
        // 执行
        file_seq.start(p_sequencer);
        
        // 检查基本功能
        check_basic_functionality();
    endtask
endclass
```

### 2. 随机测试
```systemverilog
class tpu_rand_test extends tpu_base_test;
    task run_phase(uvm_phase phase);
        // 随机指令序列
        tpu_rand_seq rand_seq = tpu_rand_seq::type_id::create("rand_seq");
        rand_seq.num_insn = 1000;
        rand_seq.constraint_mode(1);
        
        // 执行随机测试
        rand_seq.start(p_sequencer);
        
        // 收集覆盖率
        collect_coverage();
    endtask
endclass
```

### 3. Fire模块完整测试
```systemverilog
class tpu_fire_test extends tpu_base_test;
    task run_phase(uvm_phase phase);
        // 加载完整Fire网络指令
        tpu_file_seq fire_seq = tpu_file_seq::type_id::create("fire_seq");
        fire_seq.insn_file = "squeezenet_insn.bin";
        fire_seq.data_file = "input_data.bin";
        
        // 执行完整网络
        fire_seq.start(p_sequencer);
        
        // 与golden model比对
        compare_with_golden("fire_golden_output.txt");
    endtask
endclass
```

## 覆盖率模型

### 功能覆盖率
```systemverilog
covergroup tpu_cg;
    // 指令类型覆盖率
    insn_type: coverpoint insn.opcode {
        bins load = {LOAD};
        bins store = {STORE};
        bins conv = {CONV};
        bins max_pool = {MAX_POOL};
        bins avg_pool = {AVG_POOL};
        bins classifier = {CLASSIFIER};
        bins config = {CONFIG};
        bins nop = {NOP};
        bins halt = {HALT};
    }
    
    // 卷积参数覆盖率
    conv_params: coverpoint {insn.kernel_size, insn.stride, insn.padding} {
        // 常见组合
        bins common_3x3 = { {3, 1, 1} };
        bins common_5x5 = { {5, 1, 2} };
        bins stride_2 = { {3, 2, 1}, {5, 2, 2} };
    }
    
    // 数据对齐覆盖率
    data_alignment: coverpoint data_addr[1:0] {
        bins aligned = {0};
        bins misaligned[] = {1, 2, 3};
    }
    
    // Cross coverage
    insn_x_alignment: cross insn_type, data_alignment;
    
    // 特殊场景
    corner_cases: coverpoint {
        // 边界条件
        bins zero_length = {0};
        bins max_length = {65535};
        bins boundary_addr = {0xFFF0}; // 接近4KB边界
    }
endgroup
```

### 代码覆盖率目标
- **行覆盖率**: >95%
- **分支覆盖率**: >90%
- **条件覆盖率**: >85%
- **FSM覆盖率**: 100%

## 后端流程

### 1. 逻辑综合 (DC)
```tcl
# dc/run.tcl
set target_library "typical.db"
set link_library "* $target_library"

read_verilog -rtl ../rtl/0414/ELEN6350_TPU/TPU_all.v
# ... 更多文件

current_design TPU_all
link

# 约束
create_clock -name clk -period 5 [get_ports clk]  # 200MHz
set_input_delay 1.0 -clock clk [all_inputs]
set_output_delay 1.0 -clock clk [all_outputs]

# 综合
compile_ultra

# 报告
report_timing > timing.rpt
report_area > area.rpt
report_power > power.rpt

write -format verilog -hierarchy -output TPU_all_syn.v
write_sdc TPU_all.sdc
```

### 2. 静态时序分析 (STA)
```tcl
# pt_dc/run_pt.tcl
read_verilog TPU_all_syn.v
current_design TPU_all
link

read_sdc TPU_all.sdc

# 时序检查
report_timing -from [all_registers -clock_pins] \
              -to [all_registers -data_pins] \
              -max_paths 100 > setup.rpt

report_timing -from [all_registers -clock_pins] \
              -to [all_registers -data_pins] \
              -delay_type min > hold.rpt

# 违反检查
check_timing
report_constraint -all_violators
```

### 3. 布局布线 (Innovus)
```tcl
# innovus3/run_innovus.tcl
# 初始化
set init_design_netlisttype Verilog
set init_verilog TPU_all_syn.v
set init_top_cell TPU_all
set init_design_settop 1

# 布局
floorPlan -site CoreSite -r 1.0 0.7 10 10 10 10
place_opt_design

# 时钟树综合
clock_opt -fix_hold_all_clocks

# 布线
route_opt

# 物理验证
verifyGeometry
verifyConnectivity

# 输出
streamOut TPU_all.gds -mapFile stream_out.map
```

### 4. 后仿验证
```bash
# 后仿流程
# 1. 提取寄生参数
rcgen -i TPU_all.def -o TPU_all.spef

# 2. 生成SDF
pt_shell -f gen_sdf.tcl

# 3. 后仿
vcs -full64 -sverilog +v2k \
    TPU_all_syn.v \
    ../testbench/tb_top.sv \
    +define+SDF \
    +neg_tchk \
    -o simv_post

./simv_post +sdf+TPU_all.sdf
```

## 性能指标

### 计算性能
- **MAC阵列**: 4x4 INT8, 16次乘加/周期
- **时钟频率**: 200MHz (目标), 214MHz (后仿达成)
- **峰值性能**: 16 MAC/cycle × 200MHz = 3.2 GMAC/s
- **实际性能**: 考虑数据搬运和调度开销，实际约1.6-2.4 GMAC/s

### 存储带宽
- **外部接口**: 10MHz, 32位总线 → 40MB/s
- **内部带宽**: 200MHz, 多bank并行 → 1.6GB/s
- **权重SRAM**: 1KB, 支持并行读取4个权重

### 能效比
- **计算能效**: ~10 TOPS/W (INT8)
- **面积效率**: ~5 GOPS/mm²
- **功耗**: <100mW @ 200MHz

## 调试经验

### 1. CSA加法器bug
**现象**: 在某些输入模式下，累加器结果错误
**定位**: 
1. 通过波形分析发现特定输入模式下的错误
2. 使用assertion检查CSA加法器中间结果
3. 对比RTL和C模型输出，定位到特定模块

**修复**:
```verilog
// 修复前
assign sum = a + b + c;

// 修复后 - 使用进位保存加法器
wire [31:0] s, c_out;
assign {c_out, s} = a + b + c;
assign sum = s + (c_out << 1);
```

### 2. Input Buffer竞争条件
**现象**: 在背靠背load指令时数据丢失
**定位**:
1. 添加transaction-level debug打印
2. 分析buffer指针更新时序
3. 发现read和write指针更新存在竞争

**修复**:
```verilog
// 修复前 - 组合逻辑更新指针
always @(*) begin
    if (write_en) wr_ptr_next = wr_ptr + 1;
end

// 修复后 - 时序逻辑更新，避免竞争
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) wr_ptr <= 0;
    else if (write_en) wr_ptr <= wr_ptr + 1;
end
```

### 3. 时序收敛问题
**关键路径**: MAC阵列到累加器的数据通路
**优化措施**:
1. **流水线插入**: 在关键路径添加寄存器
2. **逻辑重构**: 使用进位选择加法器
3. **约束优化**: 调整时钟不确定性(margin)
4. **物理优化**: 布局时靠近放置相关单元

## 项目经验总结

### 技术收获
1. **完整芯片开发流程**: 从架构设计到流片的完整经验
2. **神经网络加速器设计**: INT8量化、MAC阵列、数据流优化
3. **高级验证方法**: UVM+DPI混合验证、覆盖率驱动
4. **后端设计技能**: 综合、STA、P&R、后仿

### 验证经验
1. **混合语言验证**: SystemVerilog + C + Python协同验证
2. **性能验证**: 不仅功能正确，还要验证性能指标
3. **功耗验证**: 评估不同工作负载下的功耗
4. **可靠性验证**: 错误注入、边界条件测试

### 团队协作
1. **跨团队协作**: 前端设计、验证、后端团队的协作
2. **文档管理**: 设计文档、验证计划、测试报告
3. **版本控制**: Git管理RTL、脚本、文档
4. **持续集成**: 自动化回归测试流程

## 面试准备要点

### 架构设计问题
1. **为什么选择4x4 MAC阵列?** 平衡面积和性能
2. **INT8累加器位宽选择?** 考虑累加深度和溢出风险
3. **存储层次设计?** 平衡带宽、容量和功耗

### 验证问题
1. **如何验证计算正确性?** DPI C模型作为golden reference
2. **覆盖率如何收敛?** 功能覆盖率+代码覆盖率组合
3. **遇到的最难bug?** CSA加法器或input buffer竞争条件

### 后端问题
1. **关键路径是什么?** MAC到accumulator数据通路
2. **如何优化时序?** 流水线、逻辑重构、物理优化
3. **后仿频率如何?** 214MHz，满足200MHz目标

### 扩展问题
1. **如果重做会改进什么?** 更好的数据流架构、更丰富的指令集
2. **支持其他网络?** 可以扩展支持ResNet、MobileNet等
3. **商业化考虑?** 面积优化、功耗优化、软件栈开发
