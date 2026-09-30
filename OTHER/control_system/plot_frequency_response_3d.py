import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# ##################################################################
# ## DESCRIZIONE
# ##################################################################
# Questo script è una visualizzazione 3D della risposta in
# frequenza |H(jω)| (vedi 'plot_frequency_response_2d.py').
#
# Disegna la curva del modulo |H(jω)| sul piano complesso s,
# limitatamente all'asse immaginario (cioè dove σ=0).
#
# Serve per visualizzare la curva 2D (Modulo vs ω) come una
# curva nello spazio 3D (σ, ω, Modulo).
#
# ##################################################################
# ## COME USARE
# ##################################################################
# 1. Definisci i parametri e le F.d.T. G(s) e C(s) nella "Sezione 1",
#    esattamente come nello script 2D.
# 2. Esegui lo script.
# ##################################################################


# --- 1. Definizione del Sistema e Parametri ---

# Parametri
a = 9.0
K = 3.0

# Intervallo di pulsazione ω (rad/s) da analizzare
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


# --- 3. Plotting 3D ---

# Creiamo la figura 3D
fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111, projection='3d')

# Disegna il piano grigio (piano sigma = 0)
sigma_plane = np.zeros((2, 2))
omega_plane_coords = np.array([[min(omega), max(omega)], [min(omega), max(omega)]])
z_plane = np.zeros((2, 2))
ax.plot_surface(sigma_plane, omega_plane_coords, z_plane, color='lightgray', alpha=0.3)

# Disegna la curva rossa |H(jω)| sul piano sigma=0
ax.plot(
    np.zeros_like(omega),   # sigma = 0
    omega,                  # ω variabile
    H_mag,                  # |H_dy(jω)|
    color='red',
    linewidth=2,
    label=r'$|\,H_{dy}(j\omega)\,|$'
)

# Metti un marker blu nel punto (σ=0, ω=3, |H|=1)
ax.scatter(
    [0], [omega_point], [mag_point],
    color='blue',
    s=50,
    label=rf'$(\sigma=0,\;\omega={omega_point},\;|H|={mag_point})$'
)

# Etichette e titolo
ax.set_xlabel(r'$\sigma$ (Re$\{s\}$)', fontsize=10)
ax.set_ylabel(r'$\omega$ (Im$\{s\}$)', fontsize=10)
ax.set_zlabel(r'$|H_{dy}(j\omega)|$', fontsize=10)
ax.set_title(r'Risposta $|H_{dy}(j\omega)|$ sul piano $\sigma=0$', fontsize=11)

# Impostiamo i limiti degli assi
ax.set_xlim(-0.5, 0.5)
ax.set_ylim(0, max(omega))
ax.set_zlim(0, np.max(H_mag)*1.1)

ax.legend(loc='upper left')
plt.tight_layout()
plt.show()