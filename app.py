import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import os

# ---------- Config ----------
DATA_FILE = "wellness_data.csv"
SCORE_MIN, SCORE_MAX = 0, 100

# ---------- Helper Functions ----------
def ensure_datafile():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=[
            "username", "date", "sleep_hours", "screen_time", "stress_level",
            "mood", "wellness_score", "tip", "journal"
        ])
        df.to_csv(DATA_FILE, index=False)

def load_data():
    ensure_datafile()
    df = pd.read_csv(DATA_FILE, parse_dates=["date"], dayfirst=True)
    return df.drop_duplicates(subset=["username", "date"], keep="last")

def save_entry(entry):
    df = load_data()
    exists = ((df["username"] == entry["username"]) & (df["date"] == entry["date"])).any()
    if exists:
        st.warning("You’ve already submitted an entry for today.")
        return False
    df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)
    return True

def compute_wellness_score(sleep, screen, stress):
    sleep_score = np.clip((sleep / 8.0) * 40, 0, 40)
    stress_score = np.clip((10 - stress) / 10.0 * 30, 0, 30)
    screen_score = 30 if screen <= 3 else max(0, 30 - (screen - 3) * (30 / 9))
    return int(np.clip(sleep_score + stress_score + screen_score, SCORE_MIN, SCORE_MAX))

def generate_tip(sleep, screen, stress, mood):
    tip = ""
    if sleep < 6: tip += "🛌 Try sleeping 7–8 hours. "
    if screen > 8: tip += "📱 Too much screen time! Reduce it. "
    if stress >= 7: tip += "😣 High stress! Try breathing exercises. "
    if mood.lower() in ["tired", "exhausted"]: tip += "💤 Take a power nap. "
    return tip

def render_card(title, value, delta=None, color="#4CAF50", emoji=""):
    delta_text = f"<br><span style='font-size:15px; color:white;'>Δ {delta}</span>" if delta is not None else ""
    st.markdown(f"""
    <div style='background-color:{color}; padding:20px; border-radius:15px; text-align:center;'>
        <h3 style='color:white; margin:0;'>{emoji} {title}</h3>
        <p style='font-size:28px; font-weight:bold; color:white; margin:5px 0;'>{value}</p>
        {delta_text}
    </div>
    """, unsafe_allow_html=True)

def get_last_n_days(df, n=7, username=None):
    df_user = df[df["username"]==username] if username else df
    df_user = df_user.copy()
    df_user["date_only"] = pd.to_datetime(df_user["date"].dt.date)
    today = pd.Timestamp(datetime.now().date())
    start = today - pd.Timedelta(days=n-1)
    return df_user[df_user["date_only"] >= start].sort_values("date_only").tail(n)

# ---------- Streamlit Setup ----------
st.set_page_config(page_title="🌿 Digital Wellness App", layout="wide")

# ---------- Initialize Session State ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "login"
if "checkin_done" not in st.session_state:
    st.session_state.checkin_done = False

