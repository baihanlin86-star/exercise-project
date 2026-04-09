import streamlit as st
import pandas as pd
import plotly.express as px

# --- 頁面設定 ---
st.set_page_config(page_title="AI健身教練專題展示", layout="wide", initial_sidebar_state="collapsed")

# --- 進階 CSS 樣式 ---
st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    .hero-section {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        padding: 50px 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    .content-card {
        background-color: white;
        padding: 25px;
        border-radius: 15px;
        border-top: 5px solid #00c6ff;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
    .progress-box {
        border-left: 3px solid #00c6ff;
        padding-left: 15px;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 頂部 Header ---
st.markdown(f"""
    <div class="hero-section">
        <h1 style="font-size: 42px; margin-bottom: 10px;">AI驅動的個人化健身教練</h1>
        <p style="font-size: 18px; opacity: 0.9;">指導教師：朱學亭 教授 | 專題小組：林柏翰 等四位</p>
    </div>
    """, unsafe_allow_html=True)

# --- 關鍵數據摘要  ---
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.metric(label="預計預算", value="NT$ 85,500", delta="包含設備及雜支")
with col_m2:
    st.metric(label="整合領域", value="3 大領域", delta="營養、健身、物治")
with col_m3:
    st.metric(label="團隊人數", value="4 人", delta="資工三B")
with col_m4:
    st.metric(label="開發環境", value="Python 3.10", delta="深度學習模型")

# --- 分頁導覽 (新增：每週進度) ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎯 專案摘要", "🛠️ 技術與分工", "💰 預算編列", "👥 團隊資訊", "📅 每週進度"])

# --- 1. 專案摘要  ---
with tab1:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.subheader("📝 專題摘要")
    st.write("本專題結合 **營養、健身動作、物治知識**，為健身新手建立全方位 AI 網站 。")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 2. 技術與分工  ---
with tab2:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.subheader("📋 工作分配")
    work_data = {
        "成員": ["林柏翰", "彭治翔", "許睿川", "蘇彥瑋"],
        "職責": ["資料處理、程式設計", "程式設計", "程式設計", "程式設計"]
    }
    st.table(pd.DataFrame(work_data))
    st.markdown('</div>', unsafe_allow_html=True)

# --- 3. 預算編列  ---
with tab3:
    st.subheader("💵 經費預算 (總計 NT$ 85,500)")
    budget_data = [
        ["個人電腦", 52000], ["雷射印表機", 10000], ["繪圖板", 5000],
        ["消耗器材", 8000], ["雜支費用", 10500]
    ]
    df_budget = pd.DataFrame(budget_data, columns=["項目", "小計"])
    st.plotly_chart(px.pie(df_budget, values='小計', names='項目', hole=0.3), use_container_width=True)

# --- 4. 團隊資訊  ---
with tab4:
    st.subheader("👥 團隊成員清單")
    members = [
        {"name": "林柏翰", "id": "411203487", "tag": "組長"},
        {"name": "彭治翔", "id": "411220764", "tag": "開發"},
        {"name": "許睿川", "id": "411214331", "tag": "開發"},
        {"name": "蘇彥瑋", "id": "411214357", "tag": "開發"}
    ]
    cols = st.columns(4)
    for i, m in enumerate(members):
        with cols[i]:
            st.markdown(f'<div style="text-align:center; padding:10px; border:1px solid #ddd; border-radius:10px;"><b>{m["name"]}</b><br><small>{m["id"]}</small></div>', unsafe_allow_html=True)

# --- 5. 每週進度 (根據計畫書時程更新 ) ---
with tab5:
    st.subheader("📅 專題開發里程碑")
    
    # 這裡根據 2026/03/31 截止日之後的開發計畫編排 
    progress_data = [
    ("2026/04 第 1 週", "深度學習環境最佳化", "優化 Python 3.10 模型訓練環境與 CUDA 配置 。"),
    ("2026/04 第 2 週", "營養學數據庫擴展", "針對計畫書提到的資料不足問題，補充多方書籍與文獻資料 。"),
    ("2026/04 第 3 週", "物治知識圖譜建立", "結合物理治療基礎理論，進行 AI 指令初步測試 。"),
    ("2026/04 第 4 週", "系統介面與 AI 整合", "將後端 AI 模型與 Streamlit 前端介面進行深度整合測試 。"), # <--- 這裡一定要有逗號
    ("2026/04 第 5 週", "Github 共同編輯程式碼", "完成環境設定與多人協作流程測試 。") # <--- 記得補上第3個資料內容
]
    
    for week, title, detail in progress_data:
        st.markdown(f"""
            <div class="progress-box">
                <b style="color: #00c6ff;">{week}</b><br>
                <b>{title}</b><br>
                <small style="color: #666;">{detail}</small>
            </div>
            """, unsafe_allow_html=True)

# --- 頁尾 ---
st.markdown("---")
st.caption("最後更新日期：115/04/09 | 靜宜大學資訊工程學系 專題計畫書展示 ")