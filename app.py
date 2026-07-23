import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json
import os
import requests
import random
import time
import base64

# ==================== 北京时间工具 ====================
def get_beijing_time():
    return datetime.utcnow() + timedelta(hours=8)

def format_beijing_time(fmt="%Y-%m-%d %H:%M:%S"):
    return get_beijing_time().strftime(fmt)

# ==================== 页面设置 ====================
st.set_page_config(
    page_title="AI智能投资系统 Pro",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 AI智能投资系统 Pro")
st.caption("📈 对话交互 · 智能诊断 · 自动盯盘 · 千人千面 · 全流程闭环")

# ==================== GitHub永久存储 ====================
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
GITHUB_REPO = st.secrets.get("GITHUB_REPO", "Aaron99w/ai-fund-system")
HOLDINGS_PATH = "holdings.json"
USER_PROFILE_PATH = "user_profile.json"

def github_api_request(endpoint, method="GET", data=None):
    if not GITHUB_TOKEN:
        return None
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

def load_data(filename, default):
    if not GITHUB_TOKEN:
        return default
    try:
        response = github_api_request(f"contents/{filename}")
        if response and response.status_code == 200:
            content = response.json()
            file_content = base64.b64decode(content["content"]).decode("utf-8")
            data = json.loads(file_content)
            st.session_state[f"{filename}_sha"] = content.get("sha", "")
            return data
        elif response and response.status_code == 404:
            save_data(filename, default)
            return default
        else:
            return default
    except:
        return default

def save_data(filename, data):
    if not GITHUB_TOKEN:
        return False
    try:
        content = json.dumps(data, ensure_ascii=False, indent=2)
        encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        payload = {"message": f"更新 {filename} {format_beijing_time()}", "content": encoded}
        sha = st.session_state.get(f"{filename}_sha")
        if sha:
            payload["sha"] = sha
        response = github_api_request(f"contents/{filename}", "PUT", payload)
        if response and response.status_code in [200, 201]:
            if response.status_code == 201:
                st.session_state[f"{filename}_sha"] = response.json().get("content", {}).get("sha", "")
            return True
        return False
    except:
        return False

def load_holdings():
    return load_data(HOLDINGS_PATH, [])

def save_holdings(holdings):
    return save_data(HOLDINGS_PATH, holdings)

def load_user_profile():
    return load_data(USER_PROFILE_PATH, {"risk": "中", "goal": "稳健增值", "horizon": 3})

def save_user_profile(profile):
    return save_data(USER_PROFILE_PATH, profile)

# ==================== 微信通知 ====================
WEBHOOK_URL = st.secrets.get("WEBHOOK_URL", "")

def send_wechat_message(content):
    if not WEBHOOK_URL:
        return False
    try:
        data = {"msgtype": "text", "text": {"content": content[:2000]}}
        response = requests.post(WEBHOOK_URL, json=data, timeout=5)
        return response.status_code == 200
    except:
        return False

# ==================== DeepSeek API ====================
DEEPSEEK_API_KEY = st.secrets.get("DEEPSEEK_API_KEY", "")

def call_deepseek(prompt, system="你是一个专业的投资顾问，回答简洁、实用。"):
    if not DEEPSEEK_API_KEY:
        return None
    try:
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 500
        }
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return None
    except:
        return None

