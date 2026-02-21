from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

data_path = str(_PROJECT_ROOT / 'assets') + '/'
networks_path = str(_PROJECT_ROOT / 'assets' / 'networks') + '/'
vis_path = str(_PROJECT_ROOT / 'assets' / 'visualisations') + '/'
