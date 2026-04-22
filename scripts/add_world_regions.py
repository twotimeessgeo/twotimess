#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


DATASET_PATH = Path("data/climate-data.json")
BUNDLE_PATH = Path("data/climate-data.js")
CACHE_DIR = Path("data/.open-meteo-cache")
OPEN_METEO_DOCS_URL = "https://open-meteo.com/en/docs/historical-weather-api"
MONTHS = [f"{index}월" for index in range(1, 13)]
BATCH_SIZE = 5

CANDIDATES = [
    {
        "name": "멜버른",
        "englishName": "Melbourne",
        "continent": "오세아니아",
        "country": "Australia",
        "countryCode": "AU",
        "latitude": -37.8140,
        "longitude": 144.9633,
        "elevationM": 25,
        "timezone": "Australia/Melbourne",
        "aliases": ["Melbourne"],
    },
    {
        "name": "브리즈번",
        "englishName": "Brisbane",
        "continent": "오세아니아",
        "country": "Australia",
        "countryCode": "AU",
        "latitude": -27.4679,
        "longitude": 153.0281,
        "elevationM": 27,
        "timezone": "Australia/Brisbane",
        "aliases": ["Brisbane"],
    },
    {
        "name": "앨리스스프링스",
        "englishName": "Alice Springs",
        "continent": "오세아니아",
        "country": "Australia",
        "countryCode": "AU",
        "latitude": -23.6975,
        "longitude": 133.8836,
        "elevationM": 583,
        "timezone": "Australia/Darwin",
        "aliases": ["Alice Springs"],
    },
    {
        "name": "크라이스트처치",
        "englishName": "Christchurch",
        "continent": "오세아니아",
        "country": "New Zealand",
        "countryCode": "NZ",
        "latitude": -43.5333,
        "longitude": 172.6333,
        "elevationM": 14,
        "timezone": "Pacific/Auckland",
        "aliases": ["Christchurch"],
    },
    {
        "name": "맥머도",
        "englishName": "McMurdo Station",
        "continent": "오세아니아",
        "country": "Antarctica",
        "countryCode": "AQ",
        "latitude": -77.8419,
        "longitude": 166.6863,
        "elevationM": 24,
        "timezone": "Antarctica/McMurdo",
        "aliases": ["McMurdo", "McMurdo Station"],
    },
    {
        "name": "웰링턴",
        "englishName": "Wellington",
        "continent": "오세아니아",
        "country": "New Zealand",
        "countryCode": "NZ",
        "latitude": -41.2866,
        "longitude": 174.7756,
        "elevationM": 31,
        "timezone": "Pacific/Auckland",
        "aliases": ["Wellington"],
    },
    {
        "name": "호바트",
        "englishName": "Hobart",
        "continent": "오세아니아",
        "country": "Australia",
        "countryCode": "AU",
        "latitude": -42.8794,
        "longitude": 147.3294,
        "elevationM": 19,
        "timezone": "Australia/Hobart",
        "aliases": ["Hobart"],
    },
    {
        "name": "누메아",
        "englishName": "Noumea",
        "continent": "오세아니아",
        "country": "New Caledonia",
        "countryCode": "NC",
        "latitude": -22.2741,
        "longitude": 166.4488,
        "elevationM": 26,
        "timezone": "Pacific/Noumea",
        "aliases": ["Noumea", "Nouméa"],
    },
    {
        "name": "수바",
        "englishName": "Suva",
        "continent": "오세아니아",
        "country": "Fiji",
        "countryCode": "FJ",
        "latitude": -18.1368,
        "longitude": 178.4253,
        "elevationM": 5,
        "timezone": "Pacific/Fiji",
        "aliases": ["Suva"],
    },
    {
        "name": "라고스",
        "englishName": "Lagos",
        "continent": "아프리카",
        "country": "Nigeria",
        "countryCode": "NG",
        "latitude": 6.4541,
        "longitude": 3.3947,
        "elevationM": 11,
        "timezone": "Africa/Lagos",
        "aliases": ["Lagos"],
    },
    {
        "name": "아크라",
        "englishName": "Accra",
        "continent": "아프리카",
        "country": "Ghana",
        "countryCode": "GH",
        "latitude": 5.5560,
        "longitude": -0.1969,
        "elevationM": 33,
        "timezone": "Africa/Accra",
        "aliases": ["Accra"],
    },
    {
        "name": "다카르",
        "englishName": "Dakar",
        "continent": "아프리카",
        "country": "Senegal",
        "countryCode": "SN",
        "latitude": 14.6937,
        "longitude": -17.4441,
        "elevationM": 12,
        "timezone": "Africa/Dakar",
        "aliases": ["Dakar"],
    },
    {
        "name": "알제",
        "englishName": "Algiers",
        "continent": "아프리카",
        "country": "Algeria",
        "countryCode": "DZ",
        "latitude": 36.7323,
        "longitude": 3.0875,
        "elevationM": 113,
        "timezone": "Africa/Algiers",
        "aliases": ["Algiers", "Alger"],
    },
    {
        "name": "카사블랑카",
        "englishName": "Casablanca",
        "continent": "아프리카",
        "country": "Morocco",
        "countryCode": "MA",
        "latitude": 33.5731,
        "longitude": -7.5898,
        "elevationM": 27,
        "timezone": "Africa/Casablanca",
        "aliases": ["Casablanca"],
    },
    {
        "name": "요하네스버그",
        "englishName": "Johannesburg",
        "continent": "아프리카",
        "country": "South Africa",
        "countryCode": "ZA",
        "latitude": -26.2023,
        "longitude": 28.0436,
        "elevationM": 1767,
        "timezone": "Africa/Johannesburg",
        "aliases": ["Johannesburg"],
    },
    {
        "name": "나이로비",
        "englishName": "Nairobi",
        "continent": "아프리카",
        "country": "Kenya",
        "countryCode": "KE",
        "latitude": -1.2833,
        "longitude": 36.8167,
        "elevationM": 1684,
        "timezone": "Africa/Nairobi",
        "aliases": ["Nairobi"],
    },
    {
        "name": "모가디슈",
        "englishName": "Mogadishu",
        "continent": "아프리카",
        "country": "Somalia",
        "countryCode": "SO",
        "latitude": 2.0371,
        "longitude": 45.3438,
        "elevationM": 12,
        "timezone": "Africa/Mogadishu",
        "aliases": ["Mogadishu"],
    },
    {
        "name": "마이애미",
        "englishName": "Miami",
        "continent": "아메리카",
        "country": "United States of America",
        "countryCode": "US",
        "latitude": 25.7743,
        "longitude": -80.1937,
        "elevationM": 2,
        "timezone": "America/New_York",
        "aliases": ["Miami"],
    },
    {
        "name": "하바나",
        "englishName": "Havana",
        "continent": "아메리카",
        "country": "Cuba",
        "countryCode": "CU",
        "latitude": 23.1330,
        "longitude": -82.3830,
        "elevationM": 41,
        "timezone": "America/Havana",
        "aliases": ["Havana", "La Habana"],
    },
    {
        "name": "뉴올리언스",
        "englishName": "New Orleans",
        "continent": "아메리카",
        "country": "United States of America",
        "countryCode": "US",
        "latitude": 29.9546,
        "longitude": -90.0751,
        "elevationM": 2,
        "timezone": "America/Chicago",
        "aliases": ["New Orleans"],
    },
    {
        "name": "페어뱅크스",
        "englishName": "Fairbanks",
        "continent": "아메리카",
        "country": "United States of America",
        "countryCode": "US",
        "latitude": 64.8378,
        "longitude": -147.7164,
        "elevationM": 136,
        "timezone": "America/Anchorage",
        "aliases": ["Fairbanks"],
    },
    {
        "name": "파나마시티",
        "englishName": "Panama City",
        "continent": "아메리카",
        "country": "Panama",
        "countryCode": "PA",
        "latitude": 8.9936,
        "longitude": -79.5197,
        "elevationM": 17,
        "timezone": "America/Panama",
        "aliases": ["Panama City"],
    },
    {
        "name": "리우데자네이루",
        "englishName": "Rio de Janeiro",
        "continent": "아메리카",
        "country": "Brazil",
        "countryCode": "BR",
        "latitude": -22.9064,
        "longitude": -43.1822,
        "elevationM": 12,
        "timezone": "America/Sao_Paulo",
        "aliases": ["Rio de Janeiro", "Rio"],
    },
    {
        "name": "핼리팩스",
        "englishName": "Halifax",
        "continent": "아메리카",
        "country": "Canada",
        "countryCode": "CA",
        "latitude": 44.6427,
        "longitude": -63.5769,
        "elevationM": 60,
        "timezone": "America/Halifax",
        "aliases": ["Halifax"],
    },
    {
        "name": "헬싱키",
        "englishName": "Helsinki",
        "continent": "유라시아",
        "country": "Finland",
        "countryCode": "FI",
        "latitude": 60.1695,
        "longitude": 24.9354,
        "elevationM": 26,
        "timezone": "Europe/Helsinki",
        "aliases": ["Helsinki", "Helsingfors"],
    },
    {
        "name": "스톡홀름",
        "englishName": "Stockholm",
        "continent": "유라시아",
        "country": "Sweden",
        "countryCode": "SE",
        "latitude": 59.3294,
        "longitude": 18.0687,
        "elevationM": 17,
        "timezone": "Europe/Stockholm",
        "aliases": ["Stockholm"],
    },
    {
        "name": "베를린",
        "englishName": "Berlin",
        "continent": "유라시아",
        "country": "Germany",
        "countryCode": "DE",
        "latitude": 52.5244,
        "longitude": 13.4105,
        "elevationM": 74,
        "timezone": "Europe/Berlin",
        "aliases": ["Berlin"],
    },
    {
        "name": "빈",
        "englishName": "Vienna",
        "continent": "유라시아",
        "country": "Austria",
        "countryCode": "AT",
        "latitude": 48.2085,
        "longitude": 16.3721,
        "elevationM": 171,
        "timezone": "Europe/Vienna",
        "aliases": ["Vienna", "Wien"],
    },
    {
        "name": "마닐라",
        "englishName": "Manila",
        "continent": "유라시아",
        "country": "Philippines",
        "countryCode": "PH",
        "latitude": 14.6042,
        "longitude": 120.9822,
        "elevationM": 13,
        "timezone": "Asia/Manila",
        "aliases": ["Manila"],
    },
    {
        "name": "방콕",
        "englishName": "Bangkok",
        "continent": "유라시아",
        "country": "Thailand",
        "countryCode": "TH",
        "latitude": 13.7540,
        "longitude": 100.5014,
        "elevationM": 12,
        "timezone": "Asia/Bangkok",
        "aliases": ["Bangkok", "Krung Thep"],
    },
    {
        "name": "쿠알라룸푸르",
        "englishName": "Kuala Lumpur",
        "continent": "유라시아",
        "country": "Malaysia",
        "countryCode": "MY",
        "latitude": 3.1412,
        "longitude": 101.6865,
        "elevationM": 56,
        "timezone": "Asia/Kuala_Lumpur",
        "aliases": ["Kuala Lumpur"],
    },
    {
        "name": "타슈켄트",
        "englishName": "Tashkent",
        "continent": "유라시아",
        "country": "Uzbekistan",
        "countryCode": "UZ",
        "latitude": 41.2646,
        "longitude": 69.2163,
        "elevationM": 424,
        "timezone": "Asia/Tashkent",
        "aliases": ["Tashkent"],
    },
    {
        "name": "노보시비르스크",
        "englishName": "Novosibirsk",
        "continent": "유라시아",
        "country": "Russian Federation",
        "countryCode": "RU",
        "latitude": 55.0344,
        "longitude": 82.9434,
        "elevationM": 143,
        "timezone": "Asia/Novosibirsk",
        "aliases": ["Novosibirsk"],
    },
    {
        "name": "오사카",
        "englishName": "Osaka",
        "continent": "유라시아",
        "country": "Japan",
        "countryCode": "JP",
        "latitude": 34.6938,
        "longitude": 135.5011,
        "elevationM": 4,
        "timezone": "Asia/Tokyo",
        "aliases": ["Osaka"],
    },
]


