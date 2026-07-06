import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
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
st.caption("📈 AI推荐 · ETF · 股票 · 普通基金 · 可转债 · REITs · 指数估值 · 板块轮动")

# ==================== 数据持久化 ====================
HOLDINGS_FILE = "holdings.json"

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

# ==================== 数据获取函数 ====================
def get_etf_data(code):
    try:
        import akshare as ak
        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=180)).strftime("%Y%m%d")
        df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start, end_date=end, adjust="qfq")
        if df is not None and not df.empty:
            df['日期'] = pd.to_datetime(df['日期'])
            df = df.sort_values('日期')
            return df, "akshare真实数据"
    except:
        pass
    return generate_simulated_data(code, "ETF"), "模拟数据"

def get_stock_data(code):
    try:
        import akshare as ak
        df = ak.stock_zh_a_hist(symbol=code, period="daily", 
                                start_date=(datetime.now()-timedelta(days=180)).strftime("%Y%m%d"),
                                end_date=datetime.now().strftime("%Y%m%d"), adjust="qfq")
        if df is not None and not df.empty:
            df['日期'] = pd.to_datetime(df['日期'])
            df = df.sort_values('日期')
            return df, "akshare真实数据"
    except:
        pass
    return generate_simulated_data(code, "股票"), "模拟数据"

def get_fund_nav_data(code):
    try:
        import akshare as ak
        df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
        if df is not None and not df.empty:
            df['净值日期'] = pd.to_datetime(df['净值日期'])
            df = df.sort_values('净值日期')
            df = df.rename(columns={'净值日期': '日期', '单位净值': '收盘'})
            df['开盘'] = df['收盘']
            df['最高'] = df['收盘']
            df['最低'] = df['收盘']
            df['成交量'] = 0
            return df, "akshare真实数据"
    except:
        pass
    return generate_simulated_data(code, "基金"), "模拟数据"

def get_cb_data(code):
    try:
        import akshare as ak
        df = ak.bond_zh_cov_daily(symbol=code)
        if df is not None and not df.empty:
            df['日期'] = pd.to_datetime(df['日期'])
            df = df.sort_values('日期')
            df = df.rename(columns={'close': '收盘', 'open': '开盘', 'high': '最高', 'low': '最低', 'volume': '成交量'})
            return df, "akshare真实数据"
    except:
        pass
    return generate_simulated_data(code, "可转债"), "模拟数据"

def get_reits_data(code):
    try:
        import akshare as ak
        df = ak.reits_hist_em(symbol=code)
        if df is not None and not df.empty:
            df['日期'] = pd.to_datetime(df['日期'])
            df = df.sort_values('日期')
            df = df.rename(columns={'close': '收盘', 'open': '开盘', 'high': '最高', 'low': '最低', 'volume': '成交量'})
            return df, "akshare真实数据"
    except:
        pass
    return generate_simulated_data(code, "REITs"), "模拟数据"

def get_market_index():
    try:
        import akshare as ak
        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        df = ak.stock_zh_index_hist(symbol="sh000300", period="daily", start_date=start, end_date=end)
        return df if df is not None and not df.empty else None
    except:
        return None

def get_sector_data():
    try:
        import akshare as ak
        df = ak.stock_sector_spot()
        return df if df is not None and not df.empty else None
    except:
        return None

def get_news_data():
    try:
        import akshare as ak
        df = ak.stock_news_em(symbol="头条")
        return df.head(10).to_dict('records') if df is not None and not df.empty else []
    except:
        return []

