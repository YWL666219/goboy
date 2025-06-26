import json
import streamlit as st, sqlite3, hashlib, time, pandas as pd, json
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.agents import AgentType


# 记忆管理类
class ConversationMemory:
    def __init__(self, db_path="conversation_memory.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, question TEXT, 
            answer TEXT, question_hash TEXT, data_hash TEXT, timestamp DATETIME, response_time REAL)""")
        
        cursor.execute("""CREATE TABLE IF NOT EXISTS quick_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, question_hash TEXT UNIQUE, data_hash TEXT, 
            question TEXT, answer TEXT, hit_count INTEGER DEFAULT 1, last_used DATETIME, created_at DATETIME)""")
        
        conn.commit()
        conn.close()

    def get_question_hash(self, question: str) -> str:
        return hashlib.md5(question.lower().strip().encode('utf-8')).hexdigest()

    def get_data_hash(self, df) -> str:
        try:
            data_str = str(df.shape) + str(df.columns.tolist()) + str(df.dtypes.tolist())
            return hashlib.md5(data_str.encode('utf-8')).hexdigest()
        except:
            return "unknown"

    def add_conversation(self, session_id: str, question: str, answer: str, data_hash: str, response_time: float):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        question_hash = self.get_question_hash(question)
        cursor.execute("""INSERT INTO conversations (session_id, question, answer, question_hash, data_hash, timestamp, response_time)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""", (session_id, question, answer, question_hash, data_hash, datetime.now(), response_time))
        conn.commit()
        conn.close()

    def get_quick_answer(self, question: str, data_hash: str) -> Dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        question_hash = self.get_question_hash(question)
        cursor.execute("SELECT answer, hit_count FROM quick_answers WHERE question_hash = ? AND data_hash = ?", (question_hash, data_hash))
        result = cursor.fetchone()
        if result:
            cursor.execute("UPDATE quick_answers SET hit_count = hit_count + 1, last_used = ? WHERE question_hash = ? AND data_hash = ?", 
                          (datetime.now(), question_hash, data_hash))
            conn.commit()
            conn.close()
            return {"found": True, "answer": result[0], "hit_count": result[1] + 1}
        conn.close()
        return {"found": False}

    def save_quick_answer(self, question: str, answer: str, data_hash: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        question_hash = self.get_question_hash(question)
        cursor.execute("INSERT OR REPLACE INTO quick_answers (question_hash, data_hash, question, answer, hit_count, last_used, created_at) VALUES (?, ?, ?, ?, 1, ?, ?)", 
                      (question_hash, data_hash, question, answer, datetime.now(), datetime.now()))
        conn.commit()
        conn.close()

    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT question, answer, timestamp, response_time FROM conversations WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?", (session_id, limit))
        results = cursor.fetchall()
        conn.close()
        return [{"question": row[0], "answer": row[1], "timestamp": row[2], "response_time": row[3]} for row in reversed(results)]

    def get_popular_questions(self, data_hash: str, limit: int = 5) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT question, hit_count, last_used FROM quick_answers WHERE data_hash = ? ORDER BY hit_count DESC LIMIT ?", (data_hash, limit))
        results = cursor.fetchall()
        conn.close()
        return [{"question": row[0], "hit_count": row[1], "last_used": row[2]} for row in results]


# 全局记忆管理器实例
memory_manager = ConversationMemory()

PROMPT_TEMPLATE = """你是一个专业的数据分析助手。请使用python_repl_ast工具执行pandas代码分析数据，并严格按照以下JSON格式返回最终结果：

**分析步骤：**
1. 理解用户问题
2. 编写pandas代码进行分析
3. 将结果格式化为指定的JSON格式

**返回格式要求：**
- 纯文字回答：{"answer": "简洁的回答内容"}
- 表格数据：{"table":{"columns":["列名1", "列名2"], "data":[["值1", "值2"], ["值3", "值4"]]}}
- 柱状图：{"bar":{"columns": ["类别1", "类别2"], "data":[数值1, 数值2]}}
- 折线图：{"line":{"columns": ["时间1", "时间2"], "data": [数值1, 数值2]}}

**重要规则：**
- 使用python_repl_ast工具执行pandas代码
- 字符串必须用双引号，数值不加引号
- 确保JSON格式正确，无语法错误
- 最终必须返回有效的JSON格式结果

