import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import json
import requests
import akshare as ak
import random

# ==================== 页面设置 ====================
st.set_page_config(
    page_title="🤖 AI基金投顾 真实数据版",
    page_icon="📊",
    layout="wide"
)

st.title("🤖 AI基金投顾 真实数据版")
st.caption("📊 实时行情 · 真实净值 · AI推荐 · 卖出提醒 · 微信通知")

# ==================== 微信通知配置 ====================
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=9f94cf9d-5c12-4ad3-a2d2-5ef15afc17bb"

def send_wechat_message(content):
    if not WEBHOOK_URL:
        return False, "⚠️ 未配置 Webhook 地址"
    try:
        data = {"msgtype": "text", "text": {"content": content[:2000]}}
        response = requests.post(WEBHOOK_URL, json=data, timeout=5)
        if response.status_code == 200:
            return True, "✅ 微信通知已发送"
        else:
            return False, f"❌ 发送失败：{response.status_code}"
    except Exception as e:
        return False, f"❌ 发送失败：{str(e)}"

# ==================== 真实数据获取函数 ====================
@st.cache_data(ttl=300)
def get_real_fund_nav(fund_code):
    try:
        df = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")
        if df.empty:
            return None
        df['净值日期'] = pd.to_datetime(df['净值日期'])
        df = df.sort_values('净值日期')
        return df
    except:
        return None

@st.cache_data(ttl=300)
def get_real_etf_price(etf_code):
    try:
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")
        df = ak.stock_zh_a_hist(symbol=etf_code, period="daily",
                                start_date=start_date, end_date=end_date, adjust="qfq")
        if df.empty:
            return None
        df['日期'] = pd.to_datetime(df['日期'])
        df = df.sort_values('日期')
        return df
    except:
        return None

@st.cache_data(ttl=300)
def get_real_market_index():
    try:
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        df = ak.stock_zh_index_hist(symbol="sh000300", period="daily",
                                    start_date=start_date, end_date=end_date)
        if df.empty:
            return None
        return df
    except:
        return None

@st.cache_data(ttl=300)
def get_real_news():
    try:
        df = ak.stock_news_em(symbol="头条")
        if df.empty:
            return []
        return df.head(10).to_dict('records')
    except:
        return []

# ==================== 短线ETF基金池 ====================
SHORT_TERM_ETFS = [
    {"name": "沪深300ETF", "code": "510300", "type": "T+1", "sector": "大盘"},
    {"name": "中证500ETF", "code": "510500", "type": "T+1", "sector": "中小盘"},
    {"name": "创业板ETF", "code": "159915", "type": "T+1", "sector": "创业板"},
    {"name": "科创50ETF", "code": "588000", "type": "T+1", "sector": "科创板"},
    {"name": "半导体ETF", "code": "512480", "type": "T+1", "sector": "半导体"},
    {"name": "芯片ETF", "code": "159995", "type": "T+1", "sector": "芯片"},
    {"name": "新能源车ETF", "code": "515030", "type": "T+1", "sector": "新能源"},
    {"name": "光伏ETF", "code": "515790", "type": "T+1", "sector": "光伏"},
    {"name": "军工ETF", "code": "512660", "type": "T+1", "sector": "军工"},
    {"name": "证券ETF", "code": "512880", "type": "T+1", "sector": "券商"},
    {"name": "银行ETF", "code": "512800", "type": "T+1", "sector": "银行"},
    {"name": "消费ETF", "code": "159928", "type": "T+1", "sector": "消费"},
    {"name": "医药ETF", "code": "512010", "type": "T+1", "sector": "医药"},
    {"name": "酒ETF", "code": "512690", "type": "T+1", "sector": "白酒"},
    {"name": "人工智能ETF", "code": "159819", "type": "T+1", "sector": "AI"},
]

