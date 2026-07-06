import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
import random

# ==================== 页面设置 ====================
st.set_page_config(
    page_title="AI投资助手",
    page_icon="📈",
    layout="wide"
)

st.title("📊 AI投资助手")
st.caption("AI推荐 · 持仓管理 · 一键买入")

# ==================== 数据持久化 ====================
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

# ==================== 基金池 ====================
FUNDS = [
    {"name": "前海开源人工智能混合", "code": "001986", "style": "科技"},
    {"name": "万家人工智能混合", "code": "006281", "style": "科技"},
    {"name": "中欧时代先锋股票A", "code": "001938", "style": "科技"},
    {"name": "易方达蓝筹精选混合", "code": "005827", "style": "消费"},
    {"name": "交银阿尔法核心混合", "code": "519712", "style": "均衡"},
    {"name": "兴全合润混合", "code": "163406", "style": "均衡"},
    {"name": "富国天惠成长混合", "code": "161005", "style": "均衡"},
    {"name": "中欧医疗健康混合A", "code": "003095", "style": "医药"},
    {"name": "诺安成长混合", "code": "320007", "style": "芯片"},
    {"name": "农银新能源主题混合", "code": "002190", "style": "新能源"},
]

# ==================== 侧边栏 ====================
with st.sidebar:
    st.header("💰 我的资产")
    total_cash = st.number_input("总资金（元）", min_value=1000, value=10000, step=1000)
    
    st.divider()
    holdings = load_holdings()
    st.metric("持仓数量", f"{len(holdings)} 只")
    total_cost = sum(h.get("amount", 0) for h in holdings)
    st.metric("已投入", f"{total_cost:.0f} 元")
    st.metric("剩余资金", f"{total_cash - total_cost:.0f} 元")

# ==================== 主界面 ====================
tab1, tab2 = st.tabs(["📈 AI推荐", "📋 我的持仓"])

# ==================== Tab1: AI推荐 ====================
with tab1:
    st.subheader("🤖 AI智能推荐")
    
    # 简单评分
    for f in FUNDS:
        score = random.randint(60, 95)
        f["score"] = score
    
    sorted_funds = sorted(FUNDS, key=lambda x: x["score"], reverse=True)
    
    for i, f in enumerate(sorted_funds):
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            with col1:
                st.write(f"**{i+1}. {f['name']}**")
                st.caption(f"{f['code']} | {f['style']}")
            with col2:
                st.metric("AI评分", f"{f['score']}/100")
            with col3:
                suggest = 1000
                st.caption(f"建议投入")
                st.caption(f"**{suggest}元**")
            with col4:
                # 检查是否已持有
                holdings = load_holdings()
                already_hold = any(h["code"] == f["code"] for h in holdings)
                if already_hold:
                    st.button("已持有", disabled=True, key=f"held_{f['code']}")
                else:
                    # 买入按钮 - 使用最简单的逻辑
                    if st.button(f"📥 买入", key=f"buy_{f['code']}_{i}"):
                        # 执行买入
                        holdings = load_holdings()
                        holdings.append({
                            "code": f["code"],
                            "name": f["name"],
                            "amount": 1000,
                            "buy_date": datetime.now().strftime("%Y-%m-%d"),
                            "nav": round(random.uniform(1.0, 2.5), 4)
                        })
                        save_holdings(holdings)
                        st.success(f"✅ 成功买入 {f['name']} 1000元")
                        st.rerun()
            st.divider()

# ==================== Tab2: 持仓管理 ====================
with tab2:
    st.subheader("📋 我的持仓")
    
    holdings = load_holdings()
    if holdings:
        for i, h in enumerate(holdings):
            col1, col2, col3 = st.columns([2, 1, 0.5])
            with col1:
                st.write(f"**{h['name']}**")
                st.caption(f"金额：{h['amount']}元 | 日期：{h['buy_date']}")
            with col2:
                st.caption(f"买入价：{h.get('nav', 0):.3f}")
            with col3:
                if st.button("🗑️", key=f"del_{i}"):
                    holdings.pop(i)
                    save_holdings(holdings)
                    st.rerun()
            st.divider()
        
        if st.button("清空全部持仓", use_container_width=True):
            save_holdings([])
            st.rerun()
    else:
        st.info("📭 暂无持仓")

st.caption("⚠️ 本系统为学习演示工具")