用户问题：\n"""


@st.cache_data(ttl=1800)  # 缓存30分钟
def cached_dataframe_analysis(df_hash, query_hash, query):
    """缓存数据分析结果"""
    # 实际的分析逻辑会在dataframe_agent中执行
    return None

load_dotenv()
def get_enhanced_model(model_choice="gpt-4.1-mini"):
    """获取增强的AI模型"""
    model_configs = {
        "gpt-4o": {
            "model": "gpt-4o",
            "temperature": 0.1,
            "max_tokens": 8192
        },
        "gpt-4o-mini": {
            "model": "gpt-4o-mini",
            "temperature": 0,
            "max_tokens": 4096
        },
        "gpt-4-turbo": {
            "model": "gpt-4-turbo-preview",
            "temperature": 0.2,
            "max_tokens": 8192
        }
    }

    config = model_configs.get(model_choice, model_configs["gpt-4o-mini"])

    return ChatOpenAI(
        base_url='https://twapi.openai-hk.com/v1',
        #api_key=st.secrets['API_KEY'],
        **config
    )


def dataframe_agent(df, query, model_choice="gpt-4o-mini", use_cache=True, session_id=None):
    """数据分析智能体"""
    start_time = time.time()
    data_hash = memory_manager.get_data_hash(df)

    # 检查缓存
    if use_cache:
        quick_answer = memory_manager.get_quick_answer(query, data_hash)
        if quick_answer["found"]:
            try:
                cached_result = json.loads(quick_answer["answer"])
                if session_id:
                    memory_manager.add_conversation(session_id, query, quick_answer["answer"], data_hash, time.time() - start_time)
                return cached_result
            except json.JSONDecodeError:
                pass

    # 创建智能体
    try:
        model = get_enhanced_model(model_choice)
        agent = create_pandas_dataframe_agent(llm=model, df=df, verbose=False, agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION, allow_dangerous_code=True, return_intermediate_steps=False)
    except Exception as e:
        return {"answer": "AI智能体初始化失败，请稍后重试。"}

    # 构建提示词
    enhanced_prompt = PROMPT_TEMPLATE + f"""
数据集信息：行数{len(df)}，列数{len(df.columns)}，列名{', '.join(df.columns.tolist())}，数值列{', '.join(df.select_dtypes(include=['number']).columns.tolist())}，文本列{', '.join(df.select_dtypes(include=['object']).columns.tolist())}
用户问题：{query}"""

    try:
        response = agent.invoke({"input": enhanced_prompt})
        if "output" not in response or not response["output"]:
            return {"answer": "AI分析失败，请重新尝试"}
        
        output = response["output"].strip()
        try:
            result = json.loads(output)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{.*\}', output, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                except json.JSONDecodeError:
                    return {"answer": f"分析完成，但结果格式有误：{output[:100]}..."}
            else:
                return {"answer": f"分析结果：{output[:100]}..."}
        
        if not isinstance(result, dict):
            return {"answer": "分析完成，但返回格式不正确"}

        response_time = time.time() - start_time
        result_json = json.dumps(result, ensure_ascii=False)
        
        if session_id:
            memory_manager.add_conversation(session_id, query, result_json, data_hash, response_time)
        
        if "answer" in result or "table" in result or "bar" in result or "line" in result:
            memory_manager.save_quick_answer(query, result_json, data_hash)
        
        return result

    except Exception as err:
        error_result = {"answer": "分析过程中出现错误，请重新尝试"}
        if session_id:
            memory_manager.add_conversation(session_id, query, json.dumps(error_result, ensure_ascii=False), data_hash, time.time() - start_time)
        return error_result





# 记忆管理辅助函数
def get_session_id():
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"session_{int(time.time())}_{hash(str(time.time()))}"
    return st.session_state.session_id

def display_conversation_history(df, limit=5):
    history = memory_manager.get_conversation_history(get_session_id(), limit)
    if history:
        for i, conv in enumerate(history):
            question_preview = conv['question'][:50] + "..." if len(conv['question']) > 50 else conv['question']
            st.markdown(f"**💬 问题 {i + 1}:** {question_preview}")
            with st.container():
                st.markdown(f"**完整问题:** {conv['question']}")
                try:
                    answer_data = json.loads(conv['answer'])
                    if "answer" in answer_data:
                        st.markdown(f"**回答:** {answer_data['answer']}")
                    if "table" in answer_data:
                        st.markdown("**数据表格:**")
                        result_df = pd.DataFrame(answer_data["table"]["data"], columns=answer_data["table"]["columns"])
                        st.dataframe(result_df, use_container_width=True)
                except:
                    st.markdown(f"**回答:** {conv['answer']}")
                st.caption(f"⏱️ 响应时间: {conv['response_time']:.2f}秒 | 🕐 时间: {conv['timestamp']}")
                st.divider()
    else:
        st.info("暂无对话历史")

def display_popular_questions(df, limit=5):
    popular = memory_manager.get_popular_questions(memory_manager.get_data_hash(df), limit)
    if popular:
        for i, item in enumerate(popular):
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(f"📝 {item['question']}", key=f"popular_{i}"):
                    st.session_state.selected_question = item['question']
                    st.rerun()
            with col2:
                st.caption(f"🔥 {item['hit_count']}次")
    else:
        st.info("暂无热门问题")


def get_memory_stats(df):
    session_id = get_session_id()
    data_hash = memory_manager.get_data_hash(df)
    conn = sqlite3.connect(memory_manager.db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM conversations WHERE session_id = ?", (session_id,))
    session_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM quick_answers WHERE data_hash = ?", (data_hash,))
    quick_answers_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM conversations")
    total_conversations = cursor.fetchone()[0]
    cursor.execute("SELECT AVG(response_time) FROM conversations WHERE data_hash = ?", (data_hash,))
    avg_response_time = cursor.fetchone()[0] or 0
    
    conn.close()
    return {"session_count": session_count, "quick_answers_count": quick_answers_count, 
            "total_conversations": total_conversations, "avg_response_time": avg_response_time}

def clear_session_memory(session_id):
    conn = sqlite3.connect(memory_manager.db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted_count

def clear_all_memory():
    conn = sqlite3.connect(memory_manager.db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM conversations")
    cursor.execute("DELETE FROM quick_answers")
    conn.commit()
    conn.close()
    return True