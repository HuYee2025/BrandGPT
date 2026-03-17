"""
餐饮品牌AI顾问系统 - Flask主应用
"""
import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime
from config import config
from models import db, User, Conversation, Message, Report, ModelConfig
from ai_engine import (
    SYSTEM_PROMPT,
    generate_question_prompt,
    generate_report_prompt,
    get_initial_question,
    get_model_client
)

app = Flask(__name__)
app.config.from_object(config[os.getenv('FLASK_ENV', 'default')])

# 初始化扩展
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# 创建数据库
with app.app_context():
    db.create_all()


# ==================== 路由 ====================

@app.route('/')
def index():
    """首页"""
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    return render_template('index.html')


# ==================== 用户认证 ====================

@app.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # 检查用户是否存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'error')
            return redirect(url_for('register'))

        # 创建用户
        user = User(username=username, email=email)
        user.set_password(password)

        # 设置默认API Key（如果有环境变量）
        if os.getenv('OPENAI_API_KEY'):
            user.api_key = os.getenv('OPENAI_API_KEY')
            user.model_provider = 'openai'
            user.model_name = 'gpt-4'

        db.session.add(user)
        db.session.commit()

        flash('注册成功，请登录', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash('登录成功', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('chat'))
        else:
            flash('用户名或密码错误', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """退出登录"""
    logout_user()
    flash('已退出登录', 'info')
    return redirect(url_for('login'))


# ==================== AI问答 ====================

@app.route('/chat')
@login_required
def chat():
    """AI问答页面"""
    # 获取用户最近的对话
    conversations = Conversation.query.filter_by(user_id=current_user.id)\
        .order_by(Conversation.updated_at.desc()).limit(10).all()
    return render_template('chat.html', conversations=conversations)


@app.route('/api/chat/new', methods=['POST'])
@login_required
def new_conversation():
    """创建新对话"""
    conversation = Conversation(
        user_id=current_user.id,
        title='新对话'
    )
    db.session.add(conversation)
    db.session.commit()

    # 添加系统消息
    system_msg = Message(
        conversation_id=conversation.id,
        role='system',
        content=SYSTEM_PROMPT
    )
    db.session.add(system_msg)

    # 添加初始问题
    initial_question = get_initial_question()
    assistant_msg = Message(
        conversation_id=conversation.id,
        role='assistant',
        content=initial_question
    )
    db.session.add(assistant_msg)
    db.session.commit()

    return jsonify({
        'conversation_id': conversation.id,
        'message': initial_question
    })


@app.route('/api/chat/<int:conversation_id>/send', methods=['POST'])
@login_required
def send_message(conversation_id):
    """发送消息"""
    data = request.get_json()
    user_message = data.get('message', '')

    conversation = Conversation.query.get_or_404(conversation_id)
    if conversation.user_id != current_user.id:
        return jsonify({'error': '无权访问'}), 403

    # 保存用户消息
    user_msg = Message(
        conversation_id=conversation.id,
        role='user',
        content=user_message
    )
    db.session.add(user_msg)
    db.session.commit()

    # 获取对话历史
    messages = Message.query.filter_by(conversation_id=conversation.id)\
        .order_by(Message.created_at).all()

    # 构建消息列表
    chat_messages = []
    for msg in messages:
        chat_messages.append({
            'role': msg.role,
            'content': msg.content
        })

    # 获取模型客户端
    api_key = current_user.api_key or os.getenv('OPENAI_API_KEY', '')
    provider = current_user.model_provider or 'openai'
    model_name = current_user.model_name or 'gpt-4'

    if not api_key:
        return jsonify({'error': '请先配置API Key'}), 400

    try:
        client = get_model_client(provider, api_key, model_name)

        # 调用AI
        response = client.chat(chat_messages, stream=False)

        # 保存AI响应
        assistant_msg = Message(
            conversation_id=conversation.id,
            role='assistant',
            content=response
        )
        db.session.add(assistant_msg)

        # 更新对话时间
        conversation.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'message': response,
            'conversation_id': conversation.id
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat/<int:conversation_id>/stream', methods=['POST'])
@login_required
def stream_chat(conversation_id):
    """流式聊天"""
    data = request.get_json()
    user_message = data.get('message', '')

    conversation = Conversation.query.get_or_404(conversation_id)
    if conversation.user_id != current_user.id:
        return jsonify({'error': '无权访问'}), 403

    # 保存用户消息
    user_msg = Message(
        conversation_id=conversation.id,
        role='user',
        content=user_message
    )
    db.session.add(user_msg)
    db.session.commit()

    # 获取对话历史
    messages = Message.query.filter_by(conversation_id=conversation.id)\
        .order_by(Message.created_at).all()

    # 构建消息列表
    chat_messages = []
    for msg in messages:
        chat_messages.append({
            'role': msg.role,
            'content': msg.content
        })

    # 获取模型客户端
    api_key = current_user.api_key or os.getenv('OPENAI_API_KEY', '')
    provider = current_user.model_provider or 'openai'
    model_name = current_user.model_name or 'gpt-4'

    if not api_key:
        return jsonify({'error': '请先配置API Key'}), 400

    def generate():
        try:
            client = get_model_client(provider, api_key, model_name)
            full_response = ''

            for chunk in client.chat(chat_messages, stream=True):
                full_response += chunk
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"

            # 保存完整响应
            assistant_msg = Message(
                conversation_id=conversation.id,
                role='assistant',
                content=full_response
            )
            db.session.add(assistant_msg)

            conversation.updated_at = datetime.utcnow()
            db.session.commit()

            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/conversations')
@login_required
def get_conversations():
    """获取对话列表"""
    conversations = Conversation.query.filter_by(user_id=current_user.id)\
        .order_by(Conversation.updated_at.desc()).all()

    return jsonify([{
        'id': c.id,
        'title': c.title,
        'updated_at': c.updated_at.strftime('%Y-%m-%d %H:%M')
    } for c in conversations])


@app.route('/api/conversations/<int:conversation_id>')
@login_required
def get_conversation(conversation_id):
    """获取对话详情"""
    conversation = Conversation.query.get_or_404(conversation_id)
    if conversation.user_id != current_user.id:
        return jsonify({'error': '无权访问'}), 403

    messages = Message.query.filter_by(conversation_id=conversation.id)\
        .order_by(Message.created_at).all()

    return jsonify([{
        'id': m.id,
        'role': m.role,
        'content': m.content,
        'created_at': m.created_at.strftime('%Y-%m-%d %H:%M')
    } for m in messages])


# ==================== 报告生成 ====================

@app.route('/report/<int:report_id>')
@login_required
def view_report(report_id):
    """查看报告"""
    report = Report.query.get_or_404(report_id)
    if report.user_id != current_user.id:
        return redirect(url_for('chat'))

    return render_template('report.html', report=report)


@app.route('/api/report/generate/<int:conversation_id>', methods=['POST'])
@login_required
def generate_report(conversation_id):
    """生成报告"""
    conversation = Conversation.query.get_or_404(conversation_id)
    if conversation.user_id != current_user.id:
        return jsonify({'error': '无权访问'}), 403

    # 获取所有消息
    messages = Message.query.filter_by(conversation_id=conversation.id)\
        .order_by(Message.created_at).all()

    # 构建对话历史
    conversation_history = []
    for msg in messages:
        if msg.role in ['user', 'assistant']:
            conversation_history.append({
                'role': msg.role,
                'content': msg.content
            })

    # 获取模型客户端
    api_key = current_user.api_key or os.getenv('OPENAI_API_KEY', '')
    provider = current_user.model_provider or 'openai'
    model_name = current_user.model_name or 'gpt-4'

    if not api_key:
        return jsonify({'error': '请先配置API Key'}), 400

    try:
        client = get_model_client(provider, api_key, model_name)

        # 生成报告
        prompt = generate_report_prompt(conversation_history)
        report_content = client.chat([
            {'role': 'system', 'content': '你是一个专业的商业计划书撰写专家。请生成专业、详实的商业计划书。'},
            {'role': 'user', 'content': prompt}
        ])

        # 保存报告
        report = Report(
            user_id=current_user.id,
            conversation_id=conversation.id,
            title=f"商业计划书 - {datetime.now().strftime('%Y-%m-%d')}",
            content=report_content,
            html_content=markdown_to_html(report_content)
        )
        db.session.add(report)

        # 更新对话标题
        conversation.title = '已完成'
        db.session.commit()

        return jsonify({
            'report_id': report.id,
            'content': report_content
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def markdown_to_html(markdown_text):
    """简单的Markdown转HTML（实际项目中建议用markdown库）"""
    import re

    # 标题
    text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', markdown_text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)

    # 粗体
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

    # 列表
    text = re.sub(r'^- (.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)

    # 段落
    text = re.sub(r'\n\n', '</p><p>', text)
    text = '<p>' + text + '</p>'

    return text


@app.route('/api/report/download/<int:report_id>')
@login_required
def download_report(report_id):
    """下载报告"""
    report = Report.query.get_or_404(report_id)
    if report.user_id != current_user.id:
        return jsonify({'error': '无权访问'}), 403

    # 生成Word文档
    from docx import Document
    from io import BytesIO

    doc = Document()
    doc.add_heading(report.title, 0)

    # 简单解析内容
    lines = report.content.split('\n')
    for line in lines:
        if line.strip():
            if line.startswith('#'):
                doc.add_heading(line.replace('#', '').strip(), level=2)
            elif line.startswith('-'):
                doc.add_paragraph(line.strip(), style='List Bullet')
            else:
                doc.add_paragraph(line.strip())

    # 保存到内存
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    from flask import send_file
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{report.title}.docx",
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )


# ==================== 设置 ====================

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """模型配置页面"""
    if request.method == 'POST':
        current_user.model_provider = request.form.get('provider', 'openai')
        current_user.model_name = request.form.get('model_name', 'gpt-4')
        current_user.api_key = request.form.get('api_key', '')

        db.session.commit()
        flash('配置已保存', 'success')
        return redirect(url_for('settings'))

    return render_template('settings.html',
                         user=current_user,
                         providers=[
                             {'id': 'openai', 'name': 'OpenAI (GPT-4)'},
                             {'id': 'claude', 'name': 'Claude'}
                         ])


# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', error='页面不存在'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', error='服务器错误'), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
