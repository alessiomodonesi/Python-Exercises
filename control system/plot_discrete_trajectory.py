import numpy as np
import matplotlib.pyplot as plt

# ##################################################################
# ## DESCRIZIONE
# ##################################################################
# Questo script simula e disegna la traiettoria di un sistema
# lineare 2D a tempo discreto.
# L'evoluzione è data dalla formula:
#   x[k] = mu1 * (lambda1^k) * v1 + mu2 * (lambda2^k) * v2
#
# Dove:
# - lambda1, lambda2: Autovalori (modi del sistema)
# - v1, v2: Autovettori (direzioni principali)
# - mu1, mu2: Coefficienti (dipendenti dalle condizioni iniziali)
# - k: passo temporale (intero)
#
# ##################################################################
# ## COME USARE
# ##################################################################
# 1. Modifica gli autovalori (lambda), autovettori (v)
#    e i coefficienti (mu) nella "Sezione 1".
# 2. Regola i parametri di simulazione (numero di passi).
# 3. Esegui lo script.
# ##################################################################


# --- 1. Impostazione dei Parametri ---

# Autovalori (modi)
# |lambda| > 1: instabile (diverge)
# |lambda| < 1: stabile (converge a zero)
lambda1 = -0.9
lambda2 = 0.5

# Autovettori (direzioni)
v1 = np.array([1.0, 2.0])
v2 = np.array([-1.0, 1.0])

# Coefficienti (condizioni iniziali)
mu1 = 1.0
mu2 = 1.0

# Parametri di Simulazione
steps = 20    # Numero di passi temporali da calcolare


# --- 2. Simulazione del Sistema ---
x_vals = []
for k in range(steps):
    # Equazione della soluzione
    xk = mu1 * (lambda1**k) * v1 + mu2 * (lambda2**k) * v2
    x_vals.append(xk)
x_vals = np.array(x_vals)


# --- 3. Plotting della Traiettoria ---
plt.figure(figsize=(8, 8))
# Disegna i punti e le linee che li connettono
plt.plot(x_vals[:, 0], x_vals[:, 1], '-o', label="Traiettoria discreta")

# Disegna gli autovettori (direzioni)
plt.quiver(0, 0, *v1, angles='xy', scale_units='xy', scale=1, color='green', label=f"v1 (lambda={lambda1})")
plt.quiver(0, 0, *v2, angles='xy', scale_units='xy', scale=1, color='red', label=f"v2 (lambda={lambda2})")

# Assi
plt.axhline(0, color='black', linewidth=0.5)
plt.axvline(0, color='black', linewidth=0.5)

# Impostazioni grafiche
plt.title("Traiettoria Sistema a Tempo Discreto")
plt.xlabel("x1")
plt.ylabel("x2")
plt.axis('equal')
plt.grid(True)
plt.legend()
plt.show()