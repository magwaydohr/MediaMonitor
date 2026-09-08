import os
os.environ["PYTHONIOENCODING"] = "utf-8"

import streamlit as st
import feedparser
import pandas as pd
import requests

# Dashboard ၏ အပြင်အဆင်ကို သတ်မှတ်ခြင်း
st.set_page_config(page_title="DoHR Media Monitoring", layout="wide")

# ==========================================
# လုံခြုံရေးအရ ဝင်ရောက်ခွင့် (Login System)
# ==========================================
# ဌာနတွင်း အသုံးပြုခွင့်ပေးမည့် Username နှင့် Password များ (မိမိစိတ်ကြိုက် ပြင်ဆင်နိုင်ပါသည်)
USER_CREDENTIALS = {
    "dohr_admin": "Anyar@2026",
    "kokyaw": "Imfug#2026"
}

def check_login():
    """အသုံးပြုသူ မှန်ကန်ကြောင်း စစ်ဆေးသည့် လုပ်ငန်းစဉ်"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        # Login Form ပြသခြင်း
        st.title("🔒 လူ့အခွင့်အရေးဌာန (DoHR) - သတင်းစောင့်ကြည့်ရေးစနစ်")
        st.info("ဤ Dashboard ကို IMFUG အဖွဲ့ဝင်များသာ အသုံးပြုနိုင်ပါသည်။ ဝင်ရောက်ရန် အောက်ပါအချက်အလက်များ ဖြည့်စွက်ပါ။")
        
        with st.form("login_form"):
            username = st.text_input("အသုံးပြုသူအမည် (DoHR@Magway)")
            password = st.text_input("စကားဝှက် (MagwayDoHR060826)", type="password")
            submitted = st.form_submit_button("ဝင်မည် (Login)")
            
            if submitted:
                if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
                    st.session_state.logged_in = True
                    st.success("ဝင်ရောက်ခြင်း အောင်မြင်ပါသည်။")
                    st.rerun()  # စာမျက်နှာကို Refresh လုပ်ပြီး Dashboard သို့သွားရန်
                else:
                    st.error("❌ Username သို့မဟုတ် Password မှားယွင်းနေပါသည်။")
        return False
    return True

# ==========================================
# အဓိက Dashboard လုပ်ငန်းစဉ်များ
# ==========================================
def main_dashboard():
    # ဘေးဘက် (Sidebar) တွင် အကောင့်ထွက်ရန် ခလုတ်ထည့်ခြင်း
    st.sidebar.title("DoHR Dashboard")
    st.sidebar.write("👤 အကောင့်ဝင်ရောက်ထားပါသည်")
    if st.sidebar.button("🚪 အကောင့်မှ ထွက်မည် (Logout)"):
        st.session_state.logged_in = False
        st.rerun()

    st.title("📰 Media Monitoring Dashboard")
    st.markdown("**(လူ့အခွင့်အရေးနှင့် မြေပြင်အခြေအနေ စောင့်ကြည့်လေ့လာရေး သတင်းစုစည်းမှု)**")

    NEWS_SOURCES = {
        "BBC မြန်မာပိုင်း": "https://www.bbc.com/burmese/index.xml",
        "RFA မြန်မာပိုင်း": "https://www.rfa.org/burmese/rss2.xml",
        "Myanmar Now": "https://myanmar-now.org/mm/feed/"
    }

    def categorize_news(title):
        title_lower = title.lower()
        
        keywords_conflict = ["တိုက်ပွဲ", "စစ်တပ်", "ဗုံး", "လက်နက်", "aa", "tnla", "pdf", "kia", "စစ်ရေး", "ပစ်ခတ်", "သိမ်း", "လေကြောင်း", "ထိုးစစ်", "စစ်ကောင်စီ", "ဗုံးကြဲ", "တိုက်ခိုက်", "ဒရုန်း"]
        keywords_human_rights = ["လူ့အခွင့်အရေး", "ဖမ်းဆီး", "သတ်ဖြတ်", "ထောင်", "ညှဉ်းပန်း", "မီးရှို့", "စစ်ရှောင်", "ရွှေ့ပြောင်း", "ဒုက္ခသည်", "အရပ်သား", "ဖမ်းဆီးခံ", "မုဒိမ်း", "ပေါ်တာ"]
        keywords_politics = ["နိုင်ငံရေး", "ရွေးကောက်ပွဲ", "nug", "အစိုးရ", "လွှတ်တော်", "ဒေါ်အောင်ဆန်းစုကြည်", "ဒီမိုကရေစီ", "တော်လှန်ရေး", "crph"]
        keywords_economy = ["စီးပွားရေး", "ဒေါ်လာ", "ရွှေ", "ဈေး", "ကုန်သွယ်ရေး", "ဘဏ်", "ငွေကြေး"]
        
        if any(word in title_lower for word in keywords_human_rights):
            return "လူ့အခွင့်အရေး"
        elif any(word in title_lower for word in keywords_conflict):
            return "စစ်ရေး/တိုက်ပွဲ"
        elif any(word in title_lower for word in keywords_politics):
            return "နိုင်ငံရေး"
        elif any(word in title_lower for word in keywords_economy):
            return "စီးပွားရေး"
        else:
            return "အထွေထွေ/အခြား"

    def fetch_all_news():
        news_list = []
        fetch_stats = {} 
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        }
        
        for source_name, url in NEWS_SOURCES.items():
            try:
                response = requests.get(url, headers=headers, timeout=15)
                feed = feedparser.parse(response.content)
                
                entries_fetched = 0
                for entry in feed.entries[:15]: 
                    date_str = entry.get('published', entry.get('updated', 'ရက်စွဲမပါဝင်ပါ'))
                    category = categorize_news(entry.title)
                    
                    news_list.append({
                        "သတင်းဌာန": source_name,
                        "ရက်စွဲ": date_str,
                        "အမျိုးအစား": category,
                        "သတင်းခေါင်းစဉ်": entry.title,
                        "လင့်ခ်": entry.link
                    })
                    entries_fetched += 1
                
                fetch_stats[source_name] = entries_fetched
                
            except Exception as e:
                st.warning(f"⚠️ {source_name} မှ သတင်းဆွဲယူ၍ မရပါ။")
                fetch_stats[source_name] = 0
                
        return news_list, fetch_stats

    if 'news_data' not in st.session_state:
        st.session_state.news_data = None
        st.session_state.fetch_stats = None

    st.write("အောက်ပါ သတင်းဌာနများမှ နောက်ဆုံးရသတင်း (၁၅) ပုဒ်စီကို ဆွဲယူပါမည်။")

    if st.button("🔄 သတင်းများကို ဆွဲယူပြီး အမျိုးအစားခွဲပါ", type="primary"):
        with st.spinner("အချက်အလက်များ ဆွဲယူနေပါသည်... စက္ကန့်အနည်းငယ် ကြာနိုင်ပါသည်။"):
            fetched_news, stats = fetch_all_news()
            st.session_state.news_data = fetched_news
            st.session_state.fetch_stats = stats

    if st.session_state.news_data:
        df = pd.DataFrame(st.session_state.news_data)
        st.success(f"အောင်မြင်စွာ ဆွဲယူစိစစ်ပြီးပါပြီ! (စုစုပေါင်း သတင်း {len(df)} ပုဒ် ရရှိပါသည်)")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            tab1, tab2, tab3 = st.tabs(["📊 အားလုံး", "⚠️ လူ့အခွင့်အရေး သီးသန့်", "⚔️ စစ်ရေး/တိုက်ပွဲ"])
            with tab1:
                st.dataframe(df, use_container_width=True, height=500)
            with tab2:
                hr_df = df[df['အမျိုးအစား'] == 'လူ့အခွင့်အရေး']
                st.dataframe(hr_df, use_container_width=True, height=500)
            with tab3:
                conflict_df = df[df['အမျိုးအစား'] == 'စစ်ရေး/တိုက်ပွဲ']
                st.dataframe(conflict_df, use_container_width=True, height=500)
                
        with col2:
            st.markdown("### 📈 ဆွဲယူရရှိမှု မှတ်တမ်း")
            for source, count in st.session_state.fetch_stats.items():
                if count > 0:
                    st.write(f"✔️ **{source}**: {count} ပုဒ်")
                else:
                    st.write(f"❌ **{source}**: မရရှိပါ")
        
        csv_data = df.to_csv(index=False).encode('utf-8-sig')
        st.markdown("---")
        st.download_button(
            label="📥 ဇယားကို Download ဆွဲရန် (CSV ဖိုင်)",
            data=csv_data,
            file_name='Human_Rights_Media_Monitoring.csv',
            mime='text/csv',
        )

# ==========================================
# အစီအစဉ်စတင်ခြင်း
# ==========================================
# အသုံးပြုသူသည် Login ဝင်ပြီးမှသာ Main Dashboard ကို မြင်ရမည်
if check_login():
    main_dashboard()
