import streamlit as st
import json
from datetime import datetime
import time
from openai import OpenAI
import requests
import sqlite3
import os
from typing import Dict, List, Optional, Any
import logging
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 页面配置
st.set_page_config(
    page_title="智能用电分析系统 - AI+能源大赛",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 简化版CSS样式 - 避免DOM冲突
@st.cache_resource
def load_css_styles():
    return """
<style>
    /* 简化版CSS样式 - 避免DOM冲突 */
    .main-header {
        font-size: 2.5rem;
        text-align: center;
        margin-bottom: 0.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #1a56db 0%, #3b82f6 50%, #10b981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.2;
    }
    
    .subtitle {
        font-size: 1.1rem;
        text-align: center;
        color: #64748b;
        margin-bottom: 2rem;
        font-weight: 400;
        line-height: 1.4;
    }
    
    .section-header {
        font-size: 1.6rem;
        color: #1a56db;
        margin: 1.5rem 0 0.8rem 0;
        font-weight: 700;
        padding-bottom: 0.3rem;
        border-bottom: 3px solid #10b981;
    }
    
    .question-card {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(26, 86, 219, 0.08);
        border: 1px solid #e2e8f0;
    }
    
    .service-card {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 0.8rem 0;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 12px rgba(26, 86, 219, 0.06);
    }
    
    .report-container {
        background: linear-gradient(135deg, #f0f4ff 0%, #f8fafc 100%);
        padding: 1.5rem;
        border-radius: 16px;
        margin: 1.5rem 0;
        border: 1px solid #e2e8f0;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #1a56db 0%, #1e3a8a 100%);
        color: white;
        border: none;
        padding: 0.8rem 1.5rem;
        font-size: 1rem;
        border-radius: 10px;
        font-weight: 600;
        width: 100%;
    }
    
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem;
        }
        
        .section-header {
            font-size: 1.4rem;
        }
        
        .question-card {
            padding: 1.2rem;
        }
    }
</style>
"""

class RobotAssistant:
    """修复版的机器人助手 - 避免DOM冲突"""
    
    def __init__(self):
        self.name = "小电宝"
        self.avatar = "🤖"
        self.role = "您的智能用电助手"
        
    def render_assistant(self, current_tab, user_type, answers, services, progress_data=None):
        """使用Streamlit原生组件渲染机器人助手"""
        
        # 使用st.container创建机器人助手区域
        with st.container():
            st.markdown("---")
            
            # 机器人头部
            col1, col2 = st.columns([0.1, 0.9])
            with col1:
                st.markdown(f"<div style='font-size: 2.5rem; text-align: center;'>{self.avatar}</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"**{self.name}** - {self.role}")
            
            st.markdown("---")
            
            # 根据当前标签页显示不同的引导信息
            if current_tab == "questionnaire":
                self._render_questionnaire_guide(user_type, answers)
            elif current_tab == "services":
                self._render_services_guide(services, answers)
            elif current_tab == "analysis":
                self._render_analysis_guide(answers, services, progress_data)
            elif current_tab == "history":
                self._render_history_guide()
            
            st.markdown("---")
    
    def _render_questionnaire_guide(self, user_type, answers):
        """渲染问卷调研引导"""
        if not answers:
            st.info("👋 **嗨！我是小电宝，很高兴为您服务！**\n\n让我来帮您完成用电情况调研，这样我就能为您生成个性化的分析报告啦！\n\n💡 **小贴士：**请根据您的实际情况如实填写，这样我的分析会更准确哦！")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚀 开始填写问卷", key="robot_start_questionnaire"):
                    st.success("开始填写问卷吧！我会一步步指导您的！")
            with col2:
                if st.button("❓ 需要帮助", key="robot_help_questionnaire"):
                    st.info("别担心，我会一步步指导您的！填写问卷时遇到任何问题都可以问我。")
        else:
            total_questions = 7 if user_type == "家庭用户" else 6
            progress = len(answers) / total_questions
            
            if progress < 1.0:
                st.info(f"📝 **问卷填写进度：{progress*100:.0f}%**\n\n您已经完成了{len(answers)}个问题，继续加油！\n\n🎯 **下一步：**请继续完成剩余的问题，然后我们就可以进入服务选择啦！")
            else:
                st.success("🎉 **太棒了！您已经完成了所有问卷问题！**\n\n您的用电画像已经建立完成，接下来让我们选择适合您的智能服务吧！\n\n💡 **建议：**点击上方的'服务定制'标签继续下一步")
                
                if st.button("🔧 前往服务定制", key="robot_to_services"):
                    st.success("正在跳转到服务定制页面...")
    
    def _render_services_guide(self, services, answers):
        """渲染服务选择引导"""
        if not answers:
            st.warning("⏳ **请先完成问卷调研**\n\n我注意到您还没有填写问卷呢！\n\n📋 **建议：**请先点击'问卷调研'标签完成用电情况调研，这样我才能为您推荐合适的服务哦！")
            
            if st.button("📋 前往问卷调研", key="robot_to_questionnaire"):
                st.success("正在跳转到问卷调研页面...")
        elif not services:
            st.info("🔧 **欢迎来到服务定制环节！**\n\n基于您的用电情况，我为您准备了6项智能服务：\n\n• 📊 **智能用电监控** - 实时了解用电情况\n• 💡 **节能优化建议** - AI个性化节能方案\n• ⏰ **峰谷电价策略** - 最大化节省电费\n• 🔌 **设备能效评估** - 发现节能潜力设备\n• 🛡️ **用电安全预警** - 保障用电安全\n• 🌱 **碳足迹分析** - 为环保贡献力量\n\n💡 **小贴士：**您可以根据需求选择多项服务，选择越多节能效果越好哦！")
        else:
            st.success(f"✅ **完美！您已选择 {len(services)} 项服务**\n\n您选择的 **{'、'.join(services)}** 都是很棒的节能选择！\n\n🎯 **下一步：**点击'AI智能分析'标签，让我为您生成专业的用电分析报告！")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📈 生成分析报告", key="robot_generate_report"):
                    st.success("正在准备生成分析报告...")
            with col2:
                if st.button("⚙️ 调整服务", key="robot_adjust_services"):
                    st.info("您可以继续调整服务选择")
    
    def _render_analysis_guide(self, answers, services, progress_data):
        """渲染分析报告引导"""
        if not answers:
            st.warning("📋 **请先完成问卷调研**\n\n我注意到您还没有填写问卷呢！\n\n📝 **建议：**请先点击'问卷调研'标签完成用电情况调研")
        elif not services:
            st.warning("🔧 **请先选择服务**\n\n您已经完成了问卷，但还没有选择任何智能服务呢！\n\n🎯 **建议：**请点击'服务定制'标签选择您需要的服务")
        else:
            if progress_data and progress_data.get('report_generated'):
                st.success("🎊 **恭喜！您的专业用电分析报告已生成！**\n\n报告包含了详细的节能建议、经济效益分析和环境效益评估。\n\n💡 **下一步建议：**\n• 仔细阅读报告内容\n• 下载报告保存\n• 查看历史记录对比不同方案")
            else:
                st.info("🧠 **准备生成智能分析报告**\n\n一切准备就绪！基于您的问卷数据和服务选择，我将为您生成：\n\n• 📈 个性化用电分析\n• 💰 经济效益评估\n• 🌍 环境效益计算\n• 🎯 具体实施建议\n\n💡 **小贴士：**点击下方按钮，让我开始为您生成专业的分析报告吧！")
    
    def _render_history_guide(self):
        """渲染历史记录引导"""
        st.info("📚 **历史记录查看**\n\n在这里您可以查看之前生成的所有分析报告。\n\n💡 **功能说明：**\n• 查看历史分析记录\n• 对比不同时间点的报告\n• 重新加载之前的分析\n\n🎯 **建议：**如果您是第一次使用，请先完成问卷调研生成第一份报告！")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🆕 开始新的分析", key="robot_new_analysis"):
                st.success("正在跳转到问卷调研页面...")
        with col2:
            if st.button("📖 了解历史功能", key="robot_learn_history"):
                st.info("历史记录功能让您可以：\n- 查看之前的所有分析报告\n- 对比不同时期的用电情况\n- 跟踪节能效果变化\n- 重新使用之前的配置")

class EnergyAnalytics:
    """能源分析引擎 - 负责生成波形图和环境影响数据"""
    
    def __init__(self):
        self.carbon_factors = {
            'coal': 0.997,  # kg CO2/kWh
            'renewable': 0.033  # kg CO2/kWh
        }
    
    def estimate_consumption(self, user_data: Dict, user_type: str) -> float:
        """估算年用电量"""
        if user_type == "家庭用户":
            bill_ranges = {'A': 600, 'B': 1800, 'C': 3000, 'D': 6000}  # kWh/年
            bill_key = user_data.get('electricity_bill', 'B')
            return bill_ranges.get(bill_key, 1800)
        else:
            bill_ranges = {'A': 60000, 'B': 240000, 'C': 1200000, 'D': 6000000}
            bill_key = user_data.get('monthly_bill', 'B')
            return bill_ranges.get(bill_key, 240000)
    
    def calculate_savings_potential(self, user_data: Dict, services: List[str], user_type: str) -> Dict:
        """计算节能潜力"""
        base_consumption = self.estimate_consumption(user_data, user_type)
        
        # 更精确的服务节能潜力系数
        savings_potential = {
            "智能用电监控": 0.08,    # 实时监控可节省8%
            "节能优化建议": 0.12,    # AI优化建议可节省12%
            "峰谷电价策略": 0.15,    # 峰谷电价优化可节省15%
            "设备能效评估": 0.10,    # 设备评估升级可节省10%
            "用电安全预警": 0.05,    # 安全预警减少浪费可节省5%
            "碳足迹分析": 0.03       # 碳足迹意识可节省3%
        }
        
        # 计算总节能比例（有重叠效应，不是简单相加）
        total_savings = 0
        for service in services:
            total_savings += savings_potential.get(service, 0)
        
        # 考虑服务间的重叠效应，最大不超过40%
        total_savings = min(total_savings, 0.40)
        
        annual_savings_kwh = base_consumption * total_savings
        annual_co2_reduction = annual_savings_kwh * self.carbon_factors['coal']
        
        # 计算电费节省（假设平均电价0.6元/kWh）
        electricity_price = 0.6
        annual_savings_yuan = annual_savings_kwh * electricity_price
        
        return {
            'annual_savings_kwh': annual_savings_kwh,
            'annual_co2_reduction': annual_co2_reduction,
            'savings_percentage': total_savings * 100,
            'base_consumption': base_consumption,
            'annual_savings_yuan': annual_savings_yuan
        }
    
    def generate_energy_chart(self, user_data: Dict, savings_data: Dict):
        """生成能源使用波形图"""
        hours = list(range(24))
        
        # 生成基础能耗曲线（模拟数据）
        if user_data.get('usage_pattern') == 'A':  # 晚上用电多
            baseline = [30 + 40 * np.sin(2 * np.pi * (h - 18) / 24) + np.random.normal(0, 5) for h in hours]
        elif user_data.get('usage_pattern') == 'C':  # 白天用电多
            baseline = [30 + 40 * np.sin(2 * np.pi * (h - 12) / 24) + np.random.normal(0, 5) for h in hours]
        else:  # 均匀用电
            baseline = [50 + 20 * np.sin(2 * np.pi * (h - 12) / 24) + np.random.normal(0, 3) for h in hours]
        
        baseline = [max(10, x) for x in baseline]  # 确保最小值
        
        # 生成优化后曲线（按节能比例降低）
        savings_factor = 1 - (savings_data['savings_percentage'] / 100)
        optimized = [x * savings_factor for x in baseline]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=hours, y=baseline,
            mode='lines',
            name='优化前',
            line=dict(color='red', width=3),
            fill='tozeroy',
            fillcolor='rgba(255,0,0,0.1)'
        ))
        
        fig.add_trace(go.Scatter(
            x=hours, y=optimized,
            mode='lines',
            name='优化后',
            line=dict(color='green', width=3),
            fill='tozeroy',
            fillcolor='rgba(0,255,0,0.1)'
        ))
        
        fig.update_layout(
            title="24小时能耗模拟对比分析",
            xaxis_title="时间 (小时)",
            yaxis_title="功率 (kW)",
            height=400,
            showlegend=True,
            template="plotly_white"
        )
        
        return fig
    
    def generate_environmental_impact(self, savings_data: Dict):
        """生成环境影响数据"""
        co2_reduction = savings_data['annual_co2_reduction']
        
        # 转换为易于理解的指标
        tree_equivalents = co2_reduction / 22  # 一棵树年吸收约22kg CO2
        car_equivalents = co2_reduction / 4200  # 一辆车年排放约4200kg CO2
        
        return {
            'co2_reduction_kg': co2_reduction,
            'tree_equivalents': tree_equivalents,
            'car_equivalents': car_equivalents,
            'electricity_savings': savings_data['annual_savings_kwh'],
            'annual_savings_yuan': savings_data['annual_savings_yuan']
        }

