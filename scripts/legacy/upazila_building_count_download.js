// Original Google Earth Engine Code Editor script (JavaScript).
// Superseded by scripts/download_building_counts.py, which generalizes this
// to any country (via FAO GAUL boundaries, no manual asset upload needed)
// and downloads results directly to a local CSV/XLSX instead of exporting
// to Google Drive. Kept here for reference / for reproducing the exact
// original Bangladesh-only workflow in the GEE Code Editor.
//
// Requires a "districts" table imported as an Asset in the Code Editor
// (Import > table) before running.

// District layer imported from Assets
var districts = ee.FeatureCollection(table);

// Microsoft Buildings (Bangladesh only - see download_building_counts.py
// for a country-general alternative using Google Open Buildings V3)
var buildings = ee.FeatureCollection(
  'projects/sat-io/open-datasets/MSBuildings/Bangladesh'
);

// Count buildings in each district
var output = districts.map(function(district) {
  var count = buildings.filterBounds(district.geometry()).size();
  return district.set('building_count', count);
});

// Check one feature only
print('Sample district:', output.first());

// District name + count only
var output_clean = output.map(function(f) {
  return ee.Feature(null, {
    ADM2_EN: f.get('ADM2_EN'),   // change if your asset uses a different field name
    building_count: f.get('building_count')
  });
});

// Preview only first few rows
print('Preview:', output_clean.limit(10));

Export.table.toDrive({
  collection: output_clean,
  description: 'Bangladesh_District_Building_Count',
  fileNamePrefix: 'bd_district_building_count',
  fileFormat: 'CSV'
});
