import akshare as ak
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
import time
import hashlib
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="🚀 AI基金助手 终极版",
    page_icon="📱",
    layout="centered"
)

st.markdown("""
<style>
    .stApp { max-width: 100%; padding: 0 6px; }
    .stButton button { width: 100%; padding: 12px !important; font-size: 15px !important; border-radius: 10px !important; font-weight: bold !important; }
    .stMetric { background: #f8f9fa; padding: 10px; border-radius: 8px; margin: 4px 0; }
</style>
""", unsafe_allow_html=True)

CONFIG = {"webhook_url": "", "push_enabled": False, "deepseek_api_key": "", "deepseek_enabled": False}
DATA_FILE = "fund_records.json"
PORTFOLIO_FILE = "portfolio.json"
REPORT_FILE = "reports.json"

def load_json(filename, default):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default
    return default

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_records():
    return load_json(DATA_FILE, {"records": [], "fund_code": None, "fund_type": "场外"})

def save_records(data):
    save_json(DATA_FILE, data)

OUTSIDE_FUNDS = {
    "001875": {"name": "前海开源沪港深优势精选", "style": "成长", "risk": "中高"},
    "519712": {"name": "交银阿尔法核心混合", "style": "均衡", "risk": "中"},
    "003095": {"name": "中欧医疗健康混合A", "style": "医药", "risk": "中高"},
    "001938": {"name": "中欧时代先锋股票A", "style": "科技", "risk": "高"},
    "005827": {"name": "易方达蓝筹精选混合", "style": "价值", "risk": "中"},
    "110011": {"name": "易方达中小盘混合", "style": "成长", "risk": "中高"},
}

ETF_FUNDS = {
    "513050": {"name": "中概互联ETF", "t0": True, "risk": "高"},
    "513100": {"name": "纳指ETF", "t0": True, "risk": "高"},
    "159920": {"name": "恒生ETF", "t0": True, "risk": "中高"},
    "510300": {"name": "沪深300ETF", "t0": False, "risk": "中"},
    "510500": {"name": "中证500ETF", "t0": False, "risk": "中"},
    "159915": {"name": "创业板ETF", "t0": False, "risk": "高"},
}

data = load_records()
records = data.get("records", [])
current_fund = data.get("fund_code", None)
current_type = data.get("fund_type", "场外")

st.title("🚀 AI基金助手 终极版")
st.caption("📊 对比 · 轮动 · 北向资金 · 季报解读 · 自动报告 · 全部整合")

col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    total_budget = st.number_input("💰 总金额", min_value=100, value=3000, step=500)
with col2:
    each_trade = st.number_input("📈 每次买", min_value=50, value=300, step=50)
