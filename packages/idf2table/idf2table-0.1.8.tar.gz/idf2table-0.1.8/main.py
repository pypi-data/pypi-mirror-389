"""
Script d'exemple utilisant le module idf2table.

Ce script peut être utilisé comme exemple ou pour des conversions rapides.
Pour une utilisation en ligne de commande, utilisez : idf2table --help
"""
from pathlib import Path

from eppy.modeleditor import IDF

from idf2table import find_idd, idf_to_table


def main(
    idf_path: str = "data/OPIO_run.idf",
    object_idf: str = "Material",
    save_xls: bool = False,
):
    """
    Exemple d'utilisation de l'outil de conversion.

    Args:
        idf_path: Chemin vers le fichier IDF
        object_idf: Type d'objet à convertir
        save_xls: Si True, sauvegarde le DataFrame en Excel
    """
    # Trouver et configurer le fichier IDD
    try:
        idd_path = find_idd()
        IDF.setiddname(str(idd_path))
        print(f"Fichier IDD utilisé: {idd_path}")
    except FileNotFoundError as e:
        print(f"Erreur: {e}")
        return

    idf = IDF(str(idf_path))

    # Convertir les objets en DataFrame
    print(f"Conversion des objets {object_idf}...")
    df_ = idf_to_table(idf, object_idf)

    print(f"\nDataFrame créé avec {len(df_)} lignes et {len(df_.columns)} colonnes")
    print("\nPremières lignes:")
    print(df_.head())

    print("\nColonnes:", list(df_.columns))

    if save_xls:
        output_file = f"{Path(idf_path).stem}_{object_idf}.xlsx"
        df_.to_excel(output_file, index=False)
        print(f"\n✓ Fichier Excel sauvegardé: {output_file}")


if __name__ == "__main__":
    # main(object_idf="Material", save_xls=True)
    # main(object_idf="BuildingSurface:Detailed")
    # main(idf_path="data/OPIO_run_hamt.idf",object_idf="Construction", save_xls=True)
    # main(
    #     idf_path="data/OPIO_run_hamt.idf",
    #     object_idf="MaterialProperty:HeatAndMoistureTransfer:SorptionIsotherm",
    #     save_xls=True,
    # )

    # main(idf_path="data/OPIO_run_hamt.idf",object_idf="Construction", save_xls=True)
    main(
        idf_path="data/pelussin_v8.idf",
        object_idf="AirflowNetwork:MultiZone:Surface",
        save_xls=True,
    )

