# ParallelKDEpy: Python wrapper for ParallelKDE.jl

[![Stable](https://img.shields.io/badge/docs-stable-blue.svg)](https://chrissm23.github.io/ParallelKDEpy/stable/)
[![Dev](https://img.shields.io/badge/docs-dev-blue.svg)](https://chrissm23.github.io/ParallelKDEpy/dev/)
[![Build Status](https://github.com/chrissm23/ParallelKDEpy/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/chrissm23/ParallelKDEpy/actions/workflows/ci.yml?query=branch%3Amain)

High performance implementation of a parallel kernel density estimation algorithm described in [Sustay Martinez *et al.* (2025)]. The algorithm is specially suited for high-dimensional data, with CPU/CUDA support.

**Quick links:**

- 📑 Docs: [stable](https://chrissm23.github.io/ParallelKDEpy/stable/) | [dev](https://chrissm23.github.io/ParallelKDEpy/dev/)
- 📇 [Citing](#citing)
- ![Julia](https://img.shields.io/badge/-Julia-9558B2?style=for-the-badge&logo=julia&logoColor=white) Julia package: [ParallelKDE.jl](https://github.com/chrissm23/ParallelKDE.jl)

## Installation

```bash
pip install parallelkdypy
```

The wrapper will handle installing `Julia` and `ParallelKDE.jl` the first time you import it. No additional setup is required.

## Quick Start

```python
import numpy as np
import parallelkdepy as pkde

# Assume 'data' is a 2D array of points for which we want to estimate the density
data = np.random.randn(10000, 1)

density_estimation = pkde.DensityEstimation(data, grid=True, device="cpu")
density_estimation.estimate_density("gradepro")

density estimated = density_estimation.get_density()
```

See the [documentation](https://chrissm23.github.io/ParallelKDEpy) for more details on how to use the package.

## Features

Currently, there are two estimators available:

- `"gradepro"`: As described in [Sustay Martinez et al. (2025)], this estimator is designed for high-dimensional data and can be run on both CPU and GPU.
- `"rot"`: Implements the rules of thumb (Silverman and Scott) for bandwidth selection. It makes use of some of the routines from `:gradepro` to evaluate the density on a grid.

## Julia Package

Please keep in mind that this package is a wrapper around the Julia package [ParallelKDE.jl](https://github.com/chrissm23/ParallelKDE.jl). For more information on the Julia package, please refer to its [documentation](https://chrissm23.github.io/ParallelKDE.jl/stable/).

## Citing

Please cite the following papers when using ParallelKDEpy in your work:

## Known Issues

List of main known issues:

- [Issue #5](https://github.com/chrissm23/ParallelKDEpy/issues/5): Segmentation faults for CUDA implementations
