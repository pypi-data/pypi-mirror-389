"""
IDF2TABLE - Convertir des fichiers EnergyPlus IDF en DataFrames pandas

Ce module permet de convertir des objets issus de fichiers EnergyPlus IDF
(Input Data File) en DataFrames pandas pour faciliter l'analyse et la manipulation.
"""

from idf2table.core import idf_to_table, find_idd

__version__ = "0.1.0"
__all__ = ["idf_to_table", "find_idd"]

