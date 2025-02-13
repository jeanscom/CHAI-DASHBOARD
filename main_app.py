import pandas as pd
import sqlite3
import os
import csv
import webbrowser
from datetime import datetime, date, timedelta
import streamlit as st
import requests
from tqdm import tqdm
import plotly.express as px
import dash
import sister_management as sm
import open_linkapp as openapp
import Sql_manage as sqm
import reminder as rem
import rpodash as rp

# st.set_page_config(
#     page_title="Chai Tele Medicine Dashboard",
#     page_icon="🏥",
#     layout="wide"
# )

def login():
    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user:
        if st.session_state.user["role"] == "Admin":
            admin_page()
        else:
            user_page()  # Call user_page without parameters

    else:
        # Display login form
        st.subheader("Login")
        username = st.text_input('Enter username: ', placeholder="Enter Your Email ID")
        password = st.text_input('Enter password: ', type='password', placeholder="Enter Your Password")
        
        if st.button("Login"):
            if (username in ['j', 'J']) and (password in ['j', 'J']):
                st.session_state.user = {
                    "role": "Admin",
                    "name": "Admin"
                }
                st.success("Welcome, Admin!")
                st.rerun()  # Use experimental_rerun to refresh the app
            
            else:
                conn = sqlite3.connect("chai.db")
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE email=? AND password=?', (username, password))
                data = cursor.fetchone()
                
                if data is None:
                    st.error("Invalid credentials. Please try again.")
                else:
                    # Store user information in session state
                    
                    st.session_state.user = {
                        "role": "User",
                        "name": data[1],
                        "email": data[3],
                        "ru": data[5]
                    }
                    st.success(f"Welcome, {data[1]}!") 
                    st.rerun() 
                
                conn.close()

