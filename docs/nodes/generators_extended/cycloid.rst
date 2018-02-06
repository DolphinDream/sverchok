Cycloid
=======

Functionality
-------------
The cycloid node creates cycloid paths given a set of main parameters: radii, periods, offsets and time.

Inputs
------

All inputs are vectorized and they will accept single or multiple values.

- **Radius1**
- **Radius2**
- **Period1**
- **Period2**
- **Offset1**
- **Offset2**
- **Time**
- **Resolution**

Parameters
----------

The **Centering** parameter lets you center the cycloid around one of its planets.

All parameters except **Centering** can take values from the node itself or an external input.

The inputs are "sanitized" to restrict their values to valid domains:
- The radii are floats with values >= 0
- The periods are floats with values >= 0
- The offsets are a floats with values in the range [0.0, 1.0]
- The resolution is an integer with value >= 3

+------------------+--------+---------+----------------------------------------+
| Param            | Type   | Default | Description                            |
+==================+========+=========+========================================+
| **Radius1**      | Float  | 2.0     | Radius of the first orbit              |
+------------------+--------+---------+----------------------------------------+
| **Radius2**      | Float  | 3.0     | Radius of the second orbit             |
+------------------+--------+---------+----------------------------------------+
| **Period1**      | Float  | 2.0     | Period of the first orbit              |
+------------------+--------+---------+----------------------------------------+
| **Period2**      | Float  | 7.0     | Minor radius of the cycloid            |
+------------------+--------+---------+----------------------------------------+
| **Offset1**      | Float  | 0.0     | Offset of the first orbit              |
+------------------+--------+---------+----------------------------------------+
| **Offset2**      | Float  | 0.0     | Offset of the second orbit             |
+------------------+--------+---------+----------------------------------------+
| **Resolution**   | Int    | 200     | Number of vertices in the path         |
+------------------+--------+---------+----------------------------------------+


Outputs
-------
Outputs will be generated when connected.

**Verts**, **Edges**
These are the vertices and edges of the cycloid.


Example of usage
----------------

