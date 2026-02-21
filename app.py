import streamlit as st
import snowflake.connector
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

st.set_page_config(layout="wide", page_title="Shubham Ticket Dashboard", page_icon="🎟️")

# -----------------------------
# Snowflake Connection
# -----------------------------
@st.cache_resource
def get_connection():
    return snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
        role=os.getenv("SNOWFLAKE_ROLE")
    )

conn = get_connection()

# -----------------------------
# HEADER
# -----------------------------
col1, col2 = st.columns([8, 2])

with col1:
    st.title("Shubham Ticket Dashboard")
    st.caption("Manage your tickets efficiently")

with col2:
    if st.button("➕ Create Ticket"):
        st.session_state.show_modal = True

# -----------------------------
# DASHBOARD METRICS
# -----------------------------
query = """
SELECT
    COUNT(*) AS TOTAL,
    COUNT_IF(status='New') AS NEW,
    COUNT_IF(status='In Progress') AS IN_PROGRESS,
    COUNT_IF(status='Completed') AS COMPLETED,
    COUNT_IF(status='Issue') AS ISSUE
FROM DEV.TESTDEC.Ticket
"""

df = pd.read_sql(query, conn)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Tickets", df["TOTAL"][0])
col2.metric("In Progress", df["IN_PROGRESS"][0])
col3.metric("Completed", df["COMPLETED"][0])
col4.metric("Issues & Blocked", df["ISSUE"][0])

st.divider()

# -----------------------------
# ALL TICKETS (CARD STYLE)
# -----------------------------
tickets = pd.read_sql(
    "SELECT * FROM DEV.TESTDEC.Ticket ORDER BY created_at DESC",
    conn
)

st.subheader("All Tickets")

for _, row in tickets.iterrows():
    with st.container(border=True):
        col1, col2 = st.columns([8,2])

        with col1:
            st.markdown(f"### {row['TITLE']}")
            st.write(row["DESCRIPTION"])

            st.markdown(
                f"**Status:** `{row['STATUS']}` | "
                f"**Priority:** `{row['PRIORITY']}`"
            )

        with col2:
            if st.button("View", key=f"view_{row['TICKET_ID']}"):
                st.session_state.selected_ticket = row["TICKET_ID"]

# -----------------------------
# TICKET DETAIL PAGE
# -----------------------------
if "selected_ticket" in st.session_state:

    ticket_id = st.session_state.selected_ticket
    ticket = pd.read_sql(
        f"SELECT * FROM DEV.TESTDEC.Ticket WHERE ticket_id={ticket_id}",
        conn
    ).iloc[0]

    st.divider()
    st.header(ticket["TITLE"])

    st.write(ticket["DESCRIPTION"])
    st.write("Status:", ticket["STATUS"])
    st.write("Priority:", ticket["PRIORITY"])

    # Comments
    comments = pd.read_sql(
        f"""
        SELECT c.comment_text, c.created_at
        FROM DEV.TESTDEC.Ticket_Comment c
        WHERE c.ticket_id={ticket_id}
        ORDER BY created_at DESC
        """,
        conn
    )

    st.subheader("Comments")

    for _, c in comments.iterrows():
        st.write(f"🗨️ {c['COMMENT_TEXT']}")
        st.caption(c["CREATED_AT"])

    comment = st.text_area("Add Comment")

    if st.button("Post Comment"):
        insert_comment = f"""
        INSERT INTO DEV.TESTDEC.Ticket_Comment
        (ticket_id, user_id, comment_text, created_at)
        VALUES
        ({ticket_id}, 1, '{comment}', CURRENT_TIMESTAMP())
        """
        with conn.cursor() as cursor:
            cursor.execute(insert_comment)

        st.success("Comment added!")
        st.rerun()

# -----------------------------
# MODAL POPUP
# -----------------------------
if st.session_state.get("show_modal"):

    @st.dialog("Create New Ticket")
    def create_ticket_modal():

        title = st.text_input("Title")
        description = st.text_area("Description")
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])

        if st.button("Submit"):

            insert_query = f"""
            INSERT INTO DEV.TESTDEC.Ticket
            (title, description, status, priority, created_at)
            VALUES
            ('{title}', '{description}', 'New', '{priority}', CURRENT_TIMESTAMP())
            """

            with conn.cursor() as cursor:
                cursor.execute(insert_query)

            st.success("Ticket Created!")
            st.session_state.show_modal = False
            st.rerun()

    create_ticket_modal()
