# 🚀 GitHub + Railway 部署指南

## 完整部署步骤

### 第一步：将项目推送到GitHub

#### 1.1 在GitHub上创建新仓库

1. 访问 [GitHub.com](https://github.com)
2. 点击右上角的 "+" 号，选择 "New repository"
3. 填写仓库信息：
   - **Repository name**: `ai-tshirt-design-flask`
   - **Description**: `AI T-shirt Design Generator - Flask Version`
   - **Visibility**: Public (推荐) 或 Private
   - ⚠️ **不要**初始化README、.gitignore或license（因为我们已经有了）
4. 点击 "Create repository"

#### 1.2 推送代码到GitHub

在您的项目目录中运行以下命令：

```bash
# 1. 添加GitHub远程仓库（替换为您的用户名和仓库名）
git remote add origin https://github.com/YOUR_USERNAME/ai-tshirt-design-flask.git

# 2. 推送代码到GitHub
git branch -M main
git push -u origin main
```

**示例：**
```bash
# 假设您的GitHub用户名是 "yourname"
git remote add origin https://github.com/yourname/ai-tshirt-design-flask.git
git branch -M main
git push -u origin main
```

#### 1.3 验证推送成功

刷新GitHub页面，您应该能看到所有项目文件已上传。

---

### 第二步：在Railway部署项目

#### 2.1 注册/登录Railway

1. 访问 [Railway.app](https://railway.app)
2. 点击 "Start a New Project" 或 "Login"
3. 使用GitHub账号登录（推荐）

#### 2.2 创建新项目

1. 在Railway控制台，点击 "New Project"
2. 选择 "Deploy from GitHub repo"
3. 如果是第一次使用，会要求授权GitHub访问权限，点击 "Configure GitHub App"
4. 选择要授权的仓库（可以选择所有仓库或特定仓库）

#### 2.3 选择仓库

1. 在仓库列表中找到您的 `ai-tshirt-design-flask` 仓库
2. 点击 "Deploy Now"

#### 2.4 配置项目

Railway会自动检测到这是一个Python项目，并：
- 自动使用 `Procfile` 配置
- 安装 `requirements.txt` 中的依赖
- 启动Flask应用

#### 2.5 等待部署完成

1. 部署过程通常需要2-5分钟
2. 您可以在 "Deployments" 标签中查看部署日志
3. 部署成功后，会显示绿色的 "Success" 状态

#### 2.6 获取部署URL

1. 在项目面板中，点击 "Settings" 标签
2. 在 "Domains" 部分，点击 "Generate Domain"
3. Railway会生成一个免费的子域名，如：`your-app-name.up.railway.app`
4. 点击该URL访问您的应用

---

### 第三步：验证部署

#### 3.1 测试应用功能

1. 访问生成的URL
2. 您应该看到AI T恤设计生成器界面
3. 输入一些关键词（如："休闲，自然，蓝色"）
4. 点击"生成T恤设计"
5. 等待1-3分钟，应该能看到20个AI生成的设计

#### 3.2 检查日志（如果有问题）

1. 在Railway项目面板，点击 "Deployments"
2. 点击最新的部署记录
3. 查看 "Build Logs" 和 "Deploy Logs"
4. 如果有错误，日志会显示详细信息

---

### 常见问题和解决方案

#### Q1: 推送到GitHub时出现权限错误

**解决方案：**
```bash
# 使用个人访问令牌（如果启用了2FA）
# 1. 在GitHub Settings > Developer settings > Personal access tokens > Tokens (classic)
# 2. 生成新token，选择 "repo" 权限
# 3. 使用token作为密码
```

#### Q2: Railway部署失败

**常见原因和解决方案：**

1. **依赖安装失败**
   - 检查 `requirements.txt` 是否正确
   - 确保所有包版本兼容

2. **启动命令错误**
   - 确认 `Procfile` 内容为：`web: python flask_app.py`
   - 检查 `flask_app.py` 中端口配置

3. **文件缺失**
   - 确保推送了所有必需文件
   - 检查 `.gitignore` 没有忽略重要文件

#### Q3: 应用启动后无法访问

**检查项目：**
1. 确认Flask应用监听 `0.0.0.0` 而不是 `127.0.0.1`
2. 确认使用环境变量 `PORT` 或默认端口

#### Q4: API调用失败

**检查项目：**
1. 网络连接是否正常
2. API密钥是否有效
3. 查看Railway日志中的错误信息

---

### 更新部署

#### 本地修改后重新部署

```bash
# 1. 提交更改
git add .
git commit -m "Update: description of changes"

# 2. 推送到GitHub
git push origin main

# 3. Railway会自动重新部署
```

---

### 成本说明

- **GitHub**: 公开仓库免费
- **Railway**: 
  - 免费计划：每月500小时运行时间
  - 包含自定义域名
  - 足够个人项目和测试使用

---

### 🎉 完成！

按照以上步骤，您的AI T恤设计应用将成功部署到云端，可以通过互联网访问。

**部署后的URL格式：** `https://your-app-name.up.railway.app`

**功能确认：**
- ✅ 网页正常加载
- ✅ 可以输入关键词
- ✅ 可以生成AI设计
- ✅ 响应式设计在移动设备上正常工作

如果遇到任何问题，请检查Railway的部署日志获取详细错误信息。
