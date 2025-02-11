import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import calendar
import io 


def dashboard(reg):
    # Set page title
    st.header("Consultation Dashboard")

    # Create date input widgets in sidebar
    with st.sidebar:
        st.header("Date Range")
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

    # Function to get consultation data
    def get_consultation_data(start_date, end_date):
        conn = sqlite3.connect("chai.db")
        try:
            query = f"""
            SELECT *
            FROM daily_calls
            WHERE date BETWEEN '{start_date}' AND '{end_date}'  and RegionalUnit=?
            """
           
            df = pd.read_sql_query(query, conn, params=(reg,))
            return df
        finally:
            conn.close()

    # Get data based on date range
    if start_date_str and end_date_str:
        try:
            # Get the consultation data for the selected date range
            df = get_consultation_data(start_date_str, end_date_str)
            
            if not df.empty:
                # Extract the unique months from the dataframe
                df['month_num'] = pd.to_datetime(df['Date']).dt.month  # Extract month number
                df['month_name'] = df['month_num'].apply(lambda x: calendar.month_name[x])  # Convert to month name
                months_available = df['month_name'].unique().tolist()

                # Sidebar for selecting months and nurses
                with st.sidebar:
                    st.header("Filter by Month")
                    selected_months = st.multiselect("Select Months", options=months_available)
                    filtered_df = df[df['month_name'].isin(selected_months)]

                    st.header("Filter by Region")
                    all_regions = sorted(df['RegionalUnit'].unique().tolist())
                    selected_regions = st.multiselect("Select Regions", options=all_regions)

                    st.header("Filter by Active Sister")
                    all_nurses = sorted(filtered_df['Nurse Name'].unique().tolist())
                    selected_nurses = st.multiselect("Select Nurses", options=all_nurses)

                    st.header("Filter by Date")
                    selected_dates = st.multiselect("Select Dates", options=filtered_df['Date'].unique().tolist())
                
                # Display total consultations
                total_consultations = len(filtered_df)
                st.header(f"Total Consultations: {total_consultations}")
                active_sisters = filtered_df['Nurse Name'].unique()
                st.subheader(f"Total Active Sisters: {len(active_sisters)}")
                # Download button for complete data
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                        label="Get Data",
                        data=csv,
                        file_name=f'consultations_{start_date_str}_to_{end_date_str}.csv',
                        mime='text/csv'
                    )

                # Handle Month filtering
                if selected_months:
                    # Filter by selected months
                    filtered_df = df[df['month_name'].isin(selected_months)]
                    month_counts = filtered_df['month_name'].value_counts()

                    # Sort the months in chronological order
                    month_counts = month_counts.reindex([m for m in calendar.month_name[1:] if m in month_counts.index])

                    # Create two columns for the analyses
                    col1, col3 = st.columns([2,2])

                    # Month-wise Analysis in first column
                    with col1:
                        st.subheader("Month-wise Analysis")
                        fig1, ax1 = plt.subplots(figsize=(10, 6))  # Adjusted figure size for better visibility
                        # Changed to horizontal bar plot by swapping x and y
                        sns.barplot(y=month_counts.index, x=month_counts.values, ax=ax1)
                        plt.xticks(rotation=0)  # No need to rotate x-axis labels anymore
                        ax1.set_xlabel("Consultations Count")
                        ax1.set_ylabel("Month")
                        ax1.set_title("Consultations by Month")
                        
                        # Add data labels to the bars
                        ax1.bar_label(ax1.containers[0], labels=[f'{v}' for v in month_counts.values], padding=3)
                        st.pyplot(fig1)
                        img_bytes = io.BytesIO()
                        fig1.savefig(img_bytes, format='png')
                        img_bytes.seek(0)  # Move to the beginning of the BytesIO object

                        # Create columns for download buttons
                        dl_col1, dl_col2 = st.columns(2)
                        
                        # Download graph button in first column
                        with dl_col1:
                            st.download_button(
                                label="Download Graph",
                                data=img_bytes,
                                file_name="month_wise_analysis.png",
                                mime="image/png"
                            )
                        
                        # Download data button in second column
                        with dl_col2:
                            csv = month_counts.to_csv(index=True)
                            st.download_button(
                                label="Download Data",
                                data=csv,
                                file_name=f'month_wise_data.csv',
                                mime='text/csv'
                            )

                        with st.expander("Click to view month wise data"):
                            st.write(month_counts)

                    # Nurse Analysis Section
                    if selected_nurses:
                        nurse_df = filtered_df[filtered_df['Nurse Name'].isin(selected_nurses)]
                    else:
                        nurse_df = filtered_df  # If no specific nurses are selected, use the entire filtered dataset

                    # Filter nurse data by region if selected regions are present
                    if selected_regions:
                        nurse_df = nurse_df[nurse_df['RegionalUnit'].isin(selected_regions)]  # Filter nurses based on selected region(s)

                    nurse_monthly = pd.pivot_table(
                        nurse_df,
                        values='Date',
                        index='Nurse Name',
                        columns='month_name',
                        aggfunc='count',
                        fill_value=0
                    ).round(0)

                    nurse_monthly['Total'] = nurse_monthly.sum(axis=1)
                    nurse_monthly = nurse_monthly.sort_values('Total', ascending=False)

                    with col3:
                        st.subheader("Active Sister Analysis")
                        # Get all nurse counts and top 10 for display
                        all_nurse_counts = nurse_df['Nurse Name'].value_counts()
                        nurse_counts = all_nurse_counts.head(10)  # Top 10 for visualization
                        
                        # Create nurse performance visualization
                        fig3, ax3 = plt.subplots(figsize=(10, 6))
                        sns.barplot(x=nurse_counts.values, y=nurse_counts.index, ax=ax3)
                        ax3.set_title("Top 10 Active Sisters")
                        ax3.set_xlabel("Number of Consultations")
                        
                        # Add data labels to the bars
                        ax3.bar_label(ax3.containers[0], labels=[f'{v}' for v in nurse_counts.values], padding=3)
                        
                        st.pyplot(fig3)

                        # Save nurse graph
                        nurse_img_bytes = io.BytesIO()
                        fig3.savefig(nurse_img_bytes, format='png')
                        nurse_img_bytes.seek(0)
                        
                        # Create columns for nurse download buttons
                        nurse_dl_col1, nurse_dl_col2 = st.columns(2)
                        
                        # Download nurse graph button
                        with nurse_dl_col1:
                            st.download_button(
                                label="Download Graph",
                                data=nurse_img_bytes,
                                file_name="nurse_analysis.png",
                                mime="image/png"
                            )
                        
                        # Download nurse data button (all nurses)
                        with nurse_dl_col2:
                            all_nurse_csv = all_nurse_counts.to_frame(name='Consultations').to_csv(index=True)
                            st.download_button(
                                label="Download Data",
                                data=nurse_monthly.to_csv(index=True),
                                file_name=f'nurse_wise_data.csv',
                                mime='text/csv'
                            )
                        
                        # Show detailed nurse data in expander
                        with st.expander("Click to view nurse-wise details"):
                            st.write("Monthly Consultation Breakdown:")
                            st.dataframe(nurse_monthly)
                                                
                    # Date-wise Analysis Section
                    col5, col6 = st.columns(2)
                    if selected_dates:
                        date_df = filtered_df[filtered_df['Date'].isin(selected_dates)]
                    else:
                        date_df = filtered_df
                    date_monthly = pd.pivot_table(
                                date_df,
                                values='month_name',
                                index='Date',
                                columns='RegionalUnit',
                                aggfunc='count',
                                fill_value=0
                                
                            ).round(0)
                
                    with col5:
                        st.subheader("Date Wise Analysis")
                        # Get region counts for selected months
                        date_counts = date_df['Date'].value_counts()
                        
                        # Create region performance visualization
                        fig5, ax5 = plt.subplots(figsize=(10, 6))
                        sns.barplot(x=date_counts.values, y=date_counts.index, ax=ax5)
                        ax5.set_title(f"Date Wise Analysis")
                        ax5.set_xlabel("Number of Consultations")
                        ax5.set_ylabel("Date")
                        
                        # Add data labels to the bars
                        ax5.bar_label(ax5.containers[0], labels=[f'{v}' for v in date_counts.values], padding=3)
                        
                        st.pyplot(fig5)
                        
                        # Save region graph
                        date_img_bytes = io.BytesIO()
                        fig5.savefig(date_img_bytes, format='png')
                        date_img_bytes.seek(0)
                        
                        # Create columns for region download buttons
                        date_dl_col1, date_dl_col2 = st.columns(2)
                        
                        # Download region graph button
                        with date_dl_col1:
                            st.download_button(
                                label="Download Graph",
                                data=date_img_bytes,
                                file_name="date_analysis.png",
                                mime="image/png"
                            )
                        
                        # Download region data button
                        with date_dl_col2:
                            date_csv = date_counts.to_csv(index=True)
                            st.download_button(
                                label="Download Data",
                                data=date_monthly.to_csv(index=True),
                                file_name=f'date_wise_data.csv',
                                mime='text/csv'
                            )
                        
                        # Show detailed region data in expander
                        with st.expander("Click to view date-wise details"):
                            st.write("Monthly Consultation Breakdown by Date:")
                            st.dataframe(date_monthly) 

                    # Filter the date_df based on selected regions
                    if selected_dates:
                        date_df = filtered_df[filtered_df['Date'].isin(selected_dates)]
                    else:
                        date_df = filtered_df  # If no region is selected, use the entire filtered dataset

                    # Create monthly consultation breakdown for nurses based on date_df
                    date_monthly = pd.pivot_table(
                        date_df,
                        values='month_name',
                        index='Nurse Name',
                        columns='Date',
                        aggfunc='count',
                        fill_value=0
                    ).round(0)

                    # Sort by total consultations
                    date_monthly['Total'] = date_monthly.sum(axis=1)
                    date_monthly = date_monthly.sort_values('Total', ascending=False)

                    with col6:
                        st.subheader("Performance of Active Sisters")
                        
                        # Get region counts for selected months

                        performance_counts = date_df['Date'].value_counts()
                        
                        # Create performance visualization
                        fig6, ax6 = plt.subplots(figsize=(10, 6))
                        sns.barplot(x=performance_counts.values, y=performance_counts.index, ax=ax6)
                        ax6.set_title(f"Performance of Active Sisters")
                        ax6.set_xlabel("Number of Consultations")
                        ax6.set_ylabel("Date")
                        
                        # Add data labels to the bars
                        ax6.bar_label(ax6.containers[0], labels=[f'{v}' for v in performance_counts.values], padding=3)
                        
                        st.pyplot(fig6)
                        
                        # Save performance graph
                        date_img_bytes = io.BytesIO()
                        fig6.savefig(date_img_bytes, format='png')  # Ensure correct figure (fig6) is saved
                        date_img_bytes.seek(0)
                        
                        # Create columns for download buttons
                        date_dl_col1, date_dl_col2 = st.columns(2)
                        
                        # Download graph button
                        with date_dl_col1:
                            st.download_button(
                                label="Download Graph",
                                data=date_img_bytes,
                                file_name="performance.png",
                                mime="image/png"
                            )
                        
                        # Download data button (performance data)
                        with date_dl_col2:
                            date_monthly_csv = date_monthly.to_csv(index=True)  # Use filtered date_monthly for download
                            st.download_button(
                                label="Download Data",
                                data=date_monthly_csv,
                                file_name=f'performance_data.csv',
                                mime='text/csv'
                            )
                        
                        # Show detailed date-wise data in expander
                        with st.expander("Click to view date-wise details"):
                            st.write("Monthly Consultation Breakdown by Date:")
                            st.dataframe(date_monthly)

        except Exception as e:
            st.error(f"Error retrieving data: {str(e)}")
            
if __name__ == "__main__":
    dashboard()
