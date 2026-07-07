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
    page_title="📊 AI智能投资系统",
    page_icon="📈",
    layout="wide"
)

st.title("🧠 AI智能投资系统")
st.caption("📈 AI扫描 · 实时监控 · 组合分析 · 买卖提醒 · 微信通知")

# ==================== 数据持久化 ====================
HOLDINGS_FILE = "holdings.json"
MONITOR_FILE = "monitor_log.json"
REPORT_FILE = "report.json"

def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default
    return default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_holdings():
    return load_json(HOLDINGS_FILE, [])

def save_holdings(holdings):
    save_json(HOLDINGS_FILE, holdings)

def load_monitor_log():
    return load_json(MONITOR_FILE, [])

def save_monitor_log(log):
    save_json(MONITOR_FILE, log)

# ==================== 微信通知 ====================
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=9f94cf9d-5c12-4ad3-a2d2-5ef15afc17bb"

def send_wechat_message(content):
    if not WEBHOOK_URL:
        return False
    try:
        data = {"msgtype": "text", "text": {"content": content[:2000]}}
        response = requests.post(WEBHOOK_URL, json=data, timeout=5)
        return response.status_code == 200
    except:
        return False

# ==================== 真实数据获取 ====================
def get_fund_real_data(code):
    try:
        import akshare as ak
        df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
        if df is not None and not df.empty:
            df['净值日期'] = pd.to_datetime(df['净值日期'])
            df = df.sort_values('净值日期')
            df = df.rename(columns={'净值日期': '日期', '单位净值': '收盘'})
            df['收盘'] = df['收盘'].astype(float)
            return df
    except Exception as e:
        pass
    return None

def get_etf_real_data(code):
    try:
        import akshare as ak
        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=180)).strftime("%Y%m%d")
        df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start, end_date=end, adjust="qfq")
        if df is not None and not df.empty:
            df['日期'] = pd.to_datetime(df['日期'])
            df = df.sort_values('日期')
            df['收盘'] = df['收盘'].astype(float)
            return df
    except:
        pass
    return None

def get_fund_data(code, holding_type="场外基金"):
    if holding_type in ["场外基金", "普通基金"]:
        df = get_fund_real_data(code)
    else:
        df = get_etf_real_data(code)
    if df is not None:
        return df, "真实数据"
    # 模拟数据（保底）
    dates = pd.date_range(end=datetime.now(), periods=180, freq='D')
    random.seed(hash(code) % 100)
    base = random.uniform(1.0, 2.0)
    prices = [base]
    for i in range(179):
        change = np.random.normal(0.0003, 0.018)
        prices.append(prices[-1] * (1 + change))
    df = pd.DataFrame({'日期': dates, '收盘': prices})
    df['日期'] = pd.to_datetime(df['日期'])
    df['收盘'] = df['收盘'].astype(float)
    return df.sort_values('日期'), "模拟数据"

def get_current_price(code, holding_type="场外基金"):
    df, source = get_fund_data(code, holding_type)
    if df is not None and not df.empty:
        return float(df['收盘'].iloc[-1]), source
    return None, "无数据"

# ==================== 技术指标计算 ====================
def calculate_indicators(df):
    if df is None or len(df) < 30:
        return None
    close = df['收盘'].values
    latest = float(close[-1])
    # 均线
    ma20 = float(pd.Series(close).rolling(20).mean().values[-1]) if len(close) >= 20 else latest
    ma60 = float(pd.Series(close).rolling(60).mean().values[-1]) if len(close) >= 60 else latest
    # RSI
    if len(close) >= 14:
        delta = pd.Series(close).diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = float(rsi.iloc[-1]) if not rsi.empty else 50
    else:
        current_rsi = 50
    # 位置 (近60日)
    if len(close) >= 60:
        high_60 = float(pd.Series(close).tail(60).max())
        low_60 = float(pd.Series(close).tail(60).min())
        position = (latest - low_60) / (high_60 - low_60) if high_60 != low_60 else 0.5
    else:
        position = 0.5
    return {
        "latest": latest,
        "ma20": ma20,
        "ma60": ma60,
        "rsi": current_rsi,
        "position": position
    }