# ==================== 基金池 ====================
FUNDS = [
    {"name": "前海开源人工智能混合", "code": "001986", "style": "科技"},
    {"name": "万家人工智能混合", "code": "006281", "style": "科技"},
    {"name": "中欧时代先锋股票A", "code": "001938", "style": "科技"},
    {"name": "易方达蓝筹精选混合", "code": "005827", "style": "消费"},
    {"name": "易方达中小盘混合", "code": "110011", "style": "消费"},
    {"name": "景顺长城新兴成长混合", "code": "260108", "style": "消费"},
    {"name": "汇添富消费行业混合", "code": "000083", "style": "消费"},
    {"name": "中欧医疗健康混合A", "code": "003095", "style": "医药"},
    {"name": "汇添富创新医药混合", "code": "006113", "style": "医药"},
    {"name": "广发医疗保健股票A", "code": "004851", "style": "医药"},
    {"name": "交银阿尔法核心混合", "code": "519712", "style": "均衡"},
    {"name": "兴全合润混合", "code": "163406", "style": "均衡"},
    {"name": "富国天惠成长混合", "code": "161005", "style": "均衡"},
    {"name": "睿远成长价值混合A", "code": "007119", "style": "均衡"},
    {"name": "前海开源沪港深优势精选", "code": "001875", "style": "港股"},
    {"name": "诺安成长混合", "code": "320007", "style": "芯片"},
    {"name": "银河创新成长混合", "code": "519674", "style": "芯片"},
    {"name": "农银新能源主题混合", "code": "002190", "style": "新能源"},
    {"name": "华夏能源革新股票", "code": "003834", "style": "新能源"},
    {"name": "工银瑞信金融地产混合", "code": "000251", "style": "金融"},
]

