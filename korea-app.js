const KOREA_MAP_BOUNDS = {
  minLongitude: 123.2,
  minLatitude: 32.0,
  maxLongitude: 131.8,
  maxLatitude: 43.6,
};

const collator = new Intl.Collator("ko-KR", { numeric: true, sensitivity: "base" });
const coordinateFormatter = new Intl.NumberFormat("ko-KR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const state = {
  dataset: window.KOREA_CLIMATE_DATA ?? null,
  regions: [],
  search: "",
  nation: "전체",
  zone: "전체",
  mapScope: "all",
  selectedIds: new Set(),
};

const elements = {
  heroCount: document.querySelector("#heroCount"),
  heroCaption: document.querySelector("#heroCaption"),
  selectionSummary: document.querySelector("#selectionSummary"),
  searchInput: document.querySelector("#searchInput"),
  clearSelectionButton: document.querySelector("#clearSelectionButton"),
  nationChips: document.querySelector("#nationChips"),
  zoneChips: document.querySelector("#zoneChips"),
  regionList: document.querySelector("#regionList"),
  worldMap: document.querySelector("#worldMap"),
  mapSummary: document.querySelector("#mapSummary"),
  mapScopeChips: document.querySelector("#mapScopeChips"),
  selectedRegionsContent: document.querySelector("#selectedRegionsContent"),
  comparisonContent: document.querySelector("#comparisonContent"),
};

document.addEventListener("DOMContentLoaded", () => {
  void init();
});

async function init() {
  if (!state.dataset) {
    const response = await fetch("./data/korea-climate-data.json");
    state.dataset = await response.json();
  }

  state.regions = [...state.dataset.regions].sort(sortRegions);
  applyDefaultSelection();
  bindEvents();
  render();
}

function bindEvents() {
  elements.searchInput?.addEventListener("input", (event) => {
    state.search = event.target.value ?? "";
    render();
  });

  elements.clearSelectionButton?.addEventListener("click", () => {
    state.selectedIds.clear();
    render();
  });

  elements.nationChips?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-nation]");
    if (!button) {
      return;
    }
    state.nation = button.dataset.nation;
    render();
  });

  elements.zoneChips?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-zone]");
    if (!button) {
      return;
    }
    state.zone = button.dataset.zone;
    render();
  });

  elements.mapScopeChips?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-map-scope]");
    if (!button) {
      return;
    }
    state.mapScope = button.dataset.mapScope;
    render();
  });

  elements.regionList?.addEventListener("change", (event) => {
    const checkbox = event.target.closest("[data-region-checkbox]");
    if (!checkbox) {
      return;
    }
    toggleSelection(checkbox.dataset.regionCheckbox);
  });

  elements.regionList?.addEventListener("click", (event) => {
    const option = event.target.closest("[data-region-option]");
    if (!option || event.target.matches("input")) {
      return;
    }
    toggleSelection(option.dataset.regionOption);
  });

  elements.worldMap?.addEventListener("click", (event) => {
    const marker = event.target.closest("[data-map-region-id]");
    if (!marker) {
      return;
    }
    toggleSelection(marker.dataset.mapRegionId);
  });
}

function applyDefaultSelection() {
  const defaults = state.dataset.defaultSampleNames ?? [];
  state.selectedIds = new Set(
    state.regions.filter((region) => defaults.includes(region.name)).map((region) => region.id)
  );
}

function toggleSelection(regionId) {
  if (state.selectedIds.has(regionId)) {
    state.selectedIds.delete(regionId);
  } else {
    state.selectedIds.add(regionId);
  }
  render();
}

