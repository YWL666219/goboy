import matplotlib.pyplot as plt
import openpyxl
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from utils import dataframe_agent

# 页面配置
st.set_page_config(
    page_title="小脑瓜数据分析智能体",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.2rem;
        text-align: center;
        color: #666;
        margin-bottom: 3rem;
    }
    .upload-section {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .query-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .result-section {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

def create_chart(input_data, chart_type):
    """生成美化的统计图表"""
    df_data = pd.DataFrame(
        data={
            "x": input_data["columns"],
            "y": input_data["data"]
        }
    )
    
    if chart_type == "bar":
        fig = px.bar(
            df_data, 
            x="x", 
            y="y",
            title="📊 柱状图分析",
            color="y",
            color_continuous_scale="viridis"
        )
        fig.update_layout(
            title_font_size=20,
            title_x=0.5,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)
    elif chart_type == "line":
        fig = px.line(
            df_data, 
            x="x", 
            y="y",
            title="📈 趋势线分析",
            markers=True
        )
        fig.update_layout(
            title_font_size=20,
            title_x=0.5,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)

def load_data(file_type, file):
    """加载数据文件"""
    if file_type == "xlsx":
        wb = openpyxl.load_workbook(file)
        option = st.radio(
            label="📋 请选择要加载的工作表：", 
            options=wb.sheetnames,
            horizontal=True
        )
        return pd.read_excel(file, sheet_name=option)
    else:
        return pd.read_csv(file)

def display_data_summary(df):
    """显示数据摘要信息"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>📊 总行数</h3>
            <h2 style="color: #667eea;">{}</h2>
        </div>
        """.format(len(df)), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>📈 总列数</h3>
            <h2 style="color: #764ba2;">{}</h2>
        </div>
        """.format(len(df.columns)), unsafe_allow_html=True)
    
    with col3:
        numeric_cols = df.select_dtypes(include=['number']).columns
        st.markdown("""
        <div class="metric-card">
            <h3>🔢 数值列</h3>
            <h2 style="color: #f093fb;">{}</h2>
        </div>
        """.format(len(numeric_cols)), unsafe_allow_html=True)
    
    with col4:
        missing_values = df.isnull().sum().sum()
        st.markdown("""
        <div class="metric-card">
            <h3>❓ 缺失值</h3>
            <h2 style="color: #f5576c;">{}</h2>
        </div>
        """.format(missing_values), unsafe_allow_html=True)

# 主页面标题
st.markdown('<h1 class="main-header">🧠 小脑瓜数据分析智能体</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">✨ 让数据分析变得简单有趣 ✨</p>', unsafe_allow_html=True)

# 侧边栏
with st.sidebar:
    st.markdown("### 🎯 功能导航")
    st.markdown("""
    - 📁 **数据上传**: 支持Excel和CSV格式
    - 🔍 **智能分析**: AI驱动的数据洞察
    - 📊 **可视化**: 交互式图表生成
    - 💡 **问答系统**: 自然语言查询
    """)
    
    st.markdown("### 📋 使用说明")
    st.markdown("""
    1. 选择文件类型
    2. 上传数据文件
    3. 输入分析问题
    4. 获取智能回答
    """)

# 数据上传区域
st.markdown('<div class="upload-section">', unsafe_allow_html=True)
st.markdown("### 📁 数据上传区域")

col1, col2 = st.columns([1, 2])
with col1:
    option = st.radio(
        "📂 请选择数据文件类型:", 
        ("Excel", "CSV"),
        horizontal=True
    )
    file_type = "xlsx" if option == "Excel" else "csv"

with col2:
    data = st.file_uploader(
        f"📤 上传你的{option}数据文件", 
        type=file_type,
        help=f"支持{option}格式文件，最大200MB"
    )
st.markdown('</div>', unsafe_allow_html=True)

# 数据预览和摘要
if data:
    df = load_data(file_type, data)
    st.session_state["df"] = df
    
    st.markdown("### 📊 数据概览")
    display_data_summary(df)
    
    with st.expander("🔍 查看原始数据", expanded=False):
        st.dataframe(
            st.session_state["df"], 
            use_container_width=True,
            height=400
        )

# 查询区域
st.markdown('<div class="query-section">', unsafe_allow_html=True)
st.markdown("### 🤖 AI智能问答")
query = st.text_area(
    "💬 请输入你关于以上数据集的问题或数据可视化需求：",
    disabled="df" not in st.session_state,
    placeholder="例如：显示销售额最高的前5个地区的柱状图",
    height=100
)

col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    button = st.button("🚀 生成回答", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# 错误提示
if button and not data:
    st.error("⚠️ 请先上传数据文件")
    st.stop()

# 结果展示区域
if query and button:
    st.markdown('<div class="result-section">', unsafe_allow_html=True)
    st.markdown("### 🎯 分析结果")
    
    with st.spinner("🤔 AI正在思考中，请稍等..."):
        result = dataframe_agent(st.session_state["df"], query)
        
        if "answer" in result:
            st.markdown("#### 💡 智能回答")
            st.success(result["answer"])
        
        if "table" in result:
            st.markdown("#### 📋 数据表格")
            st.dataframe(
                pd.DataFrame(
                    result["table"]["data"],
                    columns=result["table"]["columns"]
                ),
                use_container_width=True
            )
        
        if "bar" in result:
            st.markdown("#### 📊 图表分析")
            create_chart(result["bar"], "bar")
        
        if "line" in result:
            st.markdown("#### 📈 趋势分析")
            create_chart(result["line"], "line")
    
    st.markdown('</div>', unsafe_allow_html=True)

# 页脚
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #666;'>🌟 由AI驱动的智能数据分析平台 🌟</p>", 
    unsafe_allow_html=True
)