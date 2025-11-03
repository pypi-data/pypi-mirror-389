import numpy as np
from scipy.stats import cauchy

def cct(pvals_arr, weights_arr=None):
    ## Check if pvals_arr contains NaN values.
    if(np.isnan(pvals_arr).any()):
        raise ValueError("pvals_arr contains NaN values")

    ## Check if all pvals are between 0 and 1.
    if(np.any(pvals_arr < 0) or np.any(pvals_arr > 1)):
        raise ValueError("pvals_arr contains values outside of the range 0-1")
    
    ## Check whether there are pvals that are exactly 0 or 1.
    if(np.any(pvals_arr == 0) or np.any(pvals_arr == 1)):
        raise ValueError("pvals_arr contains values that are exactly 0 or 1")
    
    ## Check if there is only one pval.
    if(pvals_arr.ndim==0):
        return float(pvals_arr.reshape(-1)[0])
    
    ## Check if weights_arr is provided.
    if(not isinstance(weights_arr, np.ndarray)):
        weights_arr = np.full(len(pvals_arr), 1.0 / len(pvals_arr)) ## initialize the weights to 1/n.
        
    else:
        ## Check if weights_arr contains NaN values.
        if(np.isnan(weights_arr).any()):
            raise ValueError("weights_arr contains NaN values")
        ## Check if there are weights that are negative.
        if(np.any(weights_arr < 0)):
            raise ValueError("weights_arr contains negative values")
    
    ## Check if the sum of weights is 1.
    if(abs(np.sum(weights_arr) - 1) > 1E-15):
        print(np.sum(weights_arr))
        raise ValueError("the sum of weights is not 1")
    
    ## Check whether there are exteme pvals.
    mask = (pvals_arr < 1e-16)
    if(mask.any()):
        cct_stat = np.sum(weights_arr[mask] / pvals_arr[mask] / np.pi)
        cct_stat += np.sum(weights_arr[~mask] * np.tan((0.5 - pvals_arr[~mask]) * np.pi))
    else:
        cct_stat = np.sum(weights_arr * np.tan((0.5-pvals_arr)*np.pi))

    ## Check whether the cct_stat is very large.
    if(cct_stat > 1E15):
        pval = (1 / cct_stat) / np.pi
    else:
        pval = 1 - cauchy.cdf(cct_stat)

    return pval
