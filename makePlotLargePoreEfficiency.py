import numpy as np
import matplotlib.pyplot as plt

voltages = np.array([1300, 1400, 1600, 1800, 2000])
collectionRate = np.array([0.0333, 2.24, 4.05, 4.12, 4.10])

plt.figure(figsize=(15, 9))
plt.scatter(voltages, collectionRate, marker='x', s=500, linewidth=7)
plt.title("Collection Efficiency Comparison for 9890-31", fontsize=36)
plt.xlabel("Voltage Across MCP (V)", fontsize=36)
plt.ylabel("Collection Rate\n(hits per shot)", fontsize=36)
plt.xticks(fontsize=26)
plt.yticks(fontsize=26)
plt.xlim([1200, 2100])
plt.ylim([0, 5])
plt.xticks([1400, 1600, 1800, 2000])
plt.yticks([1, 2, 3, 4])
plt.draw()
plt.pause(0.01)