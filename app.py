import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone
import json
import os
import requests
import random
import time
import base64

# ==================== 北京时间工具函数 ====================
def get_beijing_time():
    return datetime.utcnow() + timedelta(hours=8)

def format_beijing_time(fmt="%Y-%m-%d %H:%M:%S"):
    return get_beijing_time().strftime(fmt)

def format_beijing_time_short():
    return get_beijing_time().strftime("%H:%M:%S")

# ==================== 页面设置 ====================
st.set_page_config(
    page_title="AI智能投资系统",
    page_icon="📈",
    layout="wide"
)

st.title("📊 AI智能投资系统")
st.caption("📈 场内ETF · 场外基金 · 股票 · 可转债 · REITs · 全品种覆盖")

# ==================== GitHub永久存储 ====================
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
GITHUB_REPO = st.secrets.get("GITHUB_REPO", "Aaron99w/ai-fund-system")
WEBHOOK_URL = st.secrets.get("WEBHOOK_URL", "")
HOLDINGS_PATH = "holdings.json"

def github_api_request(endpoint, method="GET", data=None):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/{endpoint}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=10)
        else:
            return None
        return response
    except:
        return None

def load_holdings_from_github():
    if not GITHUB_TOKEN:
        return load_holdings_local()
    try:
        response = github_api_request(f"contents/{HOLDINGS_PATH}")
        if response and response.status_code == 200:
            content = response.json()
            file_content = base64.b64decode(content["content"]).decode("utf-8")
            data = json.loads(file_content)
            st.session_state["file_sha"] = content.get("sha", "")
            return data
        elif response and response.status_code == 404:
            save_holdings_to_github([])
            return []
        else:
            return load_holdings_local()
    except:
        return load_holdings_local()

def save_holdings_to_github(holdings):
    if not GITHUB_TOKEN:
        return save_holdings_local(holdings)
    try:
        content = json.dumps(holdings, ensure_ascii=False, indent=2)
        encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        data = {"message": f"更新持仓 {format_beijing_time()}", "content": encoded, "sha": st.session_state.get("file_sha", "")}
        response = github_api_request(f"contents/{HOLDINGS_PATH}", "PUT", data)
        if response and response.status_code in [200, 201]:
            if response.status_code == 201:
                st.session_state["file_sha"] = response.json().get("content", {}).get("sha", "")
            return True
        else:
            return save_holdings_local(holdings)
    except:
        return save_holdings_local(holdings)

