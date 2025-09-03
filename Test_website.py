# app.py
import json
from datetime import date, datetime
import uuid
import streamlit as st

# =========================
# Config & simple styling
# =========================
st.set_page_config(page_title="Metabolic Care Demo", page_icon="💊", layout="centered")

PRIMARY = "#7C3AED"
ACCENT = "#10B981"

st.markdown(f"""
<style>
  .stProgress > div > div > div > div {{ background-color: {PRIMARY}; }}
  .pill {{
    display:inline-block; padding:4px 10px; border-radius:999px;
    background:#f3f4f6; color:#111827; font-size:12px; margin-right:6px;
    border:1px solid #e5e7eb;
  }}
  .muted {{ color:#6b7280; }}
  .ok {{ color:{ACCENT}; font-weight:600; }}
  .warn {{ color:#ef4444; font-weight:600; }}
  .price {{ font-size: 28px; font-weight:700; }}
  .strike {{ text-decoration: line-through; color:#9CA3AF; font-weight:500; }}
  .card {{ border:1px solid #E5E7EB; border-radius:14px; padding:16px; }}
  .note {{ color:#6b7280; font-size:13px; }}
  .small {{ font-size:12px; color:#6b7280; }}
</style>
""", unsafe_allow_html=True)

# =========================
# Session init
# =========================
if "step" not in st.session_state:
    st.session_state.step = 0

if "lead_id" not in st.session_state:
    st.session_state.lead_id = str(uuid.uuid4())[:8]

if "form" not in st.session_state:
    st.session_state.form = {
        "leadId": st.session_state.lead_id,
        "consent": {"tos": False, "privacy": False, "marketing": False},
        "profile": {"first_name": "", "last_name": "", "dob": None, "sex": "", "state": "", "email": "", "phone": ""},
        "metrics": {"height_cm": None, "weight_kg": None, "bmi": None},
        "eligibility": {"age_ok": None, "bmi_ok": None, "contra": [], "pregnant": "No"},
        "medical": {"conditions": [], "meds": [], "allergies": [], "notes": ""},
        "plan": {"selected": None, "coupon": "", "price": None, "billing": "Monthly"},
        "checkout": {"name_on_card": "", "billing_zip": "", "agree_medical_review": False},
        "utm": {},
        "submitted_at": None
    }

STEPS = [
    "Landing",
    "Eligibility",
    "Medical",
    "Plan & Pricing",
    "Checkout",
    "Confirmation"
]

def progress():
    pct = (st.session_state.step + 1) / len(STEPS)
    st.progress(pct)

def next_step():
    st.session_state.step += 1
    st.experimental_rerun()

def prev_step():
    st.session_state.step = max(0, st.session_state.step - 1)
    st.experimental_rerun()

def calc_bmi(h_cm, w_kg):
    try:
        return round(w_kg / ((h_cm/100) ** 2), 1)
    except Exception:
        return None