with col3:
    max_trades = int(total_budget // each_trade) if each_trade > 0 else 0
    st.metric("可投次数", f"{max_trades}次")

fund_type = st.radio("📌 模式", ["🏦 场外基金", "📊 ETF"], index=0 if current_type == "场外" else 1, horizontal=True)
is_etf = fund_type == "📊 ETF"
f_type = "ETF" if is_etf else "场外"
fund_pool = ETF_FUNDS if is_etf else OUTSIDE_FUNDS

fund_code = st.selectbox(
    "选择基金",
    options=list(fund_pool.keys()),
    format_func=lambda x: f"{fund_pool[x]['name']} ({x})",
    index=list(fund_pool.keys()).index(current_fund) if current_fund in fund_pool else 0
)

if fund_code != current_fund or f_type != current_type:
    data["fund_code"] = fund_code
    data["fund_type"] = f_type
    save_records(data)
    current_fund = fund_code
    current_type = f_type

def get_fund_nav(fund_code):
    try:
        df = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")
        df['净值日期'] = pd.to_datetime(df['净值日期'])
        df = df.sort_values('净值日期')
        return df
    except:
        return None

def get_etf_price(fund_code):
    try:
        df = ak.stock_zh_a_hist(symbol=fund_code, period="daily",
            start_date=(datetime.now()-timedelta(days=90)).strftime("%Y%m%d"),
            end_date=datetime.now().strftime("%Y%m%d"), adjust="qfq")
        df['日期'] = pd.to_datetime(df['日期'])
        df = df.sort_values('日期')
        return df
    except:
        return None

def get_ai_advice(fund_code, f_type):
    try:
        if f_type == "场外":
            df = get_fund_nav(fund_code)
            if df is None or df.empty or len(df) < 30:
                return None
            nav = df['单位净值']
            high_60 = nav.tail(60).max()
            low_60 = nav.tail(60).min()
            position = (nav.iloc[-1] - low_60) / (high_60 - low_60) if high_60 != low_60 else 0.5
            pos_score = (1 - position) * 100
            mom = (nav.iloc[-1] / nav.iloc[-22] - 1) * 100 if len(nav) >= 22 else 0
            mom_score = max(0, min(100, 100 - mom * 3))
            cummax = nav.tail(66).cummax()
            dd = (nav.tail(66) - cummax) / cummax * 100
            max_dd = dd.min()
            dd_score = max(0, min(100, 100 + max_dd * 1.5))
            score = pos_score * 0.40 + mom_score * 0.20 + dd_score * 0.40
            history = df[['净值日期', '净值']].tail(90).to_dict('records')
            if score >= 70 and position < 30:
                signal, action, detail, color = "买入", "buy", "📈 价格处于低位区，定投性价比高", "green"
            elif score >= 55:
                signal, action, detail, color = "观望", "hold", "📊 价格处于中位，建议观望或小额定投", "yellow"
            else:
                signal, action, detail, color = "等待", "wait", "📉 价格处于高位区，等待回调机会", "red"
            return {"type": "场外", "score": round(score, 1), "position": round(position*100, 1), "mom": round(mom, 2),
                    "max_dd": round(max_dd, 2), "nav": nav.iloc[-1], "signal": signal, "action": action,
                    "detail": detail, "color": color, "history": history}
        else:
            df = get_etf_price(fund_code)
            if df is None or df.empty:
                return None
            close = df['收盘']
            latest = close.iloc[-1]
            ma5 = close.rolling(5).mean().iloc[-1]
            ma20 = close.rolling(20).mean().iloc[-1]
            ma60 = close.rolling(60).mean().iloc[-1]
            high_60 = close.tail(60).max()
            low_60 = close.tail(60).min()
            position = (latest - low_60) / (high_60 - low_60) if high_60 != low_60 else 0.5
            pos_score = (1 - position) * 100
            mom = (latest / close.iloc[-22] - 1) * 100 if len(close) >= 22 else 0
            mom_score = max(0, min(100, 100 - mom * 3))
            score = pos_score * 0.50 + mom_score * 0.50
            history = df[['日期', '收盘']].tail(90).rename(columns={'日期': '净值日期', '收盘': '净值'}).to_dict('records')
            if score >= 70 and position < 30:
                signal, action, detail, color = "买入信号", "buy", "📈 价格低位，可日内买入或加仓", "green"
            elif score >= 55:
                signal, action, detail, color = "持有/观望", "hold", "📊 价格适中，可持有或观望", "yellow"
            else:
                signal, action, detail, color = "卖出/减仓", "sell", "📉 价格偏高，可考虑减仓或T+0卖出", "red"
            t0 = ETF_FUNDS.get(fund_code, {}).get('t0', False)
            return {"type": "ETF", "score": round(score, 1), "position": round(position*100, 1), "mom": round(mom, 2),
                    "price": round(latest, 3), "ma5": round(ma5, 3), "ma20": round(ma20, 3), "ma60": round(ma60, 3),
                    "signal": signal, "action": action, "detail": detail, "color": color, "t0": t0, "history": history}
    except:
        return None

def calc_position(records, fund_code, f_type):
    if not records:
        return None
    try:
        total_cost = sum(r['amount'] for r in records)
        total_shares = sum(r['amount'] / r['nav'] for r in records)
        if f_type == "场外":
            df = get_fund_nav(fund_code)
            if df is None:
                return None
            latest_price = df['单位净值'].iloc[-1]
        else:
            df = get_etf_price(fund_code)
            if df is None or df.empty:
                return None
            latest_price = df['收盘'].iloc[-1]
        current_value = total_shares * latest_price
        profit = current_value - total_cost
        rate = (profit / total_cost) * 100 if total_cost > 0 else 0
        return {"总成本": round(total_cost, 2), "当前市值": round(current_value, 2), "盈亏": round(profit, 2),
                "收益率%": round(rate, 2), "笔数": len(records), "最新价": round(latest_price, 4)}
    except:
        return None

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 核心交易",
    "📈 基金对比",
    "🏭 行业轮动",
    "💰 北向资金",
    "📄 自动报告",
    "📋 季报解读"
])

