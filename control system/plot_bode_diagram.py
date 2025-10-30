import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

# ##################################################################
# ## DESCRIZIONE
# ##################################################################
# Questo script genera i diagrammi di Bode (Modulo e Fase)
# per un sistema LTI definito dalla sua rappresentazione
# Zeri-Poli-Guadagno (ZPK).
#
# ##################################################################
# ## COME USARE
# ##################################################################
# 1. Modifica le liste `zeros`, `poles` e il `gain`
#    nella "Sezione 1" qui sotto.
# 2. Modifica `w_range` per cambiare l'intervallo di pulsazioni.
# 3. Esegui lo script.
# ##################################################################


# --- 1. Definizione del Sistema (ZPK) ---
# Modifica questi valori per analizzare il tuo sistema
# Le posizioni sono sull'asse reale (stabili = negativi)
zeros = [-10.0]
poles = [-100.0, -10000.0, -100000.0]
gain_dc = 1.0  # Guadagno desiderato in continua (DC)

# Intervallo di pulsazioni (rad/s) da visualizzare
w_range = np.logspace(0, 7, num=1000)


# --- 2. Calcolo Guadagno 'k' per ZPK ---
# Calcola il guadagno 'k' della forma ZPK necessario
# per ottenere il 'gain_dc' (guadagno in continua) desiderato.
k = gain_dc * (np.prod([-p for p in poles]) / np.prod([-z for z in zeros]))


# --- 3. Creazione Oggetto di Sistema ---
# Crea un oggetto LTI (Linear Time-Invariant)
# usando la rappresentazione Zeri-Poli-Guadagno (ZPK)
system = signal.ZerosPolesGain(zeros, poles, k)


# --- 4. Calcolo dei Dati di Bode ---
# Calcola magnitudine e fase nell'intervallo di pulsazioni specificato
w, mag, phase = signal.bode(system, w_range)


# --- 5. Plotting dei Diagrammi di Bode ---
plt.figure(figsize=(12, 8))

# Grafico del Modulo (Guadagno)
plt.subplot(2, 1, 1)
plt.semilogx(w, mag)
plt.title('Diagramma di Bode', fontsize=16)
plt.ylabel('Guadagno (dB)')
plt.grid(which='major', linestyle='--', alpha=0.6)

# Grafico della Fase
plt.subplot(2, 1, 2)
plt.semilogx(w, phase)
plt.xlabel('Pulsazione (rad/s)')
plt.ylabel('Fase (gradi)')
plt.grid(which='major', linestyle='--', alpha=0.6)

plt.tight_layout()
plt.show()