# =========================
# Step 0: Landing
# =========================
def render_landing():
    st.title("GLP-1 Program (Demo)")
    st.caption("This is a demo app for a telehealth intake flow. No medical advice. No real purchases.")
    c1, c2 = st.columns([2,1])
    with c1:
        st.markdown("### Clinician-guided metabolic care\nGet evaluated for GLP-1–based treatment with lifestyle coaching.")
        st.markdown("**What’s included**")
        st.markdown("- Initial eligibility screening\n- Licensed clinician review\n- Ongoing follow-ups & messaging\n- Shipping & support")
        st.markdown('<span class="small">HIPAA-like demo: do not submit real PHI.</span>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<span class="price">$199</span> <span class="small">initial evaluation</span><br>', unsafe_allow_html=True)
        st.markdown('<span class="strike">$249</span> <span class="small">limited-time demo price</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with st.form("lead_capture", clear_on_submit=False):
        st.subheader("Start your evaluation")
        fn = st.text_input("First name")
        ln = st.text_input("Last name")
        email = st.text_input("Email")
        phone = st.text_input("Mobile (for notifications)")
        dob = st.date_input("Date of birth", value=date(1995,1,1))
        sex = st.selectbox("Sex", ["", "Female", "Male", "Intersex", "Prefer not to say"], index=0)
        state = st.selectbox("State", ["", "CA","NY","TX","FL","IL","Other"], index=0)

        agree_tos = st.checkbox("I agree to the Terms of Service (demo)")
        agree_priv = st.checkbox("I agree to the Privacy Notice (demo)")

        submitted = st.form_submit_button("Begin Eligibility →")
        if submitted:
            errs = []
            if not fn.strip(): errs.append("First name required")
            if not ln.strip(): errs.append("Last name required")
            if not email or "@" not in email: errs.append("Valid email required")
            if not agree_tos or not agree_priv: errs.append("You must accept Terms & Privacy")

            if errs:
                for e in errs: st.error(e)
            else:
                st.session_state.form["profile"].update(
                    {"first_name": fn, "last_name": ln, "dob": dob, "sex": sex, "state": state, "email": email, "phone": phone}
                )
                st.session_state.form["consent"].update({"tos": agree_tos, "privacy": agree_priv})
                next_step()

# =========================
# Step 1: Eligibility
# =========================
def render_eligibility():
    st.markdown("### Eligibility Screening")
    st.caption("Quick checks to see if you may qualify. Final decisions require clinician review.")
    with st.form("elig_form", clear_on_submit=False):
        h = st.number_input("Height (cm)", min_value=120, max_value=230, value=170)
        w = st.number_input("Weight (kg)", min_value=40, max_value=300, value=85)
        preg = st.selectbox("Are you currently pregnant?", ["No", "Yes"])
        age_ok = st.checkbox("I confirm I am 18+")
        contra = st.multiselect(
            "Any of the following? (demo list)",
            ["History of medullary thyroid carcinoma", "MEN2", "Severe pancreatitis", "Severe GI disease"]
        )
        bmi = calc_bmi(h, w)
        st.info(f"Estimated BMI: **{bmi}**" if bmi else "Enter height/weight for BMI")

        submit = st.form_submit_button("Continue →")
        if submit:
            bmi_ok = (bmi is not None) and (bmi >= 27)  # demo threshold
            st.session_state.form["metrics"].update({"height_cm": h, "weight_kg": w, "bmi": bmi})
            st.session_state.form["eligibility"].update({"age_ok": age_ok, "bmi_ok": bmi_ok, "contra": contra, "pregnant": preg})
            next_step()

    st.button("← Back", on_click=prev_step)

# =========================
# Step 2: Medical
# =========================
def render_medical():
    st.markdown("### Medical Questionnaire")
    with st.form("med_form", clear_on_submit=False):
        conditions = st.multiselect("Conditions (demo)", ["Hypertension","Diabetes","High cholesterol","Depression","None"])
        meds = st.tags_input("Current medications (type to add)") if hasattr(st, "tags_input") else st.text_input("Current medications (comma-separated)")
        allergies = st.multiselect("Allergies", ["Penicillin","Sulfa","Peanuts","Latex","None"])
        notes = st.text_area("Anything else your clinician should know? (demo)")

        agree = st.checkbox("I understand a licensed clinician must review before any treatment.")
        submit = st.form_submit_button("Choose a Plan →")
        if submit:
            if not agree:
                st.error("You must acknowledge clinician review to continue.")
            else:
                meds_list = meds if isinstance(meds, list) else [m.strip() for m in meds.split(",") if m.strip()]
                st.session_state.form["medical"].update({
                    "conditions": conditions, "meds": meds_list, "allergies": allergies, "notes": notes
                })
                st.session_state.form["checkout"]["agree_medical_review"] = True
                next_step()
    st.button("← Back", on_click=prev_step)

# =========================
# Step 3: Plan & Pricing
# =========================
PLANS = [
    {"id": "starter", "name": "Starter", "price": 199, "desc": "Initial eval + care plan"},
    {"id": "plus", "name": "Plus", "price": 299, "desc": "Eval + clinician messaging + monthly check-ins"},
    {"id": "complete", "name": "Complete", "price": 399, "desc": "All of the above + priority support"},
]

def render_plan():
    st.markdown("### Pick your plan")
    billing = st.radio("Billing", ["Monthly", "Quarterly (save 10%)"], horizontal=True)
    cols = st.columns(len(PLANS))
    chosen = None
    for i, plan in enumerate(PLANS):
        with cols[i]:
            st.markdown(f"#### {plan['name']}")
            base = plan["price"]
            price = base if billing == "Monthly" else round(base * 0.9)
            st.markdown(f"<div class='price'>${price}</div><div class='small'>{plan['desc']}</div>", unsafe_allow_html=True)
            if st.button(f"Select {plan['name']}", key=f"sel_{plan['id']}"):
                chosen = (plan["id"], plan["name"], price)

    coupon = st.text_input("Have a promo code? (demo)")

    if chosen:
        st.success(f"Selected: {chosen[1]} — ${chosen[2]} {billing}")
        st.session_state.form["plan"].update({"selected": chosen[0], "price": chosen[2], "billing": billing, "coupon": coupon})
        next_step()

    st.button("← Back", on_click=prev_step)

# =========================
# Step 4: Checkout (mock)
# =========================
def render_checkout():
    st.markdown("### Checkout (Demo)")
    p = st.session_state.form["plan"]
    if not p.get("selected"):
        st.warning("Please choose a plan first.")
        if st.button("Back to Plans"):
            prev_step()
        return

    st.markdown(f"**Plan:** {p['selected'].title()}  \n**Billing:** {p['billing']}  \n**Amount due now (demo):** **${p['price']}**")

    with st.form("pay_form", clear_on_submit=False):
        name = st.text_input("Name on card (demo)")
        zipc = st.text_input("Billing ZIP")
        pay = st.form_submit_button("Pay & Submit (Demo)")
        if pay:
            errs = []
            if not name.strip(): errs.append("Name on card required")
            if not zipc.strip() or len(zipc) < 4: errs.append("Valid ZIP required")
            if errs:
                for e in errs: st.error(e)
            else:
                st.success("Payment simulated ✅ (no real charge).")
                st.session_state.form["checkout"].update({"name_on_card": name, "billing_zip": zipc})
                st.session_state.form["submitted_at"] = datetime.utcnow().isoformat()
                next_step()

    st.button("← Back", on_click=prev_step)

# =========================
# Step 5: Confirmation
# =========================
def render_confirmation():
    st.markdown("### 🎉 Submission received")
    st.caption("A licensed clinician will review your information (demo).")
    data = st.session_state.form.copy()
    # Serialize date for JSON
    if isinstance(data["profile"]["dob"], date):
        data["profile"]["dob"] = data["profile"]["dob"].isoformat()
    st.json(data)

    st.download_button("⬇️ Download submission JSON", data=json.dumps(data, indent=2),
                       file_name=f"submission_{st.session_state.lead_id}.json",
                       mime="application/json")
    st.markdown("<div class='note'>This is a demo UI. No diagnosis or treatment is provided.</div>", unsafe_allow_html=True)

    st.button("← Back to start", on_click=lambda: (st.session_state.update(step=0), st.experimental_rerun()))

# =========================
# Optional webhooks / analytics (pseudo)
# =========================
def send_to_webhook(payload: dict):
    """
    Plug your endpoint here. For example:
        import requests
        r = requests.post(st.secrets['SUBMIT_ENDPOINT'], json=payload, timeout=10)
    """
    pass

# =========================
# Render header + progress
# =========================
st.markdown(" ".join([f'<span class="pill">{i+1}. {name}</span>' for i, name in enumerate(STEPS)]), unsafe_allow_html=True)
progress()

# Router
step = st.session_state.step
if   step == 0: render_landing()
elif step == 1: render_eligibility()
elif step == 2: render_medical()
elif step == 3: render_plan()
elif step == 4: render_checkout()
elif step == 5: render_confirmation()
else:
    st.session_state.step = 0
    st.experimental_rerun()