# ==================== AI买入决策 ====================
def ai_buy_decision(code, name, holding_type="场外基金", existing_holdings=[]):
    df, source = get_fund_data(code, holding_type)
    if df is None or df.empty or len(df) < 30:
        return {"decision": "❌ 无法分析", "score": 0, "reasons": ["数据不足"], "action": "wait"}
    
    indicators = calculate_indicators(df)
    if not indicators:
        return {"decision": "❌ 无法分析", "score": 0, "reasons": ["指标计算失败"], "action": "wait"}
    
    latest = indicators["latest"]
    ma20 = indicators["ma20"]
    ma60 = indicators["ma60"]
    rsi = indicators["rsi"]
    position = indicators["position"]
    
    already_hold = any(h["code"] == code for h in existing_holdings)
    
    score = 50
    reasons = []
    
    # 位置评分 (30分)
    if position < 0.2:
        score += 25
        reasons.append(f"✅ 价格处于历史低位（{position*100:.0f}%分位）")
    elif position < 0.35:
        score += 18
        reasons.append(f"✅ 价格偏低（{position*100:.0f}%分位）")
    elif position < 0.5:
        score += 10
        reasons.append(f"📊 价格适中（{position*100:.0f}%分位）")
    elif position < 0.7:
        score += 3
        reasons.append(f"📊 价格偏高（{position*100:.0f}%分位）")
    else:
        score -= 10
        reasons.append(f"⚠️ 价格高位（{position*100:.0f}%分位）")
    
    # 均线趋势 (25分)
    if latest > ma20 > ma60:
        score += 22
        reasons.append("✅ 均线多头排列")
    elif latest > ma20:
        score += 12
        reasons.append("📈 价格在MA20上方")
    elif latest > ma60:
        score += 5
        reasons.append("📊 价格在MA60上方")
    else:
        score -= 8
        reasons.append("⚠️ 价格在MA60下方")
    
    # RSI (20分)
    if rsi < 30:
        score += 18
        reasons.append(f"✅ RSI={rsi:.0f}超卖区")
    elif rsi < 40:
        score += 12
        reasons.append(f"📈 RSI={rsi:.0f}偏低")
    elif rsi < 60:
        score += 5
        reasons.append(f"📊 RSI={rsi:.0f}中性")
    elif rsi < 75:
        score -= 5
        reasons.append(f"⚠️ RSI={rsi:.0f}偏高")
    else:
        score -= 15
        reasons.append(f"⚠️ RSI={rsi:.0f}超买区")
    
    # 动量（近1月涨跌） (15分)
    close = df['收盘'].values
    ret_1m = (latest / close[-22] - 1) * 100 if len(close) >= 22 else 0
    if ret_1m > 5:
        score += 12
        reasons.append(f"✅ 近1月涨{ret_1m:.1f}%")
    elif ret_1m > 0:
        score += 5
        reasons.append(f"📈 近1月涨{ret_1m:.1f}%")
    elif ret_1m > -5:
        score -= 3
        reasons.append(f"📉 近1月跌{abs(ret_1m):.1f}%")
    else:
        score -= 8
        reasons.append(f"⚠️ 近1月大跌{abs(ret_1m):.1f}%")
    
    # 已持有降级
    if already_hold and rsi > 70:
        score = min(score, 45)
        reasons.append("📌 已持有且RSI超买，暂缓加仓")
        decision = "⏳ 暂缓加仓"
        action = "wait"
    elif already_hold:
        score -= 10
        reasons.append("📌 已持有")
        decision = "📌 已持有"
        action = "hold_already"
    elif score >= 70:
        decision = "✅ 强烈推荐买入"
        action = "strong_buy"
    elif score >= 55:
        decision = "📈 建议买入"
        action = "buy"
    elif score >= 40:
        decision = "⏳ 建议观望"
        action = "wait"
    else:
        decision = "❌ 不建议买入"
        action = "avoid"
    
    score = max(0, min(100, score))
    return {
        "code": code,
        "name": name,
        "current_price": latest,
        "score": int(score),
        "position": int(position*100),
        "rsi": int(rsi),
        "ma20": ma20,
        "ma60": ma60,
        "ret_1m": ret_1m,
        "decision": decision,
        "action": action,
        "reasons": reasons,
        "data_source": source,
        "already_hold": already_hold,
        "history_data": df.tail(90).to_dict('records')
    }

