# Investor / buyer disclosure control
# Sijoittaja- ja ostajatiedonantokontrolli

**As of / Tilanne:** 2026-07-31
**State / Tila:** `fail_closed`
**Machine-readable source / Koneluettava lähde:** `source/investor-disclosure-control.json`
**Public data copy / Julkinen datakopio:** `site/data/investor-disclosure-control.json`
**Schema / Skeema:** `source/schemas/investor-disclosure-control.schema.json`

## Purpose / Tarkoitus

This control permits the current published Pixan research to be reused for
initial lender, strategic-buyer, litigation-funder and adviser screening while
preventing private or rights-restricted material from leaking into the public
repository. It classifies recipients and content; it does **not** grant access,
approve a transaction, waive privilege or authorise onward disclosure.

Tämä kontrolli mahdollistaa nykyisen julkaistun Pixan-tutkimuksen käyttämisen
lainanantajan, strategisen ostajan, oikeudenkäyntirahoittajan ja neuvonantajan
alkuarvioissa estäen samalla yksityisen tai käyttöoikeuksiltaan rajoitetun
aineiston vuotamisen julkiseen repositorioon. Se luokittelee vastaanottajat ja
aineistot; se **ei** myönnä pääsyä, hyväksy transaktiota, luovu
salassapitoedusta eikä valtuuta edelleenluovutusta.

The published evidence centre is independent research. It is not Pixan Oy's
official position and is not an audit, valuation, legal opinion, investment
recommendation or lending recommendation.

Julkaistu evidenssikeskus on riippumatonta tutkimusta. Se ei ole Pixan Oy:n
virallinen kanta eikä tilintarkastus, arvonmääritys, oikeudellinen lausunto,
sijoitussuositus tai lainasuositus.

## Four access tiers / Neljä pääsytasoa

| Tier / Taso | Permitted purpose / Sallittu tarkoitus | Hard boundary / Kova raja |
| --- | --- | --- |
| **0 Public / Julkinen** | Initial screening using only the expressly mapped public assets. / Alkuarvio vain nimenomaisesti kartoitetuilla julkisilla aineistoilla. | Preserve source, date, method, uncertainty and disclaimer. Anything not allowlisted stays out. / Säilytä lähde, päivämäärä, menetelmä, epävarmuus ja vastuuvapauslauseke. Kaikki muu jää ulos. |
| **1 NDA diligence / NDA-tarkastus** | Separately approved, source-traceable and rights-cleared confirmatory summaries for named recipients. / Erikseen hyväksytyt, lähteisiin jäljitettävät ja käyttöoikeuksiltaan selvitetyt vahvistavat tiivistelmät nimetyille vastaanottajille. | Executed NDA, lawful purpose, minimum fields, licence, privacy and release authority must all pass. / Allekirjoitetun NDA:n, lainmukaisen tarkoituksen, vähimmäiskenttien, lisenssin, tietosuojan ja luovutustoimivallan on kaikkien läpäistävä. |
| **2 Restricted clean team / counsel / Rajoitettu clean team / oikeudellinen neuvonantaja** | Need-to-know review of separately stored competition-, dispute- or licence-sensitive diligence under counsel control. / Erikseen säilytetyn kilpailu-, riita- tai lisenssiarkaluonteisen aineiston need-to-know-tarkastus oikeudellisen neuvonantajan kontrollissa. | Counsel-approved perimeter, fields, recipients, privilege treatment, export limits, logs and destruction plan. / Oikeudellisen neuvonantajan hyväksymä raja, kentät, vastaanottajat, salassapitoetukäsittely, vientirajat, lokit ja hävityssuunnitelma. |
| **3 Board + counsel / Hallitus + oikeudellinen neuvonantaja** | Governance and final legal or transaction decisions in a separately controlled environment. / Hallinnolliset ja lopulliset oikeudelliset tai transaktiopäätökset erikseen kontrolloidussa ympäristössä. | Both named board authority and counsel approval; no inherited or blanket access. / Sekä nimetyn hallintoelimen toimivalta että oikeudellisen neuvonantajan hyväksyntä; ei periytyvää tai yleistä pääsyä. |

No restricted source material is embedded in or linked from this control.