# ==================== 真实数据分析函数 ====================
def analyze_real_fund(fund_code):
    df = get_real_fund_nav(fund_code)
    if df is None or df.empty:
        return None
    nav = df['单位净值']
    latest_nav = nav.iloc[-1]
    latest_date = df['净值日期'].iloc[-1]
    ret_1m = (nav.iloc[-1] / nav.iloc[-22] - 1) * 100 if len(nav) >= 22 else 0
    ret_3m = (nav.iloc[-1] / nav.iloc[-66] - 1) * 100 if len(nav) >= 66 else 0
    ret_1y = (nav.iloc[-1] / nav.iloc[-242] - 1) * 100 if len(nav) >= 242 else 0
    cummax = nav.cummax()
    drawdown = (nav - cummax) / cummax * 100
    max_drawdown = drawdown.min()
    volatility = nav.pct_change().std() * np.sqrt(252) * 100
    returns = nav.pct_change().dropna()
    sharpe = (returns.mean() * 252 - 2.5) / (returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
    high_60 = nav.tail(60).max()
    low_60 = nav.tail(60).min()
    position = (latest_nav - low_60) / (high_60 - low_60) if high_60 != low_60 else 0.5
    return {
        "最新净值": round(latest_nav, 4),
        "最新日期": latest_date.strftime("%Y-%m-%d"),
        "近1月%": round(ret_1m, 2),
        "近3月%": round(ret_3m, 2),
        "近1年%": round(ret_1y, 2),
        "最大回撤%": round(max_drawdown, 2),
        "波动率%": round(volatility, 2),
        "夏普比率": round(sharpe, 3),
        "位置%": round(position * 100, 1),
        "历史净值": df[['净值日期', '单位净值']].tail(90).to_dict('records')
    }

def analyze_real_etf(etf_code):
    df = get_real_etf_price(etf_code)
    if df is None or df.empty:
        return None
    close = df['收盘']
    latest = close.iloc[-1]
    latest_date = df['日期'].iloc[-1]
    ret_1m = (close.iloc[-1] / close.iloc[-22] - 1) * 100 if len(close) >= 22 else 0
    ret_3m = (close.iloc[-1] / close.iloc[-66] - 1) * 100 if len(close) >= 66 else 0
    ma5 = close.rolling(5).mean().iloc[-1]
    ma20 = close.rolling(20).mean().iloc[-1]
    ma60 = close.rolling(60).mean().iloc[-1]
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    current_rsi = rsi.iloc[-1] if not rsi.empty else 50
    high_60 = close.tail(60).max()
    low_60 = close.tail(60).min()
    position = (latest - low_60) / (high_60 - low_60) if high_60 != low_60 else 0.5
    score = 50
    if latest > ma5 > ma20:
        score += 15
    elif latest < ma5 < ma20:
        score -= 15
    if current_rsi < 30:
        score += 10
    elif current_rsi > 70:
        score -= 10
    if position < 30:
        score += 8
    elif position > 70:
        score -= 8
    score = max(0, min(100, score))
    if score >= 70:
        signal = "📈 买入信号"
        action = "buy"
        detail = "技术指标偏多，均线多头排列"
    elif score >= 50:
        signal = "⏳ 持有观望"
        action = "hold"
        detail = "技术指标中性，等待方向明确"
    else:
        signal = "📉 卖出信号"
        action = "sell"
        detail = "技术指标偏空，注意风险"
    return {
        "现价": round(latest, 3),
        "最新日期": latest_date.strftime("%Y-%m-%d"),
        "近1月%": round(ret_1m, 2),
        "近3月%": round(ret_3m, 2),
        "MA5": round(ma5, 3),
        "MA20": round(ma20, 3),
        "MA60": round(ma60, 3),
        "RSI": round(current_rsi, 1),
        "位置%": round(position * 100, 1),
        "综合评分": round(score, 1),
        "信号": signal,
        "信号详情": detail,
        "操作建议": action,
        "历史数据": df[['日期', '收盘']].tail(90).to_dict('records')
    }

def calculate_fund_score(fund):
    """基于真实数据计算基金评分"""
    df = get_real_fund_nav(fund["code"])
    if df is None or df.empty:
        return 50
    nav = df['单位净值']
    ret_1y = (nav.iloc[-1] / nav.iloc[-242] - 1) * 100 if len(nav) >= 242 else 0
    ret_3m = (nav.iloc[-1] / nav.iloc[-66] - 1) * 100 if len(nav) >= 66 else 0
    cummax = nav.cummax()
    drawdown = (nav - cummax) / cummax * 100
    max_dd = drawdown.min()
    returns = nav.pct_change().dropna()
    sharpe = (returns.mean() * 252 - 2.5) / (returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
    score = 0
    score += min(30, max(0, ret_1y * 0.5 + 15))
    score += min(25, max(0, ret_3m * 0.5 + 10))
    dd_score = max(0, 20 + max_dd * 0.5)
    score += min(20, dd_score)
    score += min(15, max(0, sharpe * 10 + 5))
    style_weights = {"科技": 1.2, "芯片": 1.3, "新能源": 1.2, "医药": 1.1, "消费": 1.0, "均衡": 1.0, "港股": 0.9, "金融": 0.8}
    score += min(10, style_weights.get(fund["style"], 1.0) * 8)
    return min(100, round(score))

def ai_recommend(total_amount, risk_preference="中", existing_holdings=[], count=5):
    available = [f for f in FUNDS if f["code"] not in [h["code"] for h in existing_holdings]]
    risk_map = {"低": ["低", "中低"], "中": ["中低", "中", "中高"], "高": ["中高", "高"]}
    if len(available) < count:
        available = FUNDS[:count * 2]
    for f in available:
        f["ai_score"] = calculate_fund_score(f)
    available = sorted(available, key=lambda x: x["ai_score"], reverse=True)
    recommendations = []
    for f in available[:count]:
        total_score = f["ai_score"] + random.randint(-5, 5)
        reason_parts = []
        df = get_real_fund_nav(f["code"])
        if df is not None:
            nav = df['单位净值']
            ret_3y = (nav.iloc[-1] / nav.iloc[-726] - 1) * 100 if len(nav) >= 726 else 0
            if ret_3y > 30:
                reason_parts.append(f"🔥 近3年涨幅{ret_3y:.0f}%")
            else:
                reason_parts.append(f"📊 近3年涨幅{ret_3y:.0f}%")
        style_advice = {
            "科技": "科技赛道成长性强", "消费": "消费行业长期稳健",
            "医药": "医药刚需强劲", "均衡": "均衡配置分散风险",
            "芯片": "芯片国产替代空间大", "新能源": "新能源政策持续利好",
            "港股": "港股估值偏低", "金融": "金融板块股息率高"
        }
        reason_parts.append(f"📌 {style_advice.get(f['style'], f['style'])}")
        if total_score > 75:
            reason_parts.append("🌟 综合表现优秀")
        elif total_score > 60:
            reason_parts.append("✅ 综合表现良好")
        else:
            reason_parts.append("📊 综合表现一般")
        recommendations.append({
            "name": f["name"],
            "code": f["code"],
            "style": f["style"],
            "score": min(100, max(50, total_score)),
            "suggest_amount": round(total_amount * random.uniform(0.15, 0.30), 0),
            "reason": " | ".join(reason_parts)
        })
    return recommendations

def ai_portfolio_analysis(holdings, total_amount):
    if not holdings:
        return None
    total_cost = sum(h["amount"] for h in holdings)
    total_current = 0
    for h in holdings:
        df = get_real_fund_nav(h["code"])
        if df is not None:
            nav = df['单位净值'].iloc[-1]
            total_current += (h["amount"] / h["nav"]) * nav
        else:
            total_current += h["amount"]
    profit = total_current - total_cost
    profit_rate = (profit / total_cost) * 100 if total_cost > 0 else 0
    return {"total_cost": total_cost, "total_current": total_current, "profit": profit, "profit_rate": profit_rate, "count": len(holdings)}

def get_market_sentiment():
    try:
        df = get_real_market_index()
        if df is not None and not df.empty:
            ret = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100
            if ret > 2:
                return "乐观"
            elif ret > -2:
                return "中性"
            else:
                return "谨慎"
    except:
        pass
    return "中性"

def get_market_position():
    try:
        df = get_real_market_index()
        if df is not None and not df.empty:
            high = df['close'].max()
            low = df['close'].min()
            current = df['close'].iloc[-1]
            return round((current - low) / (high - low) * 100) if high != low else 50
    except:
        pass
    return random.randint(30, 70)

# ==================== 卖出信号分析 ====================
def analyze_sell_signals(holding, market_sentiment):
    df = get_real_fund_nav(holding["code"])
    if df is None:
        return None
    nav = df['单位净值']
    current_price = nav.iloc[-1]
    buy_price = holding["nav"]
    profit_rate = (current_price - buy_price) / buy_price * 100
    signals = []
    if profit_rate >= 10:
        signals.append({"level": "🔴 止盈", "reason": f"盈利{profit_rate:.1f}%，建议止盈", "action": "卖出"})
    elif profit_rate <= -8:
        signals.append({"level": "🔴 止损", "reason": f"亏损{profit_rate:.1f}%，建议止损", "action": "卖出"})
    else:
        signals.append({"level": "🟢 持有", "reason": f"盈亏{profit_rate:.1f}%，正常持有", "action": "持有"})
    return {"signals": signals, "profit_rate": profit_rate}

# ==================== 初始化 ====================
if "holdings" not in st.session_state:
    st.session_state.holdings = []
if "recommendations" not in st.session_state:
    st.session_state.recommendations = []
if "wechat_status" not in st.session_state:
    st.session_state.wechat_status = ""

# ==================== 侧边栏 ====================
with st.sidebar:
    st.header("💰 我的资产")
    total_cash = st.number_input("总资金（元）", min_value=0, value=10000, step=1000)
    risk_level = st.selectbox("风险偏好", ["低（保本为主）", "中（稳健增值）", "高（追求高收益）"], index=1)
    
    st.divider()
    st.subheader("📱 微信通知")
    if st.button("📤 测试通知", use_container_width=True):
        success, msg = send_wechat_message("✅ AI基金投顾 真实数据版 微信通知测试成功！")
        st.session_state.wechat_status = msg
        st.rerun()
    if st.session_state.wechat_status:
        st.caption(st.session_state.wechat_status)
    
    st.divider()
    st.subheader("📊 市场状态")
    market = get_market_sentiment()
    pos = get_market_position()
    emoji = "😊" if market == "乐观" else "😐" if market == "中性" else "😰"
    st.metric("市场情绪", f"{emoji} {market}")
    st.metric("估值位置", f"{pos}%")

# ==================== 主界面 ====================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🤖 AI推荐",
    "📊 基金分析",
    "📈 短线ETF",
    "📋 持仓管理",
    "📊 市场信号"
])

