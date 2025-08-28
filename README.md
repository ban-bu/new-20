# AI Co-Creation 服装消费者行为实验平台

一个基于Streamlit构建的AI协作服装设计实验平台，用于研究AI推荐等级对创意的影响。

## 功能特性

- 🎨 交互式服装设计界面
- 🤖 AI驱动的设计推荐系统
- 📊 用户行为数据收集
- 🧪 多种实验组设置
- 📱 响应式用户界面

## 部署到Railway

### 1. 准备工作

确保你有以下账户：
- [Railway](https://railway.app) 账户
- OpenAI API密钥（通过DeepBricks.ai）

### 2. 一键部署

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/YourTemplateId)

或者手动部署：

1. Fork 这个仓库到你的GitHub账户
2. 在Railway中创建新项目
3. 连接你的GitHub仓库
4. 设置环境变量（见下方）
5. 部署应用

### 3. 环境变量配置

在Railway的项目设置中添加以下环境变量：

```
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_BASE_URL=https://api.deepbricks.ai/v1/
```

### 4. 自动部署

Railway会自动检测到以下文件并进行部署：
- `Procfile` - 指定启动命令
- `requirements.txt` - Python依赖
- `railway.json` - Railway配置

## 本地开发

### 1. 克隆仓库

```bash
git clone <repository-url>
cd study1-low-ali-main
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 环境配置

创建 `.env` 文件：

```
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_BASE_URL=https://api.deepbricks.ai/v1/
```

### 4. 运行应用

```bash
streamlit run app.py
```

应用将在 `http://localhost:8501` 启动。

## 技术栈

- **前端框架**: Streamlit
- **AI API**: OpenAI (通过DeepBricks.ai)
- **图像处理**: Pillow, OpenCV
- **SVG处理**: cairosvg, svglib
- **数据处理**: pandas, numpy
- **部署平台**: Railway

## 项目结构

```
study1-low-ali-main/
├── app.py                      # 主应用文件
├── welcome_page.py             # 欢迎页面
├── survey_page.py              # 调查问卷页面
├── low_no_explanation.py       # 低推荐无解释模式
├── low_with_explanation.py     # 低推荐有解释模式
├── high_no_explanation.py      # 高推荐无解释模式
├── high_with_explanation.py    # 高推荐有解释模式
├── fabric_texture.py           # 面料纹理处理
├── svg_utils.py                # SVG工具函数
├── experiment_data.csv         # 实验数据存储
├── white_shirt.png             # 基础T恤图像
├── Procfile                    # Railway启动配置
├── railway.json                # Railway部署配置
├── requirements.txt            # Python依赖
└── README.md                   # 项目说明
```

## 故障排除

### 常见问题

1. **SVG渲染失败**
   - 检查 `cairosvg` 依赖是否正确安装
   - 使用备选方案 `svglib` + `reportlab`

2. **API调用失败**
   - 验证 `OPENAI_API_KEY` 环境变量是否正确设置
   - 检查API余额和访问权限

3. **图像处理错误**
   - 确保 `Pillow` 和 `opencv-python-headless` 正确安装
   - 检查图像文件路径和格式

### 日志查看

在Railway中查看应用日志：
1. 进入项目页面
2. 点击 "Deployments" 标签
3. 选择最新部署查看日志

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License