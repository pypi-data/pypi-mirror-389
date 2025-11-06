# 使用示例 / Usage Examples

## 基本使用 / Basic Usage

### 1. 安装并打补丁 / Install and Patch

```bash
# 安装包 / Install package
pip install -e .

# 打补丁 / Patch Flower
flower-i18n-patch
```

### 2. 启动 Flower / Start Flower

```bash
# 基本启动 / Basic start
celery -A your_app flower

# 自定义端口 / Custom port
celery -A your_app flower --port=5555

# 指定 broker / Specify broker
celery -A your_app flower --broker=redis://localhost:6379/0
```

### 3. 访问界面 / Access Interface

打开浏览器访问：`http://localhost:5555`

在导航栏点击语言图标切换中英文。

Open browser: `http://localhost:5555`

Click the language icon in the navbar to switch between Chinese and English.

---

## 高级示例 / Advanced Examples

### 示例 1: 在自定义视图中使用 i18n / Example 1: Use i18n in Custom Views

```python
# custom_handler.py
from flower.views import BaseHandler
from flower_i18n import I18nHandler

class CustomDashboardHandler(I18nHandler, BaseHandler):
    def get(self):
        # 获取翻译文本 / Get translated text
        title = self._('workers.title')
        status = self._('workers.status')

        self.render('custom_dashboard.html',
                   title=title,
                   status=status)
```

### 示例 2: 在模板中使用翻译 / Example 2: Use Translations in Templates

```html
<!-- custom_dashboard.html -->
<!DOCTYPE html>
<html>
<head>
    <title>{{ _('workers.title') }}</title>
</head>
<body>
    <h1>{{ _('workers.title') }}</h1>
    <p>{{ _('workers.status') }}: {{ _('state.success') }}</p>
</body>
</html>
```

### 示例 3: 添加自定义翻译 / Example 3: Add Custom Translations

```python
# 在 flower_i18n/locales/zh_CN/messages.json 中添加：
{
  "custom.welcome": "欢迎使用",
  "custom.dashboard": "仪表板",
  "custom.statistics": "统计信息"
}

# 在 flower_i18n/locales/en_US/messages.json 中添加：
{
  "custom.welcome": "Welcome",
  "custom.dashboard": "Dashboard",
  "custom.statistics": "Statistics"
}
```

### 示例 4: 编程方式使用 i18n / Example 4: Programmatic i18n Usage

```python
from flower_i18n import get_i18n

# 获取 i18n 实例 / Get i18n instance
i18n = get_i18n()

# 切换语言 / Switch language
i18n.set_locale('zh_CN')

# 获取翻译 / Get translation
text = i18n.get('nav.workers')  # 返回 "工作进程"

# 获取可用语言列表 / Get available locales
locales = i18n.get_available_locales()  # ['en_US', 'zh_CN']
```

### 示例 5: 在 Celery 任务中使用 / Example 5: Use in Celery Tasks

```python
from celery import Celery
from flower_i18n import get_i18n

app = Celery('tasks', broker='redis://localhost:6379/0')

@app.task
def send_notification(user_locale='en_US'):
    i18n = get_i18n()

    # 根据用户语言发送通知 / Send notification in user's language
    if user_locale == 'zh_CN':
        message = i18n.get('tasks.state', locale='zh_CN')
    else:
        message = i18n.get('tasks.state', locale='en_US')

    print(f"Sending notification: {message}")
    return message
```

### 示例 6: 完整的 Flower 配置 / Example 6: Complete Flower Configuration

```python
# flower_config.py
from flower import Flower
from flower_i18n import setup_i18n
from celery import Celery

# 创建 Celery 应用 / Create Celery app
celery_app = Celery(
    'myapp',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1'
)

# 配置 Flower / Configure Flower
def start_flower():
    # 设置 i18n / Setup i18n
    i18n_helpers = setup_i18n(None)

    # 启动 Flower / Start Flower
    flower_app = Flower(
        capp=celery_app,
        port=5555,
        address='0.0.0.0'
    )

    flower_app.start()

if __name__ == '__main__':
    start_flower()
```

### 示例 7: Docker 部署 / Example 7: Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装依赖 / Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装 flower-i18n / Install flower-i18n
COPY flower-i18n/ /app/flower-i18n/
RUN cd /app/flower-i18n && pip install -e .

# 打补丁 / Patch Flower
RUN flower-i18n-patch

# 复制应用代码 / Copy app code
COPY . .

# 暴露端口 / Expose port
EXPOSE 5555

# 启动命令 / Start command
CMD ["celery", "-A", "your_app", "flower", "--port=5555", "--address=0.0.0.0"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  flower:
    build: .
    ports:
      - "5555:5555"
    depends_on:
      - redis
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
```

---

## 测试示例 / Test Examples

### 测试语言切换 / Test Language Switching

```python
# test_i18n.py
import pytest
from flower_i18n import get_i18n

def test_language_switching():
    i18n = get_i18n()

    # 测试英文 / Test English
    i18n.set_locale('en_US')
    assert i18n.get('nav.workers') == 'Workers'

    # 测试中文 / Test Chinese
    i18n.set_locale('zh_CN')
    assert i18n.get('nav.workers') == '工作进程'

def test_fallback():
    i18n = get_i18n()

    # 测试不存在的键，应该返回键本身 / Test non-existent key
    assert i18n.get('non.existent.key') == 'non.existent.key'

def test_available_locales():
    i18n = get_i18n()
    locales = i18n.get_available_locales()

    assert 'en_US' in locales
    assert 'zh_CN' in locales
```

运行测试 / Run tests:

```bash
pytest test_i18n.py -v
```

---

## 故障排除 / Troubleshooting

### 问题 1: 看不到语言切换按钮 / Issue 1: Can't see language switcher

```bash
# 重新打补丁 / Re-patch
flower-i18n-unpatch
flower-i18n-patch

# 清除浏览器缓存并刷新 / Clear browser cache and refresh
# Ctrl+F5 (Windows/Linux) or Cmd+Shift+R (Mac)
```

### 问题 2: 翻译没有生效 / Issue 2: Translations not working

```bash
# 检查安装 / Check installation
pip show flower-i18n

# 检查补丁状态 / Check patch status
ls -la $(python -c "import flower; print(flower.__path__[0])")/templates/

# 应该看到 templates_backup 目录 / Should see templates_backup directory
```

### 问题 3: 自定义翻译不工作 / Issue 3: Custom translations not working

```python
# 重新加载翻译 / Reload translations
from flower_i18n.i18n import _i18n_instance
_i18n_instance = None  # 重置实例 / Reset instance

from flower_i18n import get_i18n
i18n = get_i18n()  # 重新加载 / Reload
```

---

## 更多资源 / More Resources

- [Flower 官方文档 / Official Docs](https://flower.readthedocs.io/)
- [Celery 官方文档 / Official Docs](https://docs.celeryproject.org/)
- [项目 GitHub / Project GitHub](https://github.com/yourusername/flower-i18n)