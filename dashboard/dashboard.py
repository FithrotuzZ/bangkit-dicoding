import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from datetime import datetime
import datetime as dt
from babel.numbers import format_currency
sns.set(style='dark')

# fix file
try:
    all_data = pd.read_csv("data/all_data.csv")  # Adjust this path according to the file's location
    st.write("File loaded successfully!")
    st.write(all_data)
except FileNotFoundError:
    st.error("The file 'all_data.csv' was not found. Please check the file path or upload the file.")

# Dataset
all_data = pd.read_csv("all_data.csv")

datetime_columns = ["order_approved_at", "order_delivered_customer_date"]
all_data.sort_values(by="order_approved_at", inplace=True)
all_data.reset_index(inplace=True)

for column in datetime_columns:
    all_data[column] = pd.to_datetime(all_data[column])


def create_order_items(df):
    sum_order_items = df.groupby("product_category_name_english").order_item_id.sum().sort_values(ascending=False).reset_index()
    return sum_order_items


def create_by_product(df):
    product_id_counts = df.groupby('product_category_name_english')['product_id'].count().reset_index()
    sorted = product_id_counts.sort_values(by='product_id', ascending=False)
    return sorted


def create_monthly_order_count(df) : 
    monthly_count = df.resample(rule='M', on='order_approved_at').agg({
    "order_id": "nunique",
    "price": "sum"
})
    monthly_count['Year'] = monthly_count.index.year  # Add column 'Year'
    monthly_count.index = monthly_count.index.strftime('%B')  # Convert order date to month
    monthly_count = monthly_count.reset_index()
    monthly_count.rename(columns={
    "order_approved_at" : "Month",
    "order_id": "order_count",
    "price": "revenue"
}, inplace=True)
    return monthly_count


def number_order_per_month(df):
    monthly_df = df.resample(rule='M', on='order_approved_at').agg({
        "order_id": "size",
    })
    monthly_df.index = monthly_df.index.strftime('%B') #mengubah format order_approved_at menjadi Tahun-Bulan
    monthly_df = monthly_df.reset_index()
    monthly_df.rename(columns={
        "order_id": "order_count",
    }, inplace=True)
    monthly_df = monthly_df.sort_values('order_count').drop_duplicates('order_approved_at', keep='last')
    month_mapping = {
        "January": 1,
        "February": 2,
        "March": 3,
        "April": 4,
        "May": 5,
        "June": 6,
        "July": 7,
        "August": 8,
        "September": 9,
        "October": 10,
        "November": 11,
        "December": 12
    }

    monthly_df["month_numeric"] = monthly_df["order_approved_at"].map(month_mapping)
    monthly_df = monthly_df.sort_values("month_numeric")
    monthly_df = monthly_df.drop("month_numeric", axis=1)
    return monthly_df
    

def create_bystate(df):
    state_customer = df.groupby(by="customer_state").customer_id.nunique().sort_values(ascending=False).reset_index()
    state_customer.rename(columns={
        "customer_id": "customer_count"
    }, inplace=True)
    
    return state_customer


def create_bycity(df):
    city_customer = df['customer_city'].value_counts().sort_values(ascending=False)
    return city_customer


def rating_customer(df):
    rating_service = df['review_score'].value_counts().sort_values(ascending=False)
    max_score = rating_service.idxmax()
    df_cust=df['review_score']
    return (rating_service,max_score,df_cust)


# def create_rfm(df):
#     rfm = df.groupby(by="customer_id", as_index=False).agg({
#         "order_purchase_timestamp": "max", #mengambil tanggal order terakhir
#         "order_id": "nunique",
#         "price": "sum"
#     })
#     rfm.columns = ["customer_id", "order_purchase_timestamp", "frequency", "monetary"]
    
#     rfm["order_purchase_timestamp"] = pd.to_datetime(rfm["order_purchase_timestamp"]).dt.to_period('M')
#     recent_date = df["order_purchase_timestamp"].max().to_period('M')
#     rfm["recency"] = rfm["order_purchase_timestamp"].apply(lambda x: (recent_date - x).n)
#     rfm.drop("order_purchase_timestamp", axis=1, inplace=True)
    
#     return rfm

def create_rfm(df):
    now=dt.datetime(2018,10,20)

    df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    # Group by 'customer_id' and calculate Recency, Frequency, and Monetary
    recency = (now - df.groupby('customer_id')['order_purchase_timestamp'].max()).dt.days
    frequency = df.groupby('customer_id')['order_id'].count()
    monetary = df.groupby('customer_id')['price'].sum()

    # Create a new DataFrame with the calculated metrics
    rfm = pd.DataFrame({
        'customer_id': recency.index,
        'Recency': recency.values,
        'Frequency': frequency.values,
        'Monetary': monetary.values
    })

    col_list = ['customer_id','Recency','Frequency','Monetary']
    rfm.columns = col_list
    return rfm

#*********************************Sidebar*********************************

# Filter data
min_date = all_data["order_approved_at"].min()
max_date = all_data["order_approved_at"].max()

