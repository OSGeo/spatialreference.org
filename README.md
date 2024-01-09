# spatialreference.org

This is the base repository of the webpage [https://spatialreference.org](https://spatialreference.org)

Its content is automatically refreshed from the PROJ' SRS database, at each [PROJ](https://proj.org) release using [pyproj](https://pyproj4.github.io/pyproj/)

It contains several catalogs of Spatial Reference Systems: EPSG, ESRI, IAU:2015, IGNF, NKG and OGC.

To generate the webpage in your computer just run `scripts/run.sh` (it uses docker) and check the output in the folder `dist`.

Spatialreference.org has a sibling project under the PROJ umbrella: [CRS Explorer](https://crs-explorer.proj.org). It has a different approach displaying all the available CRSs and filtering them.
