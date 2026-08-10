import torch
import cv2
import time

print("=" * 50)
print("🔍 VERIFICA ACCELERAZIONE HARDWARE APPLE SILICON")
print("=" * 50)

# 1. Verifica PyTorch & Metal (MPS - Metal Performance Shaders)
print("\n--- 1. PyTorch / MPS (Metal) ---")
mps_available = torch.backends.mps.is_available()
mps_built = torch.backends.mps.is_built()

print(f"PyTorch Version: {torch.__version__}")
print(f"MPS Built in PyTorch: {mps_built}")
print(f"MPS Available on Host: {mps_available}")

if mps_available:
    device = torch.device("mps")
    print("✅ PyTorch sta usando: ACCELERAZIONE METAL (MPS)")
    
    # Test sintetico di velocità MPS vs CPU
    x = torch.randn(2000, 2000, device=device)
    start = time.time()
    for _ in range(100):
        y = x @ x
    torch.mps.synchronize()
    print(f"⚡ Tempo di calcolo matmul 2000x2000 su MPS (100 iterazioni): {time.time() - start:.4f}s")
else:
    print("⚠️ PyTorch STA USANDO LA CPU (Metal non disponibile o non supportato).")

# 2. Verifica OpenCV & SIMD/Accelerazione
print("\n--- 2. OpenCV Build Info ---")
print(f"OpenCV Version: {cv2.__version__}")
print(f"Optimizations Enabled: {cv2.useOptimized()}")

# Dettagli sulle ottimizzazioni CPU/NEON di Apple Silicon
build_info = cv2.getBuildInformation()
print("\n--- Dettagli Tecnologici OpenCV ---")
for line in build_info.split('\n'):
    if any(k in line for k in ["CPU/HW features", "GUI", "Parallel framework"]):
        print(line)

print("=" * 50)