# ==================== 持仓监控 ====================
def analyze_holding(holding):
    code = holding["code"]
    name = holding["name"]
    buy_price = float(holding["nav"])
    holding_type = holding.get("type", "场外基金")
    
    df, source = get_fund_data(code, holding_type)
    if df is None or df.empty:
        return None
    
    indicators = calculate_indicators(df)
    if not indicators:
        return None
    
    current_price = indicators["latest"]
    profit_rate = (current_price - buy_price) / buy_price * 100
    rsi = indicators["rsi"]
    ma20 = indicators["ma20"]
    
    sell_signals = []
    if profit_rate >= 15:
        sell_signals.append(f"🎯 止盈线（+{profit_rate:.1f}%），建议卖出")
    elif profit_rate >= 10:
        sell_signals.append(f"📈 接近止盈（+{profit_rate:.1f}%）")
    if profit_rate <= -8:
        sell_signals.append(f"⚠️ 止损线（{profit_rate:.1f}%），建议离场")
    elif profit_rate <= -5:
        sell_signals.append(f"📉 接近止损（{profit_rate:.1f}%）")
    if current_price < ma20 and profit_rate > 0:
        sell_signals.append("📊 跌破20日均线")
    if rsi > 70:
        sell_signals.append(f"📊 RSI={rsi:.0f}超买")
    
    if sell_signals:
        action = "卖出"
        advice = sell_signals[0]
        all_signals = sell_signals
        # 发送微信通知（仅高风险）
        if any("止盈" in s or "止损" in s for s in sell_signals):
            send_wechat_message(f"🔴 {name} 卖出提醒\n盈亏：{profit_rate:.1f}%\n{advice}")
    else:
        action = "持有"
        advice = f"📊 盈亏{profit_rate:.1f}%，继续持有"
        all_signals = [advice]
    
    # 历史数据
    history_data = []
    for _, row in df.tail(60).iterrows():
        history_data.append({"日期": row['日期'].strftime("%Y-%m-%d"), "收盘": float(row['收盘'])})
    
    return {
        "name": name,
        "code": code,
        "buy_price": buy_price,
        "current_price": current_price,
        "profit_rate": profit_rate,
        "rsi": rsi,
        "ma20": ma20,
        "action": action,
        "advice": advice,
        "all_signals": all_signals,
        "history_data": history_data,
        "data_source": source
    }

def auto_monitor_all_holdings():
    holdings = load_holdings()
    if not holdings:
        return []
    results = []
    for h in holdings:
        try:
            result = analyze_holding(h)
            if result:
                results.append(result)
        except:
            continue
    if results:
        log = {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "results": results}
        logs = load_monitor_log()
        logs.append(log)
        save_monitor_log(logs[-50:])
    return results

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
            {"name": "沪深300ETF", "code": "510300", "style": "大盘", "risk": "中"},
        ]
    }
}

def scan_all_for_buy(category, risk_preference="中", existing_holdings=[]):
    pool = FUND_POOLS.get(category, FUND_POOLS["场外基金"])
    results = []
    for f in pool["list"]:
        result = ai_buy_decision(f["code"], f["name"], category, existing_holdings)
        results.append(result)
    results = sorted(results, key=lambda x: x["score"], reverse=True)
    return results

# ==================== 组合分析 ====================
def portfolio_analysis(holdings):
    if not holdings:
        return None
    total_cost = sum(float(h["amount"]) for h in holdings)
    total_value = 0
    details = []
    for h in holdings:
        df, _ = get_fund_data(h["code"], h.get("type", "场外基金"))
        if df is not None and not df.empty:
            current = float(df['收盘'].iloc[-1])
            value = (h["amount"] / h["nav"]) * current
            total_value += value
            details.append({
                "名称": h["name"],
                "投入": h["amount"],
                "市值": round(value, 2),
                "盈亏": round(value - h["amount"], 2),
                "盈亏率": round((value - h["amount"]) / h["amount"] * 100, 2)
            })
        else:
            total_value += h["amount"]
            details.append({
                "名称": h["name"],
                "投入": h["amount"],
                "市值": h["amount"],
                "盈亏": 0,
                "盈亏率": 0
            })
    profit = total_value - total_cost
    profit_rate = (profit / total_cost) * 100 if total_cost > 0 else 0
    return {
        "total_cost": total_cost,
        "total_value": total_value,
        "profit": profit,
        "profit_rate": profit_rate,
        "details": details
    }