# ---------- LOGIN PAGE ----------
if not st.session_state.logged_in:
    st.markdown("""
    <div style='background-color:#fff3e0; padding:80px; border-radius:15px; text-align:center;'>
        <h1 style='color:#FF4500; font-size:60px; margin-bottom:40px;'>👤 Digital Wellness Login</h1>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<h2 style='color:#FFD700; font-size:50px; margin-bottom:15px;'>Name:</h2>", unsafe_allow_html=True)
    username = st.text_input("", max_chars=30, placeholder="Enter your name here", key="name_input")
    
    st.markdown("<h2 style='color:#FFD700; font-size:50px; margin-top:30px; margin-bottom:15px;'>Select Date:</h2>", unsafe_allow_html=True)
    date_input = st.date_input("", key="login_date_input")
    
    if st.button("Continue", key="login_button"):
        if username:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.date_input = date_input
            st.session_state.page = "dashboard"
        else:
            st.error("Please enter your name!")
    st.stop()

# ---------- DASHBOARD PAGE ----------
username = st.session_state.username
date_input = st.session_state.date_input
data = load_data()

st.markdown(f"""
<div style='background-color:#e0f7fa; padding:25px; border-radius:12px; margin-bottom:20px;'>
    <h2 style='color:#FF4500; font-size:36px; margin-bottom:5px;'>Welcome, <span style='color:#FFD700;'>{username}</span>! 🎉</h2>
    <h3 style='color:#FF8C00; font-size:28px; margin:0;'>Date: <span style='color:#FF8C00;'>{date_input.strftime('%B %d, %Y')}</span></h3>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style='background-color:#e0f7fa; padding:12px; border-radius:12px; margin-bottom:20px;'>
    <label style='color:#00796b; font-weight:bold; font-size:22px;'>Choose an option:</label>
</div>
""", unsafe_allow_html=True)

option = st.selectbox(
    "",
    ["Today's Check-in", "Weekly Overview", "Leaderboard", "View Past Entries",
     "Clear All Past Entries", "Switch Account", "Exit App"]
)

# ------------------ TODAY'S CHECK-IN ------------------
if option == "Today's Check-in":
    today_entry = data[(data["username"] == username) & (data["date"].dt.date == date_input)]
    
    c1, c2 = st.columns([1,3])
    with c1:
        st.markdown("### 🎯 Your Goals")
        st.markdown("- Sleep Hours: 8.0")
        st.markdown("- Screen Time: <=3")
        st.markdown("- Stress Level: <=4")
    with c2:
        if today_entry.empty or not st.session_state.checkin_done:
            sleep_hours = st.number_input("Sleep Hours (0-12)", min_value=0, max_value=12, value=8)
            screen_time = st.number_input("Screen Time in hours (0-24)", min_value=0, max_value=24, value=3)
            stress_level = st.slider("Stress Level (0-10)", min_value=0, max_value=10, value=5)
            mood = st.selectbox("Mood", ["Happy", "Tired", "Sad", "Anxious", "Stressed"])
            journal = st.text_area("Journal / Notes", value="")
            
            if st.button("Submit Today's Check-in"):
                wellness_score = compute_wellness_score(sleep_hours, screen_time, stress_level)
                tip = generate_tip(sleep_hours, screen_time, stress_level, mood)
                entry = {
                    "username": username,
                    "date": pd.Timestamp(date_input),
                    "sleep_hours": sleep_hours,
                    "screen_time": screen_time,
                    "stress_level": stress_level,
                    "mood": mood,
                    "wellness_score": wellness_score,
                    "tip": tip,
                    "journal": journal
                }
                save_entry(entry)
                st.balloons()
                st.success("✅ Today's check-in saved!")
                st.session_state.checkin_done = True
        if st.session_state.checkin_done or not today_entry.empty:
            row = today_entry.iloc[-1] if not today_entry.empty else entry
            st.subheader("📊 Today’s Analysis")
            c1, c2, c3, c4 = st.columns(4)
            with c1: render_card("Stress", row["stress_level"], color="#FF4B4B", emoji="😣")
            with c2: render_card("Screen", row["screen_time"], color="#FFA500", emoji="📱")
            with c3: render_card("Sleep", row["sleep_hours"], color="#1E90FF", emoji="🛌")
            with c4: render_card("Score", row["wellness_score"], color="#4CAF50", emoji="🌿")

            metrics = ["Stress", "Screen Time", "Sleep Hours", "Wellness Score"]
            values = [row["stress_level"], row["screen_time"], row["sleep_hours"], row["wellness_score"]]
            colors = ["#FF4B4B", "#FFA500", "#1E90FF", "#4CAF50"]

            fig = px.bar(
                x=metrics, y=values, text=values, color=metrics,
                color_discrete_map={m:c for m,c in zip(metrics, colors)},
                labels={"x":"Metric", "y":"Value"}
            )
            fig.update_traces(textposition='outside', marker_line_width=0)
            fig.update_layout(
                title="📊 Today's Metrics",
                yaxis=dict(range=[0, max(values)+5]),
                plot_bgcolor="white",
                paper_bgcolor="white"
            )
            st.plotly_chart(fig, use_container_width=True)

# ------------------ WEEKLY OVERVIEW ------------------
elif option == "Weekly Overview":
    st.header("📊 Weekly Overview (Last 7 Days)")
    last7 = get_last_n_days(data, 7, username)
    if last7.empty:
        st.info("No entries yet for weekly overview.")
    else:
        for _, row in last7.iterrows():
            st.markdown(f"### {row['date'].strftime('%B %d, %Y')}")
            c1, c2, c3, c4 = st.columns(4)
            with c1: render_card("Stress Level", row["stress_level"], color="#FF4B4B", emoji="😣")
            with c2: render_card("Screen Time (hrs)", row["screen_time"], color="#FFA500", emoji="📱")
            with c3: render_card("Sleep Hours", row["sleep_hours"], color="#1E90FF", emoji="🛌")
            with c4: render_card("Wellness Score", row["wellness_score"], color="#4CAF50", emoji="🌿")
        
        last7_melt = last7.melt(
            id_vars="date",
            value_vars=["stress_level","screen_time","sleep_hours","wellness_score"],
            var_name="Metric",
            value_name="Value"
        )
        fig = px.line(
            last7_melt,
            x=last7_melt["date"].dt.strftime('%b %d'),
            y="Value",
            color="Metric",
            markers=True,
            color_discrete_map={"stress_level":"red","screen_time":"orange","sleep_hours":"blue","wellness_score":"green"}
        )
        fig.update_layout(
            title="📈 Weekly Trend - Stress, Screen, Sleep, Wellness",
            yaxis_title="Level / Hours / Score",
            plot_bgcolor="white", paper_bgcolor="white"
        )
        st.plotly_chart(fig, use_container_width=True)

# ------------------ Leaderboard ------------------
elif option == "Leaderboard":
    st.header("🏆 Leaderboard")

    st.markdown("<h4 style='color:blue; font-weight:bold;'>Select leaderboard type:</h4>", unsafe_allow_html=True)
    df_score_type = st.selectbox("", ["Daily", "Weekly"], index=0)

    df_score = pd.DataFrame()
    today = pd.Timestamp(datetime.now().date())

    if df_score_type == "Daily":
        df_today = data[data["date"].dt.date == today.date()]
        df_score = df_today.groupby("username", as_index=False)["wellness_score"].mean()
    else:  # Weekly
        week_ago = today - pd.Timedelta(days=6)
        df_week = data[(data["date"].dt.date >= week_ago.date()) & (data["date"].dt.date <= today.date())]
        df_score = df_week.groupby("username", as_index=False)["wellness_score"].mean()

    if df_score.empty:
        st.info("No leaderboard records yet.")
    else:
        df_score = df_score.sort_values("wellness_score", ascending=False).reset_index(drop=True)
        df_score["Rank"] = df_score.index + 1
        df_score["Medal"] = df_score["Rank"].apply(lambda r: ["🥇","🥈","🥉"][r-1] if r <=3 else "")

        for _, row in df_score.iterrows():
            bg_color = "#1a1a1a"
            heading_color = "red"
            rank_color = "gold" if row["Rank"]==1 else ("silver" if row["Rank"]==2 else ("#cd7f32" if row["Rank"]==3 else "white"))
            st.markdown(f"""
            <div style='background-color:{bg_color}; padding:12px; border-radius:10px; margin-bottom:5px;'>
                <h4 style='color:{heading_color}; margin:0;'>Rank: <span style='color:{rank_color}; font-weight:bold;'>{row['Rank']}</span> {row['Medal']}</h4>
                <p style='color:white; margin:2px 0; font-size:16px;'>User: {row['username']} | Score: {row['wellness_score']:.1f}</p>
            </div>
            """, unsafe_allow_html=True)

# ------------------ View Past Entries ------------------
elif option == "View Past Entries":
    st.header("📜 Past Entries")
    df_user = data[data["username"] == username].sort_values("date", ascending=False).reset_index(drop=True)

    if df_user.empty:
        st.info("No past entries found.")
    else:
        for i, row in enumerate(df_user.itertuples(), start=1):
            date_str = pd.to_datetime(row.date).strftime("%B %d, %Y") if pd.notnull(row.date) else "Date Missing"
            st.markdown(f"""
            <div style='background-color:#1a1a1a; padding:10px; border-radius:10px; margin-bottom:5px;'>
                <h4 style='color:red; margin:0;'>{i}. {date_str}</h4>
                <p style='color:white; margin:2px 0;'>
                    Sleep: {row.sleep_hours} | Screen: {row.screen_time} | Stress: {row.stress_level} | Score: {row.wellness_score}
                </p>
                <p style='color:white; margin:2px 0;'>Mood: {row.mood}</p>
                <p style='color:white; margin:2px 0;'>Journal: {row.journal}</p>
            </div>
            """, unsafe_allow_html=True)

# ------------------ Clear / Switch / Exit ------------------
elif option == "Clear All Past Entries":
    if st.button("⚠ Delete All Data"):
        ensure_datafile()
        pd.DataFrame(columns=["username", "date", "sleep_hours","screen_time","stress_level",
                              "mood","wellness_score","tip","journal"]).to_csv(DATA_FILE, index=False)
        st.success("✅ All entries deleted!")
        st.stop()

elif option == "Switch Account":
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.stop()

elif option == "Exit App":
    st.stop()