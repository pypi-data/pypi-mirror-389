# Holo Search SDK

一个用于Hologres数据库搜索操作的 Python SDK，支持向量搜索和全文搜索功能。

## ✨ 特性

- **🔍 向量搜索**: 基于语义相似性的搜索功能
- **📝 全文搜索**: 传统的基于关键词的搜索
- **🛡️ 类型安全**: 使用类型提示和数据验证
- **🧩 模块化设计**: 清晰的分层架构，便于扩展和维护

## 📦 安装

### 从 PyPI 安装

```bash
pip install holo-search-sdk
```

## 🚀 快速开始

### 基本使用

```python
import holo_search_sdk as holo

# 连接到数据库
client = holo.connect(
    host="your-host",
    port=80,
    database="your-database",
    access_key_id="your-access-key-id",
    access_key_secret="your-access-key-secret",
    schema="public"
)

# 建立连接
client.connect()

# 打开表
columns = {
    "id": ("INTEGER", "PRIMARY KEY"),
    "content": "TEXT",
    "vector": "FLOAT8[]",
    "metadata": "JSONB"
}
table = client.open_table("table_name")

# 插入数据
data = [
    [1, "Hello world", [0.1, 0.2, 0.3], {"category": "greeting"}],
    [2, "Python SDK", [0.4, 0.5, 0.6], {"category": "tech"}],
    [3, "Vector search", [0.7, 0.8, 0.9], {"category": "search"}]
]
table.insert_multi(data, ["id", "content", "vector", "metadata"])

# 设置向量索引
table.set_vector_index(
    column="vector",
    distance_method="Cosine",
    base_quantization_type="rabitq",
    max_degree=64,
    ef_construction=400
)

# 向量搜索
query_vector = [0.1, 0.2, 0.3]
results = table.search_vector(query_vector, "vector").limit(10).fetchall()

# 关闭连接
client.disconnect()
```

### 使用上下文管理器

```python
import holo_search_sdk as holo

with holo.connect(
    host="your-host",
    port=80,
    database="your-database",
    access_key_id="your-access-key-id",
    access_key_secret="your-access-key-secret"
) as client:
    client.connect()
    
    # 执行数据库操作
    table = client.open_table("table_name")
    results = table.search_vector([0.1, 0.2, 0.3], "vector_column").fetchall()
    
    # 连接会自动关闭
```

## 📚 详细文档

### 核心概念

#### 1. 客户端 (Client)

客户端是与数据库交互的主要接口：

```python
from holo_search_sdk import connect

# 创建客户端
client = connect(
    host="localhost",
    port=80,
    database="test_db",
    access_key_id="your_key",
    access_key_secret="your_secret"
)

# 建立连接
client.connect()

# 执行 SQL
result = client.execute("SELECT COUNT(*) FROM users", fetch_result=True)

# 表操作
table = client.open_table("table_name")
```

#### 2. 表操作 (Table Operations)

表是数据存储和搜索的基本单位：

```python
# 打开现有表
table = client.open_table("table_name")

# 检查表是否存在
exists = client.check_table_exist("table_name")

# 删除表
client.drop_table("table_name")
```

#### 3. 数据插入

支持单条和批量数据插入：

```python
# 插入单条记录
table.insert_one(
    [1, "标题", "内容", [0.1, 0.2, 0.3]],
    ["id", "title", "content", "vector"]
)

# 批量插入
data = [
    [1, "文档1", "内容1", [0.1, 0.2, 0.3]],
    [2, "文档2", "内容2", [0.4, 0.5, 0.6]],
    [3, "文档3", "内容3", [0.7, 0.8, 0.9]]
]
table.insert_multi(data, ["id", "title", "content", "vector"])
```

#### 4. 向量索引

为向量列创建高效的搜索索引：

```python
# 设置单个向量索引
table.set_vector_index(
    column="vector",
    distance_method="Cosine",  # 可选: "Euclidean", "InnerProduct", "Cosine"
    base_quantization_type="rabitq",  # 可选: "sq8", "sq8_uniform", "fp16", "fp32", "rabitq"
    max_degree=64,
    ef_construction=400,
    use_reorder=True,
    precise_quantization_type="fp32",
    max_total_size_to_merge_mb=4096,  # 磁盘合并时数据的最大文件大小，单位MB
    build_thread_count=16  # 索引构建过程中使用的线程数
)

# 设置多个向量索引
table.set_vector_indexes({
    "content_vector": {
        "distance_method": "Cosine",
        "base_quantization_type": "rabitq",
        "max_degree": 64,
        "ef_construction": 400,
        "use_reorder": True,
        "precise_quantization_type": "fp32",
        "max_total_size_to_merge_mb": 4096,
        "build_thread_count": 16
    },
    "title_vector": {
        "distance_method": "Euclidean",
        "base_quantization_type": "rabitq",
        "max_degree": 32,
        "ef_construction": 200,
        "use_reorder": True,
        "precise_quantization_type": "fp32",
        "max_total_size_to_merge_mb": 4096,
        "build_thread_count": 16
    }
})

# 删除所有向量索引
table.delete_vector_indexes()
```

