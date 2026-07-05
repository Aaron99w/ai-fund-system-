import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import random
import json
import requests
from collections import Counter

# ==================== 页面设置 ====================
st.set_page_config(
    page_title="🤖 AI基金投顾 终极版",
    page_icon="📊",
    layout="wide"
)

st.title("🤖 AI基金投顾 终极版")
st.caption("📊 200+基金 · 短线模式 · 卖出提醒 · 投资决策 · 微信通知")

# ==================== 微信通知配置 ====================
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的key"

def send_wechat_message(content):
    if not WEBHOOK_URL or "你的key" in WEBHOOK_URL:
        return False, "⚠️ 请先配置 Webhook 地址"
    try:
        data = {"msgtype": "text", "text": {"content": content[:2000]}}
        response = requests.post(WEBHOOK_URL, json=data, timeout=5)
        if response.status_code == 200:
            return True, "✅ 微信通知已发送"
        else:
            return False, f"❌ 发送失败：{response.status_code}"
    except Exception as e:
        return False, f"❌ 发送失败：{str(e)}"

# ==================== 短线ETF基金池 ====================
SHORT_TERM_ETFS = [
    {"name": "中概互联ETF", "code": "513050", "type": "T+0", "sector": "互联网", "volatility": "高"},
    {"name": "纳指ETF", "code": "513100", "type": "T+0", "sector": "美股", "volatility": "高"},
    {"name": "恒生ETF", "code": "159920", "type": "T+0", "sector": "港股", "volatility": "中高"},
    {"name": "恒生科技ETF", "code": "513130", "type": "T+0", "sector": "港股科技", "volatility": "高"},
    {"name": "标普500ETF", "code": "513500", "type": "T+0", "sector": "美股", "volatility": "中"},
    {"name": "沪深300ETF", "code": "510300", "type": "T+1", "sector": "大盘", "volatility": "中"},
    {"name": "中证500ETF", "code": "510500", "type": "T+1", "sector": "中小盘", "volatility": "中高"},
    {"name": "创业板ETF", "code": "159915", "type": "T+1", "sector": "创业板", "volatility": "高"},
    {"name": "科创50ETF", "code": "588000", "type": "T+1", "sector": "科创板", "volatility": "高"},
    {"name": "半导体ETF", "code": "512480", "type": "T+1", "sector": "半导体", "volatility": "高"},
    {"name": "芯片ETF", "code": "159995", "type": "T+1", "sector": "芯片", "volatility": "高"},
    {"name": "新能源车ETF", "code": "515030", "type": "T+1", "sector": "新能源", "volatility": "高"},
    {"name": "光伏ETF", "code": "515790", "type": "T+1", "sector": "光伏", "volatility": "高"},
    {"name": "军工ETF", "code": "512660", "type": "T+1", "sector": "军工", "volatility": "高"},
    {"name": "证券ETF", "code": "512880", "type": "T+1", "sector": "券商", "volatility": "中高"},
    {"name": "银行ETF", "code": "512800", "type": "T+1", "sector": "银行", "volatility": "低"},
    {"name": "消费ETF", "code": "159928", "type": "T+1", "sector": "消费", "volatility": "中"},
    {"name": "医药ETF", "code": "512010", "type": "T+1", "sector": "医药", "volatility": "中高"},
    {"name": "酒ETF", "code": "512690", "type": "T+1", "sector": "白酒", "volatility": "中高"},
    {"name": "人工智能ETF", "code": "159819", "type": "T+1", "sector": "AI", "volatility": "高"},
    {"name": "机器人ETF", "code": "562500", "type": "T+1", "sector": "机器人", "volatility": "高"},
    {"name": "5G通信ETF", "code": "515050", "type": "T+1", "sector": "5G", "volatility": "高"},
]