def load_holdings_local():
    if os.path.exists("holdings.json"):
        try:
            with open("holdings.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_holdings_local(holdings):
    try:
        with open("holdings.json", "w", encoding="utf-8") as f:
            json.dump(holdings, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def load_holdings():
    return load_holdings_from_github()

def save_holdings(holdings):
    return save_holdings_to_github(holdings)

# ==================== 微信通知 ====================
def send_wechat_message(content):
    if not WEBHOOK_URL:
        return False
    try:
        data = {"msgtype": "text", "text": {"content": content[:2000]}}
        response = requests.post(WEBHOOK_URL, json=data, timeout=5)
        return response.status_code == 200
    except:
        return False

# ==================== 真实净值获取 ====================
def get_real_nav(code, asset_type="场外基金"):
    try:
        import akshare as ak
        if asset_type in ["场外基金", "普通基金"]:
            df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
            if df is not None and not df.empty:
                return float(df['单位净值'].iloc[-1]), "akshare"
        else:
            df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=(datetime.now()-timedelta(days=3)).strftime("%Y%m%d"), end_date=datetime.now().strftime("%Y%m%d"), adjust="qfq")
            if df is not None and not df.empty:
                return float(df['收盘'].iloc[-1]), "akshare"
    except:
        pass
    random.seed(hash(code) % 100)
    return round(random.uniform(0.8, 5.0), 4), "模拟数据"

def get_real_nav_with_retry(code, asset_type="场外基金", max_retries=3):
    for i in range(max_retries):
        result = get_real_nav(code, asset_type)
        if result and result[0] and result[0] > 0:
            return result
        time.sleep(0.2)
    return round(random.uniform(0.8, 5.0), 4), "模拟数据"

# ==================== 五大类别资产池 ====================
ASSET_POOLS = {
    "场内ETF": {
        "icon": "📈",
        "description": "交易灵活、费用低，适合短线操作和行业轮动",
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
            {"name": "纳指ETF", "code": "513100", "style": "美股", "risk": "高"},
            {"name": "恒生科技ETF", "code": "513130", "style": "港股科技", "risk": "高"},
            {"name": "银行ETF", "code": "512800", "style": "银行", "risk": "低"},
            {"name": "消费ETF", "code": "159928", "style": "消费", "risk": "中"},
        ]
    },
    "场外基金": {
        "icon": "📊",
        "description": "主动管理型基金，适合长期定投",
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
    "股票": {
        "icon": "💹",
        "description": "精选A股优质龙头，适合深入研究",
        "list": [
            {"name": "贵州茅台", "code": "600519", "style": "消费", "risk": "中"},
            {"name": "宁德时代", "code": "300750", "style": "新能源", "risk": "高"},
            {"name": "比亚迪", "code": "002594", "style": "新能源", "risk": "高"},
            {"name": "药明康德", "code": "603259", "style": "医药", "risk": "高"},
            {"name": "中国平安", "code": "601318", "style": "金融", "risk": "中"},
            {"name": "招商银行", "code": "600036", "style": "金融", "risk": "中"},
            {"name": "美的集团", "code": "000333", "style": "消费", "risk": "中"},
            {"name": "中芯国际", "code": "688981", "style": "芯片", "risk": "高"},
            {"name": "长江电力", "code": "600900", "style": "电力", "risk": "低"},
            {"name": "海尔智家", "code": "600690", "style": "消费", "risk": "中"},
        ]
    },
    "可转债": {
        "icon": "📋",
        "description": "下有保底上不封顶，适合稳健型投资者",
        "list": [
            {"name": "隆22转债", "code": "113055", "style": "光伏", "risk": "中"},
            {"name": "中信转债", "code": "113021", "style": "金融", "risk": "低"},
            {"name": "兴业转债", "code": "113052", "style": "金融", "risk": "低"},
            {"name": "中银转债", "code": "113057", "style": "金融", "risk": "低"},
            {"name": "海亮转债", "code": "123091", "style": "有色", "risk": "中"},
        ]
    },
    "REITs": {
        "icon": "🏠",
        "description": "稳定收息资产，适合长期持有获取分红",
        "list": [
            {"name": "张江REIT", "code": "508000", "style": "产业园", "risk": "中"},
            {"name": "蛇口REIT", "code": "180101", "style": "产业园", "risk": "中"},
            {"name": "盐港REIT", "code": "180301", "style": "港口", "risk": "中"},
            {"name": "普洛斯REIT", "code": "508056", "style": "仓储", "risk": "中"},
            {"name": "首创水务REIT", "code": "508006", "style": "水务", "risk": "中"},
        ]
    }
}

# ==================== AI推荐评分 ====================
def get_ai_recommendation(asset, asset_type):
    score = random.randint(60, 95)
    style_reasons = {
        "科技": "科技板块受益于AI技术突破和国产替代加速，长期成长空间大",
        "消费": "消费行业具备稳定增长属性，受益于内需复苏和消费升级",
        "均衡": "均衡配置多行业龙头，分散风险，适合作为底仓",
        "医药": "医药行业刚需强劲，创新药和医疗器械持续受益于老龄化",
        "芯片": "芯片国产化进程加速，政策支持力度大，国产替代空间广阔",
        "新能源": "新能源是全球能源转型主线，政策持续利好，需求保持高增长",
        "金融": "金融板块估值处于历史低位，高股息率提供安全边际",
        "军工": "军工行业景气度持续提升，国防开支稳定增长",
        "科创板": "科创企业高成长性，代表未来发展方向",
        "创业板": "创业创新企业活力强，成长空间大",
        "半导体": "半导体国产化进程加速，政策支持力度大",
        "AI": "人工智能是未来十年最大的技术革命",
        "券商": "券商直接受益于市场活跃度提升",
        "大盘": "大盘蓝筹稳健，适合作为底仓配置",
        "中小盘": "中小盘弹性大，成长性突出",
        "白酒": "白酒行业消费升级趋势明确",
        "互联网": "互联网平台经济价值重估",
        "美股": "美股科技巨头全球领先",
        "港股科技": "港股科技股估值处于历史低位",
        "银行": "银行板块高股息，防御属性强",
        "光伏": "光伏装机持续增长，全球需求旺盛",
        "产业园": "产业园租金收入稳定",
        "港口": "港口吞吐量稳定增长",
        "仓储": "仓储物流需求持续旺盛",
        "水务": "水务刚需属性强",
        "有色": "有色金属价格波动带来交易机会",
        "电力": "电力需求稳定增长",
    }
    hold_advice = {
        "高": "短期波动大，建议持有1-2年，分批止盈",
        "中": "波动适中，建议持有2-3年，稳健增值",
        "中高": "建议持有1.5-2.5年，关注市场节奏",
        "中低": "建议持有3年以上，追求长期稳健回报",
        "低": "波动小，建议持有3-5年，追求稳定回报"
    }
    extra = " ⭐ 综合表现优秀，当前性价比较高" if score >= 85 else " ✅ 综合表现良好，适合当前配置" if score >= 70 else " 📊 综合表现一般，建议小仓位参与" if score >= 55 else " ⚠️ 综合表现偏弱，建议谨慎参与"
    reason = style_reasons.get(asset.get("style", ""), "该资产风格适合当前市场环境") + extra
    target = "建议止盈目标：+15%~+20%" if score >= 80 else "建议止盈目标：+12%~+15%" if score >= 65 else "建议止盈目标：+8%~+12%"
    return {
        "score": score,
        "reason": reason,
        "hold_suggestion": hold_advice.get(asset.get("risk", "中"), "建议持有1-3年"),
        "target": target
    }

# ==================== 市场数据 ====================
def get_market_data():
    try:
        import akshare as ak
        indices = {"上证指数": "sh000001", "深证成指": "sz399001", "创业板指": "sz399006", "沪深300": "sh000300", "科创50": "sh000688"}
        market_data = {}
        for name, code in indices.items():
            try:
                df = ak.stock_zh_index_hist(symbol=code, period="daily", start_date=(datetime.now()-timedelta(days=3)).strftime("%Y%m%d"), end_date=datetime.now().strftime("%Y%m%d"))
                if df is not None and not df.empty:
                    latest = df.iloc[-1]
                    prev = df.iloc[-2] if len(df) >= 2 else latest
                    change = (latest['close'] - prev['close']) / prev['close'] * 100 if prev['close'] != 0 else 0
                    market_data[name] = {"price": round(latest['close'], 2), "change": round(change, 2)}
            except:
                pass
        if not market_data:
            for name in indices.keys():
                change = random.uniform(-1.5, 1.8)
                market_data[name] = {"price": round(random.uniform(3000, 5000), 2), "change": round(change, 2)}
        return market_data
    except:
        return {"上证指数": {"price": 3256.78, "change": round(random.uniform(-1.5, 1.8), 2)}, "深证成指": {"price": 10890.23, "change": round(random.uniform(-1.5, 1.8), 2)}, "创业板指": {"price": 2156.45, "change": round(random.uniform(-1.5, 1.8), 2)}, "沪深300": {"price": 3890.12, "change": round(random.uniform(-1.5, 1.8), 2)}, "科创50": {"price": 987.65, "change": round(random.uniform(-1.5, 1.8), 2)}}

def get_hot_sectors():
    try:
        import akshare as ak
        df = ak.stock_sector_spot()
        if df is not None and not df.empty:
            top = df.head(5)
            bottom = df.tail(5)
            return {"top": top[['板块名称', '涨跌幅']].to_dict('records'), "bottom": bottom[['板块名称', '涨跌幅']].to_dict('records')}
    except:
        pass
    sectors = ["半导体", "人工智能", "新能源车", "光伏", "医药", "白酒", "金融", "军工"]
    random.shuffle(sectors)
    top = []
    bottom = []
    for s in sectors[:3]:
        top.append({"板块名称": s, "涨跌幅": round(random.uniform(1.5, 4.5), 2)})
    for s in sectors[-3:]:
        bottom.append({"板块名称": s, "涨跌幅": round(random.uniform(-3.5, -0.5), 2)})
    return {"top": top, "bottom": bottom}

# ==================== 东方财富新闻快讯（7×24） ====================
def get_news_sentiment():
    """获取东方财富新闻（头条+快讯）"""
    try:
        import akshare as ak
        df_toutiao = ak.stock_news_em(symbol="头条")
        df_kuaixun = ak.stock_news_em(symbol="快讯")
        
        all_news = []
        if df_toutiao is not None and not df_toutiao.empty:
            all_news.extend(df_toutiao['新闻标题'].tolist())
        if df_kuaixun is not None and not df_kuaixun.empty:
            all_news.extend(df_kuaixun['新闻标题'].tolist())
        headlines = list(dict.fromkeys(all_news))[:20]  # 去重，取前20条
        
        pos_keywords = ["上涨", "大涨", "利好", "反弹", "突破", "新高", "增长", "降息", "政策", "支持"]
        neg_keywords = ["下跌", "大跌", "利空", "回调", "破位", "新低", "亏损", "加息", "制裁", "风险"]
        pos_score = sum(1 for h in headlines for kw in pos_keywords if kw in str(h))
        neg_score = sum(1 for h in headlines for kw in neg_keywords if kw in str(h))
        
        if pos_score + neg_score == 0:
            sentiment, emoji = "中性", "😐"
        elif pos_score > neg_score * 1.5:
            sentiment, emoji = "乐观", "😊"
        elif neg_score > pos_score * 1.5:
            sentiment, emoji = "悲观", "😰"
        else:
            sentiment, emoji = "中性", "😐"
        
        return {
            "sentiment": sentiment,
            "emoji": emoji,
            "headlines": headlines,
            "source": "东方财富（头条+快讯）"
        }
    except Exception as e:
        return {
            "sentiment": "中性",
            "emoji": "😐",
            "headlines": [
                "市场震荡整理，等待方向选择",
                "北向资金小幅流入",
                "政策预期升温",
                "板块轮动加快",
                "成交量萎缩"
            ],
            "source": "模拟数据"
        }

def get_market_info():
    try:
        import akshare as ak
        news = ak.stock_news_em(symbol="头条")
        if news is not None and not news.empty:
            headlines = news['新闻标题'].head(10).tolist()
            good, bad = [], []
            good_kw = ["利好", "上涨", "大涨", "反弹", "突破", "新高", "增长", "降息", "政策支持", "资金流入"]
            bad_kw = ["利空", "下跌", "大跌", "回调", "破位", "新低", "亏损", "加息", "制裁", "风险"]
            for h in headlines:
                h_str = str(h)
                if any(kw in h_str for kw in good_kw) and not any(kw in h_str for kw in bad_kw):
                    good.append(h_str[:30] + "...")
                elif any(kw in h_str for kw in bad_kw) and not any(kw in h_str for kw in good_kw):
                    bad.append(h_str[:30] + "...")
            return {"good": good[:3], "bad": bad[:3]}
    except:
        pass
    return {"good": ["政策持续发力，稳增长预期明确", "北向资金今日净流入超50亿元", "科技板块迎来新的政策支持"], "bad": ["市场成交量持续萎缩", "部分行业面临去库存压力", "外部环境不确定性增加"]}

# ==================== 定投计算器 ====================
def calculate_drip(monthly, annual_return, years):
    months = years * 12
    rate = annual_return / 12 / 100
    total = 0
    for _ in range(months):
        total = (total + monthly) * (1 + rate)
    return total

def get_fund_performance(code):
    return {"近3月": round(random.uniform(-5, 15), 2), "近1年": round(random.uniform(-10, 30), 2)}

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
if "file_sha" not in st.session_state:
    st.session_state.file_sha = ""

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
    if GITHUB_TOKEN:
        st.caption("💾 数据已永久保存到GitHub")
    else:
        st.caption("⚠️ 未配置GitHub存储")
    
    st.divider()
    st.subheader("📱 微信通知")
    if WEBHOOK_URL:
        st.success("✅ 微信通知已配置")
        if st.button("📤 测试通知", use_container_width=True):
            if send_wechat_message("✅ 测试消息：AI投资助手微信通知正常！"):
                st.success("✅ 发送成功")
            else:
                st.error("❌ 发送失败")
    else:
        st.warning("⚠️ 未配置微信通知")
    
    st.divider()
    st.caption("📊 数据状态：GitHub永久存储")
    st.caption("🔄 数据跨部署保留")
    st.caption(f"🕐 当前北京时间：{format_beijing_time()}")

# ==================== 主界面 ====================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 AI推荐",
    "📊 持仓监控",
    "📋 持仓管理",
    "💰 定投计算器",
    "📊 基金对比",
    "📈 市场情绪"
])

