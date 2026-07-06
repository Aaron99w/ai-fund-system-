import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json
import os
import random

st.set_page_config(page_title="AI投资助手", page_icon="📈", layout="wide")

st.title("📊 AI投资助手")
st.caption("AI推荐 · 持仓管理 · 一键买入")

# ==================== 数据文件 ====================
HOLDINGS_FILE = "holdings.json"

def load_holdings():
    if os.path.exists(HOLDINGS_FILE):
        try:
            with open(HOLDINGS_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_holdings(holdings):
    with open(HOLDINGS_FILE, "w") as f:
        json.dump(holdings, f, ensure_ascii=False, indent=2)

# ==================== 基金数据 ====================
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

# ==================== 侧边栏 ====================
with st.sidebar:
    st.header("💰 我的持仓")
    holdings = load_holdings()
    st.metric("持仓数量", f"{len(holdings)} 只")
    total = sum(h.get("amount", 0) for h in holdings)
    st.metric("已投入", f"{total:.0f} 元")
    
    if holdings:
        st.divider()
        st.subheader("📋 持仓列表")
        for h in holdings:
            st.write(f"• {h['name']}：{h['amount']}元")

# ==================== 主界面 ====================
st.subheader("🤖 AI智能推荐")

# 选基金
fund_names = [f"{f['name']} ({f['code']}) - {f['style']}" for f in FUNDS]
selected = st.selectbox("选择基金", fund_names)

# 获取选中基金的代码
code = selected.split("(")[-1].split(")")[0]
fund = next((f for f in FUNDS if f["code"] == code), FUNDS[0])

# 显示基金信息
col1, col2, col3 = st.columns(3)
col1.metric("基金名称", fund["name"])
col2.metric("风格", fund["style"])
col3.metric("风险", fund["risk"])

# 评分（模拟）
score = random.randint(70, 95)
st.metric("AI评分", f"{score}/100")

# 建议金额
suggest_amount = 1000

# ===== 买入按钮 =====
col1, col2 = st.columns([1, 3])
with col1:
    buy_amount = st.number_input("买入金额（元）", min_value=100, value=suggest_amount, step=100)

with col2:
    st.write("")
    st.write("")
    if st.button("📥 确认买入", type="primary", use_container_width=True):
        holdings = load_holdings()
        holdings.append({
            "name": fund["name"],
            "code": fund["code"],
            "amount": buy_amount,
            "buy_date": datetime.now().strftime("%Y-%m-%d"),
            "nav": round(random.uniform(1.0, 3.0), 4)
        })
        save_holdings(holdings)
        st.success(f"✅ 成功买入 {fund['name']}，金额 {buy_amount} 元")
        st.balloons()
        # 强制刷新
        st.rerun()

# ==================== 显示持仓 ====================
st.divider()
st.subheader("📊 我的持仓")

holdings = load_holdings()
if holdings:
    df = pd.DataFrame(holdings)
    st.dataframe(df[["name", "amount", "buy_date"]], use_container_width=True)
    
    if st.button("🗑️ 清空持仓"):
        save_holdings([])
        st.rerun()
else:
    st.info("📭 暂无持仓，请买入")

st.caption("⚠️ 本系统为学习演示工具")