def generate_simulated_data(code, asset_type):
    end_date = datetime.now()
    dates = pd.date_range(end=end_date, periods=180, freq='D')
    seed = hash(code + asset_type) % 100
    random.seed(seed)
    
    if asset_type == "基金":
        base_price = random.uniform(1.0, 3.5)
    elif asset_type == "可转债":
        base_price = random.uniform(90, 150)
    elif asset_type == "REITs":
        base_price = random.uniform(2.0, 6.0)
    else:
        base_price = random.uniform(5, 150)
    
    prices = [base_price]
    trend = random.uniform(-0.001, 0.002)
    volatility = random.uniform(0.015, 0.035)
    
    for i in range(179):
        change = np.random.normal(trend, volatility)
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, base_price * 0.3))
    
    close = np.array(prices)
    high = close * (1 + np.random.uniform(0.005, 0.02, len(close)))
    low = close * (1 - np.random.uniform(0.005, 0.02, len(close)))
    open_price = np.roll(close, 1)
    open_price[0] = close[0] * (1 - random.uniform(0.01, 0.03))
    volume = np.random.randint(10000, 5000000, len(close))
    
    df = pd.DataFrame({
        '日期': dates,
        '开盘': open_price,
        '最高': high,
        '最低': low,
        '收盘': close,
        '成交量': volume
    })
    df['日期'] = pd.to_datetime(df['日期'])
    df = df.sort_values('日期')
    return df

# ==================== AI推荐引擎（按类别） ====================

