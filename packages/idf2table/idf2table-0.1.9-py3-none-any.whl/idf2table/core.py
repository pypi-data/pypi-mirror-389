"""
Fonctions principales pour la conversion IDF vers DataFrame.
"""
import os
from pathlib import Path
from typing import Union, List, Dict, Any, Optional

import pandas as pd
from eppy.modeleditor import IDF
from eppy.iddcurrent import iddcurrent
from eppy import json_functions

# Chemins possibles pour le fichier IDD EnergyPlus
POSSIBLE_IDD = [
    r"C:\EnergyPlusV9-4-0\Energy+.idd",
    r"C:\Program Files\EnergyPlusV9-4-0\Energy+.idd",
    r"/Applications/EnergyPlus-9-4-0/Energy+.idd",
    r"./EnergyPlus-9.4.0-998c4b761e-Linux-Ubuntu18.04-x86_64/Energy+.idd",
]


def find_idd() -> Path:
    """
    Trouve le fichier IDD EnergyPlus.

    Recherche le fichier IDD dans les emplacements suivants (dans cet ordre) :
    1. Variable d'environnement ENERGYPLUS_IDD
    2. Emplacements standards selon le système d'exploitation

    Returns:
        Path: Chemin vers le fichier IDD trouvé

    Raises:
        FileNotFoundError: Si aucun fichier IDD n'est trouvé

    Example:
        >>> from idf2table import find_idd
        >>> idd_path = find_idd()
        >>> IDF.setiddname(str(idd_path))
    """
    # Vérifier d'abord la variable d'environnement
    env_idd = os.getenv("ENERGYPLUS_IDD")
    if env_idd and Path(env_idd).is_file():
        return Path(env_idd)

    # Chercher dans les emplacements possibles
    for idd_path in POSSIBLE_IDD:
        p = Path(idd_path)
        if p.is_file():
            return p

    raise FileNotFoundError(
        "Fichier IDD EnergyPlus introuvable. Vérifiez que EnergyPlus est installé "
        "ou définissez la variable d'environnement ENERGYPLUS_IDD."
    )


