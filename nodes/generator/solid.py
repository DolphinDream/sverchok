# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty

from math import sin, cos, pi, sqrt

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat

from mathutils import Vector

from pprint import pprint

import logging

logger = logging.getLogger("regular solids")
logger.propagate = False
terminal = logging.StreamHandler()
formatter = logging.Formatter("[%(levelname)s] : %(message)s")
terminal.setFormatter(formatter)
logger.addHandler(terminal)
logger.setLevel(logging.WARNING)

PHI = (1 + sqrt(5)) / 2
phi = 1 / PHI

sizeItems = [("EL", "Edge Length", ""),  # edge lenght
             # Non Truncated spheres
             ("NF", "NT Face Sphere Radius", ""),  # face sphere
             ("NE", "NT Edge Sphere Radius", ""),  # edge sphere
             ("NV", "NT Vert Sphere Radius", ""),  # vert sphere
             # Vertex Truncated spheres
             ("VF", "VT Face Sphere Radius", ""),  # face sphere
             ("VE", "VT Edge Sphere Radius", ""),  # edge sphere
             ("VV", "VT Vert Sphere Radius", ""),  # vert sphere
             # Edge Truncated spheres
             ("EF", "ET Face Sphere Radius", ""),  # face sphere
             ("EE", "ET Edge Sphere Radius", ""),  # edge sphere
             ("EV", "ET Vert Sphere Radius", "")]  # vert sphere

scaleRadiiItems = [("N", "N", ""),
                   ("RF", "F", ""),
                   ("RE", "E", ""),
                   ("RV", "V", "")]

outRadiiItems = [("RF", "F", "", 0),
                 ("RE", "E", "", 1),
                 ("RV", "V", "", 2)]

truncationItems = [("NT", "NT", "", 0),
                   ("VT", "VT", "", 1),
                   ("ET", "ET", "", 2)]

snubItems = [("N", "None", ""),
             ("L", "Left", ""),
             ("R", "Right", "")]

typeItems = [("TETRAHEDRON", "Tetrahedron", ""),
             ("HEXAHEDRON", "Hexahedron", ""),
             ("OCTAHEDRON", "Octahedron", ""),
             ("DODECAHEDRON", "Dodecahedron", ""),
             ("ICOSAHEDRON", "Icosahedron", "")]

outputItems = [("FACE CENTERS", "Face Centers", ""),
               ("FACE NORMALS", "Face Normals", ""),
               ("EDGE CENTERS", "Edge Centers", ""),
               ("DUAL VERTS", "Dual Verts", "")]

# name : [ preset index, type, dual, snub(N/L/R), v-trunc, e-trunc ]
solidPresets = {
    " ":                            (0, "", False, "N", 0.0, 0.0),
    # MAIN PLATONIC SOLIDS
    "TetraHedron":                  (10, "TETRAHEDRON",  False, "N", 0.0, 0.0),
    "HexaHedron":                   (11, "HEXAHEDRON",   False, "N", 0.0, 0.0),
    "OctaHedron":                   (12, "OCTAHEDRON",   False, "N", 0.0, 0.0),
    "DodecaHedron":                 (13, "DODECAHEDRON", False, "N", 0.0, 0.0),
    "IcosaHedron":                  (14, "ICOSAHEDRON",  False, "N", 0.0, 0.0),
    # ARCHIMEDEAN SOLIDS -------------------------------------------------------
    # BASIC TRUNCATED SOLIDS
    "Truncated TetraHedron":        (20, "TETRAHEDRON",  False, "N", 1 / 3, 0.0),
    "Truncated HexaHedron":         (21, "HEXAHEDRON",   False, "N", 1 / (sqrt(2) + 2), 0.0),
    "Truncated OctaHedron":         (22, "OCTAHEDRON",   False, "N", 1 / 3, 0.0),
    "Truncated DodecaHedron":       (23, "DODECAHEDRON", False, "N", 2 / (sqrt(5) + 5), 0.0),
    "Truncated IcosaHedron":        (24, "ICOSAHEDRON",  False, "N", 1 / 3, 0.0),
    # GREAT & SMALL RHOMBI SOLIDS
    "Great RhombiCubOctaHedron":    (30, "OCTAHEDRON",   False, "N", (sqrt(2) + 2) / (sqrt(2) + 1) / 3, 2 / (sqrt(2) + 2)),
    "Small RhombiCubOctaHedron":    (31, "OCTAHEDRON",   False, "N", 2 / (sqrt(2) + 3), 1.0),
    "Great RhombIcosiDodecaHedron": (32, "ICOSAHEDRON",  False, "N", (PHI + 2) / (PHI + 1) / 3, 2 / (PHI + 2)),
    "Small RhombIcosiDodecaHedron": (33, "ICOSAHEDRON",  False, "N",  2 / (PHI + 3), 1.0),
    # OTHER TRUNCATIONS
    "CubOctaHedron":                (40, "TETRAHEDRON",  False, "N", 1 / 2, 1.0),
    "IcosiDodecaHedron":            (41, "DODECAHEDRON", False, "N", 1 / 2, 0.0),
    # SNUBS
    "Snub HexaHedron":              (50, "HEXAHEDRON",   False, "L", 1.0875 / 2, 0.704),
    "Snub DodecaHedron":            (51, "DODECAHEDRON", False, "L", 1.1235 / 2, 0.68),
    # CATALAN SOLIDS (DUALS OF ARCHIMEDEAN SOLIDS) -----------------------------
    # DUALS of BASIC TRUNCATED SOLIDS
    "Triakis TetraHedron":          (60, "TETRAHEDRON",  True,  "N", 1 / 3, 0.0),
    "Triakis Octahedron":           (61, "HEXAHEDRON",   True,  "N", 1 / (sqrt(2) + 2), 0.0),
    "Tetrakis HexaHedron":          (62, "OCTAHEDRON",   True,  "N", 1 / 3, 0.0),
    "Triakis IcosaHedron":          (63, "DODECAHEDRON", True,  "N", 2 / (sqrt(5) + 5), 0.0),
    "Pentakis DodecaHedron":        (64, "ICOSAHEDRON",  True,  "N", 1 / 3, 0.0),
    # DUALS of GREAT & SMALL RHOMBI SOLIDS
    "Disdyakis DodecaHedron":       (70, "OCTAHEDRON",   True,  "N", (sqrt(2) + 2) / (sqrt(2) + 1) / 3, 2 / (sqrt(2) + 2)),
    "Deltoidal IcosiTetraHedron":   (71, "OCTAHEDRON",   True,  "N", 2 / (sqrt(2) + 3), 1.0),
    "Disdyakis TriaContaHedron":    (72, "ICOSAHEDRON",  True,  "N", (PHI + 2) / (PHI + 1) / 3, 2 / (PHI + 2)),
    "Deltoidal HexeContaHedron":    (73, "ICOSAHEDRON",  True,  "N", 2 / (PHI + 3), 1.0),
    # DUALS of OTHER TRUNCATIONS
    "Rhombic DodecaHedron":         (80, "TETRAHEDRON",  True,  "N", 1 / 2, 1.0),
    "Rhombic TriaContaHedron":      (81, "DODECAHEDRON", True,  "N", 1 / 2, 0.0),
    # DUALS of SNUBS
    "Pentagonal IcosiTetraHedron":  (90, "HEXAHEDRON",   True,  "L", 1.0875 / 2, 0.704),
    "Pentagonal HexeContaHedron":   (91, "DODECAHEDRON", True,  "L", 1.1235 / 2, 0.68)
}

