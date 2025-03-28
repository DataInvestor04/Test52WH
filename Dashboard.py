import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

@st.cache_data
def load_data(file):
    """Load and preprocess the data"""
    try:
        df = pd.read_csv(file)
        # url = "https://raw.githubusercontent.com/DataInvestor04/52WH/refs/heads/main/financial_metrics.csv"
        # df = pd.read_csv(url)
        df["Today's Date"] = pd.to_datetime(df["Today's Date"])

        # Clean percentage change column
        df['%chng'] = df['%chng'].astype(str).str.replace('%', '').str.strip()
        df['%chng'] = pd.to_numeric(df['%chng'], errors='coerce')

        # Clean numeric columns
        numeric_columns = ['ROE', 'ROCE', 'P/E Ratio', 'Book Value', 'Dividend Yield']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('%', '').str.replace('₹', '')
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Clean Market Cap column
        df['Market Cap'] = df['Market Cap'].astype(str).str.replace('₹', '').str.replace(',', '')
        df['Market Cap'] = pd.to_numeric(df['Market Cap'].str.extract(r'(\d+(?:\.\d+)?)', expand=False), errors='coerce')

        # Clean Symbol column
        df['Symbol'] = df['Symbol'].astype(str).str.strip().str.upper()
        df['Series Type'] = df['Series Type'].fillna('N/A')
        df['Series Type'] = df['Series Type'].astype(str)

        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()
    
def get_stock_highs(data, symbol):
    """Get dates when the stock made new highs"""
    if symbol:
        stock_data = data[data['Symbol'] == symbol].copy()
        if not stock_data.empty:
            stock_data = stock_data.sort_values("Today's Date")
            stock_data['High_LTP'] = stock_data['LTP'].cummax()
            high_dates = stock_data[stock_data['LTP'] == stock_data['High_LTP']].copy()
            return high_dates, stock_data
    return pd.DataFrame(), pd.DataFrame()

def get_latest_stock_data(filtered_data):
    """Get the latest data for each stock with count"""
    stock_counts = filtered_data['Symbol'].value_counts().to_dict()
    latest_data = filtered_data.sort_values(["Today's Date", '%chng'], ascending=[False, False]).groupby('Symbol').first().reset_index()
    latest_data['count'] = latest_data['Symbol'].map(stock_counts)
    return latest_data.sort_values('count', ascending=False)

def format_metric_value(value, precision=2):
    """Format metric value with proper type checking"""
    try:
        if pd.isna(value):
            return "N/A"
        if isinstance(value, str):
            # Try to convert string to float
            value = float(value.replace('₹', '').replace(',', '').strip())
        return f"{value:.{precision}f}"
    except (ValueError, TypeError):
        return "N/A"

