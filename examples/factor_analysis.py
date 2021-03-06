import numpy as np
np.random.seed(1)

from pybasicbayes.util.text import progprint_xrange
import matplotlib.pyplot as plt
from matplotlib.cm import get_cmap

import pybasicbayes.models.factor_analysis
reload(pybasicbayes.models.factor_analysis)
from pybasicbayes.models.factor_analysis import FactorAnalysis

N = 2000
D_obs = 20
D_latent = 2

def principal_angle(A,B):
    """
    Find the principal angle between two subspaces
    spanned by columns of A and B
    """
    from numpy.linalg import qr, svd
    qA, _ = qr(A)
    qB, _ = qr(B)
    U,S,V = svd(qA.T.dot(qB))
    return np.arccos(min(S.min(), 1.0))

def generate_synth_data():

    # Create a true model and sample from it
    mask = np.random.rand(N,D_obs) < 0.9
    true_model = FactorAnalysis(D_obs, D_latent)
    true_data = true_model.generate(N=N, mask=mask, keep=True)
    return true_model, true_data


def plot_results(lls, angles, Ztrue, Zinf):
    # Plot log probabilities
    plt.figure()
    plt.plot(lls)
    plt.ylabel("Log Likelihood")
    plt.xlabel("Iteration")

    plt.figure()
    plt.plot(np.array(angles) / np.pi * 180.)
    plt.ylabel("Principal Angle")
    plt.xlabel("Iteration")

    # Plot locations, color by angle
    N = Ztrue.shape[0]
    inds_to_plot = np.random.randint(0, N, min(N, 500))
    th = np.arctan2(Ztrue[:,1], Ztrue[:,0])
    nperm = np.argsort(np.argsort(th))
    cmap = get_cmap("jet")

    plt.figure()
    plt.subplot(121)
    for n in inds_to_plot:
        plt.plot(Ztrue[n,0], Ztrue[n,1], 'o', markerfacecolor=cmap(nperm[n] / float(N)), markeredgecolor="none")
    plt.title("True Embedding")
    plt.xlim(-4,4)
    plt.ylim(-4,4)

    plt.subplot(122)
    for n in inds_to_plot:
        plt.plot(Zinf[n,0], Zinf[n,1], 'o', markerfacecolor=cmap(nperm[n] / float(N)), markeredgecolor="none")
    plt.title("Inferred Embedding")
    plt.xlim(-4,4)
    plt.ylim(-4,4)

    plt.show()

def gibbs_example(true_model, true_data):
    X, mask = true_data.X, true_data.mask

    # Fit a test model
    model = FactorAnalysis(
        D_obs, D_latent,
        # W=true_model.W, sigmasq=true_model.sigmasq
        )
    inf_data = model.add_data(X, mask=mask)

    lps = []
    angles = []
    N_iters = 100
    for _ in progprint_xrange(N_iters):
        model.resample_model()
        lps.append(model.log_likelihood())
        angles.append(principal_angle(true_model.W, model.W))

    plot_results(lps, angles, true_data.Z, inf_data.Z)

def em_example(true_model, true_data):
    X, mask = true_data.X, true_data.mask

    # Fit a test model
    model = FactorAnalysis(
        D_obs, D_latent,
        # W=true_model.W, sigmasq=true_model.sigmasq
        )
    inf_data = model.add_data(X, mask=mask)

    lps = []
    angles = []
    N_iters = 100
    for _ in progprint_xrange(N_iters):
        model.EM_step()
        lps.append(model.log_likelihood())
        angles.append(principal_angle(true_model.W, model.W))

    plot_results(lps, angles, true_data.Z, inf_data.E_Z)

def meanfield_example(true_model, true_data):
    X, mask = true_data.X, true_data.mask

    # Fit a test model
    model = FactorAnalysis(
        D_obs, D_latent,
        # W=true_model.W, sigmasq=true_model.sigmasq
        )
    inf_data = model.add_data(X, mask=mask)

    lps = []
    angles = []
    N_iters = 100
    for _ in progprint_xrange(N_iters):
        model.meanfield_coordinate_descent_step()
        lps.append(model.expected_log_likelihood())
        E_W, _, _, _ = model.regression.mf_expectations
        angles.append(principal_angle(true_model.W, E_W))

    plot_results(lps, angles, true_data.Z, inf_data.Z)

def svi_example(true_model, true_data):
    X, mask = true_data.X, true_data.mask

    # Fit a test model
    model = FactorAnalysis(
        D_obs, D_latent,
        # W=true_model.W, sigmasq=true_model.sigmasq
        )

    # Add the data in minibatches
    minibatchsize = 250
    for start in range(0, N, minibatchsize):
        end = min(start + minibatchsize, N)
        model.add_data(X[start:end], mask=mask[start:end])

    lps = []
    angles = []
    N_iters = 100
    delay = 10.0
    forgetting_rate = 0.75
    stepsize = (np.arange(N_iters) + delay)**(-forgetting_rate)
    for itr in progprint_xrange(N_iters):
        lps.append(model.meanfield_sgdstep(stepsize[itr]))
        E_W, _, _, _ = model.regression.mf_expectations
        angles.append(principal_angle(true_model.W, E_W))

    Z_inf = model.data_list[0].E_Z
    Z_true = true_data.Z[:Z_inf.shape[0]]
    plot_results(lps, angles, Z_true, Z_inf)

if __name__ == "__main__":
    true_model, true_data = generate_synth_data()
    gibbs_example(true_model, true_data)
    em_example(true_model, true_data)
    meanfield_example(true_model, true_data)
    svi_example(true_model, true_data)