def idf_to_table(
    idf: Union[IDF, str], object_type: str, idd_file: Union[str, None] = None
) -> pd.DataFrame:
    """
    Convertit tous les objets d'un type donné d'un fichier IDF en DataFrame pandas.

    Cette fonction permet de convertir n'importe quel type d'objet EnergyPlus (Material,
    Zone, Construction, etc.) en DataFrame pandas, où chaque ligne représente un objet
    et chaque colonne représente un attribut de l'objet.

    Args:
        idf: Objet IDF ou chemin vers le fichier .idf
        object_type: Type d'objet à convertir (ex: "Material", "MATERIAL", "Zone")
        idd_file: Chemin vers le fichier IDD (optionnel, utilise le IDD par défaut si non fourni)

    Returns:
        pd.DataFrame: DataFrame pandas où chaque ligne représente un objet et chaque
        colonne représente un attribut/champ de l'objet.

    Raises:
        ValueError: Si le type d'objet spécifié n'existe pas dans le fichier IDF
        FileNotFoundError: Si le fichier IDF ou IDD n'est pas trouvé

    Example:
        >>> from idf2table import idf_to_table, find_idd
        >>> from eppy.modeleditor import IDF
        >>>
        >>> # Configurer le fichier IDD
        >>> idd_path = find_idd()
        >>> IDF.setiddname(str(idd_path))
        >>>
        >>> # Charger le fichier IDF
        >>> idf = IDF('data/OPIO_run.idf')
        >>>
        >>> # Convertir les Material en DataFrame
        >>> materials_df = idf_to_table(idf, "Material")
        >>>
        >>> # Ou directement avec le chemin du fichier
        >>> materials_df = idf_to_table('data/OPIO_run.idf', "Material")
    """
    # Si idf est un chemin de fichier, charger le fichier
    if isinstance(idf, str):
        # Configurer le fichier IDD si nécessaire
        if idd_file:
            IDF.setiddname(idd_file)
        else:
            # Essayer de trouver le IDD automatiquement
            try:
                idd_path = find_idd()
                IDF.setiddname(str(idd_path))
            except FileNotFoundError:
                # Si find_idd() échoue, essayer iddcurrent
                try:
                    idd_file = iddcurrent.iddname()
                    IDF.setiddname(idd_file)
                except Exception:
                    # Si tout échoue, laisser eppy gérer l'erreur
                    pass
        idf = IDF(idf)

    # Normaliser le type d'objet (en majuscules pour eppy)
    object_type_upper = object_type.upper()

    # Récupérer tous les objets du type spécifié
    try:
        objects = idf.idfobjects[object_type_upper]
    except KeyError:
        raise ValueError(
            f"Type d'objet '{object_type}' non trouvé dans le fichier IDF. "
            f"Types disponibles: {list(idf.idfobjects.keys())}"
        )

    if not objects:
        # Si aucun objet trouvé, retourner un DataFrame vide
        return pd.DataFrame()

    # Identifier tous les champs disponibles en examinant le premier objet
    first_obj = objects[0]
    field_names = []

    # Les objets eppy ont un attribut fieldnames qui liste tous les champs
    if hasattr(first_obj, "fieldnames"):
        field_names = first_obj.fieldnames
    else:
        # Fallback : utiliser dir() et filtrer les attributs non privés
        # et non méthodes
        all_attrs = dir(first_obj)
        field_names = [
            attr
            for attr in all_attrs
            if not attr.startswith("_") and not callable(getattr(first_obj, attr, None))
        ]

    # Créer une liste de dictionnaires, un par objet
    data: List[Dict[str, Any]] = []
    for obj in objects:
        row = {}
        for field_name in field_names:
            try:
                # Essayer d'accéder au champ via getattr ou notation []
                if hasattr(obj, field_name):
                    value = getattr(obj, field_name)
                elif hasattr(obj, "__getitem__"):
                    value = obj[field_name]
                else:
                    value = None

                # Nettoyer la valeur si c'est une chaîne (supprimer espaces)
                if isinstance(value, str):
                    value = value.strip()

                row[field_name] = value
            except (AttributeError, KeyError, IndexError):
                # Si le champ n'existe pas pour cet objet, mettre None
                row[field_name] = None
        data.append(row)

    # Créer le DataFrame
    df = pd.DataFrame(data)

    return df


# ------------------------ Excel → JSON mapping ------------------------

def _normalize_field_name(field: str) -> str:
    """Normalize an IDF field label to the json_functions key style.

    Example: "Version Identifier" -> "Version_Identifier".
    Non-alphanumeric characters are converted to underscores and multiple
    underscores are collapsed to a single underscore.
    """
    if field is None:
        return ""
    # Replace non-alphanumeric characters with underscore
    import re

    normalized = re.sub(r"[^0-9A-Za-z]+", "_", str(field).strip())
    # Collapse multiple underscores
    normalized = re.sub(r"_+", "_", normalized)
    # Remove leading/trailing underscores
    return normalized.strip("_")