function render() {
  const visibleRegions = getVisibleRegions();
  const selectedRegions = getSelectedRegions();

  if (elements.heroCount) {
    elements.heroCount.textContent = `${state.dataset.summary.regionCount}개 지역`;
  }
  if (elements.heroCaption) {
    elements.heroCaption.textContent = `${state.dataset.summary.sourceLabel} ${state.dataset.summary.period} 기준`;
  }
  if (elements.selectionSummary) {
    elements.selectionSummary.textContent = `${selectedRegions.length}개 선택됨`;
  }
  if (elements.mapSummary) {
    const mapRegions = getMapRegions(visibleRegions, selectedRegions);
    elements.mapSummary.textContent =
      state.mapScope === "selected"
        ? `선택 지역 ${mapRegions.length}개 표시`
        : `필터 결과 ${mapRegions.length}개 표시`;
  }

  elements.nationChips.innerHTML = renderNationChips();
  elements.zoneChips.innerHTML = renderZoneChips();
  elements.mapScopeChips.innerHTML = renderMapScopeChips();
  elements.regionList.innerHTML = renderRegionList(visibleRegions);
  elements.selectedRegionsContent.innerHTML = renderSelectedRegions(selectedRegions);
  elements.comparisonContent.innerHTML = renderComparison(selectedRegions);
  renderMap(visibleRegions, selectedRegions);
}

function getVisibleRegions() {
  const query = normalizeText(state.search);

  return state.regions.filter((region) => {
    const matchesNation = state.nation === "전체" || region.nation === state.nation;
    const matchesZone = state.zone === "전체" || region.zone === state.zone;
    const matchesSearch =
      !query ||
      [
        region.name,
        region.officialName,
        region.nation,
        region.zone,
        String(region.stationId),
        ...(region.aliases ?? []),
      ]
        .filter(Boolean)
        .some((value) => normalizeText(value).includes(query));

    return matchesNation && matchesZone && matchesSearch;
  });
}

function getSelectedRegions() {
  return state.regions.filter((region) => state.selectedIds.has(region.id));
}

function getMapRegions(visibleRegions, selectedRegions) {
  return state.mapScope === "selected" ? selectedRegions : visibleRegions;
}

function renderNationChips() {
  return state.dataset.nationOrder
    .map((nation) => {
      const count =
        nation === "전체"
          ? state.regions.length
          : state.regions.filter((region) => region.nation === nation).length;
      return `
        <button
          type="button"
          class="chip-button ${state.nation === nation ? "is-active" : ""}"
          data-nation="${escapeHtml(nation)}"
        >
          ${escapeHtml(nation)} (${count})
        </button>
      `;
    })
    .join("");
}

function renderZoneChips() {
  return state.dataset.zoneOrder
    .map((zone) => {
      const count =
        zone === "전체"
          ? state.regions.length
          : state.regions.filter((region) => region.zone === zone).length;
      return `
        <button
          type="button"
          class="chip-button ${state.zone === zone ? "is-active" : ""}"
          data-zone="${escapeHtml(zone)}"
        >
          ${escapeHtml(zone)} (${count})
        </button>
      `;
    })
    .join("");
}

function renderMapScopeChips() {
  const items = [
    { id: "all", label: "필터 결과" },
    { id: "selected", label: "선택 지역만" },
  ];
  return items
    .map(
      (item) => `
        <button
          type="button"
          class="chip-button ${state.mapScope === item.id ? "is-active" : ""}"
          data-map-scope="${item.id}"
        >
          ${item.label}
        </button>
      `
    )
    .join("");
}

function renderRegionList(regions) {
  if (!regions.length) {
    return renderEmptyState("조건에 맞는 지역이 없습니다.", "검색어 또는 필터를 조금 넓혀보세요.");
  }

  return regions
    .map((region) => {
      const checked = state.selectedIds.has(region.id);
      return `
        <label class="region-option ${checked ? "is-selected" : ""}" data-region-option="${region.id}">
          <div class="region-option-top">
            <div class="region-option-title">
              <strong>${escapeHtml(region.name)}</strong>
              <span>${escapeHtml(region.officialName)} · ${escapeHtml(region.nation)}</span>
            </div>
            <input
              type="checkbox"
              ${checked ? "checked" : ""}
              data-region-checkbox="${region.id}"
              aria-label="${escapeHtml(region.name)} 선택"
            />
          </div>
          <div class="region-option-meta">${escapeHtml(region.zone)} · 지점 ${region.stationId}</div>
          <div class="region-option-coordinates">${escapeHtml(formatCoordinatePair(region.coordinates))}</div>
        </label>
      `;
    })
    .join("");
}

