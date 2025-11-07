"""This is an automatically generated stub for `geo.capnp`."""

import os

import capnp

capnp.remove_import_hook()
here = os.path.dirname(os.path.abspath(__file__))
module_file = os.path.abspath(os.path.join(here, "../zalfmas_capnp_schemas/geo.capnp"))
import_path = [here, os.path.join(here, "../zalfmas_capnp_schemas")]
EPSG = capnp.load(module_file, imports=import_path).EPSG
EPSGBuilder = EPSG
EPSGReader = EPSG
UTMCoord = capnp.load(module_file, imports=import_path).UTMCoord
UTMCoordBuilder = UTMCoord
UTMCoordReader = UTMCoord
LatLonCoord = capnp.load(module_file, imports=import_path).LatLonCoord
LatLonCoordBuilder = LatLonCoord
LatLonCoordReader = LatLonCoord
GKCoord = capnp.load(module_file, imports=import_path).GKCoord
GKCoordBuilder = GKCoord
GKCoordReader = GKCoord
Point2D = capnp.load(module_file, imports=import_path).Point2D
Point2DBuilder = Point2D
Point2DReader = Point2D
RowCol = capnp.load(module_file, imports=import_path).RowCol
RowColBuilder = RowCol
RowColReader = RowCol
Coord = capnp.load(module_file, imports=import_path).Coord
CoordBuilder = Coord
CoordReader = Coord
RectBounds = capnp.load(module_file, imports=import_path).RectBounds
RectBoundsBuilder = RectBounds
RectBoundsReader = RectBounds
