import numpy as np
from itertools import permutations
from sklearn.metrics import accuracy_score

#####################################################################################################################

def adjusted_score(y_pred, y_true, metric=accuracy_score):
    """
    Computes the adjusted score (accuracy, balanced accuracy, etc.) as the maximum
    score obtained across all possible permutations of the cluster labels (`y_pred`).

    Parameters
    ----------
    y_pred : numpy.ndarray
        Predicted cluster labels.
    y_true : numpy.ndarray
        True class labels.
    metric : callable, default=accuracy_score
        Function to compute the metric. Must accept (y_true, y_pred) and return a float.

    Returns
    -------
    adj_score : float
        The best score obtained across all permutations.
    adj_cluster_labels : numpy.ndarray
        The cluster labels permuted according to the best permutation.
    """

    permutations_list = list(permutations(np.unique(y_pred)))
    scores, permuted_cluster_labels = [], {}

    for per in permutations_list:
        permutation_dict = dict(zip(np.unique(y_pred), per))
        permuted_cluster_labels[per] = np.array([permutation_dict[x] for x in y_pred])
        scores.append(metric(y_true=y_true, y_pred=permuted_cluster_labels[per]))

    scores = np.array(scores)
    best_permutation = permutations_list[np.argmax(scores)]
    adj_cluster_labels = permuted_cluster_labels[best_permutation]
    adj_score = np.max(scores)

    return adj_score, adj_cluster_labels

#####################################################################################################################