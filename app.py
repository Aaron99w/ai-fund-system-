import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import random
import re
import json
import requests
from collections import Counter
import math

# ==================== 页面设置 ====================
st.set_page_config(
    page_title="🤖 AI基金投顾 终极版",
    page_icon="📊",
    layout="wide"
)

st.title("🤖 AI基金投顾 终极版")
st.caption("📊 200+基金 · 多因子评分 · 新闻分析 · 历史回测 · 微信通知 · 投资决策")

# ==================== 微信通知配置 ====================
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的key"

def send_wechat_message(content):
    if not WEBHOOK_URL or "你的key" in WEBHOOK_URL:
        return False, "⚠️ 请先配置 Webhook 地址"
    try:
        data = {"msgtype": "text", "text": {"content": content[:2000]}}
        response = requests.post(WEBHOOK_URL, json=data, timeout=5)
        if response.status_code == 200:
            return True, "✅ 微信通知已发送"
        else:
            return False, f"❌ 发送失败：{response.status_code}"
    except Exception as e:
        return False, f"❌ 发送失败：{str(e)}"

# ==================== 202只基金完整库 ====================
FUNDS = [
    # ==================== 一、科技/成长（45只） ====================
    {"name": "前海开源人工智能混合", "code": "001986", "style": "科技", "nav": 2.85, "risk": "高", "return_1y": "+18.5%", "return_3y": "+42.5%", "max_dd": "-25.3%", "sharpe": 0.85},
    {"name": "万家人工智能混合", "code": "006281", "style": "科技", "nav": 1.92, "risk": "高", "return_1y": "+15.2%", "return_3y": "+38.2%", "max_dd": "-28.1%", "sharpe": 0.78},
    {"name": "工银瑞信信息产业混合", "code": "000263", "style": "科技", "nav": 3.45, "risk": "高", "return_1y": "+20.3%", "return_3y": "+45.7%", "max_dd": "-22.6%", "sharpe": 0.92},
    {"name": "中欧时代先锋股票A", "code": "001938", "style": "科技", "nav": 1.87, "risk": "高", "return_1y": "+22.8%", "return_3y": "+51.3%", "max_dd": "-26.7%", "sharpe": 0.95},
    {"name": "信达澳银新能源产业股票", "code": "001410", "style": "科技", "nav": 4.21, "risk": "高", "return_1y": "+25.6%", "return_3y": "+58.6%", "max_dd": "-30.2%", "sharpe": 0.88},
    {"name": "嘉实智能汽车股票", "code": "002168", "style": "科技", "nav": 2.56, "risk": "高", "return_1y": "+12.8%", "return_3y": "+35.4%", "max_dd": "-32.5%", "sharpe": 0.72},
    {"name": "汇添富科技创新混合", "code": "007355", "style": "科技", "nav": 1.78, "risk": "高", "return_1y": "+14.6%", "return_3y": "+32.1%", "max_dd": "-24.8%", "sharpe": 0.76},
    {"name": "华安智能生活混合", "code": "001071", "style": "科技", "nav": 2.34, "risk": "高", "return_1y": "+16.2%", "return_3y": "+40.8%", "max_dd": "-23.4%", "sharpe": 0.82},
    {"name": "广发科技先锋混合", "code": "008903", "style": "科技", "nav": 1.56, "risk": "高", "return_1y": "+10.5%", "return_3y": "+28.9%", "max_dd": "-29.6%", "sharpe": 0.68},
    {"name": "南方科技创新混合", "code": "007340", "style": "科技", "nav": 2.12, "risk": "高", "return_1y": "+13.8%", "return_3y": "+36.7%", "max_dd": "-26.3%", "sharpe": 0.74},
    {"name": "汇添富智能制造股票", "code": "005802", "style": "科技", "nav": 2.34, "risk": "高", "return_1y": "+12.5%", "return_3y": "+31.2%", "max_dd": "-25.1%", "sharpe": 0.72},
    {"name": "嘉实先进制造股票", "code": "001039", "style": "科技", "nav": 1.87, "risk": "高", "return_1y": "+11.8%", "return_3y": "+29.8%", "max_dd": "-27.6%", "sharpe": 0.68},
    {"name": "富国高端制造行业股票", "code": "000513", "style": "科技", "nav": 2.56, "risk": "高", "return_1y": "+13.2%", "return_3y": "+33.5%", "max_dd": "-24.3%", "sharpe": 0.74},
    {"name": "汇添富移动互联股票", "code": "000697", "style": "科技", "nav": 1.45, "risk": "高", "return_1y": "+9.8%", "return_3y": "+25.6%", "max_dd": "-30.8%", "sharpe": 0.62},
    {"name": "中邮信息产业灵活配置", "code": "001227", "style": "科技", "nav": 1.23, "risk": "高", "return_1y": "+8.6%", "return_3y": "+22.3%", "max_dd": "-32.4%", "sharpe": 0.58},
    {"name": "长盛电子信息产业混合", "code": "080012", "style": "科技", "nav": 2.87, "risk": "高", "return_1y": "+15.6%", "return_3y": "+38.9%", "max_dd": "-26.7%", "sharpe": 0.80},
    {"name": "华商计算机行业股票", "code": "007853", "style": "科技", "nav": 1.34, "risk": "高", "return_1y": "+9.2%", "return_3y": "+26.7%", "max_dd": "-28.9%", "sharpe": 0.64},
    {"name": "融通互联网传媒灵活配置", "code": "001150", "style": "科技", "nav": 1.56, "risk": "高", "return_1y": "+8.8%", "return_3y": "+24.5%", "max_dd": "-31.2%", "sharpe": 0.60},
    {"name": "前海开源工业革命4.0", "code": "001103", "style": "科技", "nav": 1.89, "risk": "高", "return_1y": "+10.5%", "return_3y": "+30.2%", "max_dd": "-27.8%", "sharpe": 0.66},
    {"name": "农银工业4.0灵活配置", "code": "001606", "style": "科技", "nav": 2.45, "risk": "高", "return_1y": "+12.8%", "return_3y": "+34.8%", "max_dd": "-25.6%", "sharpe": 0.72},
    {"name": "华夏中证人工智能ETF联接", "code": "008585", "style": "科技", "nav": 1.34, "risk": "高", "return_1y": "+14.2%", "return_3y": "+34.6%", "max_dd": "-26.5%", "sharpe": 0.70},
    {"name": "富国中证科技50ETF联接", "code": "008749", "style": "科技", "nav": 1.45, "risk": "高", "return_1y": "+13.6%", "return_3y": "+32.8%", "max_dd": "-27.2%", "sharpe": 0.68},
    {"name": "华宝科技ETF联接A", "code": "007873", "style": "科技", "nav": 1.56, "risk": "高", "return_1y": "+12.4%", "return_3y": "+30.5%", "max_dd": "-28.6%", "sharpe": 0.66},
    {"name": "天弘中证电子ETF联接", "code": "001617", "style": "科技", "nav": 1.45, "risk": "高", "return_1y": "+11.2%", "return_3y": "+28.4%", "max_dd": "-27.5%", "sharpe": 0.64},
    {"name": "南方中证500信息技术ETF联接", "code": "002900", "style": "科技", "nav": 1.34, "risk": "高", "return_1y": "+10.8%", "return_3y": "+26.8%", "max_dd": "-28.9%", "sharpe": 0.62},
    {"name": "广发中证全指信息技术ETF联接", "code": "000942", "style": "科技", "nav": 1.56, "risk": "高", "return_1y": "+9.6%", "return_3y": "+24.5%", "max_dd": "-30.2%", "sharpe": 0.58},
    {"name": "易方达中证科技50ETF联接", "code": "012717", "style": "科技", "nav": 1.23, "risk": "高", "return_1y": "+11.5%", "return_3y": "+27.6%", "max_dd": "-26.8%", "sharpe": 0.62},
    {"name": "博时中证人工智能ETF联接", "code": "017742", "style": "科技", "nav": 1.02, "risk": "高", "return_1y": "+7.8%", "return_3y": "+18.6%", "max_dd": "-33.8%", "sharpe": 0.50},
    {"name": "华夏中证机器人ETF联接", "code": "018344", "style": "科技", "nav": 1.05, "risk": "高", "return_1y": "+8.5%", "return_3y": "+20.8%", "max_dd": "-32.4%", "sharpe": 0.54},
    {"name": "华富中证人工智能ETF联接", "code": "008020", "style": "科技", "nav": 1.12, "risk": "高", "return_1y": "+9.2%", "return_3y": "+22.6%", "max_dd": "-30.8%", "sharpe": 0.56},
    {"name": "平安中证人工智能ETF联接", "code": "009051", "style": "科技", "nav": 1.08, "risk": "高", "return_1y": "+8.8%", "return_3y": "+21.8%", "max_dd": "-31.6%", "sharpe": 0.54},
    {"name": "西部利得人工智能ETF联接", "code": "011832", "style": "科技", "nav": 1.06, "risk": "高", "return_1y": "+8.2%", "return_3y": "+20.2%", "max_dd": "-32.8%", "sharpe": 0.52},
    {"name": "国泰中证计算机ETF联接", "code": "010210", "style": "科技", "nav": 1.15, "risk": "高", "return_1y": "+9.6%", "return_3y": "+24.2%", "max_dd": "-29.6%", "sharpe": 0.58},
    {"name": "南方中证计算机ETF联接", "code": "010001", "style": "科技", "nav": 1.18, "risk": "高", "return_1y": "+10.2%", "return_3y": "+25.6%", "max_dd": "-28.8%", "sharpe": 0.60},
    {"name": "富国中证大数据ETF联接", "code": "014041", "style": "科技", "nav": 1.03, "risk": "高", "return_1y": "+7.6%", "return_3y": "+19.2%", "max_dd": "-34.2%", "sharpe": 0.48},
    {"name": "华夏中证云计算ETF联接", "code": "012445", "style": "科技", "nav": 1.04, "risk": "高", "return_1y": "+8.0%", "return_3y": "+19.8%", "max_dd": "-33.6%", "sharpe": 0.50},
    {"name": "天弘中证计算机ETF联接", "code": "001630", "style": "科技", "nav": 1.42, "risk": "高", "return_1y": "+10.8%", "return_3y": "+26.2%", "max_dd": "-28.4%", "sharpe": 0.62},
    {"name": "易方达中证人工智能ETF联接", "code": "012262", "style": "科技", "nav": 1.08, "risk": "高", "return_1y": "+8.6%", "return_3y": "+21.2%", "max_dd": "-30.6%", "sharpe": 0.54},
    {"name": "嘉实中证软件服务ETF联接", "code": "012426", "style": "科技", "nav": 1.06, "risk": "高", "return_1y": "+8.4%", "return_3y": "+20.6%", "max_dd": "-31.8%", "sharpe": 0.52},
    {"name": "工银瑞信中证科技龙头ETF联接", "code": "012168", "style": "科技", "nav": 1.12, "risk": "高", "return_1y": "+9.4%", "return_3y": "+23.8%", "max_dd": "-29.2%", "sharpe": 0.56},
    
    # ==================== 二、消费/白酒（25只） ====================
    {"name": "易方达蓝筹精选混合", "code": "005827", "style": "消费", "nav": 2.56, "risk": "中", "return_1y": "+10.2%", "return_3y": "+28.6%", "max_dd": "-18.5%", "sharpe": 0.72},
    {"name": "易方达中小盘混合", "code": "110011", "style": "消费", "nav": 3.21, "risk": "中", "return_1y": "+12.5%", "return_3y": "+32.4%", "max_dd": "-20.1%", "sharpe": 0.78},
    {"name": "景顺长城新兴成长混合", "code": "260108", "style": "消费", "nav": 3.87, "risk": "中", "return_1y": "+14.8%", "return_3y": "+35.2%", "max_dd": "-19.8%", "sharpe": 0.82},
    {"name": "汇添富消费行业混合", "code": "000083", "style": "消费", "nav": 4.12, "risk": "中", "return_1y": "+16.2%", "return_3y": "+38.7%", "max_dd": "-17.6%", "sharpe": 0.85},
    {"name": "鹏华消费优选混合", "code": "206007", "style": "消费", "nav": 2.45, "risk": "中", "return_1y": "+8.6%", "return_3y": "+26.5%", "max_dd": "-21.2%", "sharpe": 0.68},
    {"name": "华夏消费升级混合A", "code": "001928", "style": "消费", "nav": 2.78, "risk": "中", "return_1y": "+11.2%", "return_3y": "+30.1%", "max_dd": "-19.5%", "sharpe": 0.74},
    {"name": "南方消费升级混合", "code": "010887", "style": "消费", "nav": 1.56, "risk": "中", "return_1y": "+7.5%", "return_3y": "+18.9%", "max_dd": "-22.6%", "sharpe": 0.56},
    {"name": "嘉实消费精选股票A", "code": "006604", "style": "消费", "nav": 1.89, "risk": "中", "return_1y": "+9.2%", "return_3y": "+22.3%", "max_dd": "-20.8%", "sharpe": 0.62},
    {"name": "富国消费主题混合", "code": "519915", "style": "消费", "nav": 2.34, "risk": "中", "return_1y": "+10.5%", "return_3y": "+25.6%", "max_dd": "-19.2%", "sharpe": 0.66},
    {"name": "银华富裕主题混合", "code": "180012", "style": "消费", "nav": 3.45, "risk": "中", "return_1y": "+12.8%", "return_3y": "+28.9%", "max_dd": "-18.6%", "sharpe": 0.72},
    {"name": "华安安信消费服务混合", "code": "519002", "style": "消费", "nav": 2.12, "risk": "中", "return_1y": "+8.9%", "return_3y": "+24.7%", "max_dd": "-20.4%", "sharpe": 0.64},
    {"name": "国泰大消费股票", "code": "009473", "style": "消费", "nav": 1.23, "risk": "中", "return_1y": "+6.8%", "return_3y": "+16.8%", "max_dd": "-24.5%", "sharpe": 0.52},
    {"name": "招商中证白酒指数", "code": "161725", "style": "消费", "nav": 1.89, "risk": "中", "return_1y": "+14.5%", "return_3y": "+28.6%", "max_dd": "-22.3%", "sharpe": 0.74},
    {"name": "鹏华中证酒指数", "code": "160632", "style": "消费", "nav": 1.56, "risk": "中", "return_1y": "+12.8%", "return_3y": "+25.4%", "max_dd": "-23.8%", "sharpe": 0.70},
    {"name": "国泰国证食品饮料", "code": "160222", "style": "消费", "nav": 1.78, "risk": "中", "return_1y": "+13.2%", "return_3y": "+26.8%", "max_dd": "-22.6%", "sharpe": 0.72},
    {"name": "天弘中证食品饮料ETF联接", "code": "001631", "style": "消费", "nav": 1.45, "risk": "中", "return_1y": "+10.6%", "return_3y": "+22.4%", "max_dd": "-24.2%", "sharpe": 0.64},
    {"name": "汇添富中证主要消费ETF联接", "code": "000248", "style": "消费", "nav": 2.12, "risk": "中", "return_1y": "+11.8%", "return_3y": "+24.6%", "max_dd": "-21.8%", "sharpe": 0.68},
    {"name": "华夏中证细分食品饮料ETF联接", "code": "013125", "style": "消费", "nav": 1.12, "risk": "中", "return_1y": "+8.5%", "return_3y": "+18.2%", "max_dd": "-25.6%", "sharpe": 0.56},
    {"name": "广发中证全指消费ETF联接", "code": "001458", "style": "消费", "nav": 1.34, "risk": "中", "return_1y": "+9.8%", "return_3y": "+20.6%", "max_dd": "-23.8%", "sharpe": 0.60},
    {"name": "南方中证全指消费ETF联接", "code": "012650", "style": "消费", "nav": 1.15, "risk": "中", "return_1y": "+7.8%", "return_3y": "+17.6%", "max_dd": "-26.2%", "sharpe": 0.54},
    {"name": "嘉实中证全指消费ETF联接", "code": "014140", "style": "消费", "nav": 1.08, "risk": "中", "return_1y": "+7.2%", "return_3y": "+16.8%", "max_dd": "-26.8%", "sharpe": 0.52},
    {"name": "富国中证消费50ETF联接", "code": "008975", "style": "消费", "nav": 1.25, "risk": "中", "return_1y": "+9.2%", "return_3y": "+21.2%", "max_dd": "-24.6%", "sharpe": 0.58},
    {"name": "易方达中证消费50ETF联接", "code": "012817", "style": "消费", "nav": 1.18, "risk": "中", "return_1y": "+8.8%", "return_3y": "+20.8%", "max_dd": "-25.2%", "sharpe": 0.56},
    {"name": "华宝中证消费龙头ETF联接", "code": "009329", "style": "消费", "nav": 1.22, "risk": "中", "return_1y": "+9.6%", "return_3y": "+22.4%", "max_dd": "-24.8%", "sharpe": 0.58},
    {"name": "国泰中证消费服务ETF联接", "code": "006952", "style": "消费", "nav": 1.28, "risk": "中", "return_1y": "+10.2%", "return_3y": "+23.6%", "max_dd": "-23.6%", "sharpe": 0.60},
    
    # ==================== 三、医药/医疗（28只） ====================
    {"name": "中欧医疗健康混合A", "code": "003095", "style": "医药", "nav": 2.34, "risk": "高", "return_1y": "+18.6%", "return_3y": "+45.8%", "max_dd": "-28.6%", "sharpe": 0.82},
    {"name": "汇添富创新医药混合", "code": "006113", "style": "医药", "nav": 1.98, "risk": "高", "return_1y": "+14.5%", "return_3y": "+38.2%", "max_dd": "-26.8%", "sharpe": 0.76},
    {"name": "广发医疗保健股票A", "code": "004851", "style": "医药", "nav": 3.12, "risk": "高", "return_1y": "+16.8%", "return_3y": "+42.6%", "max_dd": "-27.4%", "sharpe": 0.80},
    {"name": "工银瑞信前沿医疗股票", "code": "001717", "style": "医药", "nav": 2.78, "risk": "高", "return_1y": "+15.2%", "return_3y": "+40.1%", "max_dd": "-25.9%", "sharpe": 0.78},
    {"name": "大摩健康产业混合", "code": "002708", "style": "医药", "nav": 1.65, "risk": "高", "return_1y": "+12.8%", "return_3y": "+32.8%", "max_dd": "-30.2%", "sharpe": 0.68},
    {"name": "中欧医疗创新股票A", "code": "006228", "style": "医药", "nav": 1.87, "risk": "高", "return_1y": "+13.6%", "return_3y": "+36.4%", "max_dd": "-28.8%", "sharpe": 0.72},
    {"name": "招商医药健康产业股票", "code": "000960", "style": "医药", "nav": 2.45, "risk": "高", "return_1y": "+14.2%", "return_3y": "+35.2%", "max_dd": "-27.6%", "sharpe": 0.74},
    {"name": "南方医药保健灵活配置", "code": "000452", "style": "医药", "nav": 2.12, "risk": "高", "return_1y": "+11.8%", "return_3y": "+30.7%", "max_dd": "-29.4%", "sharpe": 0.66},
    {"name": "易方达医疗保健行业", "code": "110023", "style": "医药", "nav": 3.56, "risk": "高", "return_1y": "+19.2%", "return_3y": "+48.9%", "max_dd": "-26.2%", "sharpe": 0.86},
    {"name": "富国医疗保健行业混合", "code": "000220", "style": "医药", "nav": 2.67, "risk": "高", "return_1y": "+13.8%", "return_3y": "+33.5%", "max_dd": "-28.4%", "sharpe": 0.70},
    {"name": "华宝医药生物混合", "code": "240020", "style": "医药", "nav": 2.34, "risk": "高", "return_1y": "+11.2%", "return_3y": "+28.6%", "max_dd": "-30.8%", "sharpe": 0.64},
    {"name": "华夏医疗健康混合A", "code": "000945", "style": "医药", "nav": 1.89, "risk": "高", "return_1y": "+10.8%", "return_3y": "+26.7%", "max_dd": "-31.6%", "sharpe": 0.62},
    {"name": "国泰中证生物医药ETF联接", "code": "006756", "style": "医药", "nav": 1.56, "risk": "高", "return_1y": "+12.5%", "return_3y": "+30.2%", "max_dd": "-28.6%", "sharpe": 0.66},
    {"name": "汇添富中证生物科技ETF联接", "code": "501009", "style": "医药", "nav": 1.78, "risk": "高", "return_1y": "+13.2%", "return_3y": "+32.8%", "max_dd": "-27.8%", "sharpe": 0.68},
    {"name": "华安中证医药ETF联接", "code": "000373", "style": "医药", "nav": 1.45, "risk": "高", "return_1y": "+11.6%", "return_3y": "+28.4%", "max_dd": "-29.6%", "sharpe": 0.64},
    {"name": "天弘中证医药100ETF联接", "code": "001551", "style": "医药", "nav": 1.34, "risk": "高", "return_1y": "+10.8%", "return_3y": "+26.8%", "max_dd": "-30.4%", "sharpe": 0.60},
    {"name": "南方中证全指医疗保健ETF联接", "code": "010120", "style": "医药", "nav": 1.23, "risk": "高", "return_1y": "+9.8%", "return_3y": "+24.6%", "max_dd": "-31.8%", "sharpe": 0.58},
    {"name": "华夏中证医疗ETF联接", "code": "014602", "style": "医药", "nav": 1.15, "risk": "高", "return_1y": "+8.6%", "return_3y": "+22.4%", "max_dd": "-32.6%", "sharpe": 0.54},
    {"name": "国泰中证医疗ETF联接", "code": "012634", "style": "医药", "nav": 1.08, "risk": "高", "return_1y": "+7.8%", "return_3y": "+20.8%", "max_dd": "-33.8%", "sharpe": 0.50},
    {"name": "博时中证医疗ETF联接", "code": "016545", "style": "医药", "nav": 1.02, "risk": "高", "return_1y": "+7.2%", "return_3y": "+18.6%", "max_dd": "-34.5%", "sharpe": 0.48},
    {"name": "广发中证全指医药ETF联接", "code": "004857", "style": "医药", "nav": 1.42, "risk": "高", "return_1y": "+11.2%", "return_3y": "+27.6%", "max_dd": "-29.2%", "sharpe": 0.62},
    {"name": "易方达中证医药ETF联接", "code": "001344", "style": "医药", "nav": 1.38, "risk": "高", "return_1y": "+10.8%", "return_3y": "+26.8%", "max_dd": "-29.8%", "sharpe": 0.60},
    {"name": "嘉实中证医药ETF联接", "code": "011402", "style": "医药", "nav": 1.12, "risk": "高", "return_1y": "+8.2%", "return_3y": "+21.2%", "max_dd": "-31.6%", "sharpe": 0.52},
    {"name": "富国中证医药ETF联接", "code": "011161", "style": "医药", "nav": 1.15, "risk": "高", "return_1y": "+8.6%", "return_3y": "+22.4%", "max_dd": "-30.8%", "sharpe": 0.54},
    {"name": "鹏华中证医药ETF联接", "code": "012752", "style": "医药", "nav": 1.06, "risk": "高", "return_1y": "+7.6%", "return_3y": "+20.2%", "max_dd": "-32.8%", "sharpe": 0.50},
    {"name": "华宝中证医疗ETF联接", "code": "162412", "style": "医药", "nav": 1.55, "risk": "高", "return_1y": "+12.2%", "return_3y": "+29.6%", "max_dd": "-28.6%", "sharpe": 0.64},
    
    # ==================== 四、均衡/价值（25只） ====================
    {"name": "交银阿尔法核心混合", "code": "519712", "style": "均衡", "nav": 3.21, "risk": "中", "return_1y": "+12.6%", "return_3y": "+32.4%", "max_dd": "-16.5%", "sharpe": 0.82},
    {"name": "兴全轻资产混合", "code": "163412", "style": "均衡", "nav": 2.89, "risk": "中", "return_1y": "+11.8%", "return_3y": "+28.9%", "max_dd": "-17.8%", "sharpe": 0.76},
    {"name": "兴全合润混合", "code": "163406", "style": "均衡", "nav": 4.56, "risk": "中", "return_1y": "+16.8%", "return_3y": "+42.3%", "max_dd": "-18.2%", "sharpe": 0.90},
    {"name": "富国天惠成长混合", "code": "161005", "style": "均衡", "nav": 3.67, "risk": "中", "return_1y": "+14.2%", "return_3y": "+35.6%", "max_dd": "-17.8%", "sharpe": 0.86},
    {"name": "睿远成长价值混合A", "code": "007119", "style": "均衡", "nav": 2.13, "risk": "中", "return_1y": "+10.8%", "return_3y": "+26.8%", "max_dd": "-20.5%", "sharpe": 0.72},
    {"name": "东方红睿丰混合", "code": "169101", "style": "均衡", "nav": 3.45, "risk": "中", "return_1y": "+11.2%", "return_3y": "+30.2%", "max_dd": "-18.6%", "sharpe": 0.74},
    {"name": "泓德远见回报混合", "code": "001500", "style": "均衡", "nav": 2.67, "risk": "中", "return_1y": "+9.8%", "return_3y": "+25.4%", "max_dd": "-19.8%", "sharpe": 0.68},
    {"name": "国泰聚信价值优势混合", "code": "000362", "style": "均衡", "nav": 2.34, "risk": "中低", "return_1y": "+8.6%", "return_3y": "+22.1%", "max_dd": "-15.6%", "sharpe": 0.64},
    {"name": "华安策略优选混合", "code": "040008", "style": "均衡", "nav": 3.12, "risk": "中低", "return_1y": "+9.2%", "return_3y": "+24.8%", "max_dd": "-16.2%", "sharpe": 0.66},
    {"name": "博时主题行业混合", "code": "160505", "style": "均衡", "nav": 2.78, "risk": "中低", "return_1y": "+8.5%", "return_3y": "+20.5%", "max_dd": "-17.4%", "sharpe": 0.60},
    {"name": "广发稳健增长混合", "code": "270002", "style": "均衡", "nav": 2.45, "risk": "中", "return_1y": "+7.8%", "return_3y": "+18.6%", "max_dd": "-16.8%", "sharpe": 0.58},
    {"name": "南方绩优成长混合", "code": "202003", "style": "均衡", "nav": 3.56, "risk": "中", "return_1y": "+10.5%", "return_3y": "+28.4%", "max_dd": "-18.2%", "sharpe": 0.72},
    {"name": "华夏回报混合A", "code": "002001", "style": "均衡", "nav": 2.89, "risk": "中低", "return_1y": "+6.8%", "return_3y": "+16.8%", "max_dd": "-14.2%", "sharpe": 0.54},
    {"name": "嘉实增长混合", "code": "070002", "style": "均衡", "nav": 4.12, "risk": "中", "return_1y": "+12.8%", "return_3y": "+32.5%", "max_dd": "-17.6%", "sharpe": 0.80},
    {"name": "长盛成长价值混合", "code": "080001", "style": "均衡", "nav": 1.89, "risk": "中低", "return_1y": "+5.8%", "return_3y": "+14.2%", "max_dd": "-15.8%", "sharpe": 0.50},
    {"name": "易方达价值精选混合", "code": "110009", "style": "均衡", "nav": 2.78, "risk": "中", "return_1y": "+9.6%", "return_3y": "+24.6%", "max_dd": "-18.4%", "sharpe": 0.66},
    {"name": "富国天益价值混合", "code": "100020", "style": "均衡", "nav": 3.12, "risk": "中", "return_1y": "+10.2%", "return_3y": "+26.8%", "max_dd": "-17.8%", "sharpe": 0.68},
    {"name": "汇添富优势精选混合", "code": "519008", "style": "均衡", "nav": 3.45, "risk": "中", "return_1y": "+11.5%", "return_3y": "+28.2%", "max_dd": "-18.6%", "sharpe": 0.70},
    {"name": "华宝收益增长混合", "code": "240008", "style": "均衡", "nav": 2.34, "risk": "中", "return_1y": "+8.8%", "return_3y": "+22.4%", "max_dd": "-19.6%", "sharpe": 0.62},
    {"name": "国投瑞银稳健增长混合", "code": "121006", "style": "均衡", "nav": 2.56, "risk": "中低", "return_1y": "+7.6%", "return_3y": "+18.8%", "max_dd": "-16.2%", "sharpe": 0.56},
    {"name": "银华优势企业混合", "code": "180001", "style": "均衡", "nav": 2.12, "risk": "中", "return_1y": "+8.2%", "return_3y": "+20.6%", "max_dd": "-18.8%", "sharpe": 0.60},
    {"name": "长城久富核心成长混合", "code": "162006", "style": "均衡", "nav": 2.34, "risk": "中", "return_1y": "+9.4%", "return_3y": "+24.2%", "max_dd": "-17.6%", "sharpe": 0.64},
    {"name": "鹏华价值优势混合", "code": "160607", "style": "均衡", "nav": 2.45, "risk": "中", "return_1y": "+8.6%", "return_3y": "+22.8%", "max_dd": "-18.2%", "sharpe": 0.62},
    {"name": "融通新蓝筹混合", "code": "161601", "style": "均衡", "nav": 2.12, "risk": "中", "return_1y": "+7.8%", "return_3y": "+19.6%", "max_dd": "-19.6%", "sharpe": 0.58},
    
    # ==================== 五、港股/沪港深（15只） ====================
    {"name": "前海开源沪港深优势精选", "code": "001875", "style": "港股", "nav": 2.85, "risk": "中高", "return_1y": "+15.6%", "return_3y": "+38.6%", "max_dd": "-22.8%", "sharpe": 0.80},
    {"name": "富国沪港深行业精选", "code": "005354", "style": "港股", "nav": 1.56, "risk": "中高", "return_1y": "+8.8%", "return_3y": "+22.4%", "max_dd": "-25.6%", "sharpe": 0.56},
    {"name": "工银瑞信沪港深股票", "code": "002387", "style": "港股", "nav": 1.78, "risk": "中高", "return_1y": "+9.6%", "return_3y": "+25.6%", "max_dd": "-24.8%", "sharpe": 0.58},
    {"name": "广发沪港深新起点股票", "code": "002121", "style": "港股", "nav": 2.12, "risk": "中高", "return_1y": "+10.8%", "return_3y": "+28.9%", "max_dd": "-23.6%", "sharpe": 0.62},
    {"name": "嘉实沪港深精选股票", "code": "001878", "style": "港股", "nav": 2.34, "risk": "中高", "return_1y": "+12.8%", "return_3y": "+30.2%", "max_dd": "-24.6%", "sharpe": 0.66},
    {"name": "汇添富沪港深新价值股票", "code": "001685", "style": "港股", "nav": 1.89, "risk": "中高", "return_1y": "+9.2%", "return_3y": "+24.7%", "max_dd": "-26.2%", "sharpe": 0.58},
    {"name": "前海开源沪港深龙头精选", "code": "002443", "style": "港股", "nav": 1.45, "risk": "中高", "return_1y": "+7.8%", "return_3y": "+20.3%", "max_dd": "-28.4%", "sharpe": 0.52},
    {"name": "华安沪港深机会灵活配置", "code": "004263", "style": "港股", "nav": 1.67, "risk": "中高", "return_1y": "+8.5%", "return_3y": "+23.8%", "max_dd": "-26.8%", "sharpe": 0.54},
    {"name": "国富沪港深成长精选", "code": "001605", "style": "港股", "nav": 1.56, "risk": "中高", "return_1y": "+7.6%", "return_3y": "+21.6%", "max_dd": "-27.6%", "sharpe": 0.50},
    {"name": "景顺长城沪港深精选", "code": "000979", "style": "港股", "nav": 1.89, "risk": "中高", "return_1y": "+9.8%", "return_3y": "+24.8%", "max_dd": "-25.8%", "sharpe": 0.56},
    {"name": "南方沪港深价值主题", "code": "001979", "style": "港股", "nav": 1.34, "risk": "中高", "return_1y": "+7.2%", "return_3y": "+19.6%", "max_dd": "-28.6%", "sharpe": 0.48},
    {"name": "华夏沪港深上证50AH优选", "code": "501050", "style": "港股", "nav": 1.56, "risk": "中高", "return_1y": "+8.2%", "return_3y": "+22.8%", "max_dd": "-26.2%", "sharpe": 0.52},
    {"name": "鹏华沪港深互联网ETF联接", "code": "012169", "style": "港股", "nav": 1.12, "risk": "中高", "return_1y": "+6.8%", "return_3y": "+18.2%", "max_dd": "-29.6%", "sharpe": 0.46},
    {"name": "天弘沪港深ETF联接", "code": "012560", "style": "港股", "nav": 1.08, "risk": "中高", "return_1y": "+6.2%", "return_3y": "+17.6%", "max_dd": "-30.2%", "sharpe": 0.44},
    
    # ==================== 六、半导体/芯片（15只） ====================
    {"name": "诺安成长混合", "code": "320007", "style": "芯片", "nav": 2.34, "risk": "高", "return_1y": "+22.6%", "return_3y": "+52.3%", "max_dd": "-34.5%", "sharpe": 0.72},
    {"name": "银河创新成长混合", "code": "519674", "style": "芯片", "nav": 4.56, "risk": "高", "return_1y": "+28.4%", "return_3y": "+62.8%", "max_dd": "-36.2%", "sharpe": 0.76},
    {"name": "国联安中证半导体ETF联接", "code": "007301", "style": "芯片", "nav": 1.87, "risk": "高", "return_1y": "+20.8%", "return_3y": "+48.6%", "max_dd": "-30.8%", "sharpe": 0.70},
    {"name": "华夏国证半导体芯片ETF联接", "code": "008887", "style": "芯片", "nav": 1.23, "risk": "高", "return_1y": "+18.2%", "return_3y": "+42.5%", "max_dd": "-31.8%", "sharpe": 0.68},
    {"name": "泰信中小盘精选混合", "code": "290011", "style": "芯片", "nav": 2.78, "risk": "高", "return_1y": "+16.8%", "return_3y": "+45.2%", "max_dd": "-33.6%", "sharpe": 0.66},
    {"name": "国泰CES半导体芯片ETF联接", "code": "008281", "style": "芯片", "nav": 1.67, "risk": "高", "return_1y": "+17.6%", "return_3y": "+38.2%", "max_dd": "-30.1%", "sharpe": 0.64},
    {"name": "鹏华国证半导体芯片ETF联接", "code": "012969", "style": "芯片", "nav": 1.12, "risk": "高", "return_1y": "+12.8%", "return_3y": "+30.2%", "max_dd": "-32.5%", "sharpe": 0.56},
    {"name": "嘉实中证芯片产业ETF联接", "code": "015336", "style": "芯片", "nav": 1.08, "risk": "高", "return_1y": "+10.6%", "return_3y": "+25.8%", "max_dd": "-33.8%", "sharpe": 0.52},
    {"name": "国联安中证全指半导体ETF联接", "code": "007300", "style": "芯片", "nav": 1.89, "risk": "高", "return_1y": "+17.6%", "return_3y": "+40.6%", "max_dd": "-29.6%", "sharpe": 0.62},
    {"name": "汇添富中证芯片产业ETF联接", "code": "014193", "style": "芯片", "nav": 1.05, "risk": "高", "return_1y": "+9.8%", "return_3y": "+24.2%", "max_dd": "-34.2%", "sharpe": 0.50},
    {"name": "华夏中证半导体ETF联接", "code": "008516", "style": "芯片", "nav": 1.32, "risk": "高", "return_1y": "+14.2%", "return_3y": "+34.6%", "max_dd": "-31.2%", "sharpe": 0.60},
    {"name": "南方中证半导体ETF联接", "code": "008618", "style": "芯片", "nav": 1.28, "risk": "高", "return_1y": "+13.8%", "return_3y": "+33.8%", "max_dd": "-31.8%", "sharpe": 0.58},
    {"name": "易方达中证半导体ETF联接", "code": "012870", "style": "芯片", "nav": 1.18, "risk": "高", "return_1y": "+11.6%", "return_3y": "+28.4%", "max_dd": "-32.6%", "sharpe": 0.54},
    {"name": "富国中证半导体ETF联接", "code": "014099", "style": "芯片", "nav": 1.08, "risk": "高", "return_1y": "+10.2%", "return_3y": "+26.2%", "max_dd": "-33.8%", "sharpe": 0.50},
    {"name": "天弘中证半导体ETF联接", "code": "012722", "style": "芯片", "nav": 1.02, "risk": "高", "return_1y": "+8.8%", "return_3y": "+22.8%", "max_dd": "-34.8%", "sharpe": 0.46},
    
    # ==================== 七、新能源（16只） ====================
    {"name": "农银新能源主题混合", "code": "002190", "style": "新能源", "nav": 3.45, "risk": "高", "return_1y": "+24.6%", "return_3y": "+55.8%", "max_dd": "-32.4%", "sharpe": 0.82},
    {"name": "嘉实新能源新材料股票", "code": "003984", "style": "新能源", "nav": 2.67, "risk": "高", "return_1y": "+18.2%", "return_3y": "+42.6%", "max_dd": "-30.6%", "sharpe": 0.74},
    {"name": "汇丰晋信低碳先锋股票", "code": "540008", "style": "新能源", "nav": 3.12, "risk": "高", "return_1y": "+20.8%", "return_3y": "+48.3%", "max_dd": "-31.8%", "sharpe": 0.78},
    {"name": "华夏能源革新股票", "code": "003834", "style": "新能源", "nav": 2.89, "risk": "高", "return_1y": "+18.2%", "return_3y": "+45.2%", "max_dd": "-30.6%", "sharpe": 0.76},
    {"name": "东方新能源汽车主题混合", "code": "400015", "style": "新能源", "nav": 2.45, "risk": "高", "return_1y": "+15.6%", "return_3y": "+40.6%", "max_dd": "-32.8%", "sharpe": 0.70},
    {"name": "汇添富中证新能源汽车", "code": "501057", "style": "新能源", "nav": 2.45, "risk": "高", "return_1y": "+16.8%", "return_3y": "+42.6%", "max_dd": "-30.8%", "sharpe": 0.72},
    {"name": "富国中证新能源汽车", "code": "161028", "style": "新能源", "nav": 2.12, "risk": "高", "return_1y": "+15.2%", "return_3y": "+38.9%", "max_dd": "-31.6%", "sharpe": 0.68},
    {"name": "国泰国证新能源汽车", "code": "160225", "style": "新能源", "nav": 1.89, "risk": "高", "return_1y": "+14.6%", "return_3y": "+36.8%", "max_dd": "-32.4%", "sharpe": 0.66},
    {"name": "申万菱信新能源汽车", "code": "001156", "style": "新能源", "nav": 1.78, "risk": "高", "return_1y": "+13.8%", "return_3y": "+35.2%", "max_dd": "-33.6%", "sharpe": 0.64},
    {"name": "鹏华中证新能源指数", "code": "160640", "style": "新能源", "nav": 1.56, "risk": "高", "return_1y": "+12.6%", "return_3y": "+32.8%", "max_dd": "-34.2%", "sharpe": 0.60},
    {"name": "南方中证新能源ETF联接", "code": "012831", "style": "新能源", "nav": 1.23, "risk": "高", "return_1y": "+11.8%", "return_3y": "+30.6%", "max_dd": "-35.6%", "sharpe": 0.58},
    {"name": "天弘中证新能源ETF联接", "code": "012328", "style": "新能源", "nav": 1.15, "risk": "高", "return_1y": "+10.8%", "return_3y": "+28.8%", "max_dd": "-36.8%", "sharpe": 0.54},
    {"name": "华夏中证光伏产业ETF联接", "code": "012886", "style": "新能源", "nav": 1.08, "risk": "高", "return_1y": "+9.6%", "return_3y": "+22.8%", "max_dd": "-32.6%", "sharpe": 0.48},
    {"name": "天弘中证光伏产业ETF联接", "code": "011103", "style": "新能源", "nav": 1.05, "risk": "高", "return_1y": "+8.8%", "return_3y": "+20.6%", "max_dd": "-33.8%", "sharpe": 0.44},
    {"name": "华宝中证绿色能源ETF联接", "code": "015549", "style": "新能源", "nav": 1.02, "risk": "高", "return_1y": "+7.8%", "return_3y": "+18.2%", "max_dd": "-34.8%", "sharpe": 0.42},
    {"name": "易方达中证新能源ETF联接", "code": "012733", "style": "新能源", "nav": 1.12, "risk": "高", "return_1y": "+10.2%", "return_3y": "+24.6%", "max_dd": "-31.6%", "sharpe": 0.50},
    
    # ==================== 八、军工（10只） ====================
    {"name": "富国军工主题混合", "code": "005609", "style": "军工", "nav": 1.56, "risk": "高", "return_1y": "+12.6%", "return_3y": "+28.6%", "max_dd": "-25.8%", "sharpe": 0.68},
    {"name": "南方军工改革灵活配置", "code": "004224", "style": "军工", "nav": 1.78, "risk": "高", "return_1y": "+11.8%", "return_3y": "+26.4%", "max_dd": "-26.8%", "sharpe": 0.64},
    {"name": "华夏军工安全灵活配置", "code": "002251", "style": "军工", "nav": 1.45, "risk": "高", "return_1y": "+10.6%", "return_3y": "+24.8%", "max_dd": "-27.6%", "sharpe": 0.60},
    {"name": "易方达国防军工混合", "code": "001475", "style": "军工", "nav": 2.12, "risk": "高", "return_1y": "+14.8%", "return_3y": "+30.2%", "max_dd": "-26.4%", "sharpe": 0.70},
    {"name": "富国中证军工龙头ETF联接", "code": "011113", "style": "军工", "nav": 1.23, "risk": "高", "return_1y": "+10.8%", "return_3y": "+26.8%", "max_dd": "-28.6%", "sharpe": 0.58},
    {"name": "鹏华中证国防指数", "code": "160630", "style": "军工", "nav": 1.56, "risk": "高", "return_1y": "+11.2%", "return_3y": "+27.2%", "max_dd": "-27.8%", "sharpe": 0.60},
    {"name": "国泰国证航天军工指数", "code": "501019", "style": "军工", "nav": 1.34, "risk": "高", "return_1y": "+9.8%", "return_3y": "+24.6%", "max_dd": "-29.6%", "sharpe": 0.56},
    {"name": "华宝中证军工ETF联接", "code": "008841", "style": "军工", "nav": 1.12, "risk": "高", "return_1y": "+8.6%", "return_3y": "+22.4%", "max_dd": "-30.8%", "sharpe": 0.52},
    {"name": "广发中证军工ETF联接", "code": "003017", "style": "军工", "nav": 1.28, "risk": "高", "return_1y": "+9.6%", "return_3y": "+24.2%", "max_dd": "-29.2%", "sharpe": 0.54},
    {"name": "易方达中证军工ETF联接", "code": "012756", "style": "军工", "nav": 1.15, "risk": "高", "return_1y": "+8.8%", "return_3y": "+23.8%", "max_dd": "-30.2%", "sharpe": 0.52},
    
    # ==================== 九、金融/地产（12只） ====================
    {"name": "工银瑞信金融地产混合", "code": "000251", "style": "金融", "nav": 2.34, "risk": "中低", "return_1y": "+6.8%", "return_3y": "+16.8%", "max_dd": "-12.5%", "sharpe": 0.56},
    {"name": "汇添富价值精选混合", "code": "519069", "style": "金融", "nav": 2.89, "risk": "中低", "return_1y": "+7.2%", "return_3y": "+18.4%", "max_dd": "-13.2%", "sharpe": 0.58},
    {"name": "华安核心优选混合", "code": "040011", "style": "金融", "nav": 2.12, "risk": "中低", "return_1y": "+6.2%", "return_3y": "+14.5%", "max_dd": "-14.6%", "sharpe": 0.50},
    {"name": "国富金融地产混合", "code": "001392", "style": "金融", "nav": 1.56, "risk": "中低", "return_1y": "+5.8%", "return_3y": "+12.8%", "max_dd": "-15.2%", "sharpe": 0.46},
    {"name": "鹏华金融地产混合", "code": "001663", "style": "金融", "nav": 1.78, "risk": "中低", "return_1y": "+6.2%", "return_3y": "+13.6%", "max_dd": "-14.8%", "sharpe": 0.48},
    {"name": "中海进取收益混合", "code": "001252", "style": "金融", "nav": 1.45, "risk": "中低", "return_1y": "+5.2%", "return_3y": "+10.2%", "max_dd": "-16.2%", "sharpe": 0.42},
    {"name": "华宝券商ETF联接", "code": "006098", "style": "金融", "nav": 1.56, "risk": "中", "return_1y": "+7.8%", "return_3y": "+12.6%", "max_dd": "-18.6%", "sharpe": 0.48},
    {"name": "南方中证全指券商ETF联接", "code": "004069", "style": "金融", "nav": 1.45, "risk": "中", "return_1y": "+7.2%", "return_3y": "+11.8%", "max_dd": "-19.2%", "sharpe": 0.46},
    {"name": "华夏中证银行ETF联接", "code": "008298", "style": "金融", "nav": 1.12, "risk": "低", "return_1y": "+4.8%", "return_3y": "+8.6%", "max_dd": "-10.2%", "sharpe": 0.38},
    {"name": "天弘中证银行ETF联接", "code": "001594", "style": "金融", "nav": 1.08, "risk": "低", "return_1y": "+4.2%", "return_3y": "+7.8%", "max_dd": "-10.8%", "sharpe": 0.36},
    {"name": "易方达中证银行ETF联接", "code": "012868", "style": "金融", "nav": 1.05, "risk": "低", "return_1y": "+3.8%", "return_3y": "+7.2%", "max_dd": "-11.2%", "sharpe": 0.34},
    
    # ==================== 十、农业/5G/能源/其他（12只） ====================
    {"name": "农银汇理现代农业加混合", "code": "001940", "style": "农业", "nav": 1.45, "risk": "中", "return_1y": "+6.8%", "return_3y": "+18.6%", "max_dd": "-18.2%", "sharpe": 0.48},
    {"name": "国泰中证畜牧养殖ETF联接", "code": "012724", "style": "农业", "nav": 1.12, "risk": "中", "return_1y": "+5.6%", "return_3y": "+14.2%", "max_dd": "-20.6%", "sharpe": 0.42},
    {"name": "华夏中证5G通信主题ETF联接", "code": "008086", "style": "5G", "nav": 1.23, "risk": "高", "return_1y": "+12.8%", "return_3y": "+32.4%", "max_dd": "-28.6%", "sharpe": 0.62},
    {"name": "建信能源化工ETF联接", "code": "008827", "style": "能源", "nav": 1.34, "risk": "中", "return_1y": "+6.2%", "return_3y": "+16.8%", "max_dd": "-22.6%", "sharpe": 0.44},
    {"name": "国泰中证煤炭ETF联接", "code": "008279", "style": "能源", "nav": 1.45, "risk": "中", "return_1y": "+5.8%", "return_3y": "+15.6%", "max_dd": "-21.6%", "sharpe": 0.40},
    {"name": "华宝中证有色金属ETF联接", "code": "015689", "style": "能源", "nav": 1.15, "risk": "中", "return_1y": "+7.2%", "return_3y": "+18.6%", "max_dd": "-20.8%", "sharpe": 0.44},
    {"name": "南方中证有色金属ETF联接", "code": "004433", "style": "能源", "nav": 1.25, "risk": "中", "return_1y": "+7.8%", "return_3y": "+19.2%", "max_dd": "-20.2%", "sharpe": 0.46},
    {"name": "华夏中证A50ETF联接", "code": "014530", "style": "均衡", "nav": 1.02, "risk": "中低", "return_1y": "+4.8%", "return_3y": "+10.2%", "max_dd": "-14.6%", "sharpe": 0.36},
    {"name": "易方达中证A50ETF联接", "code": "015170", "style": "均衡", "nav": 1.04, "risk": "中低", "return_1y": "+5.2%", "return_3y": "+11.2%", "max_dd": "-14.2%", "sharpe": 0.38},
    {"name": "富国中证A50ETF联接", "code": "015780", "style": "均衡", "nav": 1.03, "risk": "中低", "return_1y": "+5.0%", "return_3y": "+10.8%", "max_dd": "-14.8%", "sharpe": 0.37},
    {"name": "嘉实中证A50ETF联接", "code": "015250", "style": "均衡", "nav": 1.01, "risk": "中低", "return_1y": "+4.2%", "return_3y": "+9.6%", "max_dd": "-15.2%", "sharpe": 0.34},
    {"name": "华泰柏瑞中证A50ETF联接", "code": "015280", "style": "均衡", "nav": 1.02, "risk": "中低", "return_1y": "+4.5%", "return_3y": "+10.0%", "max_dd": "-15.0%", "sharpe": 0.35},
]

