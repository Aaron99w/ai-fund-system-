import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
import requests
import random

# ==================== 页面设置 ====================
st.set_page_config(
    page_title="📊 全品种投资分析系统",
    page_icon="📈",
    layout="wide"
)

st.title("📊 全品种投资分析系统")
st.caption("📈 AI推荐 · 实时监控 · 走势曲线 · 买卖提醒 · 微信通知")

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
        json.dump(holdings, f, ensure_ascii=False, indent=2)

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

# ==================== 判断交易时间 ====================
def is_trading_time():
    """判断当前是否在A股交易时间（9:30-15:00）"""
    now = datetime.now()
    # 周一至周五 (周一=0, 周日=6)
    if now.weekday() >= 5:
        return False
    # 9:30-11:30 和 13:00-15:00
    hour = now.hour
    minute = now.minute
    if hour == 9 and minute >= 30:
        return True
    if 10 <= hour <= 11:
        return True
    if hour == 12:
        return False
    if hour == 13:
        return True
    if 14 <= hour < 15:
        return True
    if hour == 15 and minute == 0:
        return True
    return False

def get_data_label():
    if is_trading_time():
        return "🟢 实时行情（交易中）"
    else:
        return "🔵 收盘价（非交易时间）"

# ==================== 数据获取 ====================
def get_fund_data(code):
    try:
        import akshare as ak
        df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
        if df is not None and not df.empty:
            df['净值日期'] = pd.to_datetime(df['净值日期'])
            df = df.sort_values('净值日期')
            df = df.rename(columns={'净值日期': '日期', '单位净值': '收盘'})
            # 转换为Python原生类型
            df['收盘'] = df['收盘'].astype(float)
            return df
    except:
        pass
    # 模拟数据
    dates = pd.date_range(end=datetime.now(), periods=180, freq='D')
    random.seed(hash(code) % 100)
    base = random.uniform(1.0, 3.0)
    prices = [base]
    for i in range(179):
        change = np.random.normal(0.0002, 0.018)
        prices.append(prices[-1] * (1 + change))
    df = pd.DataFrame({'日期': dates, '收盘': prices})
    df['日期'] = pd.to_datetime(df['日期'])
    df['收盘'] = df['收盘'].astype(float)
    return df.sort_values('日期')

def get_etf_data(code):
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
    dates = pd.date_range(end=datetime.now(), periods=180, freq='D')
    random.seed(hash(code) % 100)
    base = random.uniform(0.8, 2.0)
    prices = [base]
    for i in range(179):
        change = np.random.normal(0.0002, 0.02)
        prices.append(prices[-1] * (1 + change))
    df = pd.DataFrame({'日期': dates, '收盘': prices})
    df['日期'] = pd.to_datetime(df['日期'])
    df['收盘'] = df['收盘'].astype(float)
    return df.sort_values('日期')

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

