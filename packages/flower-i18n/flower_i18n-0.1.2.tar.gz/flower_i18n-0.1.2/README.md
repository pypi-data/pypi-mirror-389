# Flower i18n

🌍 为 Flower Celery 监控工具提供国际化（i18n）支持，让你的 Flower 界面支持中英文切换！

[English](#english) | [中文](#chinese)

---

<a name="chinese"></a>
## 中文文档

### 简介

Flower i18n 是一个为 [Flower](https://github.com/mher/flower) Celery 监控工具添加国际化支持的 Python 包。它让你可以在 Flower 的 Web 界面中轻松切换中文和英文。

### 特性

- ✅ 支持中英文界面切换
- ✅ 自动检测浏览器语言
- ✅ 记住用户语言偏好（通过 Cookie）
- ✅ 简单的安装和配置流程
- ✅ 不影响 Flower 的原有功能
- ✅ 可扩展的翻译系统

### 安装

#### 从源码安装

```bash
# 克隆或下载此项目
cd flower-i18n

# 安装包
pip install -e .
```

#### 从 PyPI 安装（待发布）

```bash
pip install flower-i18n
```

### 快速开始

#### 1. 自动打补丁（推荐）

安装完成后，运行自动打补丁命令：

```bash
flower-i18n-patch
```

这个命令会：
- 自动备份原始的 Flower 模板文件
- 修改必要的模板以支持国际化
- 复制必要的静态文件（JavaScript）

#### 2. 启动 Flower

正常启动 Flower：

```bash
celery -A your_app flower
```

或者使用自定义端口：

```bash
celery -A your_app flower --port=5555
```

#### 3. 使用语言切换

打开 Flower 界面后，你会在导航栏看到一个语言切换下拉菜单。点击即可在中英文之间切换。

### 高级用法

#### 在自定义 Handler 中使用

如果你有自定义的 Flower Handler，可以这样使用 i18n 功能：

```python
from flower.views import BaseHandler
from flower_i18n import I18nHandler

class MyCustomHandler(I18nHandler, BaseHandler):
    def get(self):
        # 使用 self._() 方法翻译文本
        translated_text = self._('nav.workers')
        self.render('my_template.html', text=translated_text)
```

#### 添加新的翻译

你可以扩展翻译文件来添加更多语言或翻译项。

编辑翻译文件：
- 英文：`flower_i18n/locales/en_US/messages.json`
- 中文：`flower_i18n/locales/zh_CN/messages.json`

格式如下：

```json
{
  "my.key": "My Translation"
}
```

#### 添加新语言

1. 在 `flower_i18n/locales/` 下创建新的语言目录，例如 `ja_JP`（日语）
2. 在该目录下创建 `messages.json` 文件
3. 添加翻译内容
4. 修改 `flower_i18n/static/js/i18n.js` 添加新语言选项

### 卸载

如果你想移除 i18n 支持并恢复原始的 Flower：

```bash
flower-i18n-unpatch
```

这会恢复所有原始的模板文件。

然后卸载包：

```bash
pip uninstall flower-i18n
```

### 项目结构

```
flower-i18n/
├── flower_i18n/
│   ├── __init__.py          # 包初始化
│   ├── i18n.py              # 核心国际化逻辑
│   ├── patcher.py           # 模板打补丁工具
│   ├── locales/
│   │   ├── en_US/
│   │   │   └── messages.json  # 英文翻译
│   │   └── zh_CN/
│   │       └── messages.json  # 中文翻译
│   ├── static/
│   │   └── js/
│   │       └── i18n.js      # 前端语言切换逻辑
│   └── templates/           # 自定义模板（如需要）
├── pyproject.toml           # 项目配置
├── setup.py                 # 安装脚本
├── LICENSE                  # MIT 许可证
└── README.md               # 本文档
```

### 贡献

欢迎贡献！如果你想添加新的语言支持或改进翻译，请：

1. Fork 本项目
2. 创建你的功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

### 常见问题

**Q: 安装后看不到语言切换按钮？**

A: 确保你运行了 `flower-i18n-patch` 命令，并且重启了 Flower。

**Q: 切换语言后没有变化？**

A: 请刷新页面（Ctrl+F5 或 Cmd+Shift+R）清除缓存。

**Q: 如何添加更多翻译项？**

A: 编辑 `flower_i18n/locales/*/messages.json` 文件，添加你需要的键值对。

**Q: 会影响 Flower 的性能吗？**

A: 不会。i18n 只在页面加载时执行，对性能影响可忽略不计。

### 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

### 致谢

- [Flower](https://github.com/mher/flower) - 优秀的 Celery 监控工具
- [Celery](https://github.com/celery/celery) - 分布式任务队列

---

<a name="english"></a>
## English Documentation

### Introduction

Flower i18n is a Python package that adds internationalization (i18n) support to the [Flower](https://github.com/mher/flower) Celery monitoring tool. It enables easy language switching between Chinese and English in the Flower web interface.

### Features

- ✅ Chinese and English language switching
- ✅ Automatic browser language detection
- ✅ Remember user language preference (via Cookie)
- ✅ Simple installation and configuration
- ✅ Does not affect Flower's original functionality
- ✅ Extensible translation system

### Installation

#### Install from source

```bash
# Clone or download this project
cd flower-i18n

# Install the package
pip install -e .
```

#### Install from PyPI (coming soon)

```bash
pip install flower-i18n
```

### Quick Start

#### 1. Auto-patch (Recommended)

After installation, run the auto-patch command:

```bash
flower-i18n-patch
```

This command will:
- Automatically backup original Flower template files
- Modify necessary templates to support i18n
- Copy required static files (JavaScript)

#### 2. Start Flower

Start Flower normally:

```bash
celery -A your_app flower
```

Or with a custom port:

```bash
celery -A your_app flower --port=5555
```

#### 3. Use Language Switcher

After opening the Flower interface, you'll see a language switcher dropdown in the navigation bar. Click to switch between Chinese and English.

### Advanced Usage

#### Using in Custom Handlers

If you have custom Flower handlers, you can use i18n features like this:

```python
from flower.views import BaseHandler
from flower_i18n import I18nHandler

class MyCustomHandler(I18nHandler, BaseHandler):
    def get(self):
        # Use self._() method to translate text
        translated_text = self._('nav.workers')
        self.render('my_template.html', text=translated_text)
```

#### Adding New Translations

You can extend translation files to add more languages or translation entries.

Edit translation files:
- English: `flower_i18n/locales/en_US/messages.json`
- Chinese: `flower_i18n/locales/zh_CN/messages.json`

Format:

```json
{
  "my.key": "My Translation"
}
```

#### Adding New Languages

1. Create a new language directory under `flower_i18n/locales/`, e.g., `ja_JP` (Japanese)
2. Create a `messages.json` file in that directory
3. Add translation content
4. Modify `flower_i18n/static/js/i18n.js` to add the new language option

### Uninstall

If you want to remove i18n support and restore the original Flower:

```bash
flower-i18n-unpatch
```

This will restore all original template files.

Then uninstall the package:

```bash
pip uninstall flower-i18n
```

### Project Structure

```
flower-i18n/
├── flower_i18n/
│   ├── __init__.py          # Package initialization
│   ├── i18n.py              # Core i18n logic
│   ├── patcher.py           # Template patching tool
│   ├── locales/
│   │   ├── en_US/
│   │   │   └── messages.json  # English translations
│   │   └── zh_CN/
│   │       └── messages.json  # Chinese translations
│   ├── static/
│   │   └── js/
│   │       └── i18n.js      # Frontend language switching logic
│   └── templates/           # Custom templates (if needed)
├── pyproject.toml           # Project configuration
├── setup.py                 # Setup script
├── LICENSE                  # MIT License
└── README.md               # This document
```

### Contributing

Contributions are welcome! If you want to add new language support or improve translations:

1. Fork this project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### FAQ

**Q: Can't see the language switcher after installation?**

A: Make sure you ran the `flower-i18n-patch` command and restarted Flower.

**Q: No change after switching language?**

A: Please refresh the page (Ctrl+F5 or Cmd+Shift+R) to clear cache.

**Q: How to add more translation entries?**

A: Edit `flower_i18n/locales/*/messages.json` files and add your key-value pairs.

**Q: Will it affect Flower's performance?**

A: No. i18n only executes during page load, with negligible performance impact.

### License

MIT License - see [LICENSE](LICENSE) file for details

### Acknowledgments

- [Flower](https://github.com/mher/flower) - Excellent Celery monitoring tool
- [Celery](https://github.com/celery/celery) - Distributed task queue

---

## Star History

If you find this project useful, please consider giving it a star ⭐️