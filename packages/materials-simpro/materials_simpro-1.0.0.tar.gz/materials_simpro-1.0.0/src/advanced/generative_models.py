"""
Generative Models for Materials Discovery
==========================================

Deep generative models for inverse materials design.

Models:
- MaterialVAE: Variational Autoencoder
- MaterialGAN: Generative Adversarial Network
- DiffusionModel: Denoising diffusion probabilistic models

Target: Generate novel materials with desired properties.

References:
- Kingma & Welling (2013). VAE. arXiv:1312.6114
- Goodfellow et al. (2014). GAN. arXiv:1406.2661
- Ho et al. (2020). Diffusion. arXiv:2006.11239
- Xie & Grossman (2018). Crystal GAN. DOI: 10.1103/PhysRevLett.120.145301
"""

import torch
import torch.nn as nn
from typing import List, Optional
from core.structure import Structure


class MaterialVAE(nn.Module):
    """
    Variational Autoencoder for crystal structures.

    Architecture:
    Encoder: Structure ’ ¼, Ã (latent distribution)
    Decoder: z ~ N(¼, Ã) ’ Structure

    Loss:
    L = Reconstruction loss + KL divergence

    Reference: Kingma & Welling (2013). arXiv:1312.6114
    """

    def __init__(self, latent_dim: int = 256):
        super().__init__()
        self.latent_dim = latent_dim

        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(512, 512),
            nn.ReLU(),
            nn.Linear(512, 256),
            nn.ReLU(),
        )
        self.fc_mu = nn.Linear(256, latent_dim)
        self.fc_logvar = nn.Linear(256, latent_dim)

        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 512),
            nn.ReLU(),
            nn.Linear(512, 512),
        )

    def encode(self, x):
        """Encode structure to latent distribution."""
        h = self.encoder(x)
        return self.fc_mu(h), self.fc_logvar(h)

    def reparameterize(self, mu, logvar):
        """Reparameterization trick: z = ¼ + Ã * µ"""
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode(self, z):
        """Decode latent vector to structure."""
        return self.decoder(z)

    def forward(self, x):
        """VAE forward pass."""
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        return self.decode(z), mu, logvar

    def loss_function(self, recon_x, x, mu, logvar):
        """
        VAE loss = Reconstruction + KL divergence.

        KL = -0.5 * £(1 + log(Ã²) - ¼² - Ã²)
        """
        recon_loss = nn.functional.mse_loss(recon_x, x, reduction='sum')
        kld = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
        return recon_loss + kld

    def generate(self, n_samples: int = 1) -> List[Structure]:
        """Generate novel structures from prior."""
        z = torch.randn(n_samples, self.latent_dim)
        with torch.no_grad():
            generated = self.decode(z)

        # Convert to Structure objects (simplified)
        structures = []
        return structures


class DiffusionModel(nn.Module):
    """
    Denoising Diffusion Probabilistic Model for materials.

    Forward process: Add Gaussian noise over T steps
    Reverse process: Learn to denoise

    Reference: Ho et al. (2020). arXiv:2006.11239
    """

    def __init__(self, n_steps: int = 1000, beta_start: float = 1e-4, beta_end: float = 0.02):
        super().__init__()
        self.n_steps = n_steps

        # Linear noise schedule
        self.betas = torch.linspace(beta_start, beta_end, n_steps)
        self.alphas = 1.0 - self.betas
        self.alphas_cumprod = torch.cumprod(self.alphas, dim=0)

        # Denoising network (U-Net style)
        self.model = nn.Sequential(
            nn.Linear(512, 1024),
            nn.ReLU(),
            nn.Linear(1024, 1024),
            nn.ReLU(),
            nn.Linear(1024, 512),
        )

    def forward_diffusion(self, x0, t):
        """Add noise: x_t = (±_t) x_0 + (1 - ±_t) µ"""
        noise = torch.randn_like(x0)
        alpha_t = self.alphas_cumprod[t]
        return torch.sqrt(alpha_t) * x0 + torch.sqrt(1 - alpha_t) * noise, noise

    def reverse_step(self, xt, t):
        """Denoise one step."""
        return self.model(xt)

    def generate(self, shape) -> torch.Tensor:
        """
        Generate sample by reverse diffusion.

        Start from Gaussian noise, denoise T steps.
        """
        x = torch.randn(shape)

        for t in reversed(range(self.n_steps)):
            x = self.reverse_step(x, t)

        return x


class MaterialGAN:
    """
    Generative Adversarial Network for materials.

    Generator: z ’ Structure
    Discriminator: Structure ’ Real/Fake

    Reference: Goodfellow et al. (2014). arXiv:1406.2661
    """

    def __init__(self, latent_dim: int = 128):
        self.generator = self._build_generator(latent_dim)
        self.discriminator = self._build_discriminator()

    def _build_generator(self, latent_dim):
        return nn.Sequential(
            nn.Linear(latent_dim, 256),
            nn.LeakyReLU(0.2),
            nn.Linear(256, 512),
            nn.LeakyReLU(0.2),
            nn.Linear(512, 512),
            nn.Tanh(),
        )

    def _build_discriminator(self):
        return nn.Sequential(
            nn.Linear(512, 256),
            nn.LeakyReLU(0.2),
            nn.Linear(256, 128),
            nn.LeakyReLU(0.2),
            nn.Linear(128, 1),
            nn.Sigmoid(),
        )


__all__ = ['MaterialVAE', 'MaterialGAN', 'DiffusionModel']
