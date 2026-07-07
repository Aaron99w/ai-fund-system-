import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
import requests
import random
import time

# ==================== 页面设置 ====================
st.set_page_config(
    page_title="AI智能投资系统",
    page_icon="📈",
    layout="wide"
)

st.title("📊 AI智能投资系统")
st.caption("📈 一键买入 · 实时盈亏 · 止盈止损 · 定投计算 · 基金对比 · 市场情绪")

# ==================== 数据持久化 ====================
HOLDINGS_FILE = "holdings.json"
CONFIG_FILE = "config.json"

def load_holdings():
    if os.path.exists(HOLDINGS_FILE):
        try:
            with open(HOLDINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_holdings(holdings):
    with open(HOLDINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(holdings, f, ensure_ascii=False, indent=2)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

# ==================== 微信通知 ====================
def get_webhook():
    config = load_config()
    return config.get("webhook_url", "")

def set_webhook(url):
    config = load_config()
    config["webhook_url"] = url
    save_config(config)

def send_wechat_message(content):
    url = get_webhook()
    if not url:
        return False
    try:
        data = {"msgtype": "text", "text": {"content": content[:2000]}}
        response = requests.post(url, json=data, timeout=5)
        return response.status_code == 200
    except:
        return False

# ==================== 真实净值获取 ====================
def get_real_nav(code):
    try:
        import akshare as ak
        df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
        if df is not None and not df.empty:
            return float(df['单位净值'].iloc[-1])
    except:
        pass
    return None

# ==================== 基金池 ====================
FUNDS = [
    {"name": "前海开源人工智能混合", "code": "001986", "style": "科技", "risk": "高"},
    {"name": "万家人工智能混合", "code": "006281", "style": "科技", "risk": "高"},
    {"name": "中欧时代先锋股票A", "code": "001938", "style": "科技", "risk": "高"},
    {"name": "易方达蓝筹精选混合", "code": "005827", "style": "消费", "risk": "中"},
    {"name": "交银阿尔法核心混合", "code": "519712", "style": "均衡", "risk": "中"},
    {"name": "兴全合润混合", "code": "163406", "style": "均衡", "risk": "中"},
    {"name": "富国天惠成长混合", "code": "161005", "style": "均衡", "risk": "中"},
    {"name": "中欧医疗健康混合A", "code": "003095", "style": "医药", "risk": "高"},
    {"name": "诺安成长混合", "code": "320007", "style": "芯片", "risk": "高"},
    {"name": "农银新能源主题混合", "code": "002190", "style": "新能源", "risk": "高"},
]

# ==================== AI推荐评分 ====================
def ai_score(fund):
    return random.randint(60, 95)

# ==================== 定投计算器 ====================
def calculate_drip(monthly, annual_return, years):
    months = years * 12
    rate = annual_return / 12 / 100
    total = 0
    for _ in range(months):
        total = (total + monthly) * (1 + rate)
    return total

# ==================== 模拟基金业绩（用于对比） ====================
def get_fund_performance(code):
    return {
        "近3月": round(random.uniform(-5, 15), 2),
        "近1年": round(random.uniform(-10, 30), 2)
    }

# ==================== 市场情绪（模拟） ====================
def get_market_sentiment():
    change = random.uniform(-2, 2)
    if change > 0.5:
        return "乐观", "😊", change
    elif change > -0.5:
        return "中性", "😐", change
    else:
        return "悲观", "😰", change

# ==================== 止盈止损检查 ====================
def check_stop(profit):
    if profit >= 15:
        return "🔴 建议止盈", "止盈"
    elif profit <= -8:
        return "🔴 建议止损", "止损"
    elif profit >= 8:
        return "🟡 接近止盈", "观察"
    elif profit <= -5:
        return "🟡 接近止损", "观察"
    else:
        return "🟢 正常持有", "持有"

# ==================== 初始化 ====================
if "total_cash" not in st.session_state:
    st.session_state.total_cash = 10000

# ==================== 侧边栏 ====================
with st.sidebar:
    st.header("💰 我的资产")
    total_cash = st.number_input("总资金（元）", min_value=1000, value=st.session_state.total_cash, step=1000)
    st.session_state.total_cash = total_cash
    
    st.divider()
    holdings = load_holdings()
    st.metric("持仓数量", f"{len(holdings)} 只")
    total_cost = sum(h.get("amount", 0) for h in holdings)
    st.metric("已投入", f"{total_cost:.0f} 元")
    st.metric("剩余资金", f"{total_cash - total_cost:.0f} 元")
    
    st.divider()
    st.subheader("🔔 微信通知")
    webhook = st.text_input("Webhook地址（选填）", value=get_webhook(), placeholder="输入企业微信机器人地址")
    if st.button("保存配置"):
        set_webhook(webhook)
        st.success("✅ 已保存")
    if st.button("📤 测试通知"):
        if send_wechat_message("✅ 测试消息：AI投资助手已连接！"):
            st.success("✅ 发送成功")
        else:
            st.error("❌ 发送失败，请检查地址")

# ==================== 主界面 ====================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 AI推荐",
    "📊 持仓监控",
    "📋 持仓管理",
    "💰 定投计算器",
    "📊 基金对比",
    "📈 市场情绪"
])

