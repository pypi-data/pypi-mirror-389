import random

class TestCaseGeneratorT:
    def gen_edge_cases(self, X, feature_ranges):
        edge_cases = []
        for i, (fmin, fmax) in enumerate(feature_ranges):
            for val in [fmin, fmax]:
                for sample in X:
                    new_sample = list(sample)
                    new_sample[i] = val
                    edge_cases.append(new_sample)
        return edge_cases

    def gen_boundary_cases(self, X, feature_ranges, delta=1e-3):
        boundary_cases = []
        for i, (fmin, fmax) in enumerate(feature_ranges):
            for val in [fmin + delta, fmax - delta]:
                for sample in X:
                    new_sample = list(sample)
                    new_sample[i] = val
                    boundary_cases.append(new_sample)
        return boundary_cases

    def gen_adversarial_cases(self, X, epsilon=0.01):
        adv_cases = []
        for sample in X:
            new_sample = [x + random.choice([-epsilon, epsilon]) for x in sample]
            adv_cases.append(new_sample)
        return adv_cases