# ==================== 卖出信号分析函数 ====================
def analyze_sell_signals(holding, current_price, buy_price, market_sentiment, holding_days):
    signals = []
    profit_rate = (current_price - buy_price) / buy_price * 100
    is_etf = any(e["code"] == holding["code"] for e in SHORT_TERM_ETFS)
    
    if profit_rate >= 15:
        signals.append({
            "level": "🔴 强烈卖出",
            "reason": f"✅ 已达到止盈线（+{profit_rate:.1f}%），建议立即止盈",
            "action": "卖出",
            "urgency": "高"
        })
    elif profit_rate >= 10:
        signals.append({
            "level": "🟡 考虑止盈",
            "reason": f"📈 已盈利{profit_rate:.1f}%，接近止盈线（15%），可考虑分批止盈",
            "action": "分批止盈",
            "urgency": "中"
        })
    elif profit_rate >= 5:
        signals.append({
            "level": "🟢 继续持有",
            "reason": f"📊 已盈利{profit_rate:.1f}%，趋势良好，可继续持有",
            "action": "持有",
            "urgency": "低"
        })
    
    if profit_rate <= -8:
        signals.append({
            "level": "🔴 止损提醒",
            "reason": f"⚠️ 已亏损{profit_rate:.1f}%，触发止损线（-8%），建议止损离场",
            "action": "止损卖出",
            "urgency": "高"
        })
    elif profit_rate <= -5:
        signals.append({
            "level": "🟡 关注风险",
            "reason": f"📉 已亏损{profit_rate:.1f}%，接近止损线（-8%），密切关注",
            "action": "观察等待",
            "urgency": "中"
        })
    
    if is_etf and holding_days >= 7:
        signals.append({
            "level": "🟡 短线提醒",
            "reason": f"⏰ 已持有{holding_days}天，短线操作建议考虑获利了结",
            "action": "考虑卖出",
            "urgency": "中"
        })
    
    if market_sentiment == "悲观" and profit_rate > 0:
        signals.append({
            "level": "🟡 市场预警",
            "reason": "📊 市场情绪转为悲观，建议减仓保护利润",
            "action": "减仓",
            "urgency": "中"
        })
    elif market_sentiment == "乐观" and profit_rate < -3:
        signals.append({
            "level": "🟢 机会信号",
            "reason": "📈 市场情绪乐观，持仓亏损有望反弹，建议持有",
            "action": "持有等待",
            "urgency": "低"
        })
    
    if holding.get("position", 0) > 70 and profit_rate > 5:
        signals.append({
            "level": "🟡 估值提醒",
            "reason": f"📊 当前估值位置{holding.get('position', 0)}%，偏高，建议部分止盈",
            "action": "部分止盈",
            "urgency": "中"
        })
    
    if not signals:
        signals.append({
            "level": "🟢 正常持有",
            "reason": "📊 当前无卖出信号，建议继续持有观察",
            "action": "持有",
            "urgency": "低"
        })
    
    has_high_risk = any(s["urgency"] == "高" for s in signals)
    has_medium_risk = any(s["urgency"] == "中" for s in signals)
    
    if has_high_risk:
        overall = "🔴 建议立即卖出"
        summary = "检测到高风险信号，建议尽快操作"
    elif has_medium_risk:
        overall = "🟡 建议关注"
        summary = "存在中等风险信号，建议关注并准备操作"
    else:
        overall = "🟢 继续持有"
        summary = "持仓正常，暂无卖出信号"
    
    return {
        "signals": signals,
        "overall": overall,
        "summary": summary,
        "profit_rate": profit_rate,
        "has_high_risk": has_high_risk,
        "has_medium_risk": has_medium_risk
    }

def auto_check_all_holdings(holdings, market_sentiment):
    if not holdings:
        return []
    results = []
    for h in holdings:
        try:
            buy_date = datetime.strptime(h["buy_date"], "%Y-%m-%d")
            holding_days = (datetime.now() - buy_date).days
        except:
            holding_days = 0
        current_price = h.get("nav", 1.0) * random.uniform(0.88, 1.15)
        buy_price = h.get("nav", 1.0)
        h["position"] = random.randint(20, 80)
        result = analyze_sell_signals(h, current_price, buy_price, market_sentiment, holding_days)
        results.append({
            "fund_name": h["name"],
            "fund_code": h["code"],
            "buy_price": buy_price,
            "current_price": current_price,
            "holding_days": holding_days,
            "analysis": result
        })
    return results

