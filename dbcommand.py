import sqlite3
import pandas as pd
import streamlit as st
import os


def get_tables(db_name):
    try:
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in c.fetchall()]
        conn.close()
        return tables
    except Exception as e:
        st.error(f"Error fetching tables: {e}")
        return []

def get_table_info(db_name, table_name):
    try:
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        c.execute(f"PRAGMA table_info({table_name});")
        structure = c.fetchall()
        c.execute(f"SELECT COUNT(*) FROM {table_name};")
        record_count = c.fetchone()[0]
        conn.close()
        return structure, record_count
    except Exception as e:
        st.error(f"Error fetching table info: {e}")
        return [], 0

def execute_and_export(q, db_name, table_name):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    try:
        # Execute the query
        c.execute(q)
        conn.commit()
        st.success("Command Executed Successfully!")
        
        # Fetch the results of the executed query
        df = pd.read_sql_query(f"SELECT * FROM {table_name};", conn)  

    except Exception as e:
        st.error(f"Error: {e}")
    finally:
        conn.close()

# Streamlit UI
def query_executor():
    st.header("SQL Query Executor")
    col1, col2 = st.columns(2)
    with col1:
    # Select database file
        db_files = [f for f in os.listdir() if f.endswith(".db")]
        db_name = st.selectbox("Select Database", db_files)
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        # Get tables from the selected database
        if db_name:
            tables = get_tables(db_name)
            if tables:
                table_name = st.selectbox("Select Table", tables)
                if table_name:
                    structure, record_count = get_table_info(db_name, table_name)
                    st.subheader("Table Structure")
                    if structure:
                        structure_df = pd.DataFrame(structure, columns=["Column ID", "Name", "Type", "Not Null", "Default Value", "Primary Key"])
                        st.dataframe(structure_df)
                    else:
                        st.write("No structure available.")                    
                st.subheader("Number of Records")
                st.write(record_count)
                q=f"select * from {table_name}"
                df=pd.read_sql_query(q,conn)
                csv_data=df.to_csv(index=False)
                st.download_button(
                    label="Download Table Data",
                    data=csv_data,
                    file_name=f"{table_name}.csv",
                    mime="text/csv"
                ) 
        else:
            st.error("No tables found in the database.")

    # User input for query
    with col2:
        
        query = st.text_area("Enter SQL Query")

        # Execute button
        if st.button("Execute"):
            if db_name and table_name and query.strip():
                if not query.startswith('select'):
                    execute_and_export(query, db_name, table_name)
                else:
                    df=pd.read_sql_query(query,conn)
                    csv_data=df.to_csv(index=False)
                    st.download_button(
                        label="Download Output Data",
                        data=csv_data,
                        file_name="output.csv",
                        mime="text/csv"
                    ) 
            else:
                st.error("Please select a database, table, and enter a valid query.")