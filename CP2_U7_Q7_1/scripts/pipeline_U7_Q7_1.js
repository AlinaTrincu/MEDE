// Google Earth Engine Code Editor — CP1 U7/Q7.1
// Produces one aligned observation per HydroLAKES feature x calendar month.
// It does not invent missing values: valid_area_km2 helps identify JRC coverage gaps.
// Run this script in the same authenticated GEE account used to test JRC/ERA5-Land.

var START = ee.Date('2001-01-01');
var END = ee.Date('2022-01-01'); // exclusive; includes December 2021
var EXPORT_NAME = 'U7_Q7_1_lac_luna_2001_2021';

var lakes = ee.FeatureCollection('projects/sat-io/open-datasets/HydroLakes/lake_poly_v10');
var romania = ee.FeatureCollection('FAO/GAUL/2015/level0')
  .filter(ee.Filter.eq('ADM0_NAME', 'Romania'));
var lakeSubset = lakes.filterBounds(romania.geometry());

var gsw = ee.ImageCollection('JRC/GSW1_4/MonthlyHistory');
var era = ee.ImageCollection('ECMWF/ERA5_LAND/MONTHLY_AGGR');

print('JRC images in selected period', gsw.filterDate(START, END).size());
print('ERA5-Land months in selected period', era.filterDate(START, END).size());
print('HydroLAKES features intersecting Romania', lakeSubset.size());
print('Example lake feature', lakeSubset.first());

var nMonths = END.difference(START, 'month');
var offsets = ee.List.sequence(0, nMonths.subtract(1));

var byMonth = offsets.map(function(offset) {
  var monthStart = START.advance(ee.Number(offset), 'month');
  var monthEnd = monthStart.advance(1, 'month');
  var label = monthStart.format('YYYY-MM');
  var monthNumber = ee.Number(monthStart.get('month'));

  var jrc = ee.Image(gsw.filterDate(monthStart, monthEnd).first());
  var waterClass = jrc.select('water');
  var validPixels = ee.Image.pixelArea()
    .updateMask(waterClass.mask())
    .rename('valid_area_m2');
  var waterPixels = ee.Image.pixelArea()
    .updateMask(waterClass.eq(2))
    .rename('water_m2');

  var areaStats = waterPixels.addBands(validPixels).reduceRegions({
    collection: lakeSubset,
    reducer: ee.Reducer.sum(),
    scale: 30,
    tileScale: 4
  });

  var climate = ee.Image(era.filterDate(monthStart, monthEnd).first());
  var climateImage = climate.select('temperature_2m').subtract(273.15).rename('t2m_c')
    .addBands(climate.select('total_precipitation_sum').multiply(1000).rename('precip_mm'));
  var climateStats = climateImage.reduceRegions({
    collection: areaStats,
    reducer: ee.Reducer.mean(),
    scale: 11132,
    tileScale: 4
  });

  return climateStats.map(function(f) {
    var valid = ee.Number(ee.Algorithms.If(
      ee.Algorithms.IsEqual(f.get('valid_area_m2'), null), 0, f.get('valid_area_m2')));
    var water = ee.Number(ee.Algorithms.If(
      ee.Algorithms.IsEqual(f.get('water_m2'), null), 0, f.get('water_m2')));
    var observedWater = ee.Algorithms.If(valid.gt(0), water.divide(1e6), null);
    return ee.Feature(null, {
      Hylak_id: f.get('Hylak_id'),
      month: label,
      year: monthStart.get('year'),
      month_number: monthNumber,
      water_km2: observedWater,
      valid_area_km2: valid.divide(1e6),
      t2m_c: f.get('t2m_c'),
      precip_mm: f.get('precip_mm'),
      month_sin: monthNumber.multiply(2 * Math.PI / 12).sin(),
      month_cos: monthNumber.multiply(2 * Math.PI / 12).cos()
    });
  });
});

var aligned = ee.FeatureCollection(byMonth).flatten();
print('Months expected per lake', nMonths);
print('Rows expected (lakes x months)', lakeSubset.size().multiply(nMonths));
print('Aligned rows prepared', aligned.size());
print('Sample aligned rows', aligned.limit(5));

Export.table.toDrive({
  collection: aligned,
  description: EXPORT_NAME,
  fileNamePrefix: EXPORT_NAME,
  fileFormat: 'CSV',
  selectors: ['Hylak_id', 'month', 'year', 'month_number', 'water_km2',
    'valid_area_km2', 't2m_c', 'precip_mm', 'month_sin', 'month_cos']
});
