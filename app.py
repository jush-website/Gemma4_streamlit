import streamlit as st
import time
import fitz        
import docx        
from litellm import completion
from tavily import TavilyClient 

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
    你是一個專業的文件整理代理人。請閱讀下方提供的【原始文件內容】，並嚴格依照 Markdown 模板輸出結果。
    絕對禁止輸出任何問候語。必須使用繁體中文 (台灣)。

    === 目標 Markdown 模板 ===
    ## 📄 文件：{filename}
    - **核心主題：** [一句話總結]
    - **重點摘要：**
      1. [重點一]
      2. [重點二]
      3. [重點三]
    === 模板結束 ===

    【原始文件內容】：
    {text_content}
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
請作為一位專業的資料分析師。你的任務是將 <DATA> 裡的網路搜尋資料，彙整成 <FORMAT> 指定的 Markdown 格式。
絕對禁止輸出任何問候語或額外文字。必須使用繁體中文 (台灣)。

⚠️ 【重要防呆機制】：
在整理之前，請先檢查 <DATA> 裡的內容是否與使用者的查詢主題「{query}」具有實質關聯性。
如果搜尋結果完全偏離主題，請務必在「📝 核心重點摘要」的第一點加上強烈警告：「⚠️ 警告：搜尋引擎抓取的資料與您的查詢主題不符！」

<DATA>
{search_results}
</DATA>

<FORMAT>
# 🌐 網路搜尋報告：{query}

## 📝 核心重點摘要
[若資料不符，請先輸出警告標語]
[請以條列式總結 <DATA> 中的資訊]

## 📚 參考文獻與出處
[請嚴格列出 <DATA> 中的來源標題、網址與一句話摘要]

## 💡 後續研究建議
[提出 1~3 個建議]
</FORMAT>
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
st.set_page_config(page_title="萬能 AI 代理人指揮中心", page_icon="🤖", layout="wide")

with st.sidebar:
    st.title("⚙️ 系統設定")
    st.info(f"📍 目前連線：{OLLAMA_API_BASE}\n\n🧠 使用模型：{MODEL_NAME}")
    st.markdown("---")
    st.write("這是一個由 Streamlit 驅動的地端 AI 代理人系統。")

st.title("🌟 萬能 AI 代理人指揮中心")
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
        if st.button("🚀 開始彙整", type="primary"):
            with st.spinner("AI 正在卯起來閱讀並整理中，請稍候..."):
                combined_report = f"# 📚 多檔案彙整分析報告\n\n"
                combined_report += f"- **處理日期：** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n---"
                
                progress_bar = st.progress(0)
                
                for i, file in enumerate(uploaded_files):
                    raw_text = extract_text_from_uploaded_file(file)
                    if raw_text:
                        raw_text = raw_text[:8192] 
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
    query = st.text_input("🔍 請輸入你想研究的關鍵字或主題：", placeholder="例如：2024 LLM 發展趨勢")
    
    if st.button("📡 開始檢索", type="primary"):
        if not query:
            st.warning("請先輸入關鍵字喔！")
        else:
            with st.spinner(f"正在網路上搜尋「{query}」的最新資料..."):
                try:
                    # 👈 呼叫專業的 Tavily API
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
