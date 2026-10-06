"""
Custom styling and CSS injection for NeighborTools.
Implements the warm neutral palette, forest green brand identity,
and polished typography.
"""

import streamlit as st

CUSTOM_CSS = """
<style>
/* -------------------------------------------------------------------------
   GLOBAL & THEME VARIABLES
   ------------------------------------------------------------------------- */
:root {
    --color-forest-dark: #1b4332;
    --color-forest-primary: #2d6a4f;
    --color-forest-light: #40916c;
    --color-forest-mint: #52b788;
    --color-forest-tint: #d8f3dc;
    --color-forest-soft: #f0f7f3;

    --color-bg-main: #fbfaf7;
    --color-bg-card: #ffffff;
    --color-bg-subtle: #f4f2ec;
    
    --color-border-card: #e5e2d9;
    --color-border-focus: #2d6a4f;

    --color-text-main: #1f2923;
    --color-text-muted: #5e6862;
    --color-text-inverse: #ffffff;

    --color-accent-warm: #d97706;
    --color-accent-soft: #fef3c7;
    --color-danger: #dc2626;
    --color-danger-soft: #fee2e2;
    
    --radius-sm: 8px;
    --radius-md: 14px;
    --radius-lg: 20px;
    --radius-full: 9999px;
    
    --shadow-sm: 0 1px 3px rgba(27, 67, 50, 0.05);
    --shadow-md: 0 4px 16px rgba(27, 67, 50, 0.08);
    --shadow-hover: 0 8px 24px rgba(27, 67, 50, 0.12);
}

/* Base Streamlit Page container */
.stApp {
    background-color: var(--color-bg-main);
    color: var(--color-text-main);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

/* Main block padding */
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 4rem;
    max-width: 1200px;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: #f7f5ef;
    border-right: 1px solid var(--color-border-card);
}

/* Primary and secondary button styling */
.stButton > button {
    border-radius: var(--radius-sm);
    font-weight: 600;
    font-size: 0.95rem;
    transition: all 0.2s ease-in-out;
    border: 1px solid var(--color-border-card);
}

.stButton > button[kind="primary"] {
    background-color: var(--color-forest-primary);
    color: #ffffff;
    border: none;
    box-shadow: 0 2px 6px rgba(45, 106, 79, 0.3);
}

.stButton > button[kind="primary"]:hover {
    background-color: var(--color-forest-dark);
    box-shadow: 0 4px 12px rgba(27, 67, 50, 0.35);
    transform: translateY(-1px);
}

.stButton > button[kind="secondary"]:hover {
    background-color: var(--color-bg-subtle);
    border-color: var(--color-forest-light);
    color: var(--color-forest-dark);
}

/* Inputs, selects, and text areas */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div {
    background-color: #ffffff !important;
    border: 1px solid var(--color-border-card) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--color-text-main) !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--color-forest-primary) !important;
    box-shadow: 0 0 0 2px var(--color-forest-tint) !important;
}

/* -------------------------------------------------------------------------
   HEADER & WORDMARK
   ------------------------------------------------------------------------- */
.brand-header-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.25rem 1.5rem;
    background: #ffffff;
    border: 1px solid var(--color-border-card);
    border-radius: var(--radius-md);
    margin-bottom: 2rem;
    box-shadow: var(--shadow-sm);
}

.brand-wordmark {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    text-decoration: none;
}

.brand-icon-box {
    background: var(--color-forest-soft);
    border: 1px solid var(--color-forest-tint);
    width: 44px;
    height: 44px;
    border-radius: var(--radius-sm);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
}

.brand-title {
    font-size: 1.5rem;
    font-weight: 800;
    color: var(--color-forest-dark);
    letter-spacing: -0.02em;
    margin: 0;
    line-height: 1.1;
}

.brand-subtitle {
    font-size: 0.8rem;
    color: var(--color-text-muted);
    margin: 0;
    font-weight: 500;
}

.user-status-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: var(--color-forest-soft);
    border: 1px solid var(--color-forest-tint);
    padding: 0.4rem 0.9rem;
    border-radius: var(--radius-full);
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--color-forest-dark);
}

/* -------------------------------------------------------------------------
   HERO SECTION
   ------------------------------------------------------------------------- */
.hero-card {
    background: linear-gradient(135deg, #1b4332 0%, #2d6a4f 60%, #40916c 100%);
    color: #ffffff;
    border-radius: var(--radius-lg);
    padding: 3rem 2.5rem;
    margin-bottom: 2.5rem;
    box-shadow: var(--shadow-md);
    position: relative;
    overflow: hidden;
}

.hero-tag {
    display: inline-block;
    background: rgba(255, 255, 255, 0.18);
    backdrop-filter: blur(8px);
    color: #d8f3dc;
    font-size: 0.85rem;
    font-weight: 700;
    padding: 0.3rem 0.8rem;
    border-radius: var(--radius-full);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 1rem;
}

.hero-title {
    font-size: 2.6rem;
    font-weight: 800;
    line-height: 1.15;
    margin-bottom: 1rem;
    letter-spacing: -0.02em;
    color: #ffffff;
}

.hero-description {
    font-size: 1.15rem;
    line-height: 1.6;
    color: #e8f5e9;
    max-width: 680px;
    margin-bottom: 1.75rem;
}

/* -------------------------------------------------------------------------
   HOW IT WORKS CARDS
   ------------------------------------------------------------------------- */
.how-it-works-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 1.25rem;
    margin: 2rem 0;
}

.step-card {
    background: #ffffff;
    border: 1px solid var(--color-border-card);
    border-radius: var(--radius-md);
    padding: 1.5rem;
    box-shadow: var(--shadow-sm);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.step-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-hover);
    border-color: var(--color-forest-mint);
}

.step-number {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: var(--radius-full);
    background: var(--color-forest-tint);
    color: var(--color-forest-dark);
    font-weight: 800;
    font-size: 0.9rem;
    margin-bottom: 0.85rem;
}

.step-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--color-forest-dark);
    margin-bottom: 0.5rem;
}

.step-desc {
    font-size: 0.9rem;
    color: var(--color-text-muted);
    line-height: 1.5;
}

/* -------------------------------------------------------------------------
   TOOL CARDS
   ------------------------------------------------------------------------- */
.tool-card-box {
    background: #ffffff;
    border: 1px solid var(--color-border-card);
    border-radius: var(--radius-md);
    padding: 1.25rem;
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow-sm);
    transition: all 0.2s ease;
    display: flex;
    flex-direction: column;
    height: 100%;
}

.tool-card-box:hover {
    border-color: var(--color-forest-light);
    box-shadow: var(--shadow-hover);
    transform: translateY(-2px);
}

.tool-badge-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
    gap: 0.5rem;
}

.badge-category {
    background: var(--color-bg-subtle);
    color: var(--color-forest-dark);
    font-size: 0.75rem;
    font-weight: 700;
    padding: 0.25rem 0.65rem;
    border-radius: var(--radius-full);
    text-transform: uppercase;
    letter-spacing: 0.03em;
}

.badge-status-available {
    background: #dcfce7;
    color: #166534;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 0.25rem 0.65rem;
    border-radius: var(--radius-full);
}

.badge-status-borrowed {
    background: #fee2e2;
    color: #991b1b;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 0.25rem 0.65rem;
    border-radius: var(--radius-full);
}

.badge-status-pending {
    background: #fef3c7;
    color: #92400e;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 0.25rem 0.65rem;
    border-radius: var(--radius-full);
}

.tool-card-title {
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--color-forest-dark);
    margin-bottom: 0.4rem;
    line-height: 1.3;
}

.tool-card-desc {
    font-size: 0.88rem;
    color: var(--color-text-muted);
    line-height: 1.5;
    margin-bottom: 1rem;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.tool-meta-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    font-size: 0.82rem;
    color: var(--color-text-muted);
    margin-bottom: 1rem;
    padding-top: 0.75rem;
    border-top: 1px solid var(--color-bg-subtle);
}

.tool-meta-item {
    display: flex;
    align-items: center;
    gap: 0.35rem;
}

/* -------------------------------------------------------------------------
   STATUS PILLS & ALERTS
   ------------------------------------------------------------------------- */
.status-pill {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: var(--radius-full);
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: capitalize;
}
.status-pending { background: #fef3c7; color: #92400e; }
.status-approved { background: #dbeafe; color: #1e40af; }
.status-picked_up { background: #e0e7ff; color: #3730a3; }
.status-returned { background: #dcfce7; color: #166534; }
.status-declined { background: #f3f4f6; color: #4b5563; }
.status-cancelled { background: #fee2e2; color: #991b1b; }
.status-overdue { background: #fee2e2; color: #b91c1c; font-weight: 800; }

.empty-state-box {
    text-align: center;
    padding: 3.5rem 1.5rem;
    background: #ffffff;
    border: 2px dashed var(--color-border-card);
    border-radius: var(--radius-lg);
    margin: 1.5rem 0;
}

.empty-state-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.empty-state-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--color-forest-dark);
    margin-bottom: 0.5rem;
}

.empty-state-text {
    font-size: 0.92rem;
    color: var(--color-text-muted);
    max-width: 460px;
    margin: 0 auto 1.5rem auto;
}

/* Notice box for setup guidance */
.setup-notice-box {
    background: #f0f7f3;
    border-left: 4px solid var(--color-forest-primary);
    padding: 1.25rem 1.5rem;
    border-radius: var(--radius-sm);
    margin-bottom: 1.75rem;
    font-size: 0.92rem;
    color: var(--color-forest-dark);
}
</style>
"""


def apply_custom_styles():
    """Injects the custom CSS styles into the current Streamlit app session."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
