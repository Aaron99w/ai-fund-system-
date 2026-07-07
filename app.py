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
st.caption("📈 AI扫描 · 实时监控 · 组合分析 · 买卖提醒 · 微信通知")

# ==================== 数据持久化 ====================
HOLDINGS_FILE = "holdings.json"
MONITOR_FILE = "monitor_log.json"

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
        json.dump(holdings, f, ensure_ascii=False, indent=2, default=str)

def load_monitor_log():
    if os.path.exists(MONITOR_FILE):
        try:
            with open(MONITOR_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_monitor_log(log):
    with open(MONITOR_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2, default=str)

# ==================== 微信通知 ====================
WEBHOOK_URL = ""

def send_wechat_message(content):
    if not WEBHOOK_URL:
        return False
    try:
        data = {"msgtype": "text", "text": {"content": content[:2000]}}
        response = requests.post(WEBHOOK_URL, json=data, timeout=5)
        return response.status_code == 200
    except:
        return False

# ==================== 基金池 ====================
FUND_POOLS = {
    "场外基金": {
        "description": "适合长期定投，由基金经理主动管理",
        "list": [
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
    },
    "ETF": {
        "description": "适合短线交易和行业轮动，费用低、交易灵活",
        "list": [
            {"name": "科创50ETF", "code": "588000", "style": "科创板", "risk": "高"},
            {"name": "创业板ETF", "code": "159915", "style": "创业板", "risk": "高"},
            {"name": "芯片ETF", "code": "159995", "style": "半导体", "risk": "高"},
            {"name": "人工智能ETF", "code": "159819", "style": "AI", "risk": "高"},
            {"name": "新能源车ETF", "code": "515030", "style": "新能源", "risk": "高"},
        ]
    }
}

# ==================== AI买入决策 ====================
def ai_buy_decision(code, name, holding_type="场外基金", existing_holdings=[]):
    """AI判断是否值得买入"""
    # 模拟评分（真实环境接入akshare）
    score = random.randint(50, 95)
    reasons = []
    
    if score >= 70:
        reasons.append("✅ 综合评分较高")
        reasons.append("📈 技术指标向好")
    elif score >= 55:
        reasons.append("📊 综合评分中等")
        reasons.append("⏳ 建议观察")
    else:
        reasons.append("⚠️ 综合评分偏低")
        reasons.append("📉 建议等待")
    
    already_hold = any(h["code"] == code for h in existing_holdings)
    
    if already_hold:
        action = "hold"
        decision = "📌 已持有"
        advice = "已持有该基金，请勿重复买入"
    elif score >= 70:
        action = "strong_buy"
        decision = "✅ 强烈推荐买入"
        advice = f"综合评分{score}分，建议积极配置"
    elif score >= 55:
        action = "buy"
        decision = "📈 建议买入"
        advice = f"综合评分{score}分，建议适量买入"
    elif score >= 40:
        action = "wait"
        decision = "⏳ 建议观望"
        advice = f"综合评分{score}分，等待更好时机"
    else:
        action = "avoid"
        decision = "❌ 不建议买入"
        advice = f"综合评分{score}分，建议回避"
    
    return {
        "code": code,
        "name": name,
        "score": score,
        "decision": decision,
        "action": action,
        "advice": advice,
        "reasons": reasons,
        "already_hold": already_hold
    }

def scan_all_funds(category, existing_holdings=[]):
    """扫描所有基金"""
    pool = FUND_POOLS.get(category, FUND_POOLS["场外基金"])
    results = []
    for f in pool["list"]:
        result = ai_buy_decision(f["code"], f["name"], category, existing_holdings)
        result["style"] = f.get("style", "")
        result["risk"] = f.get("risk", "")
        results.append(result)
    return sorted(results, key=lambda x: x["score"], reverse=True)

# ==================== 初始化 ====================
if "total_cash" not in st.session_state:
    st.session_state.total_cash = 10000
if "scan_results" not in st.session_state:
    st.session_state.scan_results = []
if "monitor_results" not in st.session_state:
    st.session_state.monitor_results = []

# ==================== 侧边栏 ====================
with st.sidebar:
    st.header("💰 我的资产")
    total_cash = st.number_input("总资金（元）", min_value=1000, value=10000, step=1000)
    st.session_state.total_cash = total_cash
    
    st.divider()
    holdings = load_holdings()
    st.metric("持仓数量", f"{len(holdings)} 只")
    total_cost = sum(float(h.get("amount", 0)) for h in holdings)
    st.metric("已投入", f"{total_cost:.0f} 元")
    st.metric("剩余资金", f"{total_cash - total_cost:.0f} 元")

# ==================== 主界面 ====================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🧠 AI买入决策",
    "📊 持仓监控",
    "📈 组合分析",
    "📋 持仓管理",
    "📰 监控日志"
])