def round1(value: float) -> float:
    return round(float(value) + 1e-9, 1)


def average(values: list[float]) -> float:
    return round1(sum(values) / len(values))


def chunked(items: list[dict], size: int) -> list[list[dict]]:
    return [items[index:index + size] for index in range(0, len(items), size)]


def sha1(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def fetch_json(url: str) -> dict | list:
    cache_path = CACHE_DIR / f"{sha1(url)}.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ClimateAtlasStudio/1.0 (+https://open-meteo.com/)",
            "Accept": "application/json",
        },
    )
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    for attempt in range(8):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                payload = json.loads(response.read().decode("utf-8"))
                cache_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
                time.sleep(0.8)
                return payload
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == 7:
                raise
            retry_after = error.headers.get("Retry-After") if error.headers else None
            try:
                wait_seconds = max(10, int(retry_after)) if retry_after else min(90, 15 * (attempt + 1))
            except (TypeError, ValueError):
                wait_seconds = min(90, 15 * (attempt + 1))
            print(f"429 received -> retry in {wait_seconds}s", flush=True)
            time.sleep(wait_seconds)

    raise RuntimeError(f"Failed to fetch JSON after retries: {url}")


def build_archive_url(specs: list[dict]) -> str:
    query = urllib.parse.urlencode(
        {
            "latitude": ",".join(f"{spec['latitude']:.4f}" for spec in specs),
            "longitude": ",".join(f"{spec['longitude']:.4f}" for spec in specs),
            "elevation": ",".join(str(spec["elevationM"]) for spec in specs),
            "start_date": "1991-01-01",
            "end_date": "2020-12-31",
            "daily": "temperature_2m_mean,precipitation_sum",
            "timezone": ",".join("auto" for _ in specs),
            "models": "era5",
            "cell_selection": "land",
        }
    )
    return f"https://archive-api.open-meteo.com/v1/archive?{query}"


