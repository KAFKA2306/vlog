import matplotlib.pyplot as plt

def apply_design_system():
    """Human-Centric & Borderless Design System (Digital Agency x Serendie)"""
    plt.rcParams.update({
        'axes.facecolor': '#0A0A12',
        'figure.facecolor': '#0A0A12',
        'axes.edgecolor': '#00A3AF',
        'text.color': '#FFFFFF',
        'axes.labelcolor': '#FFFFFF',
        'xtick.color': '#FFFFFF',
        'ytick.color': '#FFFFFF',
        'grid.color': '#FFFFFF',
        'grid.alpha': 0.1,
        'font.family': 'sans-serif',
    })
    # Digital Blue, Serendie Teal, Vibrant Pink
    plt.rcParams['axes.prop_cycle'] = plt.cycler(color=['#005CB9', '#00A3AF', '#FF2A6D'])
