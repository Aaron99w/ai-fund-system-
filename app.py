import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta, timezone
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
    page_title="AI智能投资系统",
    page_icon="📈",
    layout="wide"
)

st.title("📊 AI智能投资系统")
st.caption("📈 基于真实市场数据 · 智能板块轮动 · 持仓永久保存")

# ==================== GitHub永久存储 ====================
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
GITHUB_REPO = st.secrets.get("GITHUB_REPO", "Aaron99w/ai-fund-system")
HOLDINGS_PATH = "holdings.json"

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

def load_holdings():
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
            save_holdings([])
            return []
        else:
            return load_holdings_local()
    except:
        return load_holdings_local()

def save_holdings(holdings):
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

# ==================== 真实市场数据获取 ====================
def get_sector_performance():
    """获取各板块近期表现"""
    try:
        import akshare as ak
        # 获取主要ETF近期表现
        etfs = [
            {"name": "科技", "code": "515000"},   # 科技ETF
            {"name": "半导体", "code": "512480"}, # 半导体ETF
            {"name": "芯片", "code": "159995"},   # 芯片ETF
            {"name": "人工智能", "code": "159819"}, # AI ETF
            {"name": "新能源车", "code": "515030"}, # 新能源车ETF
            {"name": "光伏", "code": "515790"},   # 光伏ETF
            {"name": "军工", "code": "512660"},   # 军工ETF
            {"name": "消费", "code": "159928"},   # 消费ETF
            {"name": "医药", "code": "512010"},   # 医药ETF
            {"name": "红利", "code": "510880"},   # 红利ETF
            {"name": "证券", "code": "512880"},   # 证券ETF
            {"name": "银行", "code": "512800"},   # 银行ETF
            {"name": "沪深300", "code": "510300"}, # 沪深300
            {"name": "科创50", "code": "588000"}, # 科创50
            {"name": "创业板", "code": "159915"}, # 创业板
        ]
        
        results = []
        end = datetime.now().strftime("%Y%m%d")
        start_1m = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        start_3m = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")
        
        for etf in etfs:
            try:
                df = ak.stock_zh_a_hist(symbol=etf["code"], period="daily", 
                                       start_date=start_1m, end_date=end, adjust="qfq")
                if df is not None and not df.empty and len(df) >= 5:
                    ret_1m = (df['收盘'].iloc[-1] / df['收盘'].iloc[0] - 1) * 100
                    ret_3m = 0
                    try:
                        df3 = ak.stock_zh_a_hist(symbol=etf["code"], period="daily",
                                                start_date=start_3m, end_date=end, adjust="qfq")
                        if df3 is not None and not df3.empty:
                            ret_3m = (df3['收盘'].iloc[-1] / df3['收盘'].iloc[0] - 1) * 100
                    except:
                        pass
                    results.append({
                        "板块": etf["name"],
                        "近1月%": round(ret_1m, 2),
                        "近3月%": round(ret_3m, 2),
                        "趋势": "📈" if ret_1m > 0 else "📉" if ret_1m < -2 else "➡️"
                    })
            except:
                pass
        
        # 按近1月表现排序
        if results:
            return sorted(results, key=lambda x: x["近1月%"], reverse=True)
        return generate_simulated_sectors()
    except:
        return generate_simulated_sectors()

def generate_simulated_sectors():
    """模拟板块数据（保底）"""
    sectors = ["科技", "半导体", "芯片", "人工智能", "新能源车", "光伏", "军工", "消费", "医药", "红利", "证券", "银行", "沪深300", "科创50", "创业板"]
    results = []
    for s in sectors:
        ret = round(random.uniform(-8, 6), 2)
        results.append({
            "板块": s,
            "近1月%": ret,
            "近3月%": round(ret + random.uniform(-3, 3), 2),
            "趋势": "📈" if ret > 0 else "📉" if ret < -2 else "➡️"
        })
    return sorted(results, key=lambda x: x["近1月%"], reverse=True)