Tähän kontrolliin ei ole sisällytetty eikä siitä ole linkitetty rajoitettua
lähdeaineistoa.

## Audiences / Vastaanottajaryhmät

| Audience / Vastaanottaja | Public use / Julkinen käyttö | Deeper-access condition / Syvemmän pääsyn ehto |
| --- | --- | --- |
| **Lender / Lainanantaja** | Credit, collateral and diligence screening. / Luotto-, vakuus- ja tarkastusalkuarvio. | Only information necessary for an identified credit decision after every applicable gate passes. / Vain yksilöityyn luottopäätökseen tarpeellinen aineisto kaikkien soveltuvien porttien jälkeen. |
| **Strategic buyer / Strateginen ostaja** | Acquisition screening. / Yritysoston alkuarvio. | Competition-sensitive information requires counsel-led clean-team controls. / Kilpailuarkaluonteinen aineisto edellyttää oikeudellisen neuvonantajan johtamaa clean team -kontrollia. |
| **Litigation funder / Oikeudenkäyntirahoittaja** | Screening of the published patent, evidence and proceeding record. / Julkaistun patentti-, evidenssi- ja menettelyaineiston arvio. | Counsel first decides privilege, work product, permitted use and litigation-control conditions. / Oikeudellinen neuvonantaja ratkaisee ensin salassapitoedun, work product -suojan, sallitun käytön ja oikeudenkäynnin määräysvaltaehdot. |
| **Adviser / Neuvonantaja** | Professional review within a documented mandate. / Ammatillinen tarkastus dokumentoidun toimeksiannon rajoissa. | No broader rights than the appointing principal; adviser must be named, bound and technically restricted. / Ei toimeksiantajaa laajempia oikeuksia; neuvonantajan on oltava nimetty, sitoutettu ja teknisesti rajattu. |

## Material facts that must travel with the favourable case
## Olennaiset seikat, jotka on esitettävä myönteisen aineiston rinnalla

The access model must never be used to conceal a material limitation. The
following current published facts are minimum public disclosures:

Pääsymallia ei saa koskaan käyttää olennaisen rajoituksen salaamiseen. Seuraavat
nykyiset julkaistut faktat ovat julkisen tiedonannon vähimmäistaso:

1. The evidence centre is independent and is not Pixan Oy's official position.
   Evidenssikeskus on riippumaton eikä ole Pixan Oy:n virallinen kanta.
2. The package is not an audit, company or collateral valuation, legal opinion,
   investment recommendation or lending recommendation.
   Paketti ei ole tilintarkastus, yritys- tai vakuusarvon määritys,
   oikeudellinen lausunto, sijoitussuositus tai lainasuositus.
3. As of 2026-07-31, the donor gate is **0/3** and the global vaping retail
   value is **`null/not_computed`**.
   Tilanteessa 30.7.2026 donor-portti on **0/3** ja maailman
   sähkötupakkavähittäisarvo on **`null/not_computed`**.
4. Tax, customs, shipment, registration, structural, modelled and proxy
   observations are not observed consumer-retail sales. Missing evidence is not
   zero.
   Vero-, tulli-, toimitus-, rekisteri-, rakenne-, mallinnettu ja proxy-evidenssi
   ei ole havaittua kuluttajavähittäismyyntiä. Puuttuva evidenssi ei ole nolla.
5. The EPO central record says the patent was maintained as amended, while
   national validation, renewal, operative claims, title and enforceability are
   country-specific. A family-record count is not a current-country count.
   EPO:n keskitetyn rekisterin mukaan patentti pysytettiin muutettuna, mutta
   kansallinen validointi, vuosimaksut, sovellettavat vaatimukset, omistus ja
   täytäntöönpanokelpoisuus ovat maakohtaisia. Patenttiperheen tietuemäärä ei ole
   nykyisten patenttimaiden määrä.
6. A decision or technical finding in one country does not itself establish
   validity, infringement, damages or enforceability elsewhere.
   Yhden maan ratkaisu tai tekninen havainto ei yksin osoita pätevyyttä,
   loukkausta, vahingonkorvausta tai täytäntöönpanokelpoisuutta muualla.