# ==================== Tab1: AI推荐 ====================
with tab1:
    st.subheader("🤖 AI智能基金推荐")
    st.caption("基于真实净值数据，多因子评分自动推荐")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"💰 {total_cash:,.0f}元 | 🎯 {risk_level} | 📊 持仓{len(st.session_state.holdings)}只")
    with col2:
        if st.button("🔍 AI分析", use_container_width=True, type="primary"):
            with st.spinner("AI分析中..."):
                recommendations = ai_recommend(total_cash, risk_level.replace("（保本为主）", "").replace("（稳健增值）", "").replace("（追求高收益）", ""), st.session_state.holdings)
                st.session_state.recommendations = recommendations
                st.success("✅ 分析完成！")
    
    if st.session_state.recommendations:
        for i, rec in enumerate(st.session_state.recommendations, 1):
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                with col1:
                    st.write(f"**{i}. {rec['name']}**")
                    st.caption(f"{rec['code']} | {rec['style']}")
                with col2:
                    st.metric("AI评分", f"{rec['score']}/100")
                with col3:
                    st.metric("建议投入", f"{rec['suggest_amount']:.0f}元")
                with col4:
                    if st.button(f"📥 买入", key=f"buy_{rec['code']}"):
                        nav_data = get_real_fund_nav(rec["code"])
                        nav = nav_data['单位净值'].iloc[-1] if nav_data is not None else 1.0
                        st.session_state.holdings.append({
                            "code": rec["code"],
                            "name": rec["name"],
                            "amount": rec["suggest_amount"],
                            "buy_date": datetime.now().strftime("%Y-%m-%d"),
                            "nav": nav
                        })
                        st.success(f"✅ 已添加 {rec['name']}")
                        st.rerun()
                st.caption(f"💡 {rec['reason']}")
                st.divider()

