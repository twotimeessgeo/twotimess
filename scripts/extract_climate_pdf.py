#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from pypdf import PdfReader


MONTHS = [
    "1월",
    "2월",
    "3월",
    "4월",
    "5월",
    "6월",
    "7월",
    "8월",
    "9월",
    "10월",
    "11월",
    "12월",
]
CONTINENTS = ["아프리카", "아메리카", "오세아니아", "유라시아"]
NUMBER_PATTERN = re.compile(r"-?\d+(?:\.\d+)?")
ANSWER_PATTERN = re.compile(r"\(([가-힣])\)\s*=\s*([^,(]+?)\s*\(([^)]+)\)")
PLACEHOLDER_PATTERN = re.compile(r"\([가-힣]\)")
CLIMATE_CODE_PATTERN = re.compile(r"\([^=][^)]+\)")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract monthly climate tables from the provided PDF."
    )
    parser.add_argument("pdf_path", type=Path, help="Path to the climate PDF.")
    parser.add_argument("output_path", type=Path, help="Path to the JSON output file.")
    return parser.parse_args()


def parse_numbers(line: str, prefix: str) -> list[float] | None:
    if prefix not in line:
        return None

    numbers = NUMBER_PATTERN.findall(line.split(prefix, 1)[1])
    if len(numbers) < 12:
        return None

    return [float(value) for value in numbers[:12]]


def build_answer_maps(reader: PdfReader) -> dict[str, dict[str, dict[str, str]]]:
    answer_maps: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    current_section: str | None = None

    for page in reader.pages:
        lines = [line.strip() for line in (page.extract_text() or "").splitlines() if line.strip()]
        for line in lines:
            if line in CONTINENTS:
                current_section = line

        compact_text = " ".join(lines)
        for label, name, code in ANSWER_PATTERN.findall(compact_text):
            answer_maps[current_section][f"({label})"] = {
                "name": name.strip(),
                "code": code.strip(),
            }

    return answer_maps


def build_entries(reader: PdfReader, pdf_filename: str) -> list[dict[str, object]]:
    answer_maps = build_answer_maps(reader)
    current_section: str | None = None
    entries: list[dict[str, object]] = []

    for page_number, page in enumerate(reader.pages, start=1):
        lines = [line.strip() for line in (page.extract_text() or "").splitlines() if line.strip()]

        for line in lines:
            if line in CONTINENTS:
                current_section = line

        index = 0
        while index < len(lines):
            line = lines[index]
            raw_name: str | None = None
            climate_code: str | None = None
            offset: int | None = None

            if PLACEHOLDER_PATTERN.fullmatch(line):
                if index + 1 < len(lines) and lines[index + 1].startswith("1월"):
                    raw_name = line
                    offset = 1
            elif (
                index + 2 < len(lines)
                and CLIMATE_CODE_PATTERN.fullmatch(lines[index + 1])
                and lines[index + 2].startswith("1월")
            ):
                raw_name = line
                climate_code = lines[index + 1][1:-1].strip()
                offset = 2

            if raw_name is None or offset is None:
                index += 1
                continue

            monthly_temperature: list[float] | None = None
            monthly_precipitation: list[float] | None = None
            scan_index = index + offset + 1

            while scan_index < len(lines):
                if monthly_temperature is None and lines[scan_index].startswith("월평균 기온"):
                    monthly_temperature = parse_numbers(lines[scan_index], "월평균 기온")
                if monthly_precipitation is None and lines[scan_index].startswith("월 강수량"):
                    monthly_precipitation = parse_numbers(lines[scan_index], "월 강수량")
                if monthly_temperature is not None and monthly_precipitation is not None:
                    break
                scan_index += 1

            if monthly_temperature is None or monthly_precipitation is None:
                raise ValueError(
                    f"Failed to extract monthly values from page {page_number} entry {raw_name}"
                )

            answer_info = answer_maps[current_section].get(raw_name, {})
            resolved_name = answer_info.get("name", raw_name)
            resolved_code = answer_info.get("code", climate_code or "")

            entries.append(
                {
                    "id": f"region-{len(entries) + 1:02d}",
                    "name": resolved_name,
                    "continent": current_section,
                    "climateCode": resolved_code,
                    "months": MONTHS,
                    "monthlyTemperatureC": monthly_temperature,
                    "monthlyPrecipitationMm": monthly_precipitation,
                    "annualMeanTemperatureC": round(
                        sum(monthly_temperature) / len(monthly_temperature), 1
                    ),
                    "annualPrecipitationMm": round(sum(monthly_precipitation), 1),
                    "source": {
                        "type": "pdf",
                        "file": pdf_filename,
                        "page": page_number,
                    },
                }
            )

            index = scan_index

    return entries


def main() -> None:
    args = parse_arguments()
    reader = PdfReader(str(args.pdf_path))
    entries = build_entries(reader, args.pdf_path.name)
    payload = {
        "title": "세계 주요 지역 기후 통계",
        "months": MONTHS,
        "regions": entries,
        "sources": [
            {
                "type": "pdf",
                "label": "기후 통계 PDF",
                "file": args.pdf_path.name,
            }
        ],
    }

    json_payload = json.dumps(payload, ensure_ascii=False, indent=2)
    args.output_path.write_text(json_payload, encoding="utf-8")

    js_output_path = args.output_path.with_suffix(".js")
    js_output_path.write_text(
        f"window.CLIMATE_DATA = {json.dumps(payload, ensure_ascii=False)};\n",
        encoding="utf-8",
    )

    print(f"Wrote {len(entries)} regions to {args.output_path}")
    print(f"Wrote data bundle to {js_output_path}")


if __name__ == "__main__":
    main()