# ==================== AI监控分析 ====================
def analyze_holding(holding):
    code = holding["code"]
    name = holding["name"]
    buy_price = float(holding["nav"])
    holding_type = holding.get("type", "ETF")
    
    try:
        if holding_type in ["场外基金", "普通基金"]:
            df = get_fund_data(code)
        else:
            df = get_etf_data(code)
    except:
        df = get_etf_data(code)
    
    if df is None or df.empty:
        return None
    
    current_price = float(df['收盘'].iloc[-1])
    profit_rate = (current_price - buy_price) / buy_price * 100
    
    close = df['收盘'].values
    if len(close) >= 20:
        ma20 = float(pd.Series(close).rolling(20).mean().values[-1])
    else:
        ma20 = current_price
    
    if len(close) >= 14:
        delta = pd.Series(close).diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = float(rsi.iloc[-1]) if not rsi.empty else 50
    else:
        current_rsi = 50
    
    sell_signals = []
    buy_signals = []
    
    if profit_rate >= 10:
        sell_signals.append(f"🎯 止盈线（+{profit_rate:.1f}%），建议分批卖出")
    elif profit_rate >= 7:
        sell_signals.append(f"📈 接近止盈（+{profit_rate:.1f}%）")
    
    if profit_rate <= -5:
        sell_signals.append(f"⚠️ 止损线（{profit_rate:.1f}%），建议离场")
    elif profit_rate <= -3:
        sell_signals.append(f"📉 接近止损（{profit_rate:.1f}%）")
    
    if current_price < ma20 and profit_rate > 0:
        sell_signals.append("📊 跌破20日均线")
    
    if current_rsi > 70:
        sell_signals.append(f"📊 RSI={current_rsi:.0f}超买区")
    
    if current_price < ma20 and current_rsi < 35 and profit_rate < 0:
        buy_signals.append(f"📈 RSI超卖，可考虑补仓")
    
    if sell_signals:
        action = "卖出"
        advice = sell_signals[0]
        all_signals = sell_signals
        if any("止盈" in s or "止损" in s for s in sell_signals):
            send_wechat_message(f"🔴 {name} 卖出提醒\n盈亏：{profit_rate:.1f}%\n{advice}")
    elif buy_signals:
        action = "买入"
        advice = buy_signals[0]
        all_signals = buy_signals
    else:
        action = "持有"
        advice = f"📊 盈亏{profit_rate:.1f}%，继续持有"
        all_signals = [advice]
    
    # 转换历史数据为Python原生类型
    history_data = []
    for _, row in df.tail(60).iterrows():
        history_data.append({
            "日期": row['日期'].strftime("%Y-%m-%d"),
            "收盘": float(row['收盘'])
        })
    
    return {
        "name": name,
        "code": code,
        "buy_price": float(buy_price),
        "current_price": float(current_price),
        "profit_rate": float(profit_rate),
        "ma20": float(ma20),
        "rsi": float(current_rsi),
        "action": action,
        "advice": advice,
        "all_signals": all_signals,
        "buy_date": holding.get("buy_date", ""),
        "history_data": history_data,
        "holding_type": holding_type
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
        except Exception as e:
            continue
    if results:
        log = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "results": results
        }
        logs = load_monitor_log()
        logs.append(log)
        if len(logs) > 50:
            logs = logs[-50:]
        save_monitor_log(logs)
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
            {"name": "光伏ETF", "code": "515790", "style": "新能源", "risk": "高"},
            {"name": "军工ETF", "code": "512660", "style": "军工", "risk": "高"},
            {"name": "证券ETF", "code": "512880", "style": "券商", "risk": "中高"},
            {"name": "沪深300ETF", "code": "510300", "style": "大盘", "risk": "中"},
            {"name": "中概互联ETF", "code": "513050", "style": "互联网", "risk": "高"},
        ]
    },
    "股票": {
        "description": "适合深入研究，精选个股获取超额收益",
        "list": [
            {"name": "贵州茅台", "code": "600519", "style": "消费", "risk": "中"},
            {"name": "宁德时代", "code": "300750", "style": "新能源", "risk": "高"},
            {"name": "比亚迪", "code": "002594", "style": "新能源", "risk": "高"},
            {"name": "药明康德", "code": "603259", "style": "医药", "risk": "高"},
            {"name": "中国平安", "code": "601318", "style": "金融", "risk": "中"},
            {"name": "招商银行", "code": "600036", "style": "金融", "risk": "中"},
        ]
    },
}

def ai_recommend(category, total_amount, risk_preference="中", count=5):
    pool = FUND_POOLS.get(category, FUND_POOLS["场外基金"])
    available = pool["list"]
    risk_map = {"低": ["低", "中低"], "中": ["中低", "中", "中高"], "高": ["中高", "高"]}
    allowed = risk_map.get(risk_preference, ["中"])
    available = [f for f in available if f.get("risk", "中") in allowed]
    if len(available) < count:
        available = pool["list"]
    selected = random.sample(available, min(count, len(available)))
    results = []
    for f in selected:
        score = random.randint(65, 95)
        results.append({
            "name": f["name"],
            "code": f["code"],
            "style": f.get("style", ""),
            "risk": f.get("risk", "中"),
            "score": score,
            "suggest_amount": round(total_amount * random.uniform(0.15, 0.25), 0),
            "reason": f"{f.get('style', '')}风格 | 评分{score}分",
            "category": category
        })
    return sorted(results, key=lambda x: x["score"], reverse=True)

# ==================== 初始化 ====================
if "total_cash" not in st.session_state:
    st.session_state.total_cash = 10000
if "recommendations" not in st.session_state:
    st.session_state.recommendations = []
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
    st.caption(f"📊 {get_data_label()}")
    
    st.divider()
    if st.button("📤 测试微信", use_container_width=True):
        if send_wechat_message("✅ 投资系统测试成功！"):
            st.success("✅ 已发送")

# ==================== 主界面 ====================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🤖 AI推荐",
    "📊 持仓监控",
    "📈 组合分析",
    "📋 持仓管理",
    "📰 监控日志"
])