#### 5. 向量搜索

执行语义相似性搜索：

```python
# 基本向量搜索
query_vector = [0.1, 0.2, 0.3]
results = table.search_vector(
    vector=query_vector,
    column="vector",
    distance_method="Cosine"
).fetchall()

# 带输出别名的搜索
results = table.search_vector(
    vector=query_vector,
    column="vector",
    output_name="similarity_score",
    distance_method="Cosine"
).fetchall()
```

#### 6. 数据查询

支持基于主键的精确查询：

```python
# 根据主键查询单条记录
result = table.get_by_key(
    key_column="id",
    key_value=1,
    return_columns=["id", "content", "vector"]  # 可选，不指定则返回所有列
).fetchone()

# 根据主键列表批量查询
results = table.get_multi_by_keys(
    key_column="id", 
    key_values=[1, 2, 3],
    return_columns=["id", "content"]  # 可选，不指定则返回所有列
).fetchall()
```

#### 7. 向量索引管理

查询和管理向量索引信息：

```python
# 获取向量索引信息
index_info = table.get_vector_index_info()
if index_info:
    print("当前向量索引配置:", index_info)
else:
    print("未找到向量索引配置")

# 索引信息示例返回格式
# {
#     "vector_column": {
#         "algorithm": "HGraph",
#         "distance_method": "Cosine",
#         "builder_params": {
#             "max_degree": 64,
#             "ef_construction": 400,
#             "base_quantization_type": "rabitq",
#             "use_reorder": true,
#             "precise_quantization_type": "fp32",
#             "precise_io_type": "block_memory_io",
#             "max_total_size_to_merge_mb": 4096,
#             "build_thread_count": 16
#         }
#     }
# }
```

### 配置选项

#### 连接配置

```python
from holo_search_sdk.types import ConnectionConfig

config = ConnectionConfig(
    host="your-host.com",
    port=80,
    database="production_db",
    access_key_id="user...",
    access_key_secret="secret...",
    schema="analytics"  # 默认为 "public"
)
```

#### 向量索引配置

- **distance_method**: 距离计算方法
  - `"Euclidean"`: 欧几里得距离
  - `"InnerProduct"`: 内积距离
  - `"Cosine"`: 余弦距离

- **base_quantization_type**: 基础量化类型
  - `"sq8"`, `"sq8_uniform"`, `"fp16"`, `"fp32"`, `"rabitq"`
- **max_degree**: 图构建过程中每个顶点尝试连接的最近邻数量 (默认: 64)
- **ef_construction**: 图构建过程中的搜索深度控制 (默认: 400)
- **use_reorder**: 是否使用 HGraph 高精度索引 (默认: False)
- **precise_quantization_type**: 精确量化类型 (默认: "fp32")
- **precise_io_type**: 精确 IO 类型 (默认: "block_memory_io")
- **max_total_size_to_merge_mb**: 磁盘合并时数据的最大文件大小，单位MB (默认: 4096)
- **build_thread_count**: 索引构建过程中使用的线程数 (默认: 16)

## 🔧 API 参考

### 主要类

- **`Client`**: 数据库客户端，管理连接和表操作
- **`HoloTable`**: 表操作接口，支持数据插入和向量搜索
- **`ConnectionConfig`**: 连接配置数据类

### 主要函数

- **`connect()`**: 创建数据库客户端连接
- **`open_table()`**: 打开现有表
- **`insert_one()`**: 插入单条记录
- **`insert_multi()`**: 批量插入记录
- **`set_vector_index()`**: 设置向量索引
- **`search_vector()`**: 执行向量搜索

### 异常类

- **`HoloSearchError`**: 基础异常类
- **`ConnectionError`**: 连接相关错误
- **`QueryError`**: 查询执行错误
- **`SqlError`**: SQL 生成错误
- **`TableError`**: 表操作错误

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE.txt](LICENSE.txt) 文件了解详情。

---

**Holo Search SDK** - 让Hologres向量和全文搜索变得简单高效 🚀