# ==================== 市场数据获取 ====================
def get_sector_performance():
    try:
        import akshare as ak
        etfs = [
            {"name": "科技", "code": "515000"},
            {"name": "半导体", "code": "512480"},
            {"name": "芯片", "code": "159995"},
            {"name": "人工智能", "code": "159819"},
            {"name": "新能源车", "code": "515030"},
            {"name": "光伏", "code": "515790"},
            {"name": "军工", "code": "512660"},
            {"name": "消费", "code": "159928"},
            {"name": "医药", "code": "512010"},
            {"name": "红利", "code": "510880"},
            {"name": "证券", "code": "512880"},
            {"name": "银行", "code": "512800"},
            {"name": "沪深300", "code": "510300"},
            {"name": "科创50", "code": "588000"},
            {"name": "创业板", "code": "159915"},
        ]
        results = []
        end = datetime.now().strftime("%Y%m%d")
        start_1m = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        for etf in etfs:
            try:
                df = ak.stock_zh_a_hist(symbol=etf["code"], period="daily", 
                                       start_date=start_1m, end_date=end, adjust="qfq")
                if df is not None and not df.empty and len(df) >= 5:
                    ret_1m = (df['收盘'].iloc[-1] / df['收盘'].iloc[0] - 1) * 100
                    results.append({
                        "板块": etf["name"],
                        "近1月%": round(ret_1m, 2),
                        "趋势": "📈" if ret_1m > 0 else "📉" if ret_1m < -2 else "➡️"
                    })
            except:
                pass
        if results:
            return sorted(results, key=lambda x: x["近1月%"], reverse=True)
        return generate_simulated_sectors()
    except:
        return generate_simulated_sectors()

def generate_simulated_sectors():
    sectors = ["科技", "半导体", "芯片", "人工智能", "新能源车", "光伏", "军工", "消费", "医药", "红利", "证券", "银行", "沪深300", "科创50", "创业板"]
    results = []
    for s in sectors:
        ret = round(random.uniform(-8, 6), 2)
        results.append({"板块": s, "近1月%": ret, "趋势": "📈" if ret > 0 else "📉" if ret < -2 else "➡️"})
    return sorted(results, key=lambda x: x["近1月%"], reverse=True)

def get_fund_nav(code):
    try:
        import akshare as ak
        df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
        if df is not None and not df.empty:
            return float(df['单位净值'].iloc[-1]), "akshare"
    except:
        pass
    return round(random.uniform(0.8, 3.0), 4), "模拟"

def agent_portfolio_diagnosis(holdings):
    if not holdings:
        return "暂无持仓，无法诊断。建议先通过AI推荐买入。"
    total_cost = sum(h["amount"] for h in holdings)
    total_value = 0
    sector_dist = {}
    for h in holdings:
        nav, _ = get_fund_nav(h["code"])
        value = (h["amount"] / h["nav"]) * nav
        total_value += value
        sector = h.get("sector", "未知")
        sector_dist[sector] = sector_dist.get(sector, 0) + h["amount"]
    profit = total_value - total_cost
    profit_rate = (profit / total_cost) * 100 if total_cost > 0 else 0
    max_sector = max(sector_dist, key=sector_dist.get) if sector_dist else "未知"
    max_pct = (sector_dist.get(max_sector, 0) / total_cost * 100) if total_cost > 0 else 0
    prompt = f"""持仓诊断：总投入{total_cost:.0f}元，当前市值{total_value:.0f}元，盈亏{profit:.0f}元（{profit_rate:.1f}%）。持仓板块分布：{sector_dist}。最大集中板块：{max_sector}（占比{max_pct:.0f}%）。请给出调仓建议。"""
    result = call_deepseek(prompt) if DEEPSEEK_API_KEY else None
    if result:
        return result
    advice = []
    if profit_rate > 10:
        advice.append("🏆 持仓盈利超过10%，建议止盈部分仓位。")
    elif profit_rate < -5:
        advice.append("⚠️ 持仓亏损超过5%，建议止损或等待反弹。")
    if max_pct > 60:
        advice.append(f"📊 {max_sector}板块占比过高，建议分散至其他板块降低风险。")
    if not advice:
        advice.append("📊 持仓配置合理，建议继续持有并关注市场变化。")
    return "\n".join(advice)

def agent_risk_monitor(holdings):
    if not holdings:
        return []
    alerts = []
    for h in holdings:
        nav, _ = get_fund_nav(h["code"])
        profit_rate = (nav - h["nav"]) / h["nav"] * 100
        if profit_rate >= 15:
            alerts.append(f"🔔 {h['name']} 触发止盈（+{profit_rate:.1f}%），建议卖出。")
        elif profit_rate <= -8:
            alerts.append(f"🔔 {h['name']} 触发止损（{profit_rate:.1f}%），建议离场。")
    return alerts

