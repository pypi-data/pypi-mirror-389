# 自动化版本管理 - 快速参考

本文档是 Python 包版本管理最佳实践的快速操作指南。

## 📦 版本管理工作流

### 开发阶段

```bash
# 1. 正常开发，定期提交
git add .
git commit -m "feat: 新增功能描述"

# 2. 本地验证版本（可选）
python -c "import satellitecenter; print(satellitecenter.__version__)"
# 开发版本格式：1.0.0.devN+<hash>
```

### 发布阶段（3 步发布）

```bash
# 第 1 步：确保代码已提交且测试通过
git status  # 应该显示 "working tree clean"
uv run pytest

# 第 2 步：创建版本标签
git tag v1.0.0  # 替换为实际版本号

# 第 3 步：推送标签到远程
git push origin main
git push origin v1.0.0
```

**就这样！** GitHub Actions 会自动：
- ✅ 检测标签推送
- ✅ 构建包文件
- ✅ 发布到 PyPI
- ✅ 创建 GitHub Release

## 🔢 版本号规则

遵循语义化版本：`v主.次.修`

| 场景 | 版本号 | 何时使用 |
|------|--------|---------|
| 初始发布 | v1.0.0 | 首次发布 |
| 新功能（向下兼容） | v1.1.0 | `次版本号 +1` |
| Bug 修复 | v1.0.1 | `修订版本号 +1` |
| 重大变更（不兼容） | v2.0.0 | `主版本号 +1` |
| 测试版本 | v1.0.0rc1 | 正式发布前 |

## 🔍 版本查询

### 开发环境

```bash
# 查看包版本
python -c "import satellitecenter; print(satellitecenter.__version__)"
```

### 生产环境（安装后）

```bash
# 查看已安装包版本
pip show satellitecenter
```

## 📝 发布清单

发布前确认以下项目：

- [ ] 代码已提交：`git status` 显示 "working tree clean"
- [ ] 测试通过：`uv run pytest` 全部通过
- [ ] 代码质量检查通过
- [ ] CHANGELOG.md 已更新
- [ ] 没有不需要的标签：`git tag -l -n 5`

## ❌ 常见问题处理

### 问题 1：标签打错了

```bash
# 删除本地标签
git tag -d v1.0.0

# 删除远程标签
git push origin :refs/tags/v1.0.0

# 重新创建正确的标签
git tag v1.0.1
git push origin v1.0.1
```

### 问题 2：发布后想修改版本号

```bash
# 如果尚未构建：删除标签后重新创建
# 如果已发布到 PyPI：发布 v1.0.1 或更高版本

# PyPI 上的旧版本无法删除，但可以标记为 yanked
# 参考 PyPI 官方文档
```

### 问题 3：开发版本号看起来很奇怪

```bash
# 这是正常的！格式为：上一个标签 + 提交数量 + hash
# 例如：1.0.0.dev5+ga1b2c3d

# 创建发布标签后，版本号会变为清晰的 1.0.0
git tag v1.0.0
git push origin v1.0.0
```

## 📊 版本历史示例

```
main 分支：
  v1.0.0 ← 首次发布
  v1.0.1 ← Bug 修复
  v1.1.0 ← 新功能
  v1.1.1 ← Bug 修复
  v2.0.0 ← 重大变更（主版本号增加）
```

## 🚀 一键发布命令

创建 `release.sh` 脚本以简化流程：

```bash
#!/bin/bash
# 用法：./release.sh v1.0.0

VERSION=$1

# 验证输入
if [ -z "$VERSION" ]; then
  echo "用法：./release.sh vX.Y.Z"
  exit 1
fi

# 检查工作区
if [ ! -z "$(git status -s)" ]; then
  echo "❌ 工作区不干净，请先提交所有更改"
  exit 1
fi

# 运行测试
echo "🧪 运行测试..."
uv run pytest || exit 1

# 创建标签
echo "🏷️  创建标签 $VERSION..."
git tag "$VERSION" || exit 1

# 推送
echo "📤 推送到远程..."
git push origin main || exit 1
git push origin "$VERSION" || exit 1

echo "✅ 发布成功！GitHub Actions 会自动进行后续操作。"
```

使用：

```bash
chmod +x release.sh
./release.sh v1.0.0
```

## 📚 相关文档

- **RELEASE.md** - 详细发布指南
- **CHANGELOG.md** - 项目更新日志
- **.github/workflows/publish.yml** - CI/CD 工作流配置
- **pyproject.toml** - setuptools_scm 配置

## 💡 关键概念

### setuptools_scm

- 从 Git 标签自动读取版本号
- 在 `src/satellitecenter/_version.py` 中生成版本文件
- 构建时自动包含正确的版本号

### 版本获取优先级

1. **包元数据**（安装后）：`importlib.metadata.version()`
2. **_version.py**（开发时）：setuptools_scm 生成
3. **Fallback**（兜底）：`0.1.0`

### GitHub Actions

- 触发条件：推送 `v*` 标签
- 自动任务：构建 → 发布 → 创建 Release
- 需要：PyPI API Token（在 Secrets 中配置）

## ✨ 优势总结

| 方面 | 效果 |
|------|------|
| **自动化** | 标签即发布，无需手动步骤 |
| **一致性** | 所有环节版本号完全相同 |
| **安全性** | 版本号来自 Git，不可篡改 |
| **简洁性** | 发布只需 2 个 git 命令 |
| **可追溯** | 版本与 Git 历史完全对应 |

---

**最后提醒**：养成"标签即版本"的习惯，会让版本管理变得轻松高效！
