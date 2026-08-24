"""
广州海洋经济信号灯仪表板 V2
产业分类+多维信号交叉矩阵架构
广州海洋发展促进中心 | 胜哥项目

核心架构: 四大门 → 13纲 → 36目 → 细分科
六维信号: 资金流|物流|市场主体|产业链|环境风险|政策

技术栈: Streamlit + Plotly + Python
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import json
from datetime import datetime

# 导入重构后的数据模块
from data_fetchers import OceanDataManager

# 设置页面
st.set_page_config(
    page_title="广州海洋经济信号灯仪表板 V2",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== 加载产业分类树 ==========
@st.cache_data
def load_industry_tree():
    """加载产业分类JSON"""
    try:
        with open('industry_tree.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"加载产业分类数据失败: {e}")
        return None

# ========== CSS样式 ==========
st.markdown("""
<style>
    /* 信号灯样式 */
    .signal-container {
        display: flex;
        justify-content: center;
        gap: 10px;
        padding: 10px;
    }
    .signal-light {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        border: 3px solid #333;
        box-shadow: 0 0 15px rgba(0,0,0,0.3);
        display: inline-block;
    }
    .signal-green {
        background: radial-gradient(circle at 30% 30%, #4ade80, #16a34a);
    }
    .signal-yellow {
        background: radial-gradient(circle at 30% 30%, #facc15, #ca8a04);
    }
    .signal-red {
        background: radial-gradient(circle at 30% 30%, #f87171, #dc2626);
    }
    .signal-gray {
        background: radial-gradient(circle at 30% 30%, #9ca3af, #6b7280);
    }
    
    /* 指标卡片 */
    .metric-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%);
        border-radius: 10px;
        padding: 15px;
        margin: 5px 0;
    }
    
    /* 导航样式 */
    .nav-tree {
        font-size: 14px;
    }
    .nav-phylum {
        font-weight: bold;
        color: #3b82f6;
        margin: 10px 0 5px 0;
    }
    .nav-class {
        padding-left: 10px;
        color: #6b7280;
    }
    .nav-order {
        padding-left: 20px;
        font-size: 12px;
    }
    .nav-family {
        padding-left: 30px;
        font-size: 11px;
        color: #9ca3af;
        cursor: pointer;
    }
    
    /* 信号灯矩阵 */
    .signal-matrix-cell {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        display: inline-block;
        margin: 2px;
        border: 2px solid #333;
    }
</style>
""", unsafe_allow_html=True)

# ========== 初始化数据管理器 ==========
@st.cache_resource
def get_data_manager():
    return OceanDataManager(demo_mode=True)

data_manager = get_data_manager()
industry_tree = load_industry_tree()

# ========== 侧边栏：产业分类导航 ==========
with st.sidebar:
    st.title("🧬 产业分类导航")
    st.markdown("---")
    
    # 模式切换
    st.subheader("📊 数据模式")
    demo_mode = st.toggle("演示模式", value=True, help="关闭后将尝试连接真实数据源")
    st.markdown("---")
    
    # 页面选择
    st.subheader("📍 选择页面")
    page = st.radio(
        "",
        ["📋 总览 - 信号灯矩阵", "🔬 详情 - 产业诊断", "📐 交叉 - 信号矩阵", "🩺 月度体检报告"],
        index=0
    )
    
    st.markdown("---")
    
    # 产业分类树（仅在详情页显示）
    if page == "🔬 详情 - 产业诊断" and industry_tree:
        st.subheader("🌳 产业分类树")
        
        # 构建选项列表
        family_options = []
        for phylum in industry_tree.get('phyla', []):
            phylum_name = f"{phylum['icon']} {phylum['name']}" if 'icon' in phylum else phylum['name']
            
            for class_ in phylum.get('classes', []):
                for order in class_.get('orders', []):
                    for family in order.get('families', []):
                        label = f"{family['code']}: {family['name']}"
                        family_options.append({
                            'label': label,
                            'value': family['code'],
                            'family': family,
                            'phylum': phylum_name
                        })
        
        selected_code = st.selectbox(
            "选择一个产业科",
            options=[f['value'] for f in family_options],
            format_func=lambda x: next((f['label'] for f in family_options if f['value'] == x), x)
        )
        
        # 获取选中的family数据
        selected_family = None
        for opt in family_options:
            if opt['value'] == selected_code:
                selected_family = opt['family']
                break
        
        if selected_family:
            st.markdown(f"**当前选中:** {selected_family['name']}")
            st.caption(f"{selected_family.get('description', '')}")
            
            # 显示代表性企业
            st.markdown("**🏢 代表性企业:**")
            for ent in selected_family.get('enterprises', []):
                st.markdown(f"- {ent['name']} ({ent['type']})")
    
    st.markdown("---")
    if st.button("🔄 刷新数据"):
        st.cache_resource.clear()
        st.rerun()

# ========== 辅助函数 ==========
def get_signal_color_class(color):
    """获取信号灯CSS类"""
    return {
        'green': 'signal-green',
        'yellow': 'signal-yellow',
        'red': 'signal-red',
        'off': 'signal-gray'
    }.get(color, 'signal-gray')

def render_signal_light(signal_data, size=60):
    """渲染信号灯"""
    color = signal_data.get('color', 'off')
    label = signal_data.get('label', '无数据')
    value = signal_data.get('value', '-')
    unit = signal_data.get('unit', '')
    
    color_class = get_signal_color_class(color)
    
    st.markdown(f"""
    <div style="text-align: center; padding: 10px;">
        <div class="signal-light {color_class}" style="width: {size}px; height: {size}px;"></div>
        <div style="margin-top: 8px; font-weight: bold; color: {'#4ade80' if color=='green' else '#facc15' if color=='yellow' else '#f87171' if color=='red' else '#9ca3af'};">
            {label}
        </div>
        <div style="font-size: 12px; color: #9ca3af;">
            {value}{unit}
        </div>
    </div>
    """, unsafe_allow_html=True)

def get_all_families(tree):
    """从产业树中提取所有科"""
    families = []
    if not tree:
        return families
    
    for phylum in tree.get('phyla', []):
        for class_ in phylum.get('classes', []):
            for order in class_.get('orders', []):
                for family in order.get('families', []):
                    families.append({
                        'code': family['code'],
                        'name': family['name'],
                        'phylum': phylum['name'],
                        'signals': family.get('signals', []),
                        'enterprises': family.get('enterprises', []),
                        'description': family.get('description', '')
                    })
    return families

# ========== 主内容区 ==========
st.title("🚢 广州海洋经济信号灯仪表板 V2")
st.caption("基于钱学森系统工程控制论 | 纲举目张四层结构 | 六维信号交叉验证")
st.markdown("---")

# ========== 页面1: 总览 - 信号灯矩阵 ==========
if page == "📋 总览 - 信号灯矩阵":
    st.header("📋 全产业信号灯总览矩阵")
    st.markdown("一眼看尽36个产业科的六维信号状态")

    # ===== 顶层 5 路信号灯（整合方案：信号灯 3→5 路） =====
    overview = data_manager.get_overview_signals()
    st.subheader("🚦 顶层信号灯（5 路）")
    st.caption("海温 / 港口吞吐 / AIS密度 / 海洋灾害 / 企业风险指数")
    ov_cols = st.columns(5)
    ov_meta = [
        ('sea_temp', '🌡️ 海温'),
        ('port_throughput', '📦 港口吞吐'),
        ('ais_density', '🛰️ AIS密度'),
        ('marine_disaster', '🌊 海洋灾害'),
        ('enterprise_risk', '🏢 企业风险'),
    ]
    for col, (key, title) in zip(ov_cols, ov_meta):
        sig = overview.get(key, {'color': 'off', 'label': title, 'value': '-'})
        with col:
            st.markdown(f"**{title}**")
            render_signal_light(sig, size=55)
    st.markdown("---")

    if industry_tree:
        # 生成模拟信号数据
        all_families = get_all_families(industry_tree)
        
        # 创建矩阵表格
        signal_dims = ['fund_flow', 'logistics_flow', 'market_entity', 
                      'industry_chain', 'env_risk', 'policy']
        dim_names = ['资金流', '物流流', '主体流', '产业链流', '环境流', '政策流']
        
        # 显示简化矩阵
        st.subheader("🚦 产业信号灯矩阵")
        
        # 按门分组显示
        for phylum in industry_tree.get('phyla', []):
            with st.expander(f"{phylum['icon']} {phylum['name']} ({phylum['code']}) - {phylum.get('description', '')}", expanded=False):
                
                family_list = []
                for class_ in phylum.get('classes', []):
                    for order in class_.get('orders', []):
                        for family in order.get('families', []):
                            family_list.append(family)
                
                # 创建表格
                cols = st.columns([3, 1, 1, 1, 1, 1, 1])
                with cols[0]:
                    st.markdown("**产业科**")
                for i, name in enumerate(dim_names):
                    with cols[i+1]:
                        st.markdown(f"**{name}**")
                
                # 每行一个产业科
                for family in family_list:
                    cols = st.columns([3, 1, 1, 1, 1, 1, 1])
                    
                    with cols[0]:
                        st.markdown(f"`{family['code']}`<br>{family['name']}", unsafe_allow_html=True)
                    
                    # 模拟信号数据
                    for i, dim in enumerate(signal_dims):
                        with cols[i+1]:
                            # 随机生成信号（演示）
                            colors = ['green', 'green', 'yellow', 'yellow', 'red']
                            signal_color = np.random.choice(colors, p=[0.4, 0.3, 0.2, 0.08, 0.02])
                            
                            st.markdown(f"""
                            <div style="text-align: center;">
                                <div class="signal-light signal-{signal_color}" style="width: 20px; height: 20px; margin: 0 auto;"></div>
                            </div>
                            """, unsafe_allow_html=True)
        
        # 图例
        st.markdown("---")
        st.markdown("**图例:** 🟢 优良 | 🟡 一般 | 🔴 预警 | ⚪ 无数据")
        
        # 总体统计
        st.subheader("📊 总体态势")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("产业科总数", len(all_families))
        with col2:
            st.metric("绿灯数", "~85%")
        with col3:
            st.metric("黄灯数", "~12%")
        with col4:
            st.metric("红灯数", "~3%")

# ========== 页面2: 详情 - 产业诊断 ==========
if page == "🔬 详情 - 产业诊断" and selected_family:
    st.header(f"🔬 产业诊断: {selected_family['name']}")
    st.caption(f"代码: `{selected_family['code']}` | {selected_family.get('description', '')}")
    
    # 获取六维信号数据
    signals = {}
    for sig_id in selected_family.get('signals', ['fund_flow', 'logistics_flow', 'market_entity', 
                                                   'industry_chain', 'env_risk', 'policy']):
        signals[sig_id] = data_manager.get_signal(sig_id, selected_family['code'])
    
    # 六维信号灯显示
    st.subheader("🚦 六维信号仪表盘")
    cols = st.columns(6)
    
    signal_order = ['fund_flow', 'logistics_flow', 'market_entity', 
                   'industry_chain', 'env_risk', 'policy']
    signal_titles = ['💰 资金流', '📦 物流流', '🏢 主体流', '🔗 产业链流', '🌡️ 环境流', '📜 政策流']
    
    for i, (sig_id, title) in enumerate(zip(signal_order, signal_titles)):
        with cols[i]:
            sig_data = signals.get(sig_id, {'color': 'off', 'label': '无数据', 'value': '-'})
            st.markdown(f"**{title}**")
            render_signal_light(sig_data, size=50)
            if sig_data.get('trend') is not None:
                trend = sig_data['trend']
                arrow = "↑" if trend > 0 else "↓" if trend < 0 else "→"
                st.caption(f"{arrow} {abs(trend):.1f}%")
    
    st.markdown("---")
    
    # 趋势图
    st.subheader("📈 历史趋势")
    
    # 模拟趋势数据
    dates = pd.date_range(start='2025-01-01', periods=5, freq='M')
    trend_df = pd.DataFrame({
        'date': dates,
        '综合指数': np.random.uniform(60, 90, 5),
        '资金流': np.random.uniform(50, 100, 5),
        '物流流': np.random.uniform(70, 95, 5),
    })
    
    fig = px.line(trend_df, x='date', y=['综合指数', '资金流', '物流流'],
                  title=f"{selected_family['name']} - 综合趋势",
                  labels={'value': '指数', 'date': '时间'})
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # 企业列表
    st.subheader("🏢 代表性企业")
    enterprises = selected_family.get('enterprises', [])
    if enterprises:
        for ent in enterprises:
            with st.container():
                cols = st.columns([3, 2, 1])
                with cols[0]:
                    st.markdown(f"**{ent['name']}**")
                with cols[1]:
                    st.markdown(f"类型: {ent['type']}")
                with cols[2]:
                    st.markdown(f"规模: {ent['scale']}")
    else:
        st.info("暂无企业数据")
    
    # 数据来源
    st.markdown("---")
    st.caption("数据来源: NOAA ERDDAP | 广州港务局 | 中国政府采购网 | 天眼查 (演示模式)")

# ========== 页面3: 交叉矩阵 ==========
if page == "📐 交叉 - 信号矩阵":
    st.header("📐 产业×信号交叉验证矩阵")
    st.markdown("钱学森控制论：多信号叠在一起八九不离十")
    
    if industry_tree:
        all_families = get_all_families(industry_tree)
        
        # 选择产业门进行详细分析
        selected_phylum = st.selectbox(
            "选择产业门",
            options=[p['name'] for p in industry_tree.get('phyla', [])],
            format_func=lambda x: f"{next(p['icon'] for p in industry_tree['phyla'] if p['name']==x)} {x}"
        )
        
        # 筛选该门下的产业
        filtered_families = [f for f in all_families 
                           if any(p['name'] == selected_phylum 
                                 for p in industry_tree['phyla'] 
                                 for c in p['classes'] 
                                 for o in c['orders'] 
                                 for fa in o['families'] if fa['code'] == f['code'])]
        
        # 交叉矩阵图
        st.subheader("🔀 交叉验证热力图")
        
        signal_dims = ['fund_flow', 'logistics_flow', 'market_entity', 
                      'industry_chain', 'env_risk', 'policy']
        dim_labels = ['资金流', '物流流', '主体流', '产业链', '环境流', '政策流']
        
        # 生成交叉矩阵数据
        matrix_data = []
        for family in filtered_families:
            row = []
            for dim in signal_dims:
                # 模拟信号值 - 生成0-100的分数
                has_signal = dim in family.get('signals', [])
                if has_signal:
                    score = np.random.randint(40, 95)
                else:
                    score = None
                row.append(score)
            matrix_data.append(row)
        
        # 绘制热力图
        if matrix_data:
            fig = go.Figure(data=go.Heatmap(
                z=matrix_data,
                x=dim_labels,
                y=[f"{f['code']}\n{f['name'][:8]}" for f in filtered_families],
                colorscale=[
                    [0, '#fee2e2'],      # 浅红
                    [0.5, '#fef3c7'],    # 浅黄
                    [1, '#dcfce7']       # 浅绿
                ],
                hoverongaps=False,
                text=[[f'{v:.0f}' if v else 'N/A' for v in row] for row in matrix_data],
                texttemplate="%{text}",
            ))
            fig.update_layout(
                title=f"{selected_phylum} - 产业×信号交叉矩阵",
                xaxis_title="信号维度",
                yaxis_title="产业科",
                height=max(400, len(filtered_families) * 40)
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # 综合信号雷达图
        st.subheader("📊 六维信号雷达图")
        
        # 选择对比的产业科
        compare_families = st.multiselect(
            "选择要对比的产业科（最多3个）",
            options=[f"{f['code']}: {f['name']}" for f in filtered_families],
            default=[filtered_families[0]['code'] + ': ' + filtered_families[0]['name']] if filtered_families else [],
            max_selections=3
        )
        
        if compare_families:
            fig = go.Figure()
            
            colors = ['#3b82f6', '#ef4444', '#10b981']
            for i, fam_str in enumerate(compare_families):
                code = fam_str.split(':')[0]
                family = next((f for f in filtered_families if f['code'] == code), None)
                
                if family:
                    # 模拟六维分数
                    scores = []
                    for dim in signal_dims:
                        if dim in family.get('signals', []):
                            scores.append(np.random.randint(60, 95))
                        else:
                            scores.append(30)
                    
                    fig.add_trace(go.Scatterpolar(
                        r=scores + [scores[0]],
                        theta=dim_labels + [dim_labels[0]],
                        fill='toself',
                        name=family['name'],
                        line_color=colors[i % len(colors)],
                        fillcolor=f'rgba({int(colors[i][1:3], 16)},{int(colors[i][3:5], 16)},{int(colors[i][5:7], 16)},0.3)'
                    ))
            
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=True,
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)

# ========== 页面4: 月度体检报告 ==========
if page == "🩺 月度体检报告":
    st.header("🩺 海洋经济月度体检报告")
    st.caption("自动生成 · C 出数据 → B 出报告 → D 归档（整合方案 Phase 4）")

    overview = data_manager.get_overview_signals()
    col1, col2, col3, col4, col5 = st.columns(5)
    labels = [
        ('sea_temp', '🌡️ 海温'), ('port_throughput', '📦 港口吞吐'),
        ('ais_density', '🛰️ AIS密度'), ('marine_disaster', '🌊 海洋灾害'),
        ('enterprise_risk', '🏢 企业风险'),
    ]
    cols = [col1, col2, col3, col4, col5]
    for c, (k, t) in zip(cols, labels):
        sig = overview.get(k, {})
        with c:
            st.metric(t, f"{sig.get('value', '-')}{sig.get('unit', '')}")

    families = get_all_families(industry_tree) if industry_tree else []
    report = [
        "# 广州海洋经济月度体检报告",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## 一、顶层信号灯（5 路）",
    ]
    for k, t in labels:
        sig = overview.get(k, {})
        report.append(f"- {t}：{sig.get('value', '-')}{sig.get('unit', '')}（{sig.get('color', '')}）")
    report.append("")
    report.append("## 二、产业覆盖")
    report.append(f"- 监测产业科总数：{len(families)}")
    report.append("")
    report.append("## 三、结论与建议")
    report.append("- 整体运行平稳，建议持续盯防企业风险与海洋灾害信号，异常时联动 B 站安全预警栏目。")
    report_text = "\n".join(report)

    st.markdown("---")
    st.subheader("📄 报告预览")
    st.code(report_text, language="markdown")
    st.download_button(
        "⬇️ 下载体检报告（Markdown）",
        report_text,
        file_name=f"ocean_health_report_{datetime.now().strftime('%Y%m')}.md",
        mime="text/markdown",
    )

# ========== 页脚 ==========
st.markdown("---")
st.caption(f"🕐 最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 广州海洋发展促进中心 | 基于钱学森系统工程控制论")