def build_monthly_normals(
    time_values: list[str],
    temperature_values: list[float],
    precipitation_values: list[float],
) -> tuple[list[float], list[float]]:
    by_month = [
        {"temperatureSum": 0.0, "temperatureCount": 0, "precipitationSum": 0.0, "monthCount": 0}
        for _ in range(12)
    ]
    by_year_month: dict[str, dict] = {}

    for time_value, temperature_value, precipitation_value in zip(
        time_values,
        temperature_values,
        precipitation_values,
    ):
        month_index = int(time_value[5:7]) - 1
        year_month_key = time_value[:7]
        if year_month_key not in by_year_month:
            by_year_month[year_month_key] = {
                "monthIndex": month_index,
                "temperatureSum": 0.0,
                "temperatureCount": 0,
                "precipitationTotal": 0.0,
            }
        bucket = by_year_month[year_month_key]
        if temperature_value not in (None, ""):
            bucket["temperatureSum"] += float(temperature_value)
            bucket["temperatureCount"] += 1
        if precipitation_value not in (None, ""):
            bucket["precipitationTotal"] += float(precipitation_value)

    for bucket in by_year_month.values():
        month_bucket = by_month[bucket["monthIndex"]]
        if bucket["temperatureCount"] > 0:
            month_bucket["temperatureSum"] += bucket["temperatureSum"] / bucket["temperatureCount"]
            month_bucket["temperatureCount"] += 1
        month_bucket["precipitationSum"] += bucket["precipitationTotal"]
        month_bucket["monthCount"] += 1

    monthly_temperature = [
        round1(bucket["temperatureSum"] / bucket["temperatureCount"])
        for bucket in by_month
    ]
    monthly_precipitation = [
        round1(bucket["precipitationSum"] / bucket["monthCount"])
        for bucket in by_month
    ]
    return monthly_temperature, monthly_precipitation