# inradius / midradius / circumradius : r / ρ / R of platonic solids with unit length edge
rρR_radii = {
    "TETRAHEDRON":  (sqrt(6) / 12, sqrt(2) / 4, sqrt(6) / 4),
    "TETRVHEDRON":  (sqrt(6) / 12, sqrt(2) / 4, sqrt(6) / 4),
    "HEXAHEDRON":   (1 / 2, sqrt(2) / 2, sqrt(3) / 2),
    "OCTAHEDRON":   (sqrt(6) / 6, 1 / 2, sqrt(2) / 2),
    "DODECAHEDRON": (sqrt(250 + 110 * sqrt(5)) / 20, (3 + sqrt(5)) / 4, (sqrt(15) + sqrt(3)) / 4),
    "ICOSAHEDRON":  ((3 * sqrt(3) + sqrt(15)) / 12, (1 + sqrt(5)) / 4, sqrt(10 + 2 * sqrt(5)) / 4)
}

# inradius / midradius / circumradius : r / ρ / R of platonic solids with unit length edge
radii = {
    'TETRAHEDRON':  (0.2041241452319315, 0.3535533905932738, 0.6123724356957945),
    'TETRVHEDRON':  (0.2041241452319315, 0.3535533905932738, 0.6123724356957945),
    'HEXAHEDRON':   (0.5000000000000000, 0.7071067811865476, 0.8660254037844386),
    'OCTAHEDRON':   (0.4082482904638630, 0.5000000000000000, 0.7071067811865476),
    'DODECAHEDRON': (1.1135163644116068, 1.3090169943749475, 1.4012585384440737),
    'ICOSAHEDRON':  (0.7557613140761706, 0.8090169943749475, 0.9510565162951535)
}

dualPairs = {
    "TETRAHEDRON":  "TETRVHEDRON",
    "TETRVHEDRON":  "TETRAHEDRON",
    "HEXAHEDRON":   "OCTAHEDRON",
    "OCTAHEDRON":   "HEXAHEDRON",
    "DODECAHEDRON": "ICOSAHEDRON",
    "ICOSAHEDRON":  "DODECAHEDRON"
}

dualPairNames = {
    # MAIN PLATONIC SOLIDS
    "TetraHedron":                  "TetraHedron",
    "HexaHedron":                   "OctaHedron",
    "OctaHedron":                   "HexaHedron",
    "DodecaHedron":                 "IcosaHedron",
    "IcosaHedron":                  "DodecaHedron",
    # BASIC TRUNCATED SOLIDS
    "Truncated TetraHedron":        "Triakis TetraHedron",
    "Truncated HexaHedron":         "Triakis Octahedron",
    "Truncated OctaHedron":         "Tetrakis HexaHedron",
    "Truncated DodecaHedron":       "Triakis IcosaHedron",
    "Truncated IcosaHedron":        "Pentakis DodecaHedron",
    # GREAT & SMALL RHOMBI SOLIDS
    "Great RhombiCubOctaHedron":    "Disdyakis DodecaHedron",     # Truncated CubOctaHedron
    "Small RhombiCubOctaHedron":    "Deltoidal IcosiTetraHedron",
    "Great RhombIcosiDodecaHedron": "Disdyakis TriaContaHedron",  # Truncated IcosiDodecaHedron
    "Small RhombIcosiDodecaHedron": "Deltoidal HexeContaHedron",
    # OTHER TRUNCATIONS
    "CubOctaHedron":                "Rhombic DodecaHedron",
    "IcosiDodecaHedron":            "Rhombic TriaContaHedron",
    # SNUBS
    "Snub HexaHedron":              "Pentagonal IcosiTetraHedron",
    "Snub DodecaHedron":            "Pentagonal HexeContaHedron"
}

mirrorSnub = {"N": "N", "L": "R", "R": "L"}

solids_data = {}
# ["TETRAHEDRON"]["NT"]["VERTS"]      -> [(x,y,z), ... ]
# ["TETRAHEDRON"]["NT"]["EDGES"]      -> [(i,j), ... ]
# ["TETRAHEDRON"]["NT"]["FACES"]      -> [(i,j1,..jn), ...]
# ["TETRAHEDRON"]["NT"]["VE MAP"][i]  -> [(i,j1), (i,j2), ...]
# ["TETRAHEDRON"]["NT"]["VF MAP"][i]  -> [(i,j1,..jn), (i,k1,..kn), ...]
# ["TETRAHEDRON"]["NT"]["EFMAP"][i,j] -> [(i,j,..a1), (i,j,..a2), ...]


def shift(l, n):
    return l[n:] + l[:n]


def interpolate(v1, v2, f):
    x = v1[0] * (1 - f) + v2[0] * f
    y = v1[1] * (1 - f) + v2[1] * f
    z = v1[2] * (1 - f) + v2[2] * f
    return [x, y, z]


