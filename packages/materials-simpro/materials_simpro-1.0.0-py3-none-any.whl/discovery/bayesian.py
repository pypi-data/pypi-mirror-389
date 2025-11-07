"""
Bayesian Optimization
=====================

Optimize materials properties using Gaussian processes.

Algorithm:
----------
1. Build surrogate model (GP) of f(x)
2. Find x that maximizes acquisition function α(x)
3. Evaluate f(x) via expensive calculation (DFT)
4. Update GP
5. Repeat

Acquisition Functions:
----------------------
- EI (Expected Improvement): E[max(0, f(x) - f_best)]
- UCB (Upper Confidence Bound): μ(x) + κσ(x)
- PI (Probability of Improvement): P(f(x) > f_best)

References:
-----------
[1] Shahriari et al. (2016). DOI: 10.1109/JPROC.2015.2494218
[2] Frazier, P. I. (2018). A tutorial on Bayesian optimization.
    arXiv:1807.02811.
"""

import numpy as np
from typing import Callable, Tuple, List
from scipy.optimize import minimize
from scipy.stats import norm


class GaussianProcess:
    """
    Simple Gaussian Process surrogate model.

    GP defines distribution over functions:
        f(x) ~ GP(μ(x), k(x, x'))

    Prediction:
        μ(x*) = k(x*, X) K⁻¹ y
        σ²(x*) = k(x*, x*) - k(x*, X) K⁻¹ k(X, x*)

    Reference: Rasmussen & Williams (2006). Gaussian Processes for Machine Learning.
    """

    def __init__(self, kernel: str = 'rbf', length_scale: float = 1.0):
        self.kernel_type = kernel
        self.length_scale = length_scale
        self.X_train = None
        self.y_train = None
        self.K_inv = None

    def kernel(self, x1: np.ndarray, x2: np.ndarray) -> float:
        """RBF (squared exponential) kernel."""
        # k(x, x') = exp(-||x - x'||² / (2l²))
        dist = np.linalg.norm(x1 - x2)
        return np.exp(-dist**2 / (2 * self.length_scale**2))

    def fit(self, X: np.ndarray, y: np.ndarray):
        """Fit GP to training data."""
        self.X_train = X
        self.y_train = y

        # Compute kernel matrix
        n = len(X)
        K = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                K[i, j] = self.kernel(X[i], X[j])

        # Add noise for numerical stability
        K += 1e-6 * np.eye(n)
        self.K_inv = np.linalg.inv(K)

    def predict(self, X_new: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict mean and std at new points.

        Returns:
            (mean, std)
        """
        if self.X_train is None:
            raise ValueError("GP not fitted")

        n_new = len(X_new)
        mean = np.zeros(n_new)
        std = np.zeros(n_new)

        for i, x in enumerate(X_new):
            # k(x*, X)
            k_star = np.array([self.kernel(x, x_train) for x_train in self.X_train])

            # μ(x*) = k(x*, X) K⁻¹ y
            mean[i] = np.dot(k_star, np.dot(self.K_inv, self.y_train))

            # σ²(x*) = k(x*, x*) - k(x*, X) K⁻¹ k(X, x*)
            var = self.kernel(x, x) - np.dot(k_star, np.dot(self.K_inv, k_star))
            std[i] = np.sqrt(max(0, var))

        return mean, std


class BayesianOptimizer:
    """
    Bayesian optimization for materials discovery.

    Example:
    --------
    ```python
    def objective(structure):
        # Expensive DFT calculation
        return formation_energy

    optimizer = BayesianOptimizer(objective, bounds=search_space)
    best_structure, best_value = optimizer.optimize(n_iter=50)
    ```
    """

    def __init__(
        self,
        objective_func: Callable,
        bounds: List[Tuple[float, float]],
        acquisition: str = 'EI'
    ):
        """
        Initialize Bayesian optimizer.

        Args:
            objective_func: Function to minimize (e.g., -formation_energy)
            bounds: Search space bounds [(min, max), ...]
            acquisition: 'EI', 'UCB', or 'PI'
        """
        self.objective = objective_func
        self.bounds = bounds
        self.acquisition_type = acquisition
        self.gp = GaussianProcess()

        self.X_obs = []
        self.y_obs = []

    def expected_improvement(self, x: np.ndarray, xi: float = 0.01) -> float:
        """
        Expected Improvement acquisition function.

        EI(x) = E[max(0, f(x) - f_best - ξ)]
              = (μ - f_best - ξ)Φ(Z) + σφ(Z)

        where Z = (μ - f_best - ξ)/σ

        Reference: Jones et al. (1998). Efficient global optimization.
        """
        if len(self.X_obs) == 0:
            return 0.0

        mu, sigma = self.gp.predict(np.array([x]))
        mu = mu[0]
        sigma = sigma[0]

        f_best = np.min(self.y_obs)

        if sigma == 0:
            return 0.0

        Z = (f_best - mu - xi) / sigma
        ei = (f_best - mu - xi) * norm.cdf(Z) + sigma * norm.pdf(Z)

        return ei

    def ucb(self, x: np.ndarray, kappa: float = 2.0) -> float:
        """
        Upper Confidence Bound acquisition function.

        UCB(x) = μ(x) + κσ(x)

        Balances exploitation (μ) and exploration (σ).
        """
        if len(self.X_obs) == 0:
            return 0.0

        mu, sigma = self.gp.predict(np.array([x]))
        return -(mu[0] + kappa * sigma[0])  # Negative for maximization

    def optimize(self, n_iter: int = 50, n_init: int = 5) -> Tuple[np.ndarray, float]:
        """
        Run Bayesian optimization.

        Args:
            n_iter: Number of optimization iterations
            n_init: Number of random initialization points

        Returns:
            (best_x, best_y)
        """
        # Random initialization
        for _ in range(n_init):
            x = np.array([np.random.uniform(low, high) for low, high in self.bounds])
            y = self.objective(x)
            self.X_obs.append(x)
            self.y_obs.append(y)

        # Bayesian optimization loop
        for iteration in range(n_iter):
            # Fit GP
            self.gp.fit(np.array(self.X_obs), np.array(self.y_obs))

            # Find next point by maximizing acquisition function
            x_next = self._maximize_acquisition()

            # Evaluate objective
            y_next = self.objective(x_next)

            # Update observations
            self.X_obs.append(x_next)
            self.y_obs.append(y_next)

            print(f"Iteration {iteration+1}/{n_iter}: Best = {np.min(self.y_obs):.4f}")

        # Return best point
        best_idx = np.argmin(self.y_obs)
        return self.X_obs[best_idx], self.y_obs[best_idx]

    def _maximize_acquisition(self) -> np.ndarray:
        """Find x that maximizes acquisition function."""
        if self.acquisition_type == 'EI':
            acq_func = lambda x: -self.expected_improvement(x)
        elif self.acquisition_type == 'UCB':
            acq_func = lambda x: -self.ucb(x)
        else:
            raise ValueError(f"Unknown acquisition: {self.acquisition_type}")

        # Random restart optimization
        best_x = None
        best_val = np.inf

        for _ in range(10):
            x0 = np.array([np.random.uniform(low, high) for low, high in self.bounds])
            res = minimize(acq_func, x0, bounds=self.bounds, method='L-BFGS-B')

            if res.fun < best_val:
                best_val = res.fun
                best_x = res.x

        return best_x


__all__ = ['GaussianProcess', 'BayesianOptimizer']