with st.sidebar:
    # Date Range Filter
    st.subheader('Date Range Filter')
    min_date = all_data['order_approved_at'].min().date()
    max_date = all_data['order_approved_at'].max().date()
    start_date, end_date = st.date_input(
        label='Time Range',
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )
    
     # Product Filter (selectbox)
    st.subheader('Product Filter')
    all_products = ['All Products'] + list(all_data["product_category_name_english"].unique())
    selected_product = st.selectbox("Pilih Produk", all_products, index=0)  # Set index to 0 for default selection 

# Convert date to datetime
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

# Apply Filters
if selected_product == 'All Products':
    main_df = all_data[
        (all_data["order_approved_at"] >= start_date) & 
        (all_data["order_approved_at"] <= end_date)
    ]
else:
    main_df = all_data[
        (all_data["order_approved_at"] >= start_date) & 
        (all_data["order_approved_at"] <= end_date) & 
        (all_data["product_category_name_english"] == selected_product)
    ]


#*********************************Visualization*********************************

# Prepare dataframes
sum_order_items = create_order_items(main_df)
most_and_least_products=create_by_product(main_df)
monthly_count = create_monthly_order_count(main_df)
daily_orders_df=number_order_per_month(main_df)
state_customer = create_bystate(main_df)
city_customer = create_bycity(main_df)
rating_service,max_score,df_rating_service=rating_customer(main_df)
rfm = create_rfm(all_data)  # Use the entire dataset for RFM DataFrame

# Header
st.header('E-Commerce Dataset :star:')
st.subheader('Order Performances')

col1, col2 = st.columns(2)

with col1:
    total_orders = monthly_count.order_count.sum()
    st.metric("Total orders", value=total_orders)

with col2:
    total_revenue = format_currency(monthly_count.revenue.sum(), "AUD", locale='es_CO') 
    st.metric("Total Revenue", value=total_revenue)


# Body
# Best & Worst Product
st.subheader("Most & Least Product")
col1, col2 = st.columns(2)

with col1:
    highest_product_sold=most_and_least_products['product_id'].max()
    st.markdown(f"Higest Number : **{highest_product_sold}**")

with col2:
    lowest_product_sold=most_and_least_products['product_id'].min()
    st.markdown(f"Lowest Number : **{lowest_product_sold}**")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35, 15))