def get_radius(plato, truncation, rID, vt, et):
    # Get the face, edge and vertex sphere radius for given truncated plato solid

    # print("plato=", plato)
    # print("truncation=", truncation)
    vt = vt * 2
    Rf, Re, Rv = [1, 1, 1]
    if plato in ["TETRAHEDRON", "TETRVHEDRON"]:
        if truncation == "NT":
            Rf = sqrt(6) / 12
            Re = sqrt(2) / 4
            Rv = sqrt(6) / 4
        elif truncation == "VT":
            Rf = 1 / 2 * (sqrt(3 / 2) - sqrt(2 / 3) * vt)
            # Rf = 1 / 2 * sqrt(3 / 2 - 2 * vt + vt * vt * 2 / 3)
            Re = 1 / 2 * sqrt(3 / 2 - 2 * vt + vt * vt * 3 / 4)
            Rv = 1 / 2 * sqrt(3 / 2 - 2 * vt + vt * vt * 4 / 4)
        elif truncation == "ET":
            Rf = 1
            Re = 1 / 2 * sqrt(3 / 2 - 2 * vt + vt * vt * (1 - et / 2 + et * et * 3 / 16))
            Rv = 1 / 2 * sqrt(3 / 2 - 2 * vt + vt * vt * (1 - et / 2 + et * et * 4 / 16))

    elif plato == "HEXAHEDRON":
        if truncation == "NT":
            Rf = 1 / 2
            Re = sqrt(2) / 2
            Rv = sqrt(3) / 2
        elif truncation == "VT":
            Rf = 1 / 2 * sqrt(3) * (1 - 1 / 3 * vt)
            # Rf = 1 / 2 * sqrt(3 - 2 * vt + vt * vt * 1 / 3)
            Re = 1 / 2 * sqrt(3 - 2 * vt + vt * vt * 1 / 2)
            Rv = 1 / 2 * sqrt(3 - 2 * vt + vt * vt * 2 / 2)
        elif truncation == "ET":
            Rf = 1
            Re = 1 / 2 * sqrt(3 - 2 * vt + vt * vt * (1 - et + et * et * 3 / 8))
            Rv = 1 / 2 * sqrt(3 - 2 * vt + vt * vt * (1 - et + et * et * 4 / 8))

    elif plato == "OCTAHEDRON":
        if truncation == "NT":
            Rf = sqrt(6) / 6
            Re = 1 / 2
            Rv = sqrt(2) / 2
        elif truncation == "VT":
            Rf = 1 / 2 * sqrt(2) * (1 - vt / 2)
            # Rf = 1 / 2 * sqrt(2 - 2 * vt + vt * vt * 2 / 4)
            Re = 1 / 2 * sqrt(2 - 2 * vt + vt * vt * 3 / 4)
            Rv = 1 / 2 * sqrt(2 - 2 * vt + vt * vt * 4 / 4)
        elif truncation == "ET":
            Rf = 1
            Re = 1 / 2 * sqrt(2 - 2 * vt + vt * vt * (1 - et / 2 + et * et * 1 / 8))
            Rv = 1 / 2 * sqrt(2 - 2 * vt + vt * vt * (1 - et / 2 + et * et * 2 / 8))

    elif plato == "DODECAHEDRON":
        if truncation == "NT":
            Rf = 1 / 2 * sqrt((11 * PHI + 7) / 5)
            Re = 1 / 2 * (PHI + 1)
            Rv = 1 / 2 * sqrt(3) * PHI
        elif truncation == "VT":
            Rf = 1 / 2 * (sqrt(3) * PHI - sqrt((2 - PHI) / 3) * vt)
            Re = 1 / 2 * sqrt(3 + 3 * PHI - 2 * vt + vt * vt * (3 - PHI) / 4)
            Rv = 1 / 2 * sqrt(3 + 3 * PHI - 2 * vt + vt * vt)
        elif truncation == "ET":
            Rf = 1
            Re = 1
            Rv = 1

    elif plato == "ICOSAHEDRON":
        if truncation == "NT":
            Rf = 1 / 2 * sqrt(PHI + 2 / 3)
            Re = 1 / 2 * PHI
            Rv = 1 / 2 * sqrt(PHI + 2)
        elif truncation == "VT":
            Rf = 1 / 2 * (sqrt(2 + PHI) - sqrt((3 - PHI) / 5) * vt)
            Re = 1 / 2 * sqrt(2 + PHI - 2 * vt + vt * vt * 3 / 4)
            Rv = 1 / 2 * sqrt(2 + PHI - 2 * vt + vt * vt * 4 / 4)
        elif truncation == "ET":
            Rf = 1
            Re = 1
            Rv = 1

    if rID == "RF":
        return Rf
    elif rID == "RE":
        return Re
    elif rID == "RV":
        return Rv
    else:
        return 1


def compute_edge_centers(plato, truncation, pair):
    # Compute the EDGE centers for the given platonic (Non/Vertex/Edge) truncated solid

    logger.info("compute_edge_centers for: %s [%s]" % (plato, truncation))

    if plato not in solids_data or truncation not in solids_data[plato]:
        logger.warning("cannot compute EDGE CENTERS for given plato/truncation")
        return

    verts = solids_data[plato][truncation][pair]["VERTS"]
    edges = solids_data[plato][truncation][pair]["EDGES"]

    solids_data[plato][truncation][pair]["EDGE CENTERS"] = {}
    for e in range(len(edges)):
        edge = edges[e]
        c = Vector([0, 0, 0])
        for i in edge:
            c = c + Vector(verts[i])
        solids_data[plato][truncation][pair]["EDGE CENTERS"][e] = list(c / len(edge))

    # pprint(solids_data[plato][truncation][pair]["EDGE CENTERS"])


def compute_face_centers(plato, truncation, pair):
    # Compute the FACE centers for the given platonic (Non/Vertex/Edge) truncated solid

    logger.info("compute_face_centers for: %s [%s]" % (plato, truncation))

    if plato not in solids_data or truncation not in solids_data[plato]:
        logger.warning("cannot compute FACE CENTERS for given plato/truncation")
        return

    verts = solids_data[plato][truncation][pair]["VERTS"]
    faces = solids_data[plato][truncation][pair]["FACES"]

    solids_data[plato][truncation][pair]["FACE CENTERS"] = {}
    for f in range(len(faces)):
        face = faces[f]
        c = Vector([0, 0, 0])
        for i in face:
            c = c + Vector(verts[i])
        solids_data[plato][truncation][pair]["FACE CENTERS"][f] = list(c / len(face))

    # pprint(solids_data[plato][truncation][pair]["FACE CENTERS"])


def compute_face_normals(plato, truncation, pair):
    # Compute face normals for the given platonic (Non/Vertex/Edge) truncated solid

    logger.info("compute_face_normals for: %s [%s]" % (plato, truncation))

    if plato not in solids_data or truncation not in solids_data[plato]:
        logger.warning("cannot compute FACE NORMALS for given plato/truncation")
        return

    verts = solids_data[plato][truncation][pair]["VERTS"]
    faces = solids_data[plato][truncation][pair]["FACES"]

    solids_data[plato][truncation][pair]["FACE NORMALS"] = {}
    for f in range(len(faces)):
        face = faces[f]
        v0 = Vector(verts[face[0]])
        v1 = Vector(verts[face[1]])
        v2 = Vector(verts[face[2]])
        e1 = v1 - v0
        e2 = v2 - v1
        n = e1.cross(e2)
        n.normalize()

        solids_data[plato][truncation][pair]["FACE NORMALS"][f] = list(n)

    # pprint(solids_data[plato][truncation][pair]["FACE NORMALS"])


def compute_dual_verts(plato, truncation):

    logger.info("compute_dual_verts for: %s [%s]" % (plato, truncation))

    if plato not in solids_data or truncation not in solids_data[plato]:
        logger.warning("cannot compute DUAL VERTS for given plato/truncation")
        return

    verts = solids_data[plato][truncation]["MAIN"]["VERTS"]
    edges = solids_data[plato][truncation]["MAIN"]["EDGES"]
    faces = solids_data[plato][truncation]["MAIN"]["FACES"]

    solids_data[plato][truncation]["VF DUAL"] = {}

    newVerts, newEdges, newFaces = [[], [], []]
    for f in range(len(faces)):
        face = faces[f]
        e = sorted([face[1], face[2]])
        i = edges.index(e)
        # print(face)
        # print(edges)
        # print(e)
        # print(i)
        # print("Face normals=", solids_data[plato][truncation][pair]["FACE NORMALS"])
        v = solids_data[plato][truncation]["MAIN"]["EDGE CENTERS"][i]
        n = solids_data[plato][truncation]["MAIN"]["FACE NORMALS"][f]
        # print("v=", v)
        # print("n=", n)
        # get face normal
        # get an edge center
        # compute new vertex D
        vk = Vector(v)
        nn = Vector(n)
        if vk.dot(nn) != 0:
            D = (vk.length**2 / vk.dot(nn)) * nn
        else:
            D = nn
        # print("vk = ", vk)
        # print("nn = ", nn)
        # print("D  = ", D)
        # D = sqrt(vk.dot(vk)) / vk.dot(nn) * nn
        newVerts.append(list(D))
        solids_data[plato][truncation]["VF DUAL"][f] = len(newVerts) - 1

    # construct the faces
    for i in range(len(verts)):
        faceIDs = solids_data[plato][truncation]["VFI MAP"][i]
        face = [solids_data[plato][truncation]["VF DUAL"][f] for f in faceIDs]
        newFaces.append(face)

    # construct the edges
    for face in newFaces:
        newEdges.extend([tuple(sorted([face[n - 1], face[n]])) for n in range(len(face))])
    newEdges = [list(e) for e in set(newEdges)]

    solids_data[plato][truncation]["DUAL"] = {}
    solids_data[plato][truncation]["DUAL"]["VERTS"] = newVerts
    solids_data[plato][truncation]["DUAL"]["EDGES"] = newEdges
    solids_data[plato][truncation]["DUAL"]["FACES"] = newFaces


