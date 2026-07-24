# Comparable donor-market acceptance protocol

Version 1.0 · reviewed 2026-07-24

This protocol determines whether a country-year market value may be used as a comparable donor in the Pixan Global Market Evidence Atlas. It is a research-control rule, not a valuation method, investment recommendation or Pixan Oy statement.

The global estimate gate requires at least three accepted donor markets **and**
documented regional and regulatory-archetype coverage. A candidate is accepted
only when every criterion below is passed with source-linked evidence. A failed
or unresolved criterion keeps the candidate outside the donor count. Rejected
candidates may still remain useful as official lower bounds, institutional
benchmarks, shipment proxies, manufacturer-reported series or model checks.

## Acceptance criteria

| ID | Requirement | Why it matters |
|---|---|---|
| D1 | The figure covers one complete, identified calendar year. | Partial periods and mixed years distort country comparisons. |
| D2 | The transaction level is consumer retail sell-through. | Manufacturer shipments, wholesale invoices and tax receipts are not consumer spending. |
| D3 | Devices and consumables are both covered, or their split is explicitly reconciled. | A liquid-only or hardware-only figure is not a complete vaping market. |
| D4 | Heated tobacco, herbal smoking, smokeless tobacco and other adjacent products are excluded or separately quantified. | Mixed product definitions cannot be scaled safely. |
| D5 | Nationwide channels are covered, or every material channel gap is quantified. | Specialist-retailer-only or threshold-limited reporting may be a lower bound. |
| D6 | Supply stages are de-duplicated. | Adding manufacturer, importer, wholesaler and retailer revenue can count the same product several times. |
| D7 | Method, missingness, revisions and data-quality warnings are documented. | A headline value without its error boundary cannot support lender-grade scaling. |
| D8 | Currency and tax basis are explicit. | Values including and excluding VAT/GST or excise are not directly comparable. |
| D9 | A public aggregate and reproducible source chain are available. | A reviewer must be able to trace the claim without receiving private or unlicensed raw records. |
| D10 | The value is reconciled against an independent route or direct official validation. | A second, non-duplicative route helps detect scope and reporting errors. |

## Decision rules

1. `accepted` means D1–D10 all pass.
2. `not_accepted` means at least one criterion fails or remains open.
3. `open` is not treated as a partial pass.
4. The donor count is the number of accepted candidate country-years, not the number of monetary observations.
5. Alternative estimates, taxes, physical volumes and supply-stage values are never added together merely to increase coverage.
6. Candidate status is reviewed when a new official release, methodology note or independent reconciliation becomes available.
7. Passing three country-year candidates does not by itself release a global
   value: the regional and regulatory-archetype coverage gates must also pass.
8. Missing or invalid scenario inputs return `not_computed`; they are never
   converted to zero.

## Finnish summary / suomenkielinen yhteenveto

Vertailukelpoinen luovuttajamarkkina hyväksytään vain, jos kaikki kymmenen ehtoa täyttyvät lähteistetysti. Luvun pitää koskea kokonaista kalenterivuotta ja kuluttajavähittäismyyntiä, kattaa laitteet ja kulutustarvikkeet yhteensopivasti, rajata viereiset tuoteryhmät, kattaa olennaiset myyntikanavat, estää toimitusketjun kaksoislaskenta sekä kuvata menetelmä, puuttuvuus, valuutta- ja veroperusta, julkinen toistettavuus ja riippumaton täsmäytys. Epäselvä ehto ei ole osittainen hyväksyntä. Maailman kokonaisluku edellyttää lisäksi vähintään kolmea hyväksyttyä luovuttajaa sekä alueellisen ja sääntelyarkkityyppien peiton läpäisyä. Puuttuvaa syötettä ei käsitellä nollana.

## Publication boundary

The public repository stores only reviewed aggregates, methodology, source URLs and reproducibility metadata. It must not publish respondent names, addresses, licence identifiers, private correspondence, confidential vendor data or licensed raw datasets without an explicit publication right and separate review.
