# AlignLLM - Case Alignment Package

This package contains the mathematical implementation of ILRAlign and WILRAlign from AlignLLM. 

Original paper: https://dl.acm.org/doi/10.1007/978-3-031-96559-3_2
Original SRC: https://github.com/RAbeyratne/aligned-ensemble-judge
Exploration SRC: https://github.com/RAbeyratne/alignllm-exploration


# Sample usage

!pip install alignllm-case-alignment-package
import numpy as np
from case_alignment_package import get_case_alignment, get_weighted_case_alignment
```
# Example case embedding
case_ = [np.array([1, 0, 1]), np.array([1, 2, 1])]

# Example casebase
case_base = [
    [np.array([0, 3, 2]), np.array([3, 2, 2])],
    [np.array([1, 0, 1]), np.array([1, 0, 2])]
]

# ILR Score (standard case alignment)
print("ILRScore:", get_case_alignment(case_, case_base))
# 0.7077719041151351

# WILR Score (weighted case alignment)
print("WILRScore:", get_weighted_case_alignment(case_, case_base))
# 0.7366226857266566
```