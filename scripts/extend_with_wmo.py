#!/usr/bin/env python3

from __future__ import annotations

import json
import hashlib
import time
import urllib.error
import urllib.request
from urllib.parse import urlencode
from pathlib import Path


BASE_DATA_PATH = Path("data/climate-data.json")
METADATA_PATH = Path("data/region-metadata.json")
OUTPUT_JSON_PATH = Path("data/climate-data.json")
OUTPUT_JS_PATH = Path("data/climate-data.js")
CACHE_DIR = Path("data/.open-meteo-cache")
CONTINENT_ORDER = {"아프리카": 0, "아메리카": 1, "오세아니아": 2, "유라시아": 3}
OPEN_METEO_DOCS_URL = "https://open-meteo.com/en/docs/historical-weather-api"
OPEN_METEO_START_DATE = "1991-01-01"
OPEN_METEO_END_DATE = "2020-12-31"
OPEN_METEO_BATCH_SIZE = 1
CLIMATE_ORDER = {
    "Af": 0,
    "Am": 1,
    "Aw": 2,
    "BS": 3,
    "Bw": 4,
    "Cfa": 5,
    "Cfb": 6,
    "Cs": 7,
    "Cw": 8,
    "Df": 9,
    "Dw": 10,
    "ET": 11,
    "EF": 12,
    "H": 13,
}
HEMISPHERE_ORDER = {"북반구": 0, "남반구": 1}


def load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_json(url: str) -> dict | list:
    cache_path = CACHE_DIR / f"{hashlib.sha1(url.encode('utf-8')).hexdigest()}.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ClimateAtlasStudio/1.0 (+https://worldweather.wmo.int/)",
            "Accept": "application/json",
        },
    )

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    for attempt in range(8):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
                cache_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
                time.sleep(0.35)
                return payload
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == 7:
                raise
            retry_after = error.headers.get("Retry-After") if error.headers else None
            try:
                wait_seconds = max(10, int(retry_after)) if retry_after else min(120, 15 * (attempt + 1))
            except (TypeError, ValueError):
                wait_seconds = min(120, 15 * (attempt + 1))
            print(f"429 received for {url} -> retry in {wait_seconds}s", flush=True)
            time.sleep(wait_seconds)

    raise RuntimeError(f"Failed to fetch JSON after retries: {url}")


def normalize_climate_group(raw_code: str | None) -> str:
    if not raw_code:
        return ""

    compact = raw_code.replace("북", "").replace("남", "").replace(" ", "")
    upper = compact.upper()
    lower = compact.lower()

    if upper in {"AH", "H"}:
        return "H"
    if upper.startswith("EF"):
        return "EF"
    if upper.startswith("ET"):
        return "ET"
    if upper.startswith("DW"):
        return "Dw"
    if upper.startswith("DF"):
        return "Df"
    if lower.startswith("cfa"):
        return "Cfa"
    if lower.startswith("cfb"):
        return "Cfb"
    if lower.startswith("cs"):
        return "Cs"
    if lower.startswith("cw"):
        return "Cw"
    if lower == "af":
        return "Af"
    if lower == "am":
        return "Am"
    if lower == "aw":
        return "Aw"
    if upper == "BS":
        return "BS"
    if lower == "bw":
        return "Bw"

    return compact


def format_aliases(*values: str | None) -> list[str]:
    seen: set[str] = set()
    aliases: list[str] = []
    for value in values:
        if not value:
            continue
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        aliases.append(normalized)
    return aliases


def average(values: list[float]) -> float:
    return round(sum(values) / len(values), 1)


def round_coordinate(value: float) -> str:
    return f"{float(value):.4f}".rstrip("0").rstrip(".")


def chunked(items: list[dict], size: int) -> list[list[dict]]:
    return [items[index:index + size] for index in range(0, len(items), size)]


def infer_hemisphere(latitude: float | None) -> str:
    if latitude is None:
        return ""
    return "북반구" if float(latitude) >= 0 else "남반구"


