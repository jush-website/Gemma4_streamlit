import streamlit as st
import fitz        
import docx        
from litellm import completion
from tavily import TavilyClient 
from datetime import datetime, timezone, timedelta # 匯入時間模組以修正時區

# ================= 設定區 =================
OLLAMA_API_BASE = "https://bonding-malt-nimbly.ngrok-free.dev"
MODEL_NAME = "ollama/gemma4:e4b" 
TAVILY_API_KEY = "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"  
# ==========================================

# ---------------------------------------------------------
# 【核心工具區】：處理上傳的檔案
# ---------------------------------------------------------
def extract_text_from_uploaded_file(uploaded_file):
    filename = uploaded_file.name
    ext = filename.split('.')[-1].lower()
    try:
        if ext in ["txt", "md", "csv"]:
            return uploaded_file.getvalue().decode("utf-8")
        elif ext == "pdf":
            text = ""
            with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
                for page in doc: text += page.get_text()
            return text
        elif ext == "docx":
            text = ""
            doc = docx.Document(uploaded_file)
            for paragraph in doc.paragraphs: text += paragraph.text + "\n"
            return text
        else:
            return None
    except Exception as e:
        return f"❌ 讀取 {filename} 失敗：{e}"

def format_with_agent(text_content, filename):
    system_prompt = f"""
    你是一位具備頂尖商業洞察力的高階數據分析師與知識管理專家。
    你的任務是閱讀 <DOCUMENT> 標籤內的原始文件，並提煉出一份具備高度商業與學術價值的「執行摘要報告」。

    【分析守則】：
    1. 保持客觀、精煉、具備邏輯性，使用繁體中文 (台灣) 撰寫。
    2. 絕對禁止輸出任何問候語、開場白或自我介紹，直接輸出 Markdown 報告。
    3. 注意：提供的文件可能因長度限制而在結尾被截斷。請僅針對「已提供的內容」進行總結與分析，切勿憑空捏造未提及的數據或情節。

    請嚴格遵守以下 Markdown 格式輸出：

    ## 📄 文件剖析報告：{filename}

    ### 🎯 執行摘要 (Executive Summary)
    [請用 2~3 句話，精準概括本文件的核心目的、背景與最終結論]

    ### 🔑 核心關鍵字
    [提取 3~5 個專業術語或核心概念，以頓號分隔]

    ### 📊 關鍵論點解析 (Key Findings)
    [萃取文件中最重要的 3~5 個核心論點，必須包含具體的數據、事實或強烈佐證]
    - **[論點一標題]**：[具體的細節說明與佐證]
    - **[論點二標題]**：[具體的細節說明與佐證]
    - **[論點三標題]**：[具體的細節說明與佐證]

    ### 💡 綜合結論與建議 (Conclusion & Next Steps)
    [基於現有文件內容，提出客觀的最終結論，並給出 1~2 個具備建設性的後續行動或應用建議]

    <DOCUMENT>
    {text_content}
    </DOCUMENT>
    """
    try:
        response = completion(
            model=MODEL_NAME, 
            messages=[{"role": "user", "content": system_prompt.strip()}],
            api_base=OLLAMA_API_BASE, 
            temperature=0.0, num_ctx=6000    
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ AI 處理失敗：{e}"

def summarize_web_results(query, search_results):
    system_prompt = f"""
    你是一位專業的研究分析師。你的任務是將 <SEARCH_RESULTS> 標籤內抓取到的網路搜尋資料，統整成一份結構清晰、具備洞察力的研究報告。

    【嚴格遵守事項】：
    1. 絕對禁止輸出任何問候語或額外解釋，直接輸出 Markdown 報告。
    2. 使用繁體中文 (台灣) 撰寫。
    3. 你的分析【必須 100% 來自提供的搜尋結果】，絕對不能使用你的預先訓練知識來捏造資料。
    4. ⚠️ 【防呆機制】：請先評估搜尋結果是否與主題「{query}」實質相關。若嚴重偏離，請在「📝 核心重點摘要」的最上方標註：「⚠️ 警告：目前抓取的網路資料與您的查詢主題關聯性較低，以下摘要僅供參考。」

    請依據以下格式輸出：

    # 🌐 網路搜尋報告：{query}

    ## 📝 核心重點摘要
    [請綜合所有來源，將資訊進行交叉比對與分類，以條列式（最多 5 點）總結最重要的資訊、數據或趨勢]

    ## 📚 參考來源解析
    [請列出提供的所有來源，並為每個來源寫一句話的核心價值評估]
    - **[來源標題]** ([網址])：[一句話說明這個來源提供了什麼關鍵資訊]

    ## 💡 延伸研究建議
    [基於上述資料的不足之處或未來發展，提出 2~3 個值得進一步搜尋或研究的方向]

    <SEARCH_RESULTS>
    {search_results}
    </SEARCH_RESULTS>
    """
    try:
        response = completion(
            model=MODEL_NAME, 
            messages=[{"role": "user", "content": system_prompt.strip()}],
            api_base=OLLAMA_API_BASE, 
            temperature=0.0, num_ctx=6000    
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ AI 處理失敗：{e}"


# ---------------------------------------------------------
# 【網頁介面區】：Streamlit 魔法開始
# ---------------------------------------------------------
st.set_page_config(page_title="Gemma4 彙整中心", page_icon="🤖", layout="wide")

with st.sidebar:
    st.title("⚙️ 系統設定")
    st.info(f"📍 目前連線：{OLLAMA_API_BASE}\n\n🧠 使用模型：{MODEL_NAME}")
    st.markdown("---")
    st.write("這是一個架設於 Streamlit 的本地端 Gemma4 系統。")

st.markdown("請選擇你要執行的任務：")

tab1, tab2 = st.tabs(["📂 智慧文件彙整", "🌐 自動文獻檢索"])

# ================= 頁籤一：文件彙整 =================
with tab1:
    st.header("📂 上傳檔案讓 AI 幫你整理")
    uploaded_files = st.file_uploader(
        "支援格式：PDF, Word, TXT, MD, CSV", 
        type=["pdf", "docx", "txt", "md", "csv"], 
        accept_multiple_files=True
    )

    if uploaded_files:
        # 使用欄位將按鈕並排
        col1, col2 = st.columns([1, 1])
        
        with col1:
            start_btn = st.button("🚀 開始彙整", type="primary", use_container_width=True)
            
        with col2:
            if st.button("🗑️ 清空並重置", use_container_width=True):
                st.rerun() # 強制重新載入頁面

        if start_btn:
            st.info("💡 提示：若需中斷分析，請點擊畫面右上角的「🛑 Stop」按鈕。")
            with st.spinner("AI 正在卯起來閱讀並整理中，請稍候..."):
                combined_report = f"# 📚 多檔案彙整分析報告\n\n"
                
                # 設定台灣時區 (UTC+8)
                tw_timezone = timezone(timedelta(hours=8))
                current_time = datetime.now(tw_timezone).strftime('%Y-%m-%d %H:%M:%S')
                combined_report += f"- **處理日期：** {current_time}\n\n---"
                
                progress_bar = st.progress(0)
                
                for i, file in enumerate(uploaded_files):
                    raw_text = extract_text_from_uploaded_file(file)
                    if raw_text:
                        raw_text = raw_text[:8000] # 放寬擷取字元上限，提升完整度
                        ai_result = format_with_agent(raw_text, file.name)
                        combined_report += f"\n\n{ai_result}\n\n---"
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                st.success("🎉 彙整完成！")
                st.markdown("### 報告預覽")
                st.markdown(combined_report)
                
                st.download_button(
                    label="📥 下載 Markdown 報告",
                    data=combined_report,
                    file_name="智慧彙整報告.md",
                    mime="text/markdown"
                )

# ================= 頁籤二：網路搜尋 =================
with tab2:
    st.header("🌐 輸入關鍵字，AI 自動爬文寫報告")
    query = st.text_input("🔍 請輸入你想研究的關鍵字或主題：", placeholder="例如：2026 LLM 發展趨勢")
    
    # 同樣為搜尋頁籤加入重置按鈕
    col3, col4 = st.columns([1, 1])
    
    with col3:
        search_btn = st.button("📡 開始檢索", type="primary", use_container_width=True)
        
    with col4:
        if st.button("🗑️ 清空搜尋", use_container_width=True):
            st.rerun()

    if search_btn:
        if not query:
            st.warning("請先輸入關鍵字喔！")
        else:
            st.info("💡 提示：若需中斷搜尋，請點擊畫面右上角的「🛑 Stop」按鈕。")
            with st.spinner(f"正在網路上搜尋「{query}」的最新資料..."):
                try:
                    # 呼叫專業的 Tavily API
                    tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
                    response = tavily_client.search(query=query, max_results=5)
                    results = response.get('results', [])
                    
                    if not results:
                        st.error("❌ 找不到相關資料。")
                    else:
                        search_context = ""
                        for i, res in enumerate(results):
                            search_context += f"來源 {i+1}: {res.get('title', '')}\n網址: {res.get('url', '')}\n摘要: {res.get('content', '')}\n\n"
                        
                        st.info("✅ 成功抓取 Tavily 網頁資料，正在交給大腦進行總結...")
                        
                        formatted_md = summarize_web_results(query, search_context)
                        
                        st.success("🎉 報告生成完畢！")
                        st.markdown(formatted_md)
                        
                        st.download_button(
                            label="📥 下載搜尋報告",
                            data=formatted_md,
                            file_name=f"搜尋報告_{query}.md",
                            mime="text/markdown"
                        )
                except Exception as e:
                    st.error(f"執行過程中發生錯誤：{e}")