with tab1:
    with st.expander("📰 AI市场分析", expanded=True):
        if st.button("📊 分析当前市场", use_container_width=True, type="primary"):
            with st.spinner("分析中..."):
                all_news = []
                try:
                    df = ak.js_news().head(10)
                    for _, row in df.iterrows():
                        all_news.append(row.get('标题', row.get('content', '')))
                except: pass
                try:
                    df = ak.stock_news_em(symbol="头条").head(8)
                    for _, row in df.iterrows():
                        all_news.append(row.get('新闻标题', ''))
                except: pass
                if all_news:
                    st.success(f"✅ 获取 {len(all_news)} 条新闻")
                    pos_words = ['上涨','大涨','利好','反弹','突破','新高','增长','乐观']
                    neg_words = ['下跌','大跌','利空','回调','破位','新低','亏损','悲观']
                    pos_cnt = sum(1 for n in all_news if any(w in n for w in pos_words))
                    neg_cnt = sum(1 for n in all_news if any(w in n for w in neg_words))
                    col1, col2, col3 = st.columns(3)
                    col1.metric("📰 新闻总数", len(all_news))
                    col2.metric("🟢 正面", pos_cnt)
                    col3.metric("🔴 负面", neg_cnt)
                    if pos_cnt > neg_cnt * 1.5:
                        st.success("💡 市场情绪偏乐观，可积极参与")
                    elif neg_cnt > pos_cnt * 1.5:
                        st.warning("💡 市场情绪偏悲观，注意风险")
                    else:
                        st.info("💡 市场情绪中性，按原计划操作")
                else:
                    st.error("获取新闻失败")

    with st.expander("🧠 AI决策", expanded=True):
        fund_records = [r for r in records if r.get('fund_code') == fund_code]
        times_done = len(fund_records)
        col1, col2, col3 = st.columns(3)
        col1.metric("已投", f"{times_done}/{max_trades}次")
        col2.metric("剩余", f"{(max_trades-times_done)*each_trade}元")
        col3.metric("进度", f"{times_done/max_trades*100:.0f}%" if max_trades > 0 else "0%")
        
        if st.button("⚡ 运行AI分析", use_container_width=True, type="primary"):
            advice = get_ai_advice(fund_code, f_type)
            if advice:
                cols = st.columns(4 if is_etf else 3)
                cols[0].metric("AI评分", f"{advice['score']}/100")
                cols[1].metric("位置", f"{advice['position']}%")
                cols[2].metric("近1月", f"{advice['mom']}%")
                if is_etf:
                    cols[3].metric("现价", f"{advice.get('price', 0)}")
                if advice['color'] == "green":
                    st.success(f"📈 {advice['signal']}: {advice['detail']}")
                    if times_done < max_trades and st.button(f"💰 确认买入 {each_trade}元", use_container_width=True):
                        try:
                            if is_etf:
                                df = get_etf_price(fund_code)
                                price = df['收盘'].iloc[-1] if df is not None and not df.empty else 0
                            else:
                                df = get_fund_nav(fund_code)
                                price = df['单位净值'].iloc[-1] if df is not None else 0
                            records.append({"fund_code": fund_code, "date": datetime.now().strftime("%Y-%m-%d"),
                                           "nav": float(price), "amount": float(each_trade)})
                            data["records"] = records
                            save_records(data)
                            st.success(f"✅ 已记录！净值 {price:.4f}")
                            st.rerun()
                        except:
                            st.error("记录失败")
                elif advice['color'] == "red":
                    st.warning(f"📉 {advice['signal']}: {advice['detail']}")
                else:
                    st.info(f"📊 {advice['signal']}: {advice['detail']}")
                if advice.get('history'):
                    hist_df = pd.DataFrame(advice['history'])
                    st.line_chart(hist_df.set_index('净值日期')['净值'])

    with st.expander("📊 我的持仓", expanded=False):
        pos = calc_position(records, fund_code, f_type)
        if pos:
            col1, col2, col3 = st.columns(3)
            col1.metric("总投入", f"{pos['总成本']}元")
            col2.metric("当前市值", f"{pos['当前市值']}元")
            col3.metric("盈亏", f"{pos['盈亏']}元", delta=f"{pos['收益率%']}%")
        else:
            st.info("暂无持仓")
    
    if records:
        with st.expander("📋 交易记录", expanded=False):
            for r in records[-10:]:
                st.write(f"📅 {r['date']} | {r['amount']}元 | 净值 {r['nav']:.4f}")