def compute_vert_edge_face_maps(plato, truncation):
    # construct and cache VERT -> VERT/EDGE/FACE maps (ordered verts/edges/faces)

    logger.info("compute_vert_edge_face_maps for: %s [%s]" % (plato, truncation))

    if plato not in solids_data or truncation not in solids_data[plato]:
        logger.warning("cannot compute maps for given plato/truncation")
        return

    verts = solids_data[plato][truncation]["MAIN"]["VERTS"]
    edges = solids_data[plato][truncation]["MAIN"]["EDGES"]
    faces = solids_data[plato][truncation]["MAIN"]["FACES"]

    solids_data[plato][truncation]["VV MAP"] = {}
    solids_data[plato][truncation]["VE MAP"] = {}  # not used
    solids_data[plato][truncation]["VF MAP"] = {}  # not used
    solids_data[plato][truncation]["VFI MAP"] = {}

    for i in range(len(verts)):
        vertFaces = [face for face in faces if i in face]  # get unordered faces touching the vertex

        # order the connected faces around the vertex in the CCW direction
        face = vertFaces[0]
        k = face[face.index(i) - 1]  # vertex before i in the face (for first iteration)

        orderedVerts = []
        orderedEdges = []
        orderedFaces = []
        orderedFaceIDs = []
        while len(vertFaces):
            for face in vertFaces:
                j = face[(face.index(i) + 1) % len(face)]  # vertex after i in the face

                # vertex after i in this face = vertex after i in previous face ? => faces connect at jk edge
                if j == k:
                    k = face[face.index(i) - 1]  # vertex before i in the face (for next iteration)
                    faceID = faces.index(face)
                    orderedFaceIDs.append(faceID)
                    # print("faceID = ", faceID)
                    vertFaces.remove(face)
                    orderedFaces.append(shift(face, face.index(i)))
                    orderedEdges.append([i, j])
                    orderedVerts.append(j)
                    break

        # store the ordered vertices, edges and faces touching the current vertex
        solids_data[plato][truncation]["VV MAP"][i] = orderedVerts
        solids_data[plato][truncation]["VE MAP"][i] = orderedEdges  # not used
        solids_data[plato][truncation]["VF MAP"][i] = orderedFaces  # not used
        solids_data[plato][truncation]["VFI MAP"][i] = orderedFaceIDs

    # pprint(solids_data)


def make_platonic_solid(plato):
    ''' Make a UNIT LENGTH EDGE platonic solid '''

    logger.info("make_platonic_solid for: %s " % plato)

    verts, faces = [[], []]

    if plato == "TETRAHEDRON":  # UP tetrahedron
        R, x, r, u = [sqrt(6) / 4.0, sqrt(6) / 12.0, sqrt(3) / 3, 1 / 2]

        verts = [(0, 0, +R), (-r, 0, -x), (+r / 2, -u, -x), (+r / 2, +u, -x)]
        faces = [[1, 3, 2], [0, 1, 2], [0, 2, 3], [0, 3, 1]]

    if plato == "TETRVHEDRON":  # DOWN tetrahedron (used to simplify the code)
        R, x, r, u = [sqrt(6) / 4.0, sqrt(6) / 12.0, sqrt(3) / 3, 1 / 2]

        verts = [(0, 0, -R), (+r, 0, +x), (-r / 2, +u, +x), (-r / 2, -u, +x)]
        faces = [[2, 3, 1], [2, 1, 0], [3, 2, 0], [1, 3, 0]]

    elif plato == "HEXAHEDRON":
        s = 1 / 2

        verts = [(-s, -s, -s), (-s, -s, +s), (-s, +s, -s), (-s, +s, +s),
                 (+s, -s, -s), (+s, -s, +s), (+s, +s, -s), (+s, +s, +s)]
        faces = [[0, 1, 3, 2], [4, 6, 7, 5],  # X faces
                 [0, 4, 5, 1], [6, 2, 3, 7],  # Y faces
                 [0, 2, 6, 4], [1, 5, 7, 3]]  # Z faces

    elif plato == "OCTAHEDRON":
        s = sqrt(2) / 2

        verts = [(-s, 0, 0), (+s, 0, 0), (0, -s, 0), (0, +s, 0), (0, 0, -s), (0, 0, +s)]
        faces = [[4, 2, 0], [4, 1, 2], [4, 3, 1], [4, 0, 3],  # -Z faces
                 [5, 0, 2], [5, 2, 1], [5, 1, 3], [5, 3, 0]]  # +Z faces

    elif plato == "DODECAHEDRON":
        s, t, u = [PHI / 2,  (PHI + 1) / 2, 1 / 2]

        verts = [[-s, -s, -s], [-s, -s, +s], [-s, +s, -s], [-s, +s, +s],
                 [+s, -s, -s], [+s, -s, +s], [+s, +s, -s], [+s, +s, +s],
                 [-t, -u, 0], [-t, +u, 0], [+t, -u, 0], [+t, +u, 0],
                 [-u, 0, -t], [-u, 0, +t], [+u, 0, -t], [+u, 0, +t],
                 [0, -t, -u], [0, -t, +u], [0, +t, -u], [0, +t, +u]]
        faces = [[8, 9, 2, 12, 0], [9, 8, 1, 13, 3],      # -X faces
                 [11, 10, 4, 14, 6], [10, 11, 7, 15, 5],  # +X faces
                 [19, 18, 2, 9, 3], [18, 19, 7, 11, 6],   # -Y faces
                 [16, 17, 1, 8, 0], [17, 16, 4, 10, 5],   # +Y faces
                 [12, 14, 4, 16, 0], [14, 12, 2, 18, 6],  # -Z faces
                 [15, 13, 1, 17, 5], [13, 15, 7, 19, 3]]  # +Z faces

    elif plato == "ICOSAHEDRON":
        s, t = [PHI / 2, 1 / 2]

        verts = [(-s, 0, -t), (-s, 0, +t), (+s, 0, -t), (+s, 0, +t),
                 (-t, -s, 0), (-t, +s, 0), (+t, -s, 0), (+t, +s, 0),
                 (0, -t, -s), (0, -t, +s), (0, +t, -s), (0, +t, +s)]
        faces = [[1, 0, 4], [0, 1, 5], [3, 2, 7], [2, 3, 6],
                 [4, 6, 9], [6, 4, 8], [7, 5, 11], [5, 7, 10],
                 [8, 10, 2], [10, 8, 0], [9, 11, 1], [11, 9, 3],
                 [1, 4, 9], [9, 6, 3], [3, 7, 11], [11, 5, 1],
                 [0, 5, 10], [10, 7, 2], [2, 6, 8], [8, 4, 0]]

    # construct the unique set of edges from faces
    edges = []
    for face in faces:
        edges.extend([tuple(sorted([face[n - 1], face[n]])) for n in range(len(face))])
    edges = [list(e) for e in set(edges)]

    logger.debug("verts= %s" % verts)
    logger.debug("edges= %s" % edges)
    logger.debug("faces= %s" % faces)

    # cache the mesh data
    solids_data[plato] = {}
    solids_data[plato]["NT"] = {}  # NON-TRUNCATED mesh data
    solids_data[plato]["NT"]["MAIN"] = {}
    solids_data[plato]["NT"]["MAIN"]["VERTS"] = verts
    solids_data[plato]["NT"]["MAIN"]["EDGES"] = edges
    solids_data[plato]["NT"]["MAIN"]["FACES"] = faces

    # compute some useful data
    compute_edge_centers(plato, "NT", "MAIN")
    compute_face_centers(plato, "NT", "MAIN")
    compute_face_normals(plato, "NT", "MAIN")

    compute_vert_edge_face_maps(plato, "NT")

    compute_dual_verts(plato, "NT")

    compute_edge_centers(plato, "NT", "DUAL")
    compute_face_centers(plato, "NT", "DUAL")
    compute_face_normals(plato, "NT", "DUAL")


