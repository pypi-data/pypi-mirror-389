# Triclick Doc Toolset

一个基于管道架构的文档处理工具集

## 项目架构理念

### 核心设计原则

本项目采用**管道-策略-命令**三层架构模式，实现了高度可配置、可扩展的文档处理框架：

#### 1. 管道架构 (Pipeline Architecture)
- **声明式配置**：通过YAML配置文件定义处理流程，实现业务逻辑与代码分离
- **流式处理**：数据在管道中流转，每个阶段都对上下文进行增量处理
- **可组合性**：不同的管道配置可以组合出不同的处理流程

#### 2. 策略模式 (Strategy Pattern)
- **执行策略**：支持顺序执行(sequential)和并行执行(parallel)两种模式
- **优先级控制**：通过数值优先级控制策略和命令的执行顺序
- **条件执行**：支持基于上下文条件的动态命令执行

#### 3. 命令模式 (Command Pattern)
- **统一接口**：所有处理逻辑封装为Command，提供统一的执行接口
- **自动注册**：通过CommandRegistry实现命令的自动发现和注册
- **条件判断**：每个命令都有is_satisfied和check_condition机制

### 架构层次

```
Pipeline (管道层)
├── Strategy (策略层)
│   ├── ExecMode: sequential/parallel
│   ├── Priority: 数值优先级
│   └── Commands: 命令列表
└── Command (命令层)
    ├── is_satisfied(): 前置条件检查
    ├── check_condition(): 运行时条件检查
    └── execute(): 核心执行逻辑
```

### 数据流转

项目采用**Context上下文对象**作为数据载体，在管道中流转：

```
Context {
    doc_type: 文档类型识别结果
    document_uri: 输入文档路径
    sections: 解析出的文档段落结构
    metadata: 元数据字典
    errors: 错误信息收集
    generated_files: 生成的文件列表
}
```

### 配置驱动

#### 管道配置示例
```yaml
pipeline:
  strategies:
    - name: detect_file_type
      exec_mode: sequential
      priority: 1
      commands:
        - type: FileTypeIdentificationCommand
          name: detect_file_type
          priority: 1
    
    - name: parse_by_type
      exec_mode: sequential
      priority: 2
      commands:
        - type: DocxFileParseCommand
          condition: "doc_type == 'docx'"
          priority: 1
```

### 扩展性设计

#### 1. 命令扩展
- 继承`Command`基类
- 实现`is_satisfied()`和`execute()`方法
- 通过`CommandRegistry.register()`注册

#### 2. 策略扩展
- 新增执行模式枚举值
- 在`Strategy.apply()`中实现对应逻辑

#### 3. 管道扩展
- 创建新的YAML配置文件
- 定义策略组合和执行顺序

### 领域特化

项目针对文档处理领域进行了特化设计：

#### 文档解析层
- **多格式支持**：DOCX、RTF等格式的统一处理接口
- **结构化解析**：标题、表格、脚注的结构化提取
- **元数据保留**：段落索引、样式信息的完整保留

#### 业务规则层
- **模式匹配**：基于正则表达式的标题和脚注模式识别
- **引用解析**："Same as Table X.Y"等业务规则的自动处理
- **文件命名**：基于内容标签的智能文件命名

#### 输出管理层
- **路径去重**：自动处理文件名冲突
- **样式保留**：完整保留原文档的格式和样式
- **批量处理**：支持单文件和文件夹的批量处理

### 工程实践

#### 缓存机制
- **管道缓存**：基于配置文件修改时间的智能缓存
- **线程安全**：使用锁机制保证并发安全

#### 错误处理
- **优雅降级**：单个命令失败不影响整体流程
- **错误收集**：统一的错误信息收集和报告机制

#### 资源管理
- **路径解析**：支持打包后的资源文件访问
- **内存优化**：流式处理避免大文件内存占用

## 使用方式

### 基础用法
```python
from triclick_doc_toolset import run_generation, run_review

# 运行生成流水线
result = run_generation("input.docx", "output/")

# 运行评审流水线  
result = run_review("input.docx", "output/")
```

### 自定义管道
```python
from triclick_doc_toolset import run_pipeline

result = run_pipeline("custom_pipeline.yaml", "input.docx", "output/")
```

## 项目结构

```
triclick-doc-toolset/
├── pipelines/              # 管道配置文件
│   ├── generation.yaml     # 生成流水线
│   ├── review.yaml         # 评审流水线
│   └── title_table_footnote_patterns.yaml  # 模式配置
├── src/triclick_doc_toolset/
│   ├── framework/          # 核心框架
│   │   ├── pipeline.py     # 管道实现
│   │   ├── strategy.py     # 策略实现
│   │   ├── command.py      # 命令基类
│   │   ├── context.py      # 上下文对象
│   │   └── command_registry.py  # 命令注册表
│   ├── commands/           # 具体命令实现
│   ├── common/             # 通用组件
│   │   ├── models/         # 数据模型
│   │   ├── utils/          # 工具函数
│   │   ├── rules/          # 业务规则
│   │   └── word/           # Word文档处理
│   └── service.py          # 服务入口
└── tests/                  # 测试用例
```

这种架构设计使得项目具备了良好的**可维护性**、**可扩展性**和**可测试性**，能够灵活应对不同的文档处理需求。