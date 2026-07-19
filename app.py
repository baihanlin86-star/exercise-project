import streamlit as st
import pandas as pd
import plotly.express as px

PAGE_TITLE = "AI健身教練專題展示"
TEAM_MEMBERS = [
    {"name": "林柏翰", "id": "411203487", "role": "組長"},
    {"name": "彭治翔", "id": "411220764", "role": "開發"},
    {"name": "許睿川", "id": "411214331", "role": "開發"},
    {"name": "蘇彥瑋", "id": "411214357", "role": "開發"},
]
BUDGET_ITEMS = [
    ("個人電腦", 52000),
    ("雷射印表機", 10000),
    ("繪圖板", 5000),
    ("消耗器材", 8000),
    ("雜支費用", 10500),
]
WORK_ASSIGNMENTS = [
    ("林柏翰", "資料處理、程式設計"),
    ("彭治翔", "程式設計"),
    ("許睿川", "程式設計"),
    ("蘇彥瑋", "程式設計"),
]
PROGRESS_MILESTONES = [
    ("2026/04 第 1 週", "深度學習環境最佳化", "優化 Python 3.10 模型訓練環境與 CUDA 配置。"),
    ("2026/04 第 2 週", "營養學數據庫擴展", "針對計畫書提到的資料不足問題，補充多方書籍與文獻資料。"),
    ("2026/04 第 3 週", "物治知識圖譜建立", "結合物理治療基礎理論，進行 AI 指令初步測試。"),
    ("2026/04 第 4 週", "系統介面與 AI 整合", "將後端 AI 模型與 Streamlit 前端介面進行深度整合測試。"),
    ("2026/04 第 5 週", "Github 共同編輯程式碼", "完成環境設定與多人協作流程測試。"),
]


def set_page_config() -> None:
    st.set_page_config(page_title=PAGE_TITLE, layout="wide", initial_sidebar_state="collapsed")


def inject_styles() -> None:
    css = """
    <style>
    .main { background-color: #f4f7f9; }
    .hero-section {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        padding: 50px 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
    }
    .content-card {
        background-color: white;
        padding: 25px;
        border-radius: 15px;
        border-top: 5px solid #00c6ff;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
    }
    .progress-box {
        border-left: 3px solid #00c6ff;
        padding-left: 15px;
        margin-bottom: 15px;
    }
    .member-card {
        border: 1px solid #ddd;
        border-radius: 12px;
        padding: 18px;
        text-align: center;
        background-color: #ffffff;
    }
    .member-card small {
        color: #555;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero-section">
            <h1 style="font-size: 42px; margin-bottom: 10px;">AI驅動的個人化健身教練</h1>
            <p style="font-size: 18px; opacity: 0.9;">指導教師：朱學亭 教授 | 專題小組：林柏翰 等四位</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metrics() -> None:
    metric_items = [
        ("預計預算", "NT$ 85,500", "包含設備及雜支"),
        ("整合領域", "3 大領域", "營養、健身、物治"),
        ("團隊人數", "4 人", "資工三B"),
        ("開發環境", "Python 3.10", "深度學習模型"),
    ]
    cols = st.columns(len(metric_items))
    for col, (label, value, delta) in zip(cols, metric_items):
        with col:
            st.metric(label=label, value=value, delta=delta)


def render_content_card(title: str, content_callable) -> None:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.subheader(title)
    content_callable()
    st.markdown('</div>', unsafe_allow_html=True)


def render_project_summary() -> None:
    st.write("本專題結合 **營養、健身動作、物治知識**，為健身新手建立全方位 AI 網站。")


def render_work_assignments() -> None:
    df_work = pd.DataFrame(WORK_ASSIGNMENTS, columns=["成員", "職責"])
    st.table(df_work)


def render_budget() -> None:
    df_budget = pd.DataFrame(BUDGET_ITEMS, columns=["項目", "小計"])
    chart = px.pie(df_budget, values="小計", names="項目", hole=0.3)
    chart.update_layout(margin=dict(t=0, b=0, l=0, r=0), legend_title_text="項目")
    st.plotly_chart(chart, use_container_width=True)


def render_team_info() -> None:
    cols = st.columns(len(TEAM_MEMBERS))
    for col, member in zip(cols, TEAM_MEMBERS):
        with col:
            st.markdown(
                f"""
                <div class="member-card">
                    <strong>{member['name']}</strong><br>
                    <small>{member['id']} · {member['role']}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_progress() -> None:
    for week, title, detail in PROGRESS_MILESTONES:
        st.markdown(
            f"""
            <div class="progress-box">
                <b style="color: #00c6ff;">{week}</b><br>
                <b>{title}</b><br>
                <small style="color: #666;">{detail}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )


def main() -> None:
    set_page_config()
    inject_styles()
    render_hero()
    render_metrics()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 專案摘要",
        "🛠️ 技術與分工",
        "💰 預算編列",
        "👥 團隊資訊",
        "📅 每週進度",
    ])

    with tab1:
        render_content_card("📝 專題摘要", render_project_summary)

    with tab2:
        render_content_card("📋 工作分配", render_work_assignments)

    with tab3:
        st.subheader("💵 經費預算 (總計 NT$ 85,500)")
        render_budget()

    with tab4:
        st.subheader("👥 團隊成員清單")
        render_team_info()

    with tab5:
        st.subheader("📅 專題開發里程碑")
        render_progress()

    st.markdown("---")
    st.caption("最後更新日期：115/04/09 | 靜宜大學資訊工程學系 專題計畫書展示")


if __name__ == "__main__":
    main()
