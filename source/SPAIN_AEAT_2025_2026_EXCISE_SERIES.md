# Spain AEAT 2025–2026 H1 official excise series

Reviewed: 2026-08-02
Status: extracted and reproducible official tax-stage series; retail value not
computed
Publication state: local review branch only; not published

## Executive conclusion

Two exact AEAT workbooks independently reconcile the new Spanish excise
aggregate for e-cigarette liquids and other related products:

| Period and basis | Official value |
|:---|---:|
| 2025 accrued excise, provisional | EUR 36.151 million |
| 2025 gross cash receipts | EUR 31.797 million |
| 2025 refunds | EUR -2.229 million |
| 2025 net cash receipts | EUR 29.568 million |
| 2026 H1 gross cash receipts | EUR 25.726 million |
| 2026 H1 refunds | EUR -3.950 million |
| 2026 H1 net cash receipts | EUR 21.776 million |

The annual table's EUR 29.568 million net cash value reconciles exactly to the
sum of the monthly net series. The annual accrued value and the cash value are
different accounting bases and must not be substituted for one another.

## Monthly cash series

The source unit is EUR thousand. January through March 2025 are blank in the
official workbook and are preserved as null rather than recoded as zero.

| Month | Gross | Refunds | Net |
|:---|---:|---:|---:|
| 2025-01 | — | — | — |
| 2025-02 | — | — | — |
| 2025-03 | — | — | — |
| 2025-04 | 294 | 0 | 294 |
| 2025-05 | 2,332 | 0 | 2,332 |
| 2025-06 | 2,518 | 0 | 2,518 |
| 2025-07 | 5,311 | 0 | 5,311 |
| 2025-08 | 4,296 | 0 | 4,296 |
| 2025-09 | 4,426 | -357 | 4,069 |
| 2025-10 | 3,930 | -1,016 | 2,914 |
| 2025-11 | 4,508 | -12 | 4,496 |
| 2025-12 | 4,182 | -844 | 3,338 |
| **2025 total** | **31,797** | **-2,229** | **29,568** |
| 2026-01 | 4,352 | -9 | 4,343 |
| 2026-02 | 3,633 | -232 | 3,401 |
| 2026-03 | 3,563 | -723 | 2,840 |
| 2026-04 | 5,157 | -2,492 | 2,665 |
| 2026-05 | 4,578 | -107 | 4,471 |
| 2026-06 | 4,443 | -387 | 4,056 |
| **2026 H1 total** | **25,726** | **-3,950** | **21,776** |

## Scope boundary

This is the combined tax family across all four epigraphs. It is not e-liquid-only:
the aggregate also covers other related taxed products. The
workbooks do not provide the four-epigraph split in these cells.

There are no devices, device units, device revenue or consumer prices in this
series. The controlled geographic scope is mainland Spain and the Balearic Islands;
the Canary Islands, Ceuta and Melilla are outside the scope.

Accrued excise, gross cash receipts, refunds and net cash receipts are tax-stage
measures. They are not consumer retail sell-through, retail market value or a
direct measure of taxable liquid volume. No retail uplift, tax-rate inversion,
illicit-market adjustment or global extrapolation has been applied.

## Integrity and reproducibility

The extraction validates:

- annual workbook `Cuadro_5.1_es_es.xlsx`: 67,176 bytes, SHA-256
  `643a4cbfe0a8f647167f43b6433f9f9b45f804916916d5cf3ae720e796e5ecd7`;
- monthly workbook `Cuadros_estadisticos_series_es_es.xlsx`: 1,690,257
  bytes, SHA-256
  `e5186b7d7ca55eae22c24bdd8cd2b047f26db6313fba8b755596e70569578f8f`;
- exact workbook names, worksheet names, headers, cell coordinates and values;
- 1,757,433 official source bytes in total;
- all 18 controlled month rows, including the three source blanks;
- monthly and annual reconciliation; and
- gross plus refunds equals net for every populated month and total.

Controlled records:

- `source/SPAIN_AEAT_2025_2026_EXCISE_SERIES_CONTROL.json`
  (`453e58697530c5ccbdaf96bd95111a891ebc43b087f022a44788ded9ff5d3553`);
- `scripts/extract_spain_aeat_2025_2026_series.py`;
- `source/SPAIN_AEAT_2025_2026_EXCISE_SERIES.json`
  (`f6b1239067bb34ac975b91e4dcfb40a292ecea33bd0c771078e158bc1844c893`).

Reproduction:

```bash
python3 scripts/extract_spain_aeat_2025_2026_series.py \
  --downloads /path/to/the/two/official/xlsx/files
```

The standard-library-only parser reads the OOXML package directly and fails if
either file, hash, worksheet, header, controlled cell, accounting identity or
reconciliation differs.

## Permitted wording

> AEAT reports EUR 36.151 million of provisional 2025 accrued excise and EUR
> 29.568 million of 2025 net cash receipts for the combined Spanish tax on
> e-cigarette liquids and other related products. The monthly cash series also
> reports EUR 21.776 million net for 2026 H1. These are tax-stage aggregates,
> not consumer retail market value.

Do not claim that the aggregate is e-liquid-only, that it measures devices,
that tax cash equals retail sales, that the blank January–March 2025 cells are
zeros, or that it is eligible for the donor or global roll-up.

## Canonical official sources

- [AEAT 2025 annual excise analysis](https://sede.agenciatributaria.gob.es/Sede/estadisticas/recaudacion-tributaria/informe-anual/ejercicio-2025/5-impuestos-especiales.html)
- [AEAT annual table 5.1 XLSX](https://sede.agenciatributaria.gob.es/static_files/AEAT/Estudios/Estadisticas/Informes_Estadisticos/Informes_Anuales_de_Recaudacion_Tributaria/Ejercicio_2025/Cuadro_5.1_es_es.xlsx)
- [AEAT monthly tax-revenue landing page](https://sede.agenciatributaria.gob.es/Sede/datosabiertos/catalogo/hacienda/Informe_mensual_de_Recaudacion_Tributaria.shtml)
- [AEAT monthly statistical tables and series XLSX](https://sede.agenciatributaria.gob.es/static_files/Sede/Tema/Estadisticas/Recaudacion_Tributaria/Informes_mensuales/Cuadros_estadisticos_series_es_es.xlsx)

This is independent research. It is not Pixan Oy's official position, an
audit, valuation, legal opinion, investment recommendation or lending
recommendation.