def create_metric_container(label, value, unit="", color="white", trend=None):
    """Create an enhanced metric container with better typography and colors"""
    trend_color = {
        "up": "#22C55E",
        "down": "#EF4444",
        None: "white"
    }
    
    trend_icon = {
        "up": "↑",
        "down": "↓",
        None: ""
    }
    
    st.markdown(
        f"""
        <div style="background-color: rgba(30, 34, 45, 0.98); padding: 15px; border-radius: 8px; 
                    margin: 8px 0; border: 1px solid rgba(255, 255, 255, 0.1);">
            <div style="color: #A5B4FC; font-size: 13px; font-weight: 500; 
                        letter-spacing: 0.5px; text-transform: uppercase;">{label}</div>
            <div style="color: {color}; font-size: 20px; font-weight: 600; 
                        margin-top: 8px; display: flex; align-items: center;">
                <span style="color: {trend_color[trend]}">
                    {value}{' ' + unit if unit else ''} {trend_icon[trend]}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def create_stock_card(row):
    """Create a stock card with simple background color based on performance"""
    # Determine background color based on price change
    price_change = row['%chng']
    # if price_change >= 2:
    #     bg_color = "rgba(255, 255, 255, 1)"  # Green
    # elif price_change >= 0:
    #     bg_color = "rgba(255, 255, 255, 1)"  # Blue
    # else:
    bg_color = "rgba(255, 255, 255, 0.5)"  # Red

    st.markdown(f"""
        <style>
        .stock-card {{
            background-color: {bg_color};
            border-radius: 12px;
            padding: 5px;
            margin-bottom: 24px;
            border: 1px solid rgba(255, 255, 255, 1);
        }}
        .stock-header {{
            display: flex;
            align-items: center;
            margin-bottom: 24px;
        }}
        .stock-title {{
            font-size: 28px;
            font-weight: 700;
            color: #A5B4FC;
        }}
        </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="stock-card">', unsafe_allow_html=True)
        
        # Header Section
        symbol = row['Symbol']
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"""
            <div class="stock-header">
                <div>
                    <div class="stock-title">
                    <span>
                        <a href="https://www.screener.in/company/{symbol}">
                            {row['Symbol']}   
                        </a>
                        <strong>       ({row['Series Type']})</strong>
                    </span>
                    </div>
                    <div>
                        <span style="margin-right: 20px; color: #E2E8F0;">
                            <strong>Sector:</strong> {row.get('Sector', 'N/A')}
                        </span>
                    </div>
                    <div>
                        <span style="color: #E2E8F0;">
                            <strong>Industry:</strong> {row.get('Industry', 'N/A')}     
                        </span>
                    </div>
                </div>
            </div>

            """, unsafe_allow_html=True)
        
        with col2:
            price = format_number(row['LTP'])
            price_change = row['%chng']
            price_color = "#22C55E" if price_change >= 0 else "#EF4444"
            st.markdown(f"""
                <div style="text-align: right; width: 180%;">
                    <div style="font-size: 30px; font-weight: 700; color: white;">{price}</div>
                    <div style="font-size: 20px; font-weight: 600; color: {price_color};">
                        {price_change:+.2f}% {' ↑' if price_change >= 0 else ' ↓'}
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # Metrics Grid
        col1, col2, col3 = st.columns(3)
        
        with col1:
            create_metric_container("Market Cap", 
                                  format_number(row.get('Market Cap', 'N/A')),
                                  color="#A5B4FC")
            create_metric_container("Days Since High",
                                  format_metric_value(row['Days Since High']),
                                  color="#BAE6FD")

        with col2:
            create_metric_container("Stock P/E", 
                                  format_metric_value(row.get('P/E Ratio', 'N/A')),
                                  color="#93C5FD")
            create_metric_container("ROE",
                                  format_metric_value(row.get('ROE', 'N/A')),
                                  unit="%",
                                  color="#FDA4AF")

        with col3:
            create_metric_container("Dividend Yield",
                                  format_metric_value(row.get('Dividend Yield', 'N/A')),
                                  unit="%",
                                  color="#FCA5A5")
            create_metric_container("ROCE",
                                  format_metric_value(row.get('ROCE', 'N/A')),
                                  unit="%",
                                  color="#FDBA74")

        # About Section
        if 'About' in row and pd.notnull(row['About']) and str(row['About']) != 'nan':
            st.markdown(f"""
                <div style="margin-top: 20px; padding: 16px; background: rgba(30, 41, 59, 0.4); 
                            border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1);">
                    <div style="color: #A5B4FC; font-size: 16px; font-weight: 600; margin-bottom: 8px;">About</div>
                    <div style="color: #FFFFFF; font-size: 20px; line-height: 1.6;">{row['About']}</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
def create_sector_chart(filtered_data):
    """Create an enhanced sector distribution chart"""
    sector_counts = filtered_data['Sector'].value_counts()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=sector_counts.index,
        y=sector_counts.values,
        marker_color='rgb(165, 180, 252)',
        marker_line_color='rgb(129, 140, 248)',
        marker_line_width=1.5,
        opacity=0.8,
        text=sector_counts.values,
        textposition='auto',
    ))
    
    fig.update_layout(
        title={
            'text': "Sector Distribution",
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 24, 'color': '#A5B4FC'}
        },
        xaxis_tickangle=-45,
        template='plotly_dark',
        showlegend=False,
        xaxis_title="Sector",
        yaxis_title="Number of Companies",
        height=400,
        paper_bgcolor='rgba(17, 24, 39, 0.7)',
        plot_bgcolor='rgba(17, 24, 39, 0.7)',
        font={'color': '#9CA3AF'},
        xaxis={'gridcolor': 'rgba(255, 255, 255, 0.1)'},
        yaxis={'gridcolor': 'rgba(255, 255, 255, 0.1)'}
    )

    return fig

def format_number(num):
    """Format numbers with appropriate scale and currency symbol"""
    try:
        if pd.isna(num):
            return "N/A"
        if isinstance(num, str):
            num = float(num.replace('₹', '').replace(',', '').strip())
        
        if num >= 1e9:
            return f"₹{num/1e9:.2f}B"
        elif num >= 1e7:
            return f"₹{num/1e7:.2f}Cr"
        elif num >= 1e5:
            return f"₹{num/1e5:.2f}L"
        else:
            return f"₹{num:,.2f}"
    except (ValueError, TypeError):
        return "N/A"