7. As of 2026-07-31, no tracked vendor is scored and no purchase is authorised.
   Receipt of a document, quote or sample is not proof of completeness, method
   quality or disclosure rights.
   Tilanteessa 29.7.2026 yhtäkään seurattua toimittajaa ei ole pisteytetty eikä
   ostoa ole valtuutettu. Asiakirjan, tarjouksen tai näytteen vastaanotto ei
   osoita täydellisyyttä, menetelmän laatua tai luovutusoikeuksia.
8. The dashboard is release **2026.07.31-38**. The six downloadable files
   remain the reviewed **2026.07.31-37** daily snapshot. The downloadable
   package is generated at most once per Asia/Nicosia calendar day, and each
   surface retains its own visible version.
   Dashboard on julkaisu **2026.07.31-38**. Kuusi ladattavaa tiedostoa pysyvät
   tarkistettuna **2026.07.31-37**-päiväsnapshotina. Ladattava paketti
   muodostetaan enintään kerran Asia/Nicosia-kalenteripäivässä, ja kumpikin
   pinta säilyttää oman näkyvän versionsa.
9. Failed gates, lapses, challenges, unresolved proceedings, conflicts and later
   corrections travel with favourable evidence.
   Hylätyt portit, raukeamiset, riitautukset, ratkaisemattomat menettelyt,
   ristiriidat ja myöhemmät korjaukset esitetään myönteisen evidenssin rinnalla.

If a material fact cannot lawfully be disclosed to an otherwise entitled
decision-maker, do not send a favourable-only subset. Pause or narrow the
decision package.

Jos olennaista seikkaa ei voida lainmukaisesti luovuttaa siihen muutoin
oikeutetulle päätöksentekijälle, älä lähetä vain myönteistä osajoukkoa. Keskeytä
tai rajaa päätöspaketti.

## Existing assets mapped to the public tier
## Nykyiset julkiselle tasolle kartoitetut aineistot

| Asset group / Aineistoryhmä | Public paths / Julkiset polut | Version or boundary / Versio tai raja |
| --- | --- | --- |
| Dashboard / Dashboard | `site/index.html` | `2026.07.31-38` |
| Change log / Muutosloki | `site/data/changelog.json` | `2026.07.31-38` |
| Daily manifest / Päivämanifesti | `site/data/bank-package-manifest.json` | `2026.07.31-37` |
| Concise and extended decks / Suppeat ja laajat dekit | `site/downloads/pixan-bank-deck-short-en.pptx`, `...-fi.pptx`, `site/downloads/pixan-bank-deck-large-en.pptx`, `...-fi.pptx` | `2026.07.31-37` |
| Evidence Registers / Evidence Registerit | `site/downloads/pixan-bank-evidence-register-en.xlsx`, `...-fi.xlsx` | `2026.07.31-37` |
| Structured market controls / Rakenteiset markkinakontrollit | `site/data/atlas.json`, `countries.csv`, `evidence.csv`, `market-values.*`, `evidence-lanes.json`, `donor-cockpit.json`, `country-scenarios.json`, `global-base-layer.*`, `fx-rates.json`, `third-donor-screen.json` | Each asset's own `asOf` / Kunkin aineiston oma `asOf` |
| Patent record / Patenttitietue | `site/data/patent-history.json`, `site/data/patent-family.csv` | Embedded review dates / Sisäiset tarkistuspäivät |
| Vendor control / Toimittajakontrolli | `site/data/vendor-response-control.json`, `.csv` | `2026-07-31` |
| Request routes and templates / Pyyntöreitit ja -mallit | `site/data/top20-data-request-routes.*`, `site/downloads/data-request-template-en.txt`, `...-fi.txt` | Embedded status dates / Sisäiset tilapäivät |
| Paid-data procurement guide / Maksullisen datan hankintaopas | `site/downloads/pixan-paid-data-procurement-fi-en.xlsx` | Current published workbook / Nykyinen julkaistu työkirja |

The machine-readable JSON contains the complete exact path list and the
limitation attached to each group.

Koneluettava JSON sisältää täydellisen täsmällisen polkulistan ja jokaiseen
ryhmään liittyvän rajauksen.

## Never publish / Ei koskaan julkiseksi

