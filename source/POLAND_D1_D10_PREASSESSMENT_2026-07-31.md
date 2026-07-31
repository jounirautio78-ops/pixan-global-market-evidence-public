# Poland D1-D10 donor preassessment

Reviewed: 2026-07-31
Assessment object: Poland evidence programme, **not a country-year retail-value
candidate**

## Executive conclusion

Poland does not yet have one identified full-year national consumer-retail
value to score as a donor candidate. A formal donor score is therefore
**not applicable**, not `1/10` or another partial score.

The current evidence programme has:

- one criterion passed for the existing public anchors: D9;
- two criteria confirmed not met by the current evidence: D2 and D4; and
- seven unresolved criteria: D1, D3, D5, D6, D7, D8 and D10.

This preassessment does not add a sixth candidate to the donor cockpit. Poland
remains `not_accepted`, the donor gate remains **0/3**, and global retail value
remains `null/not_computed`.

## Material v37 product-scope correction

The official Polish category `urządzenia do waporyzacji` is broader than
e-cigarettes. The Ministry of Finance defines it to include:

- refillable electronic cigarettes;
- heaters used with heated or novel tobacco products; and
- multifunction devices usable with both e-liquid and novel tobacco products.

The PLN 175.3 million realised 2025 tax amount and the resulting
**4,382,500 implied taxed units** therefore refer to this broad group, not to
e-cigarette devices alone. The PLN 2.5 million tax amount and
**62,500 implied component sets** likewise relate to the broad statutory group.

The AKC-4/R declaration requires the device type to be identified as a
refillable electronic cigarette, heater or multifunction device. This means a
targeted aggregate subgroup request is technically possible. Until that split
is obtained, neither implied count may be described as a Pixan-relevant
e-cigarette-device count.

## D1-D10 table

| ID | Evidence state | Preliminary result | Current evidence | Required closure evidence |
|:---|:---|:---|:---|:---|
| D1 | Supported | Open | Complete e-liquid flow observations exist for 2020–2023. Official full-year tax receipts exist for 2024 e-liquid and 2025 products. | One complete calendar-year consumer-retail value covering devices and consumables on the same boundary. The device tax began only on 1 July 2025. |
| D2 | Confirmed not met | Failed | ZEFIR2/AIS data describe domestic sale, intra-EU acquisition and import flows; the 2025 figures are tax receipts. | Consumer-paid retail sell-through value. |
| D3 | Supported | Open | The 2025 tax response separates e-liquid, devices and component sets. | The broad, half-year device group must be split into e-cigarettes, heaters and multifunction devices and reconciled to a full-year consumables boundary. |
| D4 | Confirmed not met | Failed | E-liquid and several adjacent categories are separate, but the device-tax group mixes e-cigarettes with heated-tobacco heaters and multifunction devices. | Aggregate AKC-4/R subgroup split and an explicit treatment of multifunction devices. |
| D5 | Missing | Open | The flow is national, but this does not demonstrate nationwide retail-channel coverage. | Specialist, general-retail, online, illicit and reporting coverage plus a quantitative denominator. |
| D6 | Missing | Open | The Ministry combines domestic sales, intra-EU acquisitions and imports. | A non-duplicative bridge for components, exports, returns, destruction, inventories and possible overlapping stages. |
| D7 | Supported | Open | ZEFIR2 and AIS source systems and headline measures are identified. | Reporter counts, missing and late returns, revisions, coverage, quality warnings and an explanation for the sharp annual break. |
| D8 | Supported | Open | PLN, statutory tax rates and effective dates are official. | The VAT and excise basis of consumer retail price; no retail value currently exists to test. |
| D9 | Confirmed | Passed for current anchors | Official PDFs, tax rates and deterministic divisions are public and reproducible. | Any future retail value must receive its own public source chain. |
| D10 | Missing | Open | A Supreme Audit Office publication supplies an additional KAS-based control but is not an independent retail route. | A same-year KAS–EU-CEG–POS or retail reconciliation, or direct official validation. |

## Current verified anchors