function renderSelectedRegions(regions) {
  if (!regions.length) {
    return renderEmptyState(
      "지역을 선택해 주세요.",
      "지도나 목록에서 지역을 고르면 1월·8월과 겨울·여름 기준 표와 그래프가 나타납니다."
    );
  }

  return regions.map((region) => renderRegionCard(region)).join("");
}

function renderRegionCard(region) {
  const periodMetrics = state.dataset.comparisonPeriods.map((period) => getPeriodMetrics(region, period));

  return `
    <article class="region-card">
      <div class="region-card-body">
        <div class="region-card-header">
          <div>
            <p class="section-kicker">지점 ${region.stationId}</p>
            <h3>${escapeHtml(region.name)}</h3>
          </div>
          <div class="selection-summary is-muted">${escapeHtml(region.nation)} · ${escapeHtml(region.zone)}</div>
        </div>
        <div class="region-meta">
          <span class="meta-pill">${escapeHtml(region.officialName)}</span>
          <span class="meta-pill">${escapeHtml(formatCoordinatePair(region.coordinates))}</span>
          <span class="meta-pill">해발 ${formatMeters(region.elevationM)}</span>
        </div>
        <div class="stats-row">
          <span class="stat-pill">연평균 ${formatTemp(region.annualMeanTemperatureC)}</span>
          <span class="stat-pill">연강수 ${formatMm(region.annualPrecipitationMm)}</span>
          <span class="stat-pill">연간 일최저 &lt;0℃ ${formatDays(region.annualColdDaysBelowZero)}</span>
          <span class="stat-pill">연간 일최저 ≥25℃ ${formatDays(region.annualHotDaysAboveTwentyFiveMin)}</span>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>시기</th>
                <th>평균기온</th>
                <th>강수량</th>
                <th>일최저 &lt;0℃</th>
                <th>일최저 ≥25℃</th>
              </tr>
            </thead>
            <tbody>
              ${periodMetrics
                .map(
                  (metric) => `
                    <tr>
                      <td>${escapeHtml(metric.label)}</td>
                      <td>${formatTemp(metric.temperature)}</td>
                      <td>${formatMm(metric.precipitation)}</td>
                      <td>${formatDays(metric.coldDays)}</td>
                      <td>${formatDays(metric.hotDays)}</td>
                    </tr>
                  `
                )
                .join("")}
            </tbody>
          </table>
        </div>
      </div>
      <div class="region-card-chart">
        <div class="charts-grid">
          <div class="chart-card">
            <h4>시기별 평균기온</h4>
            ${renderPeriodTemperatureChart(periodMetrics)}
          </div>
          <div class="chart-card">
            <h4>시기별 강수량</h4>
            ${renderPeriodPrecipitationChart(periodMetrics)}
          </div>
        </div>
      </div>
    </article>
  `;
}