# ==================== Tab1: AI推荐 ====================
with tab1:
    st.subheader("🤖 AI智能推荐")
    for i, f in enumerate(FUNDS):
        score = ai_score(f)
        with st.container():
            # 调整列宽，第三列放输入框
            col1, col2, col3, col4 = st.columns([2, 1, 1.2, 1])
            with col1:
                st.write(f"**{i+1}. {f['name']}**")
                st.caption(f"{f['code']} | {f['style']} | 风险：{f['risk']}")
            with col2:
                st.metric("AI评分", f"{score}/100")
            with col3:
                # 金额输入框
                buy_amount = st.number_input(
                    "金额(元)", 
                    min_value=100, 
                    max_value=10000, 
                    value=1000, 
                    step=100, 
                    key=f"amount_{f['code']}"
                )
            with col4:
                holdings = load_holdings()
                already = any(h["code"] == f["code"] for h in holdings)
                if already:
                    st.button("✅ 已持有", disabled=True, key=f"held_{f['code']}")
                else:
                    if st.button("📥 买入", key=f"buy_{f['code']}_{i}"):
                        real_nav = get_real_nav(f["code"])
                        if real_nav is None:
                            real_nav = 1.0
                        holdings = load_holdings()
                        holdings.append({
                            "code": f["code"],
                            "name": f["name"],
                            "amount": buy_amount,  # 使用用户输入的金额
                            "buy_date": datetime.now().strftime("%Y-%m-%d"),
                            "nav": real_nav
                        })
                        save_holdings(holdings)
                        st.success(f"✅ 买入 {f['name']} {buy_amount}元，净值 {real_nav:.4f}")
                        send_wechat_message(f"✅ 买入 {f['name']}，金额{buy_amount}元")
                        st.rerun()
            st.divider()

# ==================== 以下 Tab2~Tab6 与之前相同，保持不变 ====================
# ==================== Tab2: 持仓监控（含止盈止损） ====================
with tab2:
    st.subheader("📊 持仓监控")
    holdings = load_holdings()
    if holdings:
        for h in holdings:
            real_nav = get_real_nav(h["code"])
            if real_nav is not None and h.get("nav", 0) > 0:
                profit = (real_nav - h["nav"]) / h["nav"] * 100
                status, action = check_stop(profit)
            else:
                profit = 0.0
                status = "🟢 刚买入"
                action = "持有"
            
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                with col1:
                    st.write(f"**{h['name']}**")
                    st.caption(f"买入价：{h.get('nav', 0):.4f} | 金额：{h['amount']}元")
                with col2:
                    st.metric("盈亏", f"{'+' if profit > 0 else ''}{profit:.2f}%")
                with col3:
                    st.write(status)
                with col4:
                    if action == "止盈":
                        st.warning("📈 建议分批卖出")
                        if st.button("📤 已止盈", key=f"take_profit_{h['code']}"):
                            holdings = load_holdings()
                            holdings = [x for x in holdings if x["code"] != h["code"]]
                            save_holdings(holdings)
                            send_wechat_message(f"📈 {h['name']} 已止盈，盈利 {profit:.2f}%")
                            st.rerun()
                    elif action == "止损":
                        st.error("📉 建议卖出")
                        if st.button("📤 已止损", key=f"stop_loss_{h['code']}"):
                            holdings = load_holdings()
                            holdings = [x for x in holdings if x["code"] != h["code"]]
                            save_holdings(holdings)
                            send_wechat_message(f"📉 {h['name']} 已止损，亏损 {profit:.2f}%")
                            st.rerun()
                    else:
                        st.info("🟢 继续持有")
                st.divider()
    else:
        st.info("📭 暂无持仓")