class DatabaseManager:
    """数据库管理类 - 负责数据持久化"""
    
    def __init__(self, db_path="user_data.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表结构"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_type TEXT NOT NULL,
                    answers TEXT NOT NULL,
                    services TEXT NOT NULL,
                    report_content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("数据库初始化成功")
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
    
    def save_analysis_record(self, user_type: str, answers: Dict, services: List[str], report_content: str = None) -> int:
        """保存分析记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO analysis_records (user_type, answers, services, report_content)
                VALUES (?, ?, ?, ?)
            ''', (user_type, json.dumps(answers, ensure_ascii=False), 
                  json.dumps(services, ensure_ascii=False), report_content))
            
            record_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"分析记录保存成功，ID: {record_id}")
            return record_id
        except Exception as e:
            logger.error(f"保存分析记录失败: {str(e)}")
            return None
    
    def get_analysis_history(self, limit: int = 10) -> List[Dict]:
        """获取分析历史记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, user_type, answers, services, created_at, report_content
                FROM analysis_records 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            records = []
            for row in cursor.fetchall():
                records.append({
                    'id': row[0],
                    'user_type': row[1],
                    'answers': json.loads(row[2]),
                    'services': json.loads(row[3]),
                    'created_at': row[4],
                    'report_content': row[5]
                })
            
            conn.close()
            return records
        except Exception as e:
            logger.error(f"获取分析历史失败: {str(e)}")
            return []

class AIService:
    """AI服务类 - 负责与AI API交互"""
    
    def __init__(self):
        # 在这里设置你的API密钥 - 请替换为真实的API密钥
        self.api_keys = {
            "OpenAI": "sk-your-openai-api-key-here",  # 请替换为你的OpenAI API密钥
            "ModelScope": "your-modelscope-api-key-here"  # 请替换为你的ModelScope API密钥
        }
        
        self.api_configs = {
            "ModelScope": {
                "base_url": "https://api-inference.modelscope.cn/v1/",
                "model": "qwen/Qwen2.5-72B-Instruct"
            },
            "OpenAI": {
                "base_url": None,
                "model": "gpt-3.5-turbo"
            }
        }
    
    def call_ai_api(self, prompt: str, api_type: str = "OpenAI") -> Optional[str]:
        """调用AI API生成报告 - 使用内置API密钥"""
        api_key = self.api_keys.get(api_type)
        
        if not api_key or api_key.startswith("sk-your-") or api_key.startswith("your-"):
            st.error(f"❌ 请配置有效的{api_type} API密钥")
            return None
        
        if api_type not in self.api_configs:
            st.error(f"❌ 不支持的API类型: {api_type}")
            return None
        
        config = self.api_configs[api_type]
        
        try:
            client = OpenAI(
                api_key=api_key,
                base_url=config.get("base_url")
            )
            
            # 显示生成进度
            progress_placeholder = st.empty()
            progress_bar = progress_placeholder.progress(0)
            status_text = st.empty()
            
            status_text.text(f"🔄 连接{api_type}模型...")
            progress_bar.progress(20)
            
            response = client.chat.completions.create(
                model=config["model"],
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的能源管理专家，擅长用电分析和节能优化。请提供详细、专业、可操作性强的建议。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                stream=True,
                max_tokens=2000,
                temperature=0.7
            )
            
            status_text.text("🧠 AI正在生成专业报告...")
            progress_bar.progress(40)
            
            report = ""
            progress = 40
            
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    report += chunk.choices[0].delta.content
                    progress = min(90, progress + 1)
                    progress_bar.progress(progress)
            
            progress_bar.progress(100)
            status_text.text("✅ 报告生成完成！")
            time.sleep(0.5)
            progress_placeholder.empty()
            status_text.empty()
            
            return report
            
        except Exception as e:
            logger.error(f"{api_type} API调用失败: {str(e)}")
            st.error(f"❌ {api_type} API调用失败: {str(e)}")
            return None

class QuestionnaireManager:
    """问卷管理类 - 负责问卷数据的处理"""
    
    def __init__(self):
        self.initialize_questions()
    
    def initialize_questions(self):
        """初始化所有问卷问题"""
        self.family_questions = [
            {
                "id": "address",
                "question": "您的详细地址？",
                "type": "text_input",
                "required": True,
                "icon": "📍",
                "placeholder": "请输入您的详细地址（省市区街道门牌号）"
            },
            {
                "id": "house_type",
                "question": "您的住宅类型是？",
                "options": {
                    "A": "公寓（100平米以下）",
                    "B": "普通住宅（100-150平米）", 
                    "C": "大户型/别墅（150平米以上）",
                    "D": "其他特殊类型"
                },
                "required": True,
                "icon": "🏠"
            },
            {
                "id": "family_size", 
                "question": "您的家庭成员人数？",
                "options": {
                    "A": "1-2人",
                    "B": "3-4人",
                    "C": "5人以上",
                    "D": "独居"
                },
                "required": True,
                "icon": "👨‍👩‍👧‍👦"
            },
            {
                "id": "electricity_bill",
                "question": "您每月电费大约是多少？",
                "options": {
                    "A": "100元以下",
                    "B": "100-300元", 
                    "C": "300-500元",
                    "D": "500元以上"
                },
                "required": True,
                "icon": "💰"
            },
            {
                "id": "usage_pattern",
                "question": "您家的主要用电时段？",
                "options": {
                    "A": "主要集中在晚上（18:00-24:00）",
                    "B": "全天均匀用电",
                    "C": "白天用电较多（8:00-18:00）",
                    "D": "不确定或特殊时段"
                },
                "required": True,
                "icon": "⏰"
            },
            {
                "id": "appliances",
                "question": "您家有哪些大功率电器？",
                "options": {
                    "A": "空调（多台或中央空调）",
                    "B": "电热水器/即热式热水器",
                    "C": "电动汽车充电桩",
                    "D": "大功率厨房电器（烤箱、蒸箱等）",
                    "E": "其他大功率设备"
                },
                "multiple": True,
                "required": False,
                "icon": "🔌"
            },
            {
                "id": "energy_saving",
                "question": "您对节能省电的态度是？",
                "options": {
                    "A": "非常重视，愿意投资节能设备",
                    "B": "比较重视，会注意用电习惯",
                    "C": "一般关注，顺其自然",
                    "D": "不太关注，更注重舒适度"
                },
                "required": True,
                "icon": "🌱"
            }
        ]
        
        self.enterprise_questions = [
            {
                "id": "address",
                "question": "企业详细地址？",
                "type": "text_input",
                "required": True,
                "icon": "🏢",
                "placeholder": "请输入企业详细地址（省市区街道门牌号）"
            },
            {
                "id": "business_type",
                "question": "您的企业类型是？",
                "options": {
                    "A": "制造业/工厂",
                    "B": "办公楼/写字楼",
                    "C": "商场/零售业",
                    "D": "数据中心/科技公司",
                    "E": "其他服务业"
                },
                "required": True,
                "icon": "🏢"
            },
            {
                "id": "scale",
                "question": "企业规模如何？",
                "options": {
                    "A": "小型企业（50人以下）",
                    "B": "中型企业（50-200人）",
                    "C": "大型企业（200-1000人）",
                    "D": "超大型企业（1000人以上）"
                },
                "required": True,
                "icon": "📊"
            },
            {
                "id": "monthly_bill",
                "question": "月均电费支出？",
                "options": {
                    "A": "5000元以下",
                    "B": "5000-20000元",
                    "C": "2万-10万元", 
                    "D": "10万元以上"
                },
                "required": True,
                "icon": "💳"
            },
            {
                "id": "operation_hours",
                "question": "每日运营时间？",
                "options": {
                    "A": "8小时以内（标准工作日）",
                    "B": "8-12小时（延长运营）", 
                    "C": "12-16小时（两班制）",
                    "D": "24小时运营（三班制）"
                },
                "required": True,
                "icon": "🕒"
            },
            {
                "id": "equipment",
                "question": "主要用电设备？",
                "options": {
                    "A": "生产设备/机械设备",
                    "B": "中央空调系统",
                    "C": "照明系统", 
                    "D": "服务器/IT设备",
                    "E": "其他专用设备"
                },
                "multiple": True,
                "required": False,
                "icon": "⚙️"
            }
        ]
    
    def validate_answers(self, answers: Dict, user_type: str) -> tuple:
        """验证答案完整性"""
        questions = self.family_questions if user_type == "家庭用户" else self.enterprise_questions
        
        missing_questions = []
        for question in questions:
            if question.get("required", False) and question["id"] not in answers:
                missing_questions.append(question["question"])
            elif question["id"] in answers and not answers[question["id"]]:
                missing_questions.append(question["question"])
        
        if missing_questions:
            return False, f"请完成以下必填问题：{'、'.join(missing_questions)}"
        
        return True, "验证通过"

class UIRenderer:
    """UI渲染类 - 负责界面显示"""
    
    def __init__(self):
        self.services = {
            "智能用电监控": {
                "description": "实时监测用电行为，识别异常能耗",
                "implementation": "安装智能电表和传感器，通过手机App实时查看用电数据"
            },
            "节能优化建议": {
                "description": "基于AI算法的个性化节能方案",
                "implementation": "AI分析用电习惯，提供具体的设备使用优化建议"
            },
            "峰谷电价策略": {
                "description": "智能分析最佳用电时段，最大化节省电费",
                "implementation": "根据当地峰谷电价政策，智能规划高能耗设备运行时间"
            },
            "设备能效评估": {
                "description": "全面评估电器设备能效，提供升级建议",
                "implementation": "专业设备检测，推荐能效更高的替代产品"
            },
            "用电安全预警": {
                "description": "智能识别安全隐患，预防用电事故",
                "implementation": "实时监测电路状态，异常情况立即报警"
            },
            "碳足迹分析": {
                "description": "计算碳排放，提供碳中和路径建议",
                "implementation": "量化碳足迹，提供减排方案和碳交易建议"
            }
        }
    
    def render_question(self, question: Dict, question_number: int) -> Any:
        """渲染单个问题"""
        with st.container():
            st.markdown(f'<div class="question-card">', unsafe_allow_html=True)
            
            col1, col2 = st.columns([0.1, 0.9])
            with col1:
                st.markdown(f"<div style='font-size: 2rem;'>{question.get('icon', '❓')}</div>", unsafe_allow_html=True)
            with col2:
                required_flag = " *" if question.get("required", False) else ""
                st.markdown(f"<h3 style='color: #1a56db; margin:0;'>问题 {question_number}{required_flag}</h3>", unsafe_allow_html=True)
                st.markdown(f"<p style='font-size: 1.3rem; margin: 0.5rem 0 1.5rem 0; font-weight: 500; line-height: 1.5;'>{question['question']}</p>", unsafe_allow_html=True)
            
            # 处理文本输入类型的问题
            if question.get('type') == 'text_input':
                placeholder = question.get('placeholder', '请输入...')
                answer = st.text_input(
                    f"请输入（问题{question_number}）",
                    placeholder=placeholder,
                    key=question['id'],
                    label_visibility="collapsed"
                )
                st.markdown('</div>', unsafe_allow_html=True)
                return answer
            
            # 处理单选/多选类型的问题
            if not question.get('multiple', False):
                selected = st.radio(
                    f"选择答案（问题{question_number}）",
                    options=list(question['options'].keys()),
                    format_func=lambda x: f"{x}. {question['options'][x]}",
                    key=question['id'],
                    horizontal=False
                )
                st.markdown('</div>', unsafe_allow_html=True)
                return selected
            else:
                selected_options = []
                st.markdown("<p style='font-weight: 600; margin-bottom: 1rem;'>请选择所有适用的选项：</p>", unsafe_allow_html=True)
                
                cols = st.columns(2)
                for i, (option_key, option_text) in enumerate(question['options'].items()):
                    with cols[i % 2]:
                        if st.checkbox(f"**{option_key}.** {option_text}", key=f"{question['id']}_{option_key}"):
                            selected_options.append(option_key)
                
                st.markdown('</div>', unsafe_allow_html=True)
                return selected_options
    
    def render_service_selection(self) -> List[str]:
        """渲染服务选择界面"""
        st.markdown("### 🔧 定制服务选择")
        st.markdown("请选择您需要的智能用电服务，我们将根据您的选择提供精准的解决方案。")
        
        selected_services = []
        
        cols = st.columns(2)
        for i, (service, service_info) in enumerate(self.services.items()):
            with cols[i % 2]:
                with st.container():
                    st.markdown(f"""
                    <div class='service-card'>
                        <h4 style='color: #1a56db; margin: 0 0 0.5rem 0; display: flex; align-items: center;'>
                            <span style='margin-right: 0.5rem;'>🔹</span>{service}
                        </h4>
                        <p style='color: #64748b; font-size: 0.95rem; margin: 0; line-height: 1.5;'>{service_info['description']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.checkbox(f"选择【{service}】", key=f"service_{i}"):
                        selected_services.append(service)
        
        if selected_services:
            st.success(f"✅ **已选择 {len(selected_services)} 项服务**\n\n{'、'.join(selected_services)}")
            
            # 显示服务实施方式
            st.markdown("#### 🛠️ 服务实施方式")
            for service in selected_services:
                with st.expander(f"{service} - 实施方式", expanded=False):
                    st.info(f"**实施方式:** {self.services[service]['implementation']}")
        
        return selected_services

class PowerAnalysisApp:
    """主应用类 - 协调各个组件"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.ai_service = AIService()
        self.questionnaire_manager = QuestionnaireManager()
        self.ui_renderer = UIRenderer()
        self.energy_analytics = EnergyAnalytics()
        self.robot_assistant = RobotAssistant()
        
        # 初始化会话状态
        if 'progress_data' not in st.session_state:
            st.session_state.progress_data = {
                'report_generated': False,
                'current_step': 'questionnaire'
            }
    
    def collect_family_questionnaire(self) -> Dict:
        """收集家庭用户问卷"""
        st.markdown("### 🏠 家庭用电情况调研")
        st.markdown("请根据您的实际情况填写以下问卷，我们将为您生成个性化的用电分析报告。")
        
        answers = {}
        for i, question in enumerate(self.questionnaire_manager.family_questions, 1):
            answer = self.ui_renderer.render_question(question, i)
            answers[question['id']] = answer
        
        progress = len(answers) / len(self.questionnaire_manager.family_questions)
        st.progress(progress)
        st.markdown(f"**问卷进度: {len(answers)}/{len(self.questionnaire_manager.family_questions)}**")
        
        return answers
    
    def collect_enterprise_questionnaire(self) -> Dict:
        """收集企业用户问卷"""
        st.markdown("### 🏢 企业用电情况调研")
        st.markdown("请根据贵企业的实际情况填写以下问卷，我们将为您提供专业的能源管理解决方案。")
        
        answers = {}
        for i, question in enumerate(self.questionnaire_manager.enterprise_questions, 1):
            answer = self.ui_renderer.render_question(question, i)
            answers[question['id']] = answer
        
        progress = len(answers) / len(self.questionnaire_manager.enterprise_questions)
        st.progress(progress)
        st.markdown(f"**问卷进度: {len(answers)}/{len(self.questionnaire_manager.enterprise_questions)}**")
        
        return answers
    
    def generate_ai_prompt(self, user_type: str, answers: Dict, services: List[str], savings_data: Dict, environmental_data: Dict) -> str:
        """生成专业的AI提示词"""
        user_type_text = user_type
        
        if user_type == "家庭用户":
            questions = self.questionnaire_manager.family_questions
        else:
            questions = self.questionnaire_manager.enterprise_questions
        
        answers_analysis = "## 用户用电画像分析\n\n"
        for q in questions:
            q_id = q['id']
            if q_id in answers:
                answer = answers[q_id]
                if isinstance(answer, list):
                    answer_text = "、".join([f"{opt}. {q['options'][opt]}" for opt in answer])
                else:
                    if q.get('type') == 'text_input':
                        answer_text = answer
                    else:
                        answer_text = f"{answer}. {q['options'][answer]}"
                
                answers_analysis += f"- **{q['question']}**\n  - {answer_text}\n"
        
        # 添加精确的节能数据分析
        savings_analysis = f"""
## 精确节能潜力分析（请务必在报告中准确使用这些数据）

### 基础用电情况
- 基础年用电量: {savings_data['base_consumption']:.0f} kWh
- 节能比例: {savings_data['savings_percentage']:.1f}%

### 经济效益
- 预计年节电量: {savings_data['annual_savings_kwh']:.0f} kWh
- 年节省电费: ¥{savings_data['annual_savings_yuan']:.0f} 元
- 5年总节省电费: ¥{savings_data['annual_savings_yuan'] * 5:.0f} 元

### 环境效益
- 年减少碳排放: {savings_data['annual_co2_reduction']:.1f} kg
- 等效植树: {environmental_data['tree_equivalents']:.0f} 棵
- 等效减少汽车: {environmental_data['car_equivalents']:.1f} 辆年排放

### 所选服务详情
选择的服务: {', '.join(services)}
"""
        
        prompt = f"""
# 智能用电分析专家任务

## 角色定位
您是拥有15年经验的能源管理专家，专精于智能用电分析和节能优化。请基于用户数据生成专业报告。

## 用户基本信息
- **用户类型**: {user_type_text}
- **需求服务**: {', '.join(services)}

## 详细用户数据
{answers_analysis}

{savings_analysis}

## 重要说明
**请务必在报告中准确使用上述"精确节能潜力分析"部分的所有数据，不要自行估算或修改任何数字。**

## 报告要求
请生成一份专业、详细、可操作性强的用电分析报告，包含以下内容：

### 1. 执行摘要
- 关键发现和主要建议
- 预期节省（电费和电量）- 使用上面提供的准确数据
- 环境效益（碳减排等）- 使用上面提供的准确数据

### 2. 用电现状深度分析
- 当前用电模式特点
- 能效水平评估
- 主要问题和改进机会

### 3. 个性化优化方案
- 具体可操作的节能措施
- 设备使用优化建议
- 行为习惯改进方案

### 4. 经济效益分析
- 预计节省金额（月度/年度）- 使用上面提供的准确数据
- 投资回报周期
- 成本效益分析

### 5. 实施路线图
- 分阶段实施计划
- 优先级排序
- 预期时间表

### 6. 环境效益
- 碳减排估算 - 使用上面提供的准确数据
- 可持续发展贡献
- 绿色价值体现

## 专业要求
- 数据驱动：必须使用上面提供的准确数据
- 可行性：建议要切实可行
- 专业性：使用能源管理专业术语
- 个性化：紧密结合用户具体情况

请生成详细、专业的分析报告（约1200-1500字），确保所有数字与上面提供的数据完全一致：
"""
        return prompt
    
    def render_energy_analytics(self, user_data: Dict, services: List[str], user_type: str):
        """渲染能源分析图表和环境影响数据"""
        st.markdown("### 📊 能源分析与环境影响")
        
        # 计算节能潜力
        savings_data = self.energy_analytics.calculate_savings_potential(user_data, services, user_type)
        environmental_data = self.energy_analytics.generate_environmental_impact(savings_data)
        
        # 显示能源波形图
        st.markdown("#### ⚡ 24小时能耗模拟")
        energy_chart = self.energy_analytics.generate_energy_chart(user_data, savings_data)
        st.plotly_chart(energy_chart, use_container_width=True)
        
        # 显示环境影响指标
        st.markdown("#### 🌍 环境效益分析")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "年节电量", 
                f"{savings_data['annual_savings_kwh']:.0f} kWh",
                delta=f"{savings_data['savings_percentage']:.1f}%"
            )
        
        with col2:
            st.metric(
                "碳减排量", 
                f"{environmental_data['co2_reduction_kg']/1000:.1f} 吨",
                help="相当于减少的二氧化碳排放量"
            )
        
        with col3:
            st.metric(
                "等效树木", 
                f"{environmental_data['tree_equivalents']:.0f} 棵",
                help="相当于种植的树木数量"
            )
        
        with col4:
            st.metric(
                "等效汽车", 
                f"{environmental_data['car_equivalents']:.1f} 辆",
                help="相当于减少的汽车年排放"
            )
        
        # 显示经济效益
        st.markdown("#### 💰 经济效益分析")
        
        electricity_price = 0.6  # 元/kWh
        annual_savings_yuan = savings_data['annual_savings_kwh'] * electricity_price
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("年节省电费", f"¥{annual_savings_yuan:.0f}")
        
        with col2:
            st.metric("5年总节省", f"¥{annual_savings_yuan * 5:.0f}")
        
        with col3:
            investment = 5000  # 假设投资成本
            payback_period = investment / annual_savings_yuan if annual_savings_yuan > 0 else float('inf')
            st.metric("投资回收期", f"{payback_period:.1f} 年")
        
        return savings_data, environmental_data
    
    def render_sidebar(self) -> tuple:
        """渲染侧边栏"""
        with st.sidebar:
            st.markdown("""
            <div style='text-align: center; padding: 0.8rem 0;'>
                <h2 style='color: #1a56db; margin: 0; font-size: 1.2rem;'>🔧 系统配置</h2>
                <p style='color: #64748b; margin: 0.3rem 0 0 0; font-size: 0.8rem;'>专业能源分析平台</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("#### 🤖 AI服务配置")
            
            api_type = st.selectbox(
                "选择AI服务提供商",
                ["OpenAI", "ModelScope"],
                help="选择AI服务提供商"
            )
            
            st.markdown("#### 📊 系统状态")
            
            st.markdown("""
            <div style="display: flex; flex-direction: column; gap: 0.5rem; margin: 1rem 0;">
                <div style="background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); border: 1px solid #e2e8f0; border-radius: 8px; padding: 0.8rem; text-align: center;">
                    <span style="font-size: 0.75rem; color: #64748b; font-weight: 600; margin-bottom: 0.3rem; display: block;">系统版本</span>
                    <span style="font-size: 0.9rem; color: #1e293b; font-weight: 700; display: block;">v2.1</span>
                </div>
                <div style="background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); border: 1px solid #e2e8f0; border-radius: 8px; padding: 0.8rem; text-align: center;">
                    <span style="font-size: 0.75rem; color: #64748b; font-weight: 600; margin-bottom: 0.3rem; display: block;">AI服务</span>
                    <span style="font-size: 0.9rem; color: #3b82f6; font-weight: 700; display: block;">已配置</span>
                </div>
                <div style="background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); border: 1px solid #e2e8f0; border-radius: 8px; padding: 0.8rem; text-align: center;">
                    <span style="font-size: 0.75rem; color: #64748b; font-weight: 600; margin-bottom: 0.3rem; display: block;">服务状态</span>
                    <span style="font-size: 0.9rem; color: #10b981; font-weight: 700; display: block;">在线</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("#### 👥 用户类型")
            user_type = st.radio(
                "选择分析类型",
                ["家庭用户", "企业用户"],
                help="根据您的需求选择合适的分析类型"
            )
            
            st.markdown("---")
            st.markdown("""
            <div style='background: linear-gradient(135deg, #dbeafe 0%, #93c5fd 100%); border: 1px solid #3b82f6; border-radius: 10px; padding: 0.8rem;'>
                <h4 style='font-size: 0.9rem;'>💡 系统特色功能</h4>
                <ul style='margin: 0.3rem 0 0 0; padding-left: 1rem; font-size: 0.75rem;'>
                    <li>AI智能分析</li>
                    <li>个性化方案</li>
                    <li>专业级报告</li>
                    <li>实时优化建议</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            return user_type, api_type
    
    def render_history_tab(self):
        """渲染历史记录标签页"""
        st.markdown("### 📚 分析历史记录")
        
        history_records = self.db_manager.get_analysis_history(limit=10)
        
        if not history_records:
            st.info("**暂无历史记录**\n\n您还没有生成过分析报告，请先完成问卷调研并生成报告。")
            return
        
        for record in history_records:
            with st.expander(f"📅 {record['created_at']} - {record['user_type']}", expanded=False):
                st.write(f"**用户类型:** {record['user_type']}")
                st.write(f"**选择服务:** {', '.join(record['services'])}")
                st.write(f"**创建时间:** {record['created_at']}")
                
                if record['report_content']:
                    with st.expander("查看报告内容", expanded=False):
                        st.markdown(record['report_content'][:500] + "..." if len(record['report_content']) > 500 else record['report_content'])
    
    def main(self):
        """主应用逻辑"""
        # 应用标题
        st.markdown("""
        <div style='text-align: center; padding: 2rem 0 1.5rem 0;'>
            <h1 class='main-header'>⚡ 智能用电分析系统</h1>
            <p class='subtitle'>基于AI技术的专业能源管理解决方案 | AI+能源大赛参赛作品</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 加载CSS样式
        st.markdown(load_css_styles(), unsafe_allow_html=True)
        
        # 渲染侧边栏
        user_type, api_type = self.render_sidebar()
        
        # 主内容区域 - 使用选项卡
        tabs = st.tabs(["📋 问卷调研", "🔧 服务定制", "📊 AI智能分析", "📚 历史记录"])
        
        with tabs[0]:
            st.markdown('<div class="tab-content">', unsafe_allow_html=True)
            
            # 显示机器人助手
            answers = st.session_state.get('family_answers' if user_type == "家庭用户" else 'enterprise_answers', {})
            self.robot_assistant.render_assistant("questionnaire", user_type, answers, [])
            
            if user_type == "家庭用户":
                if 'family_answers' not in st.session_state:
                    st.session_state.family_answers = {}
                st.session_state.family_answers = self.collect_family_questionnaire()
            else:
                if 'enterprise_answers' not in st.session_state:
                    st.session_state.enterprise_answers = {}
                st.session_state.enterprise_answers = self.collect_enterprise_questionnaire()
            st.markdown('</div>', unsafe_allow_html=True)
        
        with tabs[1]:
            st.markdown('<div class="tab-content">', unsafe_allow_html=True)
            
            # 显示机器人助手
            answers = st.session_state.get('family_answers' if user_type == "家庭用户" else 'enterprise_answers', {})
            services = st.session_state.get('services', [])
            self.robot_assistant.render_assistant("services", user_type, answers, services)
            
            if 'services' not in st.session_state:
                st.session_state.services = []
            st.session_state.services = self.ui_renderer.render_service_selection()
            st.markdown('</div>', unsafe_allow_html=True)
        
        with tabs[2]:
            st.markdown('<div class="tab-content">', unsafe_allow_html=True)
            
            # 显示机器人助手
            answers = st.session_state.get('family_answers' if user_type == "家庭用户" else 'enterprise_answers', {})
            services = st.session_state.get('services', [])
            self.robot_assistant.render_assistant("analysis", user_type, answers, services, st.session_state.progress_data)
            
            st.markdown("### 📈 AI智能分析报告")
            
            st.info("🎯 **专业AI分析引擎**\n\n我们的AI系统结合了先进的机器学习算法和专业的能源管理知识，为您提供精准、个性化的用电分析报告。")
            
            # 检查数据完整性
            answers = st.session_state.get('family_answers' if user_type == "家庭用户" else 'enterprise_answers', {})
            services = st.session_state.get('services', [])
            
            if not answers:
                st.warning("⚠️ **需要完成问卷**\n\n请先完成问卷调研以生成分析报告。")
            elif not services:
                st.warning("⚠️ **需要选择服务**\n\n请至少选择一项服务以生成分析报告。")
            else:
                is_valid, validation_msg = self.questionnaire_manager.validate_answers(answers, user_type)
                
                if not is_valid:
                    st.warning(f"⚠️ **数据验证失败**\n\n{validation_msg}")
                else:
                    st.success("✅ **数据准备就绪**\n\n已收集完整的问卷数据和服务选择，可以生成AI分析报告。")
            
            if st.button("🚀 生成AI智能分析报告", type="primary", use_container_width=True):
                if not answers:
                    st.error("❌ 请先完成问卷调研！")
                    return
                if not services:
                    st.error("❌ 请至少选择一项服务！")
                    return
                
                is_valid, validation_msg = self.questionnaire_manager.validate_answers(answers, user_type)
                if not is_valid:
                    st.error(f"❌ {validation_msg}")
                    return
                
                try:
                    user_data_for_analytics = answers.copy()
                    
                    savings_data, environmental_data = self.render_energy_analytics(user_data_for_analytics, services, user_type)
                    
                    with st.spinner("🔄 准备分析数据..."):
                        prompt = self.generate_ai_prompt(user_type, answers, services, savings_data, environmental_data)
                    
                    with st.expander("📋 查看分析数据预览", expanded=False):
                        st.text_area("AI分析提示词", prompt, height=200)
                    
                    report = self.ai_service.call_ai_api(prompt, api_type)
                    
                    if report:
                        record_id = self.db_manager.save_analysis_record(user_type, answers, services, report)
                        
                        st.session_state.progress_data['report_generated'] = True
                        
                        st.markdown("### 📄 专业用电分析报告")
                        st.markdown(f"**生成时间：** {datetime.now().strftime('%Y年%m月%d日 %H:%M')}")
                        st.markdown(f"**用户类型：** {user_type}")
                        st.markdown(f"**记录ID：** {record_id}")
                        
                        st.markdown("#### 📊 关键数据摘要")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("年节电量", f"{savings_data['annual_savings_kwh']:.0f} kWh")
                        with col2:
                            st.metric("年节省电费", f"¥{savings_data['annual_savings_yuan']:.0f}")
                        with col3:
                            st.metric("碳减排量", f"{savings_data['annual_co2_reduction']/1000:.1f} 吨")
                        
                        st.markdown('<div class="report-container">', unsafe_allow_html=True)
                        st.markdown(report)
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.download_button(
                                label="📥 下载分析报告",
                                data=report,
                                file_name=f"智能用电分析报告_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                                mime="text/markdown",
                                use_container_width=True
                            )
                        with col2:
                            if st.button("🔄 重新生成报告", use_container_width=True):
                                st.rerun()
                    else:
                        st.error("❌ 报告生成失败，请检查API密钥配置")
                        
                except Exception as e:
                    st.error(f"❌ 报告生成失败: {str(e)}")
                    logger.error(f"报告生成失败: {str(e)}")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with tabs[3]:
            st.markdown('<div class="tab-content">', unsafe_allow_html=True)
            
            # 显示机器人助手
            self.robot_assistant.render_assistant("history", user_type, {}, [])
            
            self.render_history_tab()
            st.markdown('</div>', unsafe_allow_html=True)

def main():
    """主函数"""
    try:
        app = PowerAnalysisApp()
        app.main()
    except Exception as e:
        st.error(f"应用启动失败: {str(e)}")
        logger.error(f"应用启动失败: {str(e)}")
        # 提供重新加载的选项
        if st.button("重新加载应用"):
            st.rerun()

if __name__ == "__main__":
    main()