def excel_to_update_mapping(
    path: Union[str, Path], sheet_name: Union[int, str] = 0
) -> Dict[str, Any]:
    """
    Convertit un Excel/CSV "large" (export `idf_to_table`) en mapping
    compatible `eppy.json_functions.updateidf`.

    Format attendu (insensible à la casse):
      - Colonne `key` (type d'objet par ligne, ex: "Material")
      - Colonne `Name` (nom de l'objet)
      - Autres colonnes = champs à mettre à jour (ex: Conductivity, Density)

    Le mapping retourné utilise des clés de type:
        idf.{OBJECT}.{NAME}.{FIELD}
    avec OBJECT en MAJUSCULES et FIELD normalisé en `Field_Name`.
    """

    def _read_table(p: Path) -> pd.DataFrame:
        return pd.read_csv(p) if p.suffix.lower() == ".csv" else pd.read_excel(p, sheet_name=sheet_name)

    def _find_case_insensitive(df_cols: List[str], targets: List[str]) -> Optional[str]:
        lookup = {c.lower(): c for c in df_cols}
        for t in targets:
            if t in lookup:
                return lookup[t]
        return None

    def _cast_value_raw(val: Any) -> Any:
        if pd.isna(val):
            return None
        if isinstance(val, str):
            v = val.strip()
            if v == "":
                return None
            low = v.lower()
            if low in {"yes", "no"}:
                return "Yes" if low == "yes" else "No"
            try:
                if "." in v or "e" in low:
                    return float(v)
                return int(v)
            except Exception:
                return v
        return val

    path = Path(path)
    df = _read_table(path)

    # Détecter colonnes 'key' et 'Name'
    key_col = _find_case_insensitive(list(df.columns), ["key"])
    name_col = _find_case_insensitive(list(df.columns), ["name", "nom"])
    if key_col is None or name_col is None:
        raise ValueError(
            "Fichier d'updates invalide: colonnes 'key' et/ou 'Name' introuvables. "
            "Utilisez un export idf_to_table (key, Name, ...)."
        )

    # Colonnes de valeurs (tous les champs sauf key/Name)
    value_cols = [c for c in df.columns if c not in {key_col, name_col}]
    if not value_cols:
        return {}

    # Dérouler en format long
    df_long = (
        df.melt(
            id_vars=[key_col, name_col],
            value_vars=value_cols,
            var_name="field",
            value_name="value",
        )
        .rename(columns={key_col: "object_type", name_col: "object_name"})
    )

    # Normalisation objet/nom/champ
    df_long["object_type"] = df_long["object_type"].astype(str).str.strip()
    df_long["object_name"] = df_long["object_name"].astype(str).str.strip()
    df_long["field"] = df_long["field"].astype(str).str.strip()

    # Nettoyage lignes vides
    df_long = df_long[(df_long["field"] != "") & df_long["value"].notna()]

    # Normaliser label de champ et caster la valeur
    df_long["field_norm"] = df_long["field"].map(_normalize_field_name)
    df_long["value_cast"] = df_long["value"].map(_cast_value_raw)
    df_long = df_long[df_long["value_cast"].notna()]

    # Construction du mapping (vectorisée)
    keys = (
        "idf." + df_long["object_type"].astype(str)
        + "." + df_long["object_name"].astype(str)
        + "." + df_long["field_norm"].astype(str)
    )
    values = df_long["value_cast"].tolist()
    mapping: Dict[str, Any] = dict(zip(keys.tolist(), values))

    return mapping


def apply_updates_from_excel(
    idf: Union[IDF, str],
    excel_path: Union[str, Path],
    idd_file: Union[str, None] = None,
    sheet_name: Union[int, str] = 0,
    save_to: Union[str, Path, None] = None,
    save_encoding: str = "utf-8",
) -> IDF:
    """
    Apply updates described in an Excel file to an IDF using eppy.json_functions.

    Args:
      idf: IDF object or path to .idf file
      excel_path: Excel file path containing updates (see excel_to_update_mapping)
      idd_file: Optional IDD path if loading from idf path
      sheet_name: Excel sheet name or index
      save_to: Optional path to save updated IDF

    Returns:
      Updated IDF instance
    """
    # Ensure IDF instance
    if isinstance(idf, str) or isinstance(idf, Path):
        if idd_file:
            IDF.setiddname(str(idd_file))
        else:
            try:
                IDF.setiddname(str(find_idd()))
            except FileNotFoundError:
                # last resort: try eppy default
                try:
                    IDF.setiddname(iddcurrent.iddname())
                except Exception:
                    pass
        idf_obj = IDF(str(idf))
    else:
        idf_obj = idf

    mapping = excel_to_update_mapping(excel_path, sheet_name=sheet_name)
    if not mapping:
        return idf_obj

    # Apply updates
    json_functions.updateidf(idf_obj, mapping)

    if save_to is not None:
        # Sauvegarde en UTF-8 par défaut pour supporter les caractères accentués
        try:
            idf_obj.saveas(str(save_to), encoding=save_encoding)
        except TypeError:
            # Anciennes versions d'eppy sans paramètre encoding
            idf_obj.saveas(str(save_to))

    return idf_obj