def make_vertex_trucated_solid(plato, vTrunc):
    ''' Make Vertex-Truncated solid from the Non-Truncated solid '''

    logger.info("make_vertex_trucated_solid for: %s, %.2f" % (plato, vTrunc))

    nVerts = solids_data[plato]["NT"]["MAIN"]["VERTS"]
    nEdges = solids_data[plato]["NT"]["MAIN"]["EDGES"]
    nFaces = solids_data[plato]["NT"]["MAIN"]["FACES"]

    solids_data[plato]["VT"] = {}  # VERTEX-TRUNCATED mesh data
    solids_data[plato]["VT"]["V FACE"] = {}  # book-keeping (truncated vertex face)
    solids_data[plato]["VT"]["EV MAP"] = {}  # book-keeping map (edge to truncated edge)
    solids_data[plato]["VT"]["E EDGE"] = {}  # book-keeping map
    solids_data[plato]["VT"]["F FACE"] = {}  # book-keeping map

    # generate the truncated VERTS (and edges/faces at the each vertex)
    newVerts, newEdges, newFaces = [[], [], []]
    f = vTrunc
    for i in range(len(nVerts)):
        nv = solids_data[plato]["NT"]["VV MAP"][i]  # vertices connected to i
        # print("nv=", nv)
        newFace = []
        for j in nv:  # each vertex j connected to i
            if f == 0.5:  # cut in the middle of edge ? => only one vertex per edge
                logger.debug("ONE vertex per edge")
                if (j, i) in solids_data[plato]["VT"]["EV MAP"]:
                    vijID = solids_data[plato]["VT"]["EV MAP"][(j, i)]
                else:  # create new vertex on the edge
                    vijID = len(newVerts)  # the vertex ID of the new vertex being created
                    vij = interpolate(nVerts[i], nVerts[j], f)  # compute new vertex location
                    newVerts.append(vij)  # add to the list of new vertices
            else:  # not cut in the middle ? => create two vertex per edge
                vijID = len(newVerts)  # the vertex ID of the new vertex being created
                vij = interpolate(nVerts[i], nVerts[j], f)  # compute new vertex location
                newVerts.append(vij)  # add to the list of new vertices
            newFace.append(vijID)  # add vertex to the new face
            solids_data[plato]["VT"]["EV MAP"][(i, j)] = vijID  # book-keeping (edge -> truncated vertex)
        # print("face= ", face)
        solids_data[plato]["VT"]["V FACE"][i] = newFace  # book-keeping (vertex -> vertex face)
        newFaces.append(newFace)
        ne = [[newFace[n - 1], newFace[n]] for n in range(len(newFace))]
        newEdges.extend(ne)

    # append the truncated EDGES generated from the original edges (these connect vertex faces)
    if f != 0.5:  # if f = 0.5 there is no truncated edge
        for n, e in enumerate(nEdges):
            i, j = e
            vijID = solids_data[plato]["VT"]["EV MAP"][(i, j)]
            vjiID = solids_data[plato]["VT"]["EV MAP"][(j, i)]
            newEdge = [vijID, vjiID]
            # book-keeping (edge -> truncated edge)
            solids_data[plato]["VT"]["E EDGE"][n] = newEdge
            newEdges.append(newEdge)

    # append the truncated FACES generated from the original faces
    for n, face in enumerate(nFaces):
        newFace = []
        faceEdges = [[face[n - 1], face[n]] for n in range(len(face))]
        for edge in faceEdges:
            i, j = edge
            if f != 0.5:  # two vertex per edge
                vijID = solids_data[plato]["VT"]["EV MAP"][(i, j)]
                newFace.append(vijID)
            vjiID = solids_data[plato]["VT"]["EV MAP"][(j, i)]
            newFace.append(vjiID)
            # book-keeping (face -> truncated face)
            solids_data[plato]["VT"]["F FACE"][n] = newFace
        newFaces.append(newFace)

    # sort the indices of the new edges (needed for lookup)
    newEdges = [sorted(e) for e in newEdges]

    # store the vertex truncation mesh (later used to compute edge truncation)
    solids_data[plato]["VT"]["MAIN"] = {}
    solids_data[plato]["VT"]["MAIN"]["VERTS"] = newVerts
    solids_data[plato]["VT"]["MAIN"]["EDGES"] = newEdges
    solids_data[plato]["VT"]["MAIN"]["FACES"] = newFaces

    # pprint(solids_data)

    compute_face_normals(plato, "VT", "MAIN")
    compute_face_centers(plato, "VT", "MAIN")
    compute_edge_centers(plato, "VT", "MAIN")

    compute_vert_edge_face_maps(plato, "VT")

    compute_dual_verts(plato, "VT")

    compute_face_normals(plato, "VT", "DUAL")
    compute_face_centers(plato, "VT", "DUAL")
    compute_edge_centers(plato, "VT", "DUAL")