def get_short_term_signal(etf_code):
    signals = {
        "趋势": random.choice(["多头排列", "空头排列", "震荡整理"]),
        "RSI": random.randint(20, 80),
        "MACD": random.choice(["金叉", "死叉", "粘合"]),
        "量能": random.choice(["放量", "缩量", "正常"]),
        "支撑位": round(random.uniform(0.92, 1.02), 3),
        "压力位": round(random.uniform(1.03, 1.15), 3),
        "布林带": random.choice(["上轨", "中轨", "下轨"]),
        "现价": round(random.uniform(0.8, 2.5), 3),
    }
    score = 50
    if signals["趋势"] == "多头排列":
        score += 15
    elif signals["趋势"] == "空头排列":
        score -= 15
    if signals["RSI"] < 30:
        score += 10
    elif signals["RSI"] > 70:
        score -= 10
    if signals["MACD"] == "金叉":
        score += 10
    elif signals["MACD"] == "死叉":
        score -= 10
    if signals["量能"] == "放量":
        score += 8
    elif signals["量能"] == "缩量":
        score -= 5
    if signals["布林带"] == "下轨":
        score += 8
    elif signals["布林带"] == "上轨":
        score -= 8
    signals["综合评分"] = max(0, min(100, score))
    if signals["综合评分"] >= 70:
        signals["操作建议"] = "📈 买入/加仓"
        signals["建议理由"] = "技术指标偏多，量价配合良好"
        signals["仓位建议"] = "60-80%"
    elif signals["综合评分"] >= 50:
        signals["操作建议"] = "⏳ 持有/观望"
        signals["建议理由"] = "技术指标中性，等待方向明确"
        signals["仓位建议"] = "30-50%"
    else:
        signals["操作建议"] = "📉 卖出/减仓"
        signals["建议理由"] = "技术指标偏空，注意风险"
        signals["仓位建议"] = "10-30%"
    return signals

# ==================== 核心长线基金池 ====================
FUNDS = [
    {"name": "前海开源人工智能混合", "code": "001986", "style": "科技", "nav": 2.85, "risk": "高", "return_1y": "+18.5%", "return_3y": "+42.5%", "max_dd": "-25.3%", "sharpe": 0.85},
    {"name": "万家人工智能混合", "code": "006281", "style": "科技", "nav": 1.92, "risk": "高", "return_1y": "+15.2%", "return_3y": "+38.2%", "max_dd": "-28.1%", "sharpe": 0.78},
    {"name": "中欧时代先锋股票A", "code": "001938", "style": "科技", "nav": 1.87, "risk": "高", "return_1y": "+22.8%", "return_3y": "+51.3%", "max_dd": "-26.7%", "sharpe": 0.95},
    {"name": "易方达蓝筹精选混合", "code": "005827", "style": "消费", "nav": 2.56, "risk": "中", "return_1y": "+10.2%", "return_3y": "+28.6%", "max_dd": "-18.5%", "sharpe": 0.72},
    {"name": "易方达中小盘混合", "code": "110011", "style": "消费", "nav": 3.21, "risk": "中", "return_1y": "+12.5%", "return_3y": "+32.4%", "max_dd": "-20.1%", "sharpe": 0.78},
    {"name": "景顺长城新兴成长混合", "code": "260108", "style": "消费", "nav": 3.87, "risk": "中", "return_1y": "+14.8%", "return_3y": "+35.2%", "max_dd": "-19.8%", "sharpe": 0.82},
    {"name": "汇添富消费行业混合", "code": "000083", "style": "消费", "nav": 4.12, "risk": "中", "return_1y": "+16.2%", "return_3y": "+38.7%", "max_dd": "-17.6%", "sharpe": 0.85},
    {"name": "中欧医疗健康混合A", "code": "003095", "style": "医药", "nav": 2.34, "risk": "高", "return_1y": "+18.6%", "return_3y": "+45.8%", "max_dd": "-28.6%", "sharpe": 0.82},
    {"name": "汇添富创新医药混合", "code": "006113", "style": "医药", "nav": 1.98, "risk": "高", "return_1y": "+14.5%", "return_3y": "+38.2%", "max_dd": "-26.8%", "sharpe": 0.76},
    {"name": "广发医疗保健股票A", "code": "004851", "style": "医药", "nav": 3.12, "risk": "高", "return_1y": "+16.8%", "return_3y": "+42.6%", "max_dd": "-27.4%", "sharpe": 0.80},
    {"name": "交银阿尔法核心混合", "code": "519712", "style": "均衡", "nav": 3.21, "risk": "中", "return_1y": "+12.6%", "return_3y": "+32.4%", "max_dd": "-16.5%", "sharpe": 0.82},
    {"name": "兴全合润混合", "code": "163406", "style": "均衡", "nav": 4.56, "risk": "中", "return_1y": "+16.8%", "return_3y": "+42.3%", "max_dd": "-18.2%", "sharpe": 0.90},
    {"name": "富国天惠成长混合", "code": "161005", "style": "均衡", "nav": 3.67, "risk": "中", "return_1y": "+14.2%", "return_3y": "+35.6%", "max_dd": "-17.8%", "sharpe": 0.86},
    {"name": "睿远成长价值混合A", "code": "007119", "style": "均衡", "nav": 2.13, "risk": "中", "return_1y": "+10.8%", "return_3y": "+26.8%", "max_dd": "-20.5%", "sharpe": 0.72},
    {"name": "前海开源沪港深优势精选", "code": "001875", "style": "港股", "nav": 2.85, "risk": "中高", "return_1y": "+15.6%", "return_3y": "+38.6%", "max_dd": "-22.8%", "sharpe": 0.80},
    {"name": "诺安成长混合", "code": "320007", "style": "芯片", "nav": 2.34, "risk": "高", "return_1y": "+22.6%", "return_3y": "+52.3%", "max_dd": "-34.5%", "sharpe": 0.72},
    {"name": "银河创新成长混合", "code": "519674", "style": "芯片", "nav": 4.56, "risk": "高", "return_1y": "+28.4%", "return_3y": "+62.8%", "max_dd": "-36.2%", "sharpe": 0.76},
    {"name": "农银新能源主题混合", "code": "002190", "style": "新能源", "nav": 3.45, "risk": "高", "return_1y": "+24.6%", "return_3y": "+55.8%", "max_dd": "-32.4%", "sharpe": 0.82},
    {"name": "华夏能源革新股票", "code": "003834", "style": "新能源", "nav": 2.89, "risk": "高", "return_1y": "+18.2%", "return_3y": "+45.2%", "max_dd": "-30.6%", "sharpe": 0.76},
    {"name": "工银瑞信金融地产混合", "code": "000251", "style": "金融", "nav": 2.34, "risk": "中低", "return_1y": "+6.8%", "return_3y": "+16.8%", "max_dd": "-12.5%", "sharpe": 0.56},
]

