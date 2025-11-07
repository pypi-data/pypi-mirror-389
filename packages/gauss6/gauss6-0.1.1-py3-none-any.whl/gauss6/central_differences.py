import jax.numpy as jnp

def dx_order_2(y, dx, axis=0):
    y_p_1 = jnp.roll(y, shift=-1, axis=axis)
    y_m_1 = jnp.roll(y, shift=1, axis=axis)
    return (y_p_1 - y_m_1) / (2 * dx)

def dx_order_4(y, dx, axis=0):
    y_p_1 = jnp.roll(y, shift=-1, axis=axis)
    y_m_1 = jnp.roll(y, shift=1, axis=axis)
    y_p_2 = jnp.roll(y, shift=-2, axis=axis)
    y_m_2 = jnp.roll(y, shift=2, axis=axis)
    return (-y_p_2 + 8*y_p_1 - 8*y_m_1 + y_m_2)/(12*dx)

def dx_order_6(y, dx, axis=0):
    y_p_1 = jnp.roll(y, shift=-1, axis=axis)
    y_m_1 = jnp.roll(y, shift=1, axis=axis)
    y_p_2 = jnp.roll(y, shift=-2, axis=axis)
    y_m_2 = jnp.roll(y, shift=2, axis=axis)
    y_p_3 = jnp.roll(y, shift=-3, axis=axis)
    y_m_3 = jnp.roll(y, shift=3, axis=axis)
    return (y_p_3 - 9*y_p_2 + 45*y_p_1 - 45*y_m_1 + 9*y_m_2 - y_m_3)/(60*dx)

def dxx_order_2(y, dx, axis=0):
    y_p_1 = jnp.roll(y, shift=-1, axis=axis)
    y_m_1 = jnp.roll(y, shift=1, axis=axis)
    return (y_p_1 - 2 * y + y_m_1) / dx**2

def dxx_order_4(y, dx, axis=0):
    y_p_1 = jnp.roll(y, shift=-1, axis=axis)
    y_m_1 = jnp.roll(y, shift=1, axis=axis)
    y_p_2 = jnp.roll(y, shift=-2, axis=axis)
    y_m_2 = jnp.roll(y, shift=2, axis=axis)
    return (-y_p_2+16*y_p_1-30*y+16*y_m_1-y_m_2)/(12*dx**2)

def dxx_order_6(y, dx, axis=0):
    """Assumes periodic boundary conditions"""
    y_p_1 = jnp.roll(y, shift=-1, axis=axis)
    y_m_1 = jnp.roll(y, shift=1, axis=axis)
    y_p_2 = jnp.roll(y, shift=-2, axis=axis)
    y_m_2 = jnp.roll(y, shift=2, axis=axis)
    y_p_3 = jnp.roll(y, shift=-3, axis=axis)
    y_m_3 = jnp.roll(y, shift=3, axis=axis)
    return (270*y_m_1 - 27*y_m_2 + 2*y_m_3 + 270*y_p_1 - 27*y_p_2 + 2*y_p_3 - 490*y) / (180*dx**2)

def dxxx_order_2(y, dx, axis=0):
    """Assumes periodic boundary conditions"""
    y_p_1 = jnp.roll(y, shift=-1, axis=axis)
    y_p_2 = jnp.roll(y, shift=-2, axis=axis)
    y_m_1 = jnp.roll(y, shift=1, axis=axis)
    y_m_2 = jnp.roll(y, shift=2, axis=axis)
    return (-y_m_2 + 2* y_m_1 - 2*y_p_1 + y_p_2) / (2*dx**3)

def dxxx_order_4(y, dx, axis=0):
    """Assumes periodic boundary conditions"""
    y_p_1 = jnp.roll(y, shift=-1, axis=axis)
    y_p_2 = jnp.roll(y, shift=-2, axis=axis)
    y_m_1 = jnp.roll(y, shift=1, axis=axis)
    y_m_2 = jnp.roll(y, shift=2, axis=axis)
    y_p_3 = jnp.roll(y, shift=-3, axis=axis)
    y_m_3 = jnp.roll(y, shift=3, axis=axis)
    return (y_m_3 - 8*y_m_2 + 13* y_m_1 - 13* y_p_1 + 8*y_p_2 - y_p_3)/(8*dx**3)
    
def dxxx_order_6(y, dx, axis=0):
    """Assumes periodic boundary conditions"""
    y_p_1 = jnp.roll(y, shift=-1, axis=axis)
    y_p_2 = jnp.roll(y, shift=-2, axis=axis)
    y_m_1 = jnp.roll(y, shift=1, axis=axis)
    y_m_2 = jnp.roll(y, shift=2, axis=axis)
    y_p_3 = jnp.roll(y, shift=-3, axis=axis)
    y_m_3 = jnp.roll(y, shift=3, axis=axis)
    y_p_4 = jnp.roll(y, shift=-4, axis=axis)
    y_m_4 = jnp.roll(y, shift=4, axis=axis)
    return (-7 * (y_m_4-y_p_4) + 72*(y_m_3-y_p_3) - 338*(y_m_2-y_p_2) + 488 * (y_m_1- y_p_1))/(240*dx**3)