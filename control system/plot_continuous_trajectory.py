import numpy as np
import matplotlib.pyplot as plt

# ##################################################################
# ## DESCRIZIONE
# ##################################################################
# Questo script simula e disegna la traiettoria di un sistema
# lineare 2D a tempo continuo.
# L'evoluzione è data dalla formula:
#   x(t) = mu1 * exp(lambda1 * t) * v1 + mu2 * exp(lambda2 * t) * v2
#
# Dove:
# - lambda1, lambda2: Autovalori (tassi di crescita/decadimento)
# - v1, v2: Autovettori (direzioni principali)
# - mu1, mu2: Coefficienti (dipendenti dalle condizioni iniziali)
#
# ##################################################################
# ## COME USARE
# ##################################################################
# 1. Modifica gli autovalori (lambda), autovettori (v)
#    e i coefficienti (mu) nella "Sezione 1".
# 2. Regola i parametri di simulazione (tempo finale, n. di punti).
# 3. Esegui lo script.
# ##################################################################


# --- 1. Impostazione dei Parametri ---

# Autovalori (tassi)
lambda1 = -3.0
lambda2 = 0.1

# Autovettori (direzioni)
v1 = np.array([1.0, 2.0])
v2 = np.array([1.0, 0.2])

# Coefficienti (condizioni iniziali)
mu1 = 1.0
mu2 = 1.0

# Parametri di Simulazione
t_end = 5.0    # Tempo finale
points = 200   # Numero di punti da calcolare


# --- 2. Simulazione del Sistema ---
t_vals = np.linspace(0, t_end, points)
x_vals = []
for t in t_vals:
    # Equazione della soluzione
    xt = mu1 * np.exp(lambda1 * t) * v1 + mu2 * np.exp(lambda2 * t) * v2
    x_vals.append(xt)
x_vals = np.array(x_vals)


# --- 3. Plotting della Traiettoria ---
plt.figure(figsize=(8, 8))
plt.plot(x_vals[:, 0], x_vals[:, 1], label="Traiettoria continua")

# Disegna gli autovettori (direzioni)
plt.quiver(0, 0, *v1, angles='xy', scale_units='xy', scale=1, color='green', label=f"v1 (lambda={lambda1})")
plt.quiver(0, 0, *v2, angles='xy', scale_units='xy', scale=1, color='red', label=f"v2 (lambda={lambda2})")

# Assi
plt.axhline(0, color='black', linewidth=0.5)
plt.axvline(0, color='black', linewidth=0.5)

# Impostazioni grafiche
plt.title("Traiettoria Sistema a Tempo Continuo")
plt.xlabel("x1")
plt.ylabel("x2")
plt.axis('equal')
plt.grid(True)
plt.legend()
plt.show()