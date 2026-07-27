# Five-country official-data method sprint

**Reviewed:** 2026-07-27

**Countries:** Austria (`AT`), Belgium (`BE`), Switzerland (`CH`),
Luxembourg (`LU`) and Norway (`NO`)

**Status:** reviewed acquisition and calculation plans; no new national retail
market value is computed

## Purpose and evidence boundary

This sprint converts five previously reviewed source leads into explicit,
country-specific evidence plans. A plan identifies an official holder, exact
fields, a reproducible calculation route and the evidence still needed. It is
not a market observation, a donor decision or a retail-market estimate.

The requests recorded below seek only non-confidential national aggregates.
No company-, brand-, product- or person-identifying data is requested. A sent
request is process evidence only: it is not a response and does not establish
that the requested fields exist.

Across all five countries:

- excise releases, regulatory sales reports, product notifications, customs
  flows and enforcement records are separate lenses and are never added
  together;
- customs values are border-stage values, not consumer turnover;
- notified products or operators describe reporting structure, not units sold;
- statutory tax rates do not establish that tax was collected;
- seizures are enforcement evidence, not lawful sales; and
- retail value remains `not_computed` until same-period volume, price, tax,
  channel and reconciliation boundaries are evidenced.

## Austria

### Verified official route

Austria has two complementary official routes.

1. Section 10d of the Tobacco and Non-Smoker Protection Act requires annual
   prior-year sales-volume reporting by brand and product type, together with
   consumer preferences, sales channels and market-study summaries. The
   Austrian Ministry and AGES administer the EU-CEG route.
2. From 1 April 2026, nicotine and nicotine-free e-liquids intended for vaping
   are subject to Austrian tobacco excise. The statutory rates are EUR 200 per
   litre from 1 April 2026 to 31 January 2027, EUR 230 per litre from
   1 February 2027 to 31 January 2028 and EUR 260 per litre from
   1 February 2028.

Primary method: `statutory_annual_sales_reporting`

Secondary methods: `excise_to_volume_reconstruction`,
`product_registry_plus_sales_request` and
`eu_tpd_annual_reporting_pattern`

### Reproducible calculations

For a period with one applicable rate:

`taxed litres = e-liquid-specific net assessed excise / applicable EUR per litre`

Mixed-rate years must be split before inversion. In 2027, January uses
EUR 200/litre and February–December use EUR 230/litre. Gross assessment,
collections, refunds, corrections, exports and timing differences must remain
separate.

The annual regulatory series must retain its reported unit and transaction
stage. It becomes a retail-value input only after reporting coverage,
duplicates/revisions, product scope, same-year tax-inclusive prices and an
independent retail reconciliation are documented.

### Missing evidence

- No public, reproducible annual Section 10d national aggregate was verified.
- The excise route starts in April 2026 and cannot backcast earlier years.
- Devices do not have a corresponding e-liquid excise volume.
- Product-register counts are assortment evidence, not sales.
- A vaping-specific official retail-price or POS series is still missing.

### Official sources

