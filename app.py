# ==================== Tab6: 市场情绪（带刷新功能） ====================
with tab6:
    st.subheader("📈 市场情绪分析")
    st.caption("基于实时市场数据 + 新闻情绪综合判断")
    
    # 刷新按钮
    col_refresh, col_info = st.columns([1, 3])
    with col_refresh:
        if st.button("🔄 刷新数据", use_container_width=True):
            st.rerun()
    with col_info:
        st.caption(f"⏱️ 最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ===== 获取数据 =====
    market_data = get_market_data()
    hot_sectors = get_hot_sectors()
    news_sentiment = get_news_sentiment()
    market_info = get_market_info()
    
    # ===== 分析 =====
    index_changes = [v["change"] for v in market_data.values()]
    avg_change = sum(index_changes) / len(index_changes) if index_changes else 0
    
    news_score = 0
    if news_sentiment["sentiment"] == "乐观":
        news_score = 1
    elif news_sentiment["sentiment"] == "悲观":
        news_score = -1
    
    if avg_change > 0.5 and news_score >= 0:
        final_sentiment = "乐观 😊"
        sentiment_desc = "市场整体上涨，新闻情绪偏积极"
        advice = "💡 市场情绪乐观，可适当增加仓位"
    elif avg_change > 0 and news_score >= 0:
        final_sentiment = "中性偏乐观 🚀"
        sentiment_desc = "市场小幅上涨，情绪平稳"
        advice = "💡 市场情绪平稳，保持现有配置"
    elif avg_change < -0.5 and news_score <= 0:
        final_sentiment = "悲观 😰"
        sentiment_desc = "市场整体下跌，新闻情绪偏消极"
        advice = "💡 市场情绪悲观，建议控制仓位"
    else:
        final_sentiment = "中性 😐"
        sentiment_desc = "市场震荡整理，方向不明"
        advice = "💡 市场情绪中性，保持观望"
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 综合情绪", final_sentiment)
    with col2:
        st.metric("📈 平均涨跌幅", f"{'+' if avg_change > 0 else ''}{avg_change:.2f}%")
    with col3:
        st.metric("🕐 更新时间", datetime.now().strftime("%H:%M:%S"))
    
    st.caption(f"📌 {sentiment_desc}")
    
    # ===== 各大指数 =====
    st.subheader("📊 各大指数表现")
    index_cols = st.columns(5)
    for i, (name, data) in enumerate(market_data.items()):
        with index_cols[i]:
            change = data["change"]
            delta = f"{'+' if change > 0 else ''}{change:.2f}%"
            st.metric(name, f"{data['price']:.2f}", delta=delta)
    
    # ===== 热门板块 =====
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
    
    # ===== 信息 =====
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
    
    # ===== 新闻 =====
    with st.expander("📰 最新财经新闻", expanded=False):
        if news_sentiment and news_sentiment.get("headlines"):
            for h in news_sentiment["headlines"]:
                st.write(f"• {h}")
        else:
            st.write("暂无新闻")
    
    # ===== 建议 =====
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
