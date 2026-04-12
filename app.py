import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Price Comparison Dashboard", page_icon="🎮", layout="wide")

st.title("🎮 Real-Time Price Comparison Dashboard")
st.markdown("Track the current price of **PlayStation 5 Console** across different merchants using SerpApi Google Shopping.")

# Add sidebar for API key
api_key = st.sidebar.text_input("Enter SerpApi Key", type="password")

if not api_key:
    st.warning("Please enter your SerpApi API key in the sidebar to continue. You can get one at https://serpapi.com/")
    st.stop()

@st.cache_data(ttl=3600)
def fetch_prices(query, api_key):
    params = {
      "engine": "google_shopping",
      "q": query,
      "hl": "en",
      "gl": "us",
      "api_key": api_key
    }
    
    url = "https://serpapi.com/search"
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching data: {response.status_code}")
        return None

query = st.text_input("Search Query", "PlayStation 5 Console")

if st.button("Fetch Prices", type="primary"):
    with st.spinner("Fetching data from SerpApi..."):
        data = fetch_prices(query, api_key)
        
        if data and "shopping_results" in data:
            results = data["shopping_results"]
            
            # Extract relevant info
            extracted_data = []
            for item in results:
                if "source" in item and "price" in item:
                    try:
                        # Sometimes price is a string like '$499.00', extraction helps to sort them.
                        raw_price = item.get("price", "0").replace("$", "").replace(",", "")
                        price_val = item.get("extracted_price", float(raw_price))
                    except ValueError:
                        continue
                        
                    extracted_data.append({
                        "Merchant": item.get("source"),
                        "Price": price_val,
                        "Title": item.get("title"),
                        "Link": item.get("link")
                    })
                    
            df = pd.DataFrame(extracted_data)
            
            if not df.empty:
                # Group by merchant and get the cheapest 3 unique merchants
                df_unique_merchants = df.sort_values("Price").drop_duplicates(subset=["Merchant"])
                top_3 = df_unique_merchants.head(3).reset_index(drop=True)
                
                st.subheader(f"Top 3 Merchants for '{query}'")
                
                # Display metrics
                cols = st.columns(3)
                for i, row in top_3.iterrows():
                    # Safeguard if there are less than 3 results
                    if i < 3:
                        with cols[i]:
                            st.metric(label=row["Merchant"], value=f"${row['Price']:.2f}")
                            st.markdown(f"**[{row['Title'][:50]}...]({row['Link']})**")
                
                st.markdown("---")
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.subheader("All Results")
                    st.dataframe(df, use_container_width=True)
                
                with col2:
                    # Chart
                    st.subheader("Price Comparison")
                    if len(top_3) > 0:
                        chart_data = top_3.set_index("Merchant")["Price"]
                        st.bar_chart(chart_data)
                    else:
                        st.info("Not enough data to generate chart.")
            else:
                st.warning("No price data found in the results.")
        else:
            st.warning("No shopping results returned. Please adjust your query.")
