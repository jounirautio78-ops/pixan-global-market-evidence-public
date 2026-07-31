# Canada RCS tax-basis clarification

Reviewed: 2026-07-31

## Privacy-safe official clarification

Statistics Canada's Statistical Information Service provided a written
clarification on 2026-07-29 for Retail Commodity Survey table
`20-10-0071-01`:

- GST, HST, PST and QST are excluded from the published values;
- additional duties embedded in the retail price are included; and
- summing the four published quarters is the intended annual calculation for
  this table.

This table-specific clarification supersedes the project's earlier inference
that the 2023–2025 RCS values excluded excise. It does not change any published
quarter, annual sum or EUR conversion.

A further official clarification received on 2026-07-30 states that additional
duties can include the federal vaping duty, the additional vaping duty and
provincial vaping duties. The same basis applies to monthly table
`20-10-0080-01` vector `v1456717223` and archived quarterly table
`20-10-0016-01` vector `v1038567205`. The archived table was discontinued when
the survey moved to NAPCS 2022.

The follow-up also closed the remaining public-authority route negatively:
NAICS `459999` is outside the confirmed `441100`–`459993` target range, and the
Retail Commodity Program has no exact product-class precision, imputation,
standard-error or annual-covariance information beyond what is published. The
full privacy-safe result is recorded in
[`CANADA_RCS_SCOPE_QUALITY_CLARIFICATION_2026-07-30.md`](CANADA_RCS_SCOPE_QUALITY_CLARIFICATION_2026-07-30.md).

The correspondence itself is retained outside the public repository. This note
records only the minimum non-personal methodological result needed to correct
the public evidence chain; it publishes no sender, recipient, address,
telephone number, message identifier or correspondence body.

## Decision effect

- Canada remains `not_accepted` at **7/10**.
- D8 remains **Passed** because the currency and the table-specific sales-tax
  and embedded-duty treatment are now explicit.
- D5 and D7 are **Failed**; D10 remains **Open**.
- The CAD 58,406,203.22 retail-minus-shipment residual is not a retailer
  margin or a market range. The RCS retail figure includes embedded additional
  duties, while the Health Canada shipment measure excludes taxes and duties;
  that stage and tax-basis difference is unresolved and cannot be quantified
  from the current evidence.
- The donor gate remains **0/3** and global retail value remains
  `null/not_computed`.

## Public reference points

- Statistics Canada quarterly table 20-10-0071-01:
  https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2010007101
- Statistics Canada monthly table 20-10-0080-01:
  https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2010008001
- Retail Commodity Survey methodology:
  https://www23.statcan.gc.ca/imdb/p2SV.pl?Function=getSurvey&Id=1544050
- Health Canada vaping-sales series:
  https://health-infobase.canada.ca/substance-use/vaping/sales/

This note is independent research. It is not Pixan Oy's official position, an
audit, valuation, legal opinion, investment recommendation or lending
recommendation.
