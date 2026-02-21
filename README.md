# Discourse Auto Read

自动阅读 Discourse 论坛帖子，使用 GitHub Actions 定时运行。

## 功能

- ✅ 自动登录论坛
- ✅ 自动查找未读帖子
- ✅ 自动阅读新话题
- ✅ 模拟真人阅读（滚动浏览）
- ✅ 随机点赞
- ✅ 支持多个论坛
- ✅ 可选录屏功能
- ✅ **TuneHub 自动签到**
- ✅ **AnyRouter 自动签到**
- ✅ **GGBOOM 自动签到**

## 快速开始

### 1. Fork 本仓库

点击右上角 **Fork** 按钮。

### 2. 配置 Secrets

进入你 fork 的仓库：**Settings** → **Secrets and variables** → **Actions** → **Secrets**

添加以下 Secrets：

| 名称 | 必填 | 说明 |
|------|------|------|
| `TARGET_URL` | ✅ | 论坛地址，例如 `https://linux.do` |
| `USERNAME` | ✅ | 你的用户名 |
| `PASSWORD` | ✅ | 你的密码 |

**可选（第二个论坛）：**

| 名称 | 说明 |
|------|------|
| `TARGET_URL_2` | 第二个论坛地址 |
| `USERNAME_2` | 第二个论坛用户名 |
| `PASSWORD_2` | 第二个论坛密码 |

### 3. 配置 Variables（可选）

进入 **Settings** → **Secrets and variables** → **Actions** → **Variables**

| 名称 | 默认值 | 说明 |
|------|--------|------|
| `MAX_TOPICS` | `10` | 每次阅读的未读帖子数量 |
| `MAX_NEW_TOPICS` | `20` | 每次阅读的新话题数量 |
| `ENABLE_RECORDING` | `false` | 是否录制视频（`true`/`false`） |
| `ENABLE_TUNEHUB_CHECKIN` | `false` | 启用 TuneHub 自动签到（`true`/`false`） |
| `ENABLE_ANYROUTER_CHECKIN` | `false` | 启用 AnyRouter 自动签到（`true`/`false`） |
| `ENABLE_GGBOOM_CHECKIN` | `false` | 启用 GGBOOM 自动签到（`true`/`false`） |

### 4. 启用 Actions

进入 **Actions** 标签页，点击 **I understand my workflows, go ahead and enable them**。

### 5. 手动运行测试

1. 进入 **Actions** 标签页
2. 选择左侧的 **Discourse Auto Read**
3. 点击 **Run workflow**
4. 查看运行日志确认是否成功

## 自动运行

默认每 2 小时自动运行一次。可以在 `.github/workflows/auto-read.yml` 中修改 cron 表达式：

```yaml
schedule:
  - cron: '0 */2 * * *'  # 每 2 小时
```

## 录屏功能

开启录屏后，可以在 Actions 运行完成后下载 `debug-artifacts`，里面包含 `recording.mp4` 视频文件。

## 注意事项

- ⚠️ 请确保你的账号密码正确
- ⚠️ 不要过于频繁运行，以免被论坛封禁
- ⚠️ 本项目仅供学习交流使用

## TuneHub 自动签到

当 `TARGET_URL` 或 `TARGET_URL_2` 包含 `linux.do` 时，程序会在完成Linux DO 任务后自动进行 TuneHub 签到。

**无需额外配置**，只要你的 `TARGET_URL` 是 `https://linux.do`，签到功能就会自动启用。

## AnyRouter 自动签到

当 `TARGET_URL` 或 `TARGET_URL_2` 包含 `linux.do` 时，程序会在 TuneHub 签到完成后自动进行 AnyRouter 签到。

**无需额外配置**，只要你的 `TARGET_URL` 是 `https://linux.do`，签到功能就会自动启用。

## GGBOOM 自动签到

当 `TARGET_URL` 或 `TARGET_URL_2` 包含 `linux.do` 时，程序会在 AnyRouter 签到完成后自动进行 GGBOOM（sign.qaq.al）签到。

**无需额外配置**，只要你的 `TARGET_URL` 是 `https://linux.do`，签到功能就会自动启用。

## License

MIT