def make_edge_trucated_solid(plato, eTrunc, snub):
    ''' Make edge truncated solid from the vertex truncated solid '''

    logger.info("make_edge_trucated_solid for: %s, %.2f" % (plato, eTrunc))

    lSnub = (snub == "L") and (0.0 < eTrunc < 1.0)
    rSnub = (snub == "R") and (0.0 < eTrunc < 1.0)

    nVerts = solids_data[plato]["NT"]["MAIN"]["VERTS"]
    nEdges = solids_data[plato]["NT"]["MAIN"]["EDGES"]
    nFaces = solids_data[plato]["NT"]["MAIN"]["FACES"]

    vVerts = solids_data[plato]["VT"]["MAIN"]["VERTS"]
    vEdges = solids_data[plato]["VT"]["MAIN"]["EDGES"]  # not used
    vFaces = solids_data[plato]["VT"]["MAIN"]["FACES"]

    solids_data[plato]["ET"] = {}  # EDGE-TRUNCATED mesh data
    solids_data[plato]["ET"]["EE MAP"] = {}  # book-keeping
    solids_data[plato]["ET"]["VV MAP"] = {}  # book-keeping

    f = eTrunc / 2
    newVerts, newEdges, newFaces = [[], [], []]
    # generate VERTS
    for v in range(len(nVerts)):
        face = solids_data[plato]["VT"]["V FACE"][v]
        # print("face = ", face)
        ne = [[face[n - 1], face[n]] for n in range(len(face))]
        # print("ne = ", ne)
        for e in ne:
            i, j = e  # the edge indices in the VT vertex list
            if f != 0.5:
                if lSnub:
                    vijID = len(newVerts)  # the vertex ID of the new vertex being created
                    vij = interpolate(vVerts[i], vVerts[j], f)  # compute new vertex location
                    newVerts.append(vij)  # add to the list of new vertices
                    vjiID = vijID

                elif rSnub:
                    vjiID = len(newVerts)  # the vertex ID of the new vertex being created
                    vji = interpolate(vVerts[j], vVerts[i], f)  # compute new vertex location
                    newVerts.append(vji)  # add to the list of new vertices
                    vijID = vjiID

                else:
                    vijID = len(newVerts)  # the vertex ID of the new vertex being created
                    vij = interpolate(vVerts[i], vVerts[j], f)  # compute new vertex location
                    newVerts.append(vij)  # add to the list of new vertices

                    vjiID = len(newVerts)  # the vertex ID of the new vertex being created
                    vji = interpolate(vVerts[j], vVerts[i], f)  # compute new vertex location
                    newVerts.append(vji)  # add to the list of new vertices

                    newEdges.append([vijID, vjiID])

            else:  # f = 0.5 -> only one vert per edge
                vijID = len(newVerts)  # the vertex ID of the new vertex being created
                vij = interpolate(vVerts[i], vVerts[j], f)  # compute new vertex location
                newVerts.append(vij)  # add to the list of new vertices
                vjiID = vijID

            solids_data[plato]["ET"]["EE MAP"][(i, j)] = [vijID, vjiID]
            solids_data[plato]["ET"]["EE MAP"][(j, i)] = [vjiID, vijID]

            if i not in solids_data[plato]["ET"]["VV MAP"]:
                solids_data[plato]["ET"]["VV MAP"][i] = []
            solids_data[plato]["ET"]["VV MAP"][i].append(vijID)

            if j not in solids_data[plato]["ET"]["VV MAP"]:
                solids_data[plato]["ET"]["VV MAP"][j] = []
            solids_data[plato]["ET"]["VV MAP"][j].append(vjiID)

    # print("vFaces=", vFaces)
    # generate FACES
    for face in vFaces:
        ne = [[face[n - 1], face[n]] for n in range(len(face))]
        newFace = []
        for e in ne:
            i, j = e
            if tuple(e) in solids_data[plato]["ET"]["EE MAP"]:
                vijID, vjiID = solids_data[plato]["ET"]["EE MAP"][tuple(e)]
                newFace.append(vijID)
                if f != 0.5 and not lSnub and not rSnub:
                    newFace.append(vjiID)
        newFaces.append(newFace)

    # generate (edge) FACES & EDGES
    for e in nEdges:
        i, j = e

        vijID = solids_data[plato]["VT"]["EV MAP"][(i, j)]
        vjiID = solids_data[plato]["VT"]["EV MAP"][(j, i)]

        fi = solids_data[plato]["VT"]["V FACE"][i]
        ia = fi[(fi.index(vijID) + 1) % len(fi)]
        ib = fi[(fi.index(vijID) - 1) % len(fi)]

        fj = solids_data[plato]["VT"]["V FACE"][j]
        ja = fj[(fj.index(vjiID) + 1) % len(fj)]
        jb = fj[(fj.index(vjiID) - 1) % len(fj)]

        v1, _ = solids_data[plato]["ET"]["EE MAP"][(vijID, ia)]
        _, v2 = solids_data[plato]["ET"]["EE MAP"][(ib, vijID)]

        v3, _ = solids_data[plato]["ET"]["EE MAP"][(vjiID, ja)]
        _, v4 = solids_data[plato]["ET"]["EE MAP"][(jb, vjiID)]

        if lSnub:
            newFace = [v1, v2, v3]
            newFaces.append(newFace)
            newFace = [v1, v3, v4]
            newFaces.append(newFace)
            newEdges.extend([[v1, v2], [v2, v3], [v3, v1]])
            newEdges.extend([[v1, v3], [v3, v4], [v4, v1]])
        elif rSnub:
            newFace = [v1, v2, v4]
            newFaces.append(newFace)
            newFace = [v4, v2, v3]
            newFaces.append(newFace)
            newEdges.extend([[v1, v2], [v2, v4], [v4, v1]])
            newEdges.extend([[v4, v2], [v2, v3], [v3, v4]])
        else:  # no snub
            newFace = [v1, v2, v3, v4]
            newFaces.append(newFace)
            ne = [[newFace[n - 1], newFace[n]] for n in range(len(newFace))]
            newEdges.extend(ne)

    # sort the indices of the new edges (needed for lookup)
    newEdges = [sorted(e) for e in newEdges]

    solids_data[plato]["ET"]["MAIN"] = {}
    solids_data[plato]["ET"]["MAIN"]["VERTS"] = newVerts
    solids_data[plato]["ET"]["MAIN"]["EDGES"] = newEdges
    solids_data[plato]["ET"]["MAIN"]["FACES"] = newFaces

    compute_face_normals(plato, "ET", "MAIN")
    compute_face_centers(plato, "ET", "MAIN")
    compute_edge_centers(plato, "ET", "MAIN")

    compute_vert_edge_face_maps(plato, "ET")

    compute_dual_verts(plato, "ET")

    compute_face_normals(plato, "ET", "DUAL")
    compute_face_centers(plato, "ET", "DUAL")
    compute_edge_centers(plato, "ET", "DUAL")


