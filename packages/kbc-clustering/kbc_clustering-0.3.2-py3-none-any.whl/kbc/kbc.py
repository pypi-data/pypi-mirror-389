"""
KBC clustering — Kernel-Bounded Clustering: Achieving the Objective of Spectral Clustering without Eigendecomposition in Artificial Intelligence Journal (AIJ) 2025.
Author: Hang Zhang
"""

import warnings
import numpy as np
import torch
import math
from tqdm import trange
from sklearn.base import BaseEstimator, ClusterMixin
from sklearn.utils import check_array, check_random_state
from scipy.sparse.csgraph import connected_components
from scipy.sparse import csr_matrix

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')


class KBC(BaseEstimator, ClusterMixin):
    """
    KBC: Isolation-Kernel + Binary Connected-component Clustering

    Parameters
    ----------
    k : int
        Number of clusters.
    tau : float
        Threshold for binarising the subgraph (relative to max kernel value).
    psi : int
        Number of centroids per isolation-tree.
    t : int, default=100
        Number of isolation trees.
    subsample_size : int, default=10_000
        Size of subset used to build the kernel matrix.
    batch_size : int, default=10_000
        GPU batch size for IK transform.
    random_state : int or None, default=None
        Random seed for reproducibility.
    post_processing : bool, default=False
        Refine labels with k-means iterations after graph clustering.

    Attributes
    ----------
    labels_ : ndarray of shape (n_samples,)
        Cluster labels (0-based).
    """

    def __init__(self, k: int, tau: float, psi: int, t: int = 100,
                 subsample_size: int = 10_000, batch_size: int = 10_000,
                 random_state=None, post_processing: bool = False, device: torch.device = 'None'):
        self.k = k
        self.tau = tau
        self.psi = psi
        self.t = t
        self.subsample_size = subsample_size
        self.batch_size = batch_size
        self.random_state = random_state
        self.post_processing = post_processing
        self.device = device

    def fit(self, X, y=None):
        """
        Perform clustering.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : Ignored
            Not used, present for sklearn API consistency.

        Returns
        -------
        self : object
        """
        X = check_array(X, dtype=np.float32, order='C')
        n, d = X.shape

        if self.device == 'None':
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # Ensure psi is at least 2 to avoid degenerate radius
        psi = max(2, min(self.psi, n))
        print("transforming data into Kernel space...")
        ik = _IsolationKernel(t=self.t, psi=psi, device=self.device)
        ik.fit(X)
        self.ndata = ik.transform(X, batch_size=self.batch_size)  # (n, t*psi), int8

        rng = check_random_state(self.random_state)
        s = min(self.subsample_size, n)
        sID = rng.choice(n, s, replace=False)

        # Move subset to GPU for kernel computation
        sub = torch.tensor(self.ndata[sID], dtype=torch.float32, device=self.device)  # (s, t*psi)

        # Compute kernel on subset
        K = sub @ sub.T  # (s, s)
        tau_s = self.tau * float(K.max().item())
        Kg = (K >= tau_s).int()

        n_comp, labels_sub = connected_components(
            csr_matrix(Kg.cpu().numpy()), directed=False
        )
        labels_sub = torch.from_numpy(labels_sub).to(self.device, dtype=torch.int32)

        if n_comp < self.k:
            raise ValueError(
                f"KBC found only {n_comp} connected components, "
                f"but k={self.k} was requested. Try increasing tau (current={self.tau:.4f})."
            )

        # Select top-k largest components
        comp_size = np.bincount(labels_sub.cpu().numpy(), minlength=n_comp)
        topk_idx = np.argsort(comp_size)[-self.k:][::-1]

        sub2full = torch.full((s,), -1, dtype=torch.int32, device=self.device)
        for new_id, old_id in enumerate(topk_idx):
            sub2full[labels_sub == old_id] = new_id

        # Assign unassigned points in subset to nearest centroid (by IK similarity)
        centers = torch.stack([
            sub[sub2full == cid].mean(dim=0) for cid in range(self.k)
        ])  # (k, t*psi)

        unassigned = (sub2full == -1)
        # if unassigned.any():
        #     similarity = sub[unassigned] @ centers.T  # (n_unassigned, k)
        #     sub2full[unassigned] = similarity.argmax(dim=1).to(torch.int32)

        if unassigned.any():
            chunk_size = 10000
            unassigned_indices = torch.where(unassigned)[0]
            for i in trange(0, len(unassigned_indices), chunk_size, desc="Assigning data to the distribution", leave=False):
                idx_chunk = unassigned_indices[i:i + chunk_size]
                sub_chunk = sub[idx_chunk] 
                sim_chunk = sub_chunk @ centers.T   
                best_center = sim_chunk.argmax(dim=1).to(torch.int32)
                sub2full[idx_chunk] = best_center


        # Propagate labels to full dataset
        full_labels = torch.full((n,), -1, dtype=torch.int32, device=self.device)
        full_labels[sID] = sub2full

        # Optional refinement via k-means in IK space
        if self.post_processing:
            ndata_tensor = torch.tensor(self.ndata, dtype=torch.float32, device=self.device)
            full_labels = self._refine_gpu(ndata_tensor, full_labels, self.k)

        self.labels_ = full_labels.cpu().numpy()
        return self

    def fit_predict(self, X, y=None):
        """Return cluster labels."""
        return self.fit(X, y).labels_

    @torch.no_grad()
    def _refine_gpu(self, ndata, labels, k, max_iter=100, tol=0.01):
        """
        Refine labels using k-means-style updates in the Isolation Kernel space.

        Parameters
        ----------
        ndata : torch.Tensor, shape (n_samples, n_features_ik)
            Data in Isolation Kernel space (dense float32).
        labels : torch.Tensor, shape (n_samples,)
            Current cluster labels (0-based).
        k : int
            Number of clusters.
        max_iter : int
            Maximum number of refinement iterations.
        tol : float
            Convergence threshold (fraction of points that can change).

        Returns
        -------
        new_labels : torch.Tensor, shape (n_samples,)
            Refined labels.
        """
        n = ndata.shape[0]
        th = max(1, int(math.ceil(tol * n)))
        for _ in range(max_iter):
            # Recompute centroids
            centers = torch.stack([
                ndata[labels == c].mean(dim=0) for c in range(k)
            ])  # (k, d_ik)

            # Assign to most similar centroid (max inner product)
            similarity = ndata @ centers.T  # (n, k)
            new_labels = similarity.argmax(dim=1).to(labels.dtype)  # 0-based

            if (new_labels != labels).sum().item() < th:
                break
            labels = new_labels
        return labels


