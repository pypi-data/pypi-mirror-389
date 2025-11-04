# 上传GmServerSdk构建产物到PyPI的步骤

### 前提条件
1. **准备PyPI账号和API Token**
   - 在 https://pypi.org/ 注册账号
   - 在Account Settings > API tokens中创建token
   - 选择"Entire account"范围或指定项目范围

### 步骤1：配置认证信息
有两种方式配置PyPI认证：

**方法A：使用.pypirc文件**
```bash
# 在用户主目录创建.pypirc文件
# Windows: C:\Users\用户名\.pypirc
# Linux/Mac: ~/.pypirc

[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmcCJDlkMmVhZjRkLTk5NmQtNDhjNi1hYTEyLWExYmYxMWMzMDMyMQACKlszLCJiMDhmM2YyNS05NjYzLTQzMjEtYjAxYS1mNjRhNmJhNmNiZTkiXQAABiAviPVuZXgHJGDbqSgdGxWhlnQ51tEADs2YmV9W418xSA

[testpypi]
username = __token__
password = your-test-pypi-token
repository = https://test.pypi.org/legacy/
```

**方法B：使用环境变量**
```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-AgEIcHlwaS5vcmcCJDlkMmVhZjRkLTk5NmQtNDhjNi1hYTEyLWExYmYxMWMzMDMyMQACKlszLCJiMDhmM2YyNS05NjYzLTQzMjEtYjAxYS1mNjRhNmJhNmNiZTkiXQAABiAviPVuZXgHJGDbqSgdGxWhlnQ51tEADs2YmV9W418xSA
```

### 步骤2：安装必要工具
```bash
pip install build twine
```

### 步骤3：验证包配置
确保`pyproject.toml`包含所有必要信息：
- 项目名称和版本
- 作者和联系方式
- 描述和关键词
- 许可证信息
- 依赖关系
- 项目URL

### 步骤4：构建包
```bash
cd GmServerSdk
python -m build
```

### 步骤5：检查包完整性
```bash
python -m twine check dist/*
```

### 步骤6：（可选）测试上传到TestPyPI
```bash
python -m twine upload --repository testpypi dist/*
```

### 步骤7：上传到正式PyPI
```bash
python -m twine upload dist/*
```

### 步骤8：验证上传结果
1. 访问 https://pypi.org/project/gmsdk/ 查看包页面
2. 测试安装：
```bash
pip install gmsdk
```

### 常见问题解决

**1. 权限错误**
- 确保API Token有足够的权限
- 检查包名是否已被占用

**2. 版本冲突**
- 如果版本已存在，需要更新版本号
- 删除PyPI上的旧版本（只能删除24小时内的版本）

**3. 构建失败**
- 检查pyproject.toml语法
- 确保所有依赖项版本兼容

**4. 上传超时**
- 检查网络连接
- 重新尝试上传命令

### 自动化部署
可以创建GitHub Actions或CI/CD流水线自动发布：
```yaml
# .github/workflows/publish.yml
name: Publish to PyPI
on:
  release:
    types: [published]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.x'
    - name: Install dependencies
      run: |
        python -m pip install build twine
    - name: Build package
      run: python -m build
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

这样，每次创建GitHub Release时就会自动发布到PyPI。

### 项目特定配置

对于GmServerSdk项目，我们已经完成了以下配置：

1. **pyproject.toml配置**：
   - 项目名称：gmsdk
   - 版本：1.0.0
   - 作者：nirvana0614
   - 许可证：MIT
   - 支持Python版本：3.8+

2. **依赖项**：
   - protobuf>=3.20.3,<4.0.0
   - grpcio==1.47.5
   - pandas>=1.5.0
   - numpy>=1.21.0

3. **项目URL**：
   - 主页：https://gitee.com/nirvana0614/gm-sdk-platform
   - 仓库：https://gitee.com/nirvana0614/gm-sdk-platform
   - 问题跟踪：https://gitee.com/nirvana0614/gm-sdk-platform/issues

4. **分类器**：
   - 支持跨平台
   - 面向开发者和金融行业
   - 开发状态：Beta版本

### 版本管理建议

对于后续版本发布，建议遵循语义化版本控制：

- **主版本号**：不兼容的API修改
- **次版本号**：向下兼容的功能性新增
- **修订号**：向下兼容的问题修正

例如：
- 1.0.0 - 首次发布
- 1.0.1 - 修复bug
- 1.1.0 - 新增功能
- 2.0.0 - 破坏性变更

### 发布清单

在发布新版本前，请检查：

- [ ] 更新版本号
- [ ] 更新CHANGELOG.md
- [ ] 运行所有测试
- [ ] 构建并检查包
- [ ] 测试安装
- [ ] 上传到PyPI
- [ ] 创建GitHub Release（如果使用）