def apply_metadata(region: dict, metadata_by_name: dict[str, dict]) -> dict:
    metadata = metadata_by_name.get(region["name"])
    if not metadata:
        region["hemisphere"] = infer_hemisphere(region.get("coordinates", {}).get("latitude"))
        return region

    if metadata.get("englishName"):
        region["englishName"] = metadata["englishName"]

    if metadata.get("coordinates"):
        region["coordinates"] = {
            "latitude": round(float(metadata["coordinates"]["latitude"]), 4),
            "longitude": round(float(metadata["coordinates"]["longitude"]), 4),
        }

    if metadata.get("country"):
        region["country"] = metadata["country"]

    region["aliases"] = format_aliases(
        region.get("name"),
        region.get("englishName"),
        *(region.get("aliases") or []),
        *(metadata.get("aliases") or []),
    )
    region["hemisphere"] = infer_hemisphere(region.get("coordinates", {}).get("latitude"))
    return region


def compute_monthly_temperature(month: dict) -> float:
    mean_temp = month.get("meanTemp")
    if mean_temp not in (None, ""):
        return round(float(mean_temp), 1)

    max_temp = month.get("maxTemp")
    min_temp = month.get("minTemp")
    if max_temp in (None, "") or min_temp in (None, ""):
        raise ValueError(f"Missing temperature values in WMO month payload: {month}")

    return round((float(max_temp) + float(min_temp)) / 2, 1)


def build_wmo_entry(spec: dict, metadata_by_name: dict[str, dict]) -> dict:
    city_id = spec["wmoCityId"]
    url = f"https://worldweather.wmo.int/en/json/{city_id}_en.json"
    payload = fetch_json(url)

    city = payload["city"]
    months = city["climate"]["climateMonth"]
    monthly_temperature = [compute_monthly_temperature(month) for month in months]
    monthly_precipitation = [round(float(month["rainfall"]), 1) for month in months]
    annual_mean_temperature = round(sum(monthly_temperature) / len(monthly_temperature), 1)
    annual_precipitation = round(sum(monthly_precipitation), 1)

    entry = {
        "name": spec["name"],
        "englishName": spec["englishName"],
        "aliases": format_aliases(
            spec["name"],
            spec["englishName"],
            city.get("cityName"),
            *spec.get("aliases", []),
        ),
        "continent": spec["continent"],
        "country": spec["country"],
        "climateCode": spec["climateGroup"],
        "climateGroup": spec["climateGroup"],
        "months": [f"{month['month']}월" for month in months],
        "monthlyTemperatureC": monthly_temperature,
        "monthlyPrecipitationMm": monthly_precipitation,
        "annualMeanTemperatureC": annual_mean_temperature,
        "annualPrecipitationMm": annual_precipitation,
        "coordinates": {
            "latitude": round(float(city["cityLatitude"]), 4),
            "longitude": round(float(city["cityLongitude"]), 4),
        },
        "source": {
            "type": "wmo",
            "label": "WMO WWIS",
            "cityId": city_id,
            "cityName": city["cityName"],
            "url": url,
            "period": "1981-2010",
            "note": "월평균 기온은 WMO JSON에 meanTemp가 비어 있어 월평균 최고·최저기온의 평균으로 계산했습니다.",
        },
    }
    return apply_metadata(entry, metadata_by_name)


def build_open_meteo_url(specs: list[dict]) -> str:
    latitudes = ",".join(round_coordinate(spec["coordinates"]["latitude"]) for spec in specs)
    longitudes = ",".join(round_coordinate(spec["coordinates"]["longitude"]) for spec in specs)
    timezones = ",".join("auto" for _ in specs)
    query = urlencode(
        {
            "latitude": latitudes,
            "longitude": longitudes,
            "start_date": OPEN_METEO_START_DATE,
            "end_date": OPEN_METEO_END_DATE,
            "daily": "temperature_2m_mean,precipitation_sum",
            "timezone": timezones,
            "models": "era5",
        }
    )
    return f"https://archive-api.open-meteo.com/v1/archive?{query}"


