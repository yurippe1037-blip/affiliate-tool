import os
import json
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

# -------------------------------------------------------------
# 0. 環境変数の読み込み（APIキーはここから取得。コードに直書きしない）
# -------------------------------------------------------------
load_dotenv()
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

# -------------------------------------------------------------
# 1. ページ全体の初期設定
# -------------------------------------------------------------
st.set_page_config(
    page_title="Affiliate Post",
    page_icon="🌸",
    layout="wide",
)

st.markdown("""
    <style>
    /* ===== カラーパレット =====
       背景: 温かみのあるオフホワイト
       メイン: テラコッタ（くすみオレンジ）
       サブ: モーヴ（くすみピンクパープル）
       文字: チャコールグレー
    */
    .stApp {
        background: #FAF7F5;
    }

    .stApp p, .stApp label, .stApp span, .stApp div {
        color: #3D3633 !important;
        font-weight: 500 !important;
        font-size: 16px !important;
    }

    h1 {
        color: #B5664E !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px;
    }
    h2, h3 {
        color: #8C5F63 !important;
        font-weight: 700 !important;
    }

    /* 各項目の見出し（性別・年齢など） */
    .stRadio > label, .stCheckbox > label, div[data-testid="stMarkdownContainer"] p strong {
        font-size: 16px !important;
        font-weight: 700 !important;
        color: #8C5F63 !important;
    }

    /* ラジオボタン・複数選択ピル（年齢・子供・トーン・行数） */
    .stRadio [role="radiogroup"],
    div[data-testid="stPills"] {
        display: flex !important;
        flex-wrap: nowrap !important;
        gap: 8px !important;
        overflow-x: auto !important;
    }
    .stRadio [role="radiogroup"] label,
    div[data-testid="stPills"] button {
        background-color: #FFFFFF !important;
        border: 1.5px solid #E4D7D2 !important;
        border-radius: 10px !important;
        padding: 7px 14px !important;
        margin: 0 !important;
        flex-shrink: 0 !important;
        white-space: nowrap !important;
        color: #6B5C58 !important;
        font-weight: 600 !important;
        transition: all 0.15s ease-in-out;
    }
    .stRadio [role="radiogroup"] label:has(input:checked) {
        background: #C97B5F !important;
        border: 1.5px solid #C97B5F !important;
        color: #FFFFFF !important;
        box-shadow: 0 2px 8px rgba(201,123,95,0.3);
    }
    .stRadio [role="radiogroup"] label:has(input:checked) p {
        color: #FFFFFF !important;
    }
    div[data-testid="stPills"] button[aria-pressed="true"] {
        background: #9C6B7A !important;
        border: 1.5px solid #9C6B7A !important;
        color: #FFFFFF !important;
        box-shadow: 0 2px 8px rgba(156,107,122,0.3);
    }

    /* セクションごとに白いカードで囲み、輪郭をくっきりと */
    div[data-testid="column"] {
        background-color: #FFFFFF;
        border: 1px solid #ECE0DC;
        border-radius: 16px;
        padding: 24px 22px;
        box-shadow: 0 2px 10px rgba(140,95,99,0.06);
    }

    hr { border-color: #ECE0DC !important; }

    .stButton>button {
        background: #C97B5F !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        border: none !important;
        padding: 14px 24px !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        box-shadow: 0 3px 10px rgba(201,123,95,0.3);
        transition: all 0.15s ease-in-out;
    }
    .stButton>button:hover {
        background: #B5664E !important;
        box-shadow: 0 4px 14px rgba(201,123,95,0.4);
    }
    .stButton>button:disabled {
        background: #EFEAE8 !important;
        color: #B0A6A2 !important;
        box-shadow: none;
    }

    .stTabs [data-baseweb="tab"] {
        font-size: 16px !important;
        font-weight: 700 !important;
        color: #B0A6A2 !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #B5664E !important;
        border-bottom-color: #B5664E !important;
    }

    .stTextArea textarea, .stTextInput input {
        background-color: #FDFBFA !important;
        color: #3D3633 !important;
        font-size: 15px !important;
        border: 1.5px solid #E4D7D2 !important;
        border-radius: 10px !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border: 1.5px solid #C97B5F !important;
        box-shadow: 0 0 0 3px rgba(201,123,95,0.12) !important;
    }

    /* 「必須」「複数可」などの小タグ */
    .stApp span[data-baseweb="tag"], .small-tag {
        background-color: #F4E8E3 !important;
        color: #B5664E !important;
        border-radius: 6px !important;
        padding: 2px 10px !important;
        font-size: 12px !important;
        font-weight: 600 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🌸 Affiliate Post")

if not GOOGLE_API_KEY:
    st.error(
        "❌ GOOGLE_API_KEY が設定されていません。\n\n"
        "プロジェクト直下に `.env` ファイルを作成し、`GOOGLE_API_KEY=あなたのキー` を記入してください。"
        "（`.env.example` をコピーして使うと簡単です）"
    )
    st.stop()

# Geminiクライアントは一度だけ生成して使い回す
@st.cache_resource
def get_client():
    return genai.Client(api_key=GOOGLE_API_KEY)

client = get_client()

# -------------------------------------------------------------
# 2. ペルソナ・トーン設定（固定情報はここにまとめておくと管理しやすい）
# -------------------------------------------------------------
PERSONA_PROMPT = """
【投稿者の設定（ペルソナ）】※最優先ルール
・年齢/立場：30代前半・会社員（OL）・既婚・子なし
・ライフスタイル：仕事とプライベートを両立し、自分へのご褒美や暮らしを豊かにする便利グッズ、美容に投資するのが好き。
・口調：親しみやすく上品。大人の女性らしい、等身大でリアルな本音が伝わる丁寧な言葉遣い（〜だよ、〜かも、おすすめ。など）。
"""

TONE_HINTS = {
    "エモい": "感情に訴えかける言葉、情景が浮かぶ表現、少しノスタルジックなトーンで。",
    "面白い": "親しみやすく、ツッコミどころを交えたり、テンポの良いフランクなトーンで。",
    "カッコいい": "洗練された言葉遣い、無駄を削ぎ落としたスタイリッシュで説得力のあるトーンで。",
    "びっくり": "「まさか…」「知らなきゃ損」などのパワーワードを使い、驚きや発見を強調して。",
    "正直レビュー": "メリットだけでなく、「ここは注意」「好みが分かれるかも」というリアルな本音を混ぜて、信頼性を最優先に。",
}


def build_prompt(gender, age, kids, tone, lines, affiliate_url, memo):
    return f"""
あなたは優秀なアフィリエイトマーケター、兼SNSクリエイターです。
添付された商品画像と以下の【ターゲット・条件】をもとに、ユーザーの購買意欲をそそる魅力的な紹介文を作成してください。

{PERSONA_PROMPT}
※画面で選択されたターゲット（性別：{gender}、年齢層：{', '.join(age) if age else '指定なし'}、子供：{', '.join(kids) if kids else '指定なし'}）に語りかけるように、上記ペルソナの目線から文章を書いてください。

【ターゲット・条件】
・全体のトーン：{tone}（補足：{TONE_HINTS.get(tone, "")}）
・出力の長さ：{lines}程度

【入力素材】
・補足メモ：{memo if memo else "特になし"}

【出力ルール】
必ず以下のJSONフォーマットのみで返答してください。余計な挨拶や解説文は一切含めないでください。
```json
{{
  "main_text": "【ここに指定された行数・トーンで生成したSNS投稿用の本文】",
  "reply_text": "【ここにアフィリエイトリンクへ自然に誘導するリプライ用の文章。アフィリエイトURLがある場合はここに含める：{affiliate_url}】"
}}
```
"""


# -------------------------------------------------------------
# 3. タブメニュー
# -------------------------------------------------------------
tabs = st.tabs(["ダッシュボード", "生成", "スケジュール", "分析"])

with tabs[0]:
    st.subheader("ダッシュボード")
    st.info("ここに投稿実績のサマリーなどを表示予定です（今後実装）。")

with tabs[1]:  # 「生成」タブ

    src_type = st.radio("入力元を選択", ["📷 写真から", "🛍️ 楽天URLから"], horizontal=True)

    if src_type == "🛍️ 楽天URLから":
        st.warning("⚠️ URLからの自動取得は現在未実装です。今は「📷 写真から」をご利用ください。")

    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.subheader("商品画像")
        uploaded_file = st.file_uploader("商品画像をアップロード（必須）", type=["jpg", "jpeg", "png"])

        img_for_gemini = None
        if uploaded_file:
            img_for_gemini = Image.open(uploaded_file)
            st.image(img_for_gemini, caption="アップロードされた画像", use_container_width=True)

    with col2:
        st.subheader("投稿設定")

        gender = st.radio("性別", ["指定なし", "男性", "女性"], horizontal=True)

        st.markdown("**年齢（複数選択可）**")
        age_options = ["10代", "20代", "30代", "40代"]
        age = st.pills(
            "年齢",
            age_options,
            selection_mode="multi",
            default=["20代", "30代"],
            label_visibility="collapsed",
        )

        st.markdown("**子供（複数選択可）**")
        kids_options = ["なし", "乳児", "幼児", "小学生"]
        kids = st.pills(
            "子供",
            kids_options,
            selection_mode="multi",
            default=["乳児", "幼児"],
            label_visibility="collapsed",
        )

        tone = st.radio("トーン", ["エモい", "面白い", "カッコいい", "びっくり", "正直レビュー"], horizontal=True, index=4)
        lines = st.radio("行数", ["1行", "3行", "5行"], horizontal=True, index=1)

        affiliate_url = st.text_input("アフィリエイトURL（任意）", placeholder="https://r10.to/xxxx")
        memo = st.text_area("補足メモ（任意）", placeholder="例：秋冬向け・プレゼントにも。使い心地など")

    st.markdown("---")

    # -------------------------------------------------------------
    # 4. 生成処理
    # -------------------------------------------------------------
    if "result" not in st.session_state:
        st.session_state.result = None

    if st.button("✨ 投稿文を生成する", use_container_width=True):
        if not img_for_gemini:
            st.error("❌ 商品画像がアップロードされていません。画像を載せてからもう一度ボタンを押してください。")
        else:
            with st.spinner("⏳ Geminiがアフィリエイト投稿文を考えています..."):
                try:
                    prompt = build_prompt(gender, age, kids, tone, lines, affiliate_url, memo)

                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[img_for_gemini, prompt],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json"
                        )
                    )

                    st.session_state.result = json.loads(response.text)

                except json.JSONDecodeError:
                    st.error("❌ AIの応答をJSONとして読み込めませんでした。もう一度お試しください。")
                except Exception as e:
                    st.error(f"❌ エラーが発生しました: {e}")

    if st.session_state.result:
        result = st.session_state.result

        st.subheader("生成された投稿文")
        main_text = st.text_area("本文", value=result.get("main_text", ""), height=150, key="main_text_area")

        st.subheader("リプライ（アフィリエイトリンク）")
        reply_text = st.text_area("リプ欄用", value=result.get("reply_text", ""), height=100, key="reply_text_area")

        c_btn1, c_btn2 = st.columns([1, 1])
        with c_btn1:
            st.button(
                "✈️ すぐ投稿",
                use_container_width=True,
                disabled=True,
                help="X・ThreadsのAPI連携が未設定のため、現在は利用できません。"
            )
        with c_btn2:
            st.button(
                "📅 スケジュール予約",
                use_container_width=True,
                disabled=True,
                help="スケジュール機能は今後実装予定です。"
            )

        st.caption("※ X / Threads への自動投稿は、それぞれのAPIキーを取得・設定後に有効化されます。")

with tabs[2]:
    st.subheader("スケジュール")
    st.info("予約投稿の一覧・カレンダー表示は今後実装予定です。")

with tabs[3]:
    st.subheader("分析")
    st.info("X / Threads のインサイトデータ表示は、API連携後に実装予定です。")