# ==================== 生成报告 ====================
def generate_report():
    holdings = load_holdings()
    if not holdings:
        return "暂无持仓"
    analysis = portfolio_analysis(holdings)
    if not analysis:
        return "无法分析"
    report = f"""
📋 投资组合报告
生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}
----------------------------------------
总投入：{analysis['total_cost']:.2f} 元
总市值：{analysis['total_value']:.2f} 元
总盈亏：{analysis['profit']:.2f} 元（{analysis['profit_rate']:.2f}%）
----------------------------------------
持仓明细：
"""
    for d in analysis['details']:
        report += f"{d['名称']}：投入{d['投入']}元，盈亏{d['盈亏']:.2f}元（{d['盈亏率']:.2f}%）\n"
    return report

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
    total_cash = st.number_input("总资金（元）", min_value=1000, value=st.session_state.total_cash, step=1000)
    st.session_state.total_cash = total_cash
    
    st.divider()
    holdings = load_holdings()
    st.metric("持仓数量", f"{len(holdings)} 只")
    total_cost = sum(float(h.get("amount", 0)) for h in holdings)
    st.metric("已投入", f"{total_cost:.0f} 元")
    st.metric("剩余资金", f"{total_cash - total_cost:.0f} 元")
    
    st.divider()
    if st.button("📤 测试微信通知", use_container_width=True):
        if send_wechat_message("✅ AI智能投资系统测试成功！"):
            st.success("✅ 已发送")

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
    st.caption("📌 已持有的基金如果RSI超买，会自动标注「暂缓加仓」")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        category = st.selectbox("选择类别", list(FUND_POOLS.keys()))
    with col2:
        if st.button("🔍 全扫描", use_container_width=True, type="primary"):
            with st.spinner("AI正在扫描..."):
                holdings = load_holdings()
                results = scan_all_for_buy(category, "中", holdings)
                st.session_state.scan_results = results
                st.success(f"✅ 扫描完成 {len(results)} 只")
                send_wechat_message(f"🧠 AI扫描完成，发现 {len([r for r in results if r['action']=='strong_buy'])} 只强烈推荐")
    
    if st.session_state.scan_results:
        results = st.session_state.scan_results
        show_results = [r for r in results if r['action'] != 'hold_already']
        st.info(f"📊 强烈推荐 {len([r for r in results if r['action']=='strong_buy'])} 只 | 建议买入 {len([r for r in results if r['action']=='buy'])} 只")
        
        for idx, r in enumerate(show_results[:10]):
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1.2, 1, 1])
                with col1:
                    st.write(f"**{r['name']}**")
                    st.caption(f"{r['code']} | 价格：{r['current_price']:.3f} | {r.get('data_source', '')}")
                    if r.get('already_hold'):
                        st.caption("📌 已持有")
                with col2:
                    st.metric("AI评分", f"{r['score']}/100")
                with col3:
                    if r['action'] == "strong_buy":
                        st.success("✅ 强烈推荐")
                    elif r['action'] == "buy":
                        st.info("📈 建议买入")
                    elif r['action'] == "wait":
                        st.warning("⏳ 观望")
                    elif r['action'] == "avoid":
                        st.error("❌ 不建议")
                    else:
                        st.caption("⏳ 观望")
                with col4:
                    if r['action'] in ["strong_buy", "buy"] and not r.get('already_hold'):
                        buy_key = f"buy_{r['code']}_{idx}_{datetime.now().strftime('%H%M%S%f')}"
                        if st.button("📥 买入", key=buy_key, use_container_width=True):
                            price, source = get_current_price(r['code'], category)
                            if price is None:
                                price = round(random.uniform(1.0, 2.5), 4)
                            holdings = load_holdings()
                            exist = [h for h in holdings if h["code"] == r["code"]]
                            if exist:
                                st.warning(f"⚠️ 已持有 {r['name']}")
                            else:
                                amount = round(total_cash * 0.15, 0)
                                holdings.append({
                                    "code": r["code"],
                                    "name": r["name"],
                                    "amount": amount,
                                    "buy_date": datetime.now().strftime("%Y-%m-%d"),
                                    "nav": float(price),
                                    "type": category
                                })
                                save_holdings(holdings)
                                st.success(f"✅ 买入 {r['name']} {amount:.0f}元 @ {price:.4f}")
                                send_wechat_message(f"✅ 买入 {r['name']} {amount:.0f}元")
                                st.rerun()
                    elif r.get('already_hold'):
                        st.caption("📌 已持有")
                
                with st.expander(f"📊 评分详情（{r['score']}分）"):
                    for reason in r.get('reasons', []):
                        if "✅" in reason:
                            st.success(reason)
                        elif "⚠️" in reason:
                            st.warning(reason)
                        else:
                            st.info(reason)
                    st.caption(f"📊 位置：{r['position']}% | RSI：{r['rsi']} | MA20：{r['ma20']:.3f} | MA60：{r['ma60']:.3f}")
                    st.caption(f"💡 {r['advice']}")
                
                st.divider()
    else:
        st.info("💡 点击「全扫描」让AI分析所有基金")