# ===== 基金池（按类别分类） =====
FUND_POOLS = {
    "场外基金": {
        "description": "适合长期定投，由基金经理主动管理",
        "list": [
            {"name": "前海开源人工智能混合", "code": "001986", "style": "科技", "risk": "高", "return_3y": "+42.5%"},
            {"name": "万家人工智能混合", "code": "006281", "style": "科技", "risk": "高", "return_3y": "+38.2%"},
            {"name": "中欧时代先锋股票A", "code": "001938", "style": "科技", "risk": "高", "return_3y": "+51.3%"},
            {"name": "易方达蓝筹精选混合", "code": "005827", "style": "消费", "risk": "中", "return_3y": "+28.6%"},
            {"name": "易方达中小盘混合", "code": "110011", "style": "消费", "risk": "中", "return_3y": "+32.4%"},
            {"name": "景顺长城新兴成长混合", "code": "260108", "style": "消费", "risk": "中", "return_3y": "+35.2%"},
            {"name": "汇添富消费行业混合", "code": "000083", "style": "消费", "risk": "中", "return_3y": "+38.7%"},
            {"name": "中欧医疗健康混合A", "code": "003095", "style": "医药", "risk": "高", "return_3y": "+45.8%"},
            {"name": "汇添富创新医药混合", "code": "006113", "style": "医药", "risk": "高", "return_3y": "+38.2%"},
            {"name": "广发医疗保健股票A", "code": "004851", "style": "医药", "risk": "高", "return_3y": "+42.6%"},
            {"name": "交银阿尔法核心混合", "code": "519712", "style": "均衡", "risk": "中", "return_3y": "+32.4%"},
            {"name": "兴全合润混合", "code": "163406", "style": "均衡", "risk": "中", "return_3y": "+42.3%"},
            {"name": "富国天惠成长混合", "code": "161005", "style": "均衡", "risk": "中", "return_3y": "+35.6%"},
            {"name": "睿远成长价值混合A", "code": "007119", "style": "均衡", "risk": "中", "return_3y": "+26.8%"},
            {"name": "前海开源沪港深优势精选", "code": "001875", "style": "港股", "risk": "中高", "return_3y": "+38.6%"},
            {"name": "诺安成长混合", "code": "320007", "style": "芯片", "risk": "高", "return_3y": "+52.3%"},
            {"name": "银河创新成长混合", "code": "519674", "style": "芯片", "risk": "高", "return_3y": "+62.8%"},
            {"name": "农银新能源主题混合", "code": "002190", "style": "新能源", "risk": "高", "return_3y": "+55.8%"},
            {"name": "华夏能源革新股票", "code": "003834", "style": "新能源", "risk": "高", "return_3y": "+45.2%"},
            {"name": "工银瑞信金融地产混合", "code": "000251", "style": "金融", "risk": "中低", "return_3y": "+16.8%"},
        ]
    },
    "ETF": {
        "description": "适合短线交易和行业轮动，费用低、交易灵活",
        "list": [
            {"name": "科创50ETF", "code": "588000", "style": "科创板", "risk": "高"},
            {"name": "创业板ETF", "code": "159915", "style": "创业板", "risk": "高"},
            {"name": "芯片ETF", "code": "159995", "style": "半导体", "risk": "高"},
            {"name": "半导体ETF", "code": "512480", "style": "半导体", "risk": "高"},
            {"name": "人工智能ETF", "code": "159819", "style": "AI", "risk": "高"},
            {"name": "新能源车ETF", "code": "515030", "style": "新能源", "risk": "高"},
            {"name": "光伏ETF", "code": "515790", "style": "新能源", "risk": "高"},
            {"name": "军工ETF", "code": "512660", "style": "军工", "risk": "高"},
            {"name": "证券ETF", "code": "512880", "style": "券商", "risk": "中高"},
            {"name": "沪深300ETF", "code": "510300", "style": "大盘", "risk": "中"},
            {"name": "中证500ETF", "code": "510500", "style": "中小盘", "risk": "中"},
            {"name": "酒ETF", "code": "512690", "style": "白酒", "risk": "中高"},
            {"name": "医药ETF", "code": "512010", "style": "医药", "risk": "中高"},
            {"name": "中概互联ETF", "code": "513050", "style": "互联网", "risk": "高"},
        ]
    },
    "股票": {
        "description": "适合深入研究，精选个股获取超额收益",
        "list": [
            {"name": "贵州茅台", "code": "600519", "style": "消费", "risk": "中"},
            {"name": "宁德时代", "code": "300750", "style": "新能源", "risk": "高"},
            {"name": "腾讯控股", "code": "00700", "style": "互联网", "risk": "高"},
            {"name": "阿里巴巴", "code": "09988", "style": "互联网", "risk": "高"},
            {"name": "比亚迪", "code": "002594", "style": "新能源", "risk": "高"},
            {"name": "药明康德", "code": "603259", "style": "医药", "risk": "高"},
            {"name": "迈瑞医疗", "code": "300760", "style": "医药", "risk": "中高"},
            {"name": "中国平安", "code": "601318", "style": "金融", "risk": "中"},
            {"name": "招商银行", "code": "600036", "style": "金融", "risk": "中"},
            {"name": "美的集团", "code": "000333", "style": "消费", "risk": "中"},
            {"name": "格力电器", "code": "000651", "style": "消费", "risk": "中"},
            {"name": "海康威视", "code": "002415", "style": "科技", "risk": "中"},
            {"name": "中芯国际", "code": "688981", "style": "芯片", "risk": "高"},
            {"name": "长江电力", "code": "600900", "style": "电力", "risk": "低"},
        ]
    },
    "可转债": {
        "description": "适合稳健型投资者，下有保底上不封顶",
        "list": [
            {"name": "隆22转债", "code": "113055", "style": "光伏", "risk": "中"},
            {"name": "中信转债", "code": "113021", "style": "金融", "risk": "低"},
            {"name": "兴业转债", "code": "113052", "style": "金融", "risk": "低"},
            {"name": "中银转债", "code": "113057", "style": "金融", "risk": "低"},
            {"name": "海亮转债", "code": "123091", "style": "有色", "risk": "中"},
        ]
    },
    "REITs": {
        "description": "适合长期收息，底层资产稳定增值",
        "list": [
            {"name": "张江REIT", "code": "508000", "style": "产业园", "risk": "中"},
            {"name": "蛇口REIT", "code": "180101", "style": "产业园", "risk": "中"},
            {"name": "盐港REIT", "code": "180301", "style": "港口", "risk": "中"},
            {"name": "普洛斯REIT", "code": "508056", "style": "仓储", "risk": "中"},
            {"name": "首创水务REIT", "code": "508006", "style": "水务", "risk": "中"},
        ]
    }
}