def personalized_recommendation(user_profile, holdings):
    risk = user_profile.get("risk", "中")
    sectors = get_sector_performance()
    if risk == "低":
        preferred = ["红利", "银行", "消费"]
    elif risk == "高":
        preferred = ["科技", "半导体", "芯片", "人工智能", "新能源车"]
    else:
        preferred = ["均衡", "医药", "沪深300", "消费"]
    strong = [s for s in sectors if s["近1月%"] > 0]
    candidates = [s for s in strong if s["板块"] in preferred]
    if not candidates:
        candidates = sectors[:3]
    fund_map = {
        "科技": [{"name": "前海开源人工智能混合", "code": "001986"}],
        "半导体": [{"name": "诺安成长混合", "code": "320007"}],
        "芯片": [{"name": "银河创新成长混合", "code": "519674"}],
        "人工智能": [{"name": "万家人工智能混合", "code": "006281"}],
        "消费": [{"name": "易方达蓝筹精选混合", "code": "005827"}],
        "医药": [{"name": "中欧医疗健康混合A", "code": "003095"}],
        "均衡": [{"name": "交银阿尔法核心混合", "code": "519712"}],
        "红利": [{"name": "工银瑞信金融地产混合", "code": "000251"}],
        "银行": [{"name": "工银瑞信金融地产混合", "code": "000251"}],
        "沪深300": [{"name": "富国天惠成长混合", "code": "161005"}]
    }
    recs = []
    used = set()
    for s in candidates[:2]:
        sector = s["板块"]
        if sector in fund_map:
            for f in fund_map[sector]:
                if f["code"] not in used:
                    used.add(f["code"])
                    score = min(95, max(60, 75 + s["近1月%"] * 1.2))
                    recs.append({
                        "name": f["name"],
                        "code": f["code"],
                        "sector": sector,
                        "score": round(score, 1),
                        "reason": f"根据您的{risk}风险偏好，推荐{sector}板块的优质基金（近1月+{s['近1月%']:.1f}%）"
                    })
    if len(recs) < 3:
        for f in fund_map.get("均衡", []):
            if f["code"] not in used:
                used.add(f["code"])
                recs.append({
                    "name": f["name"],
                    "code": f["code"],
                    "sector": "均衡",
                    "score": 78,
                    "reason": "均衡配置型基金，适合您的长期稳健目标"
                })
                break
    return recs

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

def calculate_drip(monthly, annual_return, years):
    months = years * 12
    rate = annual_return / 12 / 100
    total = 0
    for _ in range(months):
        total = (total + monthly) * (1 + rate)
    return total

# ==================== 初始化 ====================
if "total_cash" not in st.session_state:
    st.session_state.total_cash = 10000
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_profile = load_user_profile()

# ==================== 侧边栏 ====================
with st.sidebar:
    st.header("⚙️ 个人设置")
    total_cash = st.number_input("总资金（元）", min_value=1000, value=st.session_state.total_cash, step=1000)
    st.session_state.total_cash = total_cash
    
    risk = st.selectbox("风险偏好", ["低", "中", "高"], index=["低","中","高"].index(user_profile.get("risk","中")))
    goal = st.selectbox("投资目标", ["保本", "稳健增值", "追求高收益"], index=["保本","稳健增值","追求高收益"].index(user_profile.get("goal","稳健增值")))
    horizon = st.number_input("投资年限（年）", min_value=1, max_value=30, value=user_profile.get("horizon", 3))
    if st.button("💾 保存个人设置"):
        save_user_profile({"risk": risk, "goal": goal, "horizon": horizon})
        st.success("✅ 设置已保存")
    
    st.divider()
    holdings = load_holdings()
    st.metric("持仓数量", f"{len(holdings)} 只")
    total_cost = sum(h.get("amount", 0) for h in holdings)
    st.metric("已投入", f"{total_cost:.0f} 元")
    st.metric("剩余资金", f"{total_cash - total_cost:.0f} 元")
    
    st.divider()
    st.subheader("📱 微信通知")
    if WEBHOOK_URL:
        st.success("✅ 已配置")
    else:
        st.warning("⚠️ 未配置")
    if st.button("📤 测试通知", use_container_width=True):
        if send_wechat_message("✅ AI投资系统 Pro 测试通知！"):
            st.success("✅ 发送成功")
        else:
            st.error("❌ 发送失败")

