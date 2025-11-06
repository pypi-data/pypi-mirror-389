# Gauss6

Gauss6 bundles a sixth-order implicit Gauss–Legendre time integrator together with high-order finite-difference helpers, all implemented with [JAX](https://github.com/google/jax).
The method is A-stable and therefore useful for stiff systems. It is also symplectic, and therefore useful for solving Hamiltonian systems such as the KdV equation.

The systems are solved based on methods described in *Solving Ordinary Differential Equations II: Stiff and Differential-Algebraic Problems* by Hairer and Wanner (Springer, 1996), section IV.8 Implementation of Implicit Runge-Kutta Methods: The Linear System. 
The implicit steps are solved using a Newton-GMRES solver with backtracking, as explained in *Choosing the Forcing Terms in an Inexact Newton Method* by Stanley C. Eisenstat and Homer F. Walker (SIAM, 1996). We further use `jax` to automatically compute the Jacobian-vector products needed in the GMRES solver.

## Installation

The package targets Python 3.9+ and relies on JAX.  Install the right `jax`/`jaxlib` wheel for your platform (CPU-only shown below) and then install Gauss6:

```bash
pip install --upgrade pip
pip install --upgrade "jax[cpu]"
pip install gauss6
```

## Quick start

```python
import jax.numpy as jnp
from gauss6 import Gauss6

def f(t, u, args):
    alpha = args["alpha"]
    return alpha * u

t = jnp.linspace(0.0, 2.0, 201)
params = {"alpha": -1.0}
u0 = jnp.array([1.0])  # initial condition

solver = Gauss6(t, args=params, size=u0.size)
solve = solver.make_solve(f)
trajectory = solve(u0)
```

The package also exposes high-order central-difference helpers:

```python
from gauss6 import dx_order_6

spacing = 0.01
values = jnp.sin(jnp.linspace(0, jnp.pi, 512))
first_derivative = dx_order_6(values, spacing)
```

## License

Gauss6 is released under the [MIT license](LICENSE).