def admin_page():
    if st.sidebar.button("Logout"):
        st.session_state.user = None  # Clear user session  
        st.success("You have been logged out successfully!")
        st.rerun()
    st.title("CHAI TELE MEDICINE DASHBOARD")
    conn = sqlite3.connect("chai.db")
    csv_file = "dataset.csv"
    def downlaod_prescription():
        st.header("Patient Prescriptions")  
        # Create date input widgets
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")

        # Function to get consultation data
        def get_consultation_data(start_date, end_date):
            conn = sqlite3.connect("chai.db")
            try:
                query = f"""
                SELECT *
                FROM daily_calls
                WHERE date BETWEEN '{start_date}' AND '{end_date}'
                """
                df = pd.read_sql_query(query, conn)
                return df
            finally:
                conn.close()

        # Get data based on date range
        if start_date and end_date:
            try:
                # Convert dates to string format for SQLite query
                start_date_str = start_date.strftime('%Y-%m-%d')
                end_date_str = end_date.strftime('%Y-%m-%d')
                
                # Get the consultation data
                df = get_consultation_data(start_date_str, end_date_str)
                
                if not df.empty:
                    # Filter by nurse
                    selected_nurse = st.selectbox("Select Active Sister", options=sorted(df['Nurse Name'].unique()))
                    
                    if selected_nurse:
                        # Get patients for selected nurse
                        nurse_patients = df[df['Nurse Name'] == selected_nurse]
                                            
                        # Get unique dates for the selected nurse
                        dates = sorted(nurse_patients['Date'].unique())
                        selected_date = st.selectbox("Select Date", options=dates)
                        if selected_date:
                            # Get patients for this date
                            daily_patients = nurse_patients[nurse_patients['Date'] == selected_date]
                            
                            # Create dropdown for patients
                            patient_list = daily_patients['PatientName'].unique()
                            selected_patient = st.selectbox(
                                "Select Patient",
                                options=patient_list
                            )
                            
                            if selected_patient:
                                # Get selected patient's data
                                patient = daily_patients[daily_patients['PatientName'] == selected_patient].iloc[0]
                                
                                # Display patient details
                                st.write("---")
                                st.subheader("Patient Details")
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.write(f"**Patient Name:** {patient['PatientName']}")
                                    st.write(f"**Doctor:** {patient['doctorName']}")
                                
                                with col2:
                                    st.write(f"**Date:** {selected_date}")
                                    st.write(f"**Active Sister:** {selected_nurse}")
                                
                                # Prescription section
                                st.write("---")
                                st.subheader("Prescription")
                                
                                if pd.notna(patient['prescription generated']):
                                    try:
                                        # Get the prescription URL
                                        prescription_url = patient['prescription generated']
                                        
                                        # Create HTML link button
                                        st.markdown(
                                            f'<a href="{prescription_url}" target="_blank">'
                                            f'<button style="background-color:#4CAF50; color:white; padding:12px 24px; '
                                            f'border:none; border-radius:4px; cursor:pointer; width:100%; font-size:16px;">'
                                            f'📋 Download Prescription</button></a>',
                                            unsafe_allow_html=True
                                        )
                                    except Exception as e:
                                        st.error(f"Error accessing prescription: {str(e)}")
                                else:
                                    st.warning("No prescription available for this consultation")
                else:
                    st.warning("No data available for the selected date range")
                    
            except Exception as e:
                st.error(f"Error retrieving data: {str(e)}")

    def export_to_sql(csv_file):
        # Read the CSV file
        df = pd.read_csv(csv_file)
        n = len(df)  # This is where n is calculated

        # Convert the 'Date' column to the correct format
        df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y').dt.strftime('%Y-%m-%d')

        # Add new columns for day, month, and year
        df['day'] = pd.to_datetime(df['Date']).dt.day
        df['month'] = pd.to_datetime(df['Date']).dt.strftime('%B')  # Month name
        df['year'] = pd.to_datetime(df['Date']).dt.year

        # Write the DataFrame to the SQLite database
        conn = sqlite3.connect('chai.db')  # Ensure connection is created in the current thread
        try:
            df.to_sql("daily_calls", conn, if_exists='append', index=False)
            conn.commit()
        except Exception as e:
            print(f"Error: {e}")
        finally:
            conn.close()
        
        return n  # Return n to be used later

    def csv_to_sqlite():
        st.header("Uploading Csv to Db")
        conn = sqlite3.connect('chai.db')  # Get connection in the current thread
        cursor = conn.cursor()
        uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx"])

        if uploaded_file is not None:
            # Show the uploaded file name
            st.success(f"Uploaded file: {uploaded_file.name}")

            # Process CSV or Excel file
            if uploaded_file.name.endswith(".csv"):

                with open(uploaded_file.name, 'r') as file:
                    tname=uploaded_file.name.split(".")

                    csv_reader = csv.reader(file)
                    headers = next(csv_reader)
                    
                    # Create the table if it doesn't exist
                    create_table_query = f"CREATE TABLE IF NOT EXISTS {tname[0]} ({', '.join(headers)});"
                    cursor.execute(create_table_query)
                    
                    # Insert data
                    insert_data_query = f"INSERT INTO {tname[0]} VALUES ({', '.join(['?'] * len(headers))});"
                    for row in csv_reader:
                        cursor.execute(insert_data_query, row)
                
                conn.commit()
                st.success("CSV data inserted into SQLite successfully!")
                conn.close()
    def sqlite_to_excel():
        try:
            # Create a new connection in the current thread
            conn = sqlite3.connect('chai.db')
            
            # Execute the query
            query = "SELECT * FROM daily_calls;"
            df = pd.read_sql_query(query, conn)

            # Export the data to an Excel file
            excel_file_path = 'output_excel_file.xlsx'
            df.to_excel(excel_file_path, index=False)

            # Success message
      # Use len(df) here directly
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            # Always close the connection
            conn.close()


    def download_file_by_date(start_date=None, end_date=None):
        """Download file using start_date and end_date."""
        if not start_date or not end_date:
            st.error("Start date and end date are required")
            return
        
        url = f"https://champs.billionlives.in:8000/consultation_api/getCallLogsCSV?startdate={start_date}&enddate={end_date}"
        response = requests.get(url)

        if response.status_code == 200:
            csv_file_path = "dataset.csv"
            with open(csv_file_path, "wb") as file:
                file.write(response.content)
            
            # Now pass csv_file_path to export_to_sql and get n
            n = export_to_sql(csv_file_path)
            
            # Now run sqlite_to_excel
            sqlite_to_excel()
            
            st.success("File downloaded and exported to Database successfully!")
            st.write(f"{n} Datas exported successfully!")
        else:
            st.error(f"Failed to download file. Status code: {response.status_code}")

    #Download csv and displaying total counts each time
    def download_file():
        url = "https://champs.billionlives.in:8000/consultation_api/getTodayCallLogsCSV"
        response = requests.get(url)

        if response.status_code == 200:
            with open("dataset.csv", "wb") as file:
                file.write(response.content)
            

    def tracking():
            """Tracking details from the dataset."""
            try:    
                df = pd.read_csv("dataset.csv")
                n = len(df) - 1
                no_of_sister = df["Nurse Name"].unique()
                sn = len(no_of_sister)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.header("Total Consultation")
                    st.metric(label="Consultations", value=n)
                
                with col2:
                    st.header("Total Number of Sisters")
                    st.metric(label="Nurses", value=sn)
                
                with st.expander("Consultation Status"):
                    df2 = df["Status_Final"].groupby(df["Status_Final"]).count()
                    st.write(df2)
                
                with st.expander("Doctors Consultation Status"):
                    status_count = df.groupby([df["doctorName"], df["Status_Final"]]).size().unstack(fill_value=0)
                    status_count = status_count.reset_index().rename_axis(None, axis=1)
                    st.write(status_count)
                
                with st.expander("Regional Wise Status"):
                    reg_count = df["RegionalUnit"].groupby(df["RegionalUnit"]).count()
                    st.write(reg_count)
                
                with st.expander("Sister Nurse Status"):
                    df = df.rename(columns={"Nurse Name": "NurseName"})
                    sister_count = df["NurseName"].groupby(df["NurseName"]).count()
                    st.write(sister_count)
            except Exception as e:
        
                st.error(f"Error: {e}")
    def doctor_live():
        url = "https://champs.billionlives.in:8000/api/getAllOnlineCounsellorsApi/5f05ce8de3c290416ba40805"
        response = requests.get(url)
        
    # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the response as JSON
            st.header("Online Doctors")
            data = response.json()
            lst=data["doctors"]
        
            if lst==[]:
                st.write("No doctors available ")
            else:
                for i in lst:
                    st.write(i["name"])
        else:
            st.write(f"Error: {response.status_code}")


        
    main_option = st.sidebar.selectbox(
        "Main Menu:",
        ["Dashboard","Daily Tracking", "Doctor Live", "Import/Export", "Admin","Open App","Contact Sisters","Set Reminder"])

    if main_option=="Dashboard":
        dash.dashboard()

    elif main_option=="Daily Tracking":
        download_file()
        tracking()

    elif main_option=="Doctor Live":
        doctor_live()

    elif main_option=="Set Reminder":
        rem.reminder()    

    elif main_option=="Import/Export":
        import_option = st.sidebar.selectbox(
            "Import/Export Menu:",
            ["Date Wise Download","Upload Files","Download Prescription","Upload Csv to Db"])
        if import_option == "Date Wise Download":
            st.header("Download Data Date Wise")
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")
            start_date = st.text_input("Enter Start Date (DD-MM-YYYY)", value=yesterday, key="main_start_date")
            end_date = st.text_input("Enter End Date (DD-MM-YYYY)", value=yesterday, key="main_end_date")
            if st.button("Download & Export"):
                if start_date and end_date:
                    try:
                        # Validate date format
                        datetime.strptime(start_date, "%d-%m-%Y")
                        datetime.strptime(end_date, "%d-%m-%Y")

                        #s Download file by date range
                        download_file_by_date(start_date, end_date)
                    except ValueError:
                        st.error("Invalid date format. Please enter dates in DD-MM-YYYY format.")
                else:
                    st.error("Please enter both start and end dates.")
        elif import_option == "Upload Files":
            st.write("Upload Files")
        elif import_option == "Download Prescription":
            downlaod_prescription()
        elif import_option == "Upload Csv to Db":
            csv_to_sqlite()
    elif main_option=="Admin":
        st.write("Welcome to Admin")
        admin_option = st.sidebar.selectbox(
            "Choose an action:",
            ["Manage Users","Manage Data","Manage Sisters", "Manage Shortcuts", "Manage Reminder"])
            
        if admin_option == "Manage Data":
            Data_action = st.sidebar.selectbox("Manage Data :", ["DB Commands","Delete Files","Add Folders","Delete Folders"])
            if Data_action == "DB Commands":
                sqm.db_command() 
        elif admin_option == "Manage Users":
            
            def list_users():
                st.subheader("List of Users")
                conn = sqlite3.connect('chai.db')
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users')
                users = cursor.fetchall()
                
                df=pd.read_sql_query('SELECT * FROM users', conn)
                if not df.empty:
                    st.table(df)
                else:
                    st.write("No users found.")

            # Function to edit user
            def edit_user():
                st.subheader("Edit User")
                conn = sqlite3.connect('chai.db')
                cursor = conn.cursor()
                cursor.execute('SELECT userid, name FROM users')
                users = cursor.fetchall()
                conn.close()

                user_options = {user[1]: user[0] for user in users}
                selected_user = st.selectbox('Select User to Edit', list(user_options.keys()))

                if selected_user:
                    user_id = user_options[selected_user]
                    conn = sqlite3.connect('chai.db')
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM users WHERE userid = ?', (user_id,))
                    user_details = cursor.fetchone()
                    conn.close()

                    if user_details:
                        name = st.text_input('Name', user_details[1])
                        mobile = st.text_input('Mobile', user_details[2])
                        email = st.text_input('Email', user_details[3])
                        post = st.selectbox('Post', ["Admin", "PM", "APM", "RPO"], index=["Admin", "PM", "APM", "RPO"].index(user_details[4]))
                        regional_unit = st.selectbox('Regional Unit', ["All", "CHAAP", "CHABIJAN", "CHAKA", "CHAKE", "CHAMP", "CHAT", "CHAW", "NECHA", "OCHA", "RUPCHA", "WEBCHA"], index=["All", "CHAAP", "CHABIJAN", "CHAKA", "CHAKE", "CHAMP", "CHAT", "CHAW", "NECHA", "OCHA", "RUPCHA", "WEBCHA"].index(user_details[5]))
                        password = st.text_input('Password', user_details[6], type='password')

                        if st.button('Update User'):
                            conn = sqlite3.connect('chai.db')
                            cursor = conn.cursor()
                            cursor.execute('''
                                UPDATE users 
                                SET name = ?, mobile = ?, email = ?, post = ?, RegionalUnit = ?, password = ?
                                WHERE userid = ?
                            ''', (name, mobile, email, post, regional_unit, password, user_id))
                            conn.commit()
                            conn.close()
                            st.success('User updated successfully!')

            # Function to delete user
            def delete_user():
                st.subheader("Delete User")
                conn = sqlite3.connect('chai.db')
                cursor = conn.cursor()
                cursor.execute('SELECT userid, name FROM users')
                users = cursor.fetchall()
                conn.close()

                user_options = {user[1]: user[0] for user in users}
                selected_user = st.selectbox('Select User to Delete', list(user_options.keys()))

                if selected_user:
                    user_id = user_options[selected_user]
                    if st.button('Delete User'):
                        conn = sqlite3.connect('chai.db')
                        cursor = conn.cursor()
                        cursor.execute('DELETE FROM users WHERE userid = ?', (user_id,))
                        conn.commit()
                        conn.close()
                        st.success('User deleted successfully!')

            # Main function to handle user actions
            def main():
                user_action = st.sidebar.selectbox("Choose Action", ["Add User", "List Users", "Edit User", "Delete User"])

                if user_action == "Add User":
                    add_user()
                elif user_action == "List Users":
                    list_users()
                elif user_action == "Edit User":
                    edit_user()
                elif user_action == "Delete User":
                    delete_user()

            # Function to add user (from your original code)
            def add_user():
                st.subheader("Add User")
                name = st.text_input('Name')
                mobile = st.text_input('Mobile')
                email = st.text_input('Email')
                post = st.selectbox('Post', ["Admin", "PM", "APM", "RPO"])
                regional_unit = st.selectbox('Regional Unit', ["All", "CHAAP", "CHABIJAN", "CHAKA", "CHAKE", "CHAMP", "CHAT", "CHAW", "NECHA", "OCHA", "RUPCHA", "WEBCHA" ])
                password = st.text_input('Password', type='password')
                if st.button('Add User'):
                    conn = sqlite3.connect('chai.db')   
                    cursor = conn.cursor()
                    cursor.execute('''INSERT INTO users (name, mobile, email, post, RegionalUnit, password) VALUES (?, ?, ?, ?, ?, ?)''', (name, mobile, email, post, regional_unit, password))
                    conn.commit()
                    st.success('User added successfully!')

        # Call the main function
            main()

        elif admin_option == "Manage Sisters":
            sm.sister_menu()
        elif admin_option=="Manage Shortcuts":
            openapp.shortcut_menu()

    elif main_option=="Open App":
        openapp.open_shortcuts()
    elif main_option=="Contact Sisters":
         sm.contact_sisters()
