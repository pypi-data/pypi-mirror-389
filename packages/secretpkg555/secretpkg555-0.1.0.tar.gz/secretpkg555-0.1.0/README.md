# SecretPkg555

简单的1+1计算包，核心逻辑可编译为二进制保护源码。

## 安装

```bash
pip install secretpkg555
```

## 使用

```python
from secretpkg555 import SecretAPI

api = SecretAPI()
result = api.process_data(5)  # 返回 6
sum_result = api.calculate(10, 20)  # 返回 30
```

## 开发

### 测试
```bash
python test.py
```

### 编译核心逻辑（源码保护）
```bash
pip install nuitka
python compile.py
```

### 构建包
```bash
pip install build
python -m build
```

### 上传到PyPI
```bash
pip install twine
python -m twine upload dist/*
```

## 特性

- ✅ 简单易用的API
- ✅ 可选源码保护（编译为二进制）
- ✅ 纯Python实现（兼容所有平台）