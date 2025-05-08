import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime, timedelta
from .sku_mapper import SkuMapper, InventoryType, Warehouse

class InventoryDashboard:
    """Interactive dashboard for inventory management."""
    
    def __init__(self):
        self.mapper = None
        self.data = None
        self.impact_data = None
        
    def load_data(self, mapping_file: str, data_file: str):
        """Load mapping and inventory data."""
        try:
            self.mapper = SkuMapper(mapping_file)
            if data_file.endswith('.csv'):
                self.data = pd.read_csv(data_file)
            elif data_file.endswith(('.xlsx', '.xls')):
                self.data = pd.read_excel(data_file)
            elif data_file.endswith('.json'):
                self.data = pd.read_json(data_file)
            
            # Process data with SKU mapper
            self.data = self.mapper.process_inventory_data(
                self.data,
                'SKU',
                'Marketplace' if 'Marketplace' in self.data.columns else None
            )
            
            # Calculate inventory impact
            self.impact_data = self.mapper.calculate_inventory_impact(
                self.data,
                'Quantity',
                'Warehouse' if 'Warehouse' in self.data.columns else None
            )
            
            return True
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            return False

def main():
    st.set_page_config(
        page_title="Inventory Management Dashboard",
        page_icon="📦",
        layout="wide"
    )
    
    st.title("📦 Inventory Management Dashboard")
    
    # Initialize dashboard
    dashboard = InventoryDashboard()
    
    # Sidebar for file uploads
    with st.sidebar:
        st.header("Data Upload")
        mapping_file = st.file_uploader("Upload Mapping File", type=['csv', 'json'])
        data_file = st.file_uploader("Upload Inventory Data", type=['csv', 'xlsx', 'json'])
        
        if mapping_file and data_file:
            if st.button("Load Data"):
                with st.spinner("Loading data..."):
                    if dashboard.load_data(mapping_file, data_file):
                        st.success("Data loaded successfully!")
    
    if dashboard.data is not None and dashboard.impact_data is not None:
        # Create tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Overview", 
            "🏪 Warehouse Status", 
            "📈 Trends", 
            "⚠️ Alerts"
        ])
        
        with tab1:
            st.header("Inventory Overview")
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                total_skus = len(dashboard.data['MSKU'].unique())
                st.metric("Total SKUs", total_skus)
            with col2:
                total_quantity = dashboard.data['Quantity'].sum()
                st.metric("Total Quantity", total_quantity)
            with col3:
                total_revenue = dashboard.data['Revenue'].sum()
                st.metric("Total Revenue", f"${total_revenue:,.2f}")
            with col4:
                avg_price = total_revenue / total_quantity if total_quantity > 0 else 0
                st.metric("Average Price", f"${avg_price:,.2f}")
            
            # Inventory by category
            st.subheader("Inventory by Category")
            category_data = dashboard.data.groupby('Category')['Quantity'].sum().reset_index()
            fig = px.pie(
                category_data,
                values='Quantity',
                names='Category',
                title='Inventory Distribution by Category'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Top products
            st.subheader("Top Products by Quantity")
            top_products = dashboard.data.groupby('MSKU')['Quantity'].sum().nlargest(10)
            fig = px.bar(
                top_products,
                title='Top 10 Products by Quantity',
                labels={'value': 'Quantity', 'index': 'MSKU'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.header("Warehouse Status")
            
            # Warehouse inventory levels
            warehouse_data = dashboard.impact_data.groupby('Warehouse')['Quantity'].sum().reset_index()
            fig = px.bar(
                warehouse_data,
                x='Warehouse',
                y='Quantity',
                title='Inventory Levels by Warehouse',
                color='Warehouse'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Inventory type distribution
            st.subheader("Inventory Type Distribution")
            type_data = dashboard.impact_data.groupby(['Warehouse', 'Type'])['Quantity'].sum().reset_index()
            fig = px.bar(
                type_data,
                x='Warehouse',
                y='Quantity',
                color='Type',
                title='Inventory Types by Warehouse',
                barmode='group'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Warehouse details table
            st.subheader("Warehouse Details")
            warehouse_details = dashboard.impact_data.pivot_table(
                values='Quantity',
                index='Warehouse',
                columns='Type',
                aggfunc='sum'
            ).fillna(0)
            st.dataframe(warehouse_details)
        
        with tab3:
            st.header("Inventory Trends")
            
            # Date range selector
            date_col = 'Date' if 'Date' in dashboard.data.columns else None
            if date_col:
                min_date = pd.to_datetime(dashboard.data[date_col]).min()
                max_date = pd.to_datetime(dashboard.data[date_col]).max()
                
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input(
                        "Start Date",
                        min_date,
                        min_value=min_date,
                        max_value=max_date
                    )
                with col2:
                    end_date = st.date_input(
                        "End Date",
                        max_date,
                        min_value=min_date,
                        max_value=max_date
                    )
                
                # Filter data by date range
                mask = (pd.to_datetime(dashboard.data[date_col]).dt.date >= start_date) & \
                       (pd.to_datetime(dashboard.data[date_col]).dt.date <= end_date)
                filtered_data = dashboard.data[mask]
                
                # Daily inventory trends
                st.subheader("Daily Inventory Trends")
                daily_data = filtered_data.groupby(date_col)['Quantity'].sum().reset_index()
                fig = px.line(
                    daily_data,
                    x=date_col,
                    y='Quantity',
                    title='Daily Inventory Changes'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Category trends
                st.subheader("Category Trends")
                category_trends = filtered_data.groupby([date_col, 'Category'])['Quantity'].sum().reset_index()
                fig = px.line(
                    category_trends,
                    x=date_col,
                    y='Quantity',
                    color='Category',
                    title='Category-wise Inventory Trends'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with tab4:
            st.header("Inventory Alerts")
            
            # Low stock alerts
            st.subheader("Low Stock Alerts")
            low_stock_threshold = st.slider(
                "Low Stock Threshold",
                min_value=0,
                max_value=100,
                value=10
            )
            
            low_stock = dashboard.impact_data[
                dashboard.impact_data['Quantity'] < low_stock_threshold
            ].sort_values('Quantity')
            
            if not low_stock.empty:
                st.dataframe(low_stock)
            else:
                st.success("No low stock alerts!")
            
            # Warehouse capacity alerts
            st.subheader("Warehouse Capacity Alerts")
            capacity_threshold = st.slider(
                "Capacity Threshold",
                min_value=0,
                max_value=1000,
                value=500
            )
            
            warehouse_capacity = dashboard.impact_data.groupby('Warehouse')['Quantity'].sum()
            high_capacity = warehouse_capacity[warehouse_capacity > capacity_threshold]
            
            if not high_capacity.empty:
                st.warning("The following warehouses are near capacity:")
                st.dataframe(high_capacity)
            else:
                st.success("No warehouse capacity alerts!")
            
            # Combo product alerts
            st.subheader("Combo Product Alerts")
            combo_products = dashboard.data[
                dashboard.data['Inventory_Type'] == 'combo'
            ]
            
            if not combo_products.empty:
                st.info("Combo products that need component review:")
                st.dataframe(combo_products[['MSKU', 'Components', 'Quantity']])
            else:
                st.success("No combo product alerts!")

if __name__ == "__main__":
    main() 