| Year | Measure | Value | Boundary |
|:---|:---|---:|:---|
| 2020 | E-liquid domestic sale, intra-EU acquisition and import flow | 1,451,529 litres | Physical flow, not retail value |
| 2021 | Same | 277,265 litres | Physical flow, not retail value |
| 2022 | Same | 416,088 litres | Physical flow, not retail value |
| 2023 | Same | 805,441 litres | Physical flow, not retail value |
| 2024 | E-liquid excise receipts | PLN 561.4 million | Tax receipts, not sales revenue |
| First three quarters of 2024 | Domestic sale, import and intra-EU acquisition of e-liquid | 1,613.2 thousand kg | Weight, not litres or retail value |
| 2025 | E-liquid excise receipts | PLN 993.1 million | Tax receipts, not sales revenue |
| 2025 | Broad vaporisation-device-group excise receipts | PLN 175.3 million | Includes e-cigarettes, heaters and multifunction devices |
| 2025 | Broad group component-set excise receipts | PLN 2.5 million | Broad statutory group |
| 1 July–31 December 2025 tax regime | Broad-group implied taxed units | 4,382,500 devices; 62,500 sets | Deterministic tax-base bridge, not e-cigarette-only or retail sell-through |

The 1,613.2 thousand kg control is not joined to the litre series without an
official conversion. The PLN 561.4 million receipt is not divided by a single
per-ml rate to create a market volume before cash timing, refunds, inventory
and physical-flow differences are reconciled.

## Machine-readable preassessment

```json
{
  "candidateId": "PL-PREASSESSMENT-NO-RETAIL-VALUE",
  "countryIso2": "PL",
  "asOf": "2026-07-31",
  "candidateYear": null,
  "candidateRetailValue": null,
  "donorScore": null,
  "decision": "not_accepted",
  "globalRollupEligible": false,
  "passedCriteria": ["D9"],
  "failedCriteria": ["D2", "D4"],
  "openCriteria": ["D1", "D3", "D5", "D6", "D7", "D8", "D10"],
  "boundary": "Values from different years, units or transaction stages are not combined into a Polish retail-market value."
}
```

## Priority evidence route

1. Request monthly aggregate AKC-4/R device counts and tax amounts split into
   refillable electronic cigarettes, heaters and multifunction devices.
2. Request AKC-4/M e-liquid millilitres, disposable-device units and tax,
   together with domestic release, intra-EU acquisition, import, export,
   refund, destruction, inventory, exemption, reporter and revision fields.
3. Check the already-sent EU-CEG aggregate request before any follow-up. Its
   useful fields are product and kit units, devices, refill containers,
   millilitres, retail or wholesale status and reporting missingness.
4. Build a same-year KAS–EU-CEG quantity reconciliation. It may close D3, D4,
   D6 or D7 gaps but does not itself create retail value.
5. Obtain same-year tax-inclusive, channel-weighted consumer prices or
   rights-cleared POS data. A tax-times-price model is not observed market
   value.

Any new request must ask first for existing aggregates and standard extracts.
No paid work, bespoke tabulation or fee is authorised without separate written
approval.

## Primary official sources

- [Ministry response 7255 — 2020–2023 flows](https://api.sejm.gov.pl/sejm/term10/interpellations/attachment/ATTDDEJZ5/i07255-o1.pdf)
- [Ministry response 17526 — realised 2025 excise](https://api.sejm.gov.pl/sejm/term10/interpellations/attachment/ATTDVKHSJ/i17526-o1.pdf)
- [Ministry of Finance — excise rates](https://www.podatki.gov.pl/akcyza/stawki-podatkowe/)
- [Ministry of Finance — broad device-group definition](https://www.podatki.gov.pl/akcyza/komunikaty-w-zakresie-podatku-akcyzowego)
- [AKC-4/R declaration and device-type field](https://api.sejm.gov.pl/eli/acts/DU/2025/698/text.pdf)
- [EU-CEG annual reporting fields](https://www.gov.pl/web/chemical/notification-of-electronic-cigarettes-and-refill-containers)
- [Polish official market monitoring](https://www.gov.pl/web/chemikalia/monitorowanie-rynku-e-papierosow)
- [Supreme Audit Office 2024 budget audit, Sejm print 1364](https://api.sejm.gov.pl/sejm/term10/prints/1364/1364.pdf)

The Supreme Audit Office PDF was retrieved on 2026-07-31 with SHA-256
`f1cab78703efe144f36c56a4c82252fef895925ab8dcf63bd27e1589232bb6cf`.

This preassessment is independent research. It is not Pixan Oy's official
position, an audit, valuation, legal opinion, investment recommendation or
lending recommendation.