colors = ["#4b7bb5", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(x="order_item_id", y="product_category_name_english", data=sum_order_items.head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("Number of Sales", fontsize=30)
ax[0].set_title("Product with the Highest Sales", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=35)
ax[0].tick_params(axis='x', labelsize=30)

sns.barplot(x="order_item_id", y="product_category_name_english", data=sum_order_items.sort_values(by="order_item_id", ascending=True).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("Number of Sales", fontsize=30)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Product with the Lowest Sales", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=35)
ax[1].tick_params(axis='x', labelsize=30)

st.pyplot(fig)


# Order Performance Overtime
# All Order
st.subheader("Order Performance")

monthly_count["Month_Year"] = monthly_count.apply(lambda x: f"{x['Month']} {x['Year']}", axis=1) # Join Year & Month

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    monthly_count.index,  # Menggunakan indeks sebagai sumbu x
    monthly_count["order_count"],
    marker='o', 
    linewidth=2,
    color="#4b7bb5"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelrotation=45, labelsize=15)  # Mengatur rotasi label sumbu x agar lebih mudah dibaca
ax.set_xticks(monthly_count.index)  # Menetapkan titik-titik pada sumbu x
ax.set_xticklabels(monthly_count["Month_Year"], rotation=45, ha="right")  # Mengatur label pada sumbu x
ax.set_xlabel("Month and Year", fontsize=18)
ax.set_ylabel("Order Count", fontsize=18)
ax.set_title("Monthly Order Count Over Time", fontsize=20)

plt.tight_layout()
st.pyplot(fig)

# Order by Month
st.subheader('Monthly Orders')
col1, col2 = st.columns(2)

with col1:
    high_order_num = daily_orders_df['order_count'].max()
    high_order_month=daily_orders_df[daily_orders_df['order_count'] == daily_orders_df['order_count'].max()]['order_approved_at'].values[0]
    st.markdown(f"Highest orders in {high_order_month} : **{high_order_num}**")

with col2:
    low_order = daily_orders_df['order_count'].min()
    low_order_month=daily_orders_df[daily_orders_df['order_count'] == daily_orders_df['order_count'].min()]['order_approved_at'].values[0]
    st.markdown(f"Lowest orders in {low_order_month} : **{low_order}**")

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    daily_orders_df["order_approved_at"],
    daily_orders_df["order_count"],
    marker='o',
    linewidth=2,
    color="#4b7bb5",
)
plt.xticks(rotation=25)
ax.tick_params(axis='y', labelsize=15)
ax.tick_params(axis='x', labelsize=15)
ax.set_title("Order by Month", fontsize=20)

st.pyplot(fig)

# Customer Demographics
# By State
st.subheader("Customer Demographics")

top_states = state_customer.sort_values(by="customer_count", ascending=False).head(5)

other_states_count = state_customer["customer_count"].sum() - top_states["customer_count"].sum()
other_states = pd.DataFrame({"customer_state": ["Others"], "customer_count": [other_states_count]})

top_and_other = pd.concat([top_states, other_states])

fig, ax = plt.subplots(figsize=(12, 6))

colors = ["#D3D3D3"] * len(top_and_other["customer_state"])
colors[0] = "#4b7bb5"

ax.bar(top_and_other["customer_state"], top_and_other["customer_count"], color=colors)

ax.set_xlabel("Customer State", fontsize=15)
ax.set_ylabel("Number of Customers", fontsize=15)
ax.set_title("Number of Customers by States (Top 5 and other)", fontsize=20)

st.pyplot(fig)

# By City
city_customer = main_df.groupby('customer_city')['customer_id'].nunique().reset_index()
city_customer.columns = ['customer_city', 'customer_count']

st.subheader("Customer Demographics by City")

top_city = city_customer.sort_values(by="customer_count", ascending=False).head(5)

fig, ax = plt.subplots(figsize=(12, 6))

colors = ["#D3D3D3"] * len(top_city["customer_city"])
colors[0] = "#4b7bb5"

ax.bar(top_city["customer_city"], top_city["customer_count"], color=colors)

ax.set_xlabel("Customer City", fontsize=15)
ax.set_ylabel("Number of Customers", fontsize=15)
ax.set_title("Number of Customers by City (Top 5)", fontsize=20)

st.pyplot(fig)


#Rating Customer
st.subheader("Rating Customer By Service")
st.markdown(f"Rating Average  : **{df_rating_service.mean():.2f}**")
    
plt.figure(figsize=(16, 8))
sns.barplot(
            x=rating_service.index, 
            y=rating_service.values, 
            order=rating_service.index,
            palette=["#4b7bb5" if score == max_score else "#D3D3D3" for score in rating_service.index]    
            )

plt.title("Rating customers for service", fontsize=15)
plt.xlabel("Rating")
plt.ylabel("Customer")
plt.xticks(fontsize=15)
st.pyplot(plt)


#RFM
st.subheader("RFM Best Value")

colors = ["#4b7bb5", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

tab1, tab2, tab3 = st.tabs(["Recency", "Frequency", "Monetary"])

with tab1:
    average_recency_days = rfm['Recency'].mean()
    average_recency_months = average_recency_days / 30
    st.markdown(f"**Rata-rata Recency:** {average_recency_months:.2f} bulan")

    plt.figure(figsize=(16, 8))
    sns.barplot(
        y="Recency", 
        x="customer_id", 
        data=rfm.sort_values(by="Recency", ascending=True).head(5), 
        palette=colors,
        
        )
    plt.title("By Recency (Day)", loc="center", fontsize=18)
    plt.ylabel('')
    plt.xlabel("customer")
    plt.tick_params(axis ='x', labelsize=15)
    plt.xticks([])
    st.pyplot(plt)

with tab2:
    average_frequency = rfm['Frequency'].mean()
    st.markdown(f"**Rata-rata Frequency:** {average_frequency:.2f} kali")

    plt.figure(figsize=(16, 8))
    sns.barplot(
        y="Frequency", 
        x="customer_id", 
        data=rfm.sort_values(by="Frequency", ascending=False).head(5), 
        palette=colors,
        
        )
    plt.ylabel('')
    plt.xlabel("customer")
    plt.title("By Frequency", loc="center", fontsize=18)
    plt.tick_params(axis ='x', labelsize=15)
    plt.xticks([])
    st.pyplot(plt)

with tab3:
    average_monetary = rfm['Monetary'].mean()
    st.markdown(f"**Rata-rata Monetary:** ${average_monetary:.2f}")

    plt.figure(figsize=(16, 8))
    sns.barplot(
        y="Monetary", 
        x="customer_id", 
        data=rfm.sort_values(by="Monetary", ascending=False).head(5), 
        palette=colors,
        )
    plt.ylabel('')
    plt.xlabel("customer")
    plt.title("By Monetary", loc="center", fontsize=18)
    plt.tick_params(axis ='x', labelsize=15)
    plt.xticks([])
    st.pyplot(plt)


with st.expander("See explanation"):
    st.write(
        """RFM Analysis: Understanding Customer Behavior

RFM (Recency, Frequency, Monetary) analysis helps understand customer habits by dividing them into segments based on three metrics:

1. Recency

Average Recency: 9.7 months
Meaning: The average customer made their last purchase 9.7 months ago.
Interpretation: A low recency value indicates more recent purchase activity, signaling positive customer engagement.

2. Frequency

Average Frequency: 1 time
Meaning: The average customer makes one purchase.
Interpretation: Transaction frequency is low. This number can be interpreted differently depending on the business context.

3. Monetary

Average Monetary: AUD 143.54
Meaning: The average customer spends AUD 143.54 per transaction.
Interpretation: A high monetary value indicates that customers in this segment tend to spend more per transaction.

Conclusion:
This segment consists of customers who made their last purchase 9.5 months ago with a frequency of one time and an average value of AUD 143.54 per transaction.
The frequency of purchase is low, but the monetary value indicates that customers in this segment have the potential to spend high value.
        """
    )

st.caption('Copyright (C) Fithrotuz Zuhroh. 2024')
