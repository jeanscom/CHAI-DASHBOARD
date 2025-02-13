import streamlit as st
import sqlite3
from datetime import datetime, date, timedelta
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import threading

# Email credentials
SENDER_EMAIL = "scomcoaching@gmail.com"
SENDER_PASSWORD = "xgbf hqum tlys gweq"
RECEIVER_EMAIL = "jean-toms@chai-india.org"

# Initialize database
def init_db():
    conn = sqlite3.connect('reminder.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            completed BOOLEAN DEFAULT 0,
            notified BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Email Configuration
def send_email(subject, body, to_email=RECEIVER_EMAIL):
    message = MIMEMultipart()
    message["From"] = SENDER_EMAIL
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(message)
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {str(e)}")

# Check for upcoming reminders and send emails
def check_reminders():
    while True:
        try:
            conn = sqlite3.connect('reminder.db')
            c = conn.cursor()
            current_time = datetime.now()
            current_date = current_time.strftime('%Y-%m-%d')
            current_minute = current_time.strftime('%H:%M')
            
            c.execute('''
                SELECT id, task, date, time 
                FROM reminders 
                WHERE date = ? AND time = ? AND completed = 0 AND notified = 0
            ''', (current_date, current_minute))
            
            due_tasks = c.fetchall()
            
            if due_tasks:
                task_ids = [task[0] for task in due_tasks]
                placeholders = ','.join('?' * len(task_ids))
                c.execute(f'UPDATE reminders SET notified = 1 WHERE id IN ({placeholders})', task_ids)
                conn.commit()
                
                for task in due_tasks:
                    subject = "🔔 Reminder: Task Due Now!"
                    body = f"Task: {task[1]}\nDate: {task[2]}\nTime: {task[3]}\n\nThis task is due now!"
                    send_email(subject, body)
            
            conn.close()
        except Exception as e:
            print(f"Error checking reminders: {str(e)}")
        
        time.sleep(30)  # Check every 30 seconds

# Start the reminder checking thread
def init_notification_thread():
    if 'notification_thread' not in st.session_state:
        thread = threading.Thread(target=check_reminders, daemon=True)
        thread.start()
        st.session_state.notification_thread = thread
        
def update_reminder(id, task, date_obj, time_obj):
    conn = sqlite3.connect('reminder.db')
    c = conn.cursor()
    date_str = date_obj.strftime('%Y-%m-%d')
    time_str = time_obj.strftime('%H:%M')
    c.execute('UPDATE reminders SET task = ?, date = ?, time = ? WHERE id = ?', (task, date_str, time_str, id))
    conn.commit()
    conn.close()

def delete_reminder(id):
    conn = sqlite3.connect('reminder.db')
    c = conn.cursor()
    c.execute('DELETE FROM reminders WHERE id = ?', (id,))
    conn.commit()
    conn.close()

def get_all_reminders():
    conn = sqlite3.connect('reminder.db')
    df = pd.read_sql_query('SELECT id, task, date, time, completed FROM reminders ORDER BY date DESC, time', conn)
    if not df.empty:
        df['date'] = pd.to_datetime(df['date']).dt.date
        df['time'] = pd.to_datetime(df['time'], format='%H:%M').dt.time
    conn.close()
    return df

def reminder():
    st.title('📅 Daily Reminder App')
    init_db()
    init_notification_thread()
    
    menu = st.sidebar.selectbox('Menu',['Todays Tasks', 'Add Reminder','Edit Reminders'])
        
    if menu == 'Todays Tasks':
        st.subheader("Today's Tasks")
        today = date.today()
        conn = sqlite3.connect('reminder.db')
        df = pd.read_sql_query('SELECT id, task, time, completed FROM reminders WHERE date = ? ORDER BY time', conn, params=(today.strftime('%Y-%m-%d'),))
        if not df.empty:
            df['time'] = pd.to_datetime(df['time'], format='%H:%M').dt.time
        conn.close()
        
        if df.empty:
            st.info('No tasks for today! 🎉')
        else:
            for _, row in df.iterrows():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(row['task'])
                with col2:
                    st.write(row['time'].strftime('%I:%M %p'))
                with col3:
                    done = st.button('✅ Done' if not row['completed'] else '↩️ Undo', key=f'done_{row["id"]}')
                    if done:
                        conn = sqlite3.connect('reminder.db')
                        c = conn.cursor()
                        c.execute('UPDATE reminders SET completed = ? WHERE id = ?', (not row['completed'], row['id']))
                        conn.commit()
                        conn.close()
                        st.rerun()
                        
    elif menu == 'Edit Reminders':
        df = get_all_reminders()
        if not df.empty:
            task_options = {row['task']: row['id'] for _, row in df.iterrows()}
            selected_task = st.selectbox('📋 Select a task to edit', list(task_options.keys()))
            if selected_task:
                task_id = task_options[selected_task]
                with st.form(f'edit_form_{task_id}'):
                    task = st.text_input('Task', selected_task)
                    reminder_date = st.date_input('Date')
                    reminder_time = st.time_input('Time')
                    col1, col2 = st.columns(2)
                    with col1:
                        update_button = st.form_submit_button('💾 Update')
                    with col2:
                        delete_button = st.form_submit_button('🗑️ Delete')
                    if update_button:
                        update_reminder(task_id, task, reminder_date, reminder_time)
                        st.success('✅ Task updated successfully!')
                    if delete_button:
                        delete_reminder(task_id)
                        st.success('🗑️ Task deleted successfully!')
                    
    elif menu == 'Add Reminder':
        st.subheader('Add New Reminder')
        with st.form('add_reminder', clear_on_submit=True):
            task = st.text_input('Task')
            col1, col2 = st.columns(2)
            with col1:
                reminder_date = st.date_input('Date')
            with col2:
                reminder_time = st.time_input('Time')
            
            if st.form_submit_button('Add Reminder'):
                if task:
                    conn = sqlite3.connect('reminder.db')
                    c = conn.cursor()
                    c.execute('INSERT INTO reminders (task, date, time) VALUES (?, ?, ?)', (task, reminder_date.strftime('%Y-%m-%d'), reminder_time.strftime('%H:%M')))
                    conn.commit()
                    conn.close()
                    st.success('Reminder added successfully!')
                else:
                    st.error('Please enter a task')
