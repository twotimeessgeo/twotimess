# 투타임즈 기후머신

기본 57개 지역을 Open-Meteo ERA5 `1991-2020` 기준으로 맞춘 정적 웹 앱입니다.
모든 번들 기후 데이터는 같은 API 기준으로 계산되고, 추가 지역도 같은 방식으로 붙습니다.
Open-Meteo API 검색으로 새로운 도시를 계속 추가할 수 있고, 추가한 지역은 현재 브라우저에 저장되어 새로고침 후에도 유지됩니다.

## 포함 기능

- 지역 검색 및 대륙별 필터
- 반구(`북반구`, `남반구`) 필터
- 기후 구분(`Af`, `Am`, `Aw`, `BS`, `Bw`, `Cfa`, `Cfb`, `Cs`, `Cw`, `Df`, `Dw`, `ET`, `EF`, `H`) 필터
- 크게 확장된 세계 지도 패널
- 지도 표시 전환: `전체 지역` / `선택 지역만`
- 마커, 지역 목록, 선택 카드에서 위도·경도 표시
- Natural Earth 기반 투영 지도와 마커 클릭 선택
- 지도 점을 위도·경도 기준으로 투영 위치에 표시
- 기후대가 서로 다른 지역 4개 랜덤 선택
- Open-Meteo Geocoding API로 도시 검색
- Open-Meteo Historical Weather API 기반 월평년값 계산 후 새 지역 즉시 추가
- 온라인으로 추가한 지역을 브라우저에 저장해 다시 열어도 유지
- 선택 지역별 월별 기온·강수량 표
- 선택 지역별 기후 그래프
- 여러 지역 선택 시 1월, 7월 평균 기온·강수량 편차 비교
- 예시 문제 스타일의 점 그래프, 막대 그래프
- 직각형 흑백 UI와 Pretendard 폰트

## 실행 방법

가장 쉬운 방법은 아래 둘 중 하나입니다.

1. `open.command`를 더블클릭한다.
2. `index.html`을 더블클릭한다.

이제 `data/climate-data.js`와 `data/world-countries-50m.js`가 함께 포함되어,
로컬 서버 없이도 지도까지 포함한 전체 앱이 바로 실행됩니다.

단, `API로 새 지역 추가` 기능은 인터넷 연결이 필요합니다.

로컬 서버로 열고 싶다면 아래처럼 실행하면 됩니다.

```bash
python3 -m http.server 8000
```

그다음 브라우저에서 `http://localhost:8000`을 열면 됩니다.

## 다른 사람에게 공유하는 방법

- 가장 간단한 방식은 이 폴더 전체를 압축(`zip`)해서 전달하는 것입니다.
- 받은 사람은 압축을 풀고 `open.command` 또는 `index.html`만 열면 됩니다.
- 별도 백엔드가 없는 정적 웹 앱이라, 원하면 정적 파일 호스팅에도 그대로 올릴 수 있습니다.
- 온라인 검색으로 지역을 더 늘리려면 받은 사람 쪽에서도 인터넷 연결이 되어 있어야 합니다.

## 인터넷 배포

이 프로젝트는 서버가 필요 없는 정적 사이트라서 `index.html`, `styles.css`, `app.js`, `data/` 폴더만 그대로 올리면 됩니다.

### 추천 1: Cloudflare Pages

- 가장 쉬운 방식은 Cloudflare Pages에 폴더를 올리는 것입니다.
- Git 저장소를 연결해도 되고, `Direct Upload`로 현재 폴더를 바로 올려도 됩니다.
- 업로드가 끝나면 기본적으로 `프로젝트명.pages.dev` 주소가 생깁니다.

### 추천 2: GitHub Pages

- 이 프로젝트에는 이미 `.github/workflows/pages.yml`이 들어 있어, `main` 브랜치에 push하면 GitHub Actions 기반 Pages 배포를 바로 쓸 수 있습니다.
- GitHub 저장소를 만든 뒤 이 폴더를 업로드하고, 저장소의 `Settings > Pages`에서 소스를 `GitHub Actions`로 맞추면 됩니다.
- 기본 주소는 보통 `https://사용자이름.github.io/저장소명/` 형태입니다.
- 사용자 사이트 저장소 이름을 `사용자이름.github.io`로 만들면 `https://사용자이름.github.io/` 주소로 바로 운영할 수 있습니다.

## 데이터 재생성

기본 지역 57개 통계를 Open-Meteo 기준으로 다시 생성하려면 아래 스크립트를 실행합니다.

```bash
python3 scripts/extend_with_wmo.py
```

## 파일 구성

- `index.html`: 앱 화면
- `styles.css`: UI 스타일
- `app.js`: 데이터 로딩, 표/그래프 렌더링
- `data/climate-data.json`: 기본 57개 지역의 번들 기후 데이터
- `data/climate-data.js`: 브라우저에서 바로 쓰는 데이터 번들
- `data/world-countries-50m.js`: 브라우저에서 바로 쓰는 고해상도 세계 지도 Topology 번들
- `data/region-metadata.json`: 좌표, 영문명, 별칭 메타데이터
- `data/wmo-region-manifest.json`: 초기 보강 지역 선정에 사용한 외부 지역 목록
- `data/world-countries-50m.json`: 고해상도 세계 국가 Topology 데이터
- `data/world-countries-110m.json`: 지도 로드 실패 시 사용할 하위 호환 Topology 데이터
- `open.command`: macOS에서 더블클릭으로 바로 여는 실행 파일
- `data/vendor-d3.min.js`: 지도 투영 렌더링용 D3 번들
- `data/vendor-topojson-client.min.js`: TopoJSON 파싱 라이브러리
- `scripts/extend_with_wmo.py`: 기본 지역 통계를 Open-Meteo 기준으로 재생성하는 스크립트
- `.github/workflows/pages.yml`: GitHub Pages 자동 배포 워크플로

## 온라인 확장 동작

- 검색창에 도시나 지역명을 입력하면 Open-Meteo Geocoding API로 좌표 후보를 찾습니다.
- 후보에서 `기후 불러와 추가`를 누르면 Historical Weather API의 `1991-2020` 일별 자료를 월별 평균 기온·월별 평균 강수량으로 집계합니다.
- 추가된 지역은 기존 지역과 동일하게 지도, 필터, 표, 비교 그래프에 바로 포함됩니다.
- 추가된 지역은 브라우저의 `localStorage`에 저장되어 다음 실행 때도 다시 불러옵니다.
- 번들 데이터는 이미 Open-Meteo 기준이고, 필요하면 앱의 기본 데이터 재동기화로 다시 계산 상태를 점검할 수 있습니다.

## 참고 출처

- Open-Meteo Geocoding API: <https://open-meteo.com/en/docs/geocoding-api>
- Open-Meteo Historical Weather API: <https://open-meteo.com/en/docs/historical-weather-api>
- Natural Earth Downloads: <https://www.naturalearthdata.com/downloads/>
- Natural Earth Terms of Use: <https://www.naturalearthdata.com/about/terms-of-use/>
