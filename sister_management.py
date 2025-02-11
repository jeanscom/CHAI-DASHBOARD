import streamlit as st
import sqlite3
import pandas as pd

ru=["CHAAP", "CHABIJAN", "CHAKA", "CHAKE", "CHAMP", "CHAT", "CHAW", "NECHA", "OCHA", "RUPCHA", "WEBCHA"]
# Set page configuration
def get_db_connection():
        try:
            conn = sqlite3.connect('chai.db')
            return conn
        except sqlite3.Error as e:
            st.error(f"Database connection error: {e}")
            return None
def search_records_by_name(search_term):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sisters WHERE sistername LIKE ? OR mobile LIKE ?', 
               (f'%{search_term}%', f'%{search_term}%'))
        records = cursor.fetchall()
        conn.close()
        return records

def modify_record_1(nm,mob,stat,rem):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE sisters SET mobile = ?, status = ?, remarks = ? WHERE sistername = ?',
                       (mob, stat, rem, nm))
        cursor.connection.commit()
        cursor.connection.close()
    
def list_records():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sisters')
        records = cursor.fetchall()
        conn.close()
        return records


def contact_sisters():
    st.subheader('📞 Contact Actions')
    
    # Search Bar
    search_term = st.text_input('🔍 Search by name', key='search_input')
    
    # Fetch records based on search
    records = search_records_by_name(search_term) if search_term else list_records()

    if search_term and not records:
        st.info('No contacts found matching your search.')
    
    elif records:
        # Display Search Results Table
        st.subheader('Results' if search_term else 'All Contacts')
        results_df = [{'Name': r[0], 'Status': r[7], 'Remarks': r[8]} for r in records]
        st.table(results_df)
        st.divider()

        # Detailed View with Actions
        for record in records:
            name, phone, status, remarks = record[0], record[1], record[7], record[8]

            with st.expander(f"📌 {name} - {phone}"):
                col1, col2 = st.columns([2, 1])
                
                # Contact Buttons
                with col1:
                    st.markdown(f'[📞 Call {phone}](tel:{phone})', unsafe_allow_html=True)
                    st.markdown(f'[💬 WhatsApp](https://wa.me/{phone})', unsafe_allow_html=True)
                
                # Status and Remarks
                with col2:
                    new_mobile = st.text_input('Phone Number', value=phone, key=f"mobile_{name}")
                    new_status = st.selectbox('Status', ['Active', 'Inactive', 'Retreat', 'Meeting'], 
                                              index=['Active', 'Inactive', 'Retreat', 'Meeting'].index(status) if status else 0, 
                                              key=f"status_{name}")
                    
                    new_remarks = st.text_area('Remarks', value=remarks if remarks else '', key=f"remarks_{name}")
                    
                    if st.button('💾 Update', key=f"update_{name}"):
                        modify_record_1(name, new_mobile, new_status, new_remarks)
                        st.success(f'✅ {name} updated successfully!')
                        st.rerun()

