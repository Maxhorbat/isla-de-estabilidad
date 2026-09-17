import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from src.physics_engine import generate_nuclear_chart, calculate_fusion_cross_section

st.set_page_config(page_title="Isla de Estabilidad V2.0", layout="wide", page_icon="⚛️")

st.title("⚛️ Explorador Interactivo: Isla de Estabilidad V2.0")
st.markdown("Modelo teoricocomputacional para análisis de núcleos superpesados y secciones eficaces de fusión.")

tab1, tab2 = st.tabs(["🗺️ Mapa Nuclear Z-N (Estructura)", "💥 Simulación de Fusión-Evaporación"])

with tab1:
    st.sidebar.header("Parámetros del Dominio Z-N")
    z_min, z_max = st.sidebar.slider("Rango de Z", 114, 128, (119, 126))
    n_min, n_max = st.sidebar.slider("Rango de N", 150, 210, (160, 200))
    
    df_chart = generate_nuclear_chart(z_min, z_max, n_min, n_max)
    
    variable_view = st.selectbox("Variable a visualizar en el mapa de calor:", 
                                 ["B_f_MeV", "dE_shell_MeV", "B_por_A", "log10_TSF_s", "log10_Talpha_s"])
    
    pivot_table = df_chart.pivot(index="N", columns="Z", values=variable_view)
    
    fig = px.imshow(pivot_table, origin="lower", labels=dict(x="Protones (Z)", y="Neutrones (N)", color=variable_view),
                    title=f"Distribución 2D de {variable_view} en la Isla de Estabilidad",
                    color_continuous_scale="Viridis")
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(df_chart.sort_values("B_f_MeV", ascending=False).head(10))

with tab2:
    st.header("Simulador de Secciones Eficaces ($\sigma_{ER}$)")
    
    col1, col2 = st.columns(2)
    with col1:
        reaccion = st.selectbox("Seleccionar Reacción de Fusión:", [
            "50Ti + 249Bk -> Z=119",
            "50Ti + 249Cf -> Z=120",
            "54Cr + 248Cm -> Z=120",
            "48Ca + 249Cf -> 297Og (Benchmark)"
        ])
    
    rx_dict = {
        "50Ti + 249Bk -> Z=119": (22, 50, 97, 249),
        "50Ti + 249Cf -> Z=120": (22, 50, 98, 249),
        "54Cr + 248Cm -> Z=120": (24, 54, 96, 248),
        "48Ca + 249Cf -> 297Og (Benchmark)": (20, 48, 98, 249)
    }
    
    Z1, A1, Z2, A2 = rx_dict[reaccion]
    df_fusion, V_C = calculate_fusion_cross_section(Z1, A1, Z2, A2)
    
    with col2:
        st.metric("Barrera de Coulomb (V_C)", f"{V_C:.2f} MeV")
        pico_max = df_fusion.loc[df_fusion["sig_ER_pb"].idxmax()]
        st.metric("Pico Óptimo (sig_ER)", f"{pico_max['sig_ER_pb']:.2f} pb", delta=f"E* = {pico_max['E_star_MeV']:.1f} MeV")
    
    fig_rx = go.Figure()
    fig_rx.add_trace(go.Scatter(x=df_fusion["E_star_MeV"], y=df_fusion["sig_ER_pb"], mode="lines+markers", name="sig_ER (pb)"))
    fig_rx.update_layout(title=f"Ventana de Energía para {reaccion}", xaxis_title="Energía de Excitación E* (MeV)", yaxis_title="Sección Eficaz sig_ER (pb)")
    st.plotly_chart(fig_rx, use_container_width=True)

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from src.physics_engine import generate_nuclear_chart, calculate_fusion_cross_section, generate_decay_chain

st.set_page_config(page_title="Isla de Estabilidad V2.1", layout="wide", page_icon="⚛️")

st.title("⚛️ Explorador Interactivo: Isla de Estabilidad V2.1")

tab1, tab2, tab3, tab4 = st.tabs([
    "🗺️ Mapa Nuclear Z-N", 
    "🌋 Superficie 3D de Estabilidad", 
    "💥 Fusión-Evaporación", 
    "📉 Cadenas de Desintegración Alpha"
])

# TAB 1: Mapa Z-N
with tab1:
    df_chart = generate_nuclear_chart(119, 126, 160, 200)
    pivot_table = df_chart.pivot(index="N", columns="Z", values="B_f_MeV")
    fig1 = px.imshow(pivot_table, origin="lower", labels=dict(x="Z", y="N", color="B_f (MeV)"),
                    color_continuous_scale="Viridis")
    st.plotly_chart(fig1, use_container_width=True)

# TAB 2: Superficie 3D
with tab2:
    st.header("Superficie 3D de la Barrera de Fisión ($B_f$)")
    df_chart = generate_nuclear_chart(118, 128, 160, 200)
    pivot_3d = df_chart.pivot(index="N", columns="Z", values="B_f_MeV")
    
    fig_3d = go.Figure(data=[go.Surface(z=pivot_3d.values, x=pivot_3d.columns, y=pivot_3d.index, colorscale="Magma")])
    fig_3d.update_layout(title="Cima de Estabilidad alrededor de N=184",
                        scene=dict(xaxis_title="Protones (Z)", yaxis_title="Neutrones (N)", zaxis_title="B_f (MeV)"))
    st.plotly_chart(fig_3d, use_container_width=True)

# TAB 3: Fusión-Evaporación
with tab3:
    st.header("Simulación de Fusión")
    df_fusion, V_C = calculate_fusion_cross_section(22, 50, 97, 249)
    fig_rx = px.line(df_fusion, x="E_star_MeV", y="sig_ER_pb", title="Ventana 50Ti + 249Bk")
    st.plotly_chart(fig_rx, use_container_width=True)

# TAB 4: Cadenas Alpha
with tab4:
    st.header("Simulador de Cadenas de Desintegración $\alpha$")
    z_in = st.number_input("Z Inicial", min_value=114, max_value=126, value=120)
    n_in = st.number_input("N Inicial", min_value=160, max_value=200, value=184)
    
    df_chain = generate_decay_chain(z_in, n_in)
    st.dataframe(df_chain, use_container_width=True)
    
    fig_chain = px.line(df_chain, x="N", y="Z", text="Nuclido", markers=True, title=f"Línea de Decaimiento desde Z={z_in}, N={n_in}")
    fig_chain.update_traces(textposition="top center")
    st.plotly_chart(fig_chain, use_container_width=True)