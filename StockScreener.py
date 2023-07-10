import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
import yahooquery as yq
import plotly.express as px
import datetime
 
# url or file of the ticker source
sp500_url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
djia_url = 'https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average'
 
# Create a new variable query_submit and set equal to false for flow - used later, set at beginning
query_submit = False
 
# Create a simple title for our page
st.title('S&P500 and DJIA Stock Screener')
 
# Create a form located on a sidebar with a key and no clear on submit
with st.form(key = 'stock_inputs', clear_on_submit = False):
    with st.sidebar:
        
        # Create a sidebar title
        st.sidebar.title('Stock Inputs')
 
        # Create a selectbox for the index of choice
        stock_index = st.sidebar.selectbox('Select Index of Interest:', ['', 'S&P500', 'DJIA'])
 
        # Retrieving tickers data only IF index is selected, use read_html(x, flavor = 'html5lib')[x]['Symbol'])
        if stock_index:
            if stock_index == 'S&P500':
                stock_list = pd.read_html(sp500_url, flavor = 'html5lib')[0]['Symbol']
            if stock_index == 'DJIA':
                stock_list = pd.read_html(djia_url, flavor = 'html5lib')[1]['Symbol']
 
            # Select the ticker of interest from the index selected
            stock_ticker = st.sidebar.selectbox(f'Select ticker from {stock_index}', stock_list)
 
            # Get the data for that specific ticker using yf.Ticker
            ticker_data = yf.Ticker(stock_ticker)
 
            # Select a benchmark
            benchmark = st.sidebar.selectbox('Select a bechmark', ['S&P500', 'DJIA', 'Nasdaq', 'Russell 1000', 'Russell 2000'])
            if benchmark == 'S&P500':
                benchmark_ticker = 'SPY'
            if benchmark == 'DJIA':
                benchmark_ticker = 'DIA'
            if benchmark == 'Nasdaq':
                benchmark_ticker = 'QQQ'
            if benchmark == 'Russell 1000':
                benchmark_ticker = 'IWB'
            if benchmark == 'Russell 2000':
                benchmark_ticker = 'IWM'
            benchmark_data = yf.Ticker(benchmark_ticker)
 
            # Get the historical prices for that ticker using a period of '30d' and the file created above and .history
            time_period = str(st.slider('Select time period of interest in days:', min_value = 30, max_value = 365*3))
            ticker_prices = ticker_data.history(f'{time_period}'+ 'd')
            benchmark_prices = benchmark_data.history(f'{time_period}'+ 'd')
 
            # Drop all missing values from prices
            ticker_prices.dropna(inplace = True)
            benchmark_prices.dropna(inplace = True)
 
            # Create a form submit button with a label
            query_submit = st.form_submit_button('Submit stock inputs.')
        