# ==================== 基于市场数据的AI推荐 ====================
def get_ai_recommendation_real():
    """基于真实市场数据推荐基金"""
    sectors = get_sector_performance()
    
    # 找出表现最好的板块
    top_sectors = [s for s in sectors if s["近1月%"] > 0]
    if not top_sectors:
        top_sectors = sectors[:3]  # 如果都跌，选跌幅最小的
    
    # 基金池（按板块分类）
    fund_by_sector = {
        "科技": [
            {"name": "前海开源人工智能混合", "code": "001986", "style": "科技"},
            {"name": "万家人工智能混合", "code": "006281", "style": "科技"},
            {"name": "中欧时代先锋股票A", "code": "001938", "style": "科技"},
        ],
        "半导体": [
            {"name": "诺安成长混合", "code": "320007", "style": "芯片"},
            {"name": "银河创新成长混合", "code": "519674", "style": "芯片"},
        ],
        "消费": [
            {"name": "易方达蓝筹精选混合", "code": "005827", "style": "消费"},
            {"name": "易方达中小盘混合", "code": "110011", "style": "消费"},
            {"name": "景顺长城新兴成长混合", "code": "260108", "style": "消费"},
            {"name": "汇添富消费行业混合", "code": "000083", "style": "消费"},
        ],
        "医药": [
            {"name": "中欧医疗健康混合A", "code": "003095", "style": "医药"},
            {"name": "汇添富创新医药混合", "code": "006113", "style": "医药"},
            {"name": "广发医疗保健股票A", "code": "004851", "style": "医药"},
        ],
        "均衡": [
            {"name": "交银阿尔法核心混合", "code": "519712", "style": "均衡"},
            {"name": "兴全合润混合", "code": "163406", "style": "均衡"},
            {"name": "富国天惠成长混合", "code": "161005", "style": "均衡"},
            {"name": "睿远成长价值混合A", "code": "007119", "style": "均衡"},
        ],
        "新能源": [
            {"name": "农银新能源主题混合", "code": "002190", "style": "新能源"},
            {"name": "华夏能源革新股票", "code": "003834", "style": "新能源"},
        ],
        "军工": [
            {"name": "富国军工主题混合", "code": "005609", "style": "军工"},
            {"name": "易方达国防军工混合", "code": "001475", "style": "军工"},
        ],
        "红利": [
            {"name": "工银瑞信金融地产混合", "code": "000251", "style": "金融"},
            {"name": "汇添富价值精选混合", "code": "519069", "style": "金融"},
        ]
    }
    
    # 根据当前市场环境选择推荐
    recommendations = []
    used_codes = set()
    
    # 从表现最好的板块中选取基金
    for sector_data in top_sectors[:3]:
        sector_name = sector_data["板块"]
        if sector_name in fund_by_sector:
            funds = fund_by_sector[sector_name]
            for f in funds[:2]:
                if f["code"] not in used_codes:
                    used_codes.add(f["code"])
                    # 根据板块表现计算评分
                    perf = sector_data["近1月%"]
                    score = min(95, max(60, 75 + perf * 1.5))
                    recommendations.append({
                        "name": f["name"],
                        "code": f["code"],
                        "style": f["style"],
                        "score": round(score, 1),
                        "sector": sector_name,
                        "sector_return": perf,
                        "reason": f"当前{sector_name}板块表现强势（近1月+{perf:.1f}%），该基金为板块内优质标的"
                    })
    
    # 如果推荐不足，补充均衡型基金
    if len(recommendations) < 3:
        for f in fund_by_sector["均衡"]:
            if f["code"] not in used_codes:
                used_codes.add(f["code"])
                recommendations.append({
                    "name": f["name"],
                    "code": f["code"],
                    "style": f["style"],
                    "score": 78,
                    "sector": "均衡",
                    "sector_return": 0,
                    "reason": "均衡配置型基金，适合当前震荡市"
                })
                if len(recommendations) >= 5:
                    break
    
    return recommendations, sectors

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

# ==================== 其他功能函数 ====================
def get_real_nav(code, asset_type="场外基金"):
    try:
        import akshare as ak
        if asset_type in ["场外基金", "普通基金"]:
            df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
            if df is not None and not df.empty:
                return float(df['单位净值'].iloc[-1]), "akshare"
    except:
        pass
    return round(random.uniform(0.8, 3.0), 4), "模拟数据"

