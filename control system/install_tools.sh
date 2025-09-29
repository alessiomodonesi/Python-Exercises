#!/bin/bash

# Crea virtualenv se desiderato
# python3 -m venv venv
# source venv/bin/activate

echo "Aggiornamento pip..."
pip3 install --upgrade pip

echo "Installazione pacchetti: numpy, matplotlib, scipy, control, sympy..."
pip3 install numpy matplotlib scipy control sympy

echo "Tutti i pacchetti sono stati installati con successo."