- Named potential infringers, targets, product-to-claim allegations or target
  prioritisation.
  Nimetyt mahdolliset loukkaajat, kohteet, tuote–vaatimus-väitteet tai
  kohdepriorisointi.
- Legal advice, claim charts, enforcement plans, forum or settlement strategy
  and counsel work product.
  Oikeudellinen neuvonta, claim chart -vertailut, täytäntöönpanosuunnitelmat,
  foorumi- tai sovintostrategia ja oikeudellisen neuvonantajan work product.
- Negotiation floors, reservation prices, minimum licensing terms, bid ranges,
  target returns or private valuation inputs.
  Neuvottelujen alarajat, vähimmäishinnat, lisensoinnin vähimmäisehdot,
  tarjoushaarukat, tuottotavoitteet tai yksityiset arvonmäärityssyötteet.
- Personal data, private contact details, recipient lists or device and mailbox
  identifiers.
  Henkilötiedot, yksityiset yhteystiedot, vastaanottajalistat tai laite- ja
  postilaatikkotunnisteet.
- Private correspondence, message bodies, attachments, drafts, headers or
  precise message metadata.
  Yksityinen kirjeenvaihto, viestirungot, liitteet, luonnokset, otsaketiedot tai
  tarkka viestimetadata.
- Licensed raw data, record-level samples, workbooks, extracts or derived
  tables without written rights for that exact public use.
  Lisensoitu raakadata, tietuetason näytteet, työkirjat, otteet tai johdetut
  taulukot ilman kirjallista oikeutta juuri kyseiseen julkiseen käyttöön.
- Private quotes, pricing signals, negotiated or renewal terms and licence
  drafts.
  Yksityiset tarjoukset, hintasignaalit, neuvotellut ehdot, uusimisehdot ja
  lisenssiluonnokset.
- Privileged material, private board, ownership, financing, customer, contract
  or transaction records.
  Salassapitoedun alainen aineisto sekä yksityiset hallitus-, omistus-,
  rahoitus-, asiakas-, sopimus- tai transaktiotiedot.
- Non-public or unverified tests, pilots, customer claims or commercial proof.
  Ei-julkiset tai vahvistamattomat testit, pilotit, asiakasväitteet tai
  kaupallinen näyttö.
- Credentials, private data-room links, local paths, internal logs and security
  configuration.
  Tunnukset, yksityiset datahuonelinkit, paikalliset polut, sisäiset lokit ja
  turvallisuusasetukset.
- Any invented market value, customer fact, patent-country count, damages,
  forecast or other unsupported assertion.
  Mikä tahansa keksitty markkina-arvo, asiakastieto, patenttimaiden määrä,
  vahinko, ennuste tai muu tukematon väite.

## Vendor licence and privilege safeguards
## Toimittajalisenssin ja salassapitoedun suojat

### Vendor licence / Toimittajalisenssi

Receipt, a sample or payment does not create redistribution rights. Before any
deeper release, obtain written terms covering the named recipients, purpose,
data-room use, derived outputs, adviser use, AI processing, export, retention
and deletion. Silence, a quote or a sample is insufficient. If rights are
unclear, exclude the vendor material and every non-permitted derivative.

Vastaanotto, näyte tai maksu ei luo edelleenjakamisoikeutta. Ennen syvempää
luovutusta hanki kirjalliset ehdot nimetyistä vastaanottajista,
käyttötarkoituksesta, datahuonekäytöstä, johdetuista tuotoksista,
neuvonantajakäytöstä, tekoälykäsittelystä, viennistä, säilytyksestä ja poistosta.
Hiljaisuus, tarjous tai näyte ei riitä. Jos oikeudet ovat epäselvät, sulje
toimittaja-aineisto ja kaikki luvattomat johdannaiset pois.

### Privilege and work product / Salassapitoetu ja work product

Counsel decides classification and whether disclosure would waive protection.
Public evidence, business analysis and legal advice stay in separate stores and
indexes. Legal advice is never copied into the dashboard, decks, public release
logs or this control.

Oikeudellinen neuvonantaja ratkaisee luokituksen ja sen, luovutaanko suojasta
luovutuksen seurauksena. Julkinen evidenssi, liiketoiminta-analyysi ja
oikeudellinen neuvonta pidetään erillisissä säilytyspaikoissa ja indekseissä.
Oikeudellista neuvontaa ei kopioida dashboardiin, dekkeihin, julkisiin
luovutuslokeihin tai tähän kontrolliin.

