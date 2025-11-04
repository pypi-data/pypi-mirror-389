class Vizualizer:
    def printing_confusion_matrix(self, cm, class_names):
        print("Confusion Matrix:")
        print(" " * 10 + " ".join(f"{name:>8}" for name in class_names))
        for i, row in enumerate(cm):
            print(f"{class_names[i]:>10} " + " ".join(f"{val:8d}" for val in row))

    def printing_roc_curve(self, y_true, y_scores, steps=20):
        thresholds = [i / steps for i in range(steps+1)]
        print("Threshold\tTPR\tFPR")
        for t in thresholds:
            tp = fp = tn = fn = 0
            for yt, ys in zip(y_true, y_scores):
                pred = 1 if ys >= t else 0
                if yt == 1 and pred == 1: tp += 1
                if yt == 0 and pred == 1: fp += 1
                if yt == 0 and pred == 0: tn += 1
                if yt == 1 and pred == 0: fn += 1
            tpr = tp / (tp + fn + 1e-8)
            fpr = fp / (fp + tn + 1e-8)
            print(f"{t:.2f}\t{tpr:.3f}\t{fpr:.3f}")
