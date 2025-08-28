# AI T恤设计生成器 - Flask版本

这是一个完全重构后的Flask版本，不再依赖于Streamlit，可以轻松部署到Railway或其他云平台。

## 主要变化

### 从Streamlit迁移到Flask
- ✅ 移除了所有Streamlit依赖
- ✅ 使用Flask作为Web框架
- ✅ 创建了现代化的HTML/CSS/JavaScript前端
- ✅ 保留了所有AI图像生成功能
- ✅ 支持Railway部署

### 功能特性
- 🎨 AI智能T恤设计生成
- 🔀 支持20个并发设计生成
- 🎯 使用阿里云DashScope和OpenAI API
- 🧵 多种面料纹理支持
- 🎨 矢量图标logo生成
- 📱 响应式设计，支持移动设备

## 安装和运行

### 本地开发

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **运行应用**
```bash
# 方式1：直接运行Flask应用
python flask_app.py

# 方式2：使用开发脚本
python run.py
```

3. **访问应用**
打开浏览器访问：`http://localhost:5000`

### Railway部署

应用已经配置好Railway部署：

1. **Procfile配置**
```
web: python flask_app.py
```

2. **环境变量**
无需特殊环境变量，所有API密钥已内置（仅供演示使用）

3. **部署步骤**
- 将代码推送到GitHub
- 在Railway中连接GitHub仓库
- Railway会自动检测Python项目并部署

## 项目结构

```
study-ali-main/
├── flask_app.py              # 主Flask应用文件
├── templates/
│   └── index.html            # HTML模板
├── static/
│   ├── css/
│   │   └── style.css         # 样式文件
│   └── images/               # 静态图像
├── fabric_texture.py         # 面料纹理处理
├── white_shirt.png          # T恤底图
├── requirements.txt         # Python依赖
├── Procfile                 # Railway部署配置
├── run.py                   # 本地开发脚本
└── README_FLASK.md          # 本文档
```

## API接口

### 生成设计
- **端点**: `POST /generate`
- **参数**: 
  ```json
  {
    "keywords": "休闲,自然,蓝色"
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "designs": [
      {
        "image": "data:image/png;base64,...",
        "info": {
          "color": {"hex": "#....", "name": "颜色名"},
          "fabric": "面料类型",
          "logo": "logo描述"
        }
      }
    ],
    "total": 20
  }
  ```

## 技术栈

- **后端**: Flask 3.0.0
- **前端**: HTML5, CSS3, Bootstrap 5, JavaScript
- **图像处理**: PIL (Pillow)
- **AI API**: OpenAI GPT-4o-mini, 阿里云DashScope
- **部署**: Railway

## 性能特性

- **高并发**: 支持最多20个并发线程
- **多API密钥**: 35个API密钥轮询使用
- **快速生成**: 通常1-3分钟生成20个设计
- **错误重试**: 自动重试机制确保稳定性

## 与原Streamlit版本的差异

| 特性 | Streamlit版本 | Flask版本 |
|------|---------------|-----------|
| Web框架 | Streamlit | Flask |
| 前端技术 | Streamlit组件 | HTML/CSS/JS |
| 部署复杂度 | 中等 | 简单 |
| 自定义能力 | 受限 | 完全自定义 |
| 性能 | 一般 | 更好 |
| 移动适配 | 基础 | 完全响应式 |

## 故障排除

### 常见问题

1. **依赖安装失败**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **API调用失败**
   - 检查网络连接
   - 确认API密钥有效
   - 查看控制台错误日志

3. **图像生成缓慢**
   - 这是正常现象，需要1-3分钟
   - 不要刷新页面或关闭浏览器

### 开发调试

启用调试模式：
```python
app.run(debug=True)
```

查看详细日志：
```bash
python flask_app.py
```

## 许可证

此项目仅供学术研究使用。

## 贡献

欢迎提交Issue和Pull Request来改进项目。