# ==================== 多因子评分函数 ====================
def calculate_fund_score(fund):
    score = 0
    ret_1y = float(fund["return_1y"].replace("%", "").replace("+", ""))
    score += min(30, max(0, (ret_1y + 20) * 1.0))
    ret_3y = float(fund["return_3y"].replace("%", "").replace("+", ""))
    score += min(25, max(0, (ret_3y + 15) * 0.7))
    dd = float(fund["max_dd"].replace("%", "").replace("-", ""))
    score += min(20, max(0, 20 - dd * 0.7))
    sharpe = fund["sharpe"]
    score += min(15, max(0, sharpe * 15))
    style_weights = {"科技": 1.2, "芯片": 1.3, "新能源": 1.2, "医药": 1.1, "消费": 1.0, "均衡": 1.0, "港股": 0.9, "军工": 1.0, "金融": 0.8, "农业": 0.8, "5G": 1.1, "能源": 0.8}
    score += min(10, max(0, style_weights.get(fund["style"], 1.0) * 8))
    return min(100, round(score))

# ==================== 市场状态 ====================
def get_market_sentiment():
    sentiments = ["乐观", "中性", "谨慎", "悲观"]
    weights = [0.25, 0.40, 0.25, 0.10]
    return np.random.choice(sentiments, p=weights)

