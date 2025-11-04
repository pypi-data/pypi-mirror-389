__version__ = "0.1.14"

# Définition du contexte global partagé entre le package et Slicer
GLOBAL_CONTEXT = {
    "dataset_json_path": None,
    "dataset_labels": None,
}

# (optionnel mais propre)
def get_dataset_json_path():
    """Renvoie le chemin actuel du dataset.json stocké dans le contexte global."""
    return GLOBAL_CONTEXT.get("dataset_json_path")

__all__ = ["get_dataset_json_path"]
