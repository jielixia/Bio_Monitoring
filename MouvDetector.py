

import numpy as np

from scipy.ndimage import gaussian_filter1d 

class MovementDetector:
    def __init__(self):
        """
        Initialize the MovementDetector.

        """
         

    def detect_movement(self, signal):
        """
        Detect movement in the signal based on variance over the sliding window.

        Parameters:
        - signal: The raw signal data.

        Returns:
        - movement_start, movment_end: Indices where movement is detected.
        """
        

        # Lissage du signal avec un filtre gaussien
        sigma = 30  # Le paramètre sigma contrôle l'étendue du lissage
        smoothed_signal = gaussian_filter1d(signal, sigma=sigma)

        # Calcul de la moyenne du signal lissé
        mean_smoothed = np.mean(smoothed_signal)

        # Seuil de détection de mouvement basé sur le signal lissé
        tolerance_min = mean_smoothed - 10
        tolerance_max = mean_smoothed + 10

        # Détection du mouvement
        movement_indices = np.where((smoothed_signal < tolerance_min) | (smoothed_signal > tolerance_max))[0]

        # Trouver les indices de début et de fin du mouvement
        if len(movement_indices) > 0:
            movement_start = movement_indices[0]
            movement_end = movement_indices[-1]
        else:
            movement_start = movement_end = None

        # print(f"Movement detected from index {movement_start} to {movement_end}")

        return movement_start, movement_end

