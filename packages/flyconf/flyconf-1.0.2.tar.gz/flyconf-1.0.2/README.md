# FlyConf Parser

FlyConf Parser 是一个用于解析 fc 配置文件格式的 Python 库。fc 配置文件是一种具有特定语法的配置格式，支持复杂的数据结构、变量引用和环境感知配置。

## 特性

- 词法分析器，支持识别 fc 配置文件中的各种标记
- 语法分析器，构建配置块的抽象语法树
- 数据模型，用于表示解析后的配置结构
- 字符串处理（原生多行字符串和单行字符串）
- 变量引用系统（支持外部变量、环境变量和配置内引用）
- 列表解析（简单列表和嵌套列表）
- 导入导出功能（支持 JSON 格式）
- 环境感知配置合并
- 全局变量声明和引用
- 跨文件属性引用

## 安装

```bash
pip install flyconf
```

## 使用方法

### 基本用法

```python
from flyconf.parser import FCConfigParser

# 解析 fc 配置文件
config = FCConfigParser.parse_file("config.fc")

# 访问配置块
block = config.get_block("server")
print(block.data)

# 导出为 JSON
import json
json_data = config.to_json()
```

### fc 配置文件语法

fc 配置文件具有以下语法结构：

```
@block_name(meta_key>meta_value) data_key>data_value
```

示例：
```fc
&&global_host>localhost
&&global_port>3306

@mysql_default(type>conf.db)
dbtype>mysql
host>$(global_host)
port>$(global_port)
database>oax
user>root
password>1234

@remember_me(type>conf.txt)
username>admin
password>1234

@test_list
users>[user1,user2,user3]
```

### 字符串

使用 `^...^` 表示单行字符串，使用 `^^^...^^^` 表示多行字符串：

```fc
@get_users(type>conf.sql)
dbtype>mysql
sql>^
SELECT id, username, email FROM users
^
```

### 列表

使用 `[...]` 表示对象列表，使用逗号分隔表示简单值列表：

```fc
@test_list
# 简单值列表
numbers>1,2,3,4,5

# 对象列表
users>[id>1 name>Alice],[id>2 name>Bob]
```

### 变量引用

使用 `$(variable_name)` 表示变量引用：

```fc
@server
path>$(config.path)
```

### 全局变量

使用 `&&variable_name>value` 声明全局变量：

```fc
&&default_host>localhost
&&default_port>3306

@mysql_config
host>$(default_host)
port>$(default_port)
```

### 跨文件引用

使用点号表示从属关系，引用其他文件中的属性：

```fc
&&db_host>database_config.fc.mysql.host
&&db_port>database_config.fc.mysql.port
```

## API

### FCConfigParser

- `FCConfigParser.parse_text(text)` - 从文本解析配置
- `FCConfigParser.parse_file(file_path)` - 从文件解析配置

### FCConfig

- `config.get_block(name)` - 获取指定名称的块
- `config.add_block(block)` - 添加块
- `config.to_dict()` - 转换为字典
- `config.to_json()` - 转换为 JSON 字符串

### FCBlock

- `block.name` - 块名称
- `block.meta` - 元数据字典
- `block.data` - 数据字典