## Hard gates before deeper access
## Kovat portit ennen syvempää pääsyä

All gates applicable to the requested tier must have current documented
evidence:

Kaikista pyydettyyn tasoon soveltuvista porteista on oltava ajantasainen
dokumentoitu näyttö:

1. Counterparty identity, role, mandate and named recipients.
   Vastapuolen henkilöllisyys, rooli, toimeksianto ja nimetyt vastaanottajat.
2. Lawful decision purpose, minimum necessary fields, jurisdictions and period.
   Lainmukainen päätöstarkoitus, pienin tarpeellinen kenttäjoukko, valtiot ja
   ajanjakso.
3. Executed NDA or equivalent binding confidentiality duty.
   Allekirjoitettu NDA tai vastaava sitova salassapitovelvoite.
4. Balanced material-fact checklist; no favourable-only subset.
   Tasapuolinen olennaisten seikkojen tarkistuslista; ei vain myönteistä
   osajoukkoa.
5. Source, method, date, assumption, confidence, gap and exact-version review.
   Lähteen, menetelmän, päivämäärän, oletuksen, luottamustason, puutteen ja
   täsmällisen version tarkastus.
6. Written vendor and third-party rights for the exact intended use.
   Kirjalliset toimittaja- ja kolmannen osapuolen oikeudet juuri aiottuun
   käyttöön.
7. Counsel privilege and work-product review for restricted legal material.
   Oikeudellisen neuvonantajan salassapitoetu- ja work product -tarkastus
   rajoitetulle oikeudelliselle aineistolle.
8. Privacy minimisation and redaction against the final files.
   Tietojen minimointi ja peittäminen lopullisista tiedostoista.
9. Competition-law and clean-team protocol, or counsel's written
   not-applicable decision.
   Kilpailuoikeus- ja clean team -protokolla tai oikeudellisen neuvonantajan
   kirjallinen ei-sovellu-päätös.
10. Named accounts, least privilege, expiry, export control, logging and
    revocation test.
    Nimetyt tilit, vähimmät oikeudet, päättymisaika, vientikontrolli, lokitus ja
    peruutustesti.
11. Dated release authority identifying recipients, purpose, tier, files and
    versions or hashes; board+counsel requires both authorities.
    Päivätty luovutustoimivalta, joka yksilöi vastaanottajat, tarkoituksen,
    tason, tiedostot ja versiot tai tiivisteet; hallitus + oikeudellinen
    neuvonantaja -taso edellyttää molempia toimivaltuuksia.
12. Release register, access review, expiry and verified return or deletion
    plan.
    Luovutusrekisteri, pääsyn tarkistus, päättymisaika ja varmennettu palautus-
    tai poistosuunnitelma.

## Decision rule / Päätössääntö

The default and fallback tier is always **public**. A recipient advances only
when **all** gates required for the requested tier pass for that exact
recipient, purpose, file set and time period. Missing, expired, conflicting or
undocumented “not applicable” evidence is a failure. There is no automatic
promotion, blanket access, partial override or inherited right.

Oletus- ja fallback-taso on aina **julkinen**. Vastaanottaja etenee vain, kun
**kaikki** pyydetyn tason portit läpäisevät juuri kyseisen vastaanottajan,
tarkoituksen, tiedostojoukon ja ajanjakson osalta. Puuttuva, vanhentunut,
ristiriitainen tai dokumentoimaton “ei sovellu” -näyttö on hylkäys. Automaattista
siirtymää, yleistä pääsyä, osittaista ohitusta tai periytyvää oikeutta ei ole.

Revalidate whenever the recipient, adviser, purpose, jurisdiction, field set,
platform, NDA, licence, mandate, privilege assessment, access period, material
facts or file version changes.

Arvioi portit uudelleen aina, kun vastaanottaja, neuvonantaja, tarkoitus, valtio,
kenttäjoukko, alusta, NDA, lisenssi, toimeksianto, salassapitoetuarvio,
pääsyaika, olennaiset faktat tai tiedostoversio muuttuvat.