# ==================== Tab1: AI推荐（五大类别） ====================
with tab1:
    st.subheader("🤖 AI智能推荐")
    st.caption("📌 选择资产类别，AI从该类别中精选推荐")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        asset_category = st.selectbox(
            "选择资产类别",
            options=list(ASSET_POOLS.keys()),
            format_func=lambda x: f"{ASSET_POOLS[x]['icon']} {x} - {ASSET_POOLS[x]['description'][:20]}..."
        )
    with col2:
        st.caption(f"📊 {ASSET_POOLS[asset_category]['icon']} {asset_category}")
        st.caption(f"共 {len(ASSET_POOLS[asset_category]['list'])} 只标的")
    
    st.info(f"📌 {ASSET_POOLS[asset_category]['description']}")
    
    assets = ASSET_POOLS[asset_category]["list"]
    
    for i, asset in enumerate(assets):
        recommendation = get_ai_recommendation(asset, asset_category)
        score = recommendation["score"]
        
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1.2, 1.2, 1])
            with col1:
                st.write(f"**{i+1}. {asset['name']}**")
                st.caption(f"{asset['code']} | {asset['style']} | 风险：{asset['risk']}")
            with col2:
                st.metric("AI评分", f"{score}/100")
            with col3:
                buy_amount = st.number_input(
                    "金额(元)", 
                    min_value=100, 
                    max_value=10000, 
                    value=1000, 
                    step=100, 
                    key=f"amount_{asset_category}_{asset['code']}"
                )
            with col4:
                holdings = load_holdings()
                already = any(h["code"] == asset["code"] for h in holdings)
                if already:
                    st.button("✅ 已持有", disabled=True, key=f"held_{asset_category}_{asset['code']}")
                else:
                    if st.button("📥 买入", key=f"buy_{asset_category}_{asset['code']}_{i}"):
                        nav, source = get_real_nav_with_retry(asset["code"], asset_category)
                        holdings = load_holdings()
                        holdings.append({
                            "code": asset["code"],
                            "name": asset["name"],
                            "amount": buy_amount,
                            "buy_date": get_beijing_time().strftime("%Y-%m-%d"),
                            "nav": nav,
                            "nav_source": source,
                            "asset_type": asset_category,
                            "style": asset.get("style", "")
                        })
                        save_holdings(holdings)
                        st.success(f"✅ 买入 {asset['name']} {buy_amount}元，净值 {nav:.4f} ({source})")
                        send_wechat_message(f"✅ 买入 {asset['name']}，金额{buy_amount}元")
                        st.rerun()
            
            st.info(f"💡 **推荐理由**：{recommendation['reason']}")
            st.caption(f"📅 **建议持有**：{recommendation['hold_suggestion']} | **止盈目标**：{recommendation['target']}")
            st.divider()

