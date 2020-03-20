3D Project
----------

This node projects vertices in 3D space into 2D space.

Modes
=====

The available **Modes** are: PLANE, SPHERE.


Inputs
======

**Verts**

+-----------------+--------------+---------+-------------------------------------------------+
| Param           | Type         | Default | Description                                     |
+=================+==============+=========+=================================================+
| **Projection**  | Enum         | PLANAR  | Projection mode                                 |
|                 |  PLANAR      |         |  PLANE  : Perspective projection onto a plane   |
|                 |  SPHERICAL   |         |  SPHERE : Perspective projection onto a sphere  |
|                 |  CYLINDRICAL |         |  SPHERE : Perspective projection onto a sphere  |
+-----------------+--------------+---------+-------------------------------------------------+
| **Distance**    | float        | 2.0     |  Distance between the projection point and the  |
|                 |              |         |  projection surface.                            |
+-----------------+--------------+---------+-------------------------------------------------+

Outputs
=======

**Verts**

