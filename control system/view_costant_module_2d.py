import numpy as np
import matplotlib.pyplot as plt

# ----------------------------
#  Parametri del problema
# ----------------------------
a = 9
K = 3

# 1. Intervallo di frequenza ω (evitiamo esattamente 0 per non dividere per zero)
omega = np.linspace(0.001, 5, 400)

# 2. Calcolo di G(jω) e C(jω)
s = 1j * omega
G = (s**2 + s + 12) / (s**2 + a)     # G(jω)
C = K / s                            # C(jω) = K/(jω)

# 3. Funzione di trasferimento H_dy(jω)
H_dy = G / (1 + C * G)
H_mag = np.abs(H_dy)                 # |H_dy(jω)|

# 4. Creiamo il grafico 2D "modulo vs frequenza"
plt.figure(figsize=(7, 4))
plt.plot(omega, H_mag, color='red', linewidth=2, label=r'$|H_{dy}(j\omega)|$')

# 5. Segniamo il punto (ω=3, |H|=1)
plt.scatter([3], [1], color='blue', s=50, zorder=5,
            label=r'$(\omega=3,\;|H|=1)$')

# 6. Aggiungiamo una linea orizzontale a y=1 per riferimento
plt.axhline(1, color='gray', linestyle='--', linewidth=1)

# 7. Etichette, titolo e legenda
plt.xlabel(r'$\omega\,$ (rad/s)')
plt.ylabel(r'$|H_{dy}(j\omega)|$')
plt.title(r'Andamento di $|H_{dy}(j\omega)|$ in funzione di $\omega$')
plt.xlim(0, 5)
plt.ylim(0, max(H_mag)*1.1)
plt.legend(loc='upper right')
plt.grid(alpha=0.3)

plt.tight_layout()
plt.show()