def build_monthly_normals(daily: dict) -> tuple[list[float], list[float]]:
    time_values = daily.get("time", [])
    temperature_values = daily.get("temperature_2m_mean", [])
    precipitation_values = daily.get("precipitation_sum", [])
    if (
        not time_values
        or len(time_values) != len(temperature_values)
        or len(time_values) != len(precipitation_values)
    ):
        raise ValueError("Open-Meteo daily payload is incomplete for monthly normal calculation.")

    temperature_by_month: dict[int, list[float]] = {month: [] for month in range(1, 13)}
    precipitation_totals_by_month: dict[int, dict[int, float]] = {
        month: {} for month in range(1, 13)
    }

    for date_str, temperature, precipitation in zip(
        time_values,
        temperature_values,
        precipitation_values,
    ):
        year, month, _ = (int(piece) for piece in date_str.split("-"))
        if temperature not in (None, ""):
            temperature_by_month[month].append(float(temperature))

        precipitation_value = 0.0 if precipitation in (None, "") else float(precipitation)
        precipitation_totals_by_month[month][year] = (
            precipitation_totals_by_month[month].get(year, 0.0) + precipitation_value
        )

    monthly_temperature = [average(temperature_by_month[month]) for month in range(1, 13)]
    monthly_precipitation = [average(list(precipitation_totals_by_month[month].values())) for month in range(1, 13)]
    return monthly_temperature, monthly_precipitation


def build_open_meteo_entry(
    spec: dict,
    payload: dict,
    metadata_by_name: dict[str, dict],
    api_url: str,
) -> dict:
    daily = payload["daily"]
    monthly_temperature, monthly_precipitation = build_monthly_normals(daily)
    annual_mean_temperature = average(monthly_temperature)
    annual_precipitation = round(sum(monthly_precipitation), 1)

    entry = {
        "name": spec["name"],
        "englishName": spec["englishName"],
        "aliases": format_aliases(
            spec["name"],
            spec["englishName"],
            *(spec.get("aliases") or []),
        ),
        "continent": spec["continent"],
        "country": spec["country"],
        "climateCode": spec.get("climateCode") or spec["climateGroup"],
        "climateGroup": spec["climateGroup"],
        "months": [f"{month}월" for month in range(1, 13)],
        "monthlyTemperatureC": monthly_temperature,
        "monthlyPrecipitationMm": monthly_precipitation,
        "annualMeanTemperatureC": annual_mean_temperature,
        "annualPrecipitationMm": annual_precipitation,
        "coordinates": {
            "latitude": round(float(spec["coordinates"]["latitude"]), 4),
            "longitude": round(float(spec["coordinates"]["longitude"]), 4),
        },
        "source": {
            "type": "open-meteo",
            "label": "Open-Meteo Historical Weather API",
            "url": OPEN_METEO_DOCS_URL,
            "apiUrl": api_url,
            "model": "ERA5",
            "period": "1991-2020",
            "note": "기본 지역 통계를 모두 Open-Meteo ERA5 1991-2020 일별 자료 기반 월평년값으로 통일했습니다.",
        },
    }
    return apply_metadata(entry, metadata_by_name)


def enrich_existing_region(region: dict, metadata_by_name: dict[str, dict]) -> dict:
    aliases = format_aliases(region.get("name"), region.get("englishName"), *(region.get("aliases") or []))
    region["aliases"] = aliases
    region["climateGroup"] = normalize_climate_group(region.get("climateCode") or region.get("climateGroup"))
    region["englishName"] = region.get("englishName") or region.get("name")
    return apply_metadata(region, metadata_by_name)


def build_standardized_spec(region: dict, metadata_by_name: dict[str, dict]) -> dict:
    enriched = enrich_existing_region(dict(region), metadata_by_name)
    coordinates = enriched.get("coordinates")
    if not coordinates:
        raise ValueError(f"Missing coordinates for region: {enriched.get('name')}")

    return {
        "name": enriched["name"],
        "englishName": enriched.get("englishName") or enriched["name"],
        "aliases": enriched.get("aliases") or [],
        "continent": enriched.get("continent", ""),
        "country": enriched.get("country", ""),
        "climateCode": enriched.get("climateCode") or enriched.get("climateGroup", ""),
        "climateGroup": normalize_climate_group(
            enriched.get("climateGroup") or enriched.get("climateCode")
        ),
        "coordinates": {
            "latitude": float(coordinates["latitude"]),
            "longitude": float(coordinates["longitude"]),
        },
    }