def sister_menu():
    # st.set_page_config(page_title="Sister Management System", layout="wide")
    # st.title("Sister Management System")

    # Database connection function
    def get_db_connection():
        try:
            conn = sqlite3.connect('chai.db')
            return conn
        except sqlite3.Error as e:
            st.error(f"Database connection error: {e}")
            return None

    # Create table if it doesn't exist
    def create_table():
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sisters (
                        sistername TEXT,
                        mobile TEXT PRIMARY KEY,
                        email TEXT,
                        RegionalUnit TEXT, 
                        MIName TEXT,
                        Designation TEXT,
                        state TEXT,
                        status TEXT,
                        remarks TEXT
                    )
                ''')
                conn.commit()
            except sqlite3.Error as e:
                st.error(f"Error creating table: {e}")
            finally:
                conn.close()


    # Initialize the database
    create_table()
      # Sidebar for navigation
    menu = st.sidebar.selectbox("Menu", ["Add Sister", "List Sisters", "Search Sister", "Modify Sister", "Delete Sister"])

    if menu == "Add Sister":
        st.subheader("Add New Sister")
        with st.form("add_sister_form"):
            sister_name = st.text_input("Name").strip()
            mobile = st.text_input("Mobile").strip()
            email = st.text_input("Email").strip()
            regunit = st.selectbox("Regionalnit", ru).strip()
            miname = st.text_input("Miname").strip()
            designation = st.text_input("Designation").strip()
            state = st.text_input("State").strip()
            status = st.text_input("Status").strip()
            remarks = st.text_area("Remarks").strip()
            
            if st.form_submit_button("Add Sister"):
                if sister_name:
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        try:
                            cursor.execute('''
                                INSERT INTO sisters (sistername, mobile, email, regionalunit, miname, designation, state, status, remarks)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (sister_name, mobile, email, regunit, miname, designation, state, status, remarks))
                            conn.commit()
                            st.success("Sister added successfully!")
                        except sqlite3.IntegrityError:
                            st.error("A sister with this name already exists!")
                        except sqlite3.Error as e:
                            st.error(f"Error adding sister: {e}")
                        finally:
                            conn.close()
                else:
                    st.error("Name is required!")

    elif menu == "List Sisters":
        st.subheader("List of Sisters")
        conn = get_db_connection()
        if conn:
            try:
                sisters = pd.read_sql_query("SELECT * FROM sisters ORDER BY SisterName", conn)
                if not sisters.empty:
                    st.dataframe(sisters)
                else:
                    st.info("No sisters found in the database.")
            except sqlite3.Error as e:
                st.error(f"Error retrieving sisters: {e}")
            finally:
                conn.close()

    elif menu == "Search Sister": 
        st.subheader("Search Sister")
        search_term = st.text_input("Enter name to search").strip()
        if search_term:
            conn = get_db_connection()
            if conn:
                try:
                    sisters = pd.read_sql_query(
                        "SELECT * FROM sisters WHERE sistername LIKE ? ORDER BY SisterName",
                        conn,
                        params=[f"%{search_term}%"]
                    )
                    if not sisters.empty:
                        st.dataframe(sisters)
                    else:
                        st.info("No matching records found.")
                except sqlite3.Error as e:
                    st.error(f"Error searching sisters: {e}")
                finally:
                    conn.close()

    elif menu == "Modify Sister":
        st.subheader("Modify Sister")
        search_name = st.text_input("Enter name to search").strip()
        
        if search_name:
            conn = get_db_connection()
            if conn:
                try:
                    df = pd.read_sql_query(
                        "SELECT * FROM sisters WHERE SisterName LIKE ? ORDER BY SisterName",
                        conn,
                        params=[f"%{search_name}%"]
                    )
                    
                    if not df.empty:
                        st.write("Found sisters:")
                        st.dataframe(df)
                        
                        sister_to_modify = st.selectbox(
                            "Select sister to modify",
                            df['SisterName'].tolist()
                        )
                        
                        if sister_to_modify:
                
                            sister_data = df[df['SisterName'] == sister_to_modify].iloc[0]
                            
                            with st.form("modify_sister_form"):
                                new_name = st.text_input("Name", value=sister_data['SisterName']).strip()
                                new_mobile = st.text_input("Mobile", value=sister_data['Mobile'])
                                new_email = st.text_input("Email", value=sister_data['Email'])
                                new_regunit = st.selectbox("Regionalnit", ru, index=ru.index(sister_data['RegionalUnit']) if sister_data['RegionalUnit'] in ru else 0)
                                new_miname = st.text_input("Minam", value=sister_data['MIName'])
                                new_designation = st.text_input("Designation", value=sister_data['Designation'])
                                new_state = st.text_input("State", value=sister_data['State'])
                                new_status = st.text_input("Status", value=sister_data['Status'])
                                new_remarks = st.text_area("Remarks", value=sister_data['Remarks'])
                                
                                if st.form_submit_button("Update Sister"):
                                    if new_name:
                                        cursor = conn.cursor()
                                        try:
                                            if new_name != sister_to_modify:
                                                # If name is changed, delete old record and insert new one
                                                cursor.execute("DELETE FROM sisters WHERE sistername = ?", [sister_to_modify])
                                                cursor.execute('''
                                                    INSERT INTO sisters (sistername, mobile, email, regionalunit, miname, designation, state, status, remarks)
                                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                                ''', (new_name, new_mobile, new_email, new_regunit, new_miname, new_designation, new_state, new_status, new_remarks))
                                            else:
                                                # If name is same, just update other fields
                                                cursor.execute('''
                                                    UPDATE sisters
                                                    SET sistername = ?, mobile = ?, email = ?, regionalunit = ?, miname = ?, designation = ?, state = ?, status = ?, remarks = ?
                                                    WHERE sistername = ?
                                                ''', (new_name, new_mobile, new_email, new_regunit, new_miname, new_designation, new_state, new_status, new_remarks, new_name))
                                            conn.commit()
                                            st.success("Sister information updated successfully!")
                                                  # Refresh the page to show updated data
                                        except sqlite3.IntegrityError:
                                            st.error("A sister with this name already exists!")
                                        except sqlite3.Error as e:
                                            st.error(f"Error updating sister: {e}")
                                    else:
                                        st.error("Name is required!")
                    else:
                        st.info("No matching sisters found.")
                except sqlite3.Error as e:
                    st.error(f"Error searching sisters: {e}")
                finally:
                    conn.close()

    elif menu == "Delete Sister":
        st.subheader("Delete Sister")
        search_name = st.text_input("Enter name to search").strip()
        
        if search_name:
            conn = get_db_connection()
            if conn:
                try:
                    sisters = pd.read_sql_query(
                        "SELECT * FROM sisters WHERE sistername LIKE ? ORDER BY sistername",
                        conn,
                        params=[f"%{search_name}%"]
                    )
                    
                    if not sisters.empty:
                        st.write("Found sisters:")
                        st.dataframe(sisters)
                        
                        sister_to_delete = st.selectbox(
                            "Select sister to delete",
                            sisters['SisterName'].tolist()
                        )
                        
                        if sister_to_delete:
                            if st.button("Delete Sister"):
                                cursor = conn.cursor()
                                try:
                                    cursor.execute("DELETE FROM sisters WHERE sistername = ?", [sister_to_delete])
                                    conn.commit()
                                    st.success(f"Sister {sister_to_delete} deleted successfully!")
                                    st.rerun()  # Refresh the page to show updated data
                                except sqlite3.Error as e:
                                    st.error(f"Error deleting sister: {e}")
                    else:
                        st.info("No matching sisters found.")
                except sqlite3.Error as e:
                    st.error(f"Error searching sisters: {e}")
                finally:
                    conn.close()