# ==================== Tab2: 持仓监控 ====================
with tab2:
    st.subheader("📊 持仓监控")
    st.caption("🔴 卖出信号出现时，说明当前持仓需要关注风险")
    
    if st.button("🔍 扫描持仓", use_container_width=True, type="primary"):
        results = auto_monitor_all_holdings()
        st.session_state.monitor_results = results
        st.success(f"✅ 扫描完成")
        st.rerun()
    
    results = st.session_state.monitor_results if st.session_state.monitor_results else auto_monitor_all_holdings()
    
    if results:
        sell = sum(1 for r in results if r["action"] == "卖出")
        hold = len(results) - sell
        c1, c2 = st.columns(2)
        c1.metric("🔴 卖出信号", f"{sell} 只", delta="需处理" if sell > 0 else "安全")
        c2.metric("🟢 持有", f"{hold} 只")
        
        if sell > 0:
            st.warning(f"⚠️ 检测到 {sell} 只基金出现卖出信号")
        
        for r in results:
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{r['name']}**")
                    st.caption(f"买入：{r['buy_price']:.3f} → 现价：{r['current_price']:.3f}")
                    st.caption(f"MA20：{r['ma20']:.3f} | RSI：{r['rsi']:.0f}")
                with col2:
                    profit = r['profit_rate']
                    st.metric("盈亏", f"{'+' if profit > 0 else ''}{profit:.1f}%")
                with col3:
                    if r['action'] == "卖出":
                        st.error("🔴 卖出")
                    else:
                        st.success("🟢 持有")
                
                if r['action'] == "卖出":
                    st.error(f"💡 {r['advice']}")
                else:
                    st.info(f"💡 {r['advice']}")
                
                if r.get('history_data'):
                    hist_df = pd.DataFrame(r['history_data'])
                    hist_df['日期'] = pd.to_datetime(hist_df['日期'])
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=hist_df['日期'], y=hist_df['收盘'], name='净值', line=dict(color='blue', width=2)))
                    fig.add_hline(y=r['buy_price'], line_dash="dash", line_color="green", annotation_text=f"买入 {r['buy_price']:.3f}")
                    fig.update_layout(height=150, margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
                st.divider()
    else:
        st.info("📭 暂无持仓")

# ==================== Tab3: 组合分析 ====================
with tab3:
    st.subheader("📈 组合分析")
    holdings = load_holdings()
    if holdings:
        analysis = portfolio_analysis(holdings)
        if analysis:
            col1, col2, col3 = st.columns(3)
            col1.metric("总投入", f"{analysis['total_cost']:.2f}元")
            col2.metric("总市值", f"{analysis['total_value']:.2f}元")
            col3.metric("总盈亏", f"{analysis['profit']:.2f}元", delta=f"{analysis['profit_rate']:.2f}%")
            
            st.subheader("📊 持仓明细")
            df = pd.DataFrame(analysis['details'])
            st.dataframe(df, use_container_width=True)
            
            # 生成报告
            if st.button("📄 生成报告", use_container_width=True):
                report = generate_report()
                st.text_area("报告内容", report, height=300)
                # 微信通知
                send_wechat_message(f"📋 组合报告\n总盈亏：{analysis['profit']:.2f}元（{analysis['profit_rate']:.2f}%）")
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
                st.caption(f"金额：{h['amount']}元 | 日期：{h.get('buy_date', '')}")
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
        for log in logs[-10:]:
            st.write(f"📅 {log['time']}")
            if log.get('results'):
                for r in log['results']:
                    st.write(f"  • {r['name']}：{r['action']} | {r['advice'][:30]}...")
            st.divider()
    else:
        st.info("暂无日志")

# ==================== 底部 ====================
st.divider()
st.caption("⚠️ 本系统为学习演示工具，不构成投资建议")
