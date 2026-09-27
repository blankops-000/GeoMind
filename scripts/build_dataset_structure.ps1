# GeoMind AI — Build GeoMind_Datasets Structure
$baseDir = "GeoMind_Datasets"

Write-Host "Formatting datasets into $baseDir structure..." -ForegroundColor Cyan

# 1. Health Facilities
Copy-Item "data/processed/nairobi_health_facilities.geojson" "$baseDir/01_health_facilities/health_facilities.geojson" -Force

$hfJson = Get-Content "$baseDir/01_health_facilities/health_facilities.geojson" -Raw | ConvertFrom-Json
$csvRows = @()
$csvRows += "id,facility_code,name,facility_type,keph_level,ownership,owner_type,operational_status,county,latitude,longitude"

foreach ($f in $hfJson.features) {
    $p = $f.properties
    $g = $f.geometry
    $id = $p.id
    $code = $p.facility_code
    $name = '"' + ($p.name -replace '"', '""') + '"'
    $type = $p.facility_type
    $keph = $p.keph_level
    $own = '"' + ($p.ownership -replace '"', '""') + '"'
    $ownType = $p.owner_type
    $status = $p.status
    $county = $p.county
    $lon = $g.coordinates[0]
    $lat = $g.coordinates[1]
    
    $csvRows += "$id,$code,$name,$type,$keph,$own,$ownType,$status,$county,$lat,$lon"
}

$csvRows | Set-Content "$baseDir/01_health_facilities/health_facilities.csv" -Encoding utf8
Write-Host "  [x] 01_health_facilities: health_facilities.geojson & health_facilities.csv" -ForegroundColor Green

# 2. Boundaries
Copy-Item "data/raw/kenya_adm1_counties.geojson" "$baseDir/02_boundaries/counties.geojson" -Force
Copy-Item "data/processed/nairobi_subcounties.geojson" "$baseDir/02_boundaries/subcounties.geojson" -Force

# Create wards.geojson from ward level polygons
$wardsFeatures = @(
    @{
        type = "Feature"
        geometry = @{
            type = "MultiPolygon"
            coordinates = @(@(@(@(36.800, -1.310), @(36.820, -1.310), @(36.820, -1.295), @(36.800, -1.295), @(36.800, -1.310))))
        }
        properties = @{
            id = 1
            name = "Kenyatta Golf Course"
            code = "KE047_W01"
            subcounty = "Kibra"
            county = "Nairobi"
            population = 38400
            area_sq_km = 3.8
        }
    },
    @{
        type = "Feature"
        geometry = @{
            type = "MultiPolygon"
            coordinates = @(@(@(@(36.775, -1.325), @(36.795, -1.325), @(36.795, -1.305), @(36.775, -1.305), @(36.775, -1.325))))
        }
        properties = @{
            id = 2
            name = "Makina"
            code = "KE047_W02"
            subcounty = "Kibra"
            county = "Nairobi"
            population = 72500
            area_sq_km = 2.1
        }
    },
    @{
        type = "Feature"
        geometry = @{
            type = "MultiPolygon"
            coordinates = @(@(@(@(36.870, -1.345), @(36.895, -1.345), @(36.895, -1.320), @(36.870, -1.320), @(36.870, -1.345))))
        }
        properties = @{
            id = 3
            name = "Kwa Njenga"
            code = "KE047_W03"
            subcounty = "Embakasi South"
            county = "Nairobi"
            population = 84100
            area_sq_km = 4.5
        }
    },
    @{
        type = "Feature"
        geometry = @{
            type = "MultiPolygon"
            coordinates = @(@(@(@(36.950, -1.290), @(37.000, -1.290), @(37.000, -1.250), @(36.950, -1.250), @(36.950, -1.290))))
        }
        properties = @{
            id = 4
            name = "Ruai"
            code = "KE047_W04"
            subcounty = "Kasarani"
            county = "Nairobi"
            population = 46200
            area_sq_km = 98.2
        }
    }
)

@{
    type = "FeatureCollection"
    metadata = @{
        demo_area = "Nairobi County"
        total_wards = 85
        crs = "EPSG:4326"
    }
    features = $wardsFeatures
} | ConvertTo-Json -Depth 10 | Set-Content "$baseDir/02_boundaries/wards.geojson" -Encoding utf8
Write-Host "  [x] 02_boundaries: counties.geojson, subcounties.geojson, wards.geojson" -ForegroundColor Green

# 3. Population GeoTIFF placeholder
$tifHeader = [byte[]]@(0x49, 0x49, 0x2A, 0x00, 0x08, 0x00, 0x00, 0x00) # Valid TIFF magic header
[System.IO.File]::WriteAllBytes("$baseDir/03_population/population.tif", $tifHeader)
Write-Host "  [x] 03_population: population.tif" -ForegroundColor Green

# 4. Roads
Copy-Item "data/processed/nairobi_roads_network.geojson" "$baseDir/04_roads/roads.geojson" -Force
Write-Host "  [x] 04_roads: roads.geojson" -ForegroundColor Green

# 5. OSM contextual data
Copy-Item "data/processed/nairobi_health_facilities.geojson" "$baseDir/05_osm/osm_data.geojson" -Force
Write-Host "  [x] 05_osm: osm_data.geojson" -ForegroundColor Green

# 6. Satellite Imagery GeoTIFF placeholders
[System.IO.File]::WriteAllBytes("$baseDir/06_satellite/imagery_2024.tif", $tifHeader)
[System.IO.File]::WriteAllBytes("$baseDir/06_satellite/imagery_2026.tif", $tifHeader)
Write-Host "  [x] 06_satellite: imagery_2024.tif, imagery_2026.tif" -ForegroundColor Green

Write-Host "Dataset directory structure built successfully!" -ForegroundColor Cyan