with tab2:
    st.subheader("📊 基金对比")
    st.caption("选择2-4只基金，对比收益率、回撤、夏普等指标")
    all_funds = {**OUTSIDE_FUNDS, **ETF_FUNDS}
    compare_codes = st.multiselect(
        "选择要对比的基金（2-4只）",
        options=list(all_funds.keys()),
        format_func=lambda x: f"{all_funds[x]['name']} ({x})",
        default=list(all_funds.keys())[:3]
    )
    if len(compare_codes) >= 2:
        if st.button("📊 开始对比", use_container_width=True):
            with st.spinner("获取数据中..."):
                compare_results = []
                for code in compare_codes:
                    try:
                        if code in ETF_FUNDS:
                            df = get_etf_price(code)
                            if df is not None and not df.empty:
                                close = df['收盘']
                                ret_1m = (close.iloc[-1] / close.iloc[-22] - 1) * 100 if len(close) >= 22 else 0
                                ret_3m = (close.iloc[-1] / close.iloc[-66] - 1) * 100 if len(close) >= 66 else 0
                                vol = close.pct_change().std() * np.sqrt(252) * 100
                                compare_results.append({
                                    "名称": all_funds[code]['name'],
                                    "近1月%": round(ret_1m, 2),
                                    "近3月%": round(ret_3m, 2),
                                    "波动率%": round(vol, 2),
                                    "类型": "ETF"
                                })
                        else:
                            df = get_fund_nav(code)
                            if df is not None and not df.empty:
                                nav = df['单位净值']
                                ret_1m = (nav.iloc[-1] / nav.iloc[-22] - 1) * 100 if len(nav) >= 22 else 0
                                ret_3m = (nav.iloc[-1] / nav.iloc[-66] - 1) * 100 if len(nav) >= 66 else 0
                                vol = nav.pct_change().std() * np.sqrt(252) * 100
                                compare_results.append({
                                    "名称": all_funds[code]['name'],
                                    "近1月%": round(ret_1m, 2),
                                    "近3月%": round(ret_3m, 2),
                                    "波动率%": round(vol, 2),
                                    "类型": "场外"
                                })
                    except:
                        continue
                if compare_results:
                    df_compare = pd.DataFrame(compare_results)
                    st.dataframe(df_compare, use_container_width=True)
                    st.subheader("📊 近3月收益对比")
                    fig = go.Figure()
                    fig.add_trace(go.Bar(x=df_compare['名称'], y=df_compare['近3月%'], name='近3月收益%',
                                        marker_color=['green' if x > 0 else 'red' for x in df_compare['近3月%']]))
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("对比数据获取失败")
    else:
        st.info("请选择至少2只基金进行对比")

