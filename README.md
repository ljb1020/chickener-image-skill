# chickener-image：让你的 AI Agent 直接帮你生图（支持 4K）

装上这个 skill 后，在 Claude Code、Codex 里说一句"帮我生成一张 4K 的……"，Agent 就会调用 [chickener.top](https://chickener.top) 的生图模型，把图片保存到你的电脑上。

- 模型：`gpt-image-2`、`gpt-image-2.5`
- 尺寸：最高 4K（横版 3840×2160，竖版 2160×3840）
- 依赖：Python 3.8 及以上，不用装任何第三方库（没装的看第 0 节）

---

## 最快的用法：把本仓库链接发给你的 Agent

复制浏览器地址栏里的本仓库链接，连同下面这句话一起发给你的 Agent：

> 请帮我安装这个生图 skill：<本仓库链接>
> 按它 README 里的步骤安装，然后一步一步教我配置 API Key，配好后帮我测试生成一张图。

剩下的事 Agent 会照着本页带你做完，你只需要按它的提示去网站上复制一个 API Key。

---

## 0. 准备：电脑上要有 Python 3

生图脚本用 Python 写成，只需要 Python 3.8 或更高版本，不用装任何第三方库。

**先检查有没有装**：打开终端（Windows 上是 PowerShell），依次试下面的命令，有一条显示 `Python 3.x.x`（x 是数字）就说明已经装好，可以跳过本节：

```bash
python --version
python3 --version
py -3 --version
```

**没装的话，按系统安装：**

| 系统 | 安装方法 |
| --- | --- |
| Windows | 打开 https://www.python.org/downloads/ ，下载最新版并运行安装程序。**安装第一页底部一定要勾选 "Add python.exe to PATH"**，然后点 Install Now。熟悉命令行的用户也可以执行 `winget install Python.Python.3.12`。 |
| macOS | 在终端执行 `xcode-select --install`，按弹窗提示安装命令行开发者工具，其中自带 `python3`。也可以去 https://www.python.org/downloads/ 下载安装包。 |
| Linux | 一般已经预装。没有的话，Ubuntu/Debian 执行 `sudo apt install python3`，Fedora 执行 `sudo dnf install python3`。 |

**装完后要关掉终端和 Agent，再重新打开**，新装的 Python 才能被识别。

Windows 常见情况：
- 输入 `python` 后弹出了**微软商店**，或者提示 "Python was not found"：说明还没装，Windows 自带的只是一个跳转到商店的快捷方式。按上表从 python.org 安装即可。
- 装完仍提示找不到 `python`：多半是安装时没勾选 "Add python.exe to PATH"。先试 `py -3 --version`，能用的话后面所有命令把 `python` 换成 `py -3` 即可；不能用就重新运行安装程序，选 Modify 或重装，并勾上这一项。

## 1. 安装（Agent 执行）

把整个仓库克隆到对应的 skills 目录，**文件夹名必须是 `chickener-image`**。命令里的 `<本仓库链接>` 换成本仓库的 GitHub 地址：

| Agent | macOS / Linux / Git Bash | Windows PowerShell |
| --- | --- | --- |
| Claude Code | `git clone <本仓库链接> ~/.claude/skills/chickener-image` | `git clone <本仓库链接> "$HOME\.claude\skills\chickener-image"` |
| Codex | `git clone <本仓库链接> ~/.agents/skills/chickener-image` | `git clone <本仓库链接> "$HOME\.agents\skills\chickener-image"` |

- Windows 上这个目录就是 `C:\Users\你的用户名\.claude\skills\chickener-image`（Codex 是 `.agents`）。PowerShell 和 cmd 不会展开 `~`，在 Windows 上请用右边一列的命令。
- 装完后确认目录下直接就有 `SKILL.md`，不要多套一层文件夹。
- 没有 git，或者访问 GitHub 失败：在仓库页面点 **Code → Download ZIP**，解压后把文件夹改名为 `chickener-image`，放到上表的目录里。
- 装完后重启一次 Agent（或新开一个会话），它才能识别到这个 skill。

## 2. 配置 API Key（只需做一次）

**第 1 步：在网站上创建 API Key**

1. 登录 https://chickener.top ，打开左侧菜单 **API 密钥**（也可以直接访问 https://chickener.top/keys ）。
2. 点 **创建 API 密钥**，名称随便填。
3. **分组一定要选【GPT】生图分组**。选其他分组无法生图。
4. 创建后点 **复制密钥**，得到一串 `sk-` 开头的字符。

**第 2 步：把密钥发给你的 Agent**

直接把复制的密钥粘贴到聊天里发给 Agent，它会帮你保存并检查。这一步就完成了。

> 不想把密钥发在聊天里？在你自己的终端运行下面这条命令（让 Agent 告诉你完整路径），出现提示后粘贴密钥并按回车。**粘贴后屏幕上不显示任何字符，这是正常的**，直接回车即可。看到 `OK: key ... saved` 就保存好了。
>
> ```bash
> python scripts/gen_image.py --set-key
> ```

密钥会保存在固定位置：

| 系统 | 配置文件位置 |
| --- | --- |
| Windows | `C:\Users\你的用户名\.chickener\config.json` |
| macOS | `/Users/你的用户名/.chickener/config.json` |
| Linux | `/home/你的用户名/.chickener/config.json` |

文件内容只有一行：`{"api_key": "sk-你的key"}`。

**第 3 步：检查配置（Agent 会自动做）**

```bash
python scripts/gen_image.py --check
```

看到 `OK: ready` 就说明配置好了。如果报错，Agent 会告诉你哪里不对，常见原因见文末"常见问题"。

## 3. 开始生图

直接跟 Agent 说就行，例如：

- "帮我生成一张 4K 横版壁纸：雪山下的湖泊，清晨薄雾"
- "用 gpt-image-2.5 画一张 4K 竖版手机壁纸，赛博朋克城市夜景"
- "生成一张 1024x1024 的猫咪头像，水彩风格"

图片默认保存在当前文件夹的 `chickener-images/` 里，Agent 会告诉你文件路径和实际尺寸。

**4K 一张大约需要 20～60 秒，请耐心等待，不要中途打断。**

### 尺寸速查

| 想要 | 尺寸 |
| --- | --- |
| 4K 横版（16:9） | `3840x2160` |
| 4K 竖版（9:16） | `2160x3840` |
| 2K 横版 / 竖版 | `2560x1440` / `1440x2560` |
| 方图 | `1024x1024` |
| 其他比例 | `宽x高`，最长边不超过 3840，宽和高都取 16 的倍数 |

### 手动运行（不用 Agent 也可以）

```bash
python scripts/gen_image.py --prompt "雪山下的湖泊，清晨薄雾" --size 4k
python scripts/gen_image.py --prompt "赛博朋克城市夜景" --size 4k-portrait --model gpt-image-2.5 --out wallpaper.png
```

参数：`--size`（尺寸或 `4k` / `4k-portrait` / `2k` 等简写）、`--model`（`gpt-image-2` 或 `gpt-image-2.5`）、`--n`（一次生成 1～4 张）、`--out`（保存的文件夹或文件名）。

## 常见问题

| 提示 | 原因和解决 |
| --- | --- |
| `API key is not configured` | 还没保存 key，回到第 2 节。 |
| `the API key was rejected (HTTP 401)` | key 复制错了，或者已被删除、禁用。重新复制一次发给 Agent。 |
| `this does not look like a chickener API key` | 粘贴的内容不完整或为空。重新点"复制密钥"，确认复制到的是 `sk-` 开头的整串字符。 |
| `the token cannot use this model` / `cannot see any image model` | 令牌分组没选【GPT】生图分组。到 API 密钥页面编辑该令牌，把分组改过来。 |
| `not enough balance or token quota` | 账户余额或令牌额度不足，先充值，或调高令牌额度。 |
| `request timed out` | 网络慢或图太大。再试一次；还不行就先用小一点的尺寸。 |
| `python` 不是内部或外部命令 / 弹出微软商店 / "Python was not found" | 没装 Python，或者安装时没勾选加入 PATH。见第 0 节。 |

## 进阶

- 环境变量 `CHICKENER_API_KEY`：设置后优先于配置文件。
- 环境变量 `CHICKENER_BASE_URL`：修改站点地址，默认 `https://chickener.top`。
- 更新 skill：在安装目录执行 `git pull`。配置文件在用户目录下，更新不会丢失。

## 安全说明

- key 只保存在你自己电脑的 `~/.chickener/config.json` 里，不会写进本仓库或你的项目文件。
- 如果你把 key 发到了聊天里，它会留在聊天记录中。介意的话，可以在 API 密钥页面删除旧 key，重新创建一个。
- key 泄露后别人可以用你的余额生图，不要把它发给其他人。