def get_market_sentiment():
    sentiments = ["乐观", "中性", "谨慎", "悲观"]
    weights = [0.25, 0.40, 0.25, 0.10]
    return np.random.choice(sentiments, p=weights)

def get_market_position():
    return random.randint(20, 80)

def get_timing_signal():
    signals = ["强烈买入", "买入", "持有", "减仓", "卖出"]
    weights = [0.12, 0.23, 0.38, 0.17, 0.10]
    return np.random.choice(signals, p=weights)

def calculate_fund_score(fund):
    score = 0
    ret_1y = float(fund["return_1y"].replace("%", "").replace("+", ""))
    score += min(30, max(0, (ret_1y + 20) * 1.0))
    ret_3y = float(fund["return_3y"].replace("%", "").replace("+", ""))
    score += min(25, max(0, (ret_3y + 15) * 0.7))
    dd = float(fund["max_dd"].replace("%", "").replace("-", ""))
    score += min(20, max(0, 20 - dd * 0.7))
    sharpe = fund["sharpe"]
    score += min(15, max(0, sharpe * 15))
    style_weights = {"科技": 1.2, "芯片": 1.3, "新能源": 1.2, "医药": 1.1, "消费": 1.0, "均衡": 1.0, "港股": 0.9, "军工": 1.0, "金融": 0.8}
    score += min(10, max(0, style_weights.get(fund["style"], 1.0) * 8))
    return min(100, round(score))