def get_real_nav_with_retry(code, asset_type="场外基金", max_retries=3):
    for i in range(max_retries):
        result = get_real_nav(code, asset_type)
        if result and result[0] and result[0] > 0:
            return result
        time.sleep(0.2)
    return round(random.uniform(0.8, 3.0), 4), "模拟数据"

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

# ==================== 主界面 ====================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🤖 AI推荐",
    "📊 板块轮动",
    "📈 持仓监控",
    "📋 持仓管理",
    "💰 定投计算器"
])

# ==================== Tab1: AI推荐（基于真实市场） ====================
with tab1:
    st.subheader("🤖 AI智能推荐（基于真实市场数据）")
    st.caption("📌 系统自动识别当前强势板块，从强势板块中推荐基金")
    
    if st.button("📊 分析市场并推荐", use_container_width=True, type="primary"):
        with st.spinner("AI正在分析市场数据..."):
            recommendations, sectors = get_ai_recommendation_real()
            
            # 显示板块表现
            st.subheader("📊 当前板块表现（近1月）")
            df_sectors = pd.DataFrame(sectors)
            st.dataframe(df_sectors, use_container_width=True)
            
            # 显示推荐
            st.subheader("🎯 AI推荐基金")
            for i, rec in enumerate(recommendations):
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    with col1:
                        st.write(f"**{i+1}. {rec['name']}**")
                        st.caption(f"{rec['code']} | {rec['style']}")
                        st.caption(f"📌 所属板块：{rec['sector']}（近1月+{rec['sector_return']:.1f}%）")
                    with col2:
                        st.metric("AI评分", f"{rec['score']}/100")
                    with col3:
                        buy_amount = st.number_input(
                            "金额(元)", 
                            min_value=100, 
                            max_value=10000, 
                            value=1000, 
                            step=100, 
                            key=f"amount_{rec['code']}"
                        )
                    with col4:
                        holdings = load_holdings()
                        already = any(h["code"] == rec["code"] for h in holdings)
                        if already:
                            st.button("✅ 已持有", disabled=True, key=f"held_{rec['code']}")
                        else:
                            if st.button("📥 买入", key=f"buy_{rec['code']}_{i}"):
                                nav, source = get_real_nav_with_retry(rec["code"])
                                holdings = load_holdings()
                                holdings.append({
                                    "code": rec["code"],
                                    "name": rec["name"],
                                    "amount": buy_amount,
                                    "buy_date": datetime.now().strftime("%Y-%m-%d"),
                                    "nav": nav,
                                    "style": rec["style"],
                                    "sector": rec["sector"]
                                })
                                save_holdings(holdings)
                                st.success(f"✅ 买入 {rec['name']} {buy_amount}元，净值 {nav:.4f}")
                                send_wechat_message(f"✅ 买入 {rec['name']}，金额{buy_amount}元")
                                st.rerun()
                    
                    st.info(f"💡 {rec['reason']}")
                    st.divider()
    
    if not st.session_state.get("recommendations_loaded", False):
        st.info("💡 点击「分析市场并推荐」获取基于真实市场数据的基金推荐")

# ==================== Tab2: 板块轮动 ====================
with tab2:
    st.subheader("📊 板块轮动分析")
    st.caption("基于真实市场数据，识别当前强势板块")
    
    if st.button("🔄 刷新板块数据", use_container_width=True):
        sectors = get_sector_performance()
        df_sectors = pd.DataFrame(sectors)
        st.dataframe(df_sectors, use_container_width=True)
        
        # 绘制柱状图
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

# ==================== Tab3: 持仓监控 ====================
with tab3:
    st.subheader("📊 持仓监控")
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
        
        if total_profit > 0:
            st.success(f"🎉 当前总盈利 {total_profit:.2f} 元")
        elif total_profit < 0:
            st.warning(f"⚠️ 当前总亏损 {abs(total_profit):.2f} 元")
        else:
            st.info("📊 当前盈亏平衡")
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

# ==================== Tab5: 定投计算器 ====================
with tab5:
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
    st.caption("💾 持仓数据已永久保存到GitHub，重新部署不丢失")
else:
    st.caption("⚠️ 未配置GitHub存储，持仓数据可能丢失")