def sum_month_values(values: list[float], month_indexes: list[int]) -> float:
    return sum(values[index] for index in month_indexes)


def classify_climate_group(
    monthly_temperature: list[float],
    monthly_precipitation: list[float],
    latitude: float,
    elevation_m: float | None,
) -> str:
    annual_mean_temperature = average(monthly_temperature)
    annual_precipitation = sum(monthly_precipitation)
    coldest_month = min(monthly_temperature)
    warmest_month = max(monthly_temperature)
    driest_month = min(monthly_precipitation)

    if isinstance(elevation_m, (int, float)) and elevation_m >= 1500 and 0 < annual_mean_temperature < 18:
        return "H"
    if warmest_month < 0:
        return "EF"
    if warmest_month < 10:
        return "ET"

    is_northern_hemisphere = latitude >= 0
    summer_months = [3, 4, 5, 6, 7, 8] if is_northern_hemisphere else [9, 10, 11, 0, 1, 2]
    winter_months = [9, 10, 11, 0, 1, 2] if is_northern_hemisphere else [3, 4, 5, 6, 7, 8]
    summer_precipitation = sum_month_values(monthly_precipitation, summer_months)
    summer_precipitation_ratio = summer_precipitation / annual_precipitation if annual_precipitation > 0 else 0
    dryness_threshold = 20 * annual_mean_temperature

    if summer_precipitation_ratio >= 0.7:
        dryness_threshold += 280
    elif summer_precipitation_ratio >= 0.3:
        dryness_threshold += 140

    if annual_precipitation < dryness_threshold:
        return "Bw" if annual_precipitation < dryness_threshold / 2 else "BS"

    if coldest_month >= 18:
        if driest_month >= 60:
            return "Af"
        if driest_month >= 100 - annual_precipitation / 25:
            return "Am"
        return "Aw"

    summer_dryness = min(monthly_precipitation[index] for index in summer_months)
    winter_wettest = max(monthly_precipitation[index] for index in winter_months)
    winter_dryness = min(monthly_precipitation[index] for index in winter_months)
    summer_wettest = max(monthly_precipitation[index] for index in summer_months)
    has_dry_summer = summer_dryness < 40 and summer_dryness < winter_wettest / 3
    has_dry_winter = winter_dryness < summer_wettest / 10
    warm_months = sum(1 for value in monthly_temperature if value >= 10)

    if coldest_month > 0:
        if has_dry_summer:
            return "Cs"
        if has_dry_winter:
            return "Cw"
        return "Cfa" if warmest_month >= 22 and warm_months >= 4 else "Cfb"

    return "Dw" if has_dry_winter else "Df"