def get_market_position():
    return random.randint(20, 80)

def get_timing_signal():
    signals = ["强烈买入", "买入", "持有", "减仓", "卖出"]
    weights = [0.12, 0.23, 0.38, 0.17, 0.10]
    return np.random.choice(signals, p=weights)

# ==================== AI推荐引擎 ====================
def ai_recommend(total_amount, risk_preference="中", existing_holdings=[], count=5):
    available = [f for f in FUNDS if f["code"] not in [h["code"] for h in existing_holdings]]
    risk_map = {"低": ["低", "中低"], "中": ["中低", "中", "中高"], "高": ["中高", "高"]}
    available = [f for f in available if f["risk"] in risk_map.get(risk_preference, ["中"])]
    if len(available) < count:
        available = FUNDS[:count * 2]
    for f in available:
        f["ai_score"] = calculate_fund_score(f)
    available = sorted(available, key=lambda x: x["ai_score"], reverse=True)
    recommendations = []
    for f in available[:count]:
        total_score = f["ai_score"] + random.randint(-5, 5)
        recommendations.append({
            "name": f["name"],
            "code": f["code"],
            "style": f["style"],
            "risk": f["risk"],
            "score": min(100, max(50, total_score)),
            "suggest_amount": round(total_amount * random.uniform(0.15, 0.30), 0),
            "return_3y": f["return_3y"],
            "max_dd": f["max_dd"],
            "sharpe": f["sharpe"],
            "reason": f"📈 {f['return_3y']} | 📉 {f['max_dd']} | ⭐ {f['sharpe']:.2f}"
        })
    return recommendations

