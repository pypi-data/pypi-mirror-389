import jax
import jax.numpy as jnp
from jax import lax

def gmres(A, b, x0=None, M=None, tol=1e-5, maxiter=None, restart=20):
    x0 = jnp.zeros_like(b) if x0 is None else x0
    M = (lambda x: x) if M is None else M
    n = x0.shape[0]
    maxiter = jnp.inf if maxiter is None else maxiter
    arnoldi_tol = 1e-5

    def one_run(i, x0):
        r0 = M(b - A(x0))
        beta = jnp.linalg.norm(r0)
        V = jnp.zeros((restart + 1, n), dtype=x0.dtype)
        V = V.at[0].set(r0 / beta)
        H = jnp.zeros((restart + 1, restart), dtype=x0.dtype)

        def loop_cond(carry):
            j, _, _, v_norm = carry
            return (j < restart) & (v_norm > arnoldi_tol)

        def loop_body(carry):
            j, H, V, _ = carry

            # First orthogonalization step
            w = M(A(V[j]))
            h = V.conj() @ w
            v = w - (V.T) @ h

            # Second orthogonalization step
            h2 = V.conj() @ v
            v = v - (V.T) @ h2

            h = h + h2

            v_norm = jnp.linalg.norm(v)

            H = H.at[:, j].set(h)
            H = H.at[j + 1, j].set(v_norm)
            V = V.at[j + 1].set(jnp.where(v_norm > arnoldi_tol, v / v_norm, V[j+1]))

            return j + 1, H, V, v_norm

        # Initialize
        v_norm0 = jnp.inf
        carry0 = (0, H, V, v_norm0)

        _, H, V, _ = jax.lax.while_loop(loop_cond, loop_body, carry0)

        e1 = jnp.zeros(restart + 1, dtype=x0.dtype)
        e1 = e1.at[0].set(beta)
        y = jnp.linalg.lstsq(H, e1, rcond=None)[0]
        x_new = x0 + V[:-1].T @ y
        return x_new

    def cond_fun(state):
        i, x = state
        return jnp.logical_and(i < maxiter, jnp.linalg.norm(b - A(x)) > tol * jnp.linalg.norm(b))

    def body_fun(state):
        i, x = state
        x_new = one_run(i, x)
        return i + 1, x_new

    _, x_final = lax.while_loop(cond_fun, body_fun, (0, x0))
    return x_final, None