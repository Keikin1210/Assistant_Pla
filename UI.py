# UI.py 最新（修正版・完全版）
import streamlit as st
from groq import Groq
import json
import requests
import pandas as pd
from streamlit_autorefresh import st_autorefresh
import os
from datetime import datetime
import time
from dotenv import load_dotenv
load_dotenv() # これで.envファイルの中身が読み込まれます

# =========================
# 1. 基本設定
# =========================
# ⚠️本番では必ず環境変数に移してください（漏洩対策）
GROQ_API_KEY = os.getenv("GROQ_API_KEY") # 直接書かない！
groq_client = Groq(api_key=GROQ_API_KEY)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
SCROLL_HEIGHT = 660

st.set_page_config(
    page_title="AI診療アシスタント",
    layout="wide",
    page_icon="🏥",
    initial_sidebar_state="expanded",
)

# =========================
# 2. CSS スタイル
# =========================
st.markdown("""
<style>
/* ─── リセット & ベース ─── */
:root {
    --blue-50:  #EFF6FF;
    --blue-100: #DBEAFE;
    --blue-200: #BFDBFE;
    --blue-400: #60A5FA;
    --blue-500: #3B82F6;
    --blue-600: #2563EB;
    --blue-700: #1D4ED8;
    --blue-900: #1E3A5F;
    --slate-50:  #F8FAFC;
    --slate-100: #F1F5F9;
    --slate-200: #E2E8F0;
    --slate-400: #94A3B8;
    --slate-500: #64748B;
    --slate-700: #334155;
    --slate-800: #1E293B;
    --slate-900: #0F172A;
    --green-50:  #F0FDF4;
    --green-500: #22C55E;
    --green-600: #16A34A;
    --amber-50:  #FFFBEB;
    --amber-500: #F59E0B;
    --red-50:    #FFF1F2;
    --red-500:   #EF4444;
    --red-600:   #DC2626;
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --radius-xl: 20px;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
    --shadow-md: 0 4px 12px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.04);
    --shadow-lg: 0 10px 30px rgba(0,0,0,0.08), 0 4px 8px rgba(0,0,0,0.04);
}

html, body,
[data-testid="stAppViewContainer"] {
    background: linear-gradient(160deg, #EFF6FF 0%, #F1F5F9 40%, #F8FAFC 100%) !important;
    color: var(--slate-800);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Hiragino Sans",
                 "Noto Sans JP", "Meiryo", sans-serif;
    font-size: 14px;
    line-height: 1.6;
}

/* ページ余白 */
[data-testid="stAppViewContainer"] > .main {
    padding-top: 1.2rem !important;
    padding-bottom: 2rem !important;
}

/* ステータスウィジェット非表示 */
[data-testid="stStatusWidget"] { display: none !important; }

/* Streamlit デフォルト枠線を消す */
[data-testid="stForm"] {
    border: none !important;
    padding: 0 !important;
}

/* ─── カード（Streamlit border=True） ─── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF !important;
    border: 1px solid var(--blue-100) !important;
    border-radius: var(--radius-lg) !important;
    box-shadow: var(--shadow-md) !important;
    padding: 1.2rem 1.4rem !important;
    transition: box-shadow 0.2s ease !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    box-shadow: var(--shadow-lg) !important;
}

/* ─── ラベル ─── */
label, .stTextInput label, .stSelectbox label,
.stTextArea label, .stRadio label,
.stMultiSelect label {
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: var(--slate-700) !important;
    letter-spacing: 0.01em !important;
}

/* ─── 入力フィールド ─── */
input[type="text"], input[type="password"], textarea {
    border-radius: var(--radius-sm) !important;
    border: 1.5px solid var(--slate-200) !important;
    font-size: 0.88rem !important;
    transition: border-color 0.15s ease !important;
}
input[type="text"]:focus, input[type="password"]:focus, textarea:focus {
    border-color: var(--blue-400) !important;
    box-shadow: 0 0 0 3px rgba(96,165,250,0.15) !important;
}
::placeholder { color: var(--slate-400) !important; }

/* ─── ボタン共通 ─── */
button {
    border-radius: 999px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.01em !important;
    transition: all 0.18s ease !important;
}
button:hover:not([disabled]) {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(0,0,0,0.12) !important;
}
button[disabled] { opacity: 0.45 !important; cursor: not-allowed !important; }

/* ─── サイドバー ─── */
[data-testid="stSidebar"] > div:first-child {
    background: linear-gradient(180deg, #F0F5FF 0%, #F8FAFC 100%) !important;
    border-right: 1px solid var(--blue-100) !important;
}

/* ─── ログアウトボタン（赤） ─── */
div[class*="st-key-logout"] button {
    background: linear-gradient(135deg, #EF4444, #DC2626) !important;
    color: #fff !important;
    border: none !important;
    box-shadow: 0 3px 10px rgba(220,38,38,0.25) !important;
}
div[class*="st-key-logout"] button p { color: #fff !important; }
div[class*="st-key-logout"] button:hover {
    background: linear-gradient(135deg, #DC2626, #B91C1C) !important;
    box-shadow: 0 6px 18px rgba(220,38,38,0.35) !important;
}

/* ─── 上書き保存ボタン（緑） ─── */
div[class*="st-key-overwrite_btn"] button {
    background: linear-gradient(135deg, #16A34A, #15803D) !important;
    color: #fff !important;
    border: none !important;
    box-shadow: 0 3px 10px rgba(22,163,74,0.25) !important;
}
div[class*="st-key-overwrite_btn"] button p { color: #fff !important; }
div[class*="st-key-overwrite_btn"] button:hover {
    background: linear-gradient(135deg, #15803D, #166534) !important;
    box-shadow: 0 6px 18px rgba(22,163,74,0.35) !important;
}

/* ─── アニメーション ─── */
@keyframes pulse-ring {
    0%   { box-shadow: 0 0 0 0 rgba(239,68,68,0.55); }
    70%  { box-shadow: 0 0 0 8px rgba(239,68,68,0); }
    100% { box-shadow: 0 0 0 0 rgba(239,68,68,0); }
}
@keyframes fade-in {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
}
.fade-in { animation: fade-in 0.3s ease forwards; }

/* ─── ステータスバッジ ─── */
.badge {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 2px 10px; border-radius: 999px;
    font-size: 0.75rem; font-weight: 700; letter-spacing: 0.02em;
}
.badge-active  { background: var(--amber-50);  color: #B45309; border: 1px solid #FDE68A; }
.badge-done    { background: var(--green-50);  color: #15803D; border: 1px solid #BBF7D0; }
.badge-live    {
    background: var(--red-50); color: var(--red-600);
    border: 1px solid #FECACA;
    animation: pulse-ring 1.4s infinite;
}

/* ─── メトリクスカード ─── */
.metric-wrap {
    background: #fff;
    border: 1px solid var(--blue-100);
    border-radius: var(--radius-lg);
    padding: 1.2rem 1rem;
    text-align: center;
    box-shadow: var(--shadow-sm);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    cursor: default;
}
.metric-wrap:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 28px rgba(37,99,235,0.1);
}
.metric-icon  { font-size: 1.6rem; line-height: 1; margin-bottom: 6px; }
.metric-val   { font-size: 2.2rem; font-weight: 800; line-height: 1.1; margin: 4px 0; }
.metric-label { font-size: 0.78rem; font-weight: 600; color: var(--slate-500); }
.metric-sub   { font-size: 0.7rem;  color: var(--slate-400); margin-top: 2px; }

/* ─── セクションヘッダー ─── */
.section-header {
    display: flex; align-items: center; gap: 8px;
    padding: 6px 12px;
    background: linear-gradient(90deg, var(--blue-50), transparent);
    border-left: 3px solid var(--blue-500);
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
    margin: 1rem 0 0.6rem 0;
    font-size: 0.88rem; font-weight: 700;
    color: var(--blue-700);
}

/* ─── カードヘッダー ─── */
.card-title {
    font-size: 0.95rem; font-weight: 700;
    color: var(--blue-900);
    display: flex; align-items: center; gap: 6px;
    margin-bottom: 2px;
}
.card-sub {
    font-size: 0.78rem; color: var(--slate-500);
    margin-bottom: 10px;
}

/* ─── ガイドボックス ─── */
.guide-box {
    background: var(--blue-50);
    border: 1px solid var(--blue-200);
    border-left: 3px solid var(--blue-500);
    border-radius: var(--radius-md);
    padding: 12px 14px;
    font-size: 0.84rem;
    color: var(--blue-700);
    line-height: 1.7;
}

/* ─── info系のスタイル上書き ─── */
[data-testid="stAlert"] {
    border-radius: var(--radius-md) !important;
}

/* ─── データテーブル ─── */
.dataframe { font-size: 0.82rem !important; }

/* ─── ダウンロードボタン専用 ─── */
div[class*="st-key-dl_btn"] button {
    background: linear-gradient(135deg, var(--blue-600), var(--blue-700)) !important;
    color: #fff !important; border: none !important;
    box-shadow: 0 3px 12px rgba(37,99,235,0.25) !important;
    font-size: 0.9rem !important;
}
div[class*="st-key-dl_btn"] button p { color: #fff !important; }

/* ─── ヘッダーバナー ─── */
.page-header {
    background: linear-gradient(135deg, #1D4ED8 0%, #2563EB 50%, #3B82F6 100%);
    padding: 1.8rem 2rem;
    border-radius: var(--radius-xl);
    color: #fff;
    margin-bottom: 1.4rem;
    box-shadow: 0 8px 24px rgba(37,99,235,0.22);
    position: relative;
    overflow: hidden;
}
.page-header::before {
    content: "";
    position: absolute; top: -40%; right: -5%;
    width: 280px; height: 280px;
    background: rgba(255,255,255,0.06);
    border-radius: 50%;
}
.page-header::after {
    content: "";
    position: absolute; bottom: -50%; right: 10%;
    width: 180px; height: 180px;
    background: rgba(255,255,255,0.04);
    border-radius: 50%;
}
.page-header h1 {
    margin: 0; font-size: 1.75rem; font-weight: 800;
    letter-spacing: -0.01em; line-height: 1.2;
}
.page-header p {
    margin: 6px 0 0 0; opacity: 0.85; font-size: 0.9rem;
}

/* ─── ナビボタン（アクティブ状態） ─── */
div[class*="st-key-nav_dash"] button:not([disabled]) {
    background: linear-gradient(135deg, var(--blue-600), var(--blue-700)) !important;
    color: #fff !important; border: none !important;
}
div[class*="st-key-nav_dash"] button p { color: #fff !important; }
</style>
""", unsafe_allow_html=True)