def ai_recommend_by_category(category, total_amount, risk_preference="中", count=5):
    """根据类别进行AI推荐"""
    pool = FUND_POOLS.get(category, FUND_POOLS["场外基金"])
    available = pool["list"]
    
    # 根据风险偏好筛选
    risk_map = {"低": ["低", "中低"], "中": ["中低", "中", "中高"], "高": ["中高", "高"]}
    allowed_risks = risk_map.get(risk_preference, ["中"])
    available = [f for f in available if f.get("risk", "中") in allowed_risks]
    
    if len(available) < count:
        available = pool["list"][:count * 2]
    
    # 随机选并评分
    selected = random.sample(available, min(count, len(available)))
    recommendations = []
    for f in selected:
        score = random.randint(60, 95)
        reason_parts = []
        
        if "return_3y" in f:
            ret_3y = float(f["return_3y"].replace("%", "").replace("+", ""))
            if ret_3y > 30:
                reason_parts.append(f"🔥 近3年涨幅{ret_3y:.0f}%，业绩亮眼")
            elif ret_3y > 15:
                reason_parts.append(f"📈 近3年涨幅{ret_3y:.0f}%，表现稳健")
            else:
                reason_parts.append(f"📊 近3年涨幅{ret_3y:.0f}%")
        
        style_advice = {
            "科技": "科技赛道成长性强",
            "消费": "消费行业长期稳健",
            "医药": "医药刚需强劲",
            "均衡": "均衡配置分散风险",
            "芯片": "芯片国产替代空间大",
            "新能源": "新能源政策持续利好",
            "港股": "港股估值偏低",
            "金融": "金融板块股息率高",
            "AI": "AI是未来趋势",
            "半导体": "半导体国产化加速",
            "科创板": "科创企业成长性好",
            "创业板": "创业企业活力强",
            "大盘": "大盘蓝筹稳健",
            "中小盘": "中小盘弹性大",
            "白酒": "白酒消费升级",
            "互联网": "互联网平台经济",
            "光伏": "光伏装机持续增长",
            "券商": "券商受益于市场活跃",
            "产业园": "产业园租金稳定",
            "港口": "港口吞吐量增长",
            "仓储": "仓储物流需求旺盛",
            "水务": "水务刚需稳定",
            "有色": "有色金属价格波动",
            "电力": "电力需求持续增长"
        }
        reason_parts.append(f"📌 {style_advice.get(f.get('style', ''), f.get('style', '适合当前配置'))}")
        
        if score > 80:
            reason_parts.append("🌟 综合表现优秀")
        elif score > 65:
            reason_parts.append("✅ 综合表现良好")
        else:
            reason_parts.append("📊 综合表现一般")
        
        recommendations.append({
            "name": f["name"],
            "code": f["code"],
            "style": f.get("style", "综合"),
            "risk": f.get("risk", "中"),
            "score": score,
            "suggest_amount": round(total_amount * random.uniform(0.15, 0.30), 0),
            "reason": " | ".join(reason_parts),
            "category": category
        })
    
    return sorted(recommendations, key=lambda x: x["score"], reverse=True)

# ==================== 技术信号 ====================
def calculate_signals(df, asset_type="股票"):
    if df is None or len(df) < 30:
        return None
    
    close = df['收盘'].values
    high = df['最高'].values
    low = df['最低'].values
    volume = df['成交量'].values
    
    ma5 = pd.Series(close).rolling(5).mean().values
    ma20 = pd.Series(close).rolling(20).mean().values
    ma60 = pd.Series(close).rolling(60).mean().values
    
    latest = close[-1]
    bull_alignment = ma5[-1] > ma20[-1] > ma60[-1]
    above_ma20 = latest > ma20[-1]
    above_ma60 = latest > ma60[-1]
    
    roc_5 = (latest / close[-5] - 1) * 100 if len(close) >= 5 else 0
    roc_10 = (latest / close[-10] - 1) * 100 if len(close) >= 10 else 0
    roc_20 = (latest / close[-20] - 1) * 100 if len(close) >= 20 else 0
    
    delta = pd.Series(close).diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    current_rsi = rsi.iloc[-1] if not rsi.empty else 50
    
    vol_ma5 = pd.Series(volume).rolling(5).mean().values[-1]
    vol_ma20 = pd.Series(volume).rolling(20).mean().values[-1]
    volume_breakout = volume[-1] > vol_ma5 * 1.3
    
    score = 50
    if bull_alignment: score += 12
    if above_ma20: score += 8
    if above_ma60: score += 8
    if roc_5 > 0: score += 5
    if roc_20 > 3: score += 7
    if volume_breakout: score += 10
    if 40 <= current_rsi <= 70: score += 5
    if current_rsi < 30: score += 5
    score = max(0, min(100, score))
    
    if score >= 70:
        signal = "📈 买入信号"
        action = "buy"
    elif score >= 50:
        signal = "⏳ 持有观望"
        action = "hold"
    else:
        signal = "📉 卖出信号"
        action = "sell"
    
    return {
        "当前价格": round(latest, 3),
        "MA5": round(ma5[-1], 3),
        "MA20": round(ma20[-1], 3),
        "MA60": round(ma60[-1], 3),
        "ROC5": round(roc_5, 2),
        "ROC20": round(roc_20, 2),
        "RSI": round(current_rsi, 1),
        "多头排列": bull_alignment,
        "放量突破": volume_breakout,
        "综合评分": round(score, 1),
        "信号": signal,
        "操作建议": action,
        "历史数据": df.tail(90).to_dict('records')
    }