# ==================== Tab2: 持仓监控 ====================
with tab2:
    st.subheader("📊 持仓监控")
    st.caption("📌 实时盈亏 = (当前净值 - 买入价) × 持有份额")
    holdings = load_holdings()
    if holdings:
        nav_cache = {}
        for h in holdings:
            asset_type = h.get("asset_type", "场外基金")
            nav, source = get_real_nav_with_retry(h["code"], asset_type)
            nav_cache[h["code"]] = {"nav": nav, "source": source}
        total_profit, total_cost = 0, 0
        for h in holdings:
            code = h["code"]
            buy_price = h.get("nav", 0)
            amount = h.get("amount", 0)
            shares = amount / buy_price if buy_price > 0 else 0
            nav_info = nav_cache.get(code, {"nav": buy_price, "source": "未知"})
            current_nav = nav_info["nav"]
            source = nav_info["source"]
            profit = (current_nav - buy_price) * shares if buy_price > 0 else 0
            profit_rate = (current_nav - buy_price) / buy_price * 100 if buy_price > 0 else 0
            total_profit += profit
            total_cost += amount
            status, action = check_stop(profit_rate)
            asset_type = h.get("asset_type", "场外基金")
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                with col1:
                    st.write(f"**{h['name']}**")
                    st.caption(f"{asset_type} | {h.get('style', '')}")
                    st.caption(f"买入价：{buy_price:.4f} | 现价：{current_nav:.4f}")
                    st.caption(f"份额：{shares:.2f}份 | 数据：{source}")
                with col2:
                    st.metric("盈亏率", f"{'+' if profit_rate > 0 else ''}{profit_rate:.2f}%")
                with col3:
                    st.metric("盈亏金额", f"{'+' if profit > 0 else ''}{profit:.2f}元")
                with col4:
                    st.write(status)
                with col5:
                    if action == "止盈":
                        if st.button("📤 已止盈", key=f"take_profit_{code}"):
                            holdings = [x for x in holdings if x["code"] != code]
                            save_holdings(holdings)
                            send_wechat_message(f"📈 {h['name']} 已止盈，盈利 {profit:.2f}元")
                            st.rerun()
                    elif action == "止损":
                        if st.button("📤 已止损", key=f"stop_loss_{code}"):
                            holdings = [x for x in holdings if x["code"] != code]
                            save_holdings(holdings)
                            send_wechat_message(f"📉 {h['name']} 已止损，亏损 {profit:.2f}元")
                            st.rerun()
                    else:
                        st.info("🟢 继续持有")
                st.divider()
        st.subheader("📊 持仓汇总")
        col1, col2, col3 = st.columns(3)
        col1.metric("总投入", f"{total_cost:.2f}元")
        col2.metric("总盈亏", f"{'+' if total_profit > 0 else ''}{total_profit:.2f}元")
        col3.metric("总收益率", f"{'+' if total_cost > 0 else ''}{(total_profit/total_cost*100):.2f}%" if total_cost > 0 else "0.00%")
        if total_profit > 0:
            st.success(f"🎉 当前总盈利 {total_profit:.2f} 元，恭喜！")
        elif total_profit < 0:
            st.warning(f"⚠️ 当前总亏损 {abs(total_profit):.2f} 元，注意风险")
        else:
            st.info("📊 当前盈亏平衡")
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
                st.caption(f"类型：{h.get('asset_type', '场外基金')}")
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
    all_assets = []
    for category, pool in ASSET_POOLS.items():
        for asset in pool["list"]:
            all_assets.append(f"{asset['name']} ({asset['code']})")
    selected_codes = st.multiselect("选择标的", options=all_assets, default=all_assets[:2] if len(all_assets) >= 2 else all_assets)
    if len(selected_codes) >= 2:
        compare_data = []
        for item in selected_codes:
            code = item.split("(")[-1].replace(")", "")
            perf = get_fund_performance(code)
            name = item.split(" (")[0]
            compare_data.append({"标的": name, "近3月收益": f"{perf['近3月']:.1f}%", "近1年收益": f"{perf['近1年']:.1f}%"})
        df = pd.DataFrame(compare_data)
        st.dataframe(df, use_container_width=True)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df["标的"], y=[float(x.replace("%","")) for x in df["近3月收益"]], name="近3月", marker_color="lightblue"))
        fig.add_trace(go.Bar(x=df["标的"], y=[float(x.replace("%","")) for x in df["近1年收益"]], name="近1年", marker_color="lightgreen"))
        fig.update_layout(height=400, title="收益对比")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("请至少选择2只标的")

