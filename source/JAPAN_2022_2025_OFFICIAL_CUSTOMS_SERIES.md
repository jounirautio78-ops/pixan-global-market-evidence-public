# Japan 2022–2025 official customs proxy series

Reviewed: 2026-08-02
Status: extracted and reproducible official border proxy; retail value not
computed
Publication state: local v42 candidate only; not published

## Executive conclusion

Eight official Ministry of Finance / Japan Customs partner-level import CSV
tables produce 16 annual observations for four separate 9-digit statistical
codes. The clearest vaping-specific result is code `854340000`, electronic
cigarettes and similar personal electric vaporising devices:

| Year | Import CIF value JPY | ECB annual-average EUR equivalent | Declared quantity |
|:---|---:|---:|---:|
| 2022 | 70,257,202,000 | 509,009,121.12 | 19,099,172 units |
| 2023 | 70,496,284,000 | 463,821,018.99 | 18,058,688 units |
| 2024 | 74,526,020,000 | 454,837,652.81 | 17,657,457 units |
| 2025 | 84,361,341,000 | 499,051,223.28 | 20,529,032 units |

JPY is the primary observed currency. The EUR figures are secondary analytical
equivalents calculated as source JPY divided by the same-year ECB annual
average:

- 2022: 138.027392996109 JPY per EUR;
- 2023: 151.9902745098038 JPY per EUR;
- 2024: 163.8519140625 JPY per EUR;
- 2025: 169.0434509803921 JPY per EUR.

This series is a customs-import device proxy. It is not Japanese consumer
retail sell-through, does not include domestic production or retail mark-up,
and remains ineligible for the donor or global roll-up.

## Other reviewed codes kept separate

| Year | Code `240412000` JPY / quantity | Code `240419100` JPY / quantity | Code `240419200` JPY / quantity |
|:---|---:|---:|---:|
| 2022 | 3,180,000 / 1,081 kg | 172,856,000 / 36,526 kg | 1,075,026,000 / 175,133 kg |
| 2023 | 2,306,000 / 47 kg | 6,240,000 / 640 kg | 7,346,549,000 / 1,022,947 kg |
| 2024 | 445,000 / 15 kg | 2,996,000 / 355 kg | 7,130,411,000 / 815,848 kg |
| 2025 | 4,119,000 / 135 kg | 2,041,000 / 142 kg | 6,997,037,000 / 805,316 kg |

- `240412000` is a regulated nicotine-containing non-combustion category. It
  is not labelled e-liquid-only. A Japan Customs ruling places one
  nicotine-filled disposable e-cigarette in this code, which proves inclusion
  of that example rather than exclusivity of the aggregate.
- `240419100` and `240419200` are broader tobacco-substitute or other
  non-combustion categories and remain excluded from vaping aggregation. A
  separate Japan Customs example places one nicotine-free e-cigarette
  cartridge in `240419200`, but the whole code remains broader than vaping.
- The four codes are never summed into a single market value.

## Integrity and reproducibility

The extraction validates:

- eight exact official CSV files;
- 15,788,473 source bytes;
- file size and SHA-256 for every table;
- import flow, source year, partner-code format and required fields;
- the exact four-code allowlist;
- original JPY-thousand values and declared quantities; and
- same-year official ECB annual-average conversions.

Controlled records:

- `source/JAPAN_2022_2025_OFFICIAL_CUSTOMS_SERIES_CONTROL.json`
  (`49e47af1766796c162711ccef0591ee5cd6c498b9985cb389496f54173ef477e`);
- `scripts/extract_japan_2022_2025_series.py`;
- `source/JAPAN_2022_2025_OFFICIAL_CUSTOMS_SERIES.json`
  (`f90ce43a079fd0ffae9197d00e629ec7ba6ab581050df141dc4378ac194735bc`).

Reproduction:

```bash
python3 scripts/extract_japan_2022_2025_series.py \
  --downloads /path/to/the/eight/official/csv/files
```

The parser fails if a file is missing, has a different size or hash, lacks a
required field, contains an unexpected flow/year for a target code, omits a
reviewed code or mixes quantity units.

## Permitted wording

> Japan Customs records JPY 84.36 billion of 2025 CIF imports and 20.53 million
> declared units under the specific electronic-cigarette device code
> 854340000. The same-year ECB analytical equivalent is EUR 499.05 million.
> This is a border-import proxy, not consumer retail market value.

Do not claim that the CIF values are retail sales, that every declared unit was
sold in the same year, that the device code contains liquid revenue, or that
the broader chapter 24 codes are vaping-only.

## Canonical official sources

- [Japan Trade Statistics data download](https://www.customs.go.jp/toukei/info/tsdl_e.htm)
- [Japan import statistical-code schedules](https://www.customs.go.jp/english/tariff/index.htm)
- [e-Stat trade-statistics datasets](https://www.e-stat.go.jp/en/stat-search/files?layout=dataset&page=1&toukei=00350300)
- [Japan Customs ruling: nicotine-filled disposable e-cigarette](https://www.customs.go.jp/tetsuzuki_search/bunrui/J4/24/J42400321.htm)
- [Japan Customs example: nicotine-free e-cigarette cartridge](https://www.customs.go.jp/tetsuzuki/bunruijirei/bunruijirei2404001.pdf)
- [ECB EXR data information](https://data.ecb.europa.eu/data/datasets/exr/data-information)

This is independent research. It is not Pixan Oy's official position, an
audit, valuation, legal opinion, investment recommendation or lending
recommendation.