# ==================== 主界面 ====================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "💬 AI对话",
    "🎯 智能推荐",
    "📊 板块轮动",
    "📈 持仓监控",
    "🧠 智能诊断",
    "📋 持仓管理",
    "💰 定投计算器"
])

# ==================== Tab1: AI对话 ====================
with tab1:
    st.subheader("💬 AI投资助手")
    st.caption("输入您的问题，AI将为您解答（支持自然语言）")
    
    # 显示历史
    for msg in st.session_state.chat_history[-10:]:
        if msg["role"] == "user":
            st.markdown(f"**你：** {msg['content']}")
        else:
            st.markdown(f"**AI：** {msg['content']}")
    
    # 输入框必须在按钮之前定义
    user_input = st.text_input("请输入您的问题：", placeholder="例如：银行板块哪个基金值得买？", key="user_input_box")
    
    if st.button("发送", use_container_width=True):
        if user_input and user_input.strip():
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            # 检查是否提到具体板块
            sector_names = ["科技", "半导体", "芯片", "人工智能", "新能源车", "光伏", "军工", "消费", "医药", "红利", "证券", "银行", "沪深300", "科创50", "创业板"]
            mentioned_sector = None
            for s in sector_names:
                if s in user_input:
                    mentioned_sector = s
                    break
            
            if mentioned_sector:
                sectors = get_sector_performance()
                sector_data = next((s for s in sectors if s["板块"] == mentioned_sector), None)
                if sector_data:
                    sector_name = sector_data["板块"]
                    ret = sector_data["近1月%"]
                    fund_map = {
                        "科技": [{"name": "前海开源人工智能混合", "code": "001986"}, {"name": "万家人工智能混合", "code": "006281"}],
                        "半导体": [{"name": "诺安成长混合", "code": "320007"}],
                        "芯片": [{"name": "银河创新成长混合", "code": "519674"}],
                        "人工智能": [{"name": "万家人工智能混合", "code": "006281"}],
                        "消费": [{"name": "易方达蓝筹精选混合", "code": "005827"}, {"name": "景顺长城新兴成长混合", "code": "260108"}],
                        "医药": [{"name": "中欧医疗健康混合A", "code": "003095"}],
                        "均衡": [{"name": "交银阿尔法核心混合", "code": "519712"}, {"name": "兴全合润混合", "code": "163406"}],
                        "新能源": [{"name": "农银新能源主题混合", "code": "002190"}],
                        "军工": [{"name": "富国军工主题混合", "code": "005609"}],
                        "红利": [{"name": "工银瑞信金融地产混合", "code": "000251"}],
                        "银行": [{"name": "工银瑞信金融地产混合", "code": "000251"}, {"name": "汇添富价值精选混合", "code": "519069"}],
                        "证券": [{"name": "工银瑞信金融地产混合", "code": "000251"}],
                        "沪深300": [{"name": "富国天惠成长混合", "code": "161005"}],
                    }
                    funds = fund_map.get(sector_name, [])
                    if funds:
                        fund_list = "、".join([f["name"] for f in funds[:2]])
                        answer = f"📊 **{sector_name}板块**近1月涨幅 {ret:.2f}%\n推荐关注：**{fund_list}**\n当前该板块表现{'强势 ✅' if ret > 2 else '平稳 📊' if ret > 0 else '偏弱 ⚠️'}，建议{'积极参与' if ret > 2 else '适量配置' if ret > 0 else '谨慎参与'}。"
                    else:
                        answer = f"📊 **{sector_name}板块**近1月涨幅 {ret:.2f}%，但暂未找到对应的场外基金，建议关注相关ETF。"
                else:
                    answer = f"⚠️ 未找到「{mentioned_sector}」板块的数据，请尝试其他板块。"
            
            elif "板块" in user_input or "什么" in user_input or "推荐" in user_input:
                sectors = get_sector_performance()
                if sectors:
                    best = sectors[0]
                    answer = f"📊 当前近1月最强板块是 **{best['板块']}**（涨幅{best['近1月%']:.2f}%），建议关注该板块的基金。"
                else:
                    answer = "暂无法获取市场数据，请稍后再试。"
            
            elif "持仓" in user_input or "诊断" in user_input:
                holdings = load_holdings()
                answer = agent_portfolio_diagnosis(holdings)
            
            elif "风险" in user_input or "预警" in user_input:
                holdings = load_holdings()
                alerts = agent_risk_monitor(holdings)
                if alerts:
                    answer = "🚨 风险预警：\n" + "\n".join(alerts)
                else:
                    answer = "✅ 当前持仓无高风险信号。"
            
            else:
                if DEEPSEEK_API_KEY:
                    reply = call_deepseek(user_input)
                    answer = reply if reply else "抱歉，AI暂时无法回答，请稍后再试。"
                else:
                    answer = "💡 请配置 DeepSeek API Key 以获得更智能的回答。"
            
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            st.rerun()