function renderComparison(regions) {
  if (regions.length < 2) {
    return renderEmptyState(
      "두 지역 이상 선택해 주세요.",
      "여러 지역을 함께 고르면 1월·8월, 겨울·여름의 기온과 강수량 편차를 비교할 수 있습니다."
    );
  }

  const symbols = regions.map((region, index) => ({
    symbol: createSymbol(index),
    region,
  }));

  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>기호</th>
            <th>지역</th>
            <th>1월 기온</th>
            <th>1월 강수</th>
            <th>8월 기온</th>
            <th>8월 강수</th>
            <th>겨울 기온</th>
            <th>겨울 강수</th>
            <th>여름 기온</th>
            <th>여름 강수</th>
          </tr>
        </thead>
        <tbody>
          ${symbols
            .map(({ symbol, region }) => {
              const metrics = Object.fromEntries(
                state.dataset.comparisonPeriods.map((period) => [period.id, getPeriodMetrics(region, period)])
              );
              return `
                <tr>
                  <td>${symbol}</td>
                  <td>${escapeHtml(region.name)}</td>
                  <td>${formatTemp(metrics.jan.temperature)}</td>
                  <td>${formatMm(metrics.jan.precipitation)}</td>
                  <td>${formatTemp(metrics.aug.temperature)}</td>
                  <td>${formatMm(metrics.aug.precipitation)}</td>
                  <td>${formatTemp(metrics.winter.temperature)}</td>
                  <td>${formatMm(metrics.winter.precipitation)}</td>
                  <td>${formatTemp(metrics.summer.temperature)}</td>
                  <td>${formatMm(metrics.summer.precipitation)}</td>
                </tr>
              `;
            })
            .join("")}
        </tbody>
      </table>
    </div>
    <div class="legend-grid">
      ${symbols
        .map(
          ({ symbol, region }) => `
            <div class="legend-item"><strong>${symbol}</strong> ${escapeHtml(region.name)} · ${escapeHtml(region.nation)}</div>
          `
        )
        .join("")}
    </div>
    <div class="charts-grid">
      ${state.dataset.comparisonPeriods
        .map(
          (period) => `
            <div class="chart-card">
              <h4>${escapeHtml(period.label)} 기온 편차</h4>
              ${renderDeviationDotChart(symbols, period)}
            </div>
            <div class="chart-card">
              <h4>${escapeHtml(period.label)} 강수 편차</h4>
              ${renderDeviationBarChart(symbols, period)}
            </div>
          `
        )
        .join("")}
    </div>
  `;
}

function renderMap(visibleRegions, selectedRegions) {
  const d3 = window.d3;
  const topojson = window.topojson;
  const topology = window.WORLD_COUNTRIES_TOPOLOGY;

  if (!d3 || !topojson || !topology) {
    elements.worldMap.innerHTML = renderEmptyState(
      "지도를 불러오지 못했습니다.",
      "로컬 지도 데이터가 준비되지 않았습니다."
    );
    return;
  }

  const regions = getMapRegions(visibleRegions, selectedRegions).filter(
    (region) => typeof region.coordinates?.latitude === "number" && typeof region.coordinates?.longitude === "number"
  );

  const width = 1000;
  const height = 560;
  const countries = topojson.feature(topology, topology.objects.countries);
  const borders = topojson.mesh(topology, topology.objects.countries, (left, right) => left !== right);
  const projection = d3
    .geoMercator()
    .center([127.2, 38.2])
    .scale(5200)
    .translate([width / 2, height / 2])
    .clipExtent([
      [0, 0],
      [width, height],
    ]);
  const path = d3.geoPath(projection);

  const markers = regions
    .map((region) => {
      const projected = projection([region.coordinates.longitude, region.coordinates.latitude]);
      if (!projected) {
        return "";
      }
      const [x, y] = projected;
      return `
        <button
          type="button"
          class="map-marker ${state.selectedIds.has(region.id) ? "is-selected" : ""}"
          data-map-region-id="${region.id}"
          data-label="${escapeHtml(`${region.name} · ${region.nation}`)}"
          style="left:${((x / width) * 100).toFixed(3)}%; top:${((y / height) * 100).toFixed(3)}%; --marker-color: #111111;"
          aria-label="${escapeHtml(region.name)} 선택"
        ></button>
      `;
    })
    .join("");

  elements.worldMap.innerHTML = `
    <div class="world-map-frame is-natural">
      <svg class="world-map-svg" viewBox="0 0 ${width} ${height}" aria-label="한국 기후 지도">
        <rect class="map-sphere" x="0" y="0" width="${width}" height="${height}"></rect>
        <g>
          <path class="map-landmass" d="${path(countries)}"></path>
          <path class="map-country-borders" d="${path(borders)}"></path>
        </g>
        <rect class="map-frame-stroke" x="1" y="1" width="${width - 2}" height="${height - 2}"></rect>
      </svg>
      <div class="world-map-overlay">
        <span class="map-overlay-pill">기상청 지점정보 좌표</span>
        <span class="map-overlay-pill">한반도 중심 투영 지도</span>
      </div>
      <div class="world-map-markers">${markers}</div>
    </div>
  `;
}

function buildFocusPolygon() {
  return {
    type: "Polygon",
    coordinates: [[
      [KOREA_MAP_BOUNDS.minLongitude, KOREA_MAP_BOUNDS.minLatitude],
      [KOREA_MAP_BOUNDS.maxLongitude, KOREA_MAP_BOUNDS.minLatitude],
      [KOREA_MAP_BOUNDS.maxLongitude, KOREA_MAP_BOUNDS.maxLatitude],
      [KOREA_MAP_BOUNDS.minLongitude, KOREA_MAP_BOUNDS.maxLatitude],
      [KOREA_MAP_BOUNDS.minLongitude, KOREA_MAP_BOUNDS.minLatitude],
    ]],
  };
}

function getPeriodMetrics(region, period) {
  const monthIndexes = period.monthIndexes;
  return {
    id: period.id,
    label: period.label,
    temperature: average(monthIndexes.map((index) => region.monthlyTemperatureC[index])),
    precipitation: round(sum(monthIndexes.map((index) => region.monthlyPrecipitationMm[index]))),
    coldDays: round(sum(monthIndexes.map((index) => region.monthlyColdDaysBelowZero[index]))),
    hotDays: round(sum(monthIndexes.map((index) => region.monthlyHotDaysAboveTwentyFiveMin[index]))),
  };
}

function renderPeriodTemperatureChart(metrics) {
  const width = 420;
  const height = 220;
  const padding = { top: 18, right: 14, bottom: 48, left: 42 };
  const values = metrics.map((metric) => metric.temperature);
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const yMin = Math.floor((minValue - 2) / 5) * 5;
  const yMax = Math.ceil((maxValue + 2) / 5) * 5;
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  const stepX = chartWidth / Math.max(metrics.length - 1, 1);

  const points = metrics
    .map((metric, index) => {
      const x = padding.left + stepX * index;
      const y = padding.top + ((yMax - metric.temperature) / Math.max(yMax - yMin, 1)) * chartHeight;
      return { ...metric, x, y };
    });

  const pathData = points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`).join(" ");
  const yTicks = buildTicks(yMin, yMax, 5);

  return `
    <svg class="svg-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="시기별 평균기온 그래프">
      ${yTicks
        .map((tick) => {
          const y = padding.top + ((yMax - tick) / Math.max(yMax - yMin, 1)) * chartHeight;
          return `
            <line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" stroke="#d0d0d0" stroke-dasharray="4 4"></line>
            <text x="${padding.left - 8}" y="${y + 4}" text-anchor="end" font-size="11" fill="#555555">${tick}</text>
          `;
        })
        .join("")}
      <line x1="${padding.left}" y1="${padding.top + chartHeight}" x2="${width - padding.right}" y2="${padding.top + chartHeight}" stroke="#111111"></line>
      <path d="${pathData}" fill="none" stroke="#111111" stroke-width="2"></path>
      ${points
        .map(
          (point) => `
            <circle cx="${point.x}" cy="${point.y}" r="4.5" fill="#111111"></circle>
            <text x="${point.x}" y="${point.y - 10}" text-anchor="middle" font-size="11" fill="#111111">${point.temperature.toFixed(1)}</text>
            <text x="${point.x}" y="${height - 16}" text-anchor="middle" font-size="11" fill="#555555">${escapeHtml(point.label)}</text>
          `
        )
        .join("")}
    </svg>
  `;
}

