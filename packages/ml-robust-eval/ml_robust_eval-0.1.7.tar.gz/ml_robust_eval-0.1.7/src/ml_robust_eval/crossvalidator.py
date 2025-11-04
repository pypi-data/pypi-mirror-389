import random

class CrossValidatorCalc:
    def k_fold_splitter(self, X, y, k=5, seed=None):
        idx = list(range(len(X)))
        if seed is not None:
            random.seed(seed)
        random.shuffle(idx)
        fold_size = len(X) // k
        folds = []
        for i in range(k):
            test_idx_ = idx[i*fold_size:(i+1)*fold_size]
            train_idx_ = idx[:i*fold_size] + idx[(i+1)*fold_size:]
            folds.append((train_idx_, test_idx_))
        return folds

class ABTesterTool:
    def ab_testing(self, metric_func, y_true_a, y_pred_a, y_true_b, y_pred_b):
        score_a = metric_func(y_true_a, y_pred_a)
        score_b = metric_func(y_true_b, y_pred_b)
        return {'A': score_a, 'B': score_b, 'diff': score_a - score_b}