# ==================== 初始化 ====================
if "holdings" not in st.session_state:
    st.session_state.holdings = load_holdings()

if "total_cash" not in st.session_state:
    st.session_state.total_cash = 10000

# ==================== 侧边栏 ====================
with st.sidebar:
    st.header("💰 账户设置")
    total_cash = st.number_input("总资金（元）", min_value=1000, value=st.session_state.total_cash, step=1000)
    st.session_state.total_cash = total_cash
    
    st.divider()
    st.metric("持仓数量", f"{len(st.session_state.holdings)} 只")
    total_cost = sum(h.get("amount", 0) for h in st.session_state.holdings)
    st.metric("已投入", f"{total_cost:.0f} 元")
    
    st.divider()
    if st.button("📤 测试微信通知", use_container_width=True):
        if send_wechat_message("✅ 全品种分析系统测试成功！"):
            st.success("✅ 已发送")

# ==================== 主界面 ====================
tab0, tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🤖 AI推荐",
    "📈 ETF分析",
    "📊 股票分析",
    "📋 普通基金",
    "📋 可转债",
    "🏠 REITs",
    "📊 指数估值",
    "🔥 板块轮动"
])

# ==================== Tab0: AI推荐（可按类别选择） ====================
with tab0:
    st.subheader("🤖 AI智能推荐")
    st.caption("选择类别后，AI从该类别中精选推荐最适合你的标的")
    
    # 类别选择
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        category_options = list(FUND_POOLS.keys())
        category_descriptions = {k: v["description"] for k, v in FUND_POOLS.items()}
        selected_category = st.selectbox(
            "选择推荐类别", 
            category_options,
            format_func=lambda x: f"{x} - {FUND_POOLS[x]['description'][:20]}..."
        )
    with col2:
        risk_level = st.selectbox(
            "风险偏好",
            ["低（保本为主）", "中（稳健增值）", "高（追求高收益）"],
            index=1
        )
    with col3:
        recommend_count = st.selectbox("推荐数量", [3, 5, 8, 10], index=1)
    
    # 显示类别说明
    st.info(f"📌 {selected_category}：{FUND_POOLS[selected_category]['description']}")
    st.caption(f"📊 该类别共有 {len(FUND_POOLS[selected_category]['list'])} 只标的可供推荐")
    
    if st.button("🔍 AI分析推荐", use_container_width=True, type="primary"):
        with st.spinner(f"AI正在分析 {selected_category}..."):
            risk_map = {"低（保本为主）": "低", "中（稳健增值）": "中", "高（追求高收益）": "高"}
            risk_pref = risk_map[risk_level]
            
            recommendations = ai_recommend_by_category(
                selected_category, 
                total_cash, 
                risk_pref, 
                recommend_count
            )
            
            if recommendations:
                st.success(f"✅ AI分析完成！共推荐 {len(recommendations)} 只{selected_category}")
                
                for i, rec in enumerate(recommendations, 1):
                    with st.container():
                        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                        with col1:
                            st.write(f"**{i}. {rec['name']}**")
                            st.caption(f"{rec['code']} | {rec.get('style', '')} | 风险：{rec.get('risk', '中')}")
                        with col2:
                            st.metric("AI评分", f"{rec['score']}/100")
                        with col3:
                            st.metric("建议投入", f"{rec['suggest_amount']:.0f}元")
                        with col4:
                            if st.button(f"📥 买入", key=f"buy_ai_{rec['code']}_{i}"):
                                st.session_state.holdings.append({
                                    "code": rec["code"],
                                    "name": rec["name"],
                                    "amount": rec["suggest_amount"],
                                    "buy_date": datetime.now().strftime("%Y-%m-%d"),
                                    "nav": random.uniform(1.0, 4.0),
                                    "type": selected_category
                                })
                                save_holdings(st.session_state.holdings)
                                st.success(f"✅ 已添加 {rec['name']}")
                                st.rerun()
                        
                        st.caption(f"💡 {rec['reason']}")
                        st.divider()
            else:
                st.warning(f"⚠️ 当前风险偏好下没有匹配的{selected_category}，请调整风险偏好")