def user_page():
    if st.sidebar.button("Logout"):
        st.session_state.user = None  # Clear user session  
        st.success("You have been logged out successfully!")
        st.rerun()
    st.header("CHAI Tele Medicine Dashboard")
    user_option=st.sidebar.selectbox("Select ",["Profile","Dashboard","sister","Change Password"])
    email = st.session_state.user.get("email")

    def change_password(email):
        con = sqlite3.connect("chai.db")
        cursor = con.cursor()

        # Fetch the current password for the user
        cursor.execute("SELECT password FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()

        if result:
            current_password = result[0]

            # Input for old password
            old_password = st.text_input("Enter your old password", type="password")

            # Initialize session state for verification
            if "verified" not in st.session_state:
                st.session_state.verified = False

            if st.button("Verify Old Password"):
                if old_password == current_password:
                    st.session_state.verified = True
                    st.success("Old password verified! Enter new password below.")
                else:
                    st.session_state.verified = False
                    st.error("Old password is incorrect.")

            # If verified, allow new password input
            if st.session_state.verified:
                new_password = st.text_input("Enter your new password", type="password")

                if st.button("Change Password"):
                    if new_password:
                        cursor.execute("UPDATE users SET password = ? WHERE email = ?", (new_password, email))
                        con.commit()
                        st.success("Password changed successfully!")
                        st.session_state.verified = False  # Reset verification state
                    else:
                        st.error("New password cannot be empty.")
        else:
            st.error("User not found.")
        con.close()
        
    def display_user_profile():
        # Retrieve user details from the database
        email = st.session_state.user.get("email")
         # Assuming the email is stored in the session state
        conn = sqlite3.connect("chai.db")
        cursor = conn.cursor()
        cursor.execute('SELECT name, mobile, email, post, RegionalUnit FROM users WHERE email=?', (email,))
        user_data = cursor.fetchone()
        
        if user_data:
            st.header("USER PROFILE")
            st.write("Name: ", user_data[0])
            st.write("Mobile: ", user_data[1])
            st.write("Email: ", user_data[2])
            st.write("Post: ", user_data[3])
            st.write("Regional Unit: ", user_data[4])
            
            st.write("-------------------")
        else:
            st.error("User profile not found.")
        conn.close()
    if user_option=="Profile":
            display_user_profile()
    elif user_option=="Dashboard":
        reg=st.session_state.user.get("ru")
        if reg!="All":
            rp.dashboard(reg)
        else:
             dash.dashboard()
    elif user_option=="sister":
            reg=st.session_state.user.get("ru")
            display_sister(reg)

def display_sister(reg):
    
    con = sqlite3.connect("chai.db")
    
    if reg!="All":
    # Correcting the query formatting

        query = "SELECT * FROM sister WHERE RegionalUnit = ?"
        # Using params argument separately
        df = pd.read_sql_query(query, con, params=(reg,))
        so=st.sidebar.selectbox("Select menu:",["List of Sisters","Edit Sister Details"])
        if so=="List of Sisters":
            st.header("LIST OF ENROLLED SISTERS")
            n=len(df)
            st.subheader(f"Total Number of Sisters : {n}")
            st.write(df)

        elif so=="Edit Sister Details":
            st.header("EDIT SISTER DETAILS")
            sisters = df['SisterName'].tolist() if not df.empty else []
            
            if sisters:
                selected_sister = st.sidebar.selectbox("Select Sister to Edit", sisters)
                sister_data = df[df['SisterName'] == selected_sister].iloc[0]
                
                new_name = st.text_input("Name", value=sister_data['SisterName']).strip()
                new_mobile = st.text_input("Mobile", value=sister_data['Mobile'])
                new_email = st.text_input("Email", value=sister_data['Email'])
                new_regunit = st.text_input("Regionalnit", value=sister_data['RegionalUnit'])
                new_miname = st.text_input("Minam", value=sister_data['MIName'])
                new_designation = st.text_input("Designation", value=sister_data['Designation'])
                new_state = st.text_input("State", value=sister_data['State'])
                new_status = st.text_input("Status", value=sister_data['Status'])
                new_remarks = st.text_area("Remarks", value=sister_data['Remarks']) 
                

                if st.button("Save Changes"):
                    cursor = con.cursor()
                    cursor.execute("""
                        UPDATE sister 
                        SET SisterName = ?, Mobile = ?, Email = ?, RegionalUnit = ?, MIName = ?, Designation = ?, State = ?, Status = ?, Remarks = ? WHERE SisterName = ?
                    """, (new_name, new_mobile, new_email, new_regunit, new_miname, new_designation, new_state, new_status, new_remarks, selected_sister))
                    con.commit()
                    st.success("Sister details updated successfully!")
                
            else:
                st.warning("No sisters available for editing.")

       
    else:
        st.header("LIST OF ENROLLED SISTERS")
        query = "SELECT * FROM sister"
        # Using params argument separately
        df = pd.read_sql_query(query, con,)
           
        n=len(df)
        st.subheader(f"Total Number of Sisters : {n}")
        st.write(df)
        
    con.close()

def change_password(email):
    con = sqlite3.connect("chai.db")
    cursor = con.cursor()

    # Fetch the current password for the user
    cursor.execute("SELECT password FROM users WHERE email = ?", (email,))
    result = cursor.fetchone()
    email=result[3]

    if result:
        current_password = result[0]

        # Input for old password
        old_password = st.text_input("Enter your old password", type="password")

        if st.button("Verify Old Password"):
            if old_password == current_password:
                # Input for new password
                new_password = st.text_input("Enter your new password", type="password")

                if st.button("Change Password"):
                    # Update the password in the database
                    cursor.execute("UPDATE users SET password = ? WHERE email = ?", (new_password, email))
                    con.commit()
                    st.success("Password changed successfully!")
            else:
                st.error("Old password is incorrect.")
    else:
        st.error("User not found.")

    con.close()
 
login()
