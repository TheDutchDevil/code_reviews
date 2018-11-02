# -*- coding: utf-8 -*-
"""
Created on Fri Nov  2 15:17:37 2018

@author: natha
"""

import matplotlib.pyplot as plt
import numpy as np

friday_data = [0.023, 0.031, 0.021, 0.020, 0.016, 0.05, 0.015, 0.024, 0.049]
monday_data = [0.039, 0.061, 0.085, 0.081, 0.054, 0.063, 0.023, 0.058]

plt.title("Variance in measured p values")
plt.ylabel("$p$ value")

plt.boxplot([friday_data, monday_data])
plt.xticks(np.arange(2) + 1, ["Friday", "Monday"])

#%%
