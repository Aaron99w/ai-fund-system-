if "板块" in user_input or "什么" in user_input or "推荐" in user_input:
    sectors = get_sector_performance()
    if not sectors:
        answer = "暂无法获取市场数据，请稍后再试。"
    else:
        # 1. 解析用户提到的具体板块
        sector_names = ["科技", "半导体", "芯片", "人工智能", "新能源车", "光伏", "军工", "消费", "医药", "红利", "证券", "银行", "沪深300", "科创50", "创业板"]
        mentioned_sector = None
        for s in sector_names:
            if s in user_input:
                mentioned_sector = s
                break
        
        # 2. 查找该板块的表现
        sector_data = next((s for s in sectors if s["板块"] == mentioned_sector), None) if mentioned_sector else None
        
        if sector_data:
            # 用户指定了具体板块
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
                fund_names = "、".join([f["name"] for f in funds[:2]])
                answer = f"📊 **{sector_name}板块**近1月涨幅 {ret:.2f}%。\n推荐关注：{fund_names}。\n当前该板块表现{'强势' if ret > 0 else '偏弱'}，建议{'积极参与' if ret > 0 else '谨慎参与'}。"
            else:
                answer = f"📊 **{sector_name}板块**近1月涨幅 {ret:.2f}%，但暂未找到该板块的场外基金，建议关注相关ETF或均衡型基金。"
        else:
            # 用户没指定具体板块，推荐最强板块
            best = sectors[0]
            answer = f"📊 当前近1月最强板块是 **{best['板块']}**（涨幅{best['近1月%']:.2f}%）。建议关注该板块的基金。"
