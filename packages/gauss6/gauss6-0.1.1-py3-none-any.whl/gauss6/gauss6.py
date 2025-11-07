import jax
import jax.numpy as jnp
from jax import lax
import sparsejac
from jax.experimental import sparse
from jax_tqdm import scan_tqdm
from .gmres import gmres

class Gauss6:
    def __init__(self, t, args, max_newton=jnp.inf, max_backtrack=jnp.inf, max_gmres=jnp.inf, size=64 * 64, tqdm=True):
        self.dt = t[1] - t[0]
        self.t = t
        self.max_newton = max_newton
        self.max_gmres = max_gmres
        self.max_backtrack = max_backtrack
        self.args = args
        self.size = size
        self.tqdm = tqdm
    
        c = jnp.array([0.5 - jnp.sqrt(15)/10, 0.5, 0.5 + jnp.sqrt(15)/10])
        d = jnp.array([5/3, -4/3, 5/3])

        A = jnp.array([[5/36, 2/9-jnp.sqrt(15)/15, 5/36-jnp.sqrt(15)/30],
                        [5/36+jnp.sqrt(15)/24, 2/9, 5/36-jnp.sqrt(15)/24],
                        [5/36+jnp.sqrt(15)/30, 2/9+jnp.sqrt(15)/15, 5/36]])
        
        self.eps = jnp.finfo(A.dtype).eps*1e2

        A_inv = jnp.linalg.inv(A)

        eigvals, eigvecs = jnp.linalg.eig(A_inv)

        gamma_index = jnp.argmax(jnp.isclose(eigvals.imag, 0))
        gamma_hat = eigvals[gamma_index].real
        v_gamma = eigvecs[:, gamma_index].real

        alpha_beta_index = jnp.argmax(eigvals.imag)
        alpha_hat = eigvals[alpha_beta_index].real
        beta_hat = eigvals[alpha_beta_index].imag
        v_alpha_beta = eigvecs[:, alpha_beta_index]

        v_real = jnp.real(v_alpha_beta)
        v_imag = -jnp.imag(v_alpha_beta)

        T = jnp.column_stack([v_gamma, v_real, v_imag])
        T_inv = jnp.linalg.inv(T)

        Lambda = jnp.array([
                [gamma_hat, 0.0,   0.0],
                [0.0,   alpha_hat, -beta_hat],
                [0.0,   beta_hat,  alpha_hat]
            ])
        
        self.c = c
        self.A = A
        self.d = d
        self.T = T
        self.T_inv = T_inv
        self.Lambda = Lambda

        self.gamma = gamma_hat / self.dt
        self.alpha = alpha_hat / self.dt
        self.beta = beta_hat / self.dt

    def _q(self, x, z_next):
        c = self.c
        z0 = z_next[0] * (x - c[1])/(c[0]-c[1]) * x/c[0] * (x - c[2])/(c[0]-c[2])
        z1 = z_next[1] * (x - c[0])/(c[1]-c[0]) * x/c[1] * (x - c[2])/(c[1]-c[2])
        z2 = z_next[2] * (x - c[0])/(c[2]-c[0]) * (x - c[1])/(c[2]-c[1]) * x/c[2]
        return z0 + z1 + z2
    
    def make_step(self, f):
        dt = self.dt
        max_newton = self.max_newton
        max_backtrack = self.max_backtrack
        max_gmres = self.max_gmres
        c = self.c
        d = self.d
        T = self.T
        T_inv = self.T_inv
        Lambda = self.Lambda
        gamma = self.gamma
        alpha = self.alpha
        beta = self.beta
        args = self.args
        size = self.size
        eps = self.eps

        sparsity = sparse.eye(size)
        jacfwd_fn = sparsejac.jacfwd(f, argnums = 1, sparsity=sparsity)

        eta_max = 0.9
        eta_init = 0.5
        t_bt = 1e-4
        theta_min = 0.1
        theta_max = 0.5
        eta_alpha = ((1 + jnp.sqrt(5))/2)
        eta_gamma = 1.
    
        @scan_tqdm(len(self.t), disable = not self.tqdm)
        def step(carry, scan_data):
            _, tn = scan_data
            un, w_old, w_guess = carry  # un: current state, w_old: current state in w-space, w_guess: guess for the next step in w-space

            dtype = un.dtype
            complex_valued = jnp.issubdtype(dtype, jnp.complexfloating)
            c_dtype = jnp.result_type(dtype, 1j) # complex dtype matching un

            _, jvp = jax.linearize(lambda u: f(tn, u, args), un.astype(c_dtype)) # jvp function at un

            jac_diag = jacfwd_fn(tn, un, args).data

            def F(w): # we want to solve F(w) = 0
                z = T @ w
                rhs = - (Lambda @ w) / dt + (T_inv @ jax.vmap(lambda c_i, z_i : f(tn + c_i*dt, un + z_i, args))(c, z))
                return rhs

            def A0(v):
                return gamma * v - jvp(v.astype(c_dtype)).real

            def A12(v):
                return (alpha + 1j*beta) * v - jvp(v)

            def M0(v):
                return safe_divide(v, gamma - jac_diag, eps=eps)

            def M12(v):
                return safe_divide(v, (alpha + 1j*beta) - jac_diag, eps=eps)
                
            def _g(theta, w, delta_w):
                w_candidate = w + theta*delta_w
                F_val = F(w_candidate)
                return jnp.abs(jnp.vdot(F_val, F_val))
            
            def choose_theta(w, delta_w):
                g_0 = _g(0.0, w, delta_w)

                g_prime_0 = 2 * jnp.vdot(F(w), jax.vmap(jvp)(delta_w.astype(c_dtype)).astype(dtype)).real
    
                g_1 = _g(1.0, w, delta_w)
                g_theta_min = _g(theta_min, w, delta_w)
                g_theta_max = _g(theta_max, w, delta_w)

                a = g_1 - g_prime_0 - g_0
                b = g_prime_0
                theta_star = -b / (2 * a)

                cond = (a > 0) & (theta_star > theta_min) & (theta_star < theta_max)

                return lax.cond(
                    cond,
                    lambda : theta_star,
                    lambda : jnp.where(g_theta_min < g_theta_max, theta_min, theta_max),
                )
            
            def backtracking_cond(carry):
                delta_w, eta, w, rhs_norm, backtrack_iter = carry
                w_new = w + delta_w
                new_rhs_norm = jnp.linalg.norm(jnp.ravel(F(w_new)))
                return (new_rhs_norm > (1-t_bt*(1-eta))*rhs_norm) & (backtrack_iter < max_backtrack)

            def backtracking(carry):
                delta_w, eta, w, rhs_norm, backtrack_iter = carry
                new_theta = choose_theta(w, delta_w)
                new_delta_w = new_theta * delta_w
                new_eta = 1-new_theta*(1-eta)

                return new_delta_w, new_eta, w, rhs_norm, backtrack_iter + 1
            
            def newton_cond(carry):
                global_tol = eps
                update_tol = eps
                w, delta_w, _, _, _, newton_iter = carry

                rhs_norm_current = jnp.linalg.norm(jnp.ravel(F(w)))
                delta_w_norm = jnp.linalg.norm(delta_w.ravel())

                return  (newton_iter == 0) | ((newton_iter < max_newton) & (rhs_norm_current > global_tol * rhs_norm_0) & (delta_w_norm > update_tol))

            def compute_eta(rhs_norm, rhs_norm_old, eta_old):
                eta = eta_gamma*(rhs_norm / rhs_norm_old)**eta_alpha # compute tolerance
                eta = jnp.where(eta_gamma * eta_old**eta_alpha > 0.1, jnp.maximum(eta, eta_gamma * eta_old**eta_alpha), eta) # safeguard
                eta = jnp.minimum(eta, eta_max) # safeguard
                return eta

            def newton(carry):
                w, delta_w, rhs_norm_old, _, eta_old, newton_iter = carry
                rhs = F(w)
                rhs_norm = jnp.linalg.norm(jnp.ravel(rhs))

                # ADAPTIVE TOLERANCE FOR LINEAR SOLVES
                eta = lax.cond(newton_iter==0, 
                               lambda : eta_init,
                               lambda : compute_eta(rhs_norm, rhs_norm_old, eta_old)
                               )

                # SOLVE LINEAR SYSTEMS USING GMRES
                # ensure that we do at least one GMRES iteration
                delta_w0, _ = gmres(A0, rhs[0], gmres(A0, rhs[0], M=M0, maxiter = 1)[0], M=M0, tol = eta, maxiter=max_gmres)
                delta_w12, _ = gmres(A12, rhs[1] + 1j*rhs[2], gmres(A12, rhs[1] + 1j*rhs[2], M=M12, maxiter=1)[0], M=M12, tol=eta, maxiter=max_gmres)

                delta_w_new = jnp.stack([delta_w0, delta_w12.real, delta_w12.imag], axis=0)

                # BACKTRACKING
                delta_w_new = lax.while_loop(backtracking_cond, backtracking, (delta_w_new, eta, w, rhs_norm, 0))[0]

                w_new = w + delta_w_new  

                carry = (w_new, delta_w_new, rhs_norm, delta_w, eta, newton_iter + 1)
                return carry

            # initial guess for w and delta_w
            rhs_norm_0 = jnp.linalg.norm(jnp.ravel(F(w_guess))) # || F(w_k) ||
            init_carry = (w_guess, jnp.zeros_like(w_guess), 0., jnp.zeros_like(w_guess), 0, 0.) # (w, delta_w, rhs_norm_old, delta_w_old, k, eta_old), guess zero for update step
            w_next = lax.while_loop(newton_cond, newton, init_carry)[0]

            z_next = T @ w_next # transform back to z-space
            u_next = un + jnp.dot(d, z_next) # compute global state

            z_guess_next = self._q(1.0 + c[:, None], z_next) + un - u_next # compute guess for next step in z-space
            w_guess_next = T_inv @ z_guess_next # transform guess to w-space

            return (u_next, w_next, w_guess_next), u_next
        return step

    def make_solve(self, f):
        step = self.make_step(f)

        def solve(u0):
            """
            f: callable f(t, u, args)
            u0: initial state (array)
            t: array of times (time points to step over). Can be full time-grid.
            args: extra args to pass to f
            """
            # initialize guess as zeros (shape (3, state_dim))
            w_guess = jnp.zeros((3, u0.shape[0]), dtype=u0.dtype)
            w_old = jnp.zeros((3, u0.shape[0]), dtype=u0.dtype)

            carry_init = (u0, w_old, w_guess)
            _, u_series = lax.scan(lambda carry, tn: step(carry, tn), carry_init, (jnp.arange(len(self.t[:-1])), self.t[:-1]))
            u_series = jnp.concatenate([jnp.expand_dims(u0, 0), u_series])
            return u_series
        return solve
    
def safe_divide(x, y, eps=1e-8):
    return x * jnp.conj(y) / (jnp.abs(y)**2 + eps)

def complex_to_real(x):
    return jnp.concatenate([x.real, x.imag], axis=0)

def real_to_complex(x):
    n = x.shape[0] // 2
    return x[:n] + 1j * x[n:]