def ai_portfolio_analysis(holdings, total_amount):
    if not holdings:
        return None
    total_cost = sum(h["amount"] for h in holdings)
    total_current = sum(h["amount"] * random.uniform(0.88, 1.15) for h in holdings)
    profit = total_current - total_cost
    profit_rate = (profit / total_cost) * 100 if total_cost > 0 else 0
    style_dist = {}
    for h in holdings:
        f = next((x for x in FUNDS if x["code"] == h["code"]), None)
        if f:
            style_dist[f["style"]] = style_dist.get(f["style"], 0) + h["amount"]
    max_style_ratio = max(style_dist.values()) / total_cost if style_dist else 0
    return {
        "total_cost": total_cost,
        "total_current": total_current,
        "profit": profit,
        "profit_rate": profit_rate,
        "style_distribution": style_dist,
        "max_style_ratio": max_style_ratio,
        "count": len(holdings),
        "remaining": total_amount - total_cost
    }

def ai_next_action(analysis, recommendations, market_sentiment, timing_signal):
    if not analysis or analysis["count"] == 0:
        return ["📌 您还没有持仓，建议根据AI推荐开始建仓"]
    suggestions = []
    if analysis["max_style_ratio"] > 0.6:
        suggestions.append(f"⚠️ 持仓过于集中在单一风格（占比{analysis['max_style_ratio']*100:.0f}%），建议分散投资")
    if analysis["remaining"] > 100:
        if timing_signal in ["强烈买入", "买入"]:
            suggestions.append(f"💰 当前市场信号：{timing_signal}，建议用剩余{analysis['remaining']:.0f}元分批建仓")
        else:
            suggestions.append(f"💰 您还有{analysis['remaining']:.0f}元可用资金，建议保持定投节奏")
    if analysis["profit_rate"] > 15:
        suggestions.append(f"📈 您的持仓已盈利{analysis['profit_rate']:.1f}%，建议设置止盈线")
    elif analysis["profit_rate"] < -8:
        suggestions.append(f"📉 您的持仓已亏损{analysis['profit_rate']:.1f}%，建议关注市场反弹机会")
    if recommendations and analysis["remaining"] > 100:
        suggestions.append(f"💡 推荐买入：{recommendations[0]['name']}（评分{recommendations[0]['score']}分）")
    return suggestions if suggestions else ["📊 您的持仓配置合理，建议继续持有观察"]