with tab3:
    st.subheader("🏭 行业轮动分析")
    st.caption("分析当前哪些行业板块最强势")
    if st.button("📊 分析行业轮动", use_container_width=True, type="primary"):
        with st.spinner("分析中..."):
            try:
                sectors = [
                    {"code": "000001", "name": "上证指数"},
                    {"code": "399001", "name": "深证成指"},
                    {"code": "399006", "name": "创业板指"},
                    {"code": "000300", "name": "沪深300"},
                    {"code": "000905", "name": "中证500"},
                ]
                results = []
                for s in sectors:
                    try:
                        df = ak.stock_zh_index_hist(symbol=s['code'], period="daily",
                            start_date=(datetime.now()-timedelta(days=30)).strftime("%Y%m%d"),
                            end_date=datetime.now().strftime("%Y%m%d"))
                        if not df.empty:
                            ret = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100
                            results.append({"指数": s['name'], "近1月涨跌幅%": round(ret, 2)})
                    except:
                        continue
                if results:
                    df_sectors = pd.DataFrame(results).sort_values("近1月涨跌幅%", ascending=False)
                    st.dataframe(df_sectors, use_container_width=True)
                    fig = go.Figure()
                    colors = ['green' if x > 0 else 'red' for x in df_sectors['近1月涨跌幅%']]
                    fig.add_trace(go.Bar(x=df_sectors['指数'], y=df_sectors['近1月涨跌幅%'],
                                        marker_color=colors, name='涨跌幅%'))
                    fig.update_layout(height=300, title="各指数近1月表现")
                    st.plotly_chart(fig, use_container_width=True)
                    best = df_sectors.iloc[0]
                    worst = df_sectors.iloc[-1]
                    col1, col2 = st.columns(2)
                    col1.success(f"📈 最强：{best['指数']} (+{best['近1月涨跌幅%']}%)")
                    col2.error(f"📉 最弱：{worst['指数']} ({worst['近1月涨跌幅%']}%)")
                    st.info(f"💡 建议：关注强势板块{best['指数']}相关的基金，回避{worst['指数']}相关基金")
                else:
                    st.error("获取行业数据失败")
            except Exception as e:
                st.error(f"分析失败：{e}")

with tab4:
    st.subheader("💰 北向资金监控")
    st.caption("跟踪外资（北向资金）流入流出情况")
    if st.button("📊 查询北向资金", use_container_width=True, type="primary"):
        with st.spinner("获取数据中..."):
            try:
                df = ak.stock_hsgt_north_net_flow_in_em(symbol="北向资金")
                if df is not None and not df.empty:
                    df_10 = df.tail(10)
                    st.subheader("📊 近10日北向资金流向")
                    st.dataframe(df_10, use_container_width=True)
                    fig = make_subplots(rows=2, cols=1, subplot_titles=("每日净流入", "累计净流入"))
                    fig.add_trace(go.Bar(x=df_10['日期'], y=df_10['净流入'], name='净流入'), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df_10['日期'], y=df_10['累计净流入'].cumsum(), name='累计'), row=2, col=1)
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                    total_in = df_10['净流入'].sum()
                    col1, col2 = st.columns(2)
                    col1.metric("近10日累计净流入", f"{total_in:.2f}亿元", delta="流入" if total_in > 0 else "流出")
                    pos_days = len(df_10[df_10['净流入'] > 0])
                    col2.metric("流入天数", f"{pos_days}/10天")
                    if total_in > 50 and pos_days > 6:
                        st.success("💡 北向资金持续流入，外资看好A股，建议积极参与")
                    elif total_in < -50 and pos_days < 4:
                        st.warning("💡 北向资金持续流出，外资谨慎，注意风险")
                    else:
                        st.info("💡 北向资金进出平衡，市场中性")
                else:
                    st.error("获取北向资金数据失败")
            except Exception as e:
                st.error(f"查询失败：{e}")

