class ClassifMetricsCalc:
    def accuracy_calc(self, y_true, y_pred):
        return sum(yt == yp for yt, yp in zip(y_true, y_pred)) / len(y_true)

    def precision_calc(self, y_true, y_pred):
        t = sum((yt == yp == 1) for yt, yp in zip(y_true, y_pred))
        f = sum((yt == 0 and yp == 1) for yt, yp in zip(y_true, y_pred))
        return t / (t + f + 1e-8)

    def recall_calc(self, y_true, y_pred):
        t = sum((yt == yp == 1) for yt, yp in zip(y_true, y_pred))
        f = sum((yt == 1 and yp == 0) for yt, yp in zip(y_true, y_pred))
        return t / (t + f + 1e-8)

    def f1_score_calc(self, y_true, y_pred):
        pr = self.precision_calc(y_true, y_pred)
        re = self.recall_calc(y_true, y_pred)
        return 2 * pr * re / (pr + re + 1e-8)

    def confusion_matrix_(self, y_true, y_pred):
        classes_ = sorted(set(y_true) | set(y_pred))
        matrix_ = [[0 for _ in classes_] for _ in classes_]
        for yt, yp in zip(y_true, y_pred):
            matrix_[classes_.index(yt)][classes_.index(yp)] += 1
        return matrix_

class RegressionMetricsCalc:
    def mae_calc(self, y_true, y_pred):
        return sum(abs(yt - yp) for yt, yp in zip(y_true, y_pred)) / len(y_true)

    def mse_calc(self, y_true, y_pred):
        return sum((yt - yp) ** 2 for yt, yp in zip(y_true, y_pred)) / len(y_true)

    def r2_score_calc(self, y_true, y_pred):
        mean_true_ = sum(y_true) / len(y_true)
        ss_to = sum((yt - mean_true_) ** 2 for yt in y_true)
        ss_re = sum((yt - yp) ** 2 for yt, yp in zip(y_true, y_pred))
        return 1 - ss_re / (ss_to + 1e-8)

class NLPMetricsCalc:
    def bleu_calc(self, reference_, candidate_):
        ref_words = reference_.split()
        cand_words = candidate_.split()
        overlap_ = len(set(ref_words) & set(cand_words))
        return overlap_ / (len(cand_words) + 1e-8)

class CVMetricsCalc:
    def iou_calc(self, boxA, boxB):
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        interArea = max(0, xB - xA) * max(0, yB - yA)
        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        return interArea / float(boxAArea + boxBArea - interArea + 1e-8)
