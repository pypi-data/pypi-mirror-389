import argparse
from .predict import run_nnunet_prediction, rename_prediction_file

def main():
    parser = argparse.ArgumentParser(description="Prédiction pulmonaire avec nnUNetv2")
    parser.add_argument("--mode", default="Invivo", choices=["Invivo", "Exvivo"])
    parser.add_argument("--structure", required=True, choices=["Parenchyma", "Airways", "Vascular", "ParenchymaAirways", "All", "Lobes"])
    parser.add_argument("--input", required=True, help="Image d'entrée (.nii, .mha, .nrrd...)")
    parser.add_argument("--output", default="prediction", help="Dossier de sortie")
    parser.add_argument("--models_dir", required=True, help="Dossier pour stocker les modèles")
    parser.add_argument("--name", default="prediction", help="Nom du fichier final")

    args = parser.parse_args()

    prediction_file = run_nnunet_prediction(
        mode=args.mode,
        structure=args.structure,
        input_path=args.input,
        output_dir=args.output,
        models_dir=args.models_dir,
        name=args.name
    )

    rename_prediction_file(prediction_file, args.name)


if __name__ == "__main__":
    main()

