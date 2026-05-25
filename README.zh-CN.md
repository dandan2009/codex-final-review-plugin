# Codex Final Review Plugin

[English](README.md) | [简体中文](README.zh-CN.md)

`final-review` 是一个本地 Codex 插件，用来自动化“上线前终审”代码 review 流程。你可以用很短的命令触发它：

```text
$final-review uncommitted
$final-review staged
$final-review mr 123
$final-review pr 123
```

也支持中文别名：

```text
$final-review 未提交的代码
$final-review 暂存的代码
$final-review 这个mr 123
$final-review 这个pr 123
```

插件会解析你要 review 的 diff，收集上下文，运行两个 review 视角，验证 finding 是否真实，修复真实问题，重新运行相关检查，做影响面复查，并输出剩余风险。

## 包含内容

- Codex 插件清单：`.codex-plugin/plugin.json`
- `final-review` skill：`skills/final-review/SKILL.md`
- 本地 stdio MCP server：`scripts/final_review_mcp.py`
- 一键安装脚本：`install.py`

## 环境要求

- 支持本地插件的 Codex desktop app
- Python 3.10 或更新版本
- `git`
- PR/MR review 可选依赖：
  - GitHub CLI：`gh`
  - GitLab CLI：`glab`

安装脚本会创建插件本地 `.venv`，并从 `requirements.txt` 安装 Python 依赖。如果想手动安装依赖，可以运行：

```bash
python3 -m pip install mcp
```

如果要 review GitHub PR，请先登录 `gh`：

```bash
gh auth login
```

如果要 review GitLab MR，请先登录 `glab`：

```bash
glab auth login
```

## 安装

克隆仓库：

```bash
git clone https://github.com/dandan2009/codex-final-review-plugin.git
cd codex-final-review-plugin
```

运行安装脚本：

```bash
python3 install.py
```

安装脚本会：

- 创建 `~/plugins/final-review`，默认指向当前 checkout 的 symlink
- 创建 `~/plugins/final-review/.venv` 并安装 Python 依赖
- 创建或更新 `~/.agents/plugins/marketplace.json`
- 添加 Codex 识别插件所需的 marketplace entry
- 保留当前仓库 checkout 作为后续更新源

安装完成后，重启 Codex，让插件和 MCP server 被重新发现。

## 使用

Review 所有本地未提交代码：

```text
$final-review uncommitted
```

Review 暂存区代码：

```text
$final-review staged
```

Review GitLab merge request：

```text
$final-review mr 123
$final-review mr https://gitlab.example.com/group/project/-/merge_requests/123
```

Review GitHub pull request：

```text
$final-review pr 123
$final-review pr https://github.com/owner/repo/pull/123
```

中文别名：

```text
$final-review 未提交的代码
$final-review 暂存的代码
$final-review 这个mr 123
$final-review 这个pr 123
```

如果 Codex 需要你明确授权打开独立子会话，它会先问：

```text
May I open two independent read-only sub-sessions for this final-review?
```

回答 yes 或“允许”后，会使用两个独立只读 reviewer。如果你拒绝，或当前环境不支持 subagent，流程会降级成本地双 pass review，并在最终报告里说明这个降级。

## 工作原理

插件分为三层：

- Plugin：让 Codex 能发现、安装和加载这项能力。
- Skill：定义 final-review 的流程、验证规则、ledger 状态和停止条件。
- MCP：用确定性的只读工具收集 review 上下文。

这个 MCP 是本地工具，不是远程服务。Codex 会通过 stdio 启动：

```bash
python3 ./scripts/run_mcp.py
```

`run_mcp.py` 会优先使用插件本地 `.venv`。它不会把你的代码发送到第三方服务器，只会运行本地 git/CLI 命令，并把结构化上下文返回给 Codex。

## MCP 工具

插件暴露一个 MCP 工具：

```text
final_review_collect(scope, identifier?, cwd?)
```

支持的 scope：

- `uncommitted`：收集 `git status`、`git diff`、`git diff --cached` 和小型安全的 untracked 文件
- `staged`：收集 `git diff --cached`，并报告 unstaged/untracked 污染风险
- `pr`：收集 `gh pr view` 和 `gh pr diff`
- `mr`：收集 `glab mr view` 和 `glab mr diff`

这个工具是只读的。它不会修改文件、暂存文件、运行测试或创建 commit。

## 更新

如果使用默认 symlink 安装：

```bash
cd ~/plugins/final-review
git pull
```

如果你 clone 到了其他路径，就在对应 checkout 中更新：

```bash
cd /path/to/codex-final-review-plugin
git pull
```

然后重启 Codex。

## 卸载

删除 symlink 或复制出来的插件目录：

```bash
rm -rf ~/plugins/final-review
```

然后从下面的文件里删除 `final-review` entry：

```text
~/.agents/plugins/marketplace.json
```

最后重启 Codex。

## 更多文档

- [Installation Guide](docs/INSTALL.md)
- [Usage Guide](docs/USAGE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Security Notes](docs/SECURITY.md)

