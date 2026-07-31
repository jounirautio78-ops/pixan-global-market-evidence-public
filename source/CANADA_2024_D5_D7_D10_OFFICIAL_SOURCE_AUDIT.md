# Canada 2024 — D5, D7 and D10 official-source audit

**Review date:** 2026-07-31
**Candidate:** `CA-2024-STATCAN-RCS-5619122`
**Decision:** D5 and D7 are `failed`; D10 remains `open`. The candidate remains `not_accepted` at 7/10.

## Established facts

- Statistics Canada's 2024 consumer-retail point estimate remains **CAD 1,219,160,000**.
- Health Canada's four 2024 Vaping Products Reporting Regulations categories reproduce **CAD 1,160,753,796.78** of manufacturer/importer net shipment value.
- The arithmetic residual is **CAD 58,406,203.22**, or **5.031747764%** of the consumer-retail estimate.
- The residual is not a retail margin: the two sources measure different transaction stages, populations and adjustment concepts.

## D5 — national channel coverage

The current Retail Commodity Survey states that it uses the same target population as the Monthly Retail Trade Survey. Current official documentation links the survey universe to NAICS 44–45, while official NAICS 459999 examples include electronic-cigarette and vaping-products retail. Internet, direct and mail-order sellers are classified by the merchandise sold.

Statistics Canada confirmed that the RCS target population covers NAICS
`441100` through `459993`. Official NAICS examples place electronic-cigarette
and vapour-liquid specialist retailing in `459999`, outside that range. The
specialist-channel gap is therefore confirmed and unquantified. D5 is failed.

## D7 — method and missingness

The RCS publishes its method and A–F quality flags, but not the exact coefficient of variation, standard error, imputation rate, response rate or annual covariance needed for commodity 5619122. All four 2024 quarterly values carry quality flag E.

Published quarterly coefficients of variation for the broader 56191 class
cannot be transferred to the narrower 5619122 commodity. Statistics Canada
confirmed that the Retail Commodity Program has no exact product-class CV,
imputation rate, standard error or annual covariance information beyond what
is published. Because all 12 months and all four quarters remain quality `E`
and the product-class annual error boundary is unavailable, D7 is failed.

## D10 — independent reconciliation

The Health Canada shipment series is an independent official route, but it measures manufacturer/importer net shipments to wholesalers and retailers. The RCS measures consumer-retail sales. The public evidence does not decompose the residual into destination coverage, reporters and non-filers, resubmissions, inventory, margins, returns, taxes and product-scope differences.

Public excise and annual-retail routes are too broad or use different periods
and accounting bases. Applying broad published industry margins would be an
unsupported category transfer and would overshoot the RCS point estimate. D10
can close only with a same-boundary official bridge or an independent
same-period point-of-sale total.

No further Statistics Canada follow-up is scheduled for D5 or D7. The Canada
programme now pivots to an independent rights-cleared POS or retailer-coverage
route with its own national denominator, method, missingness, tax basis and
same-boundary reconciliation.

Health Canada's first TVPA legislative review adds a historical 2021
institutional benchmark: CAD 2.04 billion for the Canadian vaping market, CAD
631 million for gas and convenience stores and approximately CAD 436 million
online. The report attributes the figures to a 2022 custom Euromonitor study.
The public report does not provide the underlying workbook or full method.

The 2021 Statistics Canada RCS observation is CAD 992.732 million, or 48.66%
of the Health Canada-published benchmark. The CAD 1.047268 billion difference
is strong evidence that the two public boundaries are not interchangeable and
that omitted channels may be material. It is not a valid 2024 uplift and cannot
be allocated solely to specialist retail, tax, online sales or methodology.
D5 remains failed and D10 remains open.

The public 2023 Survey of Household Spending microdata was also inspected.
Its released hierarchy combines tobacco products, smokers' supplies and
cannabis and does not expose vaping expenditure separately, so it cannot close
the vaping-specific value gap.

## Official sources

- [Statistics Canada — Retail Commodity Survey](https://www23.statcan.gc.ca/imdb/p2SV.pl?Function=getSurvey&SDDS=2008)
- [Statistics Canada — RCS target-population document](https://www23.statcan.gc.ca/imdb/p2SV.pl?Function=getSurvDocument&InstaId=1586471&Item_Id=1512385&a=1&ai=4)
- [Statistics Canada — Monthly Retail Trade Survey](https://www23.statcan.gc.ca/imdb/p2SV.pl?Function=getSurvey&SDDS=2406)
- [Statistics Canada — NAICS 459999 examples](https://www23.statcan.gc.ca/imdb/p3VD.pl?CLV=5&CPV=459999&CST=27012022&CVD=1370970&Function=getAllExample&MLV=5&TVD=1369825&V=438494&VST=27012022)
- [Statistics Canada — annual retail trade table 20-10-0084-01](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2010008401)
- [Statistics Canada — RCS data accuracy](https://www23.statcan.gc.ca/imdb/p2SV.pl?Function=getSurvDocument&InstaId=1586471&Item_Id=1586472&a=1&ai=38)
- [Health Canada — vaping-product sales](https://health-infobase.canada.ca/substance-use/vaping/sales/)
- [Health Canada — first TVPA legislative review](https://www.canada.ca/en/health-canada/programs/consultation-legislative-review-tobacco-vaping-products-act/final-report.html)
- [Statistics Canada — 2023 Survey of Household Spending public-use files](https://www150.statcan.gc.ca/n1/pub/62m0004x/2017001/SHS_EDM_2023.zip)
- [Vaping Products Reporting Regulations](https://laws-lois.justice.gc.ca/eng/regulations/SOR-2023-123/FullText.html)
- [Statistics Canada — annual retail trade table 20-10-0083-01](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=2010008301)

The privacy-safe official result is recorded in
[`CANADA_RCS_SCOPE_QUALITY_CLARIFICATION_2026-07-30.md`](CANADA_RCS_SCOPE_QUALITY_CLARIFICATION_2026-07-30.md).
No private correspondence is published.
