# Canada RCS scope and quality clarification

Reviewed: 2026-07-31

## Privacy-safe official result

Statistics Canada's Statistical Information Service provided a further written
clarification on 2026-07-30 for the Retail Commodity Survey and NAPCS 5619122.
The official result is recorded here without publishing the correspondence or
any personal or message metadata:

- additional duties embedded in the retail price can include the federal
  vaping duty, the additional vaping duty and provincial vaping duties;
- the same sales-tax and embedded-duty basis applies to monthly table
  `20-10-0080-01` vector `v1456717223` and archived quarterly table
  `20-10-0016-01` vector `v1038567205`;
- the archived table was discontinued when the survey moved to NAPCS 2022;
- the Retail Commodity Survey target population covers NAICS `441100` through
  `459993`; and
- the Retail Commodity Program has no product-class-level coefficient of
  variation, imputation rate, standard error or annual covariance information
  beyond what is published.

Official NAICS examples place electronic-cigarette and vapour-liquid specialist
retailing in `459999`. Because `459999` is outside the confirmed RCS
target-population endpoint, the specialist-channel gap is now confirmed rather
than merely unresolved. Its monetary size is not quantified.

## D1-D10 decision effect

- Canada remains `not_accepted` at **7/10 passed**.
- D5 changes from **Open** to **Failed**: a directly relevant specialist
  channel falls outside the confirmed target range and the gap is not
  quantified.
- D7 changes from **Open** to **Failed**: every 2024 monthly and quarterly
  observation remains quality `E`, while the exact product-class precision,
  missingness and annual uncertainty measures are unavailable from the
  programme.
- D8 remains **Passed** and is stronger: the treatment now applies consistently
  to the reviewed quarterly, monthly and archived vectors, and the possible
  embedded vaping-duty components are explicit.
- D10 remains **Open**: the retail-to-shipment residual has not been
  independently decomposed.

The CAD 1,219,160,000 point estimate and EUR 822,583,715.21 comparison do not
change. The donor gate remains **0/3** and global retail value remains
`null/not_computed`.

## Research consequence

No further Statistics Canada follow-up is scheduled for D5 or D7. The remaining
Canada route is an independent, rights-cleared point-of-sale or retailer
coverage series with a documented national channel denominator, data-quality
method and tax basis, followed by a non-duplicative bridge to the RCS and Health
Canada shipment series. This route may validate a separate Canada candidate; it
cannot retrospectively create unavailable RCS product-class precision data.

## Public reference points

- Statistics Canada quarterly table 20-10-0071-01:
  https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2010007101
- Statistics Canada monthly table 20-10-0080-01:
  https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2010008001
- Retail Commodity Survey methodology:
  https://www23.statcan.gc.ca/imdb/p2SV.pl?Function=getSurvey&Id=1544050
- Statistics Canada NAICS 459999 examples:
  https://www23.statcan.gc.ca/imdb/p3VD.pl?CLV=5&CPV=459999&CST=27012022&CVD=1370970&Function=getAllExample&MLV=5&TVD=1369825&V=438494&VST=27012022
- Health Canada vaping-sales series:
  https://health-infobase.canada.ca/substance-use/vaping/sales/

The correspondence is retained outside the public repository. This note
contains no sender, recipient, address, telephone number, message identifier or
correspondence body.

This note is independent research. It is not Pixan Oy's official position, an
audit, valuation, legal opinion, investment recommendation or lending
recommendation.