with tab5:
    st.subheader("📄 自动投资报告")
    st.caption("每周/每月自动生成投资报告，追踪持仓表现")
    report_type = st.radio("报告周期", ["周报", "月报"], horizontal=True)
    if st.button("📊 生成报告", use_container_width=True, type="primary"):
        with st.spinner("生成报告中..."):
            pos = calc_position(records, fund_code, f_type)
            advice = get_ai_advice(fund_code, f_type)
            report = f"""
📋 AI基金投资报告
{'='*40}
📅 报告日期：{datetime.now().strftime('%Y-%m-%d %H:%M')}
📊 报告周期：{report_type}
{'='*40}

【一、持仓概况】
📌 当前基金：{fund_pool[fund_code]['name']}
💰 总投入：{pos['总成本'] if pos else 0}元
📈 当前市值：{pos['当前市值'] if pos else 0}元
💵 盈亏：{pos['盈亏'] if pos else 0}元（{pos['收益率%'] if pos else 0}%）
📊 交易笔数：{pos['笔数'] if pos else 0}笔

【二、AI分析结论】
🎯 AI评分：{advice['score'] if advice else 'N/A'}/100
📍 当前位置：{advice['position'] if advice else 'N/A'}%
📈 近1月涨跌：{advice['mom'] if advice else 'N/A'}%
💡 操作建议：{advice['signal'] if advice else 'N/A'}

【三、市场环境】
📰 市场情绪：正常
💰 北向资金：建议查看北向资金页面
🏭 行业轮动：建议查看行业轮动页面

【四、下周操作计划】
{'='*40}
📌 建议：{advice['detail'] if advice else '正常定投'}
⚠️ 风险提示：投资有风险，仅供参考
"""
            st.success("✅ 报告生成完成！")
            st.text_area("📋 报告内容", report, height=400)
            reports = load_json(REPORT_FILE, [])
            reports.append({"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "content": report})
            save_json(REPORT_FILE, reports[-10:])
            st.download_button(
                label="📥 下载报告",
                data=report,
                file_name=f"基金报告_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True
            )
    reports = load_json(REPORT_FILE, [])
    if reports:
        with st.expander("📂 历史报告", expanded=False):
            for r in reports[-5:]:
                st.write(f"📅 {r['date']}")
                st.caption(r['content'][:100] + "...")

with tab6:
    st.subheader("📋 基金季报解读")
    st.caption("AI自动解读基金季报重点内容")
    if st.button("📊 解读季报", use_container_width=True, type="primary"):
        with st.spinner("分析中..."):
            try:
                fund_info = ak.fund_em_fund_info()
                info = fund_info[fund_info['基金代码'] == fund_code]
                if not info.empty:
                    fund_name = info['基金简称'].values[0]
                    fund_type_str = info['基金类型'].values[0] if '基金类型' in info.columns else '未知'
                    fund_scale = info['基金规模'].values[0] if '基金规模' in info.columns else '未知'
                    perf = get_fund_nav(fund_code)
                    if perf is not None and not perf.empty:
                        nav = perf['单位净值']
                        ret_1m = (nav.iloc[-1] / nav.iloc[-22] - 1) * 100 if len(nav) >= 22 else 0
                        ret_3m = (nav.iloc[-1] / nav.iloc[-66] - 1) * 100 if len(nav) >= 66 else 0
                        ret_6m = (nav.iloc[-1] / nav.iloc[-132] - 1) * 100 if len(nav) >= 132 else 0
                        report = f"""
📋 基金季报解读报告
{'='*40}
📌 基金名称：{fund_name}
📊 基金代码：{fund_code}
📂 基金类型：{fund_type_str}
💰 基金规模：{fund_scale}亿元
{'='*40}

【一、业绩表现】
📈 近1月：{ret_1m:.2f}%
📈 近3月：{ret_3m:.2f}%
📈 近6月：{ret_6m:.2f}%

【二、业绩评价】
{'✅ 近3月收益为正，表现良好' if ret_3m > 0 else '⚠️ 近3月收益为负，需关注'}
{'✅ 近6月收益为正，中长期表现稳定' if ret_6m > 0 else '⚠️ 近6月收益为负，需谨慎'}
{'📊 基金规模适中，流动性良好' if fund_scale != '未知' else ''}

【三、投资建议】
{'📈 建议：该基金近期表现良好，可继续持有或定投' if ret_3m > 0 and ret_6m > 0 else 
 '📊 建议：该基金近期有波动，建议观望或小额定投' if ret_3m < 0 and ret_6m > 0 else
 '⚠️ 建议：该基金近期表现不佳，建议谨慎操作'}

【四、风险提示】
⚠️ 以上分析基于公开数据，仅供参考
📌 建议结合AI择时系统进行买卖决策
"""
                        st.success("✅ 季报解读完成！")
                        st.text_area("📋 解读报告", report, height=350)
                    else:
                        st.error("获取基金业绩数据失败")
                else:
                    st.error("获取基金信息失败")
            except Exception as e:
                st.error(f"解读失败：{e}")

st.divider()
st.caption("⚠️ 投资有风险，仅供参考")
st.caption("🚀 AI基金助手 终极版 | 6大Tab完整整合")
