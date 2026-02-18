# Data Directory

This directory contains the GeoPackage database used by the SG Diagram Downloader plugin.

## sg_diagrams.gpkg

The main database file containing reference data for the plugin.

### Required Tables

#### regional_office

Contains the mapping between region codes, provinces, and Surveyor General office information needed to construct download URLs.

##### Schema

```sql
CREATE TABLE regional_office (
    province TEXT,
    region_code TEXT,
    typology TEXT,
    office TEXT,
    office_no TEXT
);
```

##### Columns

| Column | Description |
|--------|-------------|
| `province` | Province name (must match valid province names below) |
| `region_code` | 8-character region division code (first 8 chars of SG code) |
| `typology` | Area type: "Rural" or "Urban" |
| `office` | Office code (e.g., "SGCTN", "SGELN", "SGPMB") |
| `office_no` | Office number used in download URLs |

#### provinces (Optional but Recommended)

A polygon layer used to determine which province a parcel falls into based on its centroid location. This is used to route download requests to the correct Surveyor General office.

##### Layer Requirements

| Requirement | Value |
|-------------|-------|
| **Layer name** | `provinces` |
| **Geometry type** | Polygon or MultiPolygon |
| **Geometry column** | `geom` (standard GeoPackage convention) |
| **CRS** | EPSG:4326 (WGS84) |

##### Required Attributes

The layer must have one of the following attribute columns containing the province name:

- `province` (preferred)
- `PROVINCE`
- `name`
- `NAME`
- `provname`
- `PROVNAME`

##### Valid Province Names

Province names must match exactly (case-sensitive):

- Eastern Cape
- Free State
- Gauteng
- KwaZulu-Natal
- Limpopo
- Mpumalanga
- Northern Cape
- North West
- Western Cape

##### Example Schema

```sql
CREATE TABLE provinces (
    fid INTEGER PRIMARY KEY,
    geom MULTIPOLYGON,
    province TEXT NOT NULL
);
```

##### Adding a Provinces Layer

You can add a provinces layer from any South African administrative boundaries dataset. For example, using QGIS:

1. Load your provinces polygon layer
2. Ensure it has a `province` field with valid province names
3. Export to the GeoPackage:
   - Right-click layer -> Export -> Save Features As...
   - Format: GeoPackage
   - File name: `data/sg_diagrams.gpkg`
   - Layer name: `provinces`
   - CRS: EPSG:4326

### Fallback Behaviour

If the provinces layer is missing, invalid, or has schema issues (e.g., wrong geometry column name), the plugin will fall back to a coordinate-based lookup using approximate bounding boxes for each province.

The fallback uses these approximate bounds (EPSG:4326):

| Province | Min X | Min Y | Max X | Max Y |
|----------|-------|-------|-------|-------|
| Western Cape | 17.5 | -34.5 | 23.5 | -31.0 |
| Eastern Cape | 23.5 | -34.0 | 30.5 | -30.5 |
| Northern Cape | 16.5 | -32.0 | 24.5 | -26.5 |
| Free State | 24.0 | -30.5 | 30.0 | -26.5 |
| KwaZulu-Natal | 28.5 | -31.5 | 33.0 | -27.0 |
| Gauteng | 27.0 | -26.5 | 29.0 | -25.0 |
| Mpumalanga | 28.5 | -27.0 | 32.0 | -24.0 |
| Limpopo | 26.5 | -25.0 | 31.5 | -22.0 |
| North West | 22.5 | -28.0 | 28.0 | -24.5 |

**Note:** The bounding box fallback is less accurate than proper spatial lookup, especially for parcels near province boundaries. For best results, include a valid provinces layer in the GeoPackage.
