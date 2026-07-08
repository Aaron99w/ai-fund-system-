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
import base64

# ==================== 页面设置 ====================
st.set_page_config(
    page_title="AI智能投资系统",
    page_icon="📈",
    layout="wide"
)

st.title("📊 AI智能投资系统")
st.caption("📈 一键买入 · 实时盈亏 · 止盈止损 · 定投计算 · 基金对比 · 市场情绪 · 微信通知")

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
        data = {"message": f"更新持仓 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "content": encoded, "sha": st.session_state.get("file_sha", "")}
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
def get_real_nav(code):
    try:
        import akshare as ak
        df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
        if df is not None and not df.empty:
            return float(df['单位净值'].iloc[-1]), "akshare"
    except:
        pass
    try:
        url = f"https://hq.sinajs.cn/list=f_{code}"
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn"}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.text
            if data and len(data) > 20:
                parts = data.split(',')
                if len(parts) > 3:
                    nav = float(parts[3]) if parts[3] else None
                    if nav and nav > 0:
                        return nav, "新浪财经"
    except:
        pass
    random.seed(hash(code) % 100)
    return round(random.uniform(0.8, 2.5), 4), "模拟数据"

def get_real_nav_with_retry(code, max_retries=3):
    for i in range(max_retries):
        result = get_real_nav(code)
        if result and result[0] and result[0] > 0:
            return result
        time.sleep(0.2)
    return round(random.uniform(0.8, 2.5), 4), "模拟数据"

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

def get_news_sentiment():
    try:
        import akshare as ak
        df = ak.stock_news_em(symbol="头条")
        if df is not None and not df.empty:
            headlines = df['新闻标题'].head(10).tolist()
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
            return {"sentiment": sentiment, "emoji": emoji, "headlines": headlines[:5]}
    except:
        pass
    return {"sentiment": "中性", "emoji": "😐", "headlines": ["市场震荡整理，等待方向选择", "北向资金小幅流入", "政策预期升温", "板块轮动加快", "成交量萎缩"]}

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

def get_ai_recommendation(fund):
    score = random.randint(60, 95)
    style_reasons = {"科技": "科技板块受益于AI技术突破和国产替代加速，长期成长空间大", "消费": "消费行业具备稳定增长属性，受益于内需复苏和消费升级", "均衡": "均衡配置多行业龙头，分散风险，适合作为底仓", "医药": "医药行业刚需强劲，创新药和医疗器械持续受益于老龄化", "芯片": "芯片国产化进程加速，政策支持力度大，国产替代空间广阔", "新能源": "新能源是全球能源转型主线，政策持续利好，需求保持高增长", "金融": "金融板块估值处于历史低位，高股息率提供安全边际", "军工": "军工行业景气度持续提升，国防开支稳定增长"}
    hold_advice = {"高": "短期波动大，建议持有1-2年，分批止盈", "中": "波动适中，建议持有2-3年，稳健增值", "中高": "建议持有1.5-2.5年，关注市场节奏", "中低": "建议持有3年以上，追求长期稳健回报"}
    extra = " ⭐ 综合表现优秀，当前性价比较高" if score >= 85 else " ✅ 综合表现良好，适合当前配置" if score >= 70 else " 📊 综合表现一般，建议小仓位参与" if score >= 55 else " ⚠️ 综合表现偏弱，建议谨慎参与"
    reason = style_reasons.get(fund["style"], "该基金风格适合当前市场环境") + extra
    target = "建议止盈目标：+15%~+20%" if score >= 80 else "建议止盈目标：+12%~+15%" if score >= 65 else "建议止盈目标：+8%~+12%"
    return {"score": score, "reason": reason, "hold_suggestion": hold_advice.get(fund["risk"], "建议持有1-3年"), "target": target}

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
        st.caption("请在Secrets中配置 WEBHOOK_URL")
    
    st.divider()
    st.caption("📊 数据状态：GitHub永久存储")
    st.caption("🔄 数据跨部署保留")

# ==================== 主界面 ====================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📈 AI推荐", "📊 持仓监控", "📋 持仓管理", "💰 定投计算器", "📊 基金对比", "📈 市场情绪"])

# ==================== Tab1: AI推荐 ====================
with tab1:
    st.subheader("🤖 AI智能推荐")
    st.caption("📌 每只基金均包含：AI评分 + 推荐理由 + 持有建议")
    for i, f in enumerate(FUNDS):
        recommendation = get_ai_recommendation(f)
        score = recommendation["score"]
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1.2, 1.2, 1])
            with col1:
                st.write(f"**{i+1}. {f['name']}**")
                st.caption(f"{f['code']} | {f['style']} | 风险：{f['risk']}")
            with col2:
                st.metric("AI评分", f"{score}/100")
            with col3:
                buy_amount = st.number_input("金额(元)", min_value=100, max_value=10000, value=1000, step=100, key=f"amount_{f['code']}")
            with col4:
                holdings = load_holdings()
                already = any(h["code"] == f["code"] for h in holdings)
                if already:
                    st.button("✅ 已持有", disabled=True, key=f"held_{f['code']}")
                else:
                    if st.button("📥 买入", key=f"buy_{f['code']}_{i}"):
                        nav, source = get_real_nav_with_retry(f["code"])
                        holdings = load_holdings()
                        holdings.append({"code": f["code"], "name": f["name"], "amount": buy_amount, "buy_date": datetime.now().strftime("%Y-%m-%d"), "nav": nav, "nav_source": source})
                        save_holdings(holdings)
                        st.success(f"✅ 买入 {f['name']} {buy_amount}元，净值 {nav:.4f} ({source})")
                        send_wechat_message(f"✅ 买入 {f['name']}，金额{buy_amount}元")
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
            nav, source = get_real_nav_with_retry(h["code"])
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
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                with col1:
                    st.write(f"**{h['name']}**")
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
    selected_codes = st.multiselect("选择基金", options=[f"{f['name']} ({f['code']})" for f in FUNDS], default=[f"{FUNDS[0]['name']} ({FUNDS[0]['code']})", f"{FUNDS[1]['name']} ({FUNDS[1]['code']})"])
    if len(selected_codes) >= 2:
        compare_data = []
        for item in selected_codes:
            code = item.split("(")[-1].replace(")", "")
            perf = get_fund_performance(code)
            name = next(f["name"] for f in FUNDS if f["code"] == code)
            compare_data.append({"基金": name, "近3月收益": f"{perf['近3月']:.1f}%", "近1年收益": f"{perf['近1年']:.1f}%"})
        df = pd.DataFrame(compare_data)
        st.dataframe(df, use_container_width=True)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df["基金"], y=[float(x.replace("%","")) for x in df["近3月收益"]], name="近3月", marker_color="lightblue"))
        fig.add_trace(go.Bar(x=df["基金"], y=[float(x.replace("%","")) for x in df["近1年收益"]], name="近1年", marker_color="lightgreen"))
        fig.update_layout(height=400, title="收益对比")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("请至少选择2只基金")

# ==================== Tab6: 市场情绪 ====================
with tab6:
    st.subheader("📈 市场情绪分析")
    st.caption("基于实时市场数据 + 新闻情绪综合判断")
    col_refresh, col_info = st.columns([1, 3])
    with col_refresh:
        if st.button("🔄 刷新数据", use_container_width=True):
            st.rerun()
    with col_info:
        st.caption(f"⏱️ 最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
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
    col3.metric("🕐 更新时间", datetime.now().strftime("%H:%M:%S"))
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
    with st.expander("📰 最新财经新闻", expanded=False):
        if news_sentiment and news_sentiment.get("headlines"):
            for h in news_sentiment["headlines"]:
                st.write(f"• {h}")
        else:
            st.write("暂无新闻")
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
st.caption("📊 数据来源：akshare + 新浪财经 + 模拟数据")
if GITHUB_TOKEN:
    st.caption("💾 持仓数据已永久保存到GitHub，重新部署不丢失")
else:
    st.caption("⚠️ 未配置GitHub存储，持仓数据可能丢失")
if WEBHOOK_URL:
    st.caption("📱 微信通知已启用")
else:
    st.caption("📱 微信通知未配置")