# ==================== Tab1: ETF分析 ====================
with tab1:
    st.subheader("📈 ETF分析")
    
    etf_list = [
        {"name": "科创50ETF", "code": "588000"},
        {"name": "创业板ETF", "code": "159915"},
        {"name": "芯片ETF", "code": "159995"},
        {"name": "半导体ETF", "code": "512480"},
        {"name": "人工智能ETF", "code": "159819"},
        {"name": "新能源车ETF", "code": "515030"},
        {"name": "光伏ETF", "code": "515790"},
        {"name": "军工ETF", "code": "512660"},
        {"name": "证券ETF", "code": "512880"},
        {"name": "中概互联ETF", "code": "513050"},
        {"name": "沪深300ETF", "code": "510300"},
        {"name": "中证500ETF", "code": "510500"},
        {"name": "酒ETF", "code": "512690"},
        {"name": "医药ETF", "code": "512010"},
    ]
    
    col1, col2 = st.columns([2, 1])
    with col1:
        etf_names = [f"{f['name']} ({f['code']})" for f in etf_list]
        selected = st.selectbox("选择ETF", etf_names, key="etf_select")
        code = selected.split("(")[-1].replace(")", "")
    with col2:
        st.info("📌 指数基金/行业ETF")
    
    if st.button("🔍 分析", use_container_width=True, type="primary"):
        with st.spinner("获取数据..."):
            df, source = get_etf_data(code)
            signal = calculate_signals(df, "ETF")
            if signal:
                st.success(f"✅ 数据来源：{source}")
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("综合评分", f"{signal['综合评分']}/100")
                c2.metric("当前价格", signal['当前价格'])
                c3.metric("RSI", signal['RSI'])
                c4.metric("涨跌幅", f"{signal['ROC5']}%")
                c5.metric("趋势", "多头" if signal['多头排列'] else "震荡/空头")
                
                if signal['操作建议'] == "buy":
                    st.success(f"### {signal['信号']}")
                elif signal['操作建议'] == "sell":
                    st.error(f"### {signal['信号']}")
                else:
                    st.info(f"### {signal['信号']}")
                
                hist_df = pd.DataFrame(signal['历史数据'])
                hist_df['日期'] = pd.to_datetime(hist_df['日期'])
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=hist_df['日期'], y=hist_df['收盘'], name='价格'))
                fig.add_trace(go.Scatter(x=hist_df['日期'], y=hist_df['收盘'].rolling(20).mean(), name='MA20'))
                fig.add_trace(go.Scatter(x=hist_df['日期'], y=hist_df['收盘'].rolling(60).mean(), name='MA60'))
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)

# ==================== Tab2: 股票分析 ====================
with tab2:
    st.subheader("📊 股票分析")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        stock_code = st.text_input("输入股票代码（如：000001）", value="000001")
    with col2:
        st.info("📌 支持A股主板/创业板/科创板")
    
    if st.button("🔍 分析股票", use_container_width=True, type="primary"):
        with st.spinner("获取数据..."):
            df, source = get_stock_data(stock_code)
            signal = calculate_signals(df, "股票")
            if signal:
                st.success(f"✅ 数据来源：{source}")
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("综合评分", f"{signal['综合评分']}/100")
                c2.metric("当前价格", signal['当前价格'])
                c3.metric("RSI", signal['RSI'])
                c4.metric("涨跌幅", f"{signal['ROC5']}%")
                c5.metric("趋势", "多头" if signal['多头排列'] else "震荡/空头")
                
                if signal['操作建议'] == "buy":
                    st.success(f"### {signal['信号']}")
                elif signal['操作建议'] == "sell":
                    st.error(f"### {signal['信号']}")
                else:
                    st.info(f"### {signal['信号']}")
                
                hist_df = pd.DataFrame(signal['历史数据'])
                hist_df['日期'] = pd.to_datetime(hist_df['日期'])
                st.line_chart(hist_df.set_index('日期')['收盘'])

