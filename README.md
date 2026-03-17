# 品牌AI顾问系统

基于大模型的品牌商业计划书智能生成系统。

## 功能特点

- **AI智能问答**：模拟顶级投资顾问，通过多轮对话深度挖掘用户需求
- **动态追问**：根据用户回答智能生成针对性问题，而非静态问卷
- **个性化报告**：AI自动整合信息，生成定制化商业计划书
- **多模型支持**：支持OpenAI、Claude、DeepSeek等多种大模型API
- **灵活配置**：用户可自定义API Key和模型参数

## 技术栈

- 后端：Python + Flask
- 数据库：SQLite
- 前端：HTML + CSS + JavaScript
- AI：大模型API (OpenAI/Claude/DeepSeek)

## 部署说明

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动应用
python app.py
```

访问 http://localhost:5000

### 环境变量（可选）

- `FLASK_ENV`: 运行模式 (development/production)
- `SECRET_KEY`: Flask密钥

## 使用流程

1. 注册账号并登录
2. 在设置中配置你的AI模型API Key
3. 开始AI问答，描述你的品牌想法
4. AI会通过多轮对话深入了解你的项目
5. 信息收集完成后，生成个性化商业计划书
6. 支持下载Word/PDF格式报告

## 项目结构

```
.
├── app.py              # 主应用
├── config.py           # 配置文件
├── models.py           # 数据模型
├── requirements.txt    # 依赖列表
├── ai_engine/          # AI引擎模块
├── static/             # 静态资源
├── templates/          # HTML模板
└── data/               # 数据目录
```

## 许可证

MIT License