def get_stock_symbols(data, search_text):
    """Get filtered list of stock symbols based on search text"""
    if not search_text:
        return []
    
    # Get unique symbols from the data
    symbols = data['Symbol'].unique()
    
    # Filter symbols that start with the search text (case-insensitive)
    filtered_symbols = [
        symbol for symbol in symbols 
        if symbol.lower().startswith(search_text.lower())
    ]
    
    return sorted(filtered_symbols)




def main():
    st.set_page_config(layout="wide", page_title="Stock Data Dashboard")
    
    st.markdown("""
        <style>
          .stSelectbox, .stDateInput {
            background-color: rgba(51, 65, 85, 0.4) !important;
            border: 1px solid rgba(148, 163, 184, 0.1) !important;
            border-radius: 8px !important;
            color: #E2E8F0 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    st.title("📈 Stock Data Dashboard")
    
    st.markdown("View and analyze 52 week high stocks with multiple filtering options.")
    
    # Description using native Streamlit components
    st.info("""
        **Comprehensive Analysis Tool:**
        - Track specific dates or date ranges
        - Analyze monthly trends
        - Search and monitor individual stocks
    """)

    # Load data
    data = load_data('financial_metrics.csv')
    if data.empty:
        st.error("No data available. Please check your CSV file.")
        return
    
    # Initialize filtered_data as empty DataFrame
    filtered_data = pd.DataFrame()
    date_display = ""
    search_text = ""
    
    # Sidebar filters
    with st.sidebar:
        st.header("Filters")
        view_type = st.radio(
            "Select View Type",
            ["Specific Date📆", "Date Range⏳", "Month📅", "Search Stock🔎"]
        )

        if view_type == "Specific Date📆":
            selected_date = st.date_input(
                "Select Date",
                data["Today's Date"].max(),
                min_value=data["Today's Date"].min(),
                max_value=data["Today's Date"].max()
            )
            # First filter by date
            filtered_data = data[data["Today's Date"].dt.date == selected_date]
            date_display = selected_date.strftime('%d %B %Y')

            # Get only the sectors present in the filtered data
            available_sectors = ['All'] + sorted(filtered_data['Sector'].unique().tolist())
            selected_sectors = st.selectbox("Filter by Sector:", available_sectors)

            # Get series types from the date-filtered data
            available_series = ['All'] + sorted(filtered_data['Series Type'].unique().tolist())
            selected_series = st.selectbox("Filter by Series:", available_series)

            # Apply additional filters
            if selected_sectors != 'All':
                filtered_data = filtered_data[filtered_data['Sector'] == selected_sectors]
            if selected_series != 'All':
                filtered_data = filtered_data[filtered_data['Series Type'] == selected_series]

        elif view_type == "Search Stock🔎":
            # Get all unique stock symbols
            all_symbols = sorted(data['Symbol'].unique())
            search_symbols = st.multiselect(
                "Search Stock Symbol",
                options=all_symbols,
                placeholder="Select stock symbols to analyze"
            )
            
            # Simple search by exact match
    if view_type == "Search Stock🔎":
        if search_symbols:
            for symbol in search_symbols:
                # Title with stock symbol and current metrics
                st.markdown(f"""
                    <div style='background-color: rgba(17, 24, 39, 0.7); padding: 20px; border-radius: 10px; margin-bottom: 25px'>
                        <h2 style='margin: 0; color: #00FFFF'>{symbol} Analysis</h2>
                    </div>
                """, unsafe_allow_html=True)

                high_dates, stock_data = get_stock_highs(data, symbol)

                if not stock_data.empty:
                    # Key metrics in a clean layout
                    highest_price = stock_data['LTP'].max()
                    
                    metrics_container = st.container()
                    with metrics_container:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric(
                                "52-Week High",
                                format_number(highest_price),
                                delta=None
                            )
                        with col3:
                            st.metric(
                                "High Points Found",
                                f"{len(high_dates)} dates" if not high_dates.empty else "0"
                            )

                    # High points table with enhanced styling
                    if not high_dates.empty:
                        st.markdown("### 📊 High Points Timeline")
                        display_df = high_dates.copy()
                        display_df = display_df.sort_values("Today's Date", ascending=False)
                        
                        # Enhanced data preparation
                        display_df['Date'] = display_df["Today's Date"].dt.strftime('%d %B %Y')
                        display_df['Price'] = display_df['LTP'].apply(format_number)
                        display_df['Change'] = display_df['%chng'].apply(
                            lambda x: f"{'💹' if x > 0 else '🔻'}{x:+.2f}%" if pd.notnull(x) else "N/A"
                        )
                        
                        # Calculate days from previous high
                        # display_df['Days Gap'] = display_df["Today's Date"].diff(-1).dt.days
                        # display_df['Days Gap'] = display_df['Days Gap'].fillna("First High")
                        
                        # Enhanced table display
                        st.dataframe(
                            display_df[['Date', 'Price', 'Change']],
                            hide_index=True,
                            column_config={
                                "Date": st.column_config.Column(
                                    "Date",
                                    help="Date when stock reached a high point",
                                    width="medium"
                                ),
                                "Price": st.column_config.Column(
                                    "Stock Price",
                                    help="Stock price at high point",
                                    width="medium"
                                ),
                                "Change": st.column_config.Column(
                                    "Daily Change",
                                    help="Percentage change on that day",
                                    width="medium"
                                )
                            },use_container_width=True
                        )

                        # Price chart with improved styling
                        # st.markdown("### 📈 Price Chart")
                        # fig = go.Figure()
                        
                        # # Main price line
                        # fig.add_trace(go.Scatter(
                        #     x=stock_data["Today's Date"],
                        #     y=stock_data['LTP'],
                        #     name='Price',
                        #     line=dict(color='#00FFFF', width=1)
                        # ))

                        # # High points markers
                        # fig.add_trace(go.Scatter(
                        #     x=high_dates["Today's Date"],
                        #     y=high_dates['LTP'],
                        #     mode='markers',
                        #     name='High Points',
                        #     marker=dict(
                        #         color='#00FF00',
                        #         size=10,
                        #         symbol='diamond',
                        #         line=dict(color='white', width=1)
                        #     )
                        # ))

                        # fig.update_layout(
                        #     xaxis_title="Date",
                        #     yaxis_title="Price (₹)",
                        #     template='plotly_dark',
                        #     height=500,
                        #     hovermode='x unified',
                        #     paper_bgcolor='rgba(17, 24, 39, 0.7)',
                        #     plot_bgcolor='rgba(17, 24, 39, 0.7)',
                        #     showlegend=True,
                        #     legend=dict(
                        #         yanchor="top",
                        #         y=0.99,
                        #         xanchor="left",
                        #         x=0.01,
                        #         bgcolor="rgba(17, 24, 39, 0.7)"
                        #     ),
                        #     margin=dict(l=0, r=0, t=0, b=0, pad=0)
                        # )

                        # st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning(f"No data found for symbol {symbol}")
        else:
            st.info("Please select one or more stock symbols to view their analysis")    

    # Main content for Specific Date view
    if view_type == "Specific Date📆" and not filtered_data.empty:
        st.header(f"Analysis for {date_display}")

        # Metrics row
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Stocks", len(filtered_data['Symbol'].unique()))
        with col2:
            st.metric("Total Sectors", len(filtered_data['Sector'].unique()))
        with col3:
            avg_change = filtered_data['%chng'].mean()
            st.metric("Average Change", f"{avg_change:+.2f}%")
        
        st.plotly_chart(create_sector_chart(filtered_data), use_container_width=True)

        # Stock cards
        st.header("Stock Details")
        latest_stock_data = get_latest_stock_data(filtered_data)

        for idx, row in latest_stock_data.iterrows():
            create_stock_card(row)

    elif view_type == "Specific Date📆":
        st.warning("No data found for the selected filters.")

    elif view_type == "Month📅":
        data['Month'] = data["Today's Date"].dt.strftime('%B %Y')
        months = sorted(data['Month'].unique(), 
                    key=lambda x: datetime.strptime(x, '%B %Y'))
        selected_month = st.sidebar.selectbox("Select Month", months)
        
        filtered_data = data[data["Today's Date"].dt.strftime('%B %Y') == selected_month]
        date_display = selected_month

        available_sectors = ['All'] + sorted(filtered_data['Sector'].unique().tolist())
        selected_sectors = st.sidebar.selectbox("Filter by Sector:", available_sectors)


        # Get series types from the date-filtered data
        available_series = ['All'] + sorted(filtered_data['Series Type'].unique().tolist())
        selected_series = st.sidebar.selectbox("Filter by Series:", available_series)

            # Apply additional filters
        if selected_sectors != 'All':
            filtered_data = filtered_data[filtered_data['Sector'] == selected_sectors]
        if selected_series != 'All':
            filtered_data = filtered_data[filtered_data['Series Type'] == selected_series]


        
        if not filtered_data.empty:
            st.header(f"Analysis for {date_display}")
            
            # Metrics row
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Stocks", len(filtered_data['Symbol'].unique()))
            with col2:
                st.metric("Total Sectors", len(filtered_data['Sector'].unique()))
            with col3:
                avg_change = filtered_data['%chng'].mean()
                st.metric("Average Change", f"{avg_change:+.2f}%")
            
            # Sector chart - full width
            st.plotly_chart(create_sector_chart(filtered_data), use_container_width=True)
            
            # Sector table - below chart
            st.markdown("### 📊 Sector Distribution")
            sector_counts = filtered_data['Sector'].value_counts().reset_index()
            sector_counts.columns = ['Sector', 'Count']
            sector_counts['Percentage'] = (sector_counts['Count'] / sector_counts['Count'].sum() * 100).round(2)
            
            
            # Apply custom CSS
            st.markdown("""
                <style>
                    div[data-testid="stDataFrame"] div[data-testid="stTable"] {
                        font-size: 1.1rem;
                    }
                    div[data-testid="stDataFrame"] th {
                        background-color: #1E3A5F;
                        color: white;
                        font-weight: bold;
                    }
                </style>
            """, unsafe_allow_html=True)
            
            # Make sure data is properly converted to basic Python types
            st.dataframe(
                sector_counts,
                hide_index=True,
                column_config={
                    "Sector": "Sector",
                    "Count": st.column_config.NumberColumn(
                        "Count",
                        format="%d"
                    ),
                    "Percentage": st.column_config.ProgressColumn(
                        "% of Total",
                        format="%.1f%%",
                        min_value=0,
                        max_value=100
                    )
                },
                use_container_width=True
            )
            
            # Stock occurrences table
            st.markdown("### 📈 Most Frequent Stocks")
            st.markdown("Stocks that appeared most frequently during the month")
            
            # Count unique dates for each stock symbol
            stock_occurrences = filtered_data.groupby('Symbol')["Today's Date"].nunique().reset_index()
            stock_occurrences.columns = ['Symbol', 'Occurrences']
            
            # Get additional information for each stock - ensure numeric values
            stock_info = filtered_data.groupby('Symbol').agg({
                # 'LTP': 'last',
                # '%chng': 'mean',
                'Series Type': 'first',
                'Sector': 'first'
            }).reset_index()
            
            # Convert any potential problematic values
            # stock_info['LTP'] = stock_info['LTP'].astype(float)
            # stock_info['%chng'] = stock_info['%chng'].astype(float)
            
            # Merge occurrences with stock info
            stock_table = pd.merge(stock_occurrences, stock_info, on='Symbol')
            stock_table = stock_table.sort_values('Occurrences', ascending=False)
            
            # Get the maximum occurrences for the progress bar
            max_occurrences = int(stock_table['Occurrences'].max())
            
            # Create the table with simplified column config

            
            # st.dataframe(
            #     stock_table,
            #     hide_index=True,
            #     column_config={
            #         "Symbol": st.column_config.TextColumn("Symbol"),
            #         "Occurrences": st.column_config.ProgressColumn(
            #             "Frequency",
            #             help="Number of days stock appeared",
            #             format="%d times",
            #             min_value=1,
            #             max_value=max(stock_table["Occurrences"])
            #         ),
            #         "Series Type": "Series",
            #         "Sector": "Sector"
            #     },
            #     use_container_width=True
            # )
            stock_table['Symbol'] = stock_table['Symbol'].apply(
        lambda symbol: f'<a href="https://www.screener.in/company/{symbol}" target="_blank">{symbol}</a>'
    )

            st.write(
                stock_table.to_html(
                    escape=False,  # Ensures HTML tags are rendered
                    index=False  # Hides the index
                ),
                unsafe_allow_html=True
            )
        else:
            st.warning(f"No data found for {selected_month}")
    elif view_type == "Date Range⏳":
    # Get min and max dates for the range selector
        min_date = data["Today's Date"].min()
        max_date = data["Today's Date"].max()
        
        # Create date range selector
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_date = st.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
        with col2:
            end_date = st.date_input("End Date", max_date, min_value=min_date, max_value=max_date)
        
        # Filter data based on selected date range
        filtered_data = data[
            (data["Today's Date"].dt.date >= start_date) & 
            (data["Today's Date"].dt.date <= end_date)
        ]
        date_display = f"{start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}"

        available_sectors = ['All'] + sorted(filtered_data['Sector'].unique().tolist())
        selected_sectors = st.sidebar.selectbox("Filter by Sector:", available_sectors)


        # Get series types from the date-filtered data
        available_series = ['All'] + sorted(filtered_data['Series Type'].unique().tolist())
        selected_series = st.sidebar.selectbox("Filter by Series:", available_series)

            # Apply additional filters
        if selected_sectors != 'All':
            filtered_data = filtered_data[filtered_data['Sector'] == selected_sectors]
        if selected_series != 'All':
            filtered_data = filtered_data[filtered_data['Series Type'] == selected_series]
        
        if not filtered_data.empty:
            st.header(f"Analysis for {date_display}")
            
            # Metrics row
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Stocks", len(filtered_data['Symbol'].unique()))
            with col2:
                st.metric("Total Sectors", len(filtered_data['Sector'].unique()))
            with col3:
                avg_change = filtered_data['%chng'].mean()
                st.metric("Average Change", f"{avg_change:+.2f}%")
            
            # Sector chart - full width
            st.plotly_chart(create_sector_chart(filtered_data), use_container_width=True)
            
            # Sector table - below chart
            st.markdown("### 📊 Sector Distribution")
            sector_counts = filtered_data['Sector'].value_counts().reset_index()
            sector_counts.columns = ['Sector', 'Count']
            sector_counts['Percentage'] = (sector_counts['Count'] / sector_counts['Count'].sum() * 100).round(2)
            
            # Apply custom CSS
            st.markdown("""
                <style>
                    div[data-testid="stDataFrame"] div[data-testid="stTable"] {
                        font-size: 1.1rem;
                    }
                    div[data-testid="stDataFrame"] th {
                        background-color: #1E3A5F;
                        color: white;
                        font-weight: bold;
                    }
                </style>
            """, unsafe_allow_html=True)
            
            # Make sure data is properly converted to basic Python types
            st.dataframe(
                sector_counts,
                hide_index=True,
                column_config={
                    "Sector": "Sector",
                    "Count": st.column_config.NumberColumn(
                        "Count",
                        format="%d"
                    ),
                    "Percentage": st.column_config.ProgressColumn(
                        "% of Total",
                        format="%.1f%%",
                        min_value=0,
                        max_value=100
                    )
                },
                use_container_width=True
            )

            
            # Stock occurrences table
            st.markdown("### 📈 Most Frequent Stocks")
            st.markdown("Stocks that appeared most frequently during the selected period")
            
            # Count unique dates for each stock symbol
            stock_occurrences = filtered_data.groupby('Symbol')["Today's Date"].nunique().reset_index()
            stock_occurrences.columns = ['Symbol', 'Occurrences']
            
            # Get additional information for each stock
            stock_info = filtered_data.groupby('Symbol').agg({
                'Series Type': 'first',
                'Sector': 'first'
            }).reset_index()
            
            # Merge occurrences with stock info
            stock_table = pd.merge(stock_occurrences, stock_info, on='Symbol')
            stock_table = stock_table.sort_values('Occurrences', ascending=False)
            
            stock_table['Symbol'] = stock_table['Symbol'].apply(
        lambda symbol: f'<a href="https://www.screener.in/company/{symbol}" target="_blank">{symbol}</a>'
    )
            # Create the table with simplified column config
            # st.dataframe(
            #     stock_table,
            #     hide_index=True,
            #     column_config={
            #         "Symbol": st.column_config.TextColumn("Symbol"),
            #         "Occurrences": st.column_config.ProgressColumn(
            #             "Frequency",
            #             help="Number of days stock appeared",
            #             format="%d times",
            #             min_value=1,
            #             max_value=max(stock_table["Occurrences"])
            #         ),
            #         "Series Type": "Series",
            #         "Sector": "Sector"
            #     },
            #     use_container_width=True
            # )

            st.write(
                stock_table.to_html(
                    escape=False,  # Ensures HTML tags are rendered
                    index=False  # Hides the index
                ),
                unsafe_allow_html=True
            )
        else:
            st.warning(f"No data found between {start_date} and {end_date}")
    
    
if __name__ == "__main__":
    main() 