# ==================== Tab2: 基金分析 ====================
with tab2:
    st.subheader("📊 真实基金分析")
    st.caption("基于akshare真实净值数据")
    
    fund_names = [f"{f['name']} ({f['code']})" for f in FUNDS]
    selected_fund = st.selectbox("选择基金", fund_names, key="fund_select")
    fund_code = selected_fund.split("(")[-1].replace(")", "")
    
    if st.button("📊 分析", use_container_width=True, type="primary"):
        with st.spinner("正在获取真实数据..."):
            result = analyze_real_fund(fund_code)
            if result:
                st.success(f"✅ 数据获取成功！最新日期：{result['最新日期']}")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("最新净值", result['最新净值'])
                col2.metric("近1月", f"{result['近1月%']}%", delta=f"{result['近1月%']}%")
                col3.metric("近3月", f"{result['近3月%']}%", delta=f"{result['近3月%']}%")
                col4.metric("近1年", f"{result['近1年%']}%", delta=f"{result['近1年%']}%")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("最大回撤", f"{result['最大回撤%']}%")
                col2.metric("波动率", f"{result['波动率%']}%")
                col3.metric("夏普比率", result['夏普比率'])
                col4.metric("当前位置", f"{result['位置%']}%")
                if result.get('历史净值'):
                    hist_df = pd.DataFrame(result['历史净值'])
                    hist_df['净值日期'] = pd.to_datetime(hist_df['净值日期'])
                    st.line_chart(hist_df.set_index('净值日期')['单位净值'])
            else:
                st.error("❌ 数据获取失败，请检查基金代码或网络")

# ==================== Tab3: 短线ETF ====================
with tab3:
    st.subheader("📈 真实ETF短线分析")
    st.caption("基于akshare实时行情数据")
    
    etf_names = [f"{e['name']} ({e['code']})" for e in SHORT_TERM_ETFS]
    selected_etf = st.selectbox("选择ETF", etf_names, key="etf_select")
    etf_code = selected_etf.split("(")[-1].replace(")", "")
    
    if st.button("📊 分析技术信号", use_container_width=True, type="primary"):
        with st.spinner("正在获取真实行情..."):
            result = analyze_real_etf(etf_code)
            if result:
                st.success(f"✅ 数据获取成功！最新日期：{result['最新日期']}")
                col1, col2, col3 = st.columns(3)
                col1.metric("现价", result['现价'])
                col2.metric("综合评分", f"{result['综合评分']}/100")
                col3.metric("RSI", f"{result['RSI']}")
                st.subheader("📌 操作建议")
                if result['操作建议'] == "buy":
                    st.success(f"### {result['信号']}")
                elif result['操作建议'] == "sell":
                    st.error(f"### {result['信号']}")
                else:
                    st.info(f"### {result['信号']}")
                st.caption(f"💡 {result['信号详情']}")
                st.subheader("📊 技术指标")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("MA5", result['MA5'])
                c2.metric("MA20", result['MA20'])
                c3.metric("MA60", result['MA60'])
                c4.metric("位置", f"{result['位置%']}%")
                if result.get('历史数据'):
                    hist_df = pd.DataFrame(result['历史数据'])
                    hist_df['日期'] = pd.to_datetime(hist_df['日期'])
                    st.line_chart(hist_df.set_index('日期')['收盘'])
            else:
                st.error("❌ 数据获取失败，请检查ETF代码或网络")