function renderPeriodPrecipitationChart(metrics) {
  const width = 420;
  const height = 220;
  const padding = { top: 18, right: 14, bottom: 48, left: 46 };
  const values = metrics.map((metric) => metric.precipitation);
  const maxValue = Math.max(...values, 10);
  const yMax = Math.ceil(maxValue / 50) * 50;
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  const barWidth = chartWidth / metrics.length - 18;

  const yTicks = buildTicks(0, yMax, Math.max(yMax / 4, 25));

  return `
    <svg class="svg-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="시기별 강수량 그래프">
      ${yTicks
        .map((tick) => {
          const y = padding.top + ((yMax - tick) / Math.max(yMax, 1)) * chartHeight;
          return `
            <line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" stroke="#d0d0d0" stroke-dasharray="4 4"></line>
            <text x="${padding.left - 8}" y="${y + 4}" text-anchor="end" font-size="11" fill="#555555">${tick}</text>
          `;
        })
        .join("")}
      <line x1="${padding.left}" y1="${padding.top + chartHeight}" x2="${width - padding.right}" y2="${padding.top + chartHeight}" stroke="#111111"></line>
      ${metrics
        .map((metric, index) => {
          const x = padding.left + index * (chartWidth / metrics.length) + 10;
          const barHeight = (metric.precipitation / Math.max(yMax, 1)) * chartHeight;
          const y = padding.top + chartHeight - barHeight;
          return `
            <rect x="${x}" y="${y}" width="${barWidth}" height="${barHeight}" fill="#111111"></rect>
            <text x="${x + barWidth / 2}" y="${y - 8}" text-anchor="middle" font-size="11" fill="#111111">${Math.round(
              metric.precipitation
            )}</text>
            <text x="${x + barWidth / 2}" y="${height - 16}" text-anchor="middle" font-size="11" fill="#555555">${escapeHtml(
              metric.label
            )}</text>
          `;
        })
        .join("")}
    </svg>
  `;
}