# =========================
# 3. データ読み込み
# =========================
@st.cache_data
def load_hospital_data():
    try:
        return pd.read_csv("hospitals.csv")
    except FileNotFoundError:
        return pd.DataFrame()

hospitals_df = load_hospital_data()


# =========================
# 4. セッション状態 初期化
# =========================
def init_session():
    defaults = {
        "form_data":            {},
        "last_text":            "",
        "form_version":         0,
        "show_reset_confirm":   False,
        "is_registered":        False,
        "generated_file_path":  None,   # 互換用（旧）
        "generated_file_url":   None,   # 新：download API URL
        "generated_filename":   None,   # 新：ファイル名
        "search_results":       None,
        "logged_in":            False,
        "page_mode":            "login",
        "show_unsaved_warning": False,
        "staff_id":             "STAFF_01",
        "is_active":            False,
        "case_list":            pd.DataFrame(columns=["ID","患者名","ステータス","担当","登録日時"]),
        "case_store":           {},
        "stats":                {"total":0,"active":0,"done":0,"today":0},
        "is_new_session":       False,
        "current_case_id":      None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()


# =========================
# 5. ユーティリティ関数
# =========================
def _recalc_stats():
    cl = st.session_state.case_list
    st.session_state.stats["total"]  = len(cl)
    st.session_state.stats["active"] = int((cl["ステータス"] == "対応中").sum())
    st.session_state.stats["done"]   = int((cl["ステータス"] == "完了").sum())


def _save_to_case_store(case_id: str, form_data: dict, last_text: str,
                         status: str, staff: str,
                         word_file_path=None, word_file_url=None, filename=None):
    """case_store に完全なフォームデータを保存する"""
    import copy
    st.session_state.case_store[case_id] = {
        "form_data":  copy.deepcopy(form_data),
        "last_text":  last_text,
        "status":     status,
        "staff_id":   staff,
        # 互換＋新方式
        "word_file_path": word_file_path,
        "word_file_url":  word_file_url,
        "filename":       filename,
    }


def _upsert_case_list(case_id: str, patient_name: str,
                       status: str, staff: str) -> str:
    """case_list に行を追加または更新する。case_id を返す。"""
    if case_id is None:
        case_id = f"CASE-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    cl = st.session_state.case_list

    if case_id in cl["ID"].values:
        mask = cl["ID"] == case_id
        st.session_state.case_list.loc[mask, "患者名"] = patient_name or "未登録"
        st.session_state.case_list.loc[mask, "ステータス"] = status
        st.session_state.case_list.loc[mask, "担当"] = staff
    else:
        new_row = pd.DataFrame([{
            "ID":     case_id,
            "患者名": patient_name or "未登録",
            "ステータス": status,
            "担当":   staff,
            "登録日時": datetime.now().strftime("%m/%d %H:%M"),
        }])
        st.session_state.case_list = pd.concat([new_row, st.session_state.case_list], ignore_index=True)

    _recalc_stats()
    return case_id


def reset_all_fields():
    """フォームをすべてリセット（session_state ベース）"""
    st.session_state.form_data            = {}
    st.session_state.last_text            = ""
    st.session_state.form_version        += 1
    st.session_state.show_reset_confirm   = False
    st.session_state.is_registered        = False
    st.session_state.search_results       = None
    st.session_state.generated_file_path  = None
    st.session_state.generated_file_url   = None
    st.session_state.generated_filename   = None
    st.session_state.show_unsaved_warning = False
    st.session_state.current_case_id      = None

    try:
        requests.get(f"{BACKEND_URL}/reset_text/{st.session_state.staff_id}", timeout=2)
    except Exception:
        pass


def check_unsaved() -> bool:
    """未保存の変更があるか確認"""
    fd = st.session_state.form_data
    has_data = any([
        str(fd.get("name", "")).strip(),
        str(st.session_state.last_text).strip(),
        str(fd.get("symptoms", "")).strip(),
    ])
    return has_data and not st.session_state.is_registered


def on_text_area_change():
    """テキストエリア変更時の自動解析コールバック"""
    if not st.session_state.is_active:
        return
    key = f"text_area_{st.session_state.form_version}"
    if key in st.session_state:
        current = st.session_state[key]
        if current != st.session_state.last_text:
            st.session_state.last_text = current
            analyze_text(current)


def analyze_text(text: str):
    """会話テキスト → フォームデータ抽出"""
    if not text.strip():
        return
    prompt = f"""
# Role
あなたは日本の病院の受付アシスタントです。提供された会話テキストから診療申込書に必要な情報を抽出してください。

# Output Format
必ず以下のJSONフォーマットのみを出力してください。説明や補足は一切不要です。

{{
  "name": "氏名",
  "sex": "Male or Female",
  "birth": "YYYY/MM/DD",
  "age": "年齢",
  "address_jp": "日本での住所",
  "address_home": "本国の住所（短期滞在のみ）",
  "phone_home": "自宅電話",
  "phone_mobile": "携帯電話",
  "nationality": "国籍",
  "interpreter_req": "Yes or No",
  "native_lang": "母国語",
  "other_langs": "対応可能言語",
  "occupation": "職業",
  "religion_care": "宗教上の配慮事項",
  "emergency_name": "緊急連絡先氏名",
  "emergency_rel": "緊急連絡先との関係",
  "emergency_address": "緊急連絡先住所",
  "emergency_home": "緊急連絡先自宅電話",
  "emergency_mobile": "緊急連絡先携帯",
  "residency_status": "滞在状況(Resident/Short-term stay/Student/Other)",
  "reason_choosing": "当院を選んだ理由",
  "first_visit": "初診(Yes/No)",
  "referral_letter": "紹介状(Yes/No)",
  "referral_institution": "紹介元医療機関名",
  "appointment": "予約(Yes/No)",
  "insurance_type": "保険の種類(Japanese public/Japanese private/Overseas/Uninsured)",
  "insurance_company": "保険会社名",
  "departments": ["希望診療科をリストから選択"],
  "symptoms": "具体的な症状"
}}

# Constraints
- address_jp: 日本での住所を抽出。具体的な住所がない場合は滞在先のキーワードを抽出。
- departments は以下のリストから英語名で配列として抽出:
  Internal Medicine, Psychosomatic Medicine, Neurology, Pulmonology, Gastroenterology,
  Cardiovascular medicine, Nephrology, Pediatrics, Surgery, Orthopedic surgery,
  Neurosurgery, Thoracic Surgery, Cardiovascular Surgery, Dermatology, Urology,
  Obstetrics and Gynecology, Ophthalmology, Otorhinolaryngology, Dentistry, Other
- 情報が見つからない場合は空文字または空リストを返す。

# Conversation Text
{text}
"""
    try:
        res = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        st.session_state.form_data  = json.loads(res.choices[0].message.content)
        st.session_state.form_version += 1
    except Exception as e:
        st.error(f"解析エラー: {e}")


def get_recommended_hospitals(symptoms, address_jp):
    if not symptoms or hospitals_df.empty:
        return None, pd.DataFrame()

    prefs = [
        "北海道","青森県","岩手県","宮城県","秋田県","山形県","福島県",
        "茨城県","栃木県","群馬県","埼玉県","千葉県","東京都","神奈川県",
        "新潟県","富山県","石川県","福井県","山梨県","長野県","岐阜県",
        "静岡県","愛知県","三重県","滋賀県","京都府","大阪府","兵庫県",
        "奈良県","和歌山県","鳥取県","島根県","岡山県","広島県","山口県",
        "徳島県","香川県","愛媛県","高知県","福岡県","佐賀県","長崎県",
        "熊本県","大分県","宮崎県","鹿児島県","沖縄県",
    ]
    target_pref = next((p for p in prefs if p in str(address_jp)), None)

    if not target_pref and address_jp:
        try:
            r = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role":"user","content": f"「{address_jp}」は日本の何県ですか？県名のみ。不明なら「不明」。"}],
                temperature=0.0,
            )
            guess = r.choices[0].message.content.strip()
            target_pref = next((p for p in prefs if p in guess), None)
        except Exception:
            pass

    available = ", ".join(hospitals_df["診療科"].unique())
    try:
        r2 = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":
                f"症状「{symptoms}」に最適な診療科を以下から1つ選んでください。出力は診療科名のみ。\nリスト: {available}"}],
            temperature=0.1,
        )
        dept = r2.choices[0].message.content.strip()
        matched = hospitals_df[hospitals_df["診療科"].str.contains(dept, na=False)]
        final = pd.DataFrame()
        if target_pref:
            final = matched[matched["都道府県"] == target_pref]
        if len(final) < 3:
            final = pd.concat([final, matched[~matched.index.isin(final.index)].head(3 - len(final))])
        if len(final) < 3:
            final = pd.concat([final, hospitals_df[~hospitals_df.index.isin(final.index)].head(3 - len(final))])
        return f"{dept}（{target_pref or '広域'}）", final.head(3)
    except Exception:
        return "一般内科（広域）", hospitals_df.head(3)


