import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import re
from wordcloud import WordCloud, STOPWORDS

matplotlib.rcParams["font.family"] = "DejaVu Sans"

# ── Page Config ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Gender Bias in CW Art Museums",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)
# ── Styling ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .hero-header {
        position: relative;
        width: 100%;
        height: 500px;
        overflow: hidden;
        border-radius: 10px;
        margin-bottom: 28px;
        display: flex;
        align-items: flex-end;
    }
    .hero-header img {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
        object-position: center;
        filter: brightness(0.55);
    }
    .hero-header-placeholder {
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, #1a1a1a 0%, #3a2a00 60%, #1a1a1a 100%);
    }
    .hero-overlay {
        position: relative;
        z-index: 2;
        padding: 24px 32px;
        width: 100%;
        background: linear-gradient(to top, rgba(0,0,0,0.75) 0%, transparent 100%);
    }
    .hero-overlay-title {
        font-size: 3.2rem !important;
        font-weight: 900;
        color: #ffffff;
        line-height: 1.15;
        text-shadow: 0 2px 8px rgba(0,0,0,0.7);
        margin: 0;
    }
    .hero-overlay-sub {
        font-size: 1.2rem !important;
        color: #FFD700;
        margin-top: 6px;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-shadow: 0 1px 4px rgba(0,0,0,0.8);
    }
    .kpi-card {
        background: #111111;
        color: #ffffff;
        padding: 28px 20px;
        border-radius: 6px;
        text-align: center;
    }
    .kpi-value {
        font-size: 3rem;
        font-weight: 900;
        color: #FFD700;
        line-height: 1;
    }
    .kpi-label {
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        margin-top: 10px;
        line-height: 1.4;
    }
    .callout {
        background: #FFD700;
        padding: 18px 22px;
        border-left: 6px solid #111;
        margin: 16px 0;
        font-weight: 600;
        line-height: 1.6;
        border-radius: 0 6px 6px 0;
    }
    .photo-placeholder {
        width: 100%;
        aspect-ratio: 4/3;
        background: linear-gradient(135deg, #e8e0d0 0%, #c8b89a 50%, #a89070 100%);
        border-radius: 8px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        border: 2px dashed #999;
        color: #666;
        font-size: 0.9rem;
        text-align: center;
        padding: 20px;
        gap: 10px;
    }
    .photo-placeholder-icon { font-size: 2.5rem; opacity: 0.6; }
    .photo-placeholder-text { font-style: italic; opacity: 0.8; }
</style>
""", unsafe_allow_html=True)


# ── Column Names (matching your CSV exactly) ───────────────────────────────────
COL_TITLE          = "Piece Title"
COL_ARTIST_GENDER  = "Artist Gender"
COL_ARTIST_POC     = "Artist of Color"
COL_FIGURE_POC     = "Figure of Color"
COL_ONLY_POC       = "If yes, only figures of color?"
COL_SUBJECT_GENDER = "Subject Gender"
COL_PLAQUE         = "Plaque Description"

COLORS = {
    "Woman":   "#111111",  # Signature Highlighter Yellow
    "Man":     "#FFD700",  # Stark Black
    "Unknown": "#CCCCCC",  # Neutral Light Gray
    "Other":   "#CCCCCC",  # Slightly Darker Gray
    "Yes":     "#111111",  # Signature Highlighter Yellow
    "No":      "#FFD700",  # Stark Black
    "Both":    "#CCCCCC",  # Soft Gray
    "None":    "#FFD700",  # Very Light Gray
    "Multiple":"#CCCCCC",  # Signature Highlighter Yellow (aligned with 'Yes')
}


# ── Helpers ────────────────────────────────────────────────────────────────────
def kpi_card(value: str, label: str, column) -> None:
    column.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def hero_header(title: str, subtitle: str = "", image_path: str = None) -> None:
    img_tag  = f'<img src="{image_path}" alt="header image">' if image_path else '<div class="hero-header-placeholder"></div>'
    sub_html = f'<div class="hero-overlay-sub">{subtitle}</div>' if subtitle else ""
    st.markdown(f"""
    <div class="hero-header">
        {img_tag}
        <div class="hero-overlay">
            <p class="hero-overlay-title">{title}</p>
            {sub_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


def photo_placeholder(caption: str = "Add a photo here") -> None:
    st.markdown(f"""
    <div class="photo-placeholder">
        <div class="photo-placeholder-icon">🖼️</div>
        <div class="photo-placeholder-text">{caption}</div>
    </div>
    """, unsafe_allow_html=True)


def styled_bar(ax, counts, color_dict, title="", xlabel="", ylabel=""):
    bar_colors = [color_dict.get(k, "#CCCCCC") for k in counts.index]
    bars = ax.bar(counts.index, counts.values, color=bar_colors, edgecolor="white", linewidth=1.5)
    for bar, val in zip(bars, counts.values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(counts.values) * 0.02,
            str(val),
            ha="center", fontweight="bold", fontsize=11,
        )
    ax.set_facecolor("#F5F5F5")
    ax.spines[["top", "right"]].set_visible(False)
    ax.yaxis.grid(True, color="white", linewidth=1)
    ax.set_axisbelow(True)
    counts.plot(kind='bar', ax=ax, color=[color_dict.get(x, '#333') for x in counts.index])
    
    # Add the new formatting lines
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel(xlabel, fontsize=10, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=10, fontweight='bold')
    
    # Optional: Rotate x-labels if they are long
    plt.setp(ax.get_xticklabels(), rotation=0)


def fig_bg(fig):
    fig.patch.set_facecolor("#F5F5F5")

                            
# ── Load & Normalize Data ──────────────────────────────────────────────────────
@st.cache_data
def load_csv(f):
    df = pd.read_csv(f)
    for col in [COL_ARTIST_GENDER, COL_ARTIST_POC, COL_FIGURE_POC,
                COL_ONLY_POC, COL_SUBJECT_GENDER]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.capitalize()
    return df


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🎨 Navigation")
    page = st.radio(
        "", 
        ["🏠 Home", "📊 Art Museum of CW", "☁️ Word Clouds"], 
        label_visibility="collapsed"
    )


# ── Load data ──────────────────────────────────────────────────────────────────
try:
    df = load_csv("data/museum_data.csv")
    st.sidebar.success(f"✅ Loaded **{len(df)}** artworks")
except FileNotFoundError:
    st.error("⚠️ The data file was not found. Please make sure 'data/museum_data.csv' exists in your project folder.")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# HOME PAGE
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Home":
    hero_header(
        title="Visualization of Gender and Racial Bias in the<br>Art Museums of Colonial Williamsburg",
        subtitle="Hannah Sweazey · GSWS 205 · Spring 2026",
        image_path="https://images.squarespace-cdn.com/content/v1/55d4aaa8e4b084df273878ef/1627960386943-1BMMO4VBOV9AYWLSXJAW/1989_GuerrillaGirls_DoWomenHavetobeNakedMetMuseum-SQP.jpg?format=1500w",  # ← replace with your image path/URL
    )

    col_main, col_side = st.columns([2, 1])

    with col_main:
        st.subheader("About This Dashboard")
        st.write(
            """
            In 2004, an anonymous group of feminist artist-activists posed a pointed question to the Metropolitan Museum of Art: 
            **"Do women have to be naked to get into the Met Museum?"** While this became the group’s most widely known poster, 
            they have built an active network of activists by using the intersection of pop art, feminism, and statistics. 
            They have called out several institutions for their underrepresentation of both women and people of color throughout their careers.
            """
        )
        st.write("""
            While 2004 seems like a long time ago, I believe there is likely still a trend in underrepresentation. 
            To put this theory to the test, I ventured to a local art museum in Colonial Williamsburg to analyze their collections 
            of paintings, drawings, and etchings. I had three major questions I hoped to answer:
            
            - **What do the percentages of representation look like for men, women, and people of color?**
            - **Who is being represented in the art pieces themselves?**
            - **What language is being used to describe different artists and subjects?**
            
            The answers I found in my local art museum will be discussed throughout this dashboard.
            """
        )

        st.subheader("Data Collection")
        st.markdown("""
            This data was collected by hand at the Colonial Art Museum. As I walked through exhibits, I recorded the following fields for every painting, drawing, and etching:
            
            * **Piece Title**: Name as it appeared on the plaque.
            * **Artist’s Gender**: Man, Woman, or Unknown.
            * **Artist of Color?**: Yes, No, or Unknown.
            * **Subject of Color?**: Whether the subject (if present) was a person of color.
            * **Only Subjects of Color?**: Whether there were *only* subjects of color.
            * **Subject’s Gender**: Man, Woman, or Both.
            * **Plaque Description**: Text from the accompanying plaque.
            
            The artist's gender and race were confirmed by an internet search and double-checking the Museum's online records. 
            The plaque description was extracted via text-copying from images and hand-proofread. Originally, I wanted to 
            look into language regarding male vs. female painters, so I did not collect plaque data for unknown artists. 
            The data ended up being heavily skewed toward male artists, so I added an analysis on language about different 
            subjects to compensate for missing data.
        """)

        st.subheader("Why This Matters")
        st.write("""
            It is easy to feel as though bigger social issues are too "far away" to pertain to you. This dashboard is 
            important because it shows that one does not have to be at the Met to see the latent sexism and racism that 
            have become commonplace in artistic spaces. To the concern that a colonial museum *should* be skewed, I offer three rebutals:
            
            1. **Was art not being made by these minority groups, or is it simply not up to "Western" artistic standards?**
            2. **The visualization of this data is impactful because some statistics from Colonial Williamsburg are actually better than those of the Met.**
            3. **This serves as a reminder to break white, masculine normativity in both creative spaces and daily life.**
            
            Learning from the past is one of our most important tools in activism and growth.
            """
        )

    with col_side:
        st.image(
            "https://northernvirginiamag.com/wp-content/uploads/2020/07/art-museum.jpg",  # <-- Put your image URL here
            caption="Courtesy of Northern Virgirnia Magazine",
            use_container_width=True # <-- This ensures it fits perfectly in the side column!
        )
        st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True): 
            st.write("### Related Works") 
            st.markdown("""
            * Guerrilla Girls — *Transgressive Techniques* (Getty Research Journal, 2010)
            * Linda Nochlin — *Why Have There Been No Great Women Artists?* (1971)
            * Nina Menkes — *Brainwashed: Sex-Camera-Power* (2022)
            """)

        st.markdown("<br>", unsafe_allow_html=True)

        st.image(
            "https://images.squarespace-cdn.com/content/v1/55d4aaa8e4b084df273878ef/ae8bef49-6e67-4e11-a67c-bd00c0c626c3/GuerrillaGirls_AboutUs_Banner.jpg?format=2500w",  # <-- Put your image URL here
            caption="Courtesy of the Guerilla Girls",
            use_container_width=True # <-- This ensures it fits perfectly in the side column!
        )

        with st.container(border=True):
            st.write("### Explore the Dashboard")
            st.markdown("""
            * 📊 **Art Museum of CW** — KPIs & charts on racial and gender distribution among artwork
            * ☁️ **Word Clouds** — Plaque language for female vs. male subjects and artists
            """)

# ══════════════════════════════════════════════════════════════════════════════
# MUSEUM PAGE (PRESENTATION MODE)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Art Museum of CW":
    hero_header(
        title="Art Museum of Colonial Williamsburg",
        subtitle="Artist Demographics · Figure Representation · Race & Gender",
        image_path="https://maryryangallery.com/wp-content/uploads/2025/02/guerrilla-girls-installed-wall-corrected.jpg"
    )
    
    # ── Derived stats ──────────────────────────────────────────────────────────
    total         = len(df)
    n_female      = (df[COL_ARTIST_GENDER] == "Woman").sum()
    n_male        = (df[COL_ARTIST_GENDER] == "Man").sum()
    n_poc         = (df[COL_ARTIST_POC] == "Yes").sum()
    n_fig_poc     = (df[COL_FIGURE_POC] == "Yes").sum()
    n_only_poc    = (df[COL_ONLY_POC] == "Yes").sum()

    pct_female    = round(n_female  / total * 100) if total > 0 else 0
    pct_poc       = round(n_poc     / total * 100) if total > 0 else 0
    pct_fig_poc   = round(n_fig_poc / total * 100) if total > 0 else 0
    pct_only_poc  = round(n_only_poc/ total * 100) if total > 0 else 0

    # ── KPIs ──────────────────────────────────────────────────────────────────
    st.subheader("Key Statistics")
    c1, c2, c3, c4 = st.columns(4)
    kpi_card(f"{pct_female}%",  f"of artists are women\n({n_female} of {total} works)", c1)
    kpi_card(f"{pct_poc}%",     f"of artists are people of color\n({n_poc} of {total} works)", c2)
    kpi_card(f"{pct_fig_poc}%", f"of works include a figure of color\n({n_fig_poc} of {total} works)", c3)
    kpi_card(f"{pct_only_poc}%", f"of works include only figures of color\n({n_only_poc} of {total} works)", c4)

    st.markdown("---")

    # ── CAROUSEL NAVIGATION (Gallery Pager) ───────────────────────────────────
    if 'slide_idx' not in st.session_state:
        st.session_state.slide_idx = 0

    slides = ["Artist Gender", "Subject Representation", "Artists of Color", "Figures of Color"]
    total_slides = len(slides)
    # 1. CAROUSEL LOGIC (Looping)
    if 'slide_idx' not in st.session_state:
        st.session_state.slide_idx = 0

    slides = ["Artist Gender", "Subject Representation", "Artists of Color", "Figures of Color"]
    total_slides = len(slides)

    # 2. THE NAVIGATION ROW
    # We use a standard 1:4:1 column ratio
    nav_col1, nav_col2, nav_col3 = st.columns([1, 4, 1])

    with nav_col1:
        # Loop backwards: if at 0, goes to (0-1)%4 = 3
        if st.button("← PREV"):
            st.session_state.slide_idx = (st.session_state.slide_idx - 1) % total_slides
            st.rerun()

    with nav_col2:
        # Standard Streamlit progress bar and text
        progress_val = (st.session_state.slide_idx + 1) / total_slides
        st.progress(progress_val)
        st.write(f"**Slide {st.session_state.slide_idx + 1} of {total_slides}**: {slides[st.session_state.slide_idx]}")

    with nav_col3:
        # Loop forwards: if at 3, goes to (3+1)%4 = 0
        if st.button("NEXT →"):
            st.session_state.slide_idx = (st.session_state.slide_idx + 1) % total_slides
            st.rerun()

    st.markdown("---")

    # ── Display Content Based on Current Slide ────────────────────────────────
    col_l, col_r = st.columns([1.2, 1])

    if st.session_state.slide_idx == 0:
        with col_l:
            gender_counts = df[COL_ARTIST_GENDER].value_counts()
            fig, ax = plt.subplots(figsize=(5.5, 4))
            styled_bar(ax, gender_counts, COLORS, title="Artist Gender Distribution", xlabel="Gender", ylabel="Count")
            fig_bg(fig)
            st.pyplot(fig)
        with col_r:
            st.subheader("The Creator Gap")
            st.write(f"Female artists account for just **{pct_female}%** of the collection.")
            st.write("This striking graph shows us a few things. Firstly, male artists are overwhelmingly represented at the CW Art Museum. We also see that there are more unknown artists than female artists. If we think about Nochlin’s piece “Why Have There Been No Great Women Artists?”, there could be a multitude of socioeconomic barriers that prevented women from becoming one of the greats. This, Nochlin reminds us, does not mean that women were not making art; they faced social barriers to things like higher education, so could not be seen as fine artists.")

    # --- SLIDE 2: SUBJECT REPRESENTATION ---
    elif st.session_state.slide_idx == 1:
        with col_l:
            subj_counts = df[COL_SUBJECT_GENDER].value_counts()
            subj_counts_display = subj_counts[subj_counts.index != "None"]
            pie_colors = [COLORS.get(k, "#CCCCCC") for k in subj_counts_display.index]
            
            fig2, ax2 = plt.subplots(figsize=(5.5, 4))
            
            # Capture patches, texts (labels), and autotexts (percentages)
            patches, texts, autotexts = ax2.pie(
                subj_counts_display.values, 
                labels=subj_counts_display.index, 
                autopct="%1.0f%%", 
                colors=pie_colors, 
                startangle=90
            )

            # Loop through and find the 'Woman' slice to change text to white
            for i, label in enumerate(subj_counts_display.index):
                if label == "Woman":
                    autotexts[i].set_color('white') # Changes the % inside the slice
                    texts[i].set_color('black')      # Keeps the label outside readable (or set to white if needed)
                    # Optional: autotexts[i].set_weight('bold')
            
            fig_bg(fig2)
            st.pyplot(fig2)
            
        with col_r:
            st.subheader("Subject Distribution")
            st.write("We saw that men dominated the artists category, and it seems this graph is no different. While the skew is not as egregious, men appear in 20% more pieces than women. This was an interesting finding, as I thought maybe women would appear more since that feels like a very object-observer-based perspective. Menkes covers this tendency for women to appear as objects, specifically in film, in her documentary Brainwashed: Sex-Camera-Power. This, I thought, would also apply to other forms of art, but perhaps because portraiture was a status symbol, it was more prevalent with men.")

    elif st.session_state.slide_idx == 2:
        with col_l:
            poc_counts = df[COL_ARTIST_POC].value_counts()
            fig3, ax3 = plt.subplots(figsize=(5.5, 4))
            styled_bar(ax3, poc_counts, COLORS, title="Artist Racial Distribution", xlabel="Race", ylabel="Count")
            fig_bg(fig3)
            st.pyplot(fig3)
        with col_r:
            st.subheader("Racial Inclusion")
            st.write(f"Only **{pct_poc}%** of recorded works are by artists of color.")
            st.write("Next to the plaque of the only portrait of a Black man in the entire museum, there is a question in bold letters that reads “Where are the rest of us?” The museum attributes the lack of representation to the fact that portraits were often commissioned by people of European descent who had better disposable income. While this is true, it also seems like a very watered-down account of the multiple layers of systemic oppression Black men and women faced during America’s early years. To account for the lack of representation, the museum has a single room dedicated to Black American artists.")

    # --- SLIDE 4: FIGURES OF COLOR ---
    elif st.session_state.slide_idx == 3:
        with col_l:
            # Defining the counts
            n_any_poc = (df[COL_FIGURE_POC] == "Yes").sum()
            n_only_poc = (df[COL_ONLY_POC] == "Yes").sum()
            n_no_poc = total - n_any_poc
            
            fig_poc_display = pd.Series({
                "At least one PoC": n_any_poc, 
                "Only PoC": n_only_poc, 
                "No PoC": n_no_poc
            })
            
            # UPDATED COLORS: Gray for 'At least one', Yellow for 'Only', Black for 'No'
            local_colors = {
                "At least one PoC": "#808080", # Gray
                "Only PoC": "#FFE800",        # Yellow
                "No PoC": "#111111"           # Black
            }
            
            fig4, ax4 = plt.subplots(figsize=(5.5, 4))
            styled_bar(ax4, fig_poc_display, local_colors)
            fig_bg(fig4)
            st.pyplot(fig4)
            
        with col_r:
            st.subheader("Visual Marginalization")
            st.write(f"While {n_any_poc} works include figures of color, only {n_only_poc} works feature them exclusively.")
            st.write("While there was already a lack of POC artists, there is also a distinct lack of POC subjects. If there was a subject that was a POC, less than half were accompanied by at least one White subject. A handful of these paintings, drawings, etches were depictions of slavery. One portrait, simply titled “Slave Girl,” was praised by the museum for not using any of the common racist character proportions from the time. This not only shows the lack of representation, but also the lack of quality acknowledgment of the structural and historical implications as to why there is a lack of representation of POC in art. Throwing praise at a White woman’s painting of an enslaved Black girl for being non-racist should be inconceivable. The preservation of art is one thing, but openly commending the context of the painting is detrimental to conversation about both POC representation in art and the rammifcations of slavery in American history.")

    # Expander for raw data (Only appears once now!)
    with st.expander("🔍 View Raw Data"):
        display_cols = [c for c in [COL_TITLE, COL_ARTIST_GENDER, COL_ARTIST_POC,
                                     COL_FIGURE_POC, COL_ONLY_POC, COL_SUBJECT_GENDER,
                                     COL_PLAQUE] if c in df.columns]
        st.dataframe(df[display_cols], use_container_width=True)
        st.caption(f"{total} artworks total")


# ══════════════════════════════════════════════════════════════════════════════
# WORD CLOUD PAGE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "☁️ Word Clouds":
    hero_header(
        title="Plaque Language: Female vs. Male",
        subtitle="What language is used to describe different artists and subjects?",
        image_path="https://images.squarespace-cdn.com/content/v1/55d4aaa8e4b084df273878ef/1460400994059-S51M7184HEH0SYHXNWRT/1991publicartfundbbd.jpg?format=1000w",  # ← replace with your image path/URL
    )

    def render_wordcloud(text, colormap, col_obj, stopwords, bg_color):
        if text.strip():
            wc = WordCloud(
                width=800, 
                height=500, 
                background_color=bg_color,
                colormap=colormap,
                max_words=100,
                prefer_horizontal=0.9,
                stopwords=stopwords
            ).generate(text)
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.imshow(wc, interpolation='bilinear')
            ax.axis('off')
            
            fig.patch.set_facecolor(bg_color) 
            plt.tight_layout(pad=0)
            
            col_obj.pyplot(fig)
            plt.close()
        else:
            col_obj.info("No text available for this category.")

    def preprocess_text(text_series):
        text_series = text_series.dropna().astype(str)
        text_series = text_series[~text_series.str.lower().isin(["none", "nan", ""])]
        combined_text = " ".join(text_series.tolist()).lower()
        combined_text = re.sub(r'[^a-z\s]', ' ', combined_text)
        return combined_text

    # 2. DEFINE STOPWORDS
    # General museum jargon
    base_stopwords = set(STOPWORDS)
    base_stopwords.update([
        "art", "artist", "painting", "museum", "collection", "gift", 
        "century", "colonial", "williamsburg", "portrait", "figure", 
        "work", "painted", "canvas", "oil", "born", "died", 
        "s", "one", "two", "portraits", "william", "john", "year", "virginia", "likely"
    ])

    # Artist-specific names to remove
    artist_names = {"hunter", "melrose", "custis", "hicks"}
    all_stopwords = base_stopwords.union(artist_names)

    # ==============================================================================
    # SECTION 1: SUBJECT GENDER COMPARISON
    # ==============================================================================
    st.header("I. The Subjects")
    st.write("What language is used to describe the subjects of these artworks, and how does it differ by gender?")

    sub_f_mask = (df[COL_SUBJECT_GENDER] == "Woman")
    sub_m_mask = (df[COL_SUBJECT_GENDER] == "Man")

    sub_f_text = preprocess_text(df.loc[sub_f_mask, COL_PLAQUE])
    sub_m_text = preprocess_text(df.loc[sub_m_mask, COL_PLAQUE])

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"### Female Subjects <small>({sub_f_mask.sum()})</small>", unsafe_allow_html=True)
        render_wordcloud(sub_f_text, "Greys", st, all_stopwords, "#C2D6FC")
    with c2:
        st.markdown(f"### Male Subjects <small>({sub_m_mask.sum()})</small>", unsafe_allow_html=True)
        render_wordcloud(sub_m_text, "Greys", st, all_stopwords, "#C2D6FC")

    st.markdown("---")

    # ==============================================================================
    # SECTION 2: ARTIST GENDER COMPARISON
    # ==============================================================================
    st.header("II. The Creators")
    st.write("What language is used to describe the artists themselves, and how does it differ by gender?")

    art_f_mask = (df[COL_ARTIST_GENDER] == "Woman")
    art_m_mask = (df[COL_ARTIST_GENDER] == "Man")

    art_f_text = preprocess_text(df.loc[art_f_mask, COL_PLAQUE])
    art_m_text = preprocess_text(df.loc[art_m_mask, COL_PLAQUE])

    c3, c4 = st.columns(2)
    with c3:
        st.markdown(f"### Female Artists <small>({art_f_mask.sum()})</small>", unsafe_allow_html=True)
        render_wordcloud(art_f_text, "Greys", st, all_stopwords, "#C2D6FC")
    with c4:
        st.markdown(f"### Male Artists <small>({art_m_mask.sum()})</small>", unsafe_allow_html=True)
        render_wordcloud(art_m_text, "Greys", st, all_stopwords, "#C2D6FC")

    
    st.markdown("---")
    st.subheader("Observations & Analysis")

    c_a, c_b = st.columns(2)
    with c_a:
        st.markdown("**Female Subjects Cloud**")
        st.write("""
            * Family
            * Children/child
            * Subject
            * Couple
            * Father
        """)

        st.write("""
        Female subjects tended to have words that were centered around other individuals, speaking about women as an additive person instead of someone with their own identity. Where the male subjects' words refer more to their life accomplishments (job, travel, success, etc.), words for female subjects centered more around how they affected the people around them.""")
    
        st.markdown("**Female Artists Cloud**")
        st.write("""
            * African
            * Minimal number of entries
            * Allowed
        """)
        
        st.write("""
        Male subjects tended to have words that spoke about their lifetime accomplishments or work. There are a few more active words in this cloud than the female counterpart. More words indicate travel, painting men’s lives as more fruitful and worldly. Men, through the eyes of the plaque’s language, seem to be more dynamic figures.
        """)

    with c_b:
        st.markdown("**Male Subjects Cloud**")
        st.write("""
            * Painter
            * New
            * Comissioned
            * Places (England, America, etc.)
        """)

        st.write("""
        There was a significantly smaller sample size for plaque descriptions for female artists, speaking to how much less representation they had in the museum. We also see the word ‘African’ very large. This is interesting because it shows that many of the female artists were also African American, showing us some instances of intersecting identities and explaining possibly why those combinations of identities show up more than others (4/7 female artists were Black women).
        """)

        st.markdown("**Male Artists Cloud**")
        st.write(
            "* Overall, similar language and words to the Male Subjects Cloud"
        )

        st.write("""
        Again, the male artists are described much more dynamically and as more of a full-fledged individual than the female artist description. There are also no descriptions pointing to minority groups, as we see in the sparse Female Artists Cloud.""")
            
    st.markdown("---")
    st.subheader("Plaque Text by Category")

    tab_f, tab_m, tab_fa, tab_ma = st.tabs(["Female Subjects", "Male Subjects", "Female Artists", "Male Artists"])
    
    with tab_f:
        rows = df[sub_f_mask][[COL_TITLE, COL_PLAQUE]]
        if not rows.empty:
            st.dataframe(rows.reset_index(drop=True), use_container_width=True)
        else:
            st.write("No records found.")
            
    with tab_m:
        rows = df[sub_m_mask][[COL_TITLE, COL_PLAQUE]]
        if not rows.empty:
            st.dataframe(rows.reset_index(drop=True), use_container_width=True)
        else:
            st.write("No records found.")

    with tab_fa:
        rows = df[art_f_mask][[COL_TITLE, COL_PLAQUE]]
        if not rows.empty:
            st.dataframe(rows.reset_index(drop=True), use_container_width=True)
        else:
            st.write("No records found.")

    with tab_ma:
        rows = df[art_m_mask][[COL_TITLE, COL_PLAQUE]]
        if not rows.empty:
            st.dataframe(rows.reset_index(drop=True), use_container_width=True)
        else:
            st.write("No records found.")