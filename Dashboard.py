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

def init_db(q):
    conn = sqlite3.connect("chai.db")
    c = conn.cursor()
    c.execute(q)
    conn.commit()
    conn.close()
# SQLite connection
conn = sqlite3.connect('chai.db')
cursor = conn.cursor()
def get_connection():
    return sqlite3.connect('chai.db')
# File configurations
today = date.today()
file_date = today.strftime("%d-%m-%Y")
csvfile = "dataset.csv"

def download_file():
    url = "https://champs.billionlives.in:8000/consultation_api/getTodayCallLogsCSV"
    response = requests.get(url)

    if response.status_code == 200:
        with open("dataset.csv", "wb") as file:
            file.write(response.content)
        st.success("File downloaded and renamed to dataset.csv successfully!")



def tracking():
    """Tracking details from the dataset."""
    try:
        if st.button("Download Today's File"):
            download_file()

        df = pd.read_csv("dataset.csv")
        n = len(df) - 1
        st.header(f"Total Number of Consultation {n}")
        no_of_sister = df["Nurse Name"].unique()
        sn = len(no_of_sister)

        st.header(f"Total Number of Sister {sn}")
        st.header("Consultation Status")
        df2 = df["Status_Final"].groupby(df["Status_Final"]).count()
        st.write(df2)
        st.header("Doctors Consultation Status")
        status_count = df.groupby([df["doctorName"], df["Status_Final"]]).size().unstack(fill_value=0)
        status_count = status_count.reset_index().rename_axis(None, axis=1)
        st.write(status_count)
        st.header("Regional Wise Status")
        reg_count = df["RegionalUnit"].groupby(df["RegionalUnit"]).count()
        st.write(reg_count)
        st.header("Sister Nurse status")
        df = df.rename(columns={"Nurse Name": "NurseName"})
        sister_count = df["NurseName"].groupby(df["NurseName"]).count()
        st.write(sister_count)
    except Exception as e:
        st.error(f"Error: {e}")

def download_file_by_date(start_date, end_date):
    """Download file using start_date and end_date."""
    url = f"https://champs.billionlives.in:8000/consultation_api/getCallLogsCSV?startdate={start_date}&enddate={end_date}"
    response = requests.get(url)

    if response.status_code == 200:
        csv_file_path = "dataset.csv"
        with open("dataset.csv", "wb") as file:
            file.write(response.content)
        st.success("File downloaded successfully as dataset.csv!")
        export_to_sql()
        if sqlite_to_excel():
            st.success("File downloaded and exported to Excel successfully!")
    else:
        st.error(f"Failed to download file. Status code: {response.status_code}")

def csv_to_excel():
    file_path = "dailyCalls.xlsx"
    if os.path.exists(file_path):
        df1 = pd.read_excel(file_path)
        df2 = pd.read_csv(csvfile)
        df2["Date"] = today.strftime("%m-%d-%Y")
        combined_data = pd.concat([df1, df2], ignore_index=True)
        combined_data.to_excel(file_path, index=False)
        st.success("Data appended successfully to Excel!")
    else:
        df2 = pd.read_csv(csvfile)
        df2["Date"] = today.strftime("%m-%d-%Y")
        with pd.ExcelWriter(file_path, engine='openpyxl') as new_excel:
            df2.to_excel(new_excel, index=False)
        st.success("New Excel file created successfully!")

def csv_to_sqlite():
    conn = get_connection()  # Get connection in the current thread
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
        st.success(f"Data exported to {excel_file_path}")
    except Exception as e:
        st.error(f"Error: {e}")
    finally:
        # Always close the connection
        conn.close()

def sql_to_excel_datewise(start_date, end_date):
    query = f"SELECT * FROM daily_calls WHERE date >= '{start_date}' AND date <= '{end_date}';"
    df = pd.read_sql_query(query, conn)
    excel_file_path = f'calls_{start_date}_{end_date}.xlsx'
    df.to_excel(excel_file_path, index=False)
    st.success(f"Data exported to {excel_file_path}")



