import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

# --- 1. Definisci Poli, Zeri e Guadagno ---
# Le posizioni sono sull'asse reale (stabili = negativi)
zeros = [-10.0]
poles = [-100.0, -10000.0, -100000.0]
gain = 1.0

# --- 2. Calcola il 'k' necessario ---
k = gain * (np.prod([-p for p in poles]) / np.prod([-z for z in zeros]))

# --- 3. Crea il sistema ---
# Crea un oggetto LTI (Linear Time-Invariant)
# usando la rappresentazione Zeri-Poli-Guadagno (ZPK)
system = signal.ZerosPolesGain(zeros, poles, k)

# --- 4. Calcola i dati per il Bode Plot ---
w_range = np.logspace(1, 7, num=1000)
w, mag, phase = signal.bode(system, w_range)

# --- 5. Disegna il Diagramma del Modulo ---
plt.figure(figsize=(10, 6))
plt.semilogx(w, mag) 
plt.title('Diagramma di Bode: Modulo (Guadagno)')
plt.xlabel('Pulsazione (rad/s)')
plt.ylabel('Guadagno (dB)')
plt.grid(which='major', linestyle='--')
plt.show()