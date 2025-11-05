"""
Export EnergyPlus IDF geometry to Wavefront OBJ.

This module extracts polygonal surfaces from an IDF using eppy and writes
them to a .obj file. It currently supports BuildingSurface:Detailed and can
optionally include FenestrationSurface:Detailed and Shading:Building:Detailed.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from eppy.modeleditor import IDF


@dataclass
class Surface:
    name: str
    surface_type: str
    construction: str | None
    zone_name: str | None
    vertices: List[Tuple[float, float, float]]


@dataclass
class ObjExportOptions:
    include_fenestration: bool = False
    include_shading: bool = False
    flip_normals: bool = False
    write_mtl: bool = False
    mtl_path: str | None = None


def _read_vertices_from_obj(obj: Any) -> List[Tuple[float, float, float]]:
    num_vertices = getattr(obj, "Number_of_Vertices", None)
    if num_vertices is None:
        # Fallback using field name variations
        for field in ["Number_of_Vertices", "Number_of_Vertices_1", "Number_of_Vertices_2"]:
            num_vertices = getattr(obj, field, None)
            if num_vertices is not None:
                break
    if not num_vertices:
        return []

    vertices: List[Tuple[float, float, float]] = []
    for i in range(1, int(num_vertices) + 1):
        x = getattr(obj, f"Vertex_{i}_Xcoordinate", None)
        y = getattr(obj, f"Vertex_{i}_Ycoordinate", None)
        z = getattr(obj, f"Vertex_{i}_Zcoordinate", None)
        if x is None or y is None or z is None:
            continue
        vertices.append((float(x), float(y), float(z)))
    return vertices


def collect_surfaces(
    idf: IDF,
    include_fenestration: bool = False,
    include_shading: bool = False,
) -> List[Surface]:
    surfaces: List[Surface] = []

    # Building surfaces
    for obj in idf.idfobjects.get("BUILDINGSURFACE:DETAILED", []):
        vertices = _read_vertices_from_obj(obj)
        surfaces.append(
            Surface(
                name=str(getattr(obj, "Name", "")),
                surface_type=str(getattr(obj, "Surface_Type", "")),
                construction=getattr(obj, "Construction_Name", None),
                zone_name=getattr(obj, "Zone_Name", None),
                vertices=vertices,
            )
        )

    if include_fenestration:
        for obj in idf.idfobjects.get("FENESTRATIONSURFACE:DETAILED", []):
            vertices = _read_vertices_from_obj(obj)
            surfaces.append(
                Surface(
                    name=str(getattr(obj, "Name", "")),
                    surface_type=str(getattr(obj, "Surface_Type", "")),
                    construction=getattr(obj, "Construction_Name", None),
                    zone_name=getattr(obj, "Zone_Name", None),
                    vertices=vertices,
                )
            )

    if include_shading:
        for key in [
            "SHADING:BUILDING:DETAILED",
            "SHADING:ZONE:DETAILED",
            "SHADING:SITE:DETAILED",
        ]:
            for obj in idf.idfobjects.get(key, []):
                vertices = _read_vertices_from_obj(obj)
                surfaces.append(
                    Surface(
                        name=str(getattr(obj, "Name", "")),
                        surface_type="Shading",
                        construction=None,
                        zone_name=None,
                        vertices=vertices,
                    )
                )

    return surfaces


def triangulate(vertices: Sequence[Tuple[float, float, float]]) -> List[Tuple[int, int, int]]:
    """
    Fan triangulation (robust and simple). For N vertices, produces N-2 triangles:
    (0, i, i+1) for i in [1..N-2]. Indices are 0-based.
    """
    n = len(vertices)
    if n < 3:
        return []
    if n == 3:
        return [(0, 1, 2)]
    return [(0, i, i + 1) for i in range(1, n - 1)]


def write_obj(
    path: str | Path,
    surfaces: Sequence[Surface],
    *,
    flip_normals: bool = False,
    write_mtl: bool = False,
    mtl_path: str | None = None,
) -> None:
    path = Path(path)
    if write_mtl and mtl_path is None:
        mtl_path = path.with_suffix(".mtl").name

    lines: List[str] = []
    if write_mtl and mtl_path is not None:
        lines.append(f"mtllib {Path(mtl_path).name}\n")

    # Simple strategy: write vertices per face without deduplication
    # Keep track of current vertex index (1-based in OBJ)
    v_index = 1

    # Optional: build a material name by surface_type
    def mat_for(s: Surface) -> str:
        return (s.surface_type or "Default").replace(" ", "_")

    for s in surfaces:
        lines.append(f"o {s.name}\n")
        lines.append(f"g {s.name}\n")
        if write_mtl and mtl_path is not None:
            lines.append(f"usemtl {mat_for(s)}\n")

        # write vertices
        for (x, y, z) in s.vertices:
            lines.append(f"v {x:.6f} {y:.6f} {z:.6f}\n")

        # faces via triangulation
        tris = triangulate(s.vertices)
        for (a, b, c) in tris:
            i, j, k = a + v_index, b + v_index, c + v_index
            if flip_normals:
                i, k = k, i
            lines.append(f"f {i} {j} {k}\n")

        v_index += len(s.vertices)

    path.write_text("".join(lines), encoding="utf-8")

    # Simple MTL (optional): one material per surface type with flat color
    if write_mtl and mtl_path is not None:
        mtl_lines: List[str] = []
        used_types = {mat_for(s) for s in surfaces}
        type_to_kd = {
            "WALL": (0.8, 0.8, 0.8),
            "FLOOR": (0.8, 0.6, 0.4),
            "ROOF": (0.6, 0.1, 0.1),
            "CEILING": (0.7, 0.7, 0.9),
            "WINDOW": (0.3, 0.5, 0.9),
            "DOOR": (0.4, 0.2, 0.1),
            "Shading": (0.2, 0.2, 0.2),
        }
        for t in sorted(used_types):
            kd = type_to_kd.get(t.upper(), (0.7, 0.7, 0.7))
            mtl_lines.append(f"newmtl {t}\nKd {kd[0]:.3f} {kd[1]:.3f} {kd[2]:.3f}\n\n")

        Path(mtl_path).write_text("".join(mtl_lines), encoding="utf-8")


def export_idf_to_obj(
    idf_or_path: IDF | str | Path,
    obj_path: str | Path,
    *,
    idd_file: str | None = None,
    options: ObjExportOptions | None = None,
) -> None:
    if options is None:
        options = ObjExportOptions()

    if not isinstance(idf_or_path, IDF):
        # Lazy import to avoid circulars
        from .core import find_idd

        if idd_file:
            IDF.setiddname(str(idd_file))
        else:
            IDF.setiddname(str(find_idd()))
        idf = IDF(str(idf_or_path))
    else:
        idf = idf_or_path

    surfaces = collect_surfaces(
        idf,
        include_fenestration=options.include_fenestration,
        include_shading=options.include_shading,
    )

    write_obj(
        obj_path,
        surfaces,
        flip_normals=options.flip_normals,
        write_mtl=options.write_mtl,
        mtl_path=options.mtl_path,
    )


