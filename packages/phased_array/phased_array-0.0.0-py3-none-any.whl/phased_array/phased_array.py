import string
import typing
import numpy as np
import numpy.typing as npt

# a phase pattern; given (θ, ϕ), return the power in linear units of the emitted energy
Pattern = typing.Callable[[float, float], float]
FloatArray = typing.TypeVar("FloatArray", bound=npt.NDArray[np.float64] | float)

c = 3e8


def uniform_pattern(theta: float, phi: float) -> float:
    """A uniform pattern; illuminates everything"""
    _, _ = theta, phi
    return 1.0


class Element:
    """An array element"""

    def __init__(
        self, x: float, y: float, z: float, pattern: Pattern = uniform_pattern
    ):
        self.x = x
        self.y = y
        self.z = z
        self.pattern = pattern

    def __array__(self):
        return np.array(
            [(self.x, self.y, self.z)], dtype=[("x", "f4"), ("y", "f4"), ("z", "f4")]
        )


class PhasedArray:
    """
    A completely arbitrary phased array antenna.

    """

    def __init__(self, elements: typing.Iterable[Element]):
        self._elements = np.asarray(elements)
        self.positions = self._elements.squeeze()
        self._ri = self.positions.view("f4").reshape(self.positions.shape + (3,))

    def Δd_at_θϕ(self, theta: FloatArray, phi: FloatArray) -> FloatArray:
        """Δd distance traveled to each element with angle of arrival θ, ϕ

        Args:
            θ: angle off of z axis
            ϕ: angle clockwise from x axis

        Returns:
            The relative pathlength traveled for every element, for every θ and ϕ.
            The returned shape of the array is `(*(self.positions) , *(θ.shape))`


        """
        # from PhasedArray Antenna Handbook, 3rd edititon
        θ = np.asarray(theta)
        ϕ = np.asarray(phi)
        if θ.shape != ϕ.shape:
            raise ValueError("θ and ϕ shape must be identical")

        θ_shape = θ.shape
        θ = θ.ravel()
        ϕ = ϕ.ravel()
        u_0, v_0 = θϕ_to_uv(θ, ϕ)
        rhat = np.array([u_0, v_0, np.cos(θ)])
        ri_dot_rhat = self._ri.dot(rhat)
        ri_dot_rhat.shape = (*self.positions.shape, *θ_shape)
        return ri_dot_rhat

    def weights_at_θϕ(self, λ: float, θ: FloatArray, ϕ: FloatArray):
        """Return the complex weights required at each element to point at θ and ϕ."""
        # TODO Refactor so that this code isn't duplicated between here and array_factor
        Δd = self.Δd_at_θφ(θ, ϕ)
        k = 2 * np.pi / λ
        phase = np.exp(-1j * k * Δd)
        return phase

    def array_factor(self, wavelength, weights, theta, phi):
        r"""Calculate the array factor of an array.

        Assumes embedded element pattern is an omnidirectional antenna. Uses equations
        in Phased Array Antenna Handbook, 3rd Edition.

        .. math::

           \gdef\rhat{\pmb{\hat{r}}}
           \gdef\xhat{\pmb{\hat{x}}}
           \gdef\yhat{\pmb{\hat{y}}}
           \gdef\zhat{\pmb{\hat{z}}}

           F(θ, ϕ) = \sum a_i \exp(jk \pmb{r}_i \cdot \rhat)

        where

        .. math::

            \begin{align*}
            k         &= 2 \frac{π}{λ} & \text {wave number} \\
            \rhat_0   &= \xhat u_0 + \yhat v_0 + \zhat \cos θ_0 & \text{direction of oncoming wave} \\
            \pmb{r}_i &= \xhat x_i + \yhat y_i + \zhat z_i & \text{ the position of the $i$th element} \\
            u         &= \sin {θ} \cos {ϕ}  & \text{direction cosine $u$} \\
            v         &= \sin{θ} \sin{ϕ} & \text{direction cosine $v$}
            \end{align*}

        """
        if weights.shape != self.positions.shape:
            raise ValueError(
                f"Invalid weights for array of shape {self.positions.shape}: {weights.shape}"
            )

        theta = np.asarray(theta)
        Δd = self.Δd_at_θφ(theta, phi)
        k = 2 * np.pi / wavelength
        phase = np.exp(1j * k * Δd)
        a_i = np.asarray(weights)

        # like a dot product but works with whatever dimensionality we were given
        # select the number of dimensions to sum across here
        dims = string.ascii_lowercase[: a_i.ndim]

        F = np.einsum(f"{dims},{dims}...", a_i, phase)
        return F

    @classmethod
    def ula(cls, d: float, n: int):
        """Uniform Linear Array

        A 1D, linear phased array, with uniform spacing between elements
        Args:
            d: distance between elements
            n: number of elements
        """
        elements = []
        for i in range(n):
            element = Element(i * d, 0, 0)
            elements.append(element)
        return cls(elements)

    @classmethod
    def planar(cls, dx: float, dy: float, nx: int, ny: int):
        """
        Construct a Phased Array with 2D, planar, linear spaced elements.

        Args:
            dx: spacing between x elements in meters
            dy: spacing between y elements in meters
            nx: number of x elements
            ny: number of x elements
        """
        rows = []
        for i in range(nx):
            col = []
            for j in range(ny):
                col.append(Element(i * dx, j * dy, 0))
            rows.append(col)
        return cls(rows)


def uv_to_θϕ(u, v):
    """Projection from uv plane to (θ, ϕ) angles"""
    θ = np.arcsin(np.sqrt(u**2 + v**2))
    ϕ = np.arctan2(v, u)
    return θ, ϕ


uv_to_thetaphi = uv_to_θφ


def azel_to_uv(az, el):
    """Convert azimuth and elevation angles (radians) to uv space"""
    u = np.cos(el) * np.sin(az)
    v = np.sin(el)
    return u, v


def uv_to_azel(u, v):
    """Convert u, v space to az, el in radians"""
    el = np.arcsin(v)
    az = np.arctan2(u, (np.sqrt(1 - u * u - v * v)))
    return az, el


def azel_to_θϕ(az, el):
    """Convert azimuth and elevation angles (in radians) to θ, ϕ (in radians)"""
    u, v = azel_to_uv(az, el)
    return uv_to_thetaphi(u, v)


def azel_to_thetaphi(az, el):
    return azel_to_θφ(az, el)


def θϕ_to_azel(θ, ϕ):
    u, v = θφ_to_uv(θ, ϕ)
    return uv_to_azel(u, v)


def thetaphi_to_azel(theta, phi):
    return θφ_to_azel(theta, phi)


def θϕ_to_uv(θ, ϕ):
    """Projection from θ, ϕ to u,v"""
    sin_θ = np.sin(θ)
    u = sin_θ * np.cos(ϕ)
    v = sin_θ * np.sin(ϕ)
    return u, v


def thetaphi_to_uv(theta, phi):
    return θϕ_to_uv(theta, phi)


def θϕr_to_xyz(θ, ϕ, r):
    u, v = θϕ_to_uv(θ, ϕ)
    x = r * u
    y = r * v
    z = r * np.cos(θ)
    return x, y, z