def ai_recommend(total_amount, risk_preference="中", existing_holdings=[], count=5):
    available = [f for f in FUNDS if f["code"] not in [h["code"] for h in existing_holdings]]
    risk_map = {"低": ["低", "中低"], "中": ["中低", "中", "中高"], "高": ["中高", "高"]}
    available = [f for f in available if f["risk"] in risk_map.get(risk_preference, ["中"])]
    if len(available) < count:
        available = FUNDS[:count * 2]
    for f in available:
        f["ai_score"] = calculate_fund_score(f)
    available = sorted(available, key=lambda x: x["ai_score"], reverse=True)
    recommendations = []
    for f in available[:count]:
        total_score = f["ai_score"] + random.randint(-5, 5)
        
        # ===== 详细推荐理由 =====
        reason_parts = []
        ret_3y_num = float(f["return_3y"].replace("%", "").replace("+", ""))
        if ret_3y_num > 30:
            reason_parts.append(f"🔥 近3年涨幅{ret_3y_num:.0f}%，业绩亮眼")
        elif ret_3y_num > 15:
            reason_parts.append(f"📈 近3年涨幅{ret_3y_num:.0f}%，表现稳健")
        else:
            reason_parts.append(f"📊 近3年涨幅{ret_3y_num:.0f}%，有待观察")
        
        dd_num = float(f["max_dd"].replace("%", "").replace("-", ""))
        if dd_num < 20:
            reason_parts.append(f"🛡️ 最大回撤{dd_num:.0f}%，风控较好")
        elif dd_num < 30:
            reason_parts.append(f"⚖️ 最大回撤{dd_num:.0f}%，波动适中")
        else:
            reason_parts.append(f"📉 最大回撤{dd_num:.0f}%，波动较大需注意")
        
        if f["sharpe"] > 0.8:
            reason_parts.append(f"⭐ 夏普比率{f['sharpe']:.2f}，性价比高")
        elif f["sharpe"] > 0.5:
            reason_parts.append(f"💡 夏普比率{f['sharpe']:.2f}，性价比较好")
        else:
            reason_parts.append(f"📊 夏普比率{f['sharpe']:.2f}，性价比一般")
        
        style_advice = {
            "科技": "科技赛道成长性强，适合进取型投资者",
            "消费": "消费行业长期稳健，适合价值投资者",
            "医药": "医药赛道刚需强劲，长期配置价值高",
            "均衡": "均衡配置分散风险，适合稳健型投资者",
            "芯片": "芯片国产替代空间大，高弹性高风险",
            "新能源": "新能源是长期趋势，政策持续利好",
            "港股": "港股估值偏低，有估值修复机会",
            "军工": "军工行业景气度提升，主题投资机会",
            "金融": "金融板块股息率高，适合保守型投资者"
        }
        reason_parts.append(f"📌 {style_advice.get(f['style'], f'{f['style']}风格适合当前配置')}")
        
        if total_score > 80:
            advice = "🌟 综合表现优秀，建议重点配置"
        elif total_score > 65:
            advice = "✅ 综合表现良好，建议适量配置"
        elif total_score > 50:
            advice = "📊 综合表现一般，建议小仓位参与"
        else:
            advice = "⚠️ 综合表现偏弱，建议谨慎参与"
        reason_parts.append(f"💡 {advice}")
        
        recommendations.append({
            "name": f["name"],
            "code": f["code"],
            "style": f["style"],
            "risk": f["risk"],
            "score": min(100, max(50, total_score)),
            "suggest_amount": round(total_amount * random.uniform(0.15, 0.30), 0),
            "return_3y": f["return_3y"],
            "max_dd": f["max_dd"],
            "sharpe": f["sharpe"],
            "reason": " | ".join(reason_parts)
        })
    return recommendations

def ai_portfolio_analysis(holdings, total_amount):
    if not holdings:
        return None
    total_cost = sum(h["amount"] for h in holdings)
    total_current = sum(h["amount"] * random.uniform(0.88, 1.15) for h in holdings)
    profit = total_current - total_cost
    profit_rate = (profit / total_cost) * 100 if total_cost > 0 else 0
    style_dist = {}
    for h in holdings:
        f = next((x for x in FUNDS if x["code"] == h["code"]), None)
        if f:
            style_dist[f["style"]] = style_dist.get(f["style"], 0) + h["amount"]
    max_style_ratio = max(style_dist.values()) / total_cost if style_dist else 0
    return {
        "total_cost": total_cost,
        "total_current": total_current,
        "profit": profit,
        "profit_rate": profit_rate,
        "style_distribution": style_dist,
        "max_style_ratio": max_style_ratio,
        "count": len(holdings),
        "remaining": total_amount - total_cost
    }

# ==================== 初始化 ====================
if "holdings" not in st.session_state:
    st.session_state.holdings = []
if "recommendations" not in st.session_state:
    st.session_state.recommendations = []
if "sell_alerts" not in st.session_state:
    st.session_state.sell_alerts = []
if "wechat_status" not in st.session_state:
    st.session_state.wechat_status = ""

# ==================== 侧边栏 ====================
with st.sidebar:
    st.header("💰 我的资产")
    total_cash = st.number_input("总资金（元）", min_value=0, value=10000, step=1000)
    risk_level = st.selectbox("风险偏好", ["低（保本为主）", "中（稳健增值）", "高（追求高收益）"], index=1)
    risk_map = {"低（保本为主）": "低", "中（稳健增值）": "中", "高（追求高收益）": "高"}
    risk_pref = risk_map[risk_level]
    
    st.divider()
    st.subheader("📱 微信通知")
    if st.button("📤 测试通知", use_container_width=True):
        success, msg = send_wechat_message("✅ AI基金投顾 Pro 微信通知测试成功！")
        st.session_state.wechat_status = msg
        st.rerun()
    if st.session_state.wechat_status:
        st.caption(st.session_state.wechat_status)
    
    st.divider()
    analysis = ai_portfolio_analysis(st.session_state.holdings, total_cash)
    if analysis:
        st.subheader("📊 持仓概览")
        c1, c2 = st.columns(2)
        c1.metric("总投入", f"{analysis['total_cost']:.0f}元")
        c2.metric("收益率", f"{analysis['profit_rate']:.1f}%", delta=f"{analysis['profit_rate']:.1f}%")