# ===================================================================
# Isolation-Kernel GPU implementation (internal use only) @Yi-xiao Ma
# ===================================================================
class _IsolationKernel:
    """Minimal GPU Isolation-Kernel transformer."""

    def __init__(self, t: int, psi: int, device: torch.device):
        self.device = device
        self._t = t
        self._psi = psi
        self._center_index_list = None
        self._radius_list = None
        self.X = None

    def fit(self, X: np.ndarray):
        self.X = X
        n_samples = X.shape[0]

        if self._psi > n_samples:
            self._psi = n_samples
            warnings.warn(f"psi is set to {n_samples} "
                          "as it is greater than the number of data points.")

        rng = np.random.default_rng()
        self._center_index_list = np.vstack([
            rng.choice(n_samples, size=self._psi, replace=False)
            for _ in range(self._t)
        ])  # shape=(t, psi)

        self._center_list = np.zeros((self._t * self._psi, X.shape[1]), dtype=X.dtype)
        self._radius_list = torch.zeros((self._t, self._psi), dtype=torch.float32, device=self.device)

        for i in range(self._t):
            sample = X[self._center_index_list[i]]
            self._center_list[i * self._psi:(i + 1) * self._psi] = sample

            sample_cuda = torch.tensor(sample, dtype=torch.float32, device=self.device)
            s2s = torch.cdist(sample_cuda, sample_cuda, p=2)
            s2s.fill_diagonal_(float('inf'))
            self._radius_list[i] = torch.min(s2s, dim=0).values
        return self

    def transform(self, X: np.ndarray, batch_size: int = 10000):
        if X.ndim == 1:
            X = X.reshape(1, -1)

        n_samples = X.shape[0]
        output = torch.zeros((n_samples, self._psi * self._t), device='cpu', dtype=torch.int8)

        for start in trange(0, n_samples, batch_size, desc="Transforming data to Kernel space", leave=False):
            end = min(start + batch_size, n_samples)
            batch_cuda = torch.tensor(X[start:end], dtype=torch.float32, device=self.device)

            for i in range(self._t):
                sl = slice(i * self._psi, (i + 1) * self._psi)
                sample_cuda = torch.tensor(self._center_list[sl], dtype=torch.float32, device=self.device)

                p2s = torch.cdist(batch_cuda, sample_cuda, p=2)
                p2ns_idx = torch.argmin(p2s, dim=1)
                p2ns = p2s[torch.arange(p2ns_idx.size(0), device=self.device), p2ns_idx]
                accept = p2ns <= self._radius_list[i, p2ns_idx]

                col_idx = p2ns_idx[accept] + i * self._psi
                output[start:end][accept, col_idx] = 1

        # Always return 2D array for consistency
        return output.numpy()