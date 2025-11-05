# SecretPkg555

简单的1+1计算包，核心逻辑可编译为二进制保护源码。

## 安装
python版本为3.8.0

接下来执行下面命令：
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