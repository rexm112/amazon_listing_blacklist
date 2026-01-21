import streamlit as st
import json
import re
import pandas as pd

# 1. 设置页面基础配置
st.set_page_config(
    page_title="Amazon Listing 合规检查器",
    page_icon="🛡️",
    layout="wide"
)

# 2. 加载敏感词库函数
@st.cache_data
def load_blacklist():
    try:
        with open('amazon_jewelry_blacklist_v1.1.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("找不到敏感词库文件 (amazon_jewelry_blacklist_v1.1.json)，请确认文件在同一目录下。")
        return None

# 3. 核心检查逻辑 (Regex Magic)
def check_text(text, blacklist_data):
    if not text:
        return [], text

    violations = []
    highlighted_text = text

    # 遍历所有分类
    for category in blacklist_data['categories']:
        cat_name = category['category_name']
        risk_level = category['risk_level']
        
        for item in category['keywords']:
            term = item['term']
            match_type = item['match_type']
            reason = item['reason']
            suggestion = item['suggestion']

            # 构建正则模式
            # re.escape(term) 确保词里的特殊符号被转义
            if match_type == 'exact':
                # \b 表示单词边界，确保 "Real" 不会匹配 "Really"
                pattern = r'\b' + re.escape(term) + r'\b'
            else: # broad
                pattern = re.escape(term)

            # 查找所有匹配项 (忽略大小写)
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            
            if matches:
                # 记录违规信息
                violations.append({
                    "风险等级": risk_level,
                    "敏感词": term,
                    "分类": cat_name,
                    "违规原因": reason,
                    "修改建议": suggestion,
                    "出现次数": len(matches)
                })

                # 替换文本用于高亮显示 (使用HTML)
                # 注意：为了避免重复替换破坏HTML结构，这里做一个简单的标记
                # 实际生产中更复杂的替换建议倒序替换，这里做演示简化处理
                highlight_style = "background-color: #ff4b4b; color: white; padding: 2px 4px; border-radius: 4px;"
                if risk_level == "CRITICAL":
                    highlight_style = "background-color: #ff4b4b; color: white; padding: 2px 4px; border-radius: 4px;" # 红
                elif risk_level == "HIGH":
                    highlight_style = "background-color: #ffa500; color: white; padding: 2px 4px; border-radius: 4px;" # 橙
                else:
                    highlight_style = "background-color: #ffd700; color: black; padding: 2px 4px; border-radius: 4px;" # 黄

                # 使用正则替换，保留原文大小写 (case insensitive replace)
                highlighted_text = re.sub(
                    pattern, 
                    lambda m: f'<span style="{highlight_style}" title="{reason}">{m.group(0)}</span>', 
                    highlighted_text, 
                    flags=re.IGNORECASE
                )

    return violations, highlighted_text

# --- UI 界面构建 ---

st.title("🛡️ 亚马逊 Listing 合规检查器")
st.markdown("专为 **首饰类目 (Jewelry)** 定制。粘贴标题、五点或描述，自动检测敏感词。")

# 侧边栏：显示加载状态
blacklist = load_blacklist()
if blacklist:
    st.sidebar.success(f"词库加载成功！版本: {blacklist['meta']['version']}")
    st.sidebar.info(f"最后更新: {blacklist['meta']['last_updated']}")

# 主要输入区
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 输入 Listing 文案")
    user_input = st.text_area("在此粘贴文本...", height=400, placeholder="例如: Real Gold Ring for natural healing...")
    check_btn = st.button("开始检查", type="primary")

with col2:
    st.subheader("🔍 检查结果")
    
    if check_btn and user_input:
        if blacklist:
            violations, html_text = check_text(user_input, blacklist)
            
            if not violations:
                st.success("✅ 完美！未发现已知敏感词。")
                st.markdown(f"<div style='padding:10px; border:1px solid #ddd; border-radius:5px;'>{user_input}</div>", unsafe_allow_html=True)
            else:
                st.error(f"⚠️ 发现 {len(violations)} 处潜在风险！")
                
                # 1. 展示高亮文本
                st.markdown("### 预览 (鼠标悬停查看原因)")
                # 将换行符转换为 HTML换行，保持段落格式
                formatted_html = html_text.replace("\n", "<br>")
                st.markdown(f"<div style='padding:15px; border:1px solid #ddd; border-radius:5px; line-height: 1.6;'>{formatted_html}</div>", unsafe_allow_html=True)
                
                # 2. 展示详细表格
                st.markdown("### 详细报告")
                df = pd.DataFrame(violations)
                # 调整列顺序
                df = df[["风险等级", "敏感词", "修改建议", "违规原因", "分类"]]
                st.dataframe(df, use_container_width=True)
                
                # 3. 统计指标
                critical_count = len([v for v in violations if v['风险等级'] == 'CRITICAL'])
                if critical_count > 0:
                    st.warning(f"🚨 注意：有 {critical_count} 个致命错误（CRITICAL），必须修改才能上架！")

    elif check_btn and not user_input:
        st.warning("请输入文本后再点击检查。")
    else:
        st.info("等待输入...")

# 页脚
st.markdown("---")
st.markdown("*Tool built for Internal Ops | Powered by Python & Streamlit*")