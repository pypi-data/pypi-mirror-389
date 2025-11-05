# SecretPkg555

简单的计算包，核心逻辑已编译为二进制保护源码。

## 安装

```bash
pip install secretpkg555
```

## API文档

### secret_algorithm(data)

给数字加1

**参数:**
- `data` (int | float): 输入的数字

**返回:**
- int | float: data + 1

**示例:**
```python
from secretpkg555 import secret_algorithm

result = secret_algorithm(5)
print(result)  # 6
```

### complex_calculation(x, y)

简单加法

**参数:**
- `x` (int | float): 第一个数字
- `y` (int | float): 第二个数字

**返回:**
- int | float: x + y

**示例:**
```python
from secretpkg555 import complex_calculation

result = complex_calculation(10, 20)
print(result)  # 30
```

### advanced_algorithm(data)

高级算法：data * 2 + 1

**参数:**
- `data` (int | float): 输入数据

**返回:**
- int | float: 计算结果

**示例:**
```python
from secretpkg555 import advanced_algorithm

result = advanced_algorithm(5)
print(result)  # 11
```

### secret_process(x, y)

秘密处理：(x + y) * 3

**参数:**
- `x` (int | float): 第一个数字
- `y` (int | float): 第二个数字

**返回:**
- int | float: 处理结果

**示例:**
```python
from secretpkg555 import secret_process

result = secret_process(10, 20)
print(result)  # 90
```

### encrypt(data)

简单加密

**参数:**
- `data` (int): 要加密的数据

**返回:**
- int: 加密后的数据

**示例:**
```python
from secretpkg555 import encrypt

encrypted = encrypt(42)
print(encrypted)  # 142
```

### decrypt(data)

简单解密

**参数:**
- `data` (int): 要解密的数据

**返回:**
- int: 解密后的数据

**示例:**
```python
from secretpkg555 import decrypt

decrypted = decrypt(142)
print(decrypted)  # 42
```

## 完整示例

```python
from secretpkg555 import (
    secret_algorithm,
    complex_calculation,
    advanced_algorithm,
    secret_process,
    encrypt,
    decrypt,
)

# 基础算法
print(secret_algorithm(5))  # 6

# 复杂计算
print(complex_calculation(10, 20))  # 30

# 高级算法
print(advanced_algorithm(5))  # 11

# 秘密处理
print(secret_process(10, 20))  # 90

# 加密解密
data = 42
encrypted = encrypt(data)
decrypted = decrypt(encrypted)
print(f"{data} -> {encrypted} -> {decrypted}")
```

## 特性

- ✅ 简单易用的API
- ✅ 核心逻辑二进制保护
- ✅ 完整的文档字符串
- ✅ 类型提示支持

## 许可证

MIT License