# ==================== 历史回测引擎 ====================
def generate_historical_prices(base_price, days, volatility=0.02, trend=0.0002):
    prices = [base_price]
    for i in range(days - 1):
        change = np.random.normal(trend, volatility)
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 0.1))
    return prices

def backtest_strategy(fund_code, start_date, end_date, total_amount, each_amount, strategy_type="智能定投"):
    fund = next((f for f in FUNDS if f["code"] == fund_code), None)
    if not fund:
        return None
    days = (end_date - start_date).days
    if days <= 0:
        return None
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    dates = [d for d in dates if d.weekday() < 5]
    if len(dates) < 20:
        return None
    base_price = fund["nav"]
    volatility = 0.025 if fund["risk"] in ["高", "中高"] else 0.015
    trend = 0.0003 if random.random() > 0.4 else -0.0001
    prices = generate_historical_prices(base_price * 0.8, len(dates), volatility, trend)
    df = pd.DataFrame({"date": dates[:len(prices)], "price": prices})
    df = df.set_index("date")
    cash = total_amount
    shares = 0
    trades = []
    portfolio_values = []
    for i in range(60, len(df)):
        current_price = df["price"].iloc[i]
        date = df.index[i]
        cash_remaining = cash - sum(t["amount"] for t in trades)
        if strategy_type == "智能定投":
            position = (current_price - df["price"].iloc[i-60:].min()) / (df["price"].iloc[i-60:].max() - df["price"].iloc[i-60:].min() + 0.001)
            buy_amount = each_amount * (1 + (0.5 - position) * 0.5)
            buy_amount = max(each_amount * 0.5, min(each_amount * 1.5, buy_amount))
            if cash_remaining >= buy_amount:
                shares += buy_amount / current_price
                trades.append({"date": date, "price": current_price, "amount": buy_amount})
        else:
            if i % 30 == 0 and cash_remaining >= each_amount:
                shares += each_amount / current_price
                trades.append({"date": date, "price": current_price, "amount": each_amount})
        portfolio_values.append({"date": date, "value": shares * current_price + (cash - sum(t["amount"] for t in trades))})
    final_price = df["price"].iloc[-1]
    final_value = shares * final_price + (cash - sum(t["amount"] for t in trades))
    total_invested = sum(t["amount"] for t in trades)
    profit = final_value - total_invested
    profit_rate = (profit / total_invested) * 100 if total_invested > 0 else 0
    value_series = pd.DataFrame(portfolio_values).set_index("date")["value"]
    cummax = value_series.cummax()
    drawdown = (value_series - cummax) / cummax * 100
    max_drawdown = drawdown.min()
    returns = value_series.pct_change().dropna()
    sharpe = (returns.mean() * 252) / (returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
    win_rate = (returns > 0).sum() / len(returns) if len(returns) > 0 else 0
    return {
        "fund_name": fund["name"],
        "fund_code": fund_code,
        "strategy": strategy_type,
        "total_invested": round(total_invested, 2),
        "final_value": round(final_value, 2),
        "profit": round(profit, 2),
        "profit_rate": round(profit_rate, 2),
        "max_drawdown": round(max_drawdown, 2),
        "sharpe_ratio": round(sharpe, 3),
        "win_rate": round(win_rate * 100, 2),
        "trade_count": len(trades),
        "value_data": value_series,
        "trades": trades
    }

# ==================== AI投资决策引擎 ====================
def ai_investment_decision(fund_code, backtest_result, market_sentiment, market_position, timing_signal):
    fund = next((f for f in FUNDS if f["code"] == fund_code), None)
    if not fund or not backtest_result:
        return None
    
    history_score = 0
    if backtest_result["profit_rate"] > 20:
        history_score += 25
    elif backtest_result["profit_rate"] > 10:
        history_score += 18
    else:
        history_score += 10
    if backtest_result["max_drawdown"] > -15:
        history_score += 15
    elif backtest_result["max_drawdown"] > -25:
        history_score += 10
    else:
        history_score += 5
    if backtest_result["win_rate"] > 60:
        history_score += 20
    elif backtest_result["win_rate"] > 50:
        history_score += 15
    else:
        history_score += 8
    history_score += min(10, backtest_result["sharpe_ratio"] * 8)
    history_score = min(70, history_score)
    
    market_score = 0
    sentiment_scores = {"乐观": 20, "中性": 15, "谨慎": 10, "悲观": 5}
    market_score += sentiment_scores.get(market_sentiment, 15)
    if market_position < 30:
        market_score += 20
    elif market_position < 50:
        market_score += 15
    elif market_position < 70:
        market_score += 10
    else:
        market_score += 5
    timing_scores = {"强烈买入": 20, "买入": 15, "持有": 10, "减仓": 5, "卖出": 0}
    market_score += timing_scores.get(timing_signal, 10)
    market_score = min(30, market_score)
    
    fund_score = calculate_fund_score(fund)
    fund_score = min(30, fund_score * 0.3)
    
    total_score = history_score + market_score + fund_score
    total_score = min(100, round(total_score))
    
    if total_score >= 75:
        decision = "✅ 强烈建议买入"
        action = "买入"
        urgency = "高"
        detail = f"综合评分{total_score}分，历史回测表现优秀"
        suggested_amount_ratio = 0.3
    elif total_score >= 60:
        decision = "📈 建议买入"
        action = "买入"
        urgency = "中"
        detail = f"综合评分{total_score}分，建议分批建仓"
        suggested_amount_ratio = 0.2
    elif total_score >= 45:
        decision = "⏳ 建议观望"
        action = "观望"
        urgency = "低"
        detail = f"综合评分{total_score}分，等待更好时机"
        suggested_amount_ratio = 0.1
    else:
        decision = "🔴 不建议买入"
        action = "回避"
        urgency = "高"
        detail = f"综合评分{total_score}分，建议等待"
        suggested_amount_ratio = 0
    
    return {
        "fund_name": fund["name"],
        "fund_code": fund_code,
        "total_score": total_score,
        "history_score": round(history_score, 1),
        "market_score": round(market_score, 1),
        "fund_score": round(fund_score, 1),
        "decision": decision,
        "action": action,
        "urgency": urgency,
        "detail": detail,
        "suggested_amount_ratio": suggested_amount_ratio,
        "backtest_profit": backtest_result["profit_rate"],
        "backtest_win_rate": backtest_result["win_rate"],
        "backtest_max_dd": backtest_result["max_drawdown"],
        "market_sentiment": market_sentiment,
        "market_position": market_position,
        "timing_signal": timing_signal,
        "report_generated": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

# ==================== 初始化session_state ====================
if "holdings" not in st.session_state:
    st.session_state.holdings = []
if "recommendations" not in st.session_state:
    st.session_state.recommendations = []
if "backtest_results" not in st.session_state:
    st.session_state.backtest_results = None
if "decision_result" not in st.session_state:
    st.session_state.decision_result = None
if "analysis_history" not in st.session_state:
    st.session_state.analysis_history = []
if "wechat_status" not in st.session_state:
    st.session_state.wechat_status = ""

# ==================== 侧边栏 ====================
with st.sidebar:
    st.header("💰 我的资产")
    total_cash = st.number_input("总资金（元）", min_value=0, value=10000, step=1000)
    risk_level = st.selectbox("风险偏好", ["低（保本为主）", "中（稳健增值）", "高（追求高收益）"], index=1)
    risk_map = {"低（保本为主）": "低", "中（稳健增值）": "中", "高（追求高收益）": "高"}
    risk_pref = risk_map[risk_level]
    
    st.divider()
    st.subheader("📱 微信通知")
    if st.button("📤 测试通知", use_container_width=True):
        success, msg = send_wechat_message("✅ AI基金投顾 Pro 微信通知测试成功！")
        st.session_state.wechat_status = msg
        st.rerun()
    if st.session_state.wechat_status:
        st.caption(st.session_state.wechat_status)
    
    st.divider()
    analysis = ai_portfolio_analysis(st.session_state.holdings, total_cash)
    if analysis:
        st.subheader("📊 持仓概览")
        c1, c2 = st.columns(2)
        c1.metric("总投入", f"{analysis['total_cost']:.0f}元")
        c2.metric("收益率", f"{analysis['profit_rate']:.1f}%", delta=f"{analysis['profit_rate']:.1f}%")

# ==================== 主界面Tab ====================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🤖 AI推荐", "📋 持仓管理", "🧠 智能分析", "📊 投资决策", "📈 市场信号", "🗂️ 基金超市"
])