# ==================== 主界面 ====================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📈 短线操作",
    "📊 卖出提醒",
    "🤖 AI推荐",
    "📋 持仓管理",
    "🧠 智能分析",
    "📊 投资决策",
    "📈 市场信号"
])

# ==================== Tab1: 短线操作 ====================
with tab1:
    st.subheader("📈 短线基金操作模式")
    st.caption("⚡ 针对ETF/T+0基金的短线技术分析 | 适合1-7天短线操作")

    col1, col2 = st.columns([2, 1])
    with col1:
        etf_names = [f"{e['name']} ({e['code']})" for e in SHORT_TERM_ETFS]
        selected_etf = st.selectbox("选择短线基金", etf_names, key="short_select")
        etf_code = selected_etf.split("(")[-1].replace(")", "")
        etf_info = next((e for e in SHORT_TERM_ETFS if e["code"] == etf_code), SHORT_TERM_ETFS[0])
    with col2:
        st.info(f"📌 {etf_info['name']}")
        st.caption(f"类型：{etf_info['type']} | 板块：{etf_info['sector']} | 波动：{etf_info['volatility']}")

    if st.button("📊 分析技术信号", use_container_width=True, type="primary"):
        with st.spinner("分析中..."):
            result = get_short_term_signal(etf_code)
            st.success("✅ 分析完成！")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("综合评分", f"{result['综合评分']}/100")
            col2.metric("趋势", result["趋势"])
            col3.metric("RSI", f"{result['RSI']}")
            col4.metric("MACD", result["MACD"])
            
            st.subheader("📌 操作建议")
            if result["操作建议"] == "📈 买入/加仓":
                st.success(f"### {result['操作建议']}")
            elif result["操作建议"] == "⏳ 持有/观望":
                st.info(f"### {result['操作建议']}")
            else:
                st.error(f"### {result['操作建议']}")
            st.caption(f"💡 {result['建议理由']}")
            st.caption(f"📊 建议仓位：{result['仓位建议']}")
            
            st.subheader("📊 技术指标详情")
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"📈 支撑位：{result['支撑位']}")
                st.write(f"📉 压力位：{result['压力位']}")
                st.write(f"📊 布林带位置：{result['布林带']}")
            with c2:
                st.write(f"📊 KDJ：{result['KDJ']}")
                st.write(f"📊 量能：{result['量能']}")
                st.write(f"💰 现价：{result['现价']}")

# ==================== Tab2: 卖出提醒 ====================
with tab2:
    st.subheader("📊 持仓卖出信号分析")
    st.caption("🔔 AI自动分析每只持仓，提醒你什么时候该卖出")
    
    market = get_market_sentiment()
    st.info(f"📊 当前市场情绪：{market}")
    
    if st.button("🔍 扫描所有持仓", use_container_width=True, type="primary"):
        with st.spinner("AI正在扫描所有持仓..."):
            time.sleep(1.5)
            results = auto_check_all_holdings(st.session_state.holdings, market)
            st.session_state.sell_alerts = results
            
            if results:
                high_risk_count = sum(1 for r in results if r["analysis"]["has_high_risk"])
                medium_risk_count = sum(1 for r in results if r["analysis"]["has_medium_risk"])
                
                col1, col2, col3 = st.columns(3)
                col1.metric("总持仓", f"{len(results)}只")
                col2.metric("🔴 高风险", f"{high_risk_count}只", delta="建议立即处理" if high_risk_count > 0 else "安全")
                col3.metric("🟡 中风险", f"{medium_risk_count}只", delta="建议关注" if medium_risk_count > 0 else "安全")
                
                if high_risk_count > 0:
                    st.warning(f"⚠️ 检测到 {high_risk_count} 只基金出现高风险信号，建议尽快处理！")
                    send_wechat_message(f"⚠️ 卖出提醒：检测到 {high_risk_count} 只基金出现高风险信号，请登录系统查看详情")
                
                st.divider()
                
                for r in results:
                    with st.container():
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            st.write(f"**{r['fund_name']}**")
                            st.caption(f"代码：{r['fund_code']} | 持有{r['holding_days']}天")
                        with col2:
                            profit = r['analysis']['profit_rate']
                            if profit > 0:
                                st.metric("盈亏", f"+{profit:.1f}%", delta="盈利", delta_color="normal")
                            else:
                                st.metric("盈亏", f"{profit:.1f}%", delta="亏损", delta_color="inverse")
                        with col3:
                            st.write(r['analysis']['overall'])
                        
                        for signal in r['analysis']['signals']:
                            if "🔴" in signal['level']:
                                st.error(f"**{signal['level']}**：{signal['reason']}")
                            elif "🟡" in signal['level']:
                                st.warning(f"**{signal['level']}**：{signal['reason']}")
                            else:
                                st.success(f"**{signal['level']}**：{signal['reason']}")
                            st.caption(f"🎯 建议操作：{signal['action']}")
                        
                        st.divider()
            else:
                st.info("📭 暂无持仓，请先添加基金")
    
    if not st.session_state.sell_alerts and st.session_state.holdings:
        st.info("💡 点击「扫描所有持仓」获取卖出信号分析")
    elif not st.session_state.holdings:
        st.info("📭 暂无持仓，请先在「持仓管理」添加基金")

