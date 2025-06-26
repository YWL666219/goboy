import matplotlib.pyplot as plt
import openpyxl
import pandas as pd
import streamlit as st
from utils import dataframe_agent
def create_chart(input_data, chart_type):
    """生成统计图表"""
    df_data = pd.DataFrame(
        data={
            "x": input_data["columns"],
            "y": input_data["data"]
        }
    ).set_index("x")
    if chart_type == "bar":
        plt.figure(figsize=(8, 5), dpi=120)
        plt.bar(input_data["columns"], input_data["data"], width=0.4, hatch='///')
        st.pyplot(plt.gcf())
        # st.bar_chart(df_data)
    elif chart_type == "line":
        st.line_chart(df_data)
st.write("## 小脑瓜数据分析智能体")
option = st.radio("请选择数据文件类型:", ("Excel", "CSV"))
file_type = "xlsx" if option == "Excel" else "csv"
data = st.file_uploader(f"上传你的{option}数据文件", type=file_type)
if data:
    if file_type == "xlsx":
        wb = openpyxl.load_workbook(data)
        option = st.radio(label="请选择要加载的工作表：", options=wb.sheetnames)
        st.session_state["df"] = pd.read_excel(data, sheet_name=option)
    else:
        st.session_state["df"] = pd.read_csv(data)
    with st.expander("原始数据"):
        st.dataframe(st.session_state["df"])
query = st.text_area(
    "请输入你关于以上数据集的问题或数据可视化需求：",
    disabled="df" not in st.session_state
)
button = st.button("生成回答")
if button and not data:
    st.info("请先上传数据文件")
    st.stop()
if query:
    with st.spinner("AI正在思考中，请稍等..."):
        result = dataframe_agent(st.session_state["df"], query)
        if "answer" in result:
            st.write(result["answer"])
        if "table" in result:
            st.table(pd.DataFrame(result["table"]["data"],
                                  columns=result["table"]["columns"]))
        if "bar" in result:
            create_chart(result["bar"], "bar")
        if "line" in result:
            create_chart(result["line"], "line")