# ==================== Tab1: AI推荐 ====================
with tab1:
    st.subheader("🤖 AI智能基金推荐")
    st.caption("基于多因子评分（收益+回撤+夏普+风格）")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"💰 {total_cash:,.0f}元 | 🎯 {risk_level} | 📊 持仓{len(st.session_state.holdings)}只")
    with col2:
        if st.button("🔍 AI分析", use_container_width=True, type="primary"):
            with st.spinner("AI分析中..."):
                recommendations = ai_recommend(total_cash, risk_pref, st.session_state.holdings)
                st.session_state.recommendations = recommendations
                st.success("✅ 分析完成！")
    if st.session_state.recommendations:
        for i, rec in enumerate(st.session_state.recommendations, 1):
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                with col1:
                    st.write(f"**{i}. {rec['name']}**")
                    st.caption(f"{rec['code']} | {rec['style']} | 风险：{rec['risk']}")
                with col2:
                    st.metric("AI评分", f"{rec['score']}/100")
                with col3:
                    st.caption(f"近3年：{rec['return_3y']}")
                    st.caption(f"回撤：{rec['max_dd']}")
                with col4:
                    st.metric("建议投入", f"{rec['suggest_amount']:.0f}元")
                    if st.button(f"📥 买入", key=f"buy_{rec['code']}"):
                        st.session_state.holdings.append({
                            "code": rec["code"],
                            "name": rec["name"],
                            "amount": rec["suggest_amount"],
                            "buy_date": datetime.now().strftime("%Y-%m-%d"),
                            "nav": random.uniform(1.0, 4.0)
                        })
                        st.success(f"✅ 已添加 {rec['name']}")
                        st.rerun()
                st.divider()

