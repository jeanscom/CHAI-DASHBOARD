import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime
from pathlib import Path
import tempfile

# Custom CSS
st.markdown("""
    <style>
        .main {
            padding: 0rem 1rem;
        }
        .stButton>button {
            width: 100%;
            border-radius: 5px;
            height: 2.5em;
        }
        .stTextInput>div>div>input {
            border-radius: 5px;
        }
        .stSelectbox>div>div>select {
            border-radius: 5px;
        }
        .stAlert {
            border-radius: 5px;
        }
    </style>
""", unsafe_allow_html=True)

def create_connection(db_path):
    """Create a database connection with error handling"""
    try:
        conn = sqlite3.connect(db_path)
        return conn, None
    except sqlite3.Error as e:
        return None, f"Error connecting to database: {str(e)}"

def get_db_tables(db_path):
    """Get all table names from the database"""
    conn, error = create_connection(db_path)
    if error:
        return [], error
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name 
            FROM sqlite_master 
            WHERE type='table'
            ORDER BY name;
        """)
        tables = [table[0] for table in cursor.fetchall()]
        return tables, None
    except sqlite3.Error as e:
        return [], f"Error getting tables: {str(e)}"
    finally:
        if conn:
            conn.close()

def get_table_info(db_path, table_name):
    """Get column information for a specific table"""
    conn, error = create_connection(db_path)
    if error:
        return None, None, error
    
    try:
        cursor = conn.cursor()
        # Safely format table name to prevent SQL injection
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            return None, None, f"Table '{table_name}' does not exist"
        
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
        sample_data = cursor.fetchone()
        
        return columns, sample_data, None
    except sqlite3.Error as e:
        return None, None, f"Error getting table info: {str(e)}"
    finally:
        if conn:
            conn.close()

def execute_sql_query(db_path, query):
    """Execute SQL query and return results as a pandas DataFrame"""
    conn, error = create_connection(db_path)
    if error:
        return None, error
    
    try:
        df = pd.read_sql_query(query, conn)
        return df, None
    except Exception as e:
        return None, str(e)
    finally:
        if conn:
            conn.close()

def alter_table(db_path, query):
    """Execute ALTER TABLE query"""
    conn, error = create_connection(db_path)
    if error:
        return error
    
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        return None
    except sqlite3.Error as e:
        return f"Error altering table: {str(e)}"
    finally:
        if conn:
            conn.close()

def insert_data(db_path, table_name, data):
    """Insert data into the specified table"""
    conn, error = create_connection(db_path)
    if error:
        return error
    
    try:
        cursor = conn.cursor()
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        cursor.execute(query, list(data.values()))
        conn.commit()
        return None
    except sqlite3.Error as e:
        return f"Error inserting data: {str(e)}"
    finally:
        if conn:
            conn.close()

def update_data(db_path, table_name, data, condition):
    """Update data in the specified table"""
    conn, error = create_connection(db_path)
    if error:
        return error
    
    try:
        cursor = conn.cursor()
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        where_clause = ' AND '.join([f"{k} = ?" for k in condition.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
        values = list(data.values()) + list(condition.values())
        cursor.execute(query, values)
        conn.commit()
        return None
    except sqlite3.Error as e:
        return f"Error updating data: {str(e)}"
    finally:
        if conn:
            conn.close()

def delete_data(db_path, table_name, condition):
    """Delete data from the specified table"""
    conn, error = create_connection(db_path)
    if error:
        return error
    
    try:
        cursor = conn.cursor()
        where_clause = ' AND '.join([f"{k} = ?" for k in condition.keys()])
        query = f"DELETE FROM {table_name} WHERE {where_clause}"
        cursor.execute(query, list(condition.values()))
        conn.commit()
        return None
    except sqlite3.Error as e:
        return f"Error deleting data: {str(e)}"
    finally:
        if conn:
            conn.close()

def search_data(db_path, table_name, search_columns, search_term):
    """Search for data in specified columns"""
    conn, error = create_connection(db_path)
    if error:
        return None, error
    
    try:
        cursor = conn.cursor()
        where_clause = ' OR '.join([f"{col} LIKE ?" for col in search_columns])
        query = f"SELECT * FROM {table_name} WHERE {where_clause}"
        params = [f"%{search_term}%" for _ in search_columns]
        df = pd.read_sql_query(query, conn, params=params)
        return df, None
    except sqlite3.Error as e:
        return None, f"Error searching data: {str(e)}"
    finally:
        if conn:
            conn.close()

def generate_sample_queries(table_name, columns):
    """Generate sample queries based on table structure"""
    queries = {
        " Select all": f"SELECT * FROM {table_name} LIMIT 1000",
        " Count records": f"SELECT COUNT(*) as total_records FROM {table_name}",
        " Basic statistics": f"SELECT COUNT(*) as count, COUNT(DISTINCT *) as unique_count FROM {table_name}"
    }
    
    # Add sample queries for each column type
    for col in columns:
        col_name = col[1]
        col_type = col[2].lower()
        
        if 'int' in col_type or 'float' in col_type or 'real' in col_type:
            queries[f" Stats for {col_name}"] = f"""
                SELECT 
                    COUNT({col_name}) as count,
                    AVG({col_name}) as average,
                    MIN({col_name}) as minimum,
                    MAX({col_name}) as maximum
                FROM {table_name}
                WHERE {col_name} IS NOT NULL
            """
        elif 'text' in col_type or 'char' in col_type:
            queries[f" Distinct {col_name}"] = f"""
                SELECT DISTINCT {col_name}, COUNT(*) as count
                FROM {table_name}
                WHERE {col_name} IS NOT NULL
                GROUP BY {col_name}
                ORDER BY count DESC
                LIMIT 10
            """
        elif 'date' in col_type or 'time' in col_type:
            queries[f" Date analysis of {col_name}"] = f"""
                SELECT 
                    date({col_name}) as date,
                    COUNT(*) as count
                FROM {table_name}
                WHERE {col_name} IS NOT NULL
                GROUP BY date({col_name})
                ORDER BY date DESC
                LIMIT 10
            """
    
    return queries

def db_command():
    # Custom header
    st.markdown('<h1 class="custom-header">🔍 SQL Database Explorer Pro</h1>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'temp_db_path' not in st.session_state:
        st.session_state.temp_db_path = None
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = None
    
    # Sidebar
    with st.sidebar:
        st.markdown("""
            <div style="padding: 1rem;">
                <h2>📁 Database Connection</h2>
            </div>
        """, unsafe_allow_html=True)
        
        db_method = st.radio(
            "Choose database source:",
            ["Upload Database", "Use Existing Database"],
            horizontal=True
        )
        
        db_path = None
        
        if db_method == "Upload Database":
            uploaded_file = st.file_uploader(
                "📤 Choose a SQLite database file",
                type=['db', 'sqlite', 'sqlite3']
            )
            
            if uploaded_file:
                if st.session_state.temp_db_path:
                    try:
                        os.remove(st.session_state.temp_db_path)
                    except:
                        pass
                
                temp_dir = tempfile.mkdtemp()
                temp_path = os.path.join(temp_dir, "temp_db.db")
                
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                
                st.session_state.temp_db_path = temp_path
                db_path = temp_path
                st.success("✅ Database uploaded successfully!")
        else:
            db_files = [f for f in os.listdir() if f.endswith(('.db', '.sqlite', '.sqlite3'))]
            if db_files:
                selected_db = st.selectbox(
                    "💾 Select existing database:",
                    db_files
                )
                if selected_db:
                    db_path = selected_db
                    st.success("✅ Database connected successfully!")
            else:
                st.warning("⚠️ No database files found!")
    
    if db_path:
        tables, error = get_db_tables(db_path)
        
        if error:
            st.error(f"❌ {error}")
            return
        
        if not tables:
            st.warning("⚠️ No tables found in the database!")
            return
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("### 📋 Database Structure")
            selected_table = st.selectbox(
                "📊 Select a table:",
                tables
            )
            
            if selected_table:
                columns, sample_data, error = get_table_info(db_path, selected_table)
                
                if error:
                    st.error(f"❌ {error}")
                    return
                
                st.write("📝 Table Schema:")
                schema_df = pd.DataFrame(
                    columns,
                    columns=['ID', 'Name', 'Type', 'NotNull', 'DefaultValue', 'PK']
                )
                st.dataframe(schema_df, height=200)
                
                # Data Operations Section
                st.markdown("### 🛠️ Data Operations")
                operation = st.radio(
                    "Select Operation:",
                    ["🔍 Search & View", "➕ Insert", "✏️ Update", "❌ Delete", "🔧 Alter Table"],
                    horizontal=True
                )
                
                if operation == "🔍 Search & View":
                    search_cols = st.multiselect(
                        "🎯 Select columns to search in:",
                        [col[1] for col in columns]
                    )
                    
                    search_term = st.text_input("🔍 Search term:")
                    
                    if st.button("🔎 Search", type="primary"):
                        if search_cols and search_term:
                            results, error = search_data(db_path, selected_table, search_cols, search_term)
                            if error:
                                st.error(f"❌ {error}")
                            else:
                                st.write("📊 Search Results:")
                                st.dataframe(results)
                                
                                if not results.empty:
                                    csv = results.to_csv(index=False)
                                    st.download_button(
                                        "📥 Download Results (CSV)",
                                        csv,
                                        f"search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                        "text/csv"
                                    )
                
                elif operation == "➕ Insert":
                    st.write("📝 Insert New Record")
                    insert_data_dict = {}
                    
                    for col in columns:
                        col_name = col[1]
                        col_type = col[2].lower()
                        
                        if col[4]:  # Skip if default value exists
                            continue
                            
                        if 'int' in col_type:
                            value = st.number_input(f"Enter {col_name}:", key=f"insert_{col_name}")
                        elif 'real' in col_type or 'float' in col_type:
                            value = st.number_input(f"Enter {col_name}:", float(0), key=f"insert_{col_name}")
                        else:
                            value = st.text_input(f"Enter {col_name}:", key=f"insert_{col_name}")
                        
                        if value or col[3]:  # Include if value provided or NotNull
                            insert_data_dict[col_name] = value
                    
                    if st.button("📈 Insert Record", type="primary"):
                        error = insert_data(db_path, selected_table, insert_data_dict)
                        if error:
                            st.error(f"❌ {error}")
                        else:
                            st.success("✅ Record inserted successfully!")
                
                elif operation == "✏️ Update":
                    st.write("📝 Update Records")
                    
                    # First search for records
                    search_cols = st.multiselect(
                        "🎯 Select columns to search in:",
                        [col[1] for col in columns]
                    )
                    
                    search_term = st.text_input("🔍 Search for records to update:")
                    
                    if search_cols and search_term:
                        results, error = search_data(db_path, selected_table, search_cols, search_term)
                        if error:
                            st.error(f"❌ {error}")
                        elif not results.empty:
                            st.write("📊 Matching Records:")
                            st.dataframe(results)
                            
                            # Update form
                            st.write("📝 Enter new values:")
                            update_data_dict = {}
                            condition_dict = {}
                            
                            # Select condition column
                            condition_col = st.selectbox(
                                "🔑 Select column to identify record(s):",
                                [col[1] for col in columns]
                            )
                            condition_value = st.text_input(f"Enter {condition_col} value to update:")
                            
                            if condition_value:
                                condition_dict[condition_col] = condition_value
                                
                                # Update values
                                for col in columns:
                                    col_name = col[1]
                                    if st.checkbox(f"Update {col_name}?"):
                                        if 'int' in col[2].lower():
                                            value = st.number_input(f"New value for {col_name}:", key=f"update_{col_name}")
                                        elif 'real' in col[2].lower() or 'float' in col[2].lower():
                                            value = st.number_input(f"New value for {col_name}:", float(0), key=f"update_{col_name}")
                                        else:
                                            value = st.text_input(f"New value for {col_name}:", key=f"update_{col_name}")
                                        
                                        if value:
                                            update_data_dict[col_name] = value
                                
                                if update_data_dict and st.button("🔄 Update Records", type="primary"):
                                    error = update_data(db_path, selected_table, update_data_dict, condition_dict)
                                    if error:
                                        st.error(f"❌ {error}")
                                    else:
                                        st.success("✅ Records updated successfully!")
                
                elif operation == "❌ Delete":
                    st.write("🚮 Delete Records")
                    
                    # First search for records
                    search_cols = st.multiselect(
                        "🎯 Select columns to search in:",
                        [col[1] for col in columns]
                    )
                    
                    search_term = st.text_input("🔍 Search for records to delete:")
                    
                    if search_cols and search_term:
                        results, error = search_data(db_path, selected_table, search_cols, search_term)
                        if error:
                            st.error(f"❌ {error}")
                        elif not results.empty:
                            st.write("📊 Matching Records:")
                            st.dataframe(results)
                            
                            # Delete confirmation
                            condition_col = st.selectbox(
                                "🔑 Select column to identify record(s) to delete:",
                                [col[1] for col in columns]
                            )
                            condition_value = st.text_input(f"Enter {condition_col} value to delete:")
                            
                            if condition_value:
                                condition_dict = {condition_col: condition_value}
                                
                                confirm_delete = st.checkbox("🚨 I understand this action cannot be undone")
                                if confirm_delete:
                                    if st.button("🚮 Delete Records", type="primary"):
                                        error = delete_data(db_path, selected_table, condition_dict)
                                        if error:
                                            st.error(f"❌ {error}")
                                        else:
                                            st.success("✅ Records deleted successfully!")
                                            st.rerun()
                
                elif operation == "🔧 Alter Table":
                    st.write("🔧 Modify Table Structure")
                    alter_type = st.selectbox(
                        "🔧 Select ALTER operation:",
                        ["Add Column", "Drop Column", "Rename Table", "Rename Column", "Modify Column", "Custom ALTER Query"]
                    )
                    
                    if alter_type == "Add Column":
                        new_col_name = st.text_input("📝 New Column Name:")
                        
                        # Check if column already exists
                        existing_columns = [col[1].upper() for col in columns]  # Case-insensitive comparison
                        if new_col_name and new_col_name.upper() in existing_columns:
                            st.error(f"🚫 Column '{new_col_name}' already exists in the table!")
                        else:
                            new_col_type = st.selectbox(
                                "📝 Column Type:",
                                ["TEXT", "INTEGER", "REAL", "BLOB", "NUMERIC", "DATE", "DATETIME", "BOOLEAN"]
                            )
                            nullable = st.checkbox("🔓 Allow NULL values", value=True)
                            default_value = st.text_input("📝 Default Value (optional):")
                            
                            if st.button("📈 Add Column", type="primary"):
                                if not new_col_name:
                                    st.error("🚫 Please enter a column name!")
                                else:
                                    query = f"ALTER TABLE {selected_table} ADD COLUMN {new_col_name} {new_col_type}"
                                    if not nullable:
                                        query += " NOT NULL"
                                    if default_value:
                                        query += f" DEFAULT {default_value}"
                                    
                                    error = alter_table(db_path, query)
                                    if error:
                                        if "duplicate column name" in error.lower():
                                            st.error(f"🚫 Column '{new_col_name}' already exists in the table!")
                                        else:
                                            st.error(f"❌ {error}")
                                    else:
                                        st.success(f"✅ Column '{new_col_name}' added successfully!")
                                        st.rerun()
                    
                    elif alter_type == "Drop Column":
                        # Get existing columns
                        columns_info = [col[1] for col in columns]
                        col_to_drop = st.selectbox("🔑 Select column to drop:", columns_info)
                        
                        confirm_drop = st.checkbox("🚨 I understand this action cannot be undone")
                        if confirm_drop:
                            if st.button("🚮 Drop Column", type="primary"):
                                try:
                                    conn = sqlite3.connect(db_path)
                                    cursor = conn.cursor()
                                    
                                    # Get all columns except the one to drop
                                    cursor.execute(f"PRAGMA table_info({selected_table})")
                                    all_columns = [col[1] for col in cursor.fetchall() if col[1] != col_to_drop]
                                    columns_str = ", ".join(all_columns)
                                    
                                    # Create new table without the column
                                    cursor.execute(f"""
                                        CREATE TABLE {selected_table}_temp AS 
                                        SELECT {columns_str}
                                        FROM {selected_table}
                                    """)
                                    
                                    # Drop old table
                                    cursor.execute(f"DROP TABLE {selected_table}")
                                    
                                    # Rename temp table to original
                                    cursor.execute(f"ALTER TABLE {selected_table}_temp RENAME TO {selected_table}")
                                    
                                    conn.commit()
                                    conn.close()
                                    
                                    st.success(f"✅ Column '{col_to_drop}' dropped successfully!")
                                    st.rerun()
                                except sqlite3.Error as e:
                                    st.error(f"❌ Error dropping column: {str(e)}")
                    
                    elif alter_type == "Rename Table":
                        new_table_name = st.text_input("📝 New Table Name:")
                        if st.button("🔄 Rename Table", type="primary"):
                            query = f"ALTER TABLE {selected_table} RENAME TO {new_table_name}"
                            error = alter_table(db_path, query)
                            if error:
                                st.error(f"❌ {error}")
                            else:
                                st.success(f"✅ Table renamed to '{new_table_name}' successfully!")
                                st.rerun()
                    
                    elif alter_type == "Rename Column":
                        # Get existing columns
                        columns_info = [col[1] for col in columns]
                        col_to_rename = st.selectbox("🔑 Select column to rename:", columns_info)
                        new_col_name = st.text_input("📝 New Column Name:")
                        
                        if st.button("🔄 Rename Column", type="primary"):
                            try:
                                conn = sqlite3.connect(db_path)
                                cursor = conn.cursor()
                                
                                # Create new table with renamed column
                                cursor.execute(f"PRAGMA table_info({selected_table})")
                                old_columns = cursor.fetchall()
                                new_columns = [f"{col[1]} AS {new_col_name}" if col[1] == col_to_rename else col[1] 
                                            for col in old_columns]
                                columns_str = ", ".join(new_columns)
                                
                                cursor.execute(f"""
                                    CREATE TABLE {selected_table}_temp AS 
                                    SELECT {columns_str}
                                    FROM {selected_table}
                                """)
                                
                                # Drop old table
                                cursor.execute(f"DROP TABLE {selected_table}")
                                
                                # Rename temp table to original
                                cursor.execute(f"ALTER TABLE {selected_table}_temp RENAME TO {selected_table}")
                                
                                conn.commit()
                                conn.close()
                                
                                st.success(f"✅ Column renamed from '{col_to_rename}' to '{new_col_name}' successfully!")
                                st.rerun()
                            except sqlite3.Error as e:
                                st.error(f"❌ Error renaming column: {str(e)}")
                    
                    elif alter_type == "Modify Column":
                        st.warning("🚨 SQLite does not support directly modifying column types. You'll need to:")
                        st.write("1. Create a new column with the desired type")
                        st.write("2. Copy data to the new column")
                        st.write("3. Drop the old column")
                        st.write("4. Rename the new column")
                        
                        # Get existing columns
                        columns_info = [col[1] for col in columns]
                        col_to_modify = st.selectbox("🔑 Select column to modify:", columns_info)
                        new_type = st.selectbox(
                            "📝 New Column Type:",
                            ["TEXT", "INTEGER", "REAL", "BLOB", "NUMERIC", "DATE", "DATETIME", "BOOLEAN"]
                        )
                        
                        if st.button("🔄 Modify Column", type="primary"):
                            try:
                                conn = sqlite3.connect(db_path)
                                cursor = conn.cursor()
                                
                                # Add new column
                                temp_col_name = f"{col_to_modify}_new"
                                cursor.execute(f"ALTER TABLE {selected_table} ADD COLUMN {temp_col_name} {new_type}")
                                
                                # Copy data with type conversion
                                cursor.execute(f"UPDATE {selected_table} SET {temp_col_name} = CAST({col_to_modify} AS {new_type})")
                                
                                # Create new table without old column
                                cursor.execute(f"PRAGMA table_info({selected_table})")
                                all_columns = cursor.fetchall()
                                new_columns = [col[1] if col[1] != col_to_modify else temp_col_name 
                                            for col in all_columns if col[1] != col_to_modify]
                                columns_str = ", ".join(new_columns)
                                
                                cursor.execute(f"""
                                    CREATE TABLE {selected_table}_temp AS 
                                    SELECT {columns_str}
                                    FROM {selected_table}
                                """)
                                
                                # Drop old table
                                cursor.execute(f"DROP TABLE {selected_table}")
                                
                                # Rename temp table to original
                                cursor.execute(f"ALTER TABLE {selected_table}_temp RENAME TO {selected_table}")
                                
                                conn.commit()
                                conn.close()
                                
                                st.success(f"✅ Column '{col_to_modify}' modified to type {new_type} successfully!")
                                st.rerun()
                            except sqlite3.Error as e:
                                st.error(f"❌ Error modifying column: {str(e)}")
                    
                    else:  # Custom ALTER Query
                        custom_query = st.text_area(
                            "📝 Enter ALTER TABLE query:",
                            value=f"ALTER TABLE {selected_table} ADD COLUMN column_name TEXT"
                        )
                        if st.button("🔄 Execute ALTER", type="primary"):
                            error = alter_table(db_path, custom_query)
                            if error:
                                st.error(f"❌ {error}")
                            else:
                                st.success("✅ Table altered successfully!")
                                st.rerun()
        
        with col2:
            st.markdown("""
                <div style="padding: 1rem;">
                    <h3>📝 Query Editor</h3>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown('<div class="css-card">', unsafe_allow_html=True)
            # Generate sample queries
            if selected_table:
                queries = generate_sample_queries(selected_table, columns)
                
                # Query templates
                st.write("📝 Query Templates:")
                selected_query = st.selectbox(
                    "🔍 Choose a template or write your own query:",
                    list(queries.keys())
                )
                
                # Query editor
                query = st.text_area(
                    "📝 SQL Query:",
                    value=queries[selected_query] if selected_query else "",
                    height=150
                )
                
                if st.button("🔄 Execute Query", type="primary"):
                    if query.strip():
                        with st.spinner("🔄 Executing query..."):
                            results, error = execute_sql_query(db_path, query)
                            
                            if error:
                                st.error(f"❌ Query Error: {error}")
                            else:
                                st.success("✅ Query executed successfully!")
                                st.write("📊 Results:")
                                st.dataframe(results)
                                
                                # Download results
                                if not results.empty:
                                    csv = results.to_csv(index=False)
                                    st.download_button(
                                        "📥 Download Results (CSV)",
                                        csv,
                                        f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                        "text/csv"
                                    )
                    else:
                        st.warning("🚨 Please enter a SQL query")
            st.markdown('</div>', unsafe_allow_html=True)

