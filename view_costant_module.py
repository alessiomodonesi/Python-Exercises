import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# ----------------------------
#  Parametri del problema
# ----------------------------
a = 9
K = 3

# 1. Intervallo di frequenza (evitiamo omega=0 per non dividere per zero)
omega = np.linspace(0.001, 5, 400)

# 2. Calcolo della risposta in frequenza H_dy(jω)
s = 1j * omega
G = (s**2 + s + 12) / (s**2 + a)  # G(jω)
C = K / s                         # C(jω) = K/(jω)
H_dy = G / (1 + C * G)            # H_dy(jω)
H_mag = np.abs(H_dy)              # modulo di H_dy(jω)

# 3. Costruiamo il "piano" sigma = 0 (rettangolo in omega ∈ [0,5], z = 0)
sigma_plane = np.zeros((2, 2))
omega_plane = np.array([[0, 5], [0, 5]])
z_plane = np.zeros((2, 2))

# 4. Creiamo la figura 3D
fig = plt.figure(figsize=(7, 5))
ax = fig.add_subplot(111, projection='3d')

# 5. Disegniamo il piano sigma = 0 (in grigio chiaro, semitrasparente)
ax.plot_surface(sigma_plane, omega_plane, z_plane, color='lightgray', alpha=0.3)

# 6. Disegniamo la curva reale di |H_dy(jω)| in rosso, sul piano sigma=0
ax.plot(
    np.zeros_like(omega),   # sigma = 0
    omega,                  # ω variabile tra 0.001 e 5
    H_mag,                  # |H_dy(jω)|
    color='red',
    linewidth=2,
    label=r'$|\,H_{dy}(j\omega)\,|$'
)

# 7. Mettiamo un marker blu in (σ=0, ω=3, |H|=1)
ax.scatter(
    [0], [3], [1],
    color='blue',
    s=50,
    label=r'$(\sigma=0,\;\omega=3,\;|H|=1)$'
)

# 8. Etichette e titolo
ax.set_xlabel(r'$\sigma$ (Re$\{s\}$)', fontsize=10)
ax.set_ylabel(r'$\omega$ (Im$\{s\}$)', fontsize=10)
ax.set_zlabel(r'$|H_{dy}(j\omega)|$', fontsize=10)
ax.set_title(r'Piano $\sigma=0$ e risposta reale $|H_{dy}(j\omega)|$', fontsize=11)

# 9. Impostiamo i limiti degli assi
ax.set_xlim(-0.5, 0.5)        # σ vicino a zero
ax.set_ylim(0, 5)             # ω da 0 a 5
ax.set_zlim(0, np.max(H_mag)*1.1)   # modulo da 0 a un poco sopra il massimo

# 10. Legenda
ax.legend(loc='upper left')

plt.tight_layout()
plt.show()