- [Austrian consolidated tobacco law and Section 10d](https://www.ris.bka.gv.at/GeltendeFassung.wxe?Abfrage=Bundesnormen&Gesetzesnummer=10010907)
- [Austrian Ministry EU-CEG reporting guidance](https://www.sozialministerium.gv.at/Themen/Gesundheit/Drogen-und-Sucht/Tabak-und-verwandte-Erzeugnisse/Meldeverpflichtungen-%28EU-CEG%29.html)
- [AGES public tobacco-product register](https://www.tabak.gv.at/8-veroeffentlichung)
- [Austrian consolidated tobacco-excise law](https://www.ris.bka.gv.at/GeltendeFassung.wxe?Abfrage=Bundesnormen&Gesetzesnummer=10004877)
- [Austrian Ministry of Finance implementation notice](https://www.bmf.gv.at/presse/pressemeldungen/2026/maerz-2026/nikotinprodukte.html)
- [Austrian Customs contact route](https://www.bmf.gv.at/themen/zoll/zollauskuenfte.html)

## Belgium

### Verified official route

Belgian EU-CEG guidance requires annual sales figures by product. The national
scope includes e-cigarettes and liquids with and without nicotine. A reported
sales-volume unit is the product unit: for example, one device, one cartridge
or one refill bottle. It is not automatically a millilitre measure or retail
turnover.

Belgian e-liquid excise took effect on 1 January 2024. The special excise rate
is EUR 0.15 per millilitre for nicotine and nicotine-free liquids within the
regulated vaping scope. Tax becomes due at release for consumption under the
W070/GestTab route. Disposable e-cigarettes were removed from the Belgian
market from 1 January 2025.

An official parliamentary answer reported approximately EUR 12.5 million of
e-liquid excise revenue for the first nine months of 2024 and cautioned that
pre-tax stockpiling and cross-border purchases affect interpretation. The
arithmetical equivalent is:

`EUR 12.5m / EUR 0.15 per ml = approximately 83.33m ml = 83,333 litres`

This is a rounded, revenue-implied January–September tax-volume indicator. It
is not a verified net release series, consumer sell-through, retail value or
full-year market measure.

Primary method: `statutory_annual_sales_reporting`

Secondary methods: `excise_to_volume_reconstruction`,
`product_registry_plus_sales_request` and
`eu_tpd_annual_reporting_pattern`

### Reproducible calculation route

The required first extract is:

`calendar year × product type × reported unit × national aggregate volume`

The extract must also state the pack multiplier, liquid millilitres where held,
nicotine scope, reporter/product counts, completeness, late or missing reports,
revisions and suppression. Only after those fields are known can devices,
pods/cartridges and refill liquids be kept disjoint and bridged to same-year
retail prices.

For a reconciled W070 period:

`taxed litres = e-liquid-specific net excise EUR / EUR 150 per litre`

The requested extract must distinguish assessed tax, cash collection, refunds,
credits, destruction, exports and inventory timing. The EU-CEG and W070 lenses
are alternative reconciliations and are not additive.

### Missing evidence

- No non-confidential annual national aggregate has yet been received.
- The published nine-month excise figure is rounded and affected by stockpiling,
  cross-border activity and collection timing.
- Product-level data may be confidential; a disclosure-controlled national
  aggregate is required.
- Reported product units cannot be converted to liquid volume without the
  product type, pack multiplier and fill quantity.
- Retail value and complete channel coverage remain unverified.

### Official sources

- [Belgian tobacco-regulation and notification page](https://www.health.belgium.be/fr/professionnels/entreprises/produits-consommation/reglementation-tabac)
- [Belgian EU-CEG e-cigarette guidance](https://www.health.belgium.be/en/organisation-policy/legislation-policy-documents/e-cigarette-notification-eu-ceg-belgian-guidelines)
- [Belgian Finance e-liquid excise guidance](https://finance.belgium.be/en/node/17000)
- [Belgian parliamentary record for the 2024 partial-period excise figure](https://www.lachambre.be/doc/CCRI/html/56/ic041x.html)
- [EU Tobacco Products Directive, Article 20(7)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex%3A32014L0040)

## Switzerland

### Verified official route

Swiss e-cigarette tobacco tax took effect on 1 October 2024. Nicotine products
for reusable e-cigarettes are taxed at CHF 0.20 per millilitre. Disposable
e-cigarette contents are taxed at CHF 1.00 per millilitre whether or not they
contain nicotine. The tax assessment base is millilitres and the official
classification separates the two rates.

The Tobacco Products Act and Ordinance also took effect on 1 October 2024 and
created the Tabacinfo notification route. Notifications can lag first market
placement and notified SKU counts are not sales.

Primary method: `excise_to_volume_reconstruction`

Secondary methods: `customs_trade_proxy` and
`product_registry_plus_sales_request`

### Reproducible calculations

`disposable taxed ml = disposable-category net tobacco tax CHF / 1.00`

`reusable nicotine taxed ml = reusable-nicotine-category net tobacco tax CHF / 0.20`

`litres = millilitres / 1,000`

The categories must be supplied separately because a combined receipt total
has no unique volume solution. The first period is only 1 October to
31 December 2024. Reusable nicotine-free liquid and empty hardware are outside
this excise inversion and need separate evidence.

A legal-market disposable-device lower bound can be calculated only after
taxed disposable millilitres are received:

`minimum disposable devices = disposable taxed ml / 2 ml statutory maximum`

This is a lower bound, not a point estimate; exact units require observed fill
volume or an official unit field.

### Missing evidence

- Category-specific e-cigarette tax receipts and millilitres are not yet public.
- Refunds, corrections, imports, domestic production and warehouse releases
  must be reconciled.
- Reusable nicotine-free liquid and hardware require separate scope.
- Tabacinfo counts can lag and do not establish sales.
- No official nationwide vaping-specific POS or retail-turnover series was
  verified.

### Official sources

- [FOCBS tobacco-tax guidance](https://www.bazg.admin.ch/dam/en/sd-web/GljEzThGISer/Tobacco%20tax.pdf)
- [FOCBS Tobacco Excise Tax page](https://www.bazg.admin.ch/en/tobacco-tax-domestic-companies)
- [FOCBS foreign-trade statistics contact and data route](https://www.bazg.admin.ch/bazg/en/home/topics/schweizerische-aussenhandelsstatistik/kontakt-aussenhandelsstatistik.html)
- [Swiss Tobacco Products Act information](https://www.bag.admin.ch/de/tabakproduktegesetz)
- [Swiss Tabacinfo notification FAQ](https://www.bag.admin.ch/de/faq-produktmeldung-und-tabacinfo)

## Luxembourg

### Verified official route

Luxembourg applies excise and source VAT to nicotine and nicotine-free
e-liquids intended for disposable or rechargeable vaping devices, including
specified DIY inputs. Excise is due when products are released for consumption
from the tax warehouse. The rate is EUR 0.12 per millilitre from
1 October 2024. The standard VAT rate in this regime is 17%. Products on sale
had to carry the Luxembourg fiscal mark from 1 April 2025.

Fiscal marks state both liquid volume and mandatory consumer selling price.
Business-to-business dispatches leaving Luxembourg are not domestic taxable
releases. This creates a strong volume route and a potential price/value route
if the authority can provide aggregate fiscal-mark fields.

Primary method: `excise_to_volume_reconstruction`

Secondary methods: `statutory_annual_sales_reporting`,
`product_registry_plus_sales_request` and
`eu_tpd_annual_reporting_pattern`

### Reproducible calculations

`taxed litres = e-liquid-specific net excise EUR / EUR 120 per litre`

If the authority supplies fiscal-mark quantities and price:

`marked consumer-price value = sum(marked pack quantity × mandatory marked price)`

The two calculations are not additive. Both require deductions or separate
fields for exports, B2B dispatches outside Luxembourg, destruction, refunds
and corrections. A fiscal-mark value still needs confirmation of sell-through
and the applicable period before it can be treated as retail turnover.

### Missing evidence

- No national monthly or annual aggregate extract has yet been received.
- The authority must provide the October–December 2024 partial-period extract,
  the first full-year 2025 extract and their revision/finality status.
- Fiscal-mark price/quantity aggregates may not be public.
- EU-CEG annual aggregate availability and reporting completeness remain
  unconfirmed.
- Devices without liquid require a separate unit and price route.

### Official sources

- [Luxembourg Customs e-liquid guidance](https://douanes.public.lu/fr/support/faq/e-liquides.html)
- [Luxembourg AC4 excise-declaration route](https://douanes.public.lu/fr/services-ligne/edouanes/LUCCS/ac4.html)
- [Luxembourg tobacco and related-product excise page](https://douanes.public.lu/fr/accises/tabacs-manufactures/produits-assimiles-tabacs-manufactures.html)
- [EU Tobacco Products Directive, Article 20(7)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex%3A32014L0040)

## Norway

### Verified official route

Current Norwegian guidance prohibits commercial import and sale of
nicotine-containing e-cigarettes and refill containers. Nicotine-free devices
and liquids may be supplied subject to the current flavour and product rules.
The Directorate of Health states that the new TPD/e-cigarette obligations,
including EU-CEG registration, are not yet applicable. Norway is therefore not
a current Article 20(7) annual-sales-reporting route.

Norwegian tax law lists an e-liquid-with-nicotine rate of NOK 5.38/ml for 2026,
but the Tax Administration says the tax has no practical effect until the
e-cigarette approval regime enters into force. The statutory rate must not be
treated as observed revenue or volume.

Statistics Norway table 08801 provides annual external-trade data. For modern
codes, the reviewed series starts in 2022. Code 85434000 has kilograms and a
supplementary device count; codes 24041200 and 24041900 are kilograms and have
broader scope than a verified e-liquid-only series.

Primary method: `regulated_supply_plus_enforcement`

Secondary method: `customs_trade_proxy`

### Reproducible calculation route

Once required fields exist:

`apparent device supply = imports + domestic production - exports - inventory change`

Current public data support only gross imports and exports. They do not support
a national sell-through result.

Excise inversion is permitted only if category-specific net receipts with
practical effect are supplied:

`taxed ml = net e-liquid excise revenue / applicable NOK per ml`

A zero, missing or suppressed record must not be inferred from the existence of
a prohibition or a statutory rate.

The kilograms reported for codes 24041200/24041900 must not be converted to
millilitres without official product-composition, packaging and density
evidence.

### Missing evidence

- No current Norwegian TPD/EU-CEG annual sales series exists.
- Lawful nicotine-free consumer sell-through, millilitres and retail value are
  missing.
- Domestic production, inventories, re-exports, duty-free, private import and
  illicit channels are not reconciled.
- Customs liquid codes are kilograms and broader than verified e-liquid scope.
- Enforcement and seizures must remain outside lawful-market totals.
- A nationwide annual vape price/POS series is missing.

### Official sources

- [Norwegian Directorate of Health e-cigarette guidance](https://www.helsedirektoratet.no/veiledere/tobakksskadeloven/e-sigaretter)
- [Norwegian Tax Administration tobacco and nicotine excise](https://www.skatteetaten.no/bedrift-og-organisasjon/avgifter/saravgifter/om/tobakk/)
- [Statistics Norway external-trade table 08801](https://www.ssb.no/en/statbank1/table/08801/)
- [Statistics Norway vaping-prevalence table 14451](https://www.ssb.no/en/statbank1/table/14451/)
- [Norwegian Directorate of Health contact route](https://www.helsedirektoratet.no/om-oss/kontakt-oss)

## Request record

On 2026-07-27, public-data requests were sent from the approved research
account to the following official functions:

| Country | Official function | Requested fields | Public status |
|---|---|---|---|
| AT | Austrian Customs and AGES tobacco coordination | Excise litres/receipts and annual regulatory sales aggregates | `sent` |
| BE | FPS Public Health EU-CEG/Enottab | Annual product units, liquid volume, scope and reporting completeness | `sent` |
| CH | FOCBS tobacco tax/statistics and FOPH Tabacinfo | Category tax base, trade fields and registry/sales availability | `sent` |
| LU | Customs tobacco/excise and Ministry of Health | Released litres, excise/VAT, fiscal-mark value and EU-CEG aggregates | `sent` |
| NO | Directorate of Health, Statistics Norway and Norwegian Customs | Lawful supply, trade-code fields, practical excise and separate enforcement data | `sent` |

Mailbox identifiers, correspondence bodies, personal metadata and non-public
files are deliberately excluded from this public repository.

## Promotion decision

All five countries are promoted from `reviewed_source_lead` to
`reviewed_method_plan` because the official holder, product boundary, required
fields, calculation method and limitations have now been reviewed. This
promotion does not change any market value:

- `retailValueStatus` remains `not_computed`;
- `eligibleForGlobalRollup` remains `false`;
- `donorAccepted` remains `false`; and
- the global retail-sales value remains `null`.