# ==================== Tab3: 持仓管理 ====================
with tab3:
    st.subheader("📋 持仓管理")
    holdings = load_holdings()
    if holdings:
        for i, h in enumerate(holdings):
            col1, col2, col3 = st.columns([2, 1, 0.5])
            with col1:
                st.write(f"**{h['name']}**")
                st.caption(f"金额：{h['amount']}元 | 日期：{h.get('buy_date', '')}")
            with col2:
                st.caption(f"买入价：{h.get('nav', 0):.4f}")
            with col3:
                if st.button("🗑️", key=f"del_{i}"):
                    holdings.pop(i)
                    save_holdings(holdings)
                    st.rerun()
            st.divider()
        if st.button("清空全部", use_container_width=True):
            save_holdings([])
            st.rerun()
    else:
        st.info("📭 暂无持仓")

# ==================== Tab4: 定投计算器 ====================
with tab4:
    st.subheader("💰 定投计算器")
    st.caption("计算每月定投一定金额，多年后的资产总额")
    col1, col2, col3 = st.columns(3)
    with col1:
        monthly = st.number_input("每月定投（元）", min_value=100, value=1000, step=100)
    with col2:
        annual_return = st.number_input("年化收益率（%）", min_value=0.0, value=10.0, step=0.5)
    with col3:
        years = st.number_input("定投年限", min_value=1, max_value=30, value=5, step=1)
    
    if st.button("📊 计算", use_container_width=True):
        total = calculate_drip(monthly, annual_return, years)
        total_invested = monthly * years * 12
        profit = total - total_invested
        st.success(f"✅ 总投入：{total_invested:,.0f} 元")
        st.success(f"📈 最终资产：{total:,.0f} 元")
        st.info(f"💵 收益：{profit:,.0f} 元（收益率 {profit/total_invested*100:.1f}%）")
        
        data = []
        rate = annual_return / 12 / 100
        cur = 0
        for m in range(1, years*12+1):
            cur = (cur + monthly) * (1 + rate)
            if m % 12 == 0:
                data.append({"年": m//12, "资产": cur})
        df = pd.DataFrame(data)
        st.line_chart(df.set_index("年"))

# ==================== Tab5: 基金对比 ====================
with tab5:
    st.subheader("📊 基金对比")
    st.caption("选择2-3只基金，对比近期表现")
    selected_codes = st.multiselect(
        "选择基金",
        options=[f"{f['name']} ({f['code']})" for f in FUNDS],
        default=[f"{FUNDS[0]['name']} ({FUNDS[0]['code']})", f"{FUNDS[1]['name']} ({FUNDS[1]['code']})"]
    )
    if len(selected_codes) >= 2:
        compare_data = []
        for item in selected_codes:
            code = item.split("(")[-1].replace(")", "")
            perf = get_fund_performance(code)
            name = next(f["name"] for f in FUNDS if f["code"] == code)
            compare_data.append({
                "基金": name,
                "近3月收益": f"{perf['近3月']:.1f}%",
                "近1年收益": f"{perf['近1年']:.1f}%"
            })
        df = pd.DataFrame(compare_data)
        st.dataframe(df, use_container_width=True)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df["基金"],
            y=[float(x.replace("%","")) for x in df["近3月收益"]],
            name="近3月",
            marker_color="lightblue"
        ))
        fig.add_trace(go.Bar(
            x=df["基金"],
            y=[float(x.replace("%","")) for x in df["近1年收益"]],
            name="近1年",
            marker_color="lightgreen"
        ))
        fig.update_layout(height=400, title="收益对比")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("请至少选择2只基金")

# ==================== Tab6: 市场情绪 ====================
with tab6:
    st.subheader("📈 市场情绪")
    sentiment, emoji, change = get_market_sentiment()
    col1, col2, col3 = st.columns(3)
    col1.metric("市场情绪", f"{emoji} {sentiment}")
    col2.metric("模拟涨跌幅", f"{'+' if change > 0 else ''}{change:.2f}%")
    col3.metric("更新时间", datetime.now().strftime("%H:%M"))
    if sentiment == "乐观":
        st.success("💡 市场情绪乐观，可适当增加仓位")
    elif sentiment == "悲观":
        st.warning("💡 市场情绪悲观，建议控制仓位")
    else:
        st.info("💡 市场情绪中性，保持现有配置")

# ==================== 底部 ====================
st.divider()
st.caption("⚠️ 本系统为学习演示工具，不构成投资建议")
st.caption("📊 数据来源：模拟数据 + akshare真实净值")
