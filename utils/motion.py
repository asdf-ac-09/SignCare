import numpy as np


def add_velocity(sequence):

    velocity = np.diff(sequence, axis=0)

    velocity = np.vstack([velocity[0], velocity])

    # emphasize motion
    velocity = velocity * 2.0

    return np.concatenate([sequence, velocity], axis=1)



#FOR BEAST MODEL