# ==================== Tab2: 持仓管理 ====================
with tab2:
    st.subheader("📋 我的持仓")
    with st.expander("➕ 添加持仓", expanded=False):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            fund_names = [f"{f['name']} ({f['code']})" for f in FUNDS]
            selected = st.selectbox("选择基金", fund_names, key="add_select")
            code = selected.split("(")[-1].replace(")", "")
            fund = next((f for f in FUNDS if f["code"] == code), None)
        with col2:
            amount = st.number_input("金额（元）", min_value=100, value=1000, step=100)
        with col3:
            date = st.date_input("日期", datetime.now())
        if st.button("✅ 确认添加", use_container_width=True) and fund:
            st.session_state.holdings.append({
                "code": code,
                "name": fund["name"],
                "amount": amount,
                "buy_date": date.strftime("%Y-%m-%d"),
                "nav": fund["nav"]
            })
            st.success(f"✅ 已添加 {fund['name']}")
            st.rerun()
    if st.session_state.holdings:
        df = pd.DataFrame(st.session_state.holdings)
        df["当前净值"] = df["nav"] * random.uniform(0.88, 1.15)
        df["市值"] = df["amount"] / df["nav"] * df["当前净值"]
        df["盈亏"] = df["市值"] - df["amount"]
        df["盈亏率%"] = (df["盈亏"] / df["amount"]) * 100
        st.dataframe(df[["name", "amount", "buy_date", "市值", "盈亏", "盈亏率%"]],
                     column_config={"name": "基金", "amount": "投入", "buy_date": "日期",
                                   "市值": st.column_config.NumberColumn(format="%.2f元"),
                                   "盈亏": st.column_config.NumberColumn(format="%.2f元"),
                                   "盈亏率%": st.column_config.NumberColumn(format="%.2f%%")},
                     use_container_width=True)
        with st.expander("🗑️ 删除持仓", expanded=False):
            idx = st.selectbox("选择要删除的", range(len(st.session_state.holdings)),
                              format_func=lambda i: st.session_state.holdings[i]["name"])
            if st.button("确认删除", use_container_width=True):
                st.session_state.holdings.pop(idx)
                st.rerun()
    else:
        st.info("📭 暂无持仓")

