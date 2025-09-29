
import numpy as np
import matplotlib.pyplot as plt

# INPUT DA TERMINALE
lambda1 = float(input("Inserisci lambda1 (es. -3): "))
lambda2 = float(input("Inserisci lambda2 (es. 0.1): "))

v1 = np.array([
    float(input("v1[0] (es. 1): ")),
    float(input("v1[1] (es. 2): "))
])
v2 = np.array([
    float(input("v2[0] (es. 1): ")),
    float(input("v2[1] (es. 0.2): "))
])

mu1 = float(input("mu1 (es. 1): "))
mu2 = float(input("mu2 (es. 1): "))
steps = int(input("Numero di passi temporali (es. 20): "))

# Simulazione
x_vals = []
for k in range(steps):
    xk = mu1 * (lambda1**k) * v1 + mu2 * (lambda2**k) * v2
    x_vals.append(xk)
x_vals = np.array(x_vals)

# Plot
plt.plot(x_vals[:, 0], x_vals[:, 1], '-o', label="Discrete trajectory")
plt.quiver(0, 0, *v1, angles='xy', scale_units='xy', scale=1, color='green', label="v1")
plt.quiver(0, 0, *v2, angles='xy', scale_units='xy', scale=1, color='red', label="v2")
plt.axhline(0, color='black', linewidth=0.5)
plt.axvline(0, color='black', linewidth=0.5)
plt.title("Discrete-Time System (User Input)")
plt.axis('equal')
plt.grid(True)
plt.legend()
plt.show()