# ==================== Tab2: 智能推荐 ====================
with tab2:
    st.subheader("🎯 智能推荐（基于您的个人设置）")
    st.caption(f"当前风险偏好：{risk} | 目标：{goal} | 年限：{horizon}年")
    if st.button("📊 获取个性化推荐", use_container_width=True, type="primary"):
        with st.spinner("正在分析您的偏好和市场..."):
            holdings = load_holdings()
            recs = personalized_recommendation({"risk": risk, "goal": goal, "horizon": horizon}, holdings)
            st.session_state.recommendations = recs
            st.success("✅ 推荐完成")
    if "recommendations" in st.session_state and st.session_state.recommendations:
        for i, rec in enumerate(st.session_state.recommendations):
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                with col1:
                    st.write(f"**{i+1}. {rec['name']}**")
                    st.caption(f"{rec['code']} | 板块：{rec['sector']}")
                with col2:
                    st.metric("AI评分", f"{rec['score']}/100")
                with col3:
                    buy_amount = st.number_input("金额(元)", min_value=100, max_value=10000, value=1000, step=100, key=f"amount_p_{rec['code']}")
                with col4:
                    holdings = load_holdings()
                    already = any(h["code"] == rec["code"] for h in holdings)
                    if already:
                        st.button("✅ 已持有", disabled=True, key=f"held_p_{rec['code']}")
                    else:
                        if st.button("📥 买入", key=f"buy_p_{rec['code']}_{i}"):
                            nav, _ = get_fund_nav(rec["code"])
                            holdings.append({
                                "code": rec["code"],
                                "name": rec["name"],
                                "amount": buy_amount,
                                "buy_date": datetime.now().strftime("%Y-%m-%d"),
                                "nav": nav,
                                "sector": rec["sector"]
                            })
                            if save_holdings(holdings):
                                st.success(f"✅ 买入 {rec['name']} {buy_amount}元，净值 {nav:.4f}")
                                send_wechat_message(f"✅ 买入 {rec['name']}，金额{buy_amount}元")
                                st.rerun()
                            else:
                                st.error("❌ 保存失败")
                st.info(f"💡 {rec['reason']}")
                st.divider()

# ==================== Tab3: 板块轮动 ====================
with tab3:
    st.subheader("📊 板块轮动分析")
    if st.button("🔄 刷新板块数据", use_container_width=True):
        sectors = get_sector_performance()
        df_sectors = pd.DataFrame(sectors)
        st.dataframe(df_sectors, use_container_width=True)
        fig = go.Figure()
        colors = ['green' if x > 0 else 'red' if x < -2 else 'orange' for x in df_sectors["近1月%"]]
        fig.add_trace(go.Bar(x=df_sectors["板块"], y=df_sectors["近1月%"], marker_color=colors))
        fig.update_layout(height=400, title="各板块近1月涨跌幅")
        st.plotly_chart(fig, use_container_width=True)
        best = df_sectors.iloc[0]
        worst = df_sectors.iloc[-1]
        col1, col2 = st.columns(2)
        col1.success(f"📈 最强板块：{best['板块']}（+{best['近1月%']:.2f}%）")
        col2.error(f"📉 最弱板块：{worst['板块']}（{worst['近1月%']:.2f}%）")

