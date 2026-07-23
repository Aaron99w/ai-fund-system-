if st.button("发送", use_container_width=True):
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # ---- 意图识别 ----
        # 检查用户是否提到了具体板块
        sector_names = ["科技", "半导体", "芯片", "人工智能", "新能源车", "光伏", "军工", "消费", "医药", "红利", "证券", "银行", "沪深300", "科创50", "创业板"]
        mentioned_sector = None
        for s in sector_names:
            if s in user_input:
                mentioned_sector = s
                break
        
        if mentioned_sector:
            # 用户指定了具体板块
            sectors = get_sector_performance()
            sector_data = next((s for s in sectors if s["板块"] == mentioned_sector), None)
            
            if sector_data:
                sector_name = sector_data["板块"]
                ret = sector_data["近1月%"]
                # 查找该板块对应的基金
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
            # 用户没指定具体板块，推荐最强
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
            # 调用DeepSeek
            if DEEPSEEK_API_KEY:
                reply = call_deepseek(user_input)
                answer = reply if reply else "抱歉，AI暂时无法回答，请稍后再试。"
            else:
                answer = "💡 请配置 DeepSeek API Key 以获得更智能的回答。"
        
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.rerun()
