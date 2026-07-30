# Canada RCS tax-basis clarification

Reviewed: 2026-07-30

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

The response did not identify which federal, additional or provincial vaping
duties are represented by “additional duties”. It also did not expressly
extend the same treatment to monthly table `20-10-0080-01` or inactive legacy
quarterly table `20-10-0016-01`. Those points, the NAICS `459993`/`459999`
coverage conflict and the exact annual precision and imputation measures were
the subject of a no-charge follow-up sent on 2026-07-30.

The correspondence itself is retained outside the public repository. This note
records only the minimum non-personal methodological result needed to correct
the public evidence chain; it publishes no sender, recipient, address,
telephone number, message identifier or correspondence body.

## Decision effect

- Canada remains `not_accepted` at **7/10**.
- D8 remains **Passed** because the currency and the table-specific sales-tax
  and embedded-duty treatment are now explicit.
- D5, D7 and D10 remain open.
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