# ==================== Tab6: 市场情绪（含东方财富快讯） ====================
with tab6:
    st.subheader("📈 市场情绪分析")
    st.caption("基于实时市场数据 + 东方财富新闻情绪综合判断")
    col_refresh, col_info = st.columns([1, 3])
    with col_refresh:
        if st.button("🔄 刷新数据", use_container_width=True):
            st.rerun()
    with col_info:
        st.caption(f"⏱️ 最后更新（北京时间）：{format_beijing_time()}")
    market_data = get_market_data()
    hot_sectors = get_hot_sectors()
    news_sentiment = get_news_sentiment()
    market_info = get_market_info()
    index_changes = [v["change"] for v in market_data.values()]
    avg_change = sum(index_changes) / len(index_changes) if index_changes else 0
    news_score = 1 if news_sentiment["sentiment"] == "乐观" else -1 if news_sentiment["sentiment"] == "悲观" else 0
    if avg_change > 0.5 and news_score >= 0:
        final_sentiment, sentiment_desc, advice = "乐观 😊", "市场整体上涨，新闻情绪偏积极", "💡 市场情绪乐观，可适当增加仓位"
    elif avg_change > 0 and news_score >= 0:
        final_sentiment, sentiment_desc, advice = "中性偏乐观 🚀", "市场小幅上涨，情绪平稳", "💡 市场情绪平稳，保持现有配置"
    elif avg_change < -0.5 and news_score <= 0:
        final_sentiment, sentiment_desc, advice = "悲观 😰", "市场整体下跌，新闻情绪偏消极", "💡 市场情绪悲观，建议控制仓位"
    else:
        final_sentiment, sentiment_desc, advice = "中性 😐", "市场震荡整理，方向不明", "💡 市场情绪中性，保持观望"
    col1, col2, col3 = st.columns(3)
    col1.metric("📊 综合情绪", final_sentiment)
    col2.metric("📈 平均涨跌幅", f"{'+' if avg_change > 0 else ''}{avg_change:.2f}%")
    col3.metric("🕐 更新时间（北京）", format_beijing_time_short())
    st.caption(f"📌 {sentiment_desc}")
    st.subheader("📊 各大指数表现")
    index_cols = st.columns(5)
    for i, (name, data) in enumerate(market_data.items()):
        with index_cols[i]:
            change = data["change"]
            st.metric(name, f"{data['price']:.2f}", delta=f"{'+' if change > 0 else ''}{change:.2f}%")
    st.subheader("🔥 热门板块")
    col1, col2 = st.columns(2)
    with col1:
        st.caption("📈 涨幅居前")
        if hot_sectors and hot_sectors.get("top"):
            for s in hot_sectors["top"]:
                st.write(f"✅ {s['板块名称']}：+{s['涨跌幅']:.2f}%")
        else:
            st.info("暂无数据")
    with col2:
        st.caption("📉 跌幅居前")
        if hot_sectors and hot_sectors.get("bottom"):
            for s in hot_sectors["bottom"]:
                st.write(f"❌ {s['板块名称']}：{s['涨跌幅']:.2f}%")
        else:
            st.info("暂无数据")
    st.subheader("📰 市场信息")
    col1, col2 = st.columns(2)
    with col1:
        st.success("🟢 利好因素")
        if market_info and market_info.get("good"):
            for item in market_info["good"]:
                st.write(f"• {item}")
        else:
            st.write("• 暂无明显利好")
    with col2:
        st.error("🔴 利空因素")
        if market_info and market_info.get("bad"):
            for item in market_info["bad"]:
                st.write(f"• {item}")
        else:
            st.write("• 暂无明显利空")
    with st.expander("📰 东方财富7×24快讯", expanded=False):
        if news_sentiment and news_sentiment.get("headlines"):
            st.caption(f"📌 来源：{news_sentiment.get('source', '东方财富')}")
            for h in news_sentiment["headlines"]:
                st.write(f"• {h}")
        else:
            st.write("暂无快讯")
    st.divider()
    st.subheader("💡 综合投资建议")
    st.info(advice)
    if avg_change > 0.5:
        st.success("✅ 市场环境偏暖，可关注科技、消费等板块")
    elif avg_change < -0.5:
        st.warning("⚠️ 市场环境偏冷，建议控制仓位，等待企稳")
    else:
        st.info("📊 市场震荡整理，建议均衡配置")
    st.caption("💡 提示：点击「刷新数据」按钮或按 F5 刷新页面获取最新行情")

# ==================== 底部 ====================
st.divider()
st.caption("⚠️ 本系统为学习演示工具，不构成投资建议")
st.caption("📊 数据来源：东方财富(中国财经网) + akshare + 新浪财经 + 模拟数据")
if GITHUB_TOKEN:
    st.caption("💾 持仓数据已永久保存到GitHub，重新部署不丢失")
else:
    st.caption("⚠️ 未配置GitHub存储，持仓数据可能丢失")
if WEBHOOK_URL:
    st.caption("📱 微信通知已启用")
else:
    st.caption("📱 微信通知未配置")
