# Spain–South Korea–Japan open official-data extraction wave — 2026-07-28

This package is an extraction control, not a market-size result. Its machine-readable controlling record is `open-official-extraction-wave-es-kr-jp.json`; the executable validator and parsers are in `scripts/extract_es_kr_jp_open_data.py`.

## Current decision

| Country | Route | State | Transaction stage | What it can establish | What it cannot establish |
| --- | --- | --- | --- | --- | --- |
| Spain | AEAT 2025 Model 573 aggregate receipts | Ready | Realised excise cash receipts | One official 2025 aggregate of EUR 30 million across all four Model 573 epigraphs | E-liquid-only receipts, product quantities, devices or consumer retail sales |
| Spain | Model 573 epigraph quantities | Blocked | Taxpayer self-assessed excise base | The exact fields required to close the product split | A national quantity series until AEAT publishes or supplies an aggregate |
| South Korea | KCS Itemtrade HSK10 API | Auth required, free | Customs border declarations | Import CIF value/net weight and export FOB value/net weight by exact validated HSK10 code | Consumer retail sales, domestic production, inventory or a justified apparent-consumption bridge |
| Japan | MOF/e-Stat Commodity by Country imports | Ready, free | Customs import declarations | 2025 import CIF value and declared quantity by separate 9-digit code | Retail sell-through, domestic production, exports, illicit supply or retail mark-up |

No route is eligible for the public global retail roll-up.

## Spain boundary

Order HAC/86/2025 applies from 1 April 2025. AEAT's 2025 annual report states that the new tax collected EUR 30 million in its first year. That is a fiscal cash observation, not a sales observation.

The tax aggregate covers four different epigraphs:

1. E-liquid without nicotine or with at most 15 mg/ml: EUR 0.15/ml.
2. E-liquid above 15 mg/ml: EUR 0.20/ml.
3. Nicotine pouches: EUR 0.10/g.
4. Other nicotine products: EUR 0.10/g.

Because AEAT does not publish the epigraph mix in the annual aggregate, the EUR 30 million must remain `ALL_EPIGRAPHS`. Backsolving litres from it would silently assume a rate and product mix and is therefore prohibited. The 2025 period is also prospective and transitional rather than a full-year comparable.

Primary sources:

- [AEAT annual revenue report 2025](https://sede.agenciatributaria.gob.es/Sede/estadisticas/recaudacion-tributaria/informe-anual/ejercicio-2025/1-ingresos-tributarios-2025/impuestos-devengados-ingresos-tributarios.html)
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

Japan Customs uses 9-digit statistical codes. The 2025 revised e-Stat partner-level import CSVs expose these exact fields:

`Exp or Imp`, `Year`, `HS`, `Country`, `Unit1`, `Unit2`, `Quantity1-Year`, `Quantity2-Year`, `Value-Year`.

The extractor filters imports (`Exp or Imp = 2`), validates the year and aggregates partner rows only within each separate 9-digit code. `Value-Year` remains in the official unit of JPY thousand and is labelled as an import CIF customs value.

The enabled 2025 code decisions are:

- `854340000`: electronic cigarettes and similar personal electric vaporising devices — included only as a device customs proxy.
- `240412000`: other products containing nicotine — retained separately as a regulated nicotine non-combustion category; not labelled e-liquid-only.
- `240419100`: manufactured tobacco substitutes — excluded from vaping aggregation pending scope review.
- `240419200`: other non-combustion product — excluded from vaping aggregation pending scope review.

MHLW Q&A 63 states that nicotine-containing e-cigarette cartridges and liquids are treated as pharmaceuticals. Customs-only personal-import limits are 60 cartridges or 120 ml; above those quantities an import confirmation is required. Business imports require the relevant marketing approval and business-licence evidence. This legal boundary is context only: it is never used as a numerical market adjustment, and nicotine records are never combined with nicotine-free retail activity.

Primary sources:

- [Japan Trade Statistics data download](https://www.customs.go.jp/toukei/info/tsdl_e.htm)
- [2025 chapter 16–24 revised import CSV](https://www.e-stat.go.jp/en/stat-search/file-download?fileKind=1&statInfId=000040424871)
- [2025 chapter 84–85 revised import CSV](https://www.e-stat.go.jp/en/stat-search/file-download?fileKind=1&statInfId=000040424883)
- [Japan Trade Statistics code lists](https://www.customs.go.jp/toukei/sankou/code/code_e.htm)
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

A saved KCS XML response can be parsed only with the exact verified classification version:

```bash
python3 scripts/extract_es_kr_jp_open_data.py \
  --korea-xml /path/to/kcs-response.xml \
  --korea-codebook-version KCS_HS_CODE_20260101
```

The script emits no zero placeholders. Missing credentials, historical codebooks, required fields, exact anchors or reviewed codes stop extraction with an error. It does not fetch data, send messages, incur fees, convert currencies, calculate a retail estimate or update shared public observations.