# ==================== Tab3: AI推荐 ====================
with tab3:
    st.subheader("🤖 AI智能基金推荐")
    st.caption("📊 基于多因子评分（收益+回撤+夏普+风格）")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"💰 {total_cash:,.0f}元 | 🎯 {risk_level} | 📊 持仓{len(st.session_state.holdings)}只")
    with col2:
        if st.button("🔍 AI分析", use_container_width=True, type="primary"):
            with st.spinner("AI分析中..."):
                recommendations = ai_recommend(total_cash, risk_pref, st.session_state.holdings)
                st.session_state.recommendations = recommendations
                st.success("✅ 分析完成！")
    
    if st.session_state.recommendations:
        for i, rec in enumerate(st.session_state.recommendations, 1):
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                with col1:
                    st.write(f"**{i}. {rec['name']}**")
                    st.caption(f"{rec['code']} | {rec['style']} | 风险：{rec['risk']}")
                with col2:
                    st.metric("AI评分", f"{rec['score']}/100")
                with col3:
                    st.caption(f"近3年：{rec['return_3y']}")
                    st.caption(f"回撤：{rec['max_dd']}")
                with col4:
                    st.metric("建议投入", f"{rec['suggest_amount']:.0f}元")
                    if st.button(f"📥 买入", key=f"buy_{rec['code']}"):
                        st.session_state.holdings.append({
                            "code": rec["code"],
                            "name": rec["name"],
                            "amount": rec["suggest_amount"],
                            "buy_date": datetime.now().strftime("%Y-%m-%d"),
                            "nav": random.uniform(1.0, 4.0)
                        })
                        st.success(f"✅ 已添加 {rec['name']}")
                        st.rerun()
                
                # ===== 显示完整推荐理由 =====
                st.caption(f"💡 {rec['reason']}")
                st.divider()
    
    if not st.session_state.recommendations:
        st.info("💡 点击「AI分析」获取基金推荐")

# ==================== Tab4: 持仓管理 ====================
with tab4:
    st.subheader("📋 我的持仓")
    with st.expander("➕ 添加持仓", expanded=False):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            fund_names = [f"{f['name']} ({f['code']})" for f in FUNDS]
            selected = st.selectbox("选择基金", fund_names, key="add_select")
            code = selected.split("(")[-1].replace(")", "")
            fund = next((f for f in FUNDS if f["code"] == code), None)
        with col2:
            amount = st.number_input("金额（元）", min_value=100, value=1000, step=100)
        with col3:
            date = st.date_input("日期", datetime.now())
        if st.button("✅ 确认添加", use_container_width=True) and fund:
            st.session_state.holdings.append({
                "code": code,
                "name": fund["name"],
                "amount": amount,
                "buy_date": date.strftime("%Y-%m-%d"),
                "nav": fund["nav"]
            })
            st.success(f"✅ 已添加 {fund['name']}")
            st.rerun()
    
    if st.session_state.holdings:
        df = pd.DataFrame(st.session_state.holdings)
        df["当前净值"] = df["nav"] * random.uniform(0.88, 1.15)
        df["市值"] = df["amount"] / df["nav"] * df["当前净值"]
        df["盈亏"] = df["市值"] - df["amount"]
        df["盈亏率%"] = (df["盈亏"] / df["amount"]) * 100
        st.dataframe(df[["name", "amount", "buy_date", "市值", "盈亏", "盈亏率%"]],
                     column_config={
                         "name": "基金",
                         "amount": "投入",
                         "buy_date": "日期",
                         "市值": st.column_config.NumberColumn(format="%.2f元"),
                         "盈亏": st.column_config.NumberColumn(format="%.2f元"),
                         "盈亏率%": st.column_config.NumberColumn(format="%.2f%%")
                     },
                     use_container_width=True)
        
        with st.expander("🗑️ 删除持仓", expanded=False):
            idx = st.selectbox("选择要删除的", range(len(st.session_state.holdings)),
                              format_func=lambda i: st.session_state.holdings[i]["name"])
            if st.button("确认删除", use_container_width=True):
                st.session_state.holdings.pop(idx)
                st.rerun()
    else:
        st.info("📭 暂无持仓")

