# Spain–South Korea–Japan open official-data extraction wave — reviewed 2026-08-02

This package is an extraction control, not a market-size result. Its machine-readable controlling record is `open-official-extraction-wave-es-kr-jp.json`; the executable validator and parsers are in `scripts/extract_es_kr_jp_open_data.py`.

## Current decision

| Country | Route | State | Transaction stage | What it can establish | What it cannot establish |
| --- | --- | --- | --- | --- | --- |
| Spain | AEAT 2025 annual and 2026 H1 machine-readable series | Ready | Accrued excise liability and gross/refund/net cash receipts | Exact 2025 accrued EUR 36.151m and net cash EUR 29.568m, plus 2025 and 2026 H1 cash reconciliations across all four Model 573 epigraphs | E-liquid-only receipts, product quantities, devices or consumer retail sales |
| Spain | Model 573 epigraph quantities | Blocked | Taxpayer self-assessed excise base | The exact fields required to close the product split | A national quantity series until AEAT publishes or supplies an aggregate |
| South Korea | KCS Itemtrade HSK10 API | Auth required, free | Customs border declarations | Import CIF value/net weight and export FOB value/net weight by exact validated HSK10 code | Consumer retail sales, domestic production, inventory or a justified apparent-consumption bridge |
| Japan | MOF/e-Stat Commodity by Country imports | Ready, free | Customs import declarations | Reproduced 2022–2025 import CIF value and declared quantity by separate 9-digit code | Retail sell-through, domestic production, exports, illicit supply or retail mark-up |

No route is eligible for the public global retail roll-up.

## Spain boundary

Order HAC/86/2025 applies from 1 April 2025. The rounded AEAT headline of EUR 30 million is now superseded for quantitative work by exact machine-readable cells. Table 5.1 reports provisional 2025 accrued excise liability of EUR 36.151 million and provisional cash-basis net receipts of EUR 29.568 million. The current monthly workbook reconciles 2025 as EUR 31.797 million gross plus EUR -2.229 million refunds and 2026 H1 as EUR 25.726 million gross plus EUR -3.950 million refunds, yielding EUR 21.776 million net. These are fiscal observations, not sales observations.

The tax aggregate covers four different epigraphs:

1. E-liquid without nicotine or with at most 15 mg/ml: EUR 0.15/ml.
2. E-liquid above 15 mg/ml: EUR 0.20/ml.
3. Nicotine pouches: EUR 0.10/g.
4. Other nicotine products: EUR 0.10/g.

Because AEAT does not publish the epigraph mix, every value must remain `ALL_EPIGRAPHS`. Backsolving litres from any aggregate would silently assume a rate and product mix and is therefore prohibited. The 2025 period is also prospective and transitional rather than a full-year comparable. The EUR 6.583 million difference between accrued liability and net cash is not margin, sales or a market gap.

Primary sources:

- [AEAT annual revenue report 2025](https://sede.agenciatributaria.gob.es/Sede/estadisticas/recaudacion-tributaria/informe-anual/ejercicio-2025/1-ingresos-tributarios-2025/impuestos-devengados-ingresos-tributarios.html)
- [AEAT table 5.1 annual workbook](https://sede.agenciatributaria.gob.es/static_files/AEAT/Estudios/Estadisticas/Informes_Estadisticos/Informes_Anuales_de_Recaudacion_Tributaria/Ejercicio_2025/Cuadro_5.1_es_es.xlsx)
- [AEAT current monthly statistical-series workbook](https://sede.agenciatributaria.gob.es/static_files/Sede/Tema/Estadisticas/Recaudacion_Tributaria/Informes_mensuales/Cuadros_estadisticos_series_es_es.xlsx)
- [AEAT Model 573 procedure](https://sede.agenciatributaria.gob.es/Sede/procedimientoini/DI10.shtml)
- [Order HAC/86/2025](https://www.boe.es/buscar/doc.php?id=BOE-A-2025-1732)
- [AEAT tax base and rates](https://sede.agenciatributaria.gob.es/Sede/impuestos-especiales-medioambientales/impuestos-especiales-fabricacion/liquidos-cigarrillos-electronicos-otros-productos-tabaco/base-imponible-tipo-gravamen.html)

## South Korea boundary

The official API contract is:

- Base URL: `https://apis.data.go.kr/1220000/Itemtrade`
- Operation: `GET /getItemtradeList`
- Version: `1.0.0`
- Required parameters: `serviceKey`, `strtYymm`, `endYymm`
- Optional product parameter: `hsSgn`
- Response fields: `year`, `balPayments`, `expDlr`, `expWgt`, `hsCode`, `impDlr`, `impWgt`, `statKor`

The API is free but needs a Public Data Portal service key. KCS describes imports as CIF/customs value in USD, exports as FOB/declared value in USD and weight as net kilograms.

The open code file currently verified here is `Korea Customs Service_HS Code_20260101`. It supplies candidate 2026 HSK10 mappings. It does not prove that the same 10-digit national codes applied unchanged in 2022–2025. Historical extraction therefore remains blocked until an exact year-specific codebook is verified. Broad “other” and parts codes remain review-only or excluded.

Primary sources:

- [KCS item-level import and export OpenAPI](https://www.data.go.kr/data/15101609/openapi.do)
- [KCS HS code file 20260101](https://www.data.go.kr/en/data/15049722/fileData.do)

## Japan boundary

Japan Customs uses 9-digit statistical codes. Eight revised e-Stat partner-level import CSVs for 2022–2025 expose these exact fields:

`Exp or Imp`, `Year`, `HS`, `Country`, `Unit1`, `Unit2`, `Quantity1-Year`, `Quantity2-Year`, `Value-Year`.

The extractor filters imports (`Exp or Imp = 2`), validates the year and aggregates partner rows only within each separate 9-digit code. `Value-Year` remains in the official unit of JPY thousand and is labelled as an import CIF customs value.

The year-specific 2022–2025 code decisions are:

- `854340000`: electronic cigarettes and similar personal electric vaporising devices — included only as a device customs proxy.
- `240412000`: other products containing nicotine — retained separately as a regulated nicotine non-combustion category; not labelled e-liquid-only.
- `240419100`: manufactured tobacco substitutes — excluded from vaping aggregation pending scope review.
- `240419200`: other non-combustion product — excluded from vaping aggregation pending scope review.

MHLW Q&A 63 states that nicotine-containing e-cigarette cartridges and liquids are treated as pharmaceuticals. Customs-only personal-import limits are 60 cartridges or 120 ml; above those quantities an import confirmation is required. Business imports require the relevant marketing approval and business-licence evidence. This legal boundary is context only: it is never used as a numerical market adjustment, and nicotine records are never combined with nicotine-free retail activity.

The exact device-code series is JPY 70.257bn / 19.099m declared units in 2022, JPY 70.496bn / 18.059m units in 2023, JPY 74.526bn / 17.657m units in 2024 and JPY 84.361bn / 20.529m units in 2025. These are CIF imports. The dedicated control preserves all four codes separately, validates all eight file hashes and publishes same-year ECB EUR equivalents only as secondary analytical values.

Primary sources:

- [Japan Trade Statistics data download](https://www.customs.go.jp/toukei/info/tsdl_e.htm)
- [2025 chapter 16–24 revised import CSV](https://www.e-stat.go.jp/en/stat-search/file-download?fileKind=1&statInfId=000040424871)
- [2025 chapter 84–85 revised import CSV](https://www.e-stat.go.jp/en/stat-search/file-download?fileKind=1&statInfId=000040424883)
- [Japan Trade Statistics code lists](https://www.customs.go.jp/toukei/sankou/code/code_e.htm)
- [Japan Customs classification ruling for a nicotine-filled disposable e-cigarette](https://www.customs.go.jp/tetsuzuki_search/bunrui/J4/24/J42400321.htm)
- [Japan Customs classification example for a nicotine-free e-cigarette cartridge](https://www.customs.go.jp/tetsuzuki/bunruijirei/bunruijirei2404001.pdf)
- [MHLW pharmaceutical import procedure Q&A 63](https://www.mhlw.go.jp/web/t_doc?dataId=00tc1462&dataType=1&pageNo=2)

## Reproducible use

Validate the route control and print current route states without network access:

```bash
python3 scripts/extract_es_kr_jp_open_data.py
```

Run the deterministic tests:

```bash
python3 -m unittest scripts/test_es_kr_jp_open_data.py
```

Extract a saved AEAT HTML page:

```bash
python3 scripts/extract_es_kr_jp_open_data.py \
  --spain-html /path/to/aeat-2025.html
```

Extract one or both downloaded 2025 Japan CSV tables:

```bash
python3 scripts/extract_es_kr_jp_open_data.py \
  --japan-import-csv /path/to/table-25-04.csv \
  --japan-import-csv /path/to/table-25-16.csv \
  --japan-year 2025
```

Reproduce the full controlled Japan series after downloading the eight exact source files named in the control:

```bash
python3 scripts/extract_japan_2022_2025_series.py \
  --downloads /path/to/the/eight/official/csv/files \
  --output /tmp/japan-series.json
python3 scripts/validate_japan_2022_2025_series.py
```

The exact Spain series has its own hash-controlled workbook extractor and validator in `scripts/extract_spain_aeat_2025_2026_series.py` and `scripts/validate_spain_aeat_2025_2026_series.py`.

A saved KCS XML response can be parsed only with the exact verified classification version:

```bash
python3 scripts/extract_es_kr_jp_open_data.py \
  --korea-xml /path/to/kcs-response.xml \
  --korea-codebook-version KCS_HS_CODE_20260101
```

The script emits no zero placeholders. Missing credentials, historical codebooks, required fields, exact anchors or reviewed codes stop extraction with an error. It does not fetch data, send messages, incur fees, convert currencies, calculate a retail estimate or update shared public observations.
