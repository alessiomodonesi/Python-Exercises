import numpy as np
import matplotlib.pyplot as plt

# ##################################################################
# ## DESCRIZIONE
# ##################################################################
# Questo script calcola e disegna il modulo della risposta
# in frequenza |H(jω)| di un sistema in anello chiuso.
#
# Il sistema è definito da:
# - G(s): Funzione di trasferimento del processo
# - C(s): Funzione di trasferimento del controllore
#
# La funzione di trasferimento in anello chiuso (es. dal disturbo
# all'uscita, H_dy) è calcolata come:
#   H_dy(s) = G(s) / (1 + C(s) * G(s))
#
# Lo script valuta questa H(jω) e ne traccia il modulo |H_dy(jω)|
# in funzione di ω.
#
# ##################################################################
# ## COME USARE
# ##################################################################
# 1. Definisci i parametri (es. 'a', 'K') nella "Sezione 1".
# 2. Definisci le F.d.T. G(s) e C(s) (come funzioni di 's').
# 3. Regola l'intervallo di pulsazioni 'omega' da analizzare.
# 4. Esegui lo script.
# ##################################################################


# --- 1. Definizione del Sistema e Parametri ---

# Parametri
a = 9.0
K = 3.0

# Intervallo di pulsazione ω (rad/s) da analizzare
# (evitiamo 0 esatto se c'è un integratore 1/s)
omega = np.linspace(0.001, 5, 400)

# Punto specifico da evidenziare (opzionale)
omega_point = 3.0
mag_point = 1.0


# --- 2. Calcolo della Risposta in Frequenza ---
# Definiamo 's' come 'j*omega' per la valutazione in frequenza
s = 1j * omega

# Funzioni di Trasferimento (definite dall'utente)
G = (s**2 + s + 12) / (s**2 + a)     # G(jω)
C = K / s                            # C(jω) = K/(jω)

# Calcolo della F.d.T. in anello chiuso H_dy(jω)
H_dy = G / (1 + C * G)

# Calcolo del modulo (magnitudine)
H_mag = np.abs(H_dy)                 # |H_dy(jω)|


# --- 3. Plotting 2D (Modulo vs Frequenza) ---
plt.figure(figsize=(7, 4))
plt.plot(omega, H_mag, color='red', linewidth=2, label=r'$|H_{dy}(j\omega)|$')

# Segna un punto di interesse (opzionale)
plt.scatter([omega_point], [mag_point], color='blue', s=50, zorder=5,
            label=rf'$(\omega={omega_point},\;|H|={mag_point})$')

# Linea di riferimento a magnitudine 1 (0 dB)
plt.axhline(1, color='gray', linestyle='--', linewidth=1)

# Etichette e titolo
plt.xlabel(r'$\omega\,$ (rad/s)')
plt.ylabel(r'$|H_{dy}(j\omega)|$ (Modulo)')
plt.title(r'Modulo della Risposta in Frequenza $|H_{dy}(j\omega)|$')
plt.xlim(0, max(omega))
plt.ylim(0, max(H_mag)*1.1)
plt.legend(loc='upper right')
plt.grid(alpha=0.3)

plt.tight_layout()
plt.show()