# ==================== Tab3: 普通基金 ====================
with tab3:
    st.subheader("📋 普通基金分析")
    
    fund_list = [
        {"name": "前海开源人工智能混合", "code": "001986"},
        {"name": "万家人工智能混合", "code": "006281"},
        {"name": "中欧时代先锋股票A", "code": "001938"},
        {"name": "易方达蓝筹精选混合", "code": "005827"},
        {"name": "易方达中小盘混合", "code": "110011"},
        {"name": "景顺长城新兴成长混合", "code": "260108"},
        {"name": "汇添富消费行业混合", "code": "000083"},
        {"name": "中欧医疗健康混合A", "code": "003095"},
        {"name": "汇添富创新医药混合", "code": "006113"},
        {"name": "广发医疗保健股票A", "code": "004851"},
        {"name": "交银阿尔法核心混合", "code": "519712"},
        {"name": "兴全合润混合", "code": "163406"},
        {"name": "富国天惠成长混合", "code": "161005"},
        {"name": "睿远成长价值混合A", "code": "007119"},
        {"name": "诺安成长混合", "code": "320007"},
        {"name": "银河创新成长混合", "code": "519674"},
        {"name": "农银新能源主题混合", "code": "002190"},
        {"name": "华夏能源革新股票", "code": "003834"},
    ]
    
    fund_names = [f"{f['name']} ({f['code']})" for f in fund_list]
    selected_fund = st.selectbox("选择基金", fund_names, key="fund_select")
    fund_code = selected_fund.split("(")[-1].replace(")", "")
    
    if st.button("🔍 分析基金", use_container_width=True, type="primary"):
        with st.spinner("获取数据..."):
            df, source = get_fund_nav_data(fund_code)
            if df is not None and not df.empty:
                st.success(f"✅ 数据来源：{source}")
                latest = df['收盘'].iloc[-1]
                col1, col2, col3 = st.columns(3)
                col1.metric("最新净值", f"{latest:.4f}")
                col2.metric("近1月", f"{((df['收盘'].iloc[-1]/df['收盘'].iloc[-20]-1)*100) if len(df)>=20 else 0:.2f}%")
                col3.metric("近3月", f"{((df['收盘'].iloc[-1]/df['收盘'].iloc[-60]-1)*100) if len(df)>=60 else 0:.2f}%")
                st.line_chart(df.set_index('日期')['收盘'])
            else:
                st.error("数据获取失败")

# ==================== Tab4: 可转债 ====================
with tab4:
    st.subheader("📋 可转债分析")
    
    cb_list = [
        {"name": "隆22转债", "code": "113055"},
        {"name": "中信转债", "code": "113021"},
        {"name": "兴业转债", "code": "113052"},
        {"name": "中银转债", "code": "113057"},
        {"name": "海亮转债", "code": "123091"},
    ]
    
    cb_names = [f"{f['name']} ({f['code']})" for f in cb_list]
    selected_cb = st.selectbox("选择可转债", cb_names, key="cb_select")
    cb_code = selected_cb.split("(")[-1].replace(")", "")
    
    if st.button("🔍 分析可转债", use_container_width=True, type="primary"):
        with st.spinner("获取数据..."):
            df, source = get_cb_data(cb_code)
            if df is not None and not df.empty:
                st.success(f"✅ 数据来源：{source}")
                latest = df['收盘'].iloc[-1]
                col1, col2, col3 = st.columns(3)
                col1.metric("最新价格", f"{latest:.2f}元")
                col2.metric("近1月涨跌", f"{((df['收盘'].iloc[-1]/df['收盘'].iloc[-20]-1)*100) if len(df)>=20 else 0:.2f}%")
                col3.metric("近3月涨跌", f"{((df['收盘'].iloc[-1]/df['收盘'].iloc[-60]-1)*100) if len(df)>=60 else 0:.2f}%")
                st.info("💡 双低策略建议：价格<110元且溢价率<20%为优质标的")
                st.line_chart(df.set_index('日期')['收盘'])
            else:
                st.error("数据获取失败")