# ==================== Tab4: 持仓管理 ====================
with tab4:
    st.subheader("📋 我的持仓")
    
    # 卖出提醒
    if st.session_state.holdings:
        market = get_market_sentiment()
        st.subheader("🔔 卖出信号扫描")
        for h in st.session_state.holdings:
            result = analyze_sell_signals(h, market)
            if result:
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**{h['name']}**")
                    st.caption(f"买入价：{h['nav']:.4f} | 盈亏：{result['profit_rate']:.1f}%")
                with col2:
                    for s in result['signals']:
                        if "🔴" in s['level']:
                            st.error(f"{s['level']}：{s['reason']}")
                        else:
                            st.success(f"{s['level']}：{s['reason']}")
                st.divider()
    
    with st.expander("➕ 添加持仓", expanded=False):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            all_funds = [f"{f['name']} ({f['code']})" for f in FUNDS]
            selected = st.selectbox("选择基金", all_funds, key="add_select")
            code = selected.split("(")[-1].replace(")", "")
            fund = next((f for f in FUNDS if f["code"] == code), None)
        with col2:
            amount = st.number_input("金额（元）", min_value=100, value=1000, step=100)
        with col3:
            date = st.date_input("日期", datetime.now())
        if st.button("✅ 确认添加", use_container_width=True) and fund:
            nav_data = get_real_fund_nav(code)
            nav = nav_data['单位净值'].iloc[-1] if nav_data is not None else 1.0
            st.session_state.holdings.append({
                "code": code,
                "name": fund["name"],
                "amount": amount,
                "buy_date": date.strftime("%Y-%m-%d"),
                "nav": nav
            })
            st.success(f"✅ 已添加 {fund['name']}，净值{nav:.4f}")
            st.rerun()
    
    if st.session_state.holdings:
        df = pd.DataFrame(st.session_state.holdings)
        latest_navs = []
        for h in st.session_state.holdings:
            nav_data = get_real_fund_nav(h["code"])
            latest_navs.append(nav_data['单位净值'].iloc[-1] if nav_data is not None else h["nav"])
        df["最新净值"] = latest_navs
        df["市值"] = df["amount"] / df["nav"] * df["最新净值"]
        df["盈亏"] = df["市值"] - df["amount"]
        df["盈亏率%"] = (df["盈亏"] / df["amount"]) * 100
        st.dataframe(df[["name", "amount", "buy_date", "最新净值", "市值", "盈亏", "盈亏率%"]],
                     column_config={
                         "name": "基金",
                         "amount": "投入",
                         "buy_date": "日期",
                         "最新净值": st.column_config.NumberColumn(format="%.4f"),
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

# ==================== Tab5: 市场信号 ====================
with tab5:
    st.subheader("📊 市场信号面板")
    market = get_market_sentiment()
    position = get_market_position()
    col1, col2 = st.columns(2)
    emoji = "😊" if market == "乐观" else "😐" if market == "中性" else "😰"
    col1.metric("市场情绪", f"{emoji} {market}")
    col2.metric("估值位置", f"{position}%")
    st.subheader("📈 沪深300走势")
    df = get_real_market_index()
    if df is not None and not df.empty:
        st.line_chart(df.set_index('日期')['close'])
    else:
        st.info("暂无数据")
    st.subheader("📰 财经快讯")
    news = get_real_news()
    if news:
        for item in news[:5]:
            st.write(f"📌 {item.get('新闻标题', '')}")
            st.caption(f"来源：{item.get('文章来源', '')} | {item.get('发布时间', '')}")
            st.divider()
    else:
        st.info("暂无新闻数据")

# ==================== 底部 ====================
st.divider()
st.caption("⚠️ 本系统为学习演示工具，数据来自akshare开源金融数据接口，不构成投资建议")
st.caption("📊 AI基金投顾 真实数据版 | AI推荐 · 真实净值 · 卖出提醒 · 微信通知")
