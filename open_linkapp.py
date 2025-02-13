import streamlit as st
import sqlite3

# Connect to SQLite database
def get_connection():
    return sqlite3.connect('chai.db')

# Create table if it doesn't exist
def create_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS openlink (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            linkname TEXT NOT NULL,
            username TEXT,
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Add a new record to the database
def add_record(name, linkname, username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO openlink (name, linkname, username, password) VALUES (?, ?, ?, ?)',
                   (name, linkname, username, password))
    conn.commit()
    conn.close()

# List all records from the database
def list_records():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM openlink')
    records = cursor.fetchall()
    conn.close()
    return records

# Delete a record from the database
def delete_record(record_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM openlink WHERE id = ?', (record_id,))
    conn.commit()
    conn.close()

# Modify a record in the database
def modify_record(record_id, name, linkname, username, password):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE openlink SET name = ?, linkname = ?, username = ?, password = ? WHERE id = ?',
                      (name, linkname, username, password, record_id))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return False
    except Exception as e:
        st.error(f"Error: {e}")
        return False

# Search records by ID
def search_record(record_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM openlink WHERE id = ?', (record_id,))
    record = cursor.fetchone()
    conn.close()
    return record

# Open a link by name using HTML

def open_link_html(linkname):
    st.markdown(f'<a href="{linkname}" target="_blank">Open Link</a>', unsafe_allow_html=True)

# Streamlit app interface
def open_shortcuts():
    st.subheader('Openlink Records')
    records = list_records()
    for record in records:
        with st.expander(record[1]):
            st.write(f'Username: {record[3]}')
            st.write(f'Password: {record[4]}')
            open_link_html(record[2])

def shortcut_menu():
    create_table()
    st.title('Openlink Manager')

    menu = ['Add', 'List', 'Delete', 'Modify', 'Search']
    choice = st.sidebar.selectbox('Menu', menu)

    if choice == 'Add':
        st.subheader('Add Record')
        name = st.text_input('Name')
        linkname = st.text_input('Link Name')
        username = st.text_input('Username')
        password = st.text_input('Password')
        if st.button('Add'):
            add_record(name, linkname, username, password)
            st.success('Record added successfully!')

    elif choice == 'List':
        st.subheader('List Records')
        records = list_records()
        for record in records:
            st.write(f'ID: {record[0]}, Name: {record[1]}, Link Name: {record[2]}, Username: {record[3]}, Password: {record[4]}')

    elif choice == 'Delete':
        st.subheader('Delete Record')
        record_id = st.number_input('Record ID', min_value=1)
        if st.button('Delete'):
            delete_record(record_id)
            st.success('Record deleted successfully!')

    elif choice == 'Modify':
        st.subheader('Modify Record')
        record_id = st.number_input('Record ID to modify', min_value=1, key='modify_id')
        search_btn = st.button('Search Record')

        if search_btn:
            record = search_record(record_id)
            if record:
                with st.form(key='modify_form'):
                    name = st.text_input('Name', value=record[1])
                    linkname = st.text_input('Link Name', value=record[2])
                    username = st.text_input('Username', value=record[3])
                    password = st.text_input('Password', value=record[4], type='password')
                    submit_button = st.form_submit_button(label='Update Record')
                    
                    if submit_button:
                        if name and linkname:
                            if modify_record(record_id, name, linkname, username, password):
                                st.success('Record modified successfully!')
                                st.rerun()
                        else:
                            st.error('Name and Link Name are required fields!')
            else:
                st.error('Record not found! Please check the ID and try again.')

    elif choice == 'Search':
        st.subheader('Search Records')
        record_id = st.number_input('Record ID', min_value=1, key='search_id')
        if st.button('Search'):
            record = search_record(record_id)
            if record:
                st.write(f'ID: {record[0]}, Name: {record[1]}, Link Name: {record[2]}, Username: {record[3]}, Password: {record[4]}')
            else:
                st.error('Record not found!')