def make_solid(sType, dual, snub, scaleRadius, size, vTrunc, eTrunc):
    ''' Make a solid '''
    # the truncation of the MAIN platonic solid for vTrunc > 0.5 is equivalent to
    # the truncation of the DUAL of the platonic solid for 1-vTrunc

    logger.info("make_solid for: %s, %s, %s, %.2f, %.2f, %.2f" % (sType, dual, snub, size, vTrunc, eTrunc))

    if vTrunc <= 0.5:  # truncate the MAIN solid
        plato = sType
        make_platonic_solid(plato)
        make_vertex_trucated_solid(plato, vTrunc)
        make_edge_trucated_solid(plato, eTrunc, snub)
    else:  # truncate the DUAL pair
        plato = dualPairs[sType]
        make_platonic_solid(plato)
        make_vertex_trucated_solid(plato, 1 - vTrunc)
        make_edge_trucated_solid(plato, eTrunc, mirrorSnub[snub])

    truncation = "NT" if vTrunc in [0, 1] else "VT" if eTrunc == 0 else "ET"

    v1 = solids_data[plato][truncation]["MAIN"]["VERTS"]
    e1 = solids_data[plato][truncation]["MAIN"]["EDGES"]
    f1 = solids_data[plato][truncation]["MAIN"]["FACES"]

    v2 = solids_data[plato][truncation]["DUAL"]["VERTS"]
    e2 = solids_data[plato][truncation]["DUAL"]["EDGES"]
    f2 = solids_data[plato][truncation]["DUAL"]["FACES"]

    # resize (scale continuity)
    if vTrunc > 0.5:

        # for continuity we need to match the following two:
        # the VT FACE radius of the DUAL solid
        # the NT FACE radius of the MAIN solid
        r1 = get_radius(sType, "NT", "RF", vTrunc, eTrunc)
        r2 = get_radius(dualPairs[sType], "VT", "RF", 1 - vTrunc, eTrunc)

        size = size * r1 / r2

        # if dualPairs[sType] == "HEXAHEDRON":
        #     logger.debug("sizing HEXAHEDRON")
        #     size = size * r1 / ((1 + 2 * vTrunc) / 3)

        # elif dualPairs[sType] == "OCTAHEDRON":
        #     logger.debug("sizing OCTAHEDRON")
        #     size = size * r1 / vTrunc

        # elif dualPairs[sType] == "TETRVHEDRON":
        #     logger.debug("sizing TETRAHEDRON")
        #     size = size * r1 / ((4 * vTrunc - 1) / 3)

        # elif dualPairs[sType] == "DODECAHEDRON":
        #     logger.debug("sizing DODECAHEDRON")
        #     size = size * r1 / (1 - 2 / 3 * sqrt(2 - PHI) / PHI * (1 - vTrunc))
        #     logger.debug("size=", size)

        # elif dualPairs[sType] == "ICOSAHEDRON":
        #     logger.debug("sizing ICOSAHEDRON")
        #     size = size * r1 / (1 - 2 * sqrt((2 - PHI) / 5) * (1 - vTrunc))
        #     logger.debug("size=", size)

        # else:
        #     logger.debug("sizing NOTHING")
        # size = size

    # print("scaleRadius = ", scaleRadius)

    # if vTrunc > 0.5:
    #     scale = get_radius(dualPairs[sType], "VT", scaleRadius, 1-vTrunc, eTrunc)
    # else:
    #     scale = get_radius(sType, "VT", scaleRadius, vTrunc, eTrunc)

    # scale = get_radius(sType, "VT", scaleRadius, vTrunc, eTrunc)

    # size = size / scale

    v1 = [tuple(Vector(v) * size) for v in v1]
    v2 = [tuple(Vector(v) * size) for v in v2]

    data = [v2, e2, f2, v1, e1, f1] if dual else [v1, e1, f1, v2, e2, f2]

    return data


class SvSolidsNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Regular Solids '''
    bl_idname = 'SvSolidsNode'
    bl_label = 'Regular Solids'
    # bl_icon = 'MESH_SOLID'

    def update_solid(self, context):
        if self.updating:
            return

        self.preset = " "
        updateNode(self, context)

    def preset_items(self, context):
        return [(k, k, "", "", s[0]) for k, s in sorted(solidPresets.items(), key=lambda k: k[1][0])]

    def update_preset(self, context):
        items = self.preset_items(context)
        nextIndex = 1 + (int(self.pIndex) - 1) % (len(items) - 1)
        self.preset = items[nextIndex][0]
        updateNode(self, context)

    def update_presets(self, context):
        if self.preset == " ":
            return

        self.updating = True

        sType, dual, snub, vTrunc, eTrunc = solidPresets[self.preset][1:]
        self.sType = sType
        self.size = 1.0
        self.vTrunc = vTrunc
        self.eTrunc = eTrunc
        self.dual = dual
        self.snub = snub

        self.updating = False
        updateNode(self, context)

    preset = EnumProperty(
        name="Presets", items=preset_items,
        update=update_presets)

    sType = EnumProperty(
        name="Type", items=typeItems,
        description="Type of the platonic solid",
        default="TETRAHEDRON", update=update_solid)

    oType = EnumProperty(
        name="Output Type", items=outputItems,
        description="Type of the output",
        default="FACE CENTERS", update=update_solid)

    scaleRadii = EnumProperty(
        name="Scale Radii", items=scaleRadiiItems,
        description="Scale plato solid to in, mid or out radius",
        default="RV", update=update_solid)

    sizeItem = EnumProperty(
        name="Size Item", items=sizeItems,
        description="Item to size",
        default="EL", update=update_solid)

    outRadii = EnumProperty(
        name="Out Radii", items=outRadiiItems,
        description="In, mid or out radius",
        default="RV", update=update_solid)

    truncationType = EnumProperty(
        name="Truncation Type", items=truncationItems,
        description="Truncation NT, VT, ET",
        default="NT", update=update_solid)

    dual = BoolProperty(
        name='Dual', description='Dual of solid',
        default=False, update=update_solid)

    snub = EnumProperty(
        name="Snub", items=snubItems,
        description="Snub the solid",
        default="N", update=update_solid)

    size = FloatProperty(
        name='Size', description='Size of the solid',
        default=1.0, min=0.0, update=update_solid)

    vTrunc = FloatProperty(
        name='V Trunc', description='Vertex Truncation',
        default=0.0, min=0.0, max=1.0, update=update_solid)

    eTrunc = FloatProperty(
        name='E Trunc', description='Edge Truncation',
        default=0.0, min=0.0, max=1.0, update=update_solid)

    pIndex = IntProperty(
        name='Preset Index', description='Preset Index',
        default=1, min=1, update=update_preset)

    updating = BoolProperty(default=False)  # used for disabling update callback

    def sv_init(self, context):
        self.width = 233
        self.inputs.new('StringsSocket', "S").prop_name = 'size'
        self.inputs.new('StringsSocket', "V").prop_name = 'vTrunc'
        self.inputs.new('StringsSocket', "E").prop_name = 'eTrunc'

        self.inputs.new('StringsSocket', "P").prop_name = 'pIndex'

        self.outputs.new('VerticesSocket', "Main Verts")
        self.outputs.new('StringsSocket',  "Main Edges")
        self.outputs.new('StringsSocket',  "Main Polys")

        self.outputs.new('VerticesSocket', "Pair Verts")
        self.outputs.new('StringsSocket',  "Pair Edges")
        self.outputs.new('StringsSocket',  "Pair Polys")

        self.outputs.new('VerticesSocket', "Original Verts")
        self.outputs.new('StringsSocket',  "Original Edges")
        self.outputs.new('StringsSocket',  "Original Polys")

        self.outputs.new('VerticesSocket',  "Other Verts")

        self.outputs.new('StringsSocket',  "Names")

        self.outputs.new('StringsSocket',  "Radius")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'preset', text="")
        layout.prop(self, 'sType')
        layout.prop(self, 'oType')
        # layout.prop(self, 'scaleRadii', expand=True)
        layout.prop(self, 'sizeItem', expand=False)
        layout.prop(self, 'snub', expand=True)
        layout.prop(self, "dual")

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'truncationType', expand=True)
        layout.prop(self, 'outRadii', expand=True)

    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        # input_P = self.inputs["P"].sv_get()[0][0]  # p Index

        # print("P = ", input_P)
        # print("updating preset : ", input_P)
        # items = self.preset_items(context)
        # nextIndex = 1 + (int(input_P) - 1) % (len(items)-1)
        # self.preset = items[nextIndex][0]

        # input values lists (single or multi value)
        input_S = self.inputs["S"].sv_get()[0]  # size
        input_V = self.inputs["V"].sv_get()[0]  # v trunc
        input_E = self.inputs["E"].sv_get()[0]  # e trunc

        # bound check the list values
        # m1, m2= [0.0001, 0.9999]
        m1, m2 = [0, 1]
        input_S = list(map(lambda x: max(0, x), input_S))
        input_V = list(map(lambda x: max(m1, min(m2, x)), input_V))
        input_E = list(map(lambda x: max(m1, min(m2, x)), input_E))

        parameters = match_long_repeat([input_S, input_V, input_E])

        mainVertList, mainEdgeList, mainPolyList = [[], [], []]
        pairVertList, pairEdgeList, pairPolyList = [[], [], []]
        for s, v, e in zip(*parameters):
            data = make_solid(self.sType, self.dual, self.snub, self.scaleRadii, s, v, e)
            mainVerts, mainEdges, mainPolys, pairVerts, pairEdges, pairPolys = data

            if self.sizeItem != "EL":
                truncation = self.sizeItem[0] + "T"
                radius = "R" + self.sizeItem[1]
                print("truncation = ", truncation)
                print("radius = ", radius)
                r1 = get_radius(self.sType, "NT", "RV", v, e)
                r2 = get_radius(self.sType, truncation, radius, v, e)

                # print("truncationType = ", self.truncationType)
                # print("outRadii = ", self.outRadii)
                # r1 = get_radius(self.sType, "NT", "RV", v, e)
                # r2 = get_radius(self.sType, self.truncationType, self.outRadii, v, e)
                # r2 = 1
                # r1 = 1
                size = s / r2
                mainVerts = [tuple(Vector(vert) * size) for vert in mainVerts]
                pairVerts = [tuple(Vector(vert) * size) for vert in pairVerts]

            mainVertList.append(mainVerts)
            mainEdgeList.append(mainEdges)
            mainPolyList.append(mainPolys)

            pairVertList.append(pairVerts)
            pairEdgeList.append(pairEdges)
            pairPolyList.append(pairPolys)

        self.outputs['Main Verts'].sv_set(mainVertList)
        self.outputs['Main Edges'].sv_set(mainEdgeList)
        self.outputs['Main Polys'].sv_set(mainPolyList)

        self.outputs['Pair Verts'].sv_set(pairVertList)
        self.outputs['Pair Edges'].sv_set(pairEdgeList)
        self.outputs['Pair Polys'].sv_set(pairPolyList)

        make_platonic_solid(self.sType)

        originalVerts = solids_data[self.sType]["NT"]["MAIN"]["VERTS"]
        originalEdges = solids_data[self.sType]["NT"]["MAIN"]["EDGES"]
        originalPolys = solids_data[self.sType]["NT"]["MAIN"]["FACES"]

        size = 1
        if self.scaleRadii == "RF":  # in
            size = size / radii[self.sType][0]
        elif self.scaleRadii == "RE":  # mid
            size = size / radii[self.sType][1]
        elif self.scaleRadii == "RV":  # out
            size = size / radii[self.sType][2]
        else:
            size = size  # no scaling

        originalVerts = [tuple(Vector(v) * size) for v in originalVerts]

        self.outputs['Original Verts'].sv_set([originalVerts])
        self.outputs['Original Edges'].sv_set([originalEdges])
        self.outputs['Original Polys'].sv_set([originalPolys])

        if self.outputs['Other Verts'].is_linked:

            if self.vTrunc == 0:
                plato = self.sType
                truncation = "NT"

            elif self.vTrunc == 1:
                plato = dualPairs[self.sType]
                truncation = "NT"

            elif self.vTrunc <= 0.5:  # simple truncation of the solid
                plato = self.sType
                if self.eTrunc == 0:  # no edge truncation -> just vertex truncation
                    truncation = "VT"
                else:  # vertex & edge truncation
                    truncation = "ET"

            else:  # vTrunc > 0.5 -> simple (mirrored) truncation of the dual
                plato = dualPairs[self.sType]
                if self.eTrunc == 0:  # no edge truncation -> just vertex truncation
                    truncation = "VT"
                else:  # vertex & edge truncation
                    truncation = "ET"

            if self.oType in ["FACE NORMALS", "FACE CENTERS", "EDGE CENTERS"]:
                # print("plato = ", plato)
                # print("sType = ", self.sType)
                # print("self.vTrunc = ", self.vTrunc)
                # print("self.eTrunc = ", self.eTrunc)
                # print("truncation = ", truncation)
                # print("oType = ", self.oType)
                pair = "DUAL" if self.dual else "MAIN"
                otherVerts = list(solids_data[plato][truncation][pair][self.oType].values())
            else:  # DUAL VERTS
                otherVerts = solids_data[plato][truncation][pair][self.oType]

            self.outputs['Other Verts'].sv_set([otherVerts])

        if self.preset != " ":
            if self.dual:
                dualPairNamesR = dict(map(reversed, dualPairNames.items()))
                dualName = dualPairNamesR[self.preset]
            else:
                dualName = dualPairNames[self.preset]
            self.outputs["Names"].sv_set([[self.preset, dualName]])
        else:
            self.outputs["Names"].sv_set([["alpha", "omega"]])

        radius = get_radius(self.sType, self.truncationType, self.outRadii, input_V[0], input_E[0])
        radius = radius * size
        self.outputs["Radius"].sv_set([[radius]])


def register():
    bpy.utils.register_class(SvSolidsNode)


def unregister():
    bpy.utils.unregister_class(SvSolidsNode)


'''
TODO:

- add dual edge/face creation : DONE
- add continuity scaling : DONE
- fix bugs when vt > 0.5 for other verts? : DONE
- add back the resizing (size) : DONE
- fix snub duplicate vertes and face orientation : DONE
- find correct way to compute snub duals
- add NT, VT, ET vep output based on user selection
- cleanup the code
- factorize debug info into debug print function : DONE


'''