def sort_regions(region: dict) -> tuple:
    return (
        CONTINENT_ORDER.get(region.get("continent"), 99),
        HEMISPHERE_ORDER.get(region.get("hemisphere"), 99),
        CLIMATE_ORDER.get(region.get("climateGroup"), 99),
        region.get("name", ""),
    )


def summarize_sources(regions: list[dict]) -> dict[str, int]:
    source_breakdown = {"pdf": 0, "wmo": 0, "open-meteo": 0}
    for region in regions:
        source_type = region.get("source", {}).get("type", "pdf")
        source_breakdown[source_type] = source_breakdown.get(source_type, 0) + 1
    return source_breakdown


def main() -> None:
    dataset = load_json(BASE_DATA_PATH)
    metadata_by_name = load_json(METADATA_PATH)
    standardized_specs = [
        build_standardized_spec(region, metadata_by_name)
        for region in dataset["regions"]
    ]
    regions = []
    total_regions = len(standardized_specs)
    for batch_index, batch_specs in enumerate(chunked(standardized_specs, OPEN_METEO_BATCH_SIZE), start=1):
        start_index = (batch_index - 1) * OPEN_METEO_BATCH_SIZE + 1
        end_index = start_index + len(batch_specs) - 1
        batch_label = ", ".join(spec["name"] for spec in batch_specs)
        print(
            f"[{start_index}-{end_index}/{total_regions}] Open-Meteo 배치 요청: {batch_label}",
            flush=True,
        )
        url = build_open_meteo_url(batch_specs)
        payload = fetch_json(url)
        payloads = payload if isinstance(payload, list) else [payload]
        if len(payloads) != len(batch_specs):
            raise ValueError(
                f"Open-Meteo batch size mismatch: requested {len(batch_specs)} locations, got {len(payloads)} payloads"
            )

        for offset, (spec, item_payload) in enumerate(zip(batch_specs, payloads), start=0):
            current_index = start_index + offset
            print(f"  -> [{current_index}/{total_regions}] {spec['name']} 처리 완료", flush=True)
            regions.append(build_open_meteo_entry(spec, item_payload, metadata_by_name, url))

    regions.sort(key=sort_regions)
    for index, region in enumerate(regions, start=1):
        region["id"] = f"region-{index:02d}"

    sources = [
        {
            "type": "open-meteo",
            "label": "Open-Meteo Historical Weather API",
            "url": OPEN_METEO_DOCS_URL,
        },
        {
            "type": "open-meteo",
            "label": "Open-Meteo Geocoding API",
            "url": "https://open-meteo.com/en/docs/geocoding-api",
        },
        {
            "type": "natural-earth",
            "label": "Natural Earth Downloads",
            "url": "https://www.naturalearthdata.com/downloads/",
        },
    ]

    source_breakdown = summarize_sources(regions)
    dataset["regions"] = regions
    dataset["sources"] = sources
    dataset["summary"] = {
        "regionCount": len(regions),
        "sourceBreakdown": source_breakdown,
        "supplementedByWmo": source_breakdown.get("wmo", 0),
        "supplementedByOpenMeteo": source_breakdown.get("open-meteo", 0),
    }

    json_payload = json.dumps(dataset, ensure_ascii=False, indent=2)
    OUTPUT_JSON_PATH.write_text(json_payload, encoding="utf-8")
    OUTPUT_JS_PATH.write_text(
        f"window.CLIMATE_DATA = {json.dumps(dataset, ensure_ascii=False)};\n",
        encoding="utf-8",
    )

    print(f"Wrote {len(regions)} total regions")
    print(f"Source breakdown: {source_breakdown}")


if __name__ == "__main__":
    main()