# =========================
# 6. ログイン画面
# =========================
def render_login():
    st.markdown("""
    <div class="page-header" style="text-align:center;">
        <h1>🏥 AI Medical Assistant</h1>
        <p>医療受付スタッフ専用　リアルタイム問診サポートシステム</p>
    </div>
    """, unsafe_allow_html=True)

    _, col_center, _ = st.columns([1, 1.2, 1])

    with col_center:
        st.markdown(
            """
            <style>
            div[data-testid="stForm"] {
                background-color: white !important;
                padding: 40px !important;
                border-radius: 16px !important;
                border: 1px solid #D1E2FF !important;
                box-shadow: 0 10px 25px rgba(0,0,0,0.05) !important;
            }
            div[data-testid="stForm"] label p {
                color: #1E293B !important;
                font-weight: 600 !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        with st.form("login_form", clear_on_submit=False, border=False):
            st.markdown(
                """
                <div style="text-align:center;">
                    <h3 style="margin:0; color:#1E293B;">🔐 Staff Login</h3>
                    <p style="color:#64748B; font-size:0.85rem; margin-top:10px; margin-bottom:20px;">
                        IDとパスワードを入力してEnterを押してください
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            user = st.text_input("ユーザー名", placeholder="admin")
            pw = st.text_input("パスワード", type="password", placeholder="••••••••")

            st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

            login_btn = st.form_submit_button("ログイン", type="primary", use_container_width=True)

            if login_btn:
                if user == "admin" and pw == "pass123":
                    st.session_state.logged_in = True
                    st.session_state.page_mode = "dashboard"
                    st.success("認証に成功しました。")
                    st.rerun()
                else:
                    st.error("ユーザー名またはパスワードが正しくありません。")

    st.markdown("""
    <div style="text-align:center; color:#94A3B8; font-size:0.75rem; margin-top:2.5rem;">
        © 2024 AI Medical Assistant Team. All rights reserved.
    </div>
    """, unsafe_allow_html=True)


# =========================
# 7. ダッシュボード画面
# =========================
def render_dashboard():
    st.markdown("""
    <div class="page-header">
        <h1>🏥 ダッシュボード</h1>
        <p>受付ケースの進捗と本日の受付状況をリアルタイムに管理します</p>
    </div>
    """, unsafe_allow_html=True)

    nav1, nav2, nav3, _, nav_out = st.columns([1.1, 1.3, 0.8, 2.5, 0.9])
    with nav1:
        st.button("📊 ダッシュボード", key="nav_dash", use_container_width=True, disabled=True)
    with nav2:
        if st.button("＋ 新しいセッション", use_container_width=True, type="primary"):
            reset_all_fields()
            for k in ["selected_case","delete_target_case","show_unsaved_warning","case_selector"]:
                st.session_state.pop(k, None)
            st.session_state.page_mode   = "case"
            st.session_state.is_new_session = True
            st.rerun()
    with nav3:
        pass
    with nav_out:
        if st.button("ログアウト", key="logout_dashboard", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.page_mode = "login"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    stats = st.session_state.stats
    c1, c2, c3, c4 = st.columns(4)
    cards = [
        (c1, "📁", str(stats["total"]),  "総ケース数", "累計",     "#2563EB"),
        (c2, "⏳", str(stats["active"]), "対応中",    "進行中",   "#D97706"),
        (c3, "✅", str(stats["done"]),   "完了済み",   "クローズ", "#16A34A"),
        (c4, "👤", str(stats["today"]),  "今日の新規", "本日受付", "#7C3AED"),
    ]
    for col, icon, val, label, sub, color in cards:
        with col:
            st.markdown(f"""
            <div class="metric-wrap">
                <div class="metric-icon">{icon}</div>
                <div class="metric-val" style="color:{color};">{val}</div>
                <div class="metric-label">{label}</div>
                <div class="metric-sub">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    left_col, right_col = st.columns([2.6, 1.4])

    with left_col:
        with st.container(border=True):
            st.markdown("""
            <div class="card-title">📂 ケース一覧</div>
            <div class="card-sub">クリックして選択 → セッションで編集 / ステータスを変更できます</div>
            """, unsafe_allow_html=True)

            search = st.text_input("🔍 検索（患者名・ID）",
                                   placeholder="山田太郎 / CASE-...",
                                   label_visibility="collapsed")

            cl = st.session_state.case_list
            if cl.empty:
                st.info("📭 まだケースがありません。「＋ 新しいセッション」から開始してください。")
            else:
                show = cl if not search else cl[
                    cl["患者名"].str.contains(search, case=False, na=False) |
                    cl["ID"].str.contains(search, case=False, na=False)
                ]
                show = show.head(10).copy()
                show["選択"] = False

                edited = st.data_editor(
                    show,
                    column_config={
                        "選択":     st.column_config.CheckboxColumn("✔", width="small"),
                        "ID":       st.column_config.TextColumn("ケースID",   disabled=True, width="medium"),
                        "患者名":   st.column_config.TextColumn("患者名",     disabled=True),
                        "ステータス": st.column_config.SelectboxColumn("ステータス", options=["対応中","完了"], width="small"),
                        "担当":     st.column_config.TextColumn("担当",       disabled=True, width="small"),
                        "登録日時": st.column_config.TextColumn("登録日時",   disabled=True, width="small"),
                    },
                    disabled=["ID","患者名","担当","登録日時"],
                    hide_index=True,
                    use_container_width=True,
                    key="case_selector",
                )

                if "case_selector" in st.session_state:
                    for idx, changes in st.session_state.case_selector.get("edited_rows",{}).items():
                        ns = changes.get("ステータス")
                        if ns:
                            cid = show.iloc[idx]["ID"]
                            st.session_state.case_list.loc[st.session_state.case_list["ID"] == cid, "ステータス"] = ns
                            if cid in st.session_state.case_store:
                                st.session_state.case_store[cid]["status"] = ns
                    _recalc_stats()

                sel_rows = []
                if "case_selector" in st.session_state:
                    for idx, changes in st.session_state.case_selector.get("edited_rows",{}).items():
                        if changes.get("選択", False):
                            sel_rows.append(show.iloc[idx])

                if sel_rows:
                    sc = sel_rows[-1]
                    st.markdown("---")
                    ia, ib, ic = st.columns([2, 1, 1])
                    with ia:
                        badge_cls = "badge-done" if sc["ステータス"]=="完了" else "badge-active"
                        st.markdown(f"""
                        <div style="display:flex;align-items:center;gap:8px;padding:6px 0;">
                            <span style="font-weight:700;color:#1E293B;">{sc['患者名']}</span>
                            <span class="badge {badge_cls}">{sc['ステータス']}</span>
                            <span style="font-size:0.78rem;color:#94A3B8;">{sc['ID']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    with ib:
                        if st.button("✏️ 開いて編集", use_container_width=True, type="primary"):
                            st.session_state.selected_case = sc.to_dict()
                            st.session_state.page_mode = "case"
                            st.rerun()
                    with ic:
                        if st.button("🗑️ 削除", use_container_width=True):
                            st.session_state.delete_target = sc.to_dict()
                            st.rerun()

                if "delete_target" in st.session_state:
                    st.markdown("---")
                    dt = st.session_state.delete_target
                    st.error(f"🗑️ **{dt['患者名']}**（{dt['ID']}）を削除しますか？")
                    if dt["ステータス"] == "完了":
                        st.warning("⚠️ DBからも削除されます")
                    d1, d2 = st.columns(2)
                    with d1:
                        if st.button("キャンセル", use_container_width=True):
                            del st.session_state.delete_target
                            st.rerun()
                    with d2:
                        if st.button("🗑️ 削除実行", use_container_width=True, type="primary"):
                            cid = dt["ID"]
                            st.session_state.case_list = st.session_state.case_list[
                                st.session_state.case_list["ID"] != cid
                            ].reset_index(drop=True)
                            st.session_state.case_store.pop(cid, None)

                            if dt["ステータス"] == "完了":
                                try:
                                    # ✅ backendにも削除を依頼（main.pyで実装済みにしてあります）
                                    requests.delete(f"{BACKEND_URL}/delete_patient/{cid}", timeout=5)
                                except Exception:
                                    pass

                            _recalc_stats()
                            del st.session_state.delete_target
                            st.rerun()

    with right_col:
        with st.container(border=True):
            st.markdown("""<div class="card-title">💡 使い方ガイド</div>""", unsafe_allow_html=True)
            st.markdown("""
            <div class="guide-box">
                <b>🆕 新規受付</b><br>
                「＋ 新しいセッション」から患者情報の入力を開始します。
            </div>
            <br>
            <div class="guide-box" style="border-left-color:#16A34A; background:#F0FDF4;">
                <b>🔄 既存ケースの編集</b><br>
                一覧でケースを選択し「開いて編集」を押すと、<b>前回の入力内容が復元</b>されます。
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
            <div style="font-size:0.8rem; color:#64748B; line-height:1.9;">
                <b style="color:#1E3A5F;">操作の流れ</b><br>
                ① リアルタイム解析を有効化<br>
                ② 通話内容から自動で情報を抽出<br>
                ③ フォームを確認・修正<br>
                ④ 一時保存 または 正式保存<br>
                ⑤ Word書類をダウンロード
            </div>
            """, unsafe_allow_html=True)


# =========================
# 8. ケースセッション画面
# =========================
def render_case_session():

    # ★★★ ケース復元（ダッシュボードから開いた場合）★★★
    if "selected_case" in st.session_state:
        sc = st.session_state.selected_case
        case_id = sc.get("ID")

        if case_id and case_id in st.session_state.case_store:
            stored = st.session_state.case_store[case_id]
            st.session_state.form_data           = stored.get("form_data", {})
            st.session_state.last_text           = stored.get("last_text", "")
            st.session_state.generated_file_path = stored.get("word_file_path")  # 互換
            st.session_state.generated_file_url  = stored.get("word_file_url")
            st.session_state.generated_filename  = stored.get("filename")
            st.session_state.is_registered       = True
        else:
            st.session_state.form_data = {"name": sc.get("患者名", "")}
            st.session_state.last_text = ""
            st.session_state.is_registered = False

        st.session_state.current_case_id = case_id
        st.session_state.staff_id        = sc.get("担当", st.session_state.staff_id)
        st.session_state.form_version   += 1
        del st.session_state.selected_case

    if st.session_state.get("is_new_session", False):
        st.session_state.is_new_session = False

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # サイドバー
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    with st.sidebar:
        st.markdown("### 📡 接続設定")

        st.session_state.staff_id = st.selectbox(
            "担当スタッフ",
            ["STAFF_01","STAFF_02","STAFF_03"],
            index=["STAFF_01","STAFF_02","STAFF_03"].index(st.session_state.staff_id),
        )
        st.session_state.is_active = st.toggle("🔴 リアルタイム解析", value=st.session_state.is_active)

        staff_id  = st.session_state.staff_id
        is_active = st.session_state.is_active

        if is_active:
            st.markdown(f"""
            <div style="background:#FFF0F0;border:1px solid #FECACA;border-radius:10px;
                        padding:10px 12px;margin:6px 0;">
                <div style="font-size:0.78rem;color:#6B7280;margin-bottom:2px;">接続ステータス</div>
                <div style="font-weight:700;color:#DC2626;display:flex;align-items:center;gap:6px;">
                    <span class="badge badge-live">● LIVE</span>
                    {staff_id}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;
                        padding:10px 12px;margin:6px 0;">
                <div style="font-size:0.78rem;color:#6B7280;margin-bottom:2px;">接続ステータス</div>
                <div style="font-weight:600;color:#64748B;">⚫ 停止中 — {staff_id}</div>
            </div>
            """, unsafe_allow_html=True)

        cid = st.session_state.current_case_id
        if cid:
            st.markdown(f"""
            <div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:10px;
                        padding:10px 12px;margin:6px 0;">
                <div style="font-size:0.78rem;color:#3B82F6;font-weight:600;margin-bottom:2px;">
                    ✏️ 編集中ケース
                </div>
                <div style="font-size:0.82rem;color:#1D4ED8;font-weight:700;">{cid}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### ⚙️ 設定")

        if not st.session_state.show_reset_confirm:
            if st.button("🗑️ フォームをリセット", use_container_width=True):
                st.session_state.show_reset_confirm = True
                st.rerun()
        else:
            if not st.session_state.is_registered:
                st.warning("⚠️ 未登録データが消えます。よろしいですか？")
            else:
                st.info("📋 登録済みデータです。表示のみクリアします。")
            rb1, rb2 = st.columns(2)
            with rb1:
                if st.button("はい", type="primary", use_container_width=True):
                    reset_all_fields()
                    st.rerun()
            with rb2:
                if st.button("いいえ", use_container_width=True):
                    st.session_state.show_reset_confirm = False
                    st.rerun()

        st.markdown("---")
        st.markdown("""
        <div class="guide-box" style="font-size:0.78rem;">
            <b>① 左カラム</b>：通話ログの確認・編集<br>
            <b>② 中央カラム</b>：フォームの確認・修正<br>
            <b>③ 右カラム</b>：病院検索・保存・ダウンロード
        </div>
        """, unsafe_allow_html=True)

    staff_id  = st.session_state.staff_id
    is_active = st.session_state.is_active

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 自動更新（リアルタイム解析中）
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if is_active:
        st_autorefresh(interval=5000, key="datarefresh")
        try:
            r = requests.get(f"{BACKEND_URL}/get_text/{staff_id}", timeout=3)
            if r.status_code == 200:
                text = r.json().get("text","")
                if text and text != st.session_state.last_text:
                    st.session_state.last_text = text
                    analyze_text(text)
                    st.rerun()
        except Exception:
            st.sidebar.warning("⚠️ サーバー接続待機中...")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ヘッダー
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    cid = st.session_state.current_case_id
    is_edit_mode = (cid is not None)

    header_right = ""
    if is_active:
        header_right = "<span style='position:absolute;top:18px;right:20px;background:rgba(255,255,255,0.18);padding:3px 12px;border-radius:20px;font-size:0.78rem;font-weight:700;'>● LIVE</span>"
    if is_edit_mode:
        header_right += f"<span style='position:absolute;bottom:14px;right:20px;background:rgba(255,255,255,0.12);padding:3px 12px;border-radius:20px;font-size:0.75rem;'>🔄 上書き編集中: {cid}</span>"

    subtitle = "既存ケースを編集中 — 上書き保存できます" if is_edit_mode else "通話内容からリアルタイムに診療申込書を自動生成します"
    st.markdown(f"""
    <div class="page-header" style="padding-bottom:{'2.2rem' if is_edit_mode else '1.8rem'}">
        <h1>🏥 AI Medical Assistant</h1>
        <p>{subtitle}</p>
        {header_right}
    </div>
    """, unsafe_allow_html=True)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ナビゲーション
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    n1, n2, n3, _, nout = st.columns([0.9, 0.8, 0.9, 3.2, 0.8])
    with n1:
        if st.button("📊 ダッシュボード", use_container_width=True):
            if check_unsaved():
                st.session_state.show_unsaved_warning = True
                st.rerun()
            else:
                st.session_state.page_mode = "dashboard"
                st.rerun()
    with n2:
        st.button("📝 セッション", use_container_width=True, disabled=True)
    with n3:
        mode_label = "🔄 上書き" if is_edit_mode else "🆕 新規"
        st.markdown(f"""
        <div style="display:flex;align-items:center;height:38px;padding:0 8px;
                    background:{'#EFF6FF' if is_edit_mode else '#F0FDF4'};
                    border:1px solid {'#BFDBFE' if is_edit_mode else '#BBF7D0'};
                    border-radius:999px;font-size:0.78rem;font-weight:600;
                    color:{'#1D4ED8' if is_edit_mode else '#15803D'};">
            {mode_label}
        </div>
        """, unsafe_allow_html=True)
    with nout:
        if st.button("ログアウト", key="logout_case", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.page_mode = "login"
            st.rerun()

    if st.session_state.show_unsaved_warning:
        with st.container(border=True):
            st.warning("⚠️ **未保存の変更があります。** 破棄してダッシュボードに戻りますか？")
            wa, wb, _ = st.columns([1,1,2])
            with wa:
                if st.button("← 入力に戻る", use_container_width=True):
                    st.session_state.show_unsaved_warning = False
                    st.rerun()
            with wb:
                if st.button("🗑️ 破棄して戻る", use_container_width=True, type="primary"):
                    reset_all_fields()
                    st.session_state.page_mode = "dashboard"
                    st.rerun()

    st.markdown("---")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 3カラム構成
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    col_l, col_c, col_r = st.columns([1.05, 1.55, 1.1])
    v = st.session_state.form_version
    f = st.session_state.form_data

    # 左カラム：リアルタイムログ
    with col_l:
        with st.container(border=True):
            st.markdown("""
            <div class="card-title">🎙️ リアルタイムログ</div>
            <div class="card-sub">通話内容を確認・編集し、再解析できます</div>
            """, unsafe_allow_html=True)

        edited_text = st.text_area(
            "通話内容",
            value=st.session_state.last_text,
            height=380,
            key=f"text_area_{v}",
            on_change=on_text_area_change,
            label_visibility="collapsed",
            placeholder="ここに通話内容が表示されます…\nまたはテキストを直接入力して「再解析」できます。",
        )

        b1, b2 = st.columns([1.2, 1])
        with b1:
            if st.button("🔄 再解析", use_container_width=True, type="primary"):
                st.session_state.last_text = edited_text
                with st.spinner("解析中..."):
                    analyze_text(edited_text)
                st.rerun()
        with b2:
            st.markdown(f"""
            <div style="display:flex;align-items:center;justify-content:center;
                        height:38px;font-size:0.78rem;color:#94A3B8;">
                📝 {len(edited_text)} 文字
            </div>
            """, unsafe_allow_html=True)

    # 中央カラム：フォーム
    with col_c:
        with st.container(border=True):
            st.markdown("""
            <div class="card-title">📋 診療申込フォーム（編集可）</div>
            <div class="card-sub">AIが抽出した情報です。必要に応じて上書きしてください</div>
            """, unsafe_allow_html=True)

        with st.container(height=SCROLL_HEIGHT):
            st.markdown('<div class="section-header">👤 基本情報</div>', unsafe_allow_html=True)
            u_name  = st.text_input("氏名 / Name ＊", value=f.get("name",""), key=f"n_{v}")
            ca, cb, cc = st.columns(3)
            u_sex   = ca.selectbox("性別", ["Male","Female"],
                                    index=0 if f.get("sex","Male")!="Female" else 1,
                                    key=f"s_{v}")
            u_birth = cb.text_input("生年月日 (YYYY/MM/DD)", value=f.get("birth",""), key=f"b_{v}")
            u_age   = cc.text_input("年齢", value=f.get("age",""), key=f"a_{v}")

            st.markdown('<div class="section-header">📍 連絡先・国籍</div>', unsafe_allow_html=True)
            u_addr_jp   = st.text_area("日本での住所", value=f.get("address_jp",""),  key=f"aj_{v}", height=72)
            u_addr_home = st.text_area("本国住所", value=f.get("address_home",""), key=f"ah_{v}", height=60)
            d1, d2 = st.columns(2)
            u_phone_h = d1.text_input("電話（自宅）", value=f.get("phone_home",""),   key=f"ph_{v}")
            u_phone_m = d2.text_input("電話（携帯）", value=f.get("phone_mobile",""), key=f"pm_{v}")
            d3, d4 = st.columns(2)
            u_nat = d3.text_input("国籍", value=f.get("nationality",""), key=f"nat_{v}")
            u_occ = d4.text_input("職業", value=f.get("occupation",""),  key=f"occ_{v}")

            st.markdown('<div class="section-header">🌐 言語・宗教的配慮</div>', unsafe_allow_html=True)
            e1, e2 = st.columns(2)
            u_intp = e1.radio("通訳希望", ["Yes","No"],
                               index=0 if f.get("interpreter_req")=="Yes" else 1,
                               horizontal=True, key=f"int_{v}")
            u_lang  = e2.text_input("母国語", value=f.get("native_lang",""), key=f"lan_{v}")
            u_other_lang = st.text_input("他言語", value=f.get("other_langs",""),  key=f"ol_{v}")
            u_religion   = st.text_area("宗教上の配慮", value=f.get("religion_care",""), key=f"rel_{v}", height=60)

            st.markdown('<div class="section-header">🚨 緊急連絡先</div>', unsafe_allow_html=True)
            u_em_name = st.text_input("氏名",     value=f.get("emergency_name",""),     key=f"en_{v}")
            u_em_rel  = st.text_input("続柄",     value=f.get("emergency_rel",""),      key=f"er_{v}")
            u_em_addr = st.text_input("住所",     value=f.get("emergency_address",""),  key=f"ea_{v}")
            f1, f2 = st.columns(2)
            u_em_h = f1.text_input("自宅電話", value=f.get("emergency_home",""),    key=f"eh_{v}")
            u_em_m = f2.text_input("携帯電話", value=f.get("emergency_mobile",""),  key=f"em_{v}")

            st.markdown('<div class="section-header">🏨 滞在・受診情報</div>', unsafe_allow_html=True)
            RES_OPTS = ["Resident","Short-term stay","Student","Other"]
            cur_res  = f.get("residency_status","Resident")
            u_residency = st.selectbox("滞在状況", RES_OPTS,
                                        index=RES_OPTS.index(cur_res) if cur_res in RES_OPTS else 0,
                                        key=f"rs_{v}")
            u_reason = st.text_area("当院を選んだ理由", value=f.get("reason_choosing",""), key=f"rc_{v}", height=60)
            g1, g2, g3 = st.columns(3)
            u_first = g1.radio("初診？",  ["Yes","No"], key=f"fv_{v}")
            u_ref   = g2.radio("紹介状？", ["Yes","No"], key=f"rl_{v}")
            u_appo  = g3.radio("予約？",  ["Yes","No"], key=f"ap_{v}")
            u_ref_inst = st.text_input("紹介元機関名", value=f.get("referral_institution",""), key=f"ri_{v}")

            st.markdown('<div class="section-header">🏥 保険・診療科・症状</div>', unsafe_allow_html=True)
            INS_KEYS = ["Japanese public","Japanese private","Overseas","Uninsured"]
            INS_DISP = {
                "Japanese public":  "日本 公的保険",
                "Japanese private": "日本 民間保険",
                "Overseas":         "海外保険",
                "Uninsured":        "未加入",
            }
            cur_ins = f.get("insurance_type","Japanese public")
            u_ins_type = st.selectbox(
                "保険種別",
                options=INS_KEYS,
                format_func=lambda x: INS_DISP[x],
                index=INS_KEYS.index(cur_ins) if cur_ins in INS_KEYS else 0,
                key=f"it_{v}",
            )
            u_ins_comp = st.text_input("保険会社名", value=f.get("insurance_company",""), key=f"ic_{v}")

            DEPT_LIST = [
                "Internal Medicine","Psychosomatic Medicine","Neurology","Pulmonology",
                "Gastroenterology","Cardiovascular medicine","Nephrology","Pediatrics",
                "Surgery","Orthopedic surgery","Neurosurgery","Thoracic Surgery",
                "Cardiovascular Surgery","Dermatology","Urology",
                "Obstetrics and Gynecology","Ophthalmology","Otorhinolaryngology",
                "Dentistry","Other",
            ]
            raw_depts     = f.get("departments",[])
            default_depts = raw_depts if isinstance(raw_depts, list) else []
            u_depts = st.multiselect("希望診療科", DEPT_LIST, default=default_depts, key=f"dept_{v}")
            u_symptoms = st.text_area("症状 ＊", value=f.get("symptoms",""), height=100, key=f"symp_{v}")

    # 右カラム：病院検索 & 保存
    with col_r:
        with st.container(border=True):
            st.markdown("""
            <div class="card-title">🤖 AI提案 & 保存</div>
            <div class="card-sub">病院の自動提案と書類作成・保存を行います</div>
            """, unsafe_allow_html=True)

        if st.button("🔍 近隣の病院を検索", use_container_width=True):
            if u_symptoms:
                with st.spinner("病院を検索中..."):
                    di, mdf = get_recommended_hospitals(u_symptoms, u_addr_jp)
                    st.session_state.search_results = {"dept_info":di, "matched_df":mdf}
            else:
                st.warning("⚠️ 症状を入力してください")

        if st.session_state.search_results:
            sr = st.session_state.search_results
            if not sr["matched_df"].empty:
                st.success(f"💡 推奨診療科: **{sr['dept_info']}**")
                for _, row in sr["matched_df"].iterrows():
                    with st.expander(f"🏢 {row['病院名']}（{row['都道府県']}）"):
                        st.write(f"📍 {row['住所']}")
                        st.write(f"📞 {row['電話番号']}")
                        st.write(f"✨ {row['特徴']}")
                        st.write(f"🌐 {row['対応言語']}")
            else:
                st.warning("該当病院が見つかりませんでした")

        st.markdown("---")

        def _validate():
            errs = []
            if not str(u_name).strip():
                errs.append("患者名（氏名）を入力してください")
            return errs

        is_edit = st.session_state.current_case_id is not None

        # ── 一時保存（対応中） ──
        temp_label = "⏳ 上書き一時保存" if is_edit else "⏳ 一時保存（対応中）"
        if st.button(temp_label, use_container_width=True, key="temp_save_btn"):
            errs = _validate()
            if errs:
                for e in errs:
                    st.warning(f"⚠️ {e}")
            else:
                with st.status("一時保存中...", expanded=False) as s:
                    st.write("ケースを保存しています...")
                    was_new = not st.session_state.is_registered
                    cid = _upsert_case_list(st.session_state.current_case_id, u_name, "対応中", staff_id)
                    _save_to_case_store(
                        cid,
                        {
                            "name":u_name,"sex":u_sex,"birth":u_birth,"age":u_age,
                            "address_jp":u_addr_jp,"address_home":u_addr_home,
                            "phone_home":u_phone_h,"phone_mobile":u_phone_m,
                            "nationality":u_nat,"occupation":u_occ,
                            "interpreter_req":u_intp,"native_lang":u_lang,
                            "other_langs":u_other_lang,"religion_care":u_religion,
                            "emergency_name":u_em_name,"emergency_rel":u_em_rel,
                            "emergency_address":u_em_addr,"emergency_home":u_em_h,
                            "emergency_mobile":u_em_m,"residency_status":u_residency,
                            "reason_choosing":u_reason,"first_visit":u_first,
                            "referral_letter":u_ref,"referral_institution":u_ref_inst,
                            "appointment":u_appo,"insurance_type":u_ins_type,
                            "insurance_company":u_ins_comp,"departments":u_depts,
                            "symptoms":u_symptoms,
                        },
                        st.session_state.last_text,
                        "対応中",
                        staff_id,
                        word_file_path=st.session_state.generated_file_path,
                        word_file_url=st.session_state.generated_file_url,
                        filename=st.session_state.generated_filename,
                    )
                    st.session_state.current_case_id = cid
                    st.session_state.is_registered   = True
                    if was_new:
                        st.session_state.stats["today"] += 1
                    s.update(label="✅ 一時保存完了", state="complete")

                st.success("✅ ダッシュボードに保存しました（対応中）")
                time.sleep(0.8)
                st.session_state.page_mode = "dashboard"
                st.rerun()

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        # ── 正式保存 + Word生成 ──
        save_label = "💾 上書き保存 & 書類更新" if is_edit else "💾 正式保存 & 書類作成"
        save_key   = "overwrite_btn" if is_edit else "final_save_btn"

        if st.button(save_label, use_container_width=True, type="primary", key=save_key):
            errs = _validate()
            if errs:
                for e in errs:
                    st.warning(f"⚠️ {e}")
            else:
                with st.status("保存・書類作成中...", expanded=True) as s:
                    st.write("📋 バリデーション OK")

                    # ✅ 既存機能維持のため、case_id を送って “上書き” を安定化
                    payload = {
                        "case_id": st.session_state.current_case_id,  # 追加
                        "staff_id": staff_id, "name": u_name, "sex": u_sex,
                        "birth": u_birth, "age": u_age,
                        "address_jp": u_addr_jp, "address_home": u_addr_home,
                        "phone_home": u_phone_h, "phone_mobile": u_phone_m,
                        "nationality": u_nat, "interpreter_req": u_intp,
                        "native_lang": u_lang, "other_langs": u_other_lang,
                        "occupation": u_occ, "religion_care": u_religion,
                        "emergency_name": u_em_name, "emergency_rel": u_em_rel,
                        "emergency_address": u_em_addr,
                        "emergency_phone_home": u_em_h,
                        "emergency_phone_mobile": u_em_m,
                        "residency_status": u_residency,
                        "reason_choosing": u_reason, "first_visit": u_first,
                        "referral_letter": u_ref,
                        "referral_institution": u_ref_inst,
                        "appointment": u_appo, "insurance_type": u_ins_type,
                        "insurance_company": u_ins_comp,
                        "departments": u_depts, "symptoms": u_symptoms,
                    }

                    st.write("🚀 サーバーへ送信中...")

                    try:
                        resp = requests.post(f"{BACKEND_URL}/save_patient", json=payload, timeout=20)
                        # 1. ネットワークエラーや500エラーを即座にチェック
                        resp.raise_for_status() 

                        # 2. JSONとして解析（ここで失敗したら ValueError へ）
                        res_data = resp.json()

                        if resp.status_code == 200:
                            res_data = resp.json()

                            # ✅ 新方式：download_url を保存
                            download_url = res_data.get("download_url")
                            filename     = res_data.get("filename")
                            # 互換用：word_file（サーバー内部パス）も来るがUIでは使わない
                            word_path    = res_data.get("word_file")

                            st.session_state.generated_file_path = word_path
                            st.session_state.generated_filename  = filename
                            st.session_state.generated_file_url  = f"{BACKEND_URL}{download_url}" if download_url else None

                            was_new = not st.session_state.is_registered

                            full_fd = {
                                "case_id": cid,           # 追加
                                "staff_id": staff_id,     # 追加
                                "name": u_name,
                                "sex": u_sex,
                                "birth": u_birth,
                                "age": u_age,
                                "address_jp": u_addr_jp,
                                "address_home": u_addr_home,
                                "phone_home": u_phone_h,
                                "phone_mobile": u_phone_m,
                                "nationality": u_nat,
                                "occupation": u_occ,
                                "interpreter_req": u_intp,
                                "native_lang": u_lang,
                                "other_langs": u_other_lang,
                                "religion_care": u_religion,
                                "emergency_name": u_em_name,
                                "emergency_rel": u_em_rel,
                                "emergency_address": u_em_addr,
                                # ↓ サーバー側に合わせて "phone_" を追加
                                "emergency_phone_home": u_em_h,
                                "emergency_phone_mobile": u_em_m,
                                "residency_status": u_residency,
                                "reason_choosing": u_reason,
                                "first_visit": u_first,
                                "referral_letter": u_ref,
                                "referral_institution": u_ref_inst,
                                "appointment": u_appo,
                                "insurance_type": u_ins_type,
                                "insurance_company": u_ins_comp,
                                "departments": u_depts,
                                "symptoms": u_symptoms,
                            }

                            cid = _upsert_case_list(st.session_state.current_case_id, u_name, "完了", staff_id)
                            _save_to_case_store(
                                cid, full_fd, st.session_state.last_text,
                                "完了", staff_id,
                                word_file_path=word_path,
                                word_file_url=st.session_state.generated_file_url,
                                filename=filename,
                            )

                            st.session_state.current_case_id = cid
                            st.session_state.is_registered   = True
                            if was_new:
                                st.session_state.stats["today"] += 1

                            st.write("✅ DB保存完了")
                            st.write("📄 Word書類生成完了")
                            s.update(label="✅ 保存・書類作成完了", state="complete", expanded=False)
                            st.balloons()

                        else:
                            # ❌ サーバー側でエラー（500/422等）が発生した場合
                            st.error(f"サーバーエラー発生 (Status: {resp.status_code})")
                            
                            # 原因を特定するための「生」の情報を表示
                            with st.expander("デバッグ詳細（ここを教えてください）", expanded=True):
                                try:
                                    # FastAPIが詳細を返している場合（バリデーションエラーなど）
                                    st.json(resp.json())
                                except:
                                    # JSONですらない致命的エラー（コードのバグなど）の場合
                                    st.code(resp.text)
                            
                            s.update(label="❌ 保存失敗", state="error")

                    except requests.exceptions.Timeout:
                        st.error("サーバーが時間内に応答しませんでした。")
                        s.update(label="❌ タイムアウト", state="error")
                    except Exception as e:
                        st.error(f"通信エラー: {e}")
                        s.update(label="❌ 接続エラー", state="error")

        st.markdown("---")

        # ── ダウンロード（新方式：HTTPで取得してdownload_buttonへ） ──
        file_url = st.session_state.get("generated_file_url")
        if file_url:
            try:
                r = requests.get(file_url, timeout=20)
                if r.status_code == 200:
                    st.download_button(
                        label="📄 診療申込書をダウンロード",
                        data=r.content,
                        file_name=f"診療申込書_{u_name or '患者名未設定'}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                        type="primary",
                        key="dl_btn",
                    )
                else:
                    st.warning(f"📄 ダウンロード準備中…（{r.status_code}）")
            except Exception as e:
                st.warning(f"📄 ダウンロード取得エラー: {e}")
        else:
            st.markdown("""
            <div style="text-align:center;padding:12px;background:#F8FAFC;
                        border:1px dashed #CBD5E1;border-radius:10px;
                        font-size:0.82rem;color:#94A3B8;">
                📄 正式保存後にダウンロード可能になります
            </div>
            """, unsafe_allow_html=True)

        if st.session_state.is_registered:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.button("📊 ダッシュボードへ戻る", use_container_width=True):
                st.session_state.page_mode = "dashboard"
                st.rerun()


# =========================
# 9. メインルーティング
# =========================
if not st.session_state.logged_in:
    st.session_state.page_mode = "login"
    render_login()
else:
    if st.session_state.page_mode == "case":
        render_case_session()
    else:
        render_dashboard()