# ==================== Tab1: AI买入决策 ====================
with tab1:
    st.subheader("🧠 AI智能买入决策")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        category = st.selectbox("选择类别", list(FUND_POOLS.keys()))
    with col2:
        if st.button("🔍 全扫描", use_container_width=True, type="primary"):
            with st.spinner("AI扫描中..."):
                holdings = load_holdings()
                results = scan_all_funds(category, holdings)
                st.session_state.scan_results = results
                st.success(f"✅ 扫描完成 {len(results)} 只")
    
    if st.session_state.scan_results:
        results = st.session_state.scan_results
        strong = len([r for r in results if r["action"] == "strong_buy"])
        buy = len([r for r in results if r["action"] == "buy"])
        st.info(f"📊 强烈推荐 {strong} 只 | 建议买入 {buy} 只")
        
        for idx, r in enumerate(results):
            if r["action"] == "hold":
                continue
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                with col1:
                    st.write(f"**{r['name']}**")
                    st.caption(f"{r['code']} | {r.get('style', '')}")
                with col2:
                    st.metric("评分", f"{r['score']}/100")
                with col3:
                    if r["action"] == "strong_buy":
                        st.success("✅ 强烈推荐")
                    elif r["action"] == "buy":
                        st.info("📈 建议买入")
                    elif r["action"] == "wait":
                        st.warning("⏳ 观望")
                    else:
                        st.error("❌ 不建议")
                with col4:
                    if r["action"] in ["strong_buy", "buy"] and not r.get("already_hold", False):
                        if st.button("📥 买入", key=f"buy_{r['code']}_{idx}"):
                            holdings = load_holdings()
                            holdings.append({
                                "code": r["code"],
                                "name": r["name"],
                                "amount": 1000,
                                "buy_date": datetime.now().strftime("%Y-%m-%d"),
                                "nav": round(random.uniform(1.0, 2.5), 4),
                                "type": category
                            })
                            save_holdings(holdings)
                            st.success(f"✅ 买入 {r['name']} 1000元")
                            st.rerun()
                
                with st.expander(f"📊 评分详情（{r['score']}分）"):
                    for reason in r.get("reasons", []):
                        st.write(f"• {reason}")
                    st.caption(f"💡 {r['advice']}")
                st.divider()
    else:
        st.info("💡 点击「全扫描」让AI分析所有基金")

# ==================== Tab2: 持仓监控 ====================
with tab2:
    st.subheader("📊 持仓监控")
    
    holdings = load_holdings()
    if holdings:
        for h in holdings:
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{h['name']}**")
                    st.caption(f"买入价：{h.get('nav', 0):.3f}")
                with col2:
                    # 模拟盈亏
                    current = h.get('nav', 1.0) * random.uniform(0.92, 1.12)
                    profit = (current - h['nav']) / h['nav'] * 100
                    st.metric("盈亏", f"{'+' if profit > 0 else ''}{profit:.1f}%")
                with col3:
                    if profit > 5:
                        st.success("🟢 持有")
                    elif profit < -3:
                        st.error("🔴 关注")
                    else:
                        st.info("🟡 正常")
                st.divider()
    else:
        st.info("📭 暂无持仓")

# ==================== Tab3: 组合分析 ====================
with tab3:
    st.subheader("📈 组合分析")
    holdings = load_holdings()
    if holdings:
        total = sum(h["amount"] for h in holdings)
        st.metric("总投入", f"{total:.0f}元")
        df = pd.DataFrame(holdings)
        st.dataframe(df[["name", "amount", "buy_date"]], use_container_width=True)
    else:
        st.info("📭 暂无持仓")

# ==================== Tab4: 持仓管理 ====================
with tab4:
    st.subheader("📋 持仓管理")
    holdings = load_holdings()
    if holdings:
        for i, h in enumerate(holdings):
            col1, col2, col3 = st.columns([2, 1, 0.5])
            with col1:
                st.write(f"**{h['name']}**")
                st.caption(f"金额：{h['amount']}元")
            with col2:
                st.caption(f"买入价：{h.get('nav', 0):.3f}")
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

# ==================== Tab5: 监控日志 ====================
with tab5:
    st.subheader("📰 监控日志")
    logs = load_monitor_log()
    if logs:
        for log in logs[-5:]:
            st.write(f"📅 {log.get('time', '')}")
            st.divider()
    else:
        st.info("暂无日志")

# ==================== 底部 ====================
st.divider()
st.caption("⚠️ 本系统为学习演示工具，不构成投资建议")