def dedupe_aliases(*values: str) -> list[str]:
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


def build_entry(spec: dict, payload: dict, api_url: str) -> dict:
    daily = payload["daily"]
    monthly_temperature, monthly_precipitation = build_monthly_normals(
        daily["time"],
        daily["temperature_2m_mean"],
        daily["precipitation_sum"],
    )
    climate_group = classify_climate_group(
        monthly_temperature,
        monthly_precipitation,
        spec["latitude"],
        spec["elevationM"],
    )
    return {
        "name": spec["name"],
        "englishName": spec["englishName"],
        "aliases": dedupe_aliases(spec["name"], spec["englishName"], *(spec.get("aliases") or [])),
        "continent": spec["continent"],
        "country": spec["country"],
        "countryCode": spec["countryCode"],
        "timezone": spec["timezone"],
        "elevationM": spec["elevationM"],
        "climateCode": climate_group,
        "climateGroup": climate_group,
        "months": MONTHS,
        "monthlyTemperatureC": monthly_temperature,
        "monthlyPrecipitationMm": monthly_precipitation,
        "annualMeanTemperatureC": average(monthly_temperature),
        "annualPrecipitationMm": round1(sum(monthly_precipitation)),
        "coordinates": {
            "latitude": round(spec["latitude"], 4),
            "longitude": round(spec["longitude"], 4),
        },
        "source": {
            "type": "open-meteo",
            "label": "Open-Meteo Historical Weather API",
            "url": OPEN_METEO_DOCS_URL,
            "apiUrl": api_url,
            "model": "ERA5",
            "period": "1991-2020",
            "note": "추가 지역 통계를 Open-Meteo Historical Weather API(ERA5) 1991-2020 일별 자료로 계산했습니다.",
        },
        "hemisphere": "북반구" if spec["latitude"] >= 0 else "남반구",
    }


