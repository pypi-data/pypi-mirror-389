"""
Script de ligne de commande pour l'utilisation de idf2table.
"""
import argparse
from pathlib import Path

from eppy.modeleditor import IDF

from idf2table.core import (
    find_idd,
    idf_to_table,
    apply_updates_from_excel,
)
from idf2table.obj_export import export_idf_to_obj, ObjExportOptions


def main():
    """
    Fonction principale pour la ligne de commande.
    """
    parser = argparse.ArgumentParser(
        description="Outils IDF2TABLE: conversion IDF↔table et application d'updates Excel",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: table (existing behavior)
    p_table = subparsers.add_parser(
        "table", help="Convertir un type d'objet IDF en DataFrame"
    )
    p_table.add_argument("idf_file", type=str, help="Chemin vers le fichier IDF")
    p_table.add_argument(
        "object_type",
        type=str,
        help="Type d'objet à convertir (ex: Material, Zone, Construction)",
    )
    p_table.add_argument("--idd", type=str, default=None, help="Chemin du fichier IDD")
    p_table.add_argument(
        "--output", "-o", type=str, default=None, help="Chemin de sortie (Excel)"
    )
    p_table.add_argument("--csv", action="store_true", help="Exporter en CSV")

    # Subcommand: apply (Excel updates)
    p_apply = subparsers.add_parser(
        "apply", help="Appliquer des mises à jour depuis un Excel sur un IDF"
    )
    p_apply.add_argument("idf_file", type=str, help="Chemin vers le fichier IDF")
    p_apply.add_argument("--excel", type=str, required=True, help="Fichier Excel d'updates")
    p_apply.add_argument("--idd", type=str, default=None, help="Chemin du fichier IDD")
    p_apply.add_argument("--sheet", type=str, default="0", help="Feuille Excel (nom ou index)")
    p_apply.add_argument("--save", type=str, default=None, help="Sauvegarder l'IDF mis à jour")

    # Subcommand: export-obj
    p_obj = subparsers.add_parser(
        "export-obj", help="Exporter la géométrie IDF en Wavefront OBJ"
    )
    p_obj.add_argument("idf_file", type=str, help="Chemin vers le fichier IDF")
    p_obj.add_argument("--obj", type=str, required=True, help="Fichier OBJ de sortie")
    p_obj.add_argument("--idd", type=str, default=None, help="Chemin du fichier IDD")
    p_obj.add_argument("--with-fenestration", action="store_true", help="Inclure les sous-surfaces (fenêtres/portes)")
    p_obj.add_argument("--with-shading", action="store_true", help="Inclure les ombrages")
    p_obj.add_argument("--flip-normals", action="store_true", help="Inverser l'orientation des faces")
    p_obj.add_argument("--mtl", type=str, default=None, help="Chemin fichier MTL (en option)")

    args = parser.parse_args()

    if args.command == "table":
        # Config IDD
        try:
            if args.idd:
                IDF.setiddname(args.idd)
                print(f"Fichier IDD utilisé: {args.idd}")
            else:
                idd_path = find_idd()
                IDF.setiddname(str(idd_path))
                print(f"Fichier IDD utilisé: {idd_path}")
        except FileNotFoundError as e:
            print(f"Erreur: {e}")
            return 1

        # Charger IDF
        try:
            idf = IDF(args.idf_file)
        except Exception as e:
            print(f"Erreur lors du chargement du fichier IDF: {e}")
            return 1

        # Convert
        try:
            print(f"Conversion des objets {args.object_type}...")
            df = idf_to_table(idf, args.object_type)
        except ValueError as e:
            print(f"Erreur: {e}")
            return 1

        print(f"\nDataFrame créé avec {len(df)} lignes et {len(df.columns)} colonnes")
        print("\nPremières lignes:")
        print(df.head())
        print("\nColonnes:", list(df.columns))

        if args.output:
            output_path = Path(args.output)
            if args.csv:
                df.to_csv(output_path, index=False)
                print(f"\n✓ Fichier CSV sauvegardé: {output_path}")
            else:
                df.to_excel(output_path, index=False)
                print(f"\n✓ Fichier Excel sauvegardé: {output_path}")
        elif args.csv:
            output_path = Path(args.idf_file).stem + f"_{args.object_type}.csv"
            df.to_csv(output_path, index=False)
            print(f"\n✓ Fichier CSV sauvegardé: {output_path}")

        return 0

    if args.command == "apply":
        # Parse sheet index/name
        sheet: int | str
        try:
            sheet = int(args.sheet)
        except ValueError:
            sheet = args.sheet

        try:
            updated = apply_updates_from_excel(
                idf=args.idf_file,
                excel_path=args.excel,
                idd_file=args.idd,
                sheet_name=sheet,
                save_to=args.save,
            )
        except Exception as e:
            print(f"Erreur pendant l'application des updates: {e}")
            return 1

        print("✓ Updates appliqués.")
        if args.save:
            print(f"✓ IDF sauvegardé: {args.save}")
        return 0

    if args.command == "export-obj":
        opts = ObjExportOptions(
            include_fenestration=args.with_fenestration,
            include_shading=args.with_shading,
            flip_normals=args.flip_normals,
            write_mtl=bool(args.mtl),
            mtl_path=args.mtl,
        )
        try:
            export_idf_to_obj(
                idf_or_path=args.idf_file,
                obj_path=args.obj,
                idd_file=args.idd,
                options=opts,
            )
        except Exception as e:
            print(f"Erreur export OBJ: {e}")
            return 1
        print(f"✓ OBJ exporté: {args.obj}")
        if args.mtl:
            print(f"✓ MTL exporté: {args.mtl}")
        return 0

    return 0


if __name__ == "__main__":
    exit(main())

