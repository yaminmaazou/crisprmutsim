from random import Random


def geometric_mean_alpha(rng: Random, alpha: float) -> int:
    p = 1.0 / alpha

    k = 1
    while rng.random() > p:
        k += 1
    return k