# ==================== Tab4: 持仓监控 ====================
with tab4:
    st.subheader("📊 持仓监控")
    holdings = load_holdings()
    if holdings:
        alerts = agent_risk_monitor(holdings)
        if alerts:
            for a in alerts:
                st.warning(a)
        nav_cache = {}
        for h in holdings:
            nav, _ = get_fund_nav(h["code"])
            nav_cache[h["code"]] = nav
        total_profit, total_cost = 0, 0
        for h in holdings:
            code = h["code"]
            buy_price = h.get("nav", 0)
            amount = h.get("amount", 0)
            shares = amount / buy_price if buy_price > 0 else 0
            current_nav = nav_cache.get(code, buy_price)
            profit = (current_nav - buy_price) * shares if buy_price > 0 else 0
            profit_rate = (current_nav - buy_price) / buy_price * 100 if buy_price > 0 else 0
            total_profit += profit
            total_cost += amount
            status, action = check_stop(profit_rate)
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                with col1:
                    st.write(f"**{h['name']}**")
                    st.caption(f"买入价：{buy_price:.4f} | 现价：{current_nav:.4f}")
                    st.caption(f"份额：{shares:.2f}份 | {h.get('sector', '')}")
                with col2:
                    st.metric("盈亏率", f"{'+' if profit_rate > 0 else ''}{profit_rate:.2f}%")
                with col3:
                    st.metric("盈亏金额", f"{'+' if profit > 0 else ''}{profit:.2f}元")
                with col4:
                    st.write(status)
                st.divider()
        st.subheader("📊 持仓汇总")
        col1, col2, col3 = st.columns(3)
        col1.metric("总投入", f"{total_cost:.2f}元")
        col2.metric("总盈亏", f"{'+' if total_profit > 0 else ''}{total_profit:.2f}元")
        col3.metric("总收益率", f"{'+' if total_cost > 0 else ''}{(total_profit/total_cost*100):.2f}%" if total_cost > 0 else "0.00%")
    else:
        st.info("📭 暂无持仓")

# ==================== Tab5: 智能诊断 ====================
with tab5:
    st.subheader("🧠 智能账户诊断")
    if st.button("📊 运行诊断", use_container_width=True, type="primary"):
        holdings = load_holdings()
        if holdings:
            with st.spinner("AI正在分析..."):
                advice = agent_portfolio_diagnosis(holdings)
                st.subheader("📋 诊断结果")
                st.markdown(advice)
                sector_dist = {}
                for h in holdings:
                    sector = h.get("sector", "未知")
                    sector_dist[sector] = sector_dist.get(sector, 0) + h["amount"]
                if sector_dist:
                    st.subheader("📊 持仓板块分布")
                    df_dist = pd.DataFrame({"板块": list(sector_dist.keys()), "金额": list(sector_dist.values())})
                    fig = go.Figure()
                    fig.add_trace(go.Pie(labels=df_dist["板块"], values=df_dist["金额"]))
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ 暂无持仓，请先买入基金")

# ==================== Tab6: 持仓管理 ====================
with tab6:
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

# ==================== Tab7: 定投计算器 ====================
with tab7:
    st.subheader("💰 定投计算器")
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

# ==================== 底部 ====================
st.divider()
st.caption("⚠️ 本系统为学习演示工具，不构成投资建议")
st.caption("📊 数据来源：东方财富(中国财经网) + akshare + 模拟数据")
if GITHUB_TOKEN:
    st.caption("💾 所有数据已永久保存到GitHub，重新部署不丢失")
else:
    st.caption("⚠️ 未配置GitHub存储，数据可能丢失")
if DEEPSEEK_API_KEY:
    st.caption("🧠 AI引擎：DeepSeek 已启用")
else:
    st.caption("🧠 AI引擎：未配置（请设置 DEEPSEEK_API_KEY）")