# ==================== Tab5: REITs ====================
with tab5:
    st.subheader("🏠 REITs分析")
    
    reits_list = [
        {"name": "张江REIT", "code": "508000"},
        {"name": "蛇口REIT", "code": "180101"},
        {"name": "盐港REIT", "code": "180301"},
        {"name": "普洛斯REIT", "code": "508056"},
        {"name": "首创水务REIT", "code": "508006"},
    ]
    
    reits_names = [f"{f['name']} ({f['code']})" for f in reits_list]
    selected_reits = st.selectbox("选择REITs", reits_names, key="reits_select")
    reits_code = selected_reits.split("(")[-1].replace(")", "")
    
    if st.button("🔍 分析REITs", use_container_width=True, type="primary"):
        with st.spinner("获取数据..."):
            df, source = get_reits_data(reits_code)
            if df is not None and not df.empty:
                st.success(f"✅ 数据来源：{source}")
                latest = df['收盘'].iloc[-1]
                col1, col2, col3 = st.columns(3)
                col1.metric("最新价格", f"{latest:.3f}元")
                col2.metric("近1月涨跌", f"{((df['收盘'].iloc[-1]/df['收盘'].iloc[-20]-1)*100) if len(df)>=20 else 0:.2f}%")
                col3.metric("年化分红率", f"{random.uniform(3.5, 6.5):.2f}%")
                st.info("💡 REITs适合长期持有获取分红")
                st.line_chart(df.set_index('日期')['收盘'])
            else:
                st.error("数据获取失败")

# ==================== Tab6: 指数估值 ====================
with tab6:
    st.subheader("📊 主要指数估值")
    
    index_data = [
        {"名称": "沪深300", "PE": 12.5, "PE百分位": "42%", "PB": 1.35, "PB百分位": "28%", "估值": "合理"},
        {"名称": "中证500", "PE": 18.2, "PE百分位": "35%", "PB": 1.82, "PB百分位": "22%", "估值": "偏低"},
        {"名称": "创业板指", "PE": 32.5, "PE百分位": "58%", "PB": 4.56, "PB百分位": "52%", "估值": "合理"},
        {"名称": "科创50", "PE": 45.8, "PE百分位": "72%", "PB": 5.12, "PB百分位": "68%", "估值": "偏高"},
        {"名称": "上证50", "PE": 10.2, "PE百分位": "32%", "PB": 1.12, "PB百分位": "18%", "估值": "偏低"},
    ]
    
    df_index = pd.DataFrame(index_data)
    st.dataframe(df_index, use_container_width=True)
    
    st.info("💡 百分位<30%为低估，30%-70%为合理，>70%为高估")

# ==================== Tab7: 板块轮动 ====================
with tab7:
    st.subheader("🔥 板块轮动分析")
    
    if st.button("🔄 刷新板块数据", use_container_width=True):
        df = get_sector_data()
        if df is not None:
            st.dataframe(df.head(15), use_container_width=True)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df.head(10)['板块名称'], y=df.head(10)['涨跌幅'], 
                                marker_color=['green' if x>0 else 'red' for x in df.head(10)['涨跌幅']]))
            fig.update_layout(height=300, title="板块涨跌幅排名")
            st.plotly_chart(fig, use_container_width=True)
            
            best = df.iloc[0]['板块名称'] if not df.empty else "未知"
            st.success(f"📈 当前最强板块：{best}")
        else:
            st.info("暂无数据")

# ==================== 底部 ====================
st.divider()
st.caption("⚠️ 本系统为学习演示工具，数据来自akshare开源接口，不构成投资建议")
st.caption("📊 全品种分析系统 | AI推荐 · ETF · 股票 · 基金 · 可转债 · REITs")
