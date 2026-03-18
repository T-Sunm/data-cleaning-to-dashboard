import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sales Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# Đường dẫn đến dataset (tương đối từ file này)
DATA_PATH = Path(__file__).parent / "notebooks" / "sales_data5.csv"

# ─── Data Loading ─────────────────────────────────────────────────────────────
@st.cache_data
def load_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        st.error(f"❌ Không tìm thấy file dữ liệu tại: {DATA_PATH}")
        st.stop()
        
    df = pd.read_csv(DATA_PATH, parse_dates=["OrderDate"])
    # Tạo cột tháng để vẽ line chart trend
    df["YearMonth"] = df["OrderDate"].dt.to_period("M").dt.to_timestamp()
    return df

# ─── Sidebar Filters ──────────────────────────────────────────────────────────
def render_filters(df: pd.DataFrame) -> pd.DataFrame:
    with st.sidebar:
        st.title("📊 Sales Dashboard")
        st.markdown("---")
        st.header("🔎 Bộ lọc dữ liệu")

        regions = st.multiselect(
            "Chọn Khu vực (Region):",
            options=sorted(df["Region"].unique()),
            default=sorted(df["Region"].unique())
        )
        
        categories = st.multiselect(
            "Chọn Danh mục (Category):",
            options=sorted(df["Category"].unique()),
            default=sorted(df["Category"].unique())
        )

        st.markdown("---")
        st.info(f"💡 Đang hiển thị dữ liệu từ {df['OrderDate'].min().date()} đến {df['OrderDate'].max().date()}")
        st.caption(f"Tổng số bản ghi: {len(df):,}")

    # Apply filtering
    filtered = df[df["Region"].isin(regions) & df["Category"].isin(categories)]
    return filtered

# ─── KPI Row ──────────────────────────────────────────────────────────────────
def render_kpis(df: pd.DataFrame):
    total_sales    = df["Sales"].sum()
    total_profit   = df["Profit"].sum()
    total_qty      = df["Quantity"].sum()
    profit_margin  = (total_profit / total_sales * 100) if total_sales != 0 else 0

    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.metric("💰 Tổng Doanh thu", f"${total_sales:,.2f}")
    with c2:
        st.metric("📈 Tổng Lợi nhuận", f"${total_profit:,.2f}", 
                  delta=f"Margin: {profit_margin:.1f}%")
    with c3:
        st.metric("📦 Tổng Số lượng", f"{int(total_qty):,} units")

# ─── Charts Implementation ────────────────────────────────────────────────────
def chart_monthly_trend(df: pd.DataFrame):
    monthly = (df.groupby("YearMonth")["Sales"]
                 .sum()
                 .reset_index()
                 .rename(columns={"YearMonth": "Month", "Sales": "Revenue"}))
    
    fig = px.line(
        monthly, x="Month", y="Revenue",
        title="📅 Xu hướng Doanh thu theo Tháng",
        markers=True,
        line_shape="spline",
        render_mode="svg" # Dùng svg để chart mượt hơn trong streamlit
    )
    fig.update_layout(xaxis_title="", yaxis_title="Doanh thu ($)", hovermode="x unified")
    return fig

def chart_region_bar(df: pd.DataFrame):
    region_df = (df.groupby("Region")["Sales"]
                   .sum()
                   .sort_values(ascending=True) # Để bar lớn nhất ở trên khi dùng ngang
                   .reset_index())
    
    fig = px.bar(
        region_df, x="Sales", y="Region",
        orientation="h",
        title="🗺️ Doanh thu theo Khu vực",
        color="Sales",
        color_continuous_scale="Blues",
        text_auto="$.2s"
    )
    fig.update_layout(showlegend=False, coloraxis_showscale=False, yaxis_title="")
    return fig

def chart_category_pie(df: pd.DataFrame):
    cat_df = df.groupby("Category")["Sales"].sum().reset_index()
    
    fig = px.pie(
        cat_df, names="Category", values="Sales",
        title="🥧 Tỷ lệ Doanh thu theo Danh mục",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return fig

def chart_sales_profit_scatter(df: pd.DataFrame):
    fig = px.scatter(
        df, x="Sales", y="Profit",
        color="Category",
        hover_data=["Region", "ProductName", "Quantity"],
        title="🔵 Tương quan Sales vs Profit",
        opacity=0.6,
        color_discrete_sequence=px.colors.qualitative.Vivid
    )
    # Thêm đường break-even (lợi nhuận = 0)
    fig.add_hline(y=0, line_dash="dash", line_color="gray", 
                  annotation_text="Điểm hòa vốn", annotation_position="bottom right")
    return fig

# ─── Main Application ─────────────────────────────────────────────────────────
def main():
    # Load data
    df = load_data()
    
    # Render Sidebar & Get Filtered Data
    filtered = render_filters(df)

    # Header
    st.header("🏪 Hệ thống Phân tích Kinh doanh (Middle Exam)")
    st.markdown(f"Phân tích hiệu suất bán hàng của **{len(filtered):,}** đơn hàng.")

    if filtered.empty:
        st.warning("⚠️ Không có dữ liệu để hiển thị. Vui lòng kiểm tra lại bộ lọc.")
        st.stop()

    # Section 1: KPI Cards
    st.markdown("### 📊 Chỉ số Hiệu năng Chính (KPIs)")
    render_kpis(filtered)
    st.divider()

    # Section 2: Trend & Region Breakdown
    col1, col2 = st.columns([3, 2])
    with col1:
        st.plotly_chart(chart_monthly_trend(filtered), use_container_width=True)
    with col2:
        st.plotly_chart(chart_region_bar(filtered), use_container_width=True)

    # Section 3: Category Share & Sales Correlation
    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(chart_category_pie(filtered), use_container_width=True)
    with col4:
        st.plotly_chart(chart_sales_profit_scatter(filtered), use_container_width=True)

    # Section 4: Data Table
    with st.expander("🗂️ Xem chi tiết bảng dữ liệu (Raw Data)"):
        st.dataframe(
            filtered[["OrderDate", "Region", "Category", "ProductName", "Sales", "Quantity", "Profit"]].sort_values("OrderDate", ascending=False),
            use_container_width=True,
            hide_index=True
        )
        st.caption("Ghi chú: Dữ liệu được sắp xếp theo thời gian mới nhất.")

if __name__ == "__main__":
    main()