# if query_submit is changed from False to True in the above for loop, display stock info
if query_submit:
    
    # display company long name (longName), use st.header
    stock_name = ticker_data.info['longName']
    st.header(stock_name)

    # display company summary (longBusinessSummary), use st.write
    with st.expander('Company Summary'):
        st.write(f'{ticker_data.info["longName"]}')
        st.write(f'Location: {ticker_data.info["city"]}, {ticker_data.info["state"]}')
        st.write(f'Industry: {ticker_data.info["industry"]}')
        st.write(f'Sector: {ticker_data.info["sector"]}')
        st.write(f'Company Officer: {ticker_data.info["companyOfficers"][0]["name"]}')
        st.write(f'Title: {ticker_data.info["companyOfficers"][0]["title"]}')
        st.write(f'Company Summary: {ticker_data.info["longBusinessSummary"]}')
 
    # get actual price data and display the dataframe
    ticker_prices['Returns'] = ticker_prices['Close'].pct_change()*100
    benchmark_prices['Benchmark_Returns'] = benchmark_prices['Close'].pct_change()*100

    st.subheader(f'Returns over time for {stock_name}')
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f'Time period: prior {time_period} days')
    with col2:
        st.write(f'Average daily return: {ticker_prices["Returns"].mean():.2f}%')
    with col3:
        st.write(f'Risk of daily returns: {ticker_prices["Returns"].std():.2f}%')
        
    col1.metric(label = f'Prior Day Price: {ticker_prices.index[-2].date()}', value = f'${ticker_prices["Close"][-2]:.2f}', delta = f'{ticker_prices["Returns"][-1]:.2f}%')
    col2.metric(label = f'Prior Month Price: {ticker_prices.index[-30].date()}', value = f'${ticker_prices["Close"][-30]:.2f}', delta = f'{(ticker_prices["Close"][-1] - ticker_prices["Close"][-30]) / ticker_prices["Close"][-30]:.2f}%')
    col3.metric(label = f'Price {time_period} Days Prior: {ticker_prices.index[-int(time_period)].date()}', value = f'${ticker_prices["Close"][-int(time_period)]:.2f}', delta = f'{(ticker_prices["Close"][-1] - ticker_prices["Close"][-int(time_period)]) / ticker_prices["Close"][-int(time_period)]:.2f}%')
        
    # Combine the two dataframes into one for excess performance measure
    excess_returns = pd.merge(ticker_prices, benchmark_prices, how = 'inner', on = 'Date')
    excess_returns['Excess Returns'] = excess_returns['Returns'] - excess_returns['Benchmark_Returns']
    st.write(f'The average return of {stock_name} is {excess_returns["Returns"].mean():.2f}% \
            and the average return of {benchmark} is {excess_returns["Benchmark_Returns"].mean():.2f}%. \
            Over the requested period {stock_name} {"outperformed" if excess_returns["Excess Returns"].mean() > 0 else "underperformed"} \
            the {benchmark} by {excess_returns["Excess Returns"].mean():.2f}%.')    
        
    # Plot the chart using st.plotly_chart
    fig = px.scatter(ticker_prices, x=ticker_prices.index, y='Returns', marginal_y = 'box', trendline = 'ols', trendline_color_override='red')
    st.plotly_chart(fig, use_container_width=True)
    
    # create subheader for analyst recommendations
    st.subheader('Analyst Recommendations')

    # download recommendations with .get_recommendations
    ticker_raw = yq.Ticker(stock_ticker)
    recos = ticker_raw.grading_history
    
    st.divider()
    st.write(f'The current price of {ticker_data.info["longName"]} is \${ticker_data.info["currentPrice"]}\
            with an avearge target price of \${ticker_data.info["targetMeanPrice"]}.')
    st.write(f'This is a {((ticker_data.info["targetMeanPrice"] - ticker_data.info["currentPrice"])/ticker_data.info["currentPrice"])*100:.2f}\% change in price.\
            The low target price is \${ticker_data.info["targetLowPrice"]} and the high target price is \${ticker_data.info["targetHighPrice"]}.')
    
    st.divider()
    col4, col5 = st.columns(2)
    with col4:
        for index, row in recos.iloc[0:5].iterrows():
            st.write(f'{row["firm"]} recommendation: ***{row["toGrade"]}***')
    with col5:
        for index, row in recos.iloc[5:10].iterrows():
            st.write(f'{row["firm"]} recommendation: ***{row["toGrade"]}***')
    with st.expander('Additonal Recommendation Info'):
        for index, row in recos.head(10).iterrows():
            st.write(f'Firm: {row["firm"]},\
                Date: {row["epochGradeDate"]},\
                Action: {row["action"]},\
                From Grade: {row["fromGrade"]}')
    
    st.subheader(f'Most recent news that mentions {ticker_data.info["longName"]}')
    with st.expander('Article Info'):
        for i in range(5):
            st.write(f'{ticker_data.news[i]["publisher"]} published ***{ticker_data.news[i]["title"]}***\
                on {datetime.datetime.fromtimestamp(ticker_data.news[i]["providerPublishTime"]).date()}\
                The article can be found at {ticker_data.news[i]["link"]}')
            
    st.subheader(f'Financial Statements for {ticker_data.info["longName"]}')
    with st.expander('Balance Sheet'):
        st.write(ticker_data.balance_sheet)
    with st.expander('Cash Flow'):
        st.write(ticker_data.cashflow)
    with st.expander('Income Statement'):
        st.write(ticker_data.income_stmt)
    