def update_summary(dataset: dict) -> None:
    source_breakdown = {"pdf": 0, "wmo": 0, "open-meteo": 0}
    for region in dataset["regions"]:
        source_type = region.get("source", {}).get("type", "pdf")
        source_breakdown[source_type] = source_breakdown.get(source_type, 0) + 1

    dataset["summary"] = {
        "regionCount": len(dataset["regions"]),
        "sourceBreakdown": source_breakdown,
        "supplementedByWmo": source_breakdown.get("wmo", 0),
        "supplementedByOpenMeteo": source_breakdown.get("open-meteo", 0),
    }


def main() -> None:
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    existing_names = {region["name"] for region in dataset["regions"]}
    missing_specs = [spec for spec in CANDIDATES if spec["name"] not in existing_names]

    if not missing_specs:
        print("No new world regions to add.")
        return

    next_region_index = len(dataset["regions"]) + 1
    new_entries: list[dict] = []
    unresolved_specs: list[dict] = []

    for batch_number, batch_specs in enumerate(chunked(missing_specs, BATCH_SIZE), start=1):
        batch_label = ", ".join(spec["name"] for spec in batch_specs)
        print(f"[batch {batch_number}] {batch_label}", flush=True)
        batch_url = build_archive_url(batch_specs)
        try:
            payload = fetch_json(batch_url)
        except Exception as error:
            unresolved_specs.extend(batch_specs)
            print(f"  -> batch failed: {error}", flush=True)
            break
        payloads = payload if isinstance(payload, list) else [payload]
        if len(payloads) != len(batch_specs):
            raise RuntimeError(
                f"Open-Meteo batch size mismatch: requested {len(batch_specs)} locations, got {len(payloads)} payloads"
            )

        for spec, item_payload in zip(batch_specs, payloads):
            entry = build_entry(spec, item_payload, batch_url)
            entry["id"] = f"region-{next_region_index:02d}"
            next_region_index += 1
            print(
                f"  -> {entry['name']}: {entry['climateGroup']} / {entry['annualMeanTemperatureC']}℃ / {entry['annualPrecipitationMm']}mm",
                flush=True,
            )
            new_entries.append(entry)

    if not new_entries:
        unresolved_names = ", ".join(spec["name"] for spec in unresolved_specs) if unresolved_specs else ""
        raise RuntimeError(f"No regions were added. unresolved={unresolved_names}")

    dataset["regions"].extend(new_entries)
    update_summary(dataset)
    DATASET_PATH.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")
    BUNDLE_PATH.write_text(
        f"window.CLIMATE_DATA = {json.dumps(dataset, ensure_ascii=False)};\n",
        encoding="utf-8",
    )

    print(f"Added {len(new_entries)} world regions")
    print(f"Total world regions: {len(dataset['regions'])}")
    if unresolved_specs:
        print("Unresolved regions:", ", ".join(spec["name"] for spec in unresolved_specs))


if __name__ == "__main__":
    main()
