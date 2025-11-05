# 发布指南

## 已完成的构建

✅ 版本：0.1.5
✅ 构建文件位置：`dist/` 目录

构建产物：
- `puhuo_mcp_server-0.1.5-py3-none-any.whl` (Wheel 包)
- `puhuo_mcp_server-0.1.5.tar.gz` (源码包)

## 本地测试安装

在发布前，可以先本地测试安装：

```bash
# 方式1：直接安装 wheel 包
pip install dist/puhuo_mcp_server-0.1.5-py3-none-any.whl

# 方式2：使用 uv 安装
uv pip install dist/puhuo_mcp_server-0.1.5-py3-none-any.whl
```

## 发布到 PyPI

### 1. 安装发布工具

```bash
pip install twine
```

### 2. 检查包

```bash
twine check dist/puhuo_mcp_server-0.1.5*
```

### 3. 发布到 Test PyPI（测试环境，推荐先测试）

```bash
twine upload --repository testpypi dist/puhuo_mcp_server-0.1.5*
```

访问 https://test.pypi.org/project/puhuo-mcp-server/ 查看

测试安装：
```bash
pip install --index-url https://test.pypi.org/simple/ puhuo-mcp-server
```

### 4. 发布到正式 PyPI

```bash
twine upload dist/puhuo_mcp_server-0.1.5*
```

访问 https://pypi.org/project/puhuo-mcp-server/ 查看

### 5. 配置 PyPI 凭证

如果没有配置过，需要先配置：

**方式1：使用 API Token（推荐）**

创建 `~/.pypirc` 文件：
```ini
[pypi]
username = __token__
password = pypi-your-api-token-here

[testpypi]
username = __token__
password = pypi-your-test-api-token-here
```

**方式2：交互式输入**

在运行 `twine upload` 时会提示输入用户名和密码

## 发布到内部仓库

如果要发布到阿里云内部 PyPI 仓库：

```bash
# 配置内部仓库地址
twine upload --repository-url https://your-internal-pypi.com dist/puhuo_mcp_server-0.1.4*
```

## 标记 Git 版本

发布后建议打上 git tag：

```bash
git tag -a v0.1.4 -m "Release version 0.1.4"
git push origin v0.1.4
```

## 安装使用

发布后，用户可以直接安装：

```bash
pip install puhuo-mcp-server
```

或使用 uv：

```bash
uv pip install puhuo-mcp-server
```

## 下一个版本

修改版本号请更新：
- `pyproject.toml` 中的 `version` 字段
- 然后重新执行 `uv build`

