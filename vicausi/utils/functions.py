import numpy as np
from scipy.stats.kde import gaussian_kde
from numpy.linalg import LinAlgError
from scipy.signal import unit_impulse

def retrieve_intervention_info(intervention):
    i_var = None    
    i_value_idx = None
    i_value = None
    if intervention: # not an empty dict
        i_var = list(intervention.keys())[0]
        if "i_value_idx" in intervention[i_var]:
            i_value_idx = intervention[i_var]["i_value_idx"]
        if "i_value" in intervention[i_var]:
            i_value = intervention[i_var]["i_value"]
    return i_var, i_value_idx, i_value
    
def kde_support(bw, bin_range=(0,1), n_samples=100, cut=3, clip=(None,None)):
    """
        Establish support for a kernel density estimate.
    """
    kmin, kmax = bin_range[0] - bw * cut, bin_range[1] + bw * cut
    if clip[0] is not None and np.isfinite(clip[0]):
        kmin = max(kmin, clip[0])
    if clip[1] is not None and np.isfinite(clip[1]):
        kmax = max(kmax, clip[1])
    return np.linspace(kmin, kmax, n_samples)

def get_impulse(x_sample, filled, impulse_shape = 20):
    y = unit_impulse(impulse_shape,'mid')
    x = np.arange(x_sample-(impulse_shape/2.), x_sample+(impulse_shape/2.)) 
    if filled:
        x=np.append(x,x[-1])
        x=np.insert(x, 0, x[0], axis=0)
        y=np.append(y,0.0)
        y=np.insert(y, 0, 0.0, axis=0)
    return dict(x=x,y=y)

def kde(samples, filled = False):
    try:
        if len(samples) == 0:
            return dict(x = np.array([]), y = np.array([]))
        if isinstance(samples, list):
            samples = np.array(samples)
        samples = samples.flatten()
        if len(samples)==1:
            return get_impulse(samples[0], filled)
        else:
#         if ~np.isfinite(samples).all():
#             samples = get_finite_samples(samples)
            kde_samples = gaussian_kde(samples)
            bw = kde_samples.scotts_factor() * samples.std(ddof=1)
            #x = _kde_support(bw, bin_range=(samples.min(),samples.max()), clip=(samples.min(),samples.max()))
            x = kde_support(bw, bin_range=(samples.min(),samples.max()))      
            y = kde_samples(x)
            if filled:
                x = np.append(x, x[-1])
                x = np.insert(x, 0, x[0], axis=0)
                y = np.append(y, 0.0)
                y = np.insert(y, 0, 0.0, axis=0)
            return dict(x = x, y = y)
    except ValueError:
        print("KDE cannot be estimated because {} samples were provided to kde".format(len(samples)))
        return dict(x=np.array([]),y=np.array([])) 
    except LinAlgError as err:
        if 'singular matrix' in str(err):
            print("KDE: singular matrix")
            return get_impulse(0., filled)
        else:
            raise

def pmf(samples):
    """
        Estimate probability mass function.
    """
    # samples = np.asarray(samples, dtype=np.float64).flatten()
    if isinstance(samples, list):
        samples = np.array(samples)
    samples = samples.flatten()
    if ~np.isfinite(samples).all():
        samples = get_finite_samples(samples)
    x = np.sort( np.unique(samples))
    y = np.asarray([ np.count_nonzero(samples == xi) / len(samples) for xi in x])
    return dict(x=x,y=y,y0=np.zeros(len(x)))

## VAR PLOTS
def get_data_hgh_indices(node, nodes, num_points = 5):
        nodes = np.asarray(nodes)
        dist_2 = (nodes - node)**2
        cn_idx = np.argmin(dist_2)
        ##
        sorted_idx = np.argsort(nodes)
        index, = np.where(sorted_idx == cn_idx)
        index = index[0]
        ##
        half_p = int((num_points-1)/2)
        start_idx = 0
        end_idx = 0
        if index - half_p < 0:
            start_idx = 0
        else:
            start_idx = index - half_p
        if len(sorted_idx) - half_p < 0:
            end_idx = len(sorted_idx)
        else:
            end_idx = index + half_p + 1
        return sorted_idx[start_idx:end_idx]