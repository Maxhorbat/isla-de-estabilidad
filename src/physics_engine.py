from pathlib import Path
import numpy as np
import pandas as pd

# Parámetros SEMF V1.1 -> V2.0
AV, AS, AC, AA, PC = 15.75, 17.80, 0.711, 23.70, 34.0
HBAR_OMEGA, R_0, E_CHARGE_SQ = 3.0, 1.16, 1.44

def pairing(Z, N):
    if Z % 2 == 0 and N % 2 == 0:
        return +PC / ((Z + N) ** 0.75)
    elif Z % 2 == 1 and N % 2 == 1:
        return -PC / ((Z + N) ** 0.75)
    return 0.0

def binding_energy_macro(Z, N):
    A = Z + N
    return (AV*A - AS*(A**(2/3)) - AC*Z*(Z-1)/(A**(1/3)) - AA*((A-2*Z)**2)/A + pairing(Z, N))

def shell_correction(Z, N):
    dZ = min(abs(Z - 120), abs(Z - 126))
    dN = abs(N - 184)
    return 8.5 * np.exp(-0.08 * (dZ**2 + dN**2))

def generate_nuclear_chart(z_min=119, z_max=126, n_min=160, n_max=200):
    filas = []
    for Z in range(z_min, z_max + 1):
        for N in range(n_min, n_max + 1):
            A = Z + N
            B_m = binding_energy_macro(Z, N)
            dE_s = shell_correction(Z, N)
            B_tot = B_m + dE_s
            B_f = dE_s  # B_f_macr ~ 0
            log10_TSF = -21.0 + 4.2 * B_f
            Q_a = (binding_energy_macro(2, 2) + 28.3) - (B_tot - binding_energy_macro(Z-2, N-2))
            log10_Ta = (1.66 * Z - 8.5) / np.sqrt(max(0.1, Q_a)) - 32.0 if Q_a > 0 else 99.0
            
            filas.append({
                "Z": Z, "N": N, "A": A,
                "B_por_A": B_tot / A,
                "dE_shell_MeV": dE_s,
                "B_f_MeV": B_f,
                "log10_TSF_s": log10_TSF,
                "log10_Talpha_s": log10_Ta,
                "Modo_Dominante": "SF" if log10_TSF < log10_Ta else "Alpha"
            })
    return pd.DataFrame(filas)

def calculate_fusion_cross_section(Z1, A1, Z2, A2, E_star_range=np.linspace(25, 55, 31)):
    prod_Z = Z1 * Z2
    A_CN = A1 + A2
    a_param = A_CN / 10.0
    R_B = R_0 * (A1**(1/3) + A2**(1/3)) + 1.5
    V_C = (E_CHARGE_SQ * prod_Z) / R_B
    
    # Factor P_CN con corrección por proyectil esférico 48Ca
    k_factor = 1820.0 if (Z1 == 20 and A1 == 48) else 1750.0
    P_CN = np.exp(-((prod_Z / k_factor)**2))
    
    filas = []
    for E_star in E_star_range:
        T = np.sqrt(E_star / a_param)
        E_cm = V_C + (E_star - 30.0)
        sig_cap = (10 * HBAR_OMEGA / (2 * max(100, E_cm))) * (R_B**2) * np.log(1 + np.exp(2 * np.pi * (E_cm - V_C) / HBAR_OMEGA))
        gamma_ratio = np.exp((7.5 - 6.2) / max(0.1, T))
        W_surv = (gamma_ratio / (1 + gamma_ratio))**3
        sig_ER_pb = sig_cap * P_CN * W_surv * 1e9
        
        filas.append({
            "E_star_MeV": E_star,
            "T_MeV": T,
            "E_cm_MeV": E_cm,
            "sig_cap_mb": sig_cap,
            "P_CN": P_CN,
            "W_surv": W_surv,
            "sig_ER_pb": sig_ER_pb
        })
    return pd.DataFrame(filas), V_C

def generate_decay_chain(z_start, n_start, steps=6):
    """
    Simula la cadena de desintegración alfa desde un núcleo superpesado inicial.
    Cada emisión alfa reduce Z en 2 y N en 2 (A en 4).
    """
    chain = []
    z_curr, n_curr = z_start, n_start
    
    for i in range(steps):
        a_curr = z_curr + n_curr
        b_tot = binding_energy_macro(z_curr, n_curr) + shell_correction(z_curr, n_curr)
        
        # Energía Q_alpha
        b_child = binding_energy_macro(z_curr - 2, n_curr - 2) + shell_correction(z_curr - 2, n_curr - 2)
        q_alpha = (binding_energy_macro(2, 2) + 28.3) - (b_tot - b_child)
        
        # Vida media T_alpha (Viola-Seaborg)
        log10_Ta = (1.66 * z_curr - 8.5) / np.sqrt(max(0.1, q_alpha)) - 32.0 if q_alpha > 0 else 99.0
        
        chain.append({
            "Paso": i + 1,
            "Nuclido": f"^{{{a_curr}}}{z_curr}",
            "Z": z_curr,
            "N": n_curr,
            "A": a_curr,
            "Q_alpha_MeV": round(q_alpha, 2),
            "log10_Talpha_s": round(log10_Ta, 2),
            "T_estimada": f"10^({log10_Ta:.1f}) s"
        })
        
        # Siguiente elemento por emisión alfa
        z_curr -= 2
        n_curr -= 2
        if z_curr < 100:
            break
            
    return pd.DataFrame(chain)