# ==================== Tab5: 智能分析 ====================
with tab5:
    st.subheader("🧠 AI智能分析")
    if st.button("📊 运行综合分析", use_container_width=True, type="primary"):
        with st.spinner("AI分析中..."):
            time.sleep(1.5)
            market = get_market_sentiment()
            timing = get_timing_signal()
            analysis = ai_portfolio_analysis(st.session_state.holdings, total_cash)
            if analysis:
                st.success("✅ 分析完成！")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("持仓数量", f"{analysis['count']}只")
                c2.metric("总收益率", f"{analysis['profit_rate']:.1f}%", delta=f"{analysis['profit_rate']:.1f}%")
                c3.metric("市场情绪", market)
                c4.metric("择时信号", timing)
                if analysis["style_distribution"]:
                    st.subheader("📊 持仓风格分布")
                    df_style = pd.DataFrame({
                        "风格": list(analysis["style_distribution"].keys()),
                        "金额": list(analysis["style_distribution"].values())
                    })
                    st.bar_chart(df_style.set_index("风格"))
            else:
                st.warning("请先添加持仓")

# ==================== Tab6: 投资决策 ====================
with tab6:
    st.subheader("📊 AI投资决策引擎")
    st.caption("结合历史回测 + 当前市场状态，AI告诉你现在能不能买")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        fund_names = [f"{f['name']} ({f['code']})" for f in FUNDS[:20]]
        decision_fund = st.selectbox("选择基金", fund_names, key="decision_select")
        decision_code = decision_fund.split("(")[-1].replace(")", "")
    with col2:
        decision_years = st.slider("回测年数", 1, 5, 2)
        decision_monthly = st.number_input("每月定投金额（元）", min_value=100, value=1000, step=100)
    
    if st.button("🧠 AI投资决策", use_container_width=True, type="primary"):
        with st.spinner("AI正在分析..."):
            time.sleep(1.5)
            market = get_market_sentiment()
            timing = get_timing_signal()
            position = get_market_position()
            
            score = random.randint(45, 85)
            if score >= 70:
                decision = "✅ 建议买入"
                action = "买入"
                detail = f"综合评分{score}分，市场情绪{market}，建议分批建仓"
            elif score >= 55:
                decision = "⏳ 建议观望"
                action = "观望"
                detail = f"综合评分{score}分，等待更好时机"
            else:
                decision = "🔴 不建议买入"
                action = "回避"
                detail = f"综合评分{score}分，建议等待"
            
            st.success("✅ 决策完成！")
            col1, col2, col3 = st.columns(3)
            col1.metric("综合评分", f"{score}/100")
            col2.metric("AI决策", action)
            col3.metric("市场情绪", market)
            st.info(f"💡 {detail}")

# ==================== Tab7: 市场信号 ====================
with tab7:
    st.subheader("📊 市场信号面板")
    market = get_market_sentiment()
    timing = get_timing_signal()
    position = get_market_position()
    col1, col2, col3 = st.columns(3)
    emoji = "😊" if market == "乐观" else "😐" if market == "中性" else "😰"
    col1.metric("市场情绪", f"{emoji} {market}")
    color = "🟢" if timing in ["强烈买入", "买入"] else "🟡" if timing in ["持有"] else "🔴"
    col2.metric("择时信号", f"{color} {timing}")
    col3.metric("估值位置", f"{position}%", delta="低估" if position < 30 else "高估" if position > 70 else "合理")
    st.info(f"💡 当前建议：{timing}信号，市场估值{position}%，{market}情绪")

# ==================== 底部 ====================
st.divider()
st.caption("⚠️ 本系统为学习演示工具，数据均为模拟，不构成投资建议")
st.caption("📊 AI基金投顾 Pro | 短线模式 · 卖出提醒 · 投资决策 · 微信通知")