function renderDeviationDotChart(symbols, period) {
  const metrics = symbols.map(({ symbol, region }) => ({
    symbol,
    ...getPeriodMetrics(region, period),
  }));
  const averageValue = average(metrics.map((metric) => metric.temperature));
  const deviations = metrics.map((metric) => ({
    ...metric,
    deviation: round(metric.temperature - averageValue),
  }));
  const width = 420;
  const height = 220;
  const padding = { top: 18, right: 16, bottom: 42, left: 40 };
  const minValue = Math.min(...deviations.map((item) => item.deviation), -1);
  const maxValue = Math.max(...deviations.map((item) => item.deviation), 1);
  const axisBound = Math.max(Math.ceil(Math.max(Math.abs(minValue), Math.abs(maxValue))), 2);
  const yMin = -axisBound;
  const yMax = axisBound;
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  const stepX = chartWidth / Math.max(deviations.length - 1, 1);
  const zeroY = padding.top + ((yMax - 0) / (yMax - yMin)) * chartHeight;

  return `
    <svg class="svg-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(period.label)} 기온 편차 그래프">
      ${buildTicks(yMin, yMax, 1)
        .map((tick) => {
          const y = padding.top + ((yMax - tick) / (yMax - yMin)) * chartHeight;
          return `
            <line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" stroke="${
              tick === 0 ? "#111111" : "#d0d0d0"
            }" stroke-dasharray="${tick === 0 ? "0" : "4 4"}"></line>
            <text x="${padding.left - 8}" y="${y + 4}" text-anchor="end" font-size="11" fill="#555555">${tick}</text>
          `;
        })
        .join("")}
      ${deviations
        .map((item, index) => {
          const x = padding.left + stepX * index;
          const y = padding.top + ((yMax - item.deviation) / (yMax - yMin)) * chartHeight;
          return `
            <circle cx="${x}" cy="${y}" r="5" fill="#111111"></circle>
            <text x="${x}" y="${zeroY + 22}" text-anchor="middle" font-size="12" fill="#111111">${item.symbol}</text>
          `;
        })
        .join("")}
    </svg>
  `;
}

