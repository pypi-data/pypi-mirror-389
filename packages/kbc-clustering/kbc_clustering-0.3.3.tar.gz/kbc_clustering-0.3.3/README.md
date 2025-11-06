# KBC Clustering

Kernel-Bounded Clustering: Achieving the Objective of Spectral Clustering without Eigendecomposition

## Installation

```bash
pip install kbc-clustering


```python
from kbc import KBC
import numpy as np

X = np.random.rand(1000, 50)
model = KBC(k=5, tau=0.4, psi=64, random_state=42)
labels = model.fit_predict(X)


## Reference
@article{ZHANG2025104440,
title = {Kernel-Bounded Clustering: Achieving the Objective of Spectral Clustering without Eigendecomposition},
journal = {Artificial Intelligence},
pages = {104440},
year = {2025},
issn = {0004-3702},
doi = {https://doi.org/10.1016/j.artint.2025.104440},
url = {https://www.sciencedirect.com/science/article/pii/S0004370225001596},
author = {Hang Zhang and Kai Ming Ting and Ye Zhu},