# ==================== Tab3: 智能分析 ====================
with tab3:
    st.subheader("🧠 AI智能分析")
    if st.button("📊 运行综合分析", use_container_width=True, type="primary"):
        with st.spinner("AI分析中..."):
            time.sleep(1.5)
            market = get_market_sentiment()
            timing = get_timing_signal()
            analysis = ai_portfolio_analysis(st.session_state.holdings, total_cash)
            if analysis:
                st.success("✅ 分析完成！")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("持仓数量", f"{analysis['count']}只")
                c2.metric("总收益率", f"{analysis['profit_rate']:.1f}%", delta=f"{analysis['profit_rate']:.1f}%")
                c3.metric("市场情绪", market)
                c4.metric("择时信号", timing)
                if analysis["style_distribution"]:
                    st.subheader("📊 持仓风格分布")
                    df_style = pd.DataFrame({
                        "风格": list(analysis["style_distribution"].keys()),
                        "金额": list(analysis["style_distribution"].values())
                    })
                    st.bar_chart(df_style.set_index("风格"))
            else:
                st.warning("请先添加持仓")

# ==================== Tab4: 投资决策 ====================
with tab4:
    st.subheader("📊 AI投资决策引擎")
    st.caption("结合历史回测 + 当前市场状态，AI告诉你现在能不能买")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        fund_names = [f"{f['name']} ({f['code']})" for f in FUNDS[:30]]
        decision_fund = st.selectbox("选择基金", fund_names, key="decision_select")
        decision_code = decision_fund.split("(")[-1].replace(")", "")
        decision_strategy = st.selectbox("回测策略", ["智能定投", "普通定投"])
    with col2:
        decision_years = st.slider("回测年数", 1, 5, 2)
        decision_monthly = st.number_input("每月定投金额（元）", min_value=100, value=1000, step=100)
        total_backtest_amount = decision_monthly * decision_years * 12
        st.caption(f"📊 回测总投入：{total_backtest_amount:.0f}元")
    
    if st.button("🧠 AI投资决策", use_container_width=True, type="primary"):
        with st.spinner("AI正在分析..."):
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365 * decision_years)
            backtest_result = backtest_strategy(decision_code, start_date, end_date, total_backtest_amount, decision_monthly, decision_strategy)
            if backtest_result:
                market_sentiment = get_market_sentiment()
                market_position = get_market_position()
                timing_signal = get_timing_signal()
                decision_result = ai_investment_decision(decision_code, backtest_result, market_sentiment, market_position, timing_signal)
                if decision_result:
                    st.session_state.decision_result = decision_result
                    st.session_state.backtest_results = backtest_result
                    st.success("✅ AI决策完成！")
                    st.balloons()
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("综合评分", f"{decision_result['total_score']}/100")
                    col2.metric("AI决策", decision_result['action'])
                    col3.metric("回测收益", f"{backtest_result['profit_rate']:.1f}%")
                    col4.metric("胜率", f"{backtest_result['win_rate']:.0f}%")
                    
                    st.subheader("📌 决策详情")
                    if "强烈建议买入" in decision_result['decision']:
                        st.success(f"### {decision_result['decision']}")
                    elif "建议买入" in decision_result['decision']:
                        st.info(f"### {decision_result['decision']}")
                    elif "观望" in decision_result['decision']:
                        st.warning(f"### {decision_result['decision']}")
                    else:
                        st.error(f"### {decision_result['decision']}")
                    st.caption(f"💡 {decision_result['detail']}")
                    
                    st.subheader("💰 资金建议")
                    suggested = total_cash * decision_result['suggested_amount_ratio']
                    col1, col2, col3 = st.columns(3)
                    col1.metric("可用资金", f"{total_cash:.0f}元")
                    col2.metric("建议投入", f"{suggested:.0f}元", delta=f"{decision_result['suggested_amount_ratio']*100:.0f}%")
                    col3.metric("分批建议", f"{suggested/3:.0f}元×3批")
                    
                    st.subheader("📈 当前市场状态")
                    col1, col2, col3 = st.columns(3)
                    col1.info(f"😊 市场情绪：{market_sentiment}")
                    col2.info(f"📊 估值位置：{market_position}%")
                    col3.info(f"🔔 择时信号：{timing_signal}")
            else:
                st.error("回测失败，请重试")
    
    if st.session_state.decision_result:
        with st.expander("📂 上次决策记录", expanded=False):
            r = st.session_state.decision_result
            st.write(f"📅 {r['report_generated']}")
            st.write(f"📌 {r['fund_name']}（{r['fund_code']}）")
            st.write(f"⭐ 综合评分：{r['total_score']}/100")
            st.write(f"🎯 决策：{r['action']}")

# ==================== Tab5: 市场信号 ====================
with tab5:
    st.subheader("📊 市场信号面板")
    market = get_market_sentiment()
    timing = get_timing_signal()
    position = get_market_position()
    col1, col2, col3 = st.columns(3)
    emoji = "😊" if market == "乐观" else "😐" if market == "中性" else "😰"
    col1.metric("市场情绪", f"{emoji} {market}")
    color = "🟢" if timing in ["强烈买入", "买入"] else "🟡" if timing in ["持有"] else "🔴"
    col2.metric("择时信号", f"{color} {timing}")
    col3.metric("估值位置", f"{position}%", delta="低估" if position < 30 else "高估" if position > 70 else "合理")
    st.info(f"💡 当前建议：{timing}信号，市场估值{position}%，{market}情绪")

# ==================== Tab6: 基金超市 ====================
with tab6:
    st.subheader("🗂️ 基金超市")
    st.caption(f"共 {len(FUNDS)} 只基金，覆盖10大风格")
    col1, col2 = st.columns(2)
    with col1:
        style_filter = st.selectbox("风格筛选", ["全部"] + sorted(list(set([f["style"] for f in FUNDS]))))
    with col2:
        risk_filter = st.selectbox("风险筛选", ["全部", "低", "中低", "中", "中高", "高"])
    filtered = FUNDS
    if style_filter != "全部":
        filtered = [f for f in filtered if f["style"] == style_filter]
    if risk_filter != "全部":
        filtered = [f for f in filtered if f["risk"] == risk_filter]
    st.caption(f"📊 显示 {len(filtered)} 只基金")
    for f in filtered[:20]:
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 0.8])
        with col1:
            st.write(f"**{f['name']}**")
            st.caption(f"{f['code']} | {f['style']}")
        with col2:
            st.caption(f"风险：{f['risk']}")
        with col3:
            st.caption(f"近3年：{f['return_3y']}")
        with col4:
            score = calculate_fund_score(f)
            st.caption(f"评分：{score}/100")
        with col5:
            if st.button("➕", key=f"add_{f['code']}"):
                st.session_state.holdings.append({
                    "code": f["code"],
                    "name": f["name"],
                    "amount": 1000,
                    "buy_date": datetime.now().strftime("%Y-%m-%d"),
                    "nav": f["nav"]
                })
                st.success(f"✅ 已添加 {f['name']}")
                st.rerun()
        st.divider()

# ==================== 底部 ====================
st.divider()
st.caption("⚠️ 本系统为学习演示工具，数据均为模拟，不构成投资建议")
st.caption(f"📊 共 {len(FUNDS)} 只基金 | AI基金投顾 Pro")
