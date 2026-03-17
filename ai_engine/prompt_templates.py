"""
AI提示词模板
"""

# 品牌顾问系统提示词
SYSTEM_PROMPT = """你是品牌创业咨询顾问，用户正在创建一个新项目。你需要通过对话逐步了解用户的创业想法。

重要规则：
1. 每次只问一个问题，不要一次问多个问题
2. 问题要简洁，像人和人聊天一样
3. 等用户回答后再问下一个问题
4. 循序渐进，先了解基本信息，再深入细节
5. 如果用户回答模糊或简略，追问澄清
6. 保持友好、专业的语气，像一个资深顾问在聊天

对话流程：
- 用户描述想法后，先确认核心产品/服务是什么
- 然后问目标客户群体
- 再问商业模式和盈利方式
- 接着问竞争情况
- 最后问团队和资金

当收集到足够信息后（至少5轮对话），提示用户可以生成商业计划书。

记住：一次只问一个问题！"""

# 维度定义
DIMENSIONS = {
    'product': {
        'name': '产品/服务',
        'key_questions': [
            '请描述你的核心产品是什么？',
            '你的产品有哪些独特卖点？',
            '定价策略是怎样的？'
        ]
    },
    'market': {
        'name': '市场/用户',
        'key_questions': [
            '你的目标客群是谁？',
            '目标市场有多大？',
            '主要竞争对手有哪些？'
        ]
    },
    'brand': {
        'name': '品牌定位',
        'key_questions': [
            '品牌名称和故事是什么？',
            '如何与竞争对手区分？',
            '品牌的核心价值主张？'
        ]
    },
    'operation': {
        'name': '运营/供应链',
        'key_questions': [
            '计划在哪里开店？',
            '需要多少员工？',
            '供应链如何解决？'
        ]
    },
    'finance': {
        'name': '成本/财务',
        'key_questions': [
            '总投资预算多少？',
            '预计多久回本？',
            '盈利模型是怎样的？'
        ]
    },
    'risk': {
        'name': '风险/挑战',
        'key_questions': [
            '你认为最大的风险是什么？',
            '如何应对竞争？',
            '有什么应对预案？'
        ]
    },
    'team': {
        'name': '团队/管理',
        'key_questions': [
            '核心团队成员有哪些？',
            '股权如何分配？',
            '有什么行业经验？'
        ]
    }
}


def generate_question_prompt(conversation_history: list, collected_info: dict = None) -> str:
    """
    生成追问提示词
    conversation_history: 对话历史列表，每项为 {'role': 'user'/'assistant', 'content': '...'}
    collected_info: 已收集的信息字典
    """
    history_text = ""
    for msg in conversation_history[-6:]:  # 只取最近6条
        role = "用户" if msg['role'] == 'user' else "顾问"
        history_text += f"{role}: {msg['content']}\n\n"

    # 分析已收集的信息
    covered_dims = []
    if collected_info:
        covered_dims = [k for k, v in collected_info.items() if v]

    prompt = f"""基于以下对话历史和已收集信息，请生成下一个问题：

对话历史：
{history_text}

已覆盖维度：{', '.join(covered_dims) if covered_dims else '暂无'}

请生成一个针对性的追问，问题要具体、有深度。如果用户已经提供了足够的信息，你可以：
1. 询问下一个维度的关键问题
2. 深入挖掘已有信息中的细节
3. 提出风险或挑战相关的问题

直接输出问题，不要输出其他内容。问题要用中文。"""

    return prompt


def generate_report_prompt(conversation_history: list) -> str:
    """
    生成报告提示词
    """
    # 整理对话内容
    content = []
    for msg in conversation_history:
        role = "创业者" if msg['role'] == 'user' else "顾问"
        content.append(f"## {role}说：\n{msg['content']}\n")

    conversation_text = "\n".join(content)

    prompt = f"""基于以下对话记录，生成一份完整的品牌商业计划书。

对话记录：
{conversation_text}

请按照以下结构生成报告：

# 品牌商业计划书

## 一、项目概述
- 项目名称
- 品牌定位
- 核心价值主张

## 二、产品/服务分析
- 核心产品介绍
- 产品特色与差异化
- 定价策略

## 三、市场分析
- 目标市场规模
- 目标客群画像
- 竞争分析（SWOT分析）

## 四、运营计划
- 选址策略
- 店面规划
- 人员配置
- 供应链管理

## 五、财务预测
- 投资预算明细
- 收入预测
- 成本分析
- 盈利预测
- 回本周期

## 六、风险评估与应对
- 主要风险分析
- 应对策略

## 七、团队介绍
- 核心团队成员
- 股权分配
- 资源优势

## 八、执行计划
- 阶段目标
- 时间表

请用Markdown格式输出，内容要专业、详实、有数据支撑。"""

    return prompt


def get_initial_question() -> str:
    """获取初始问题"""
    return """你好！我是品牌AI顾问，很高兴为你服务。

在开始之前，我想先了解一下你的基本情况：

请简单描述一下你想要创建的创业项目？例如：
- 你想做什么类型的项目？（零售、服务、科技等）
- 你的品牌叫什么名字？
- 你为什么想做这个项目？

你可以用一段文字描述你的想法，越详细越好。"""
