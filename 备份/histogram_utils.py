import numpy as np

def draw_histogram(data, ax, mode="axial"):
    flat = data.flatten()
    ax.hist(flat, bins=100, color="steelblue", edgecolor="black")
    ax.set_title(f"{mode.capitalize()} Histogram")
    ax.set_xlabel("Intensity")
    ax.set_ylabel("Pixel Count")
    ax.figure.tight_layout()