# ==================== Tab1: AI推荐 ====================
with tab1:
    st.subheader("🤖 AI智能推荐")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        category = st.selectbox("选择类别", list(FUND_POOLS.keys()))
    with col2:
        risk = st.selectbox("风险偏好", ["低", "中", "高"], index=1)
    with col3:
        count = st.selectbox("推荐数量", [3, 5, 8], index=1)
    
    st.info(f"📌 {FUND_POOLS[category]['description']}")
    
    if st.button("🔍 AI分析推荐", use_container_width=True, type="primary"):
        with st.spinner("AI分析中..."):
            results = ai_recommend(category, total_cash, risk, count)
            st.session_state.recommendations = results
            st.success(f"✅ 推荐 {len(results)} 只")
            st.rerun()
    
    if st.session_state.recommendations:
        for i, rec in enumerate(st.session_state.recommendations):
            with st.container():
                col1, col2, col3, col4 = st.columns([2.5, 1, 1, 1])
                with col1:
                    st.write(f"**{i+1}. {rec['name']}**")
                    st.caption(f"{rec['code']} | {rec.get('style', '')} | 风险：{rec.get('risk', '中')}")
                with col2:
                    st.metric("评分", f"{rec['score']}/100")
                with col3:
                    st.caption(f"建议投入")
                    st.caption(f"**{rec['suggest_amount']:.0f}元**")
                with col4:
                    btn_key = f"buy_{rec['code']}_{i}"
                    if st.button("📥 买入", key=btn_key, use_container_width=True):
                        current = load_holdings()
                        exist = [h for h in current if h["code"] == rec["code"]]
                        if exist:
                            st.warning(f"⚠️ 已持有 {rec['name']}")
                        else:
                            current.append({
                                "code": rec["code"],
                                "name": rec["name"],
                                "amount": float(rec["suggest_amount"]),
                                "buy_date": datetime.now().strftime("%Y-%m-%d"),
                                "nav": float(round(random.uniform(1.0, 3.0), 4)),
                                "type": category
                            })
                            save_holdings(current)
                            st.success(f"✅ 买入 {rec['name']} {rec['suggest_amount']:.0f}元")
                            send_wechat_message(f"✅ 买入 {rec['name']} {rec['suggest_amount']:.0f}元")
                            st.rerun()
                
                st.caption(f"💡 {rec['reason']}")
                st.divider()

# ==================== Tab2: 持仓监控（带走势图） ====================
with tab2:
    st.subheader("📊 持仓监控")
    st.caption(f"📊 {get_data_label()}")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("🔍 扫描持仓", use_container_width=True, type="primary"):
            with st.spinner("扫描中..."):
                results = auto_monitor_all_holdings()
                st.session_state.monitor_results = results
                st.success(f"✅ 扫描完成")
                st.rerun()
    with col2:
        st.caption("💡 点击更新数据")
    
    results = st.session_state.monitor_results if st.session_state.monitor_results else auto_monitor_all_holdings()
    
    if results:
        sell = sum(1 for r in results if r["action"] == "卖出")
        buy = sum(1 for r in results if r["action"] == "买入")
        hold = sum(1 for r in results if r["action"] == "持有")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("🔴 卖出", f"{sell} 只", delta="需处理" if sell > 0 else "安全")
        c2.metric("🟢 买入", f"{buy} 只", delta="可补仓" if buy > 0 else "无需")
        c3.metric("🟡 持有", f"{hold} 只")
        
        st.divider()
        
        for r in results:
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{r['name']}**")
                    st.caption(f"买入：{r['buy_price']:.3f} → 现价：{r['current_price']:.3f}")
                    st.caption(f"MA20：{r['ma20']:.3f} | RSI：{r['rsi']:.0f}")
                with col2:
                    profit = r['profit_rate']
                    if profit > 0:
                        st.metric("盈亏", f"+{profit:.1f}%", delta="盈利")
                    else:
                        st.metric("盈亏", f"{profit:.1f}%", delta="亏损")
                with col3:
                    if r['action'] == "卖出":
                        st.error(f"🔴 {r['action']}")
                    elif r['action'] == "买入":
                        st.success(f"🟢 {r['action']}")
                    else:
                        st.info(f"🟡 {r['action']}")
                
                st.info(f"💡 {r['advice']}")
                
                # ===== 走势图 =====
                if r.get('history_data'):
                    hist_df = pd.DataFrame(r['history_data'])
                    hist_df['日期'] = pd.to_datetime(hist_df['日期'])
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=hist_df['日期'], 
                        y=hist_df['收盘'], 
                        name='净值走势',
                        line=dict(color='blue', width=2)
                    ))
                    fig.add_hline(
                        y=r['buy_price'], 
                        line_dash="dash", 
                        line_color="green",
                        annotation_text=f"买入价 {r['buy_price']:.3f}"
                    )
                    if len(hist_df) >= 20:
                        ma20_vals = hist_df['收盘'].rolling(20).mean()
                        fig.add_trace(go.Scatter(
                            x=hist_df['日期'], 
                            y=ma20_vals, 
                            name='MA20',
                            line=dict(color='orange', width=1, dash='dash')
                        ))
                    
                    fig.update_layout(
                        height=200,
                        margin=dict(l=0, r=0, t=20, b=0),
                        showlegend=False,
                        xaxis_title="",
                        yaxis_title="净值"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                st.divider()
    else:
        st.info("📭 暂无持仓，请先买入")

# ==================== Tab3: 组合分析 ====================
with tab3:
    st.subheader("📈 组合分析")
    holdings = load_holdings()
    if holdings:
        total_cost = sum(float(h["amount"]) for h in holdings)
        st.metric("总投入", f"{total_cost:.0f}元")
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
                st.caption(f"金额：{h['amount']}元 | 日期：{h.get('buy_date', '')}")
            with col2:
                st.caption(f"净值：{h.get('nav', 0):.3f}")
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
st.caption(f"📊 {get_data_label()}")
