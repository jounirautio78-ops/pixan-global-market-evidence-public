# UN195 country method-control map

**Reviewed:** 2026-07-27
**Release:** `2026.07.27-31`

## Purpose

The method-control map gives every UN195 sovereign state a visible research
status and a deterministic next evidence action. It is an acquisition and
calculation-control layer, not a table of 195 market values and not a claim
that 195 bespoke country methods have been completed.

The map is built from:

- the fixed UN193 + Holy See + State of Palestine catalogue;
- the open demographic, economic and queued proxy base;
- the reviewed Top 20 official-data request programme;
- the reviewed 15-country third-donor acquisition screen;
- current donor-control records;
- the reviewed public source-lead baseline;
- the reviewed five-country official-data method sprint;
- the EU Tobacco Products Directive Article 20(7) reporting pattern; and
- the controlled method and next-action taxonomies in
  `source/country-method-route-config.json`.

## Four disjoint assignment classes

| Assignment class | Countries | Meaning |
|---|---:|---|
| `reviewed_method_plan` | 28 | A country-specific vaping evidence route has been reviewed. This does not mean that a retail value has been computed or accepted. |
| `reviewed_source_lead` | 0 | No country is currently left in the intermediate reviewed-source-lead class. |
| `regional_tpd_pattern_only` | 15 | The EU Article 20(7) reporting pattern is relevant, but the national data holder, implementation, access and aggregates remain unverified. |
| `proxy_only_unscoped` | 152 | The country remains in the open context layer; no reviewed vaping-specific official calculation route has yet been scoped. |
| **Total** | **195** | The classes are mutually exclusive and exhaustive. |

The 28 reviewed country plans are:

`AE`, `AT`, `AU`, `BE`, `BR`, `CA`, `CH`, `CN`, `DE`, `DK`, `ES`, `FI`,
`FR`, `GB`, `ID`, `IT`, `JP`, `KR`, `LU`, `NL`, `NO`, `NZ`, `PH`, `PL`,
`RU`, `SA`, `SE` and `US`.

The five former source leads — `AT`, `BE`, `CH`, `LU` and `NO` — were
promoted to reviewed country plans on 2026-07-27 after their official holders,
required fields, calculation paths and limitations were reviewed. Their
retail values remain `not_computed`.

The 15 regional-pattern-only countries are:

`BG`, `CY`, `CZ`, `EE`, `GR`, `HR`, `HU`, `IE`, `LT`, `LV`, `MT`, `PT`,
`RO`, `SI` and `SK`.

Article 20(7) may also be a secondary route in EU countries already assigned
to a reviewed plan or source-lead class. The 15-country count above includes
only countries whose primary assignment is the regional pattern, so countries
are not double-counted.

## Reviewed country-method plans

The 28 plans retain their actual transaction stage:

- `CA`: official consumer-retail survey;
- `NZ`: specialist-retailer annual returns;
- `DE`, `FI`: excise release plus statutory sales reporting;
- `US`: manufacturer reporting plus independent POS validation;
- `CH`, `ES`, `ID`, `IT`, `LU`, `PH`, `PL`, `SA`: excise-to-volume reconstruction;
- `AT`, `BE`, `DK`, `FR`, `GB`, `SE`: statutory annual product-sales reporting;
- `NL`: product registry plus aggregate-sales request;
- `CN`: official production survey plus customs;
- `JP`, `KR`: customs trade proxy;
- `AU`, `NO`: regulated lawful supply plus enforcement;
- `RU`: marking-system retail withdrawals plus excise;
- `BR`: enforcement and trade evidence only; and
- `AE`: excise base linked to designated retail price.

Customs, tax, reporting, registration, manufacturer and enforcement routes are
not relabelled as consumer retail. A reviewed route is a controlled research
plan, not a completed value calculation.

The five-country sprint is documented in
`source/FIVE_COUNTRY_METHOD_SPRINT_2026-07-27.md`. Public-safe request records
show `sent` for all five countries. A sent request is not a response, and no
mailbox identifier, private correspondence or personal metadata is published.

## Fail-closed rules

1. A country with no reviewed vaping-specific route is labelled
   `proxy_only_unscoped`, not zero.
2. A reviewed source lead is not promoted to a precise calculation method
   until the relevant authority, fields, access and product scope are
   verified.
3. A regional directive creates a reporting pattern, not a public national
   dataset or national sales total.
4. A sent request is process evidence, not a response or a market value.
5. A tax, customs, shipment, registration or enforcement route retains its
   transaction stage and is never relabelled as consumer retail.
6. A model is `not_computed` until every required numeric input has a source,
   period, unit, product scope and tax/channel boundary.
7. No country is eligible for the global retail roll-up unless it separately
   passes the D1–D10 donor protocol. The current accepted-donor count remains
   0/3.

## Retail-value and donor boundary

Canada is the only country with an official consumer-retail point
estimate in this layer, but it remains quality-limited and outside the global
roll-up. New Zealand has an observed specialist-retailer subtotal, not
national retail coverage. The other 193 countries remain `not_computed` for
consumer-retail value.

Every country record exposes, separately:

- its assignment class and review level;
- primary and secondary methods;
- transaction stage;
- retail-value status;
- global-roll-up eligibility;
- donor-assessment state and donor acceptance;
- request state and last review date;
- provenance-basis identifiers; and
- the next evidence action and calculation boundary.

The provenance identifiers resolve to the exact public control sources listed
in the top-level `methodRouteControl.provenanceSources` register. This makes
the route assignment auditable without implying that the cited source already
contains a usable retail-market value.

## Poland calculation boundary

Poland uses an `excise_to_volume_reconstruction` route:

`taxed units = realised product-specific excise / statutory unit rate`

and, only when the missing inputs exist:

`retail-equivalent value = disjoint taxed units or millilitres × same-year, tax-consistent, channel-weighted retail price`

The existing 2025 back-solutions reproduce 4,382,500 taxed device units and
62,500 taxed component-set units for the period covered by the PLN 40 unit
rate. They are not a full-year device market, consumer sell-through or retail
value. No price is inserted and no Polish retail-equivalent value is computed
in this release.

## Germany calculation boundary

Germany uses an `excise_plus_statutory_sales` route. The official 2024 taxed
e-liquid volume of 1,284,000 litres is an anchor, not retail value. The
candidate package still requires same-year disjoint device and liquid volumes,
channel-weighted consumer prices, VAT/excise treatment, reporting coverage,
and an independent retail or rights-cleared POS reconciliation.

## Canada closure boundary

Canada remains a 7/10 candidate. The route map does not change D5, D7 or D10:

- D5 needs written confirmation of the NAICS 459993/459999 population
  boundary or quantified omitted channels.
- D7 needs a commodity-level annual uncertainty measure or defensible official
  interval; the published quality class `E` alone is not an exact annual error
  boundary.
- D10 needs a same-boundary independent retail total or a documented bridge
  from manufacturer/importer shipments to consumer retail.

This project is independent research and not an official Pixan Oy disclosure,
valuation, lending recommendation or investment recommendation.