function renderDeviationBarChart(symbols, period) {
  const metrics = symbols.map(({ symbol, region }) => ({
    symbol,
    ...getPeriodMetrics(region, period),
  }));
  const averageValue = average(metrics.map((metric) => metric.precipitation));
  const deviations = metrics.map((metric) => ({
    ...metric,
    deviation: round(metric.precipitation - averageValue),
  }));
  const width = 420;
  const height = 220;
  const padding = { top: 18, right: 16, bottom: 42, left: 46 };
  const maxAbs = Math.max(...deviations.map((item) => Math.abs(item.deviation)), 20);
  const axisBound = Math.ceil(maxAbs / 20) * 20;
  const yMin = -axisBound;
  const yMax = axisBound;
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  const zeroY = padding.top + ((yMax - 0) / (yMax - yMin)) * chartHeight;
  const barWidth = chartWidth / deviations.length - 18;

  return `
    <svg class="svg-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(period.label)} 강수 편차 그래프">
      ${buildTicks(yMin, yMax, Math.max(axisBound / 4, 20))
        .map((tick) => {
          const y = padding.top + ((yMax - tick) / (yMax - yMin)) * chartHeight;
          return `
            <line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" stroke="${
              tick === 0 ? "#111111" : "#d0d0d0"
            }" stroke-dasharray="${tick === 0 ? "0" : "4 4"}"></line>
            <text x="${padding.left - 8}" y="${y + 4}" text-anchor="end" font-size="11" fill="#555555">${tick}</text>
          `;
        })
        .join("")}
      ${deviations
        .map((item, index) => {
          const x = padding.left + index * (chartWidth / deviations.length) + 10;
          const barHeight = (Math.abs(item.deviation) / Math.max(axisBound, 1)) * (chartHeight / 2);
          const y = item.deviation >= 0 ? zeroY - barHeight : zeroY;
          return `
            <rect x="${x}" y="${y}" width="${barWidth}" height="${barHeight}" fill="#111111"></rect>
            <text x="${x + barWidth / 2}" y="${zeroY + 22}" text-anchor="middle" font-size="12" fill="#111111">${item.symbol}</text>
          `;
        })
        .join("")}
    </svg>
  `;
}

function buildTicks(minValue, maxValue, step) {
  const ticks = [];
  for (let value = minValue; value <= maxValue + 0.0001; value += step) {
    ticks.push(round(value));
  }
  return ticks;
}

function sortRegions(left, right) {
  const zoneOrder = state.dataset.zoneOrder;
  const leftIndex = zoneOrder.indexOf(left.zone);
  const rightIndex = zoneOrder.indexOf(right.zone);
  if (leftIndex !== rightIndex) {
    return leftIndex - rightIndex;
  }
  return collator.compare(left.name, right.name);
}

function createSymbol(index) {
  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  const base = alphabet[index % alphabet.length];
  const cycle = Math.floor(index / alphabet.length);
  return cycle === 0 ? base : `${base}${cycle}`;
}

function normalizeText(value) {
  return String(value ?? "")
    .normalize("NFKC")
    .trim()
    .toLowerCase();
}

function renderEmptyState(title, description) {
  return `
    <div class="empty-state">
      <strong>${escapeHtml(title)}</strong>
      <p>${escapeHtml(description)}</p>
    </div>
  `;
}

function formatTemp(value) {
  return `${value.toFixed(1)}°C`;
}

function formatMm(value) {
  return `${Math.round(value)} mm`;
}

function formatDays(value) {
  return `${value.toFixed(1)}일`;
}

function formatMeters(value) {
  return `${Math.round(value).toLocaleString("ko-KR")} m`;
}

function formatCoordinatePair(location) {
  return `${formatLatitude(location.latitude)} · ${formatLongitude(location.longitude)}`;
}

function formatLatitude(value) {
  return `${value >= 0 ? "북위" : "남위"} ${coordinateFormatter.format(Math.abs(value))}°`;
}

function formatLongitude(value) {
  return `${value >= 0 ? "동경" : "서경"} ${coordinateFormatter.format(Math.abs(value))}°`;
}

function average(values) {
  return round(sum(values) / values.length);
}

function sum(values) {
  return values.reduce((total, value) => total + Number(value || 0), 0);
}

function round(value) {
  return Number(Number(value).toFixed(1));
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