def export_csv_sql(df):
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%d-%m').dt.strftime('%Y-%d-%m')

    # Add new columns for day, month, and year
    df['day'] = pd.to_datetime(df['Date']).dt.day
    df['month'] = pd.to_datetime(df['Date']).dt.strftime('%B')  # Month name
    df['year'] = pd.to_datetime(df['Date']).dt.year

    # Write the DataFrame to the SQLite database
    conn = sqlite3.connect('chai.db')  # Ensure connection is created in the current thread
    try:
        df.to_sql("daily_calls", conn, if_exists='append', index=False)
        conn.commit()
        st.write(f"{len(df)} Data exported successfully!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

def uploaded_file():
    st.title("Upload File")

    # File upload
    uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx"])

    if uploaded_file is not None:
        # Show the uploaded file name
        st.success(f"Uploaded file: {uploaded_file.name}")

        # Process CSV or Excel file
        if uploaded_file.name.endswith(".csv"):
            df1 = pd.read_csv(uploaded_file)
            #st.write(df1["Date"].unique())
            df1['Date'] = pd.to_datetime(df1['Date'], format='%m-%d-%Y')
            df1['Date'] = df1['Date'].dt.strftime('%Y-%d-%m')
            export_csv_sql(df1)
        elif uploaded_file.name.endswith(".xlsx"):
            df1 = pd.read_excel(uploaded_file)
            st.write(df1["Date"].unique())
            df1['Date'] = pd.to_datetime(df1['Date'], format='%d-%m-%Y')
            df1['Date'] = df1['Date'].dt.strftime('%Y-%d-%m')
            export_csv_sql(df1)
            sqlite_to_excel()
            
        # Display the uploaded DataFrame
        
        st.write("Preview of Uploaded File:")
        st.write(df1.head())

def export_csv_sqlS(df):
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d').dt.strftime('%Y-%m-%d')

    # Add new columns for day, month, and year
    df['day'] = pd.to_datetime(df['Date']).dt.day
    df['month'] = pd.to_datetime(df['Date']).dt.strftime('%B')  # Month name
    df['year'] = pd.to_datetime(df['Date']).dt.year

    # Write the DataFrame to the SQLite database
    conn = sqlite3.connect('chai.db')  # Ensure connection is created in the current thread
    try:
        df.to_sql("daily_calls", conn, if_exists='append', index=False)
        conn.commit()
        st.write(f"{len(df)} Data exported successfully!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

def uploaded_fileS():
    st.title("Upload File")

    # File upload
    uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx"])

    if uploaded_file is not None:
        # Show the uploaded file name
        st.success(f"Uploaded file: {uploaded_file.name}")

        # Process CSV or Excel file
        if uploaded_file.name.endswith(".csv"):
            df1 = pd.read_csv(uploaded_file)
            #st.write(df1["Date"].unique())
            df1['Date'] = pd.to_datetime(df1['Date'], format='%m-%d-%Y')
            df1['Date'] = df1['Date'].dt.strftime('%Y-%d-%m')
            export_csv_sqlS(df1)
        elif uploaded_file.name.endswith(".xlsx"):
            df1 = pd.read_excel(uploaded_file)
            st.write(df1["Date"].unique())
            df1['Date'] = pd.to_datetime(df1['Date'], format='%m/%d/%Y')
            df1['Date'] = df1['Date'].dt.strftime('%Y-%m-%d')
            export_csv_sqlS(df1)
            sqlite_to_excel()
       
        # Display the uploaded DataFrame
        
        st.write("Preview of Uploaded File:")
        st.write(df1.head())
def export_to_sql():
    # Read the CSV file
    df = pd.read_csv(csvfile)
    n=len(df)

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
        st.write(f"{n} Datas exported successfully!")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

def execute_and_export(q):
    conn = sqlite3.connect("chai.db")
    c = conn.cursor()
    try:
        # Execute the query
        c.execute(q)
        conn.commit()
        st.success("Command Executed Successfully!")
        
        # Fetch the results of the executed query
        df = pd.read_sql_query("SELECT * FROM daily_calls;", conn)  # Adjust table name if needed
        
        # Export the results to an Excel file
        excel_file_path = "output_excel_file.xlsx"
        df.to_excel(excel_file_path, index=False)
        st.success(f"Data exported to {excel_file_path} successfully!")
    except Exception as e:
        st.error(f"Error: {e}")
    finally:
        conn.close()

def active_sisters_filter():
        # Connect to the database
    conn = sqlite3.connect('chai.db')  # Update with your database connection

    # Initial query to fetch all data
    q2 = "SELECT * FROM daily_calls"
    df = pd.read_sql_query(q2, conn)

    # Get unique regional units and add "ALL" at the beginning
    reg = df['RegionalUnit'].unique().tolist()
    reg.insert(0, "ALL")
    ru = st.sidebar.selectbox("Select Regional Unit", reg)

    # Year selection
    y = st.sidebar.selectbox("Select Year", ["select", "2022", "2023", "2024", "2025", "2026"])
    st.write(f"Selected Year: {y}")

    # Month selection
    m1 = ["select", "January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]
    sm = st.sidebar.selectbox("Select Month", m1)

    # Query based on the Regional Unit selection
    if ru == "ALL":
        q2 = "SELECT * FROM daily_calls"
    else:
        q2 = f"SELECT * FROM daily_calls WHERE RegionalUnit = '{ru}'"
    
    # Fetch data from the database again based on the selected regional unit
    df = pd.read_sql_query(q2, conn)

    # Filter by selected year
    if y != "select":
        if "year" in df.columns:
            df = df[df["year"] == int(y)]
        else:
            st.write("The 'year' column is missing from the data.")
            conn.close()
            return  # Exit if the year column is missing

    # Filter by selected month
    if sm != "select":
        df = df[df['month'] == sm]
    
    # Display results
    st.title("Active Sisters")
    active_sisters = df['Nurse Name'].unique()
    st.header(f"Total Active Sisters: {len(active_sisters)}")
    
    df = df.rename(columns={"Nurse Name": "NurseName"})
    st.header(f"Total No. of Calls: {len(df)}")
    
    # Count calls per sister
    sister_count = df["NurseName"].value_counts()
    st.write(sister_count)

    # Create a bar chart for the top 10 sisters with the most calls
    top_sisters = sister_count.head(10)
    fig = px.bar(top_sisters.reset_index(),
                 x='index',
                 y='NurseName',
                 labels={'index': 'Sister Name', 'NurseName': 'Number of Calls'},
                 title='Top 10 Sisters with Most Calls')
    fig.update_traces(texttemplate='%{y}', textposition='outside')
    st.plotly_chart(fig)

    # Close the database connection
    conn.close()
   

def doctor_wise_records_filter():
    conn = sqlite3.connect('chai.db')  # Update with your database connection
    y = st.sidebar.selectbox("Select Year", ["select", "2022", "2023", "2024", "2025", "2026"])
    st.write(f"Selected Year: {y}")
    m1 = ["select", "January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]
    sm = st.sidebar.selectbox("Select Month", m1)
    # Query to fetch doctor-wise records
    q2 = "SELECT * FROM daily_calls"
    # Fetch data from the database
    df = pd.read_sql_query(q2, conn)
    # Filter by year
    if y != "select":
        if "year" in df.columns:
            df = df[df["year"] == int(y)]
        else:
            st.write("The 'year' column is missing from the data.")
    else:
        st.write("Please select a valid year.")
        st.title("Doctor-wise Records")
        # Extract and display unique doctors
    unique_doctors = df['doctorName'].unique()
    st.header(f"Total Unique Doctors: {len(unique_doctors)}")
    # Rename columns for consistency
    df = df.rename(columns={"doctorName": "doctorName"})
    # Count records for each doctor
    doctor_count = df["doctorName"].groupby(df["doctorName"]).count()
    st.header(f"Total No. of Calls: {len(df)}")
    st.write(doctor_count)
    conn.close()

    # Filter by month
    if sm!="select":
        df = df[df['month'] == sm]

def regional_wise_filter():
    conn = sqlite3.connect('chai.db')  # Update with your database connection
    q2 = "SELECT * FROM daily_calls"
    df = pd.read_sql_query(q2, conn)
    
    # Extract unique regional units
    reg = df['RegionalUnit'].unique()
    reg = ["All"] + list(reg)  # Add "All" option
    ru = st.sidebar.selectbox("Select Regional Unit", reg)
    y = st.sidebar.selectbox("Select Year", ["select", "2022", "2023", "2024", "2025", "2026"])
    st.write(f"Selected Year: {y}")
    
    m1 = ["select", "January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]
    sm = st.sidebar.selectbox("Select Month", m1)
    
    # Fetch all data first to get unique regional units
    
    
    # Filter by regional unit
    if ru != "All":
        df = df[df['RegionalUnit'] == ru]
    
    # Filter by year
    if y != "select":
        if "year" in df.columns:
            df = df[df["year"] == int(y)]
        else:
            st.write("The 'year' column is missing from the data.")
            conn.close()
            return  # Exit if the year column is missing
    else:
        st.write("Please select a valid year.")
        conn.close()
        return  # Exit if no valid year is selected
    
    # Filter by month
    if sm != "select":
        df = df[df['month'] == sm]
    
    st.title("Regional Wise Records")
    
    # Rename columns for consistency
    df = df.rename(columns={"RegionalUnit": "Regional Unit"})
    
    # Count records for each regional unit
    ru_count = df["Regional Unit"].value_counts()
    
    st.header(f"Total No. of Calls: {len(df)}")
    st.write(ru_count)
    fig = px.bar(ru_count.reset_index(), 
        x='index', 
        y='Regional Unit', 
        labels={'index': 'Regional Unit', 'Regional Unit': 'Number of Calls'},
        title='Number of Calls per Regional Unit')
    fig.update_traces(texttemplate='%{y}', textposition='outside')
    st.plotly_chart(fig)  # Display the chart
    conn.close()

def date_wise():
    conn = sqlite3.connect('chai.db')  # Update with your database connection
    
    # Allow the user to select a specific date
    selected_date = st.sidebar.date_input("Select a Date")
    st.write(f"Selected Date: {selected_date}")
    
    # Query to fetch all data
    q2 = "SELECT * FROM daily_calls"
    df = pd.read_sql_query(q2, conn)
    
    # Ensure the 'date' column exists and is properly formatted
    if "Date" in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
    else:
        st.write("The 'date' column is missing from the data.")
        conn.close()
        return  # Exit if the date column is missing
    
    # Filter by the selected date
    df = df[df['Date'].dt.date == selected_date]  # Use .dt.date to compare only the date part
    
    if df.empty:
        st.write("No data found for the selected date.")
        conn.close()
        return  # Exit if no data is found for the selected date
    
    st.title(f"Records for {selected_date}")
    
    # Active Sisters Analysis
    st.header("Active Sisters")
    active_sisters = df['Nurse Name'].unique()
    st.write(f"Total Active Sisters: {len(active_sisters)}")
    df = df.rename(columns={"Nurse Name": "NurseName"})
    st.header(f"Total No. of calls:{len(df)}")
    sister_count = df["NurseName"].value_counts()
    st.write(sister_count)
    
    # Doctor-Wise Analysis
    st.header("Doctor-Wise Records")
    if "doctorName" in df.columns:
        unique_doctors = df['doctorName'].unique()
        st.write(f"Total Unique Doctors: {len(unique_doctors)}")
        doctor_count = df['doctorName'].value_counts()
        st.write(doctor_count)
    else:
        st.write("The 'doctorName' column is missing from the data.")
    
    # Regional-Wise Analysis
    st.header("Regional-Wise Records")
    if "RegionalUnit" in df.columns:
        regional_unit_count = df["RegionalUnit"].value_counts()
        st.write(f"Total Calls by Regional Unit:")
        st.write(regional_unit_count)
        
        # Create a bar chart for Regional Units
        # fig = px.bar(regional_unit_count.reset_index(),
        #              x='index',
        #              y=regional_unit_count.values,
        #              labels={'index': 'Regional Unit', 'y': 'Number of Calls'},
        #              title='Number of Calls per Regional Unit')
        # fig.update_traces(texttemplate='%{y}', textposition='outside')
        # st.plotly_chart(fig)
    else:
        st.write("The 'RegionalUnit' column is missing from the data.")
    
def month_wise_filter():
        # Connect to the database
    conn = sqlite3.connect('chai.db')  # Update with your database connection

    # Initial query to fetch all data
    q2 = "SELECT * FROM daily_calls"
    df = pd.read_sql_query(q2, conn)

    # Get unique regional units and add "ALL" at the beginning
    reg = df['RegionalUnit'].unique().tolist()
    reg.insert(0, "ALL")
    ru = st.sidebar.selectbox("Select Regional Unit", reg)

    # Year selection
    y = st.sidebar.selectbox("Select Year", ["select", "2022", "2023", "2024", "2025", "2026"])
    st.write(f"Selected Year: {y}")

    # Month selection
    m1 = ["select", "January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]
    sm = st.sidebar.selectbox("Select Month", m1)

    # Query based on the Regional Unit selection
    if ru == "ALL":
        q2 = "SELECT * FROM daily_calls"
    else:
        q2 = f"SELECT * FROM daily_calls WHERE RegionalUnit = '{ru}'"
    
    # Fetch data from the database again based on the selected regional unit
    df = pd.read_sql_query(q2, conn)

    # Filter by selected year
    if y != "select":
        if "year" in df.columns:
            df = df[df["year"] == int(y)]
        else:
            st.write("The 'year' column is missing from the data.")
            conn.close()
            return  # Exit if the year column is missing

    # Filter by selected month
    if sm != "select":
        df = df[df['month'] == sm]

    # Display results
    st.title("Date wise call")
    active_sisters = df['month'].unique()
    #st.header(f"Total Active Sisters: {len(active_sisters)}")
    
    #df = df.rename(columns={"Nurse Name": "NurseName"})
    st.header(f"Total No. of Calls: {len(df)}")
    
    # Count calls per sister
    date_count = df["Date"].value_counts()
    st.write(date_count)

    # # Create a bar chart for the top 10 sisters with the most calls
    # top_sisters = sister_count.head(10)
    # fig = px.bar(top_sisters.reset_index(),
    #              x='index',
    #              y='NurseName',
    #              labels={'index': 'Sister Name', 'NurseName': 'Number of Calls'},
    #              title='Top 10 Sisters with Most Calls')
    # fig.update_traces(texttemplate='%{y}', textposition='outside')
    # st.plotly_chart(fig)

    # Close the database connection
    conn.close()
    conn.close()
# Streamlit UI
st.title("CHAI Data Management App")

menu = [
    "Download File",
    "Tracking",
    "Active Sisters",
    "Regional Unit Records",
    "Doctor's Records",
    "Date wise Records",
    "SQL Command",
    "CSV to Excel",
    "CSV to SQLite",
    "SQLite to Excel",
    "SQL to Excel by Date",
    "Upload File(-)",
    "Upload File(/)",
    "Export to SQL"

]
choice = st.sidebar.selectbox("Select an Option", menu)

if choice == "Download File":
    # # Button for downloading today's file
    # if st.button("Download Today's File"):
    #     download_file()

    # Inputs and button for date-wise download
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

elif choice == "CSV to Excel":
    st.button("Convert CSV to Excel", on_click=csv_to_excel)

elif choice == "Active Sisters":
    active_sisters_filter()
elif choice == "Date wise Records":
    month_wise_filter()
elif choice == "Doctor's Records":
    doctor_wise_records_filter()
elif choice == "Regional Unit Records":
    regional_wise_filter()
elif choice == "Tracking":
    tracking()
elif choice == "CSV to SQLite":
    #st.button("Insert CSV to SQLite", on_click=csv_to_sqlite)
    csv_to_sqlite()

elif choice == "SQLite to Excel":
    st.button("Export SQLite Data to Excel", on_click=sqlite_to_excel)

elif choice == "SQL Command":
    q = st.text_area(label="Type the necessary command needed", height=200, max_chars=500)
    b = st.button("Execute & Export")
    if b:
        execute_and_export(q)


elif choice == "SQL to Excel by Date":
    start_date = st.text_input("Enter Start Date (YYYY-MM-DD)")
    end_date = st.text_input("Enter End Date (YYYY-MM-DD)")
    if st.button("Export SQL Data"):
        sql_to_excel_datewise(start_date, end_date)
elif choice=="Upload File(-)":
    uploaded_file()
elif choice=="Upload File(/)":
    uploaded_fileS()
elif choice=="Export to SQL":
    export_to_sql()