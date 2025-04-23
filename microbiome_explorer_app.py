import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Microbiome Explorer", layout="wide")

# Load the cleaned dataset
reference_df = pd.read_csv("disbiome_with_titles.csv")

st.title("Microbiome–Host Association Explorer")
st.markdown("Upload a CSV of microbes or explore the full dataset. Filter, sort by dropdown, and click study titles to explore PubMed.")

# Choose mode
mode = st.radio("Choose input method:", ["Upload CSV of Microbes", "Explore Entire Dataset"])

if mode == "Upload CSV of Microbes":
    uploaded_file = st.file_uploader("📤 Upload a CSV with a column named 'Microbe'", type="csv")
    
    if uploaded_file is not None:
        input_df = pd.read_csv(uploaded_file)
        input_df["Microbe"] = input_df["Microbe"].str.strip()

        if "Microbe" not in input_df.columns:
            st.error("Your CSV must contain a column named 'Microbe'")
            st.stop()

        uploaded_microbes = input_df["Microbe"].unique().tolist()
        working_df = reference_df[reference_df["Microbe"].apply(
            lambda ref: any(ref.lower().startswith(q.lower()) for q in uploaded_microbes)
        )]

        matched_microbes = set()
        for q in uploaded_microbes:
            matched = [ref for ref in reference_df["Microbe"].unique() if ref.lower().startswith(q.lower())]
            matched_microbes.update(matched)

        unmatched = [m for m in uploaded_microbes if not any(ref.lower().startswith(m.lower()) for ref in reference_df["Microbe"])]

        if working_df.empty:
            st.error("None of your microbes were found in the reference.")
            st.stop()

        if unmatched:
            st.warning(f"{len(unmatched)} microbes not found in the reference dataset.")
            st.dataframe(pd.DataFrame(unmatched, columns=["Unmatched Microbes"]))
            st.download_button("📥 Download Unmatched", pd.DataFrame(unmatched).to_csv(index=False).encode("utf-8"), file_name="unmatched_microbes.csv")

        st.success(f"Matched {len(matched_microbes)} microbes → {len(working_df)} entries found.")
    else:
        st.warning("Please upload a CSV file to continue.")
        st.stop()
else:
    working_df = reference_df.copy()
    st.success(f"Loaded full dataset: {working_df['Microbe'].nunique()} microbes, {len(working_df)} entries")

# Sidebar filters
with st.sidebar:
    st.header("🔍 Filter Results")

    microbes = sorted(working_df["Microbe"].dropna().unique())
    conditions = sorted(working_df["Condition"].dropna().unique())
    effects = sorted(working_df["Effect"].dropna().unique())
    samples = sorted(working_df["Sample Type"].dropna().unique())
    methods = sorted(working_df["Method"].dropna().unique())

    selected_microbe = st.multiselect("Microbe", microbes)
    selected_condition = st.multiselect("Condition", conditions)
    selected_effect = st.multiselect("Effect", effects)
    selected_sample = st.multiselect("Sample Type", samples)
    selected_method = st.multiselect("Method", methods)

# Filter logic
filtered_df = working_df.copy()
if selected_microbe:
    filtered_df = filtered_df[filtered_df["Microbe"].isin(selected_microbe)]
if selected_condition:
    filtered_df = filtered_df[filtered_df["Condition"].isin(selected_condition)]
if selected_effect:
    filtered_df = filtered_df[filtered_df["Effect"].isin(selected_effect)]
if selected_sample:
    filtered_df = filtered_df[filtered_df["Sample Type"].isin(selected_sample)]
if selected_method:
    filtered_df = filtered_df[filtered_df["Method"].isin(selected_method)]

# Sort dropdown
sort_column = st.selectbox("🔃 Sort results by:", ["None", "Microbe", "Condition", "Effect", "Sample Type", "Host", "Method"])

if sort_column != "None":
    filtered_df = filtered_df.sort_values(by=sort_column)


# Create clickable PubMed links
filtered_df["Study Link"] = filtered_df.apply(
    lambda row: f'<a href="{row["PubMed Link"]}" target="_blank">{row["Study Title"]}</a>', axis=1
)

# Display styled table with clickable link
st.markdown("### 📄 Sorted Table with Clickable PubMed Links")

st.markdown("""
<style>
table {
    width: 100%;
    border-collapse: collapse;
}
thead th {
    background-color: #1e1e1e;
    color: white;
    text-align: left;
    padding: 8px;
}
tbody td {
    padding: 8px;
}
</style>
""", unsafe_allow_html=True)

st.markdown(filtered_df[[
    "Microbe", "Condition", "Effect", "Sample Type", "Host", "Method", "Study Link"
]].rename(columns={"Study Link": "PubMed Study"}).to_html(escape=False, index=False), unsafe_allow_html=True)

# Download button
st.download_button("📥 Download Filtered Data", filtered_df.to_csv(index=False).encode("utf-8"), "filtered_results.csv")

# Visualizations
if not filtered_df.empty:
    st.markdown("### 📊 Visual Insights")

    effect_counts = filtered_df["Effect"].value_counts().reset_index()
    effect_counts.columns = ["Effect", "Count"]
    fig1 = px.bar(effect_counts, x="Effect", y="Count", title="Distribution by Effect")
    st.plotly_chart(fig1, use_container_width=True)

    condition_counts = filtered_df["Condition"].value_counts().head(10).reset_index()
    condition_counts.columns = ["Condition", "Count"]
    fig2 = px.bar(condition_counts, x="Condition", y="Count", title="Top 10 Conditions")
    st.plotly_chart(fig2, use_container_width=True)

    sample_counts = filtered_df["Sample Type"].value_counts().reset_index()
    sample_counts.columns = ["Sample Type", "Count"]
    fig3 = px.pie(sample_counts, names="Sample Type", values="Count", title="Sample Types")
    st.plotly_chart(fig3, use_container_width=True)

    microbe_counts = filtered_df["Microbe"].value_counts().head(10).reset_index()
    microbe_counts.columns = ["Microbe", "Count"]
    fig4 = px.bar(microbe_counts, x="Microbe", y="Count", title="Top 10 Microbes")
    st.plotly_chart(fig4, use_container_width=True)
