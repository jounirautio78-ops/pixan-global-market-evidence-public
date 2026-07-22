"use strict";

(() => {
  const STORAGE_KEY = "pixan-global-market-evidence-language";
  const SUPPORTED = new Set(["en", "fi"]);

  const STATIC_PAIRS = [
    ["Siirry sisältöön", "Skip to content"],
    ["Riippumaton tutkimuskeskus", "Independent research center"],
    ["Riippumaton julkisiin lähteisiin perustuva sähkötupakka- ja e-nestemarkkinan evidenssikeskus.", "Independent public-source evidence center for global vaping-device and e-liquid markets."],
    ["Riippumaton, lähteistetty tarkistusmuistio Pixaniin liittyvästä maailmanlaajuisesta sähkötupakkamarkkinaevidenssistä.", "Independent, source-linked review brief for Pixan-related global vaping-market evidence."],
    ["Lainanantajan ja ostajan tarkistus | Pixan Global Market Evidence", "Lender & Buyer Review | Pixan Global Market Evidence"],
    ["Ei Pixan Oy:n virallinen julkaisu", "Independent · not a Pixan Oy disclosure"],
    ["Lainanantajan / ostajan näkymä", "Lender / buyer view"],
    ["Toimita aineistoa", "Submit material"],
    ["Päänavigaatio", "Main navigation"],
    ["Tilannekuva", "Overview"],
    ["195 maata", "195 countries"],
    ["Evidenssi", "Evidence"],
    ["Patentti ja Saksa", "Patent and Germany"],
    ["Menetelmä", "Method"],
    ["Aineistokanava", "Material intake"],
    ["Global vape market intelligence · vain julkiset lähteet", "Global vape market intelligence · public evidence only"],
    ["Markkinaväite on hyödyllinen vasta, kun sen voi jäljittää lähteeseen.", "A market claim becomes useful only when it can be traced to a source."],
    ["Rakennamme 195 maan vertailukelpoista kuvaa sähkötupakka-, laite-, podi- ja e-nestemarkkinoista. Virallinen myynti, verovolyymi, tullivirta ja mallinnus pidetään tarkoituksella erillään.", "We are building a comparable 195-country view of vaping devices, pods and e-liquids. Official sales, taxable volume, customs flows and modelling are kept deliberately separate."],
    ["Avaa maakohtainen atlas", "Open country atlas"],
    ["Jaettava tarkistusmuistio", "Shareable review brief"],
    ["Lataa CSV", "Download CSV"],
    ["Lataa JSON", "Download JSON"],
    ["Julkaisun rajaus", "Publication boundary"],
    ["Riippumaton tutkimusprojekti", "Independent research project"],
    ["Tämä sivusto ei edusta Pixan Oy:tä eikä sen virallista kantaa. Se ei ole tarjous, arvonmääritys, sijoitussuositus, tilintarkastus tai oikeudellinen lausunto.", "This site does not represent Pixan Oy or its official position. It is not an offer, valuation, investment recommendation, audit or legal opinion."],
    ["Päivitetty", "Updated"],
    ["· lähdesnapshot", "· source baseline"],
    ["Aineiston päämittarit", "Dataset summary"],
    ["Lainanantajatasoinen lähtökohta", "Lender-grade starting point"],
    ["Lender-tasoinen lähtökohta", "Lender-grade starting point"],
    ["Lender-grade lähtökohta", "Lender-grade starting point"],
    ["Yksi numero ei ole maailmanmarkkina", "One number is not the global market"],
    ["Atlas kertoo myös sen, mitä emme vielä tiedä. Puuttuva havainto on puuttuva — ei nolla.", "The atlas also shows what is not yet known. A missing observation is missing—not zero."],
    ["Kattavuus lähdetyypeittäin", "Coverage by source type"],
    ["Maailman evidenssipeitto", "Global evidence coverage"],
    ["Maa voi kuulua useaan luokkaan", "A country may appear in several categories"],
    ["Laatu ennen määrää", "Quality before quantity"],
    ["Todistetasot", "Evidence grades"],
    ["Suora viranomaisankkuri", "Direct official anchor"],
    ["Myynti, toimitus, verototeuma tai verovolyymi.", "Sales, deliveries, realised tax or taxable volume."],
    ["Virallinen proxy", "Official proxy"],
    ["Tulli- tai muu rajavirta; ei kuluttajamyynti.", "Customs or another border flow; not consumer sales."],
    ["Malli tai täydentävä lähde", "Model or supporting source"],
    ["Oletukset ja vaihteluväli näytettävä.", "Assumptions and range must be shown."],
    ["Ei hyväksyttyä numeerista ankkuria", "No accepted numeric anchor"],
    ["Tutkimusjono, ei nollamarkkina.", "Research queue, not a zero market."],
    ["Neuvotteluvalmius", "Diligence readiness"],
    ["Avoimet portit", "Open gates"],
    ["Tärkein ero", "The key distinction"],
    ["Mitä kukin mittari oikeasti todistaa?", "What does each measure actually establish?"],
    ["Virallinen myynti / toimitus", "Official sales / deliveries"],
    ["Lähimpänä markkina-arvoa, mutta toimitusmyynti ei aina ole kassamyyntiä.", "Closest to market value, although deliveries do not always equal cash sales."],
    ["Vero ja verovolyymi", "Tax and taxable volume"],
    ["Vahva laillisen markkinan ankkuri. Ei automaattisesti sisällä laitteita tai harmaata kauppaa.", "A strong lawful-market anchor. It does not automatically include devices or illicit trade."],
    ["Tullivirta", "Customs flow"],
    ["Rajalla mitattu arvo tai määrä. Kotimainen tuotanto, katteet ja varastot puuttuvat.", "Value or volume measured at the border. Domestic production, margins and inventories are excluded."],
    ["Mallinnettu vaihteluväli", "Modelled range"],
    ["Yhdistää käyttäjät, kulutuksen ja hinnat. Tulos riippuu oletuksista.", "Combines users, consumption and prices. The result depends on assumptions."],
    ["UN 193 + Pyhä istuin + Palestiina", "UN 193 + Holy See + State of Palestine"],
    ["195 maan markkina-atlas", "195-country market atlas"],
    ["Valitse maa nähdäksesi nykyisen ankkurin, puutteet, lähteet ja seuraavan tutkimusreitin.", "Select a country to inspect its current anchor, gaps, sources and next research route."],
    ["Maataulukon suodattimet", "Country table filters"],
    ["Hae maata", "Search countries"],
    ["Hae maata tai ISO-koodia…", "Search country or ISO code…"],
    ["Alue", "Region"],
    ["Kaikki alueet", "All regions"],
    ["Todistetaso", "Evidence grade"],
    ["Kaikki todistetasot", "All evidence grades"],
    ["A · viranomaisankkuri", "A · official anchor"],
    ["B · virallinen proxy", "B · official proxy"],
    ["C · mallinnus", "C · model"],
    ["D · tutkimusjono", "D · research queue"],
    ["Maa", "Country"],
    ["Paras näyttö", "Best evidence"],
    ["Peitto", "Coverage"],
    ["Keskeinen havainto", "Key finding"],
    ["Avaa", "Open"],
    ["Yksikään maa ei vastaa valittuja suodattimia.", "No country matches the selected filters."],
    ["Evidenssirekisteri", "Evidence register"],
    ["Väite → lähde", "Claim → source"],
    ["Jokainen julkinen väite sidotaan lähteeseen ja rajaukseen. A-luokka kertoo lähteen virallisuudesta, ei koko maan täydellisestä myyntipeitosta.", "Every public claim is linked to a source and scope. Grade A describes source quality, not complete national sales coverage."],
    ["Hae evidenssiä", "Search evidence"],
    ["Hae lähdettä, maata tai mittaria…", "Search source, country or measure…"],
    ["Lähdeluokka", "Source grade"],
    ["Kaikki lähdeluokat", "All source grades"],
    ["Lataa rekisteri", "Download register"],
    ["Hakua vastaavaa evidenssiä ei löytynyt.", "No evidence matches the search."],
    ["EP3032975 · julkinen prosessitieto", "EP3032975 · public procedural record"],
    ["Patentti- ja Saksa-seuranta", "Patent and Germany tracker"],
    ["Oikeudellinen näyttö kertoo oikeudesta ja prosessitilasta. Se ei itsessään todista rahaksi muuttunutta korvausta tai vakuusarvoa.", "Legal evidence establishes rights and procedural status. It does not by itself establish realised compensation or collateral value."],
    ["Prosessitila", "Procedural status"],
    ["Vahvistetut tapahtumat", "Verified events"],
    ["Tulkintaraja", "Interpretation boundary"],
    ["Vahvistettu ≠ rahaksi realisoitu", "Verified ≠ realised in cash"],
    ["Huomio", "Note"],
    ["Tuomioiden täytäntöönpanovakuudet eivät ole Pixanille maksettuja vahingonkorvauksia.", "Enforcement security posted for judgments is not damages paid to Pixan."],
    ["Toistettava tutkimusmalli", "Repeatable research model"],
    ["Menetelmä ja laskentasäännöt", "Method and calculation rules"],
    ["Tavoite ei ole täyttää karttaa hinnalla millä hyvänsä, vaan muodostaa vuosittain päivittyvä ja auditoitava aineistoketju.", "The goal is not to fill the map at any cost, but to create an annually updated and auditable evidence chain."],
    ["Täsmäytyskehikko", "Reconciliation framework"],
    ["Näennäinen laillinen kulutus", "Apparent lawful consumption"],
    ["Käytetään vain, kun kaikki komponentit ovat yhteensopivia samalta ajalta ja samasta tuoteryhmästä.", "Use only when all components are compatible in period and product scope."],
    ["kotimainen tuotanto", "domestic production"],
    ["tuonti kulutukseen", "imports for consumption"],
    ["vienti ja jälleenvienti", "exports and re-exports"],
    ["varastomuutos", "inventory change"],
    ["Kotimainen tuotanto plus kulutukseen luovutettu tuonti miinus vienti ja jälleenvienti plus tai miinus varaston muutos", "Domestic production plus imports for consumption minus exports and re-exports plus or minus inventory change"],
    ["Koneelliset portit", "Automated gates"],
    ["Mitä julkaisuputki ei saa päästää läpi", "What the publication pipeline must reject"],
    ["Secure intake · review before publish", "Secure intake · review before publish"],
    ["Toimita uutta markkina-aineistoa", "Submit new market evidence"],
    ["Alkuperäiset tiedostot vastaanotetaan erilliseen Dropbox-kansioon. Julkiseen dashboardiin päätyy vain tarkistettu, lähteistetty ja turvalliseksi rajattu tieto.", "Original files are received in a separate Dropbox folder. Only reviewed, sourced and publication-safe information enters the public dashboard."],
    ["Suositeltu tiedostoille", "Recommended for files"],
    ["Lähetä Dropboxiin", "Send via Dropbox"],
    ["PDF, Excel, Word, CSV, kuvat, sähköpostiviennit ja muut alkuperäiset tiedostot. Lähettäjä ei näe kansion muuta sisältöä.", "PDF, Excel, Word, CSV, images, email exports and other original files. The sender cannot see other folder contents."],
    ["Avaa turvallinen tiedostopyyntö", "Open secure file request"],
    ["Nopea yhteydenotto", "Quick contact"],
    ["Lähetä vihje tai sovi aineiston toimittamisesta. Älä lähetä arkaluonteisia henkilötietoja ilman tarvetta.", "Send a lead or arrange material delivery. Do not send sensitive personal data unless necessary."],
    ["Avaa viesti", "Open message"],
    ["Lähdeviitteet ja selitteet", "Source references and notes"],
    ["Sähköposti", "Email"],
    ["Kerro maa, vuosi, mittari, lähde ja miksi aineisto on merkityksellinen. Valmis otsikko ja tarkistuslista avautuvat luonnokseen.", "State the country, year, measure, source and why the material matters. A prepared subject and checklist open in the draft."],
    ["Luo sähköpostiluonnos", "Create email draft"],
    ["Marnet, tutkijat ja AI-agentit", "Marnet, researchers and AI agents"],
    ["Ehdota GitHubissa", "Propose on GitHub"],
    ["Avaa rakenteinen evidenssiehdotus tai tutkimusidea. Julkinen ehdotus tarkistetaan ennen kuin se voi vaikuttaa dataan tai sivustoon.", "Open a structured evidence proposal or research idea. A public proposal is reviewed before it can affect the data or site."],
    ["Avaa ehdotuslomakkeet", "Open proposal forms"],
    ["Paranna aineiston jäljitettävyyttä", "Improve traceability"],
    ["Luo tiedostojen mukaan saate", "Create a cover note for the files"],
    ["Tiedot käsitellään vain selaimessasi. Painike lataa tekstitiedoston, jonka voit lisätä samaan Dropbox-lähetykseen.", "The details are processed only in your browser. The button downloads a text file you can include in the same Dropbox submission."],
    ["Ei lähetä tietoja verkkoon", "Does not send data online"],
    ["Maa tai alue *", "Country or region *"],
    ["Esim. Saksa", "E.g. Germany"],
    ["Aineiston kattama vuosi *", "Period covered *"],
    ["Esim. 2025 tai 2023–2025", "E.g. 2025 or 2023–2025"],
    ["Lähteen julkaisija *", "Source publisher *"],
    ["Viranomainen, yritys tai tutkimuslaitos", "Authority, company or research institute"],
    ["Alkuperäinen lähde-URL", "Original source URL"],
    ["Mittarityyppi *", "Measure type *"],
    ["Valitse…", "Select…"],
    ["Virallinen myynti tai toimitus", "Official sales or deliveries"],
    ["Vero tai verovolyymi", "Tax or taxable volume"],
    ["Tullituonti tai -vienti", "Customs imports or exports"],
    ["Hintaotos", "Price sample"],
    ["Käyttäjä- tai prevalenssitutkimus", "User or prevalence study"],
    ["Sääntely- tai patenttiasiakirja", "Regulatory or patent document"],
    ["Malli tai kaupallinen arvio", "Model or commercial estimate"],
    ["Muu aineisto", "Other material"],
    ["Lähettäjä / organisaatio", "Sender / organisation"],
    ["Vapaaehtoinen", "Optional"],
    ["Mitä aineisto todistaa ja mitkä ovat sen rajat? *", "What does the material establish and what are its limits? *"],
    ["Kuvaa luku, yksikkö, tuoterajaus ja tunnetut puutteet.", "Describe the figure, unit, product scope and known gaps."],
    ["Vakuutan, että saan toimittaa aineiston tarkistettavaksi. Ymmärrän, ettei sitä julkaista automaattisesti.", "I confirm that I may submit the material for review. I understand that it will not be published automatically."],
    ["Lataa saate .txt", "Download cover note .txt"],
    ["Aineiston käsittelyprosessi", "Material review process"],
    ["Vastaanotto", "Receipt"],
    ["Alkuperäinen säilytetään muuttamatta.", "The original is retained unchanged."],
    ["Turvallisuusseula", "Safety screening"],
    ["Salaisuudet, henkilötiedot ja julkaisuoikeus tarkistetaan.", "Confidential information, personal data and publication rights are checked."],
    ["Lähdeauditointi", "Source audit"],
    ["Mittari, ajanjakso, rajaus ja täsmäytys varmistetaan.", "Measure, period, scope and reconciliation are verified."],
    ["Hyväksytty julkaisu", "Approved publication"],
    ["Vain julkinen johdannainen viedään atlas-dataan.", "Only a public-safe derivative enters the atlas data."],
    ["Ei automaattijulkaisua", "No automatic publication"],
    ["Saapuva tiedosto ei koskaan siirry suoraan GitHubiin tai julkiselle sivulle. Luottamuksellinen datahuone ja julkinen evidence-repo ovat erillisiä.", "An incoming file never moves directly to GitHub or the public site. The confidential data room and public evidence repository are separate."],
    ["Riippumaton, julkisiin lähteisiin perustuva tutkimusprojekti.", "Independent public-source research project."],
    ["Rajaus", "Boundary"],
    ["Lähde", "Source"],
    ["Ei Pixan Oy:n virallinen julkaisu. Ei sijoitus-, laina-, vero- tai oikeudellista neuvontaa.", "Not an official Pixan Oy publication. Not investment, lending, tax or legal advice."],
    ["maat CSV", "countries CSV"],
    ["evidenssi CSV", "evidence CSV"],
    ["Sulje", "Close"],
    ["Dashboard-dataa ei voitu ladata.", "Dashboard data could not be loaded."],
    ["Yritä päivittää sivu tai avaa JSON-aineisto suoraan.", "Refresh the page or open the JSON dataset directly."],

    ["Lainanantajan ja ostajan tarkistus", "Lender & buyer review"],
    ["Riippumaton · ei Pixan Oy:n julkilausuma", "Independent · not a Pixan Oy disclosure"],
    ["Kopioi tarkistuslinkki", "Copy review link"],
    ["Riippumaton julkisten lähteiden tarkistusmuistio", "Independent public-source diligence brief"],
    ["Tarkistettava evidenssipohja — ei lupaus markkinan koosta.", "A reviewable evidence base—not a market-size promise."],
    ["Tämä muistio antaa mahdolliselle lainanantajalle, strategiselle ostajalle, valmistajalle tai neuvonantajalle suoran reitin Pixaniin liittyvän maailmanlaajuisen sähkötupakkamarkkinatutkimuksen julkiseen evidenssiin. Kaikki johtopäätökset edellyttävät riippumatonta kaupallista, oikeudellista, patentti- ja taloudellista tarkastusta.", "This brief gives a prospective lender, strategic buyer, manufacturer or adviser a direct route into the public evidence supporting the global vaping-market research associated with Pixan. Every conclusion remains subject to independent commercial, legal, patent and financial diligence."],
    ["Avaa 195 maan atlas", "Open the 195-country atlas"],
    ["Lataa maat CSV", "Download country CSV"],
    ["Lataa evidenssi CSV", "Download evidence CSV"],
    ["Tulosta / tallenna PDF", "Print / save as PDF"],
    ["Tärkeä rajaus", "Important disclosure"],
    ["Riippumattoman tutkimuksen raja", "Independent research boundary"],
    ["Sivusto ei ole Pixan Oy:n julkaisema, ylläpitämä tai hyväksymä eikä esitä Pixan Oy:n virallista kantaa. Se ei ole tarjous, arvonmääritys, kohtuullisuuslausunto, sijoitussuositus, tilintarkastus tai oikeudellinen lausunto.", "This site is not issued, maintained or endorsed by Pixan Oy and does not state Pixan Oy’s official position. It is not an offer, valuation, fairness opinion, investment recommendation, audit or legal opinion."],
    ["Aineiston päivä", "Dataset date"],
    ["· lähdeperusta", "· source baseline"],
    ["Kuinka aineistoa käytetään", "How to use this material"],
    ["Päätöksenteon faktat ja selkeät rajat", "Decision-useful facts and explicit limits"],
    ["Atlas erottaa suorat viralliset havainnot proxyistä ja malleista, jotta tarkastaja voi hinnoitella evidenssiriskin eikä periä yhdistetyn otsikkoluvun epävarmuutta.", "The atlas separates direct official observations from proxies and models so a reviewer can price evidence risk instead of inheriting a blended headline number."],
    ["Tässä julkaisussa vahvistettu", "Established in this release"],
    ["Mitä voidaan tarkistaa nyt", "What can be reviewed now"],
    ["Kiinteä 195 maan universumi ja yhtenäinen evidenssiluokitus.", "A fixed 195-country universe and a consistent evidence taxonomy."],
    ["Lähteistetyt viranomais-, tulli-, vero-, sääntely- ja mallireitit.", "Source-linked official, customs, tax, regulatory and model routes."],
    ["Saksan viralliset patentti- ja tuomioistuinankkurit prosessitilan rajoineen.", "Official German patent and court anchors with process-status limits."],
    ["Tässä julkaisussa ei vahvistettu", "Not established by this release"],
    ["Mitä ei saa päätellä", "What must not be inferred"],
    ["Täydellinen maailmanlaajuinen vuosittaisen vähittäismyynnin kokonaismäärä.", "A complete global annual retail-sales total."],
    ["Pixanin yritys-, osake-, vakuus- tai patenttiarvo.", "Pixan’s enterprise, equity, collateral or patent value."],
    ["Muiden kuin viitatuissa tuomioissa käsiteltyjen osapuolten tai tuotteiden loukkaus.", "Infringement by parties or products outside the cited judgments."],
    ["Perittävissä olevat vahingonkorvaukset, lisenssituotot tai toteutunut kassavirta.", "Recoverable damages, licensing revenue or realised cash flow."],
    ["Nykyinen valmius", "Current readiness"],
    ["Avoimet tarkastusportit", "Open diligence gates"],
    ["Kattavuus väitteen laadun mukaan", "Coverage by claim quality"],
    ["A, B, C ja D eivät ole keskenään vaihdettavia", "A, B, C and D are not interchangeable"],
    ["Maalla voi olla vahva vero- tai tullireitti, vaikka vuosittainen kuluttajamyynti olisi vahvistamatta. Puuttuva evidenssi näytetään puuttuvana, ei koskaan nollana.", "A country may have a strong tax or customs route while annual consumer sales remain unverified. Missing evidence is shown as missing, never as zero."],
    ["Maaluokitus", "Country classification"],
    ["Paras saatavilla oleva evidenssi", "Best available evidence"],
    ["Keskeiset väiteulottuvuudet", "Key claim dimensions"],
    ["Vahvistetut ja osittaiset reitit", "Verified and partial routes"],
    ["Saksa · vain viralliset asiakirjat", "Germany · official records only"],
    ["Patentti- ja tuomioistuinprosessin ankkurit", "Patent and court-process anchors"],
    ["Oikeudelliset asiakirjat ovat tarkastusankkureita. Ne eivät yksin osoita arvostusta, täytäntöönpanokelpoisuutta muissa maissa, vahingonkorvauksia tai kassatuottoja.", "The legal records are included as diligence anchors. They do not by themselves establish valuation, enforceability in other countries, damages or cash proceeds."],
    ["Valituksen tila", "Appeal status"],
    ["BPatG-tuomio: valitus tehty", "BPatG judgment: appeal lodged"],
    ["Liittovaltion patenttituomioistuimen virallisessa asiakirjassa todetaan valitus asianumerolla X ZR 21/26. Valituksen jättämisen määräaika ei siten enää ole avoin epävarmuus; valitus on vireillä, ellei myöhempi virallinen asiakirja osoita ratkaisua tai perumista.", "The official Federal Patent Court record notes an appeal under docket X ZR 21/26. The filing deadline is therefore no longer the operative uncertainty; the appeal is pending unless an official later record shows disposition or withdrawal."],
    ["Liittovaltion patenttituomioistuimen virallisessa asiakirjassa todetaan valitus asianumerolla", "The official Federal Patent Court record notes an appeal under docket"],
    [". Valituksen jättämisen määräaika ei siten enää ole avoin epävarmuus; valitus on vireillä, ellei myöhempi virallinen asiakirja osoita ratkaisua tai perumista.", ". The filing deadline is therefore no longer the operative uncertainty; the appeal is pending unless an official later record shows disposition or withdrawal."],
    ["Julkinen asiakirja ei yksin kerro tiedoksiantopäiviä, kirjelmien pidennyksiä, käsittelypäiviä tai lopputulosta. Nämä edellyttävät ajantasaista saksalaista oikeudellista neuvontaa tai päivitettyä virallista tuomioistuinasiakirjaa.", "The public docket alone does not disclose service dates, briefing extensions, hearing dates or a final outcome. Those points require current German counsel or an updated official court record."],
    ["Avaa koko oikeudellinen näkymä", "Open full legal view"],
    ["Suositeltu tarkastusjärjestys", "Recommended diligence sequence"],
    ["Julkisesta evidenssistä rahoituskelpoiseen tapaukseen", "From public evidence to a financeable case"],
    ["Seuraava askel ei ole moninkertaistaa maailmanlaajuista otsikkoarviota. On suljettava evidenssiaukot, jotka vaikuttavat olennaisesti lainanantajan tai ostajan downside-tapaukseen.", "The next step is not to multiply a global headline estimate. It is to close the evidence gaps that materially affect a lender’s or buyer’s downside case."],
    ["Toista vahvimmat vuosittaiset aineistot", "Reproduce the strongest annual datasets"],
    ["Arkistoi kyselyparametrit, päivätyt otteet ja tiivisteet virallisista myynti-, valmisteverovolyymi- ja verotuottosarjoista.", "Archive query parameters, dated extracts and hashes for official sales, excise-volume and tax-revenue series."],
    ["Täsmäytä markkinamittarit maittain", "Reconcile market measures country by country"],
    ["Pidä vähittäismyynti, valmistajatoimitukset, tulliarvo, verollinen määrä ja mallinnettu kysyntä erillisinä sarakkeina.", "Keep retail sales, manufacturer deliveries, customs value, taxable volume and modelled demand as separate columns."],
    ["Kartoita patenttistatus ja vaatimusten laajuus", "Map patent status and claim scope"],
    ["Vahvista kansallinen validointi, vuosimaksut, claim chartit, vastapuolet ja tuotekohtainen merkitys patenttiasiantuntijan kanssa.", "Verify national validation, renewals, claim charts, counterparties and product-specific relevance with patent counsel."],
    ["Rakenna lainanantaja- ja ostajaskenaariot", "Build lender and buyer scenarios"],
    ["Liitä konservatiivinen, perus- ja noususkenaario oikeudellisesti perusteltaviin ja realisoitavissa oleviin kassavirtaoletuksiin vasta evidenssiauditoinnin jälkeen.", "Only after the evidence audit, link conservative, base and upside cases to legally supportable and realisable cash-flow assumptions."],
    ["Jatka tarkistusta", "Continue the review"],
    ["Tarkista taustalla olevat maa- ja lähdetiedot.", "Inspect the underlying country and source records."],
    ["Käytä koko atlasta maasuodattimiin, lähdelinkkeihin, evidenssiluokituksiin, menetelmään ja hallittuun aineiston toimituskanavaan.", "Use the full atlas for country filters, source links, evidence classifications, methodology and the controlled material-submission channel."],
    ["Avaa koko atlas", "Open full atlas"],
    ["Avaa evidenssirekisteri", "Open evidence register"],
    ["Ehdota evidenssiä GitHubissa", "Propose evidence on GitHub"],
    ["Toimita lähdeaineistoa", "Submit source material"],
    ["Tarkistettua aineistoa ei voitu ladata.", "The reviewed dataset could not be loaded."],
    ["Käytä koko atlasta tai lataa repositorioon tallennetut CSV-tiedostot. Älä luota tyhjiin mittareihin.", "Use the full atlas or download the committed CSV files. Do not rely on blank metrics."],
    ["Riippumaton julkisiin lähteisiin perustuva tutkimus. Ei Pixan Oy:n virallinen julkaisu.", "Independent public-source research. Not an official Pixan Oy publication."],
    ["Tarkistusraja", "Review boundary"],
    ["Ei tarjous, arvonmääritys, tilintarkastus, oikeudellinen lausunto, rahoitussitoumus tai näyttö sijoittajakiinnostuksesta.", "Not an offer, valuation, audit, legal opinion, financing commitment or evidence of investor interest."],
    ["Koneellisesti luettava evidenssi", "Machine-readable evidence"],
    ["Maat CSV", "Countries CSV"],
    ["Evidenssi CSV", "Evidence CSV"],
    ["Kielivalinta", "Language selection"],
    ["Markkinakoko", "Market size"],
    ["Markkinan arvo", "Market value"],
    ["Avaa markkina-arvo ja vuosihavainnot", "Open market value and annual observations"],
    ["Vuosittainen markkina-arvo ja laskentareitit", "Annual market value and calculation routes"],
    ["Havaittu · johdettu · mallinnettu", "Observed · derived · modelled"],
    ["Vahvistetut toimitukset, verotetut määrät, verotuotot ja mallinnetut arviot pidetään erillään. Eri mittareita käytetään rinnakkaiseen tarkistukseen, ei saman myynnin laskemiseen kahdesti.", "Verified shipments, taxable volumes, tax revenue and modelled estimates are kept separate. Different measures are used for parallel cross-checks—not to count the same sales twice."],
    ["Ulkopuolinen täsmäytyshaarukka", "External reconciliation range"],
    ["Vuoden 2025 kaupalliset maailmanmarkkina-arviot", "Commercial 2025 global-market estimates"],
    ["Ei atlaksen arvio", "Not an atlas estimate"],
    ["Julkaisijoiden tuoterajaukset ja menetelmät poikkeavat toisistaan. Haarukka on sanity check, ei vahvistettu maailmanlaajuinen myynti.", "Publisher scopes and methods differ. The range is a sanity check, not verified worldwide sales."],
    ["Mallin valmius", "Model readiness"],
    ["Ei vielä estimaattivalmis", "Not estimate-ready"],
    ["Maa × vuosi × mittari", "Country × year × measure"],
    ["Vahvistetut ja johdetut määrälliset havainnot", "Verified and derived quantitative observations"],
    ["Lataa markkina-aineisto", "Download market-value data"],
    ["Maa / alue", "Country / region"],
    ["Vuosi", "Year"],
    ["Mittari", "Measure"],
    ["Arvo tai määrä", "Value or volume"],
    ["Näytön luonne", "Evidence type"],
    ["Markkinahavaintoja ei voitu ladata.", "Market observations could not be loaded."],
    ["Triangulaatio ilman tuplalaskentaa", "Triangulation without double counting"],
    ["Kuusi vaihtoehtoista laskentareittiä", "Six alternative calculation routes"],
    ["Menetelmät tuottavat rinnakkaisia low/base/high-arvioita. Niitä verrataan ja painotetaan evidenssin laadulla; niitä ei summata keskenään.", "The methods produce parallel low/base/high estimates. They are compared and evidence-weighted; they are not added together."],
    ["Avaa maailmanlaajuinen lähdereittisuunnitelma", "Open the global source-route plan"],
    ["Avaa vuosittainen markkina-arvon näyttö", "Open annual market-value evidence"],
    ["Vuosiarvo · evidenssi ensin", "Annual value · evidence first"],
    ["Mitä voidaan määrällistää tänään", "What can be quantified today"],
    ["Viralliset maahavainnot, johdetut vaihteluvälit ja kaupalliset maailmanmarkkina-arviot näytetään erillään, jotta tarkastaja näkee sekä luvun että sen todellisen mittarin.", "Official country observations, derived ranges and commercial global estimates are shown separately so a reviewer can see both the number and what it actually measures."],
    ["Avaa kaavat, vuosihavainnot ja lähteet", "Open formulas, annual observations and sources"],
    ["Arvioitu vuosimarkkina", "Estimated annual market"],
    ["Vahvistettu havainto", "Verified observation"],
    ["Mallinnettu arvio", "Modelled estimate"],
    ["Vaihteluväli", "Range"],
    ["Lähdevuosi", "Source year"],
    ["Valuutta", "Currency"],
    ["Usein palaaville", "For returning visitors"],
    ["Usein palaaville tarkastajille", "For returning reviewers"],
    ["Mitä on muuttunut viime käyntisi jälkeen?", "What changed since your last visit?"],
    ["Tarkistetaan…", "Checking…"],
    ["Merkitse nähdyksi", "Mark as seen"],
    ["Viimeisin nähdyksi merkitsemäsi julkaisu tallennetaan vain tähän selaimeen. Sivusto ei käytä tätä toimintoa analytiikkaan eikä tunnista kävijää.", "The last release you mark as seen is stored only in this browser. This feature uses no analytics and does not identify you."],
    ["Pixan Global Market Evidence, etusivu", "Pixan Global Market Evidence, home"],
    ["Pixan Global Market Evidence, koko atlas", "Pixan Global Market Evidence, full atlas"]
  ];

  const pairByText = new Map();
  for (const [fi, en] of STATIC_PAIRS) {
    pairByText.set(fi, { fi, en });
    pairByText.set(en, { fi, en });
  }

  function storedLanguage() {
    try {
      const value = localStorage.getItem(STORAGE_KEY);
      return SUPPORTED.has(value) ? value : null;
    } catch (_) {
      return null;
    }
  }

  function queryLanguage() {
    const value = new URL(location.href).searchParams.get("lang");
    return SUPPORTED.has(value) ? value : null;
  }

  let language = queryLanguage() || storedLanguage() || "en";

  function pick(fi, en) {
    return language === "fi" ? fi : en;
  }

  function translateValue(value) {
    const trimmed = String(value || "").trim();
    const pair = pairByText.get(trimmed);
    if (!pair) return value;
    return String(value).replace(trimmed, pair[language]);
  }

  function translateStatic(root = document) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode(textNode) {
        const parent = textNode.parentElement;
        if (!parent || parent.closest("script, style, [data-no-static-i18n]")) return NodeFilter.FILTER_REJECT;
        return pairByText.has(textNode.nodeValue.trim()) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
      }
    });
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((textNode) => { textNode.nodeValue = translateValue(textNode.nodeValue); });

    for (const element of root.querySelectorAll("[aria-label], [placeholder], meta[name='description']")) {
      for (const attribute of ["aria-label", "placeholder", "content"]) {
        if (element.hasAttribute(attribute)) element.setAttribute(attribute, translateValue(element.getAttribute(attribute)));
      }
    }
    document.documentElement.lang = language;
  }

  function languageUrl(href, lang = language) {
    if (!href || /^(?:mailto:|tel:|javascript:|#)/i.test(href)) return href;
    try {
      const url = new URL(href, location.href);
      if (url.origin !== location.origin || !/\.html$|\/$/.test(url.pathname)) return href;
      url.searchParams.set("lang", lang);
      if (/^[a-z][a-z\d+.-]*:/i.test(href)) return url.href;
      return `${url.pathname.split("/").pop() || "index.html"}${url.search}${url.hash}`;
    } catch (_) {
      return href;
    }
  }

  function localizeLinks(root = document) {
    for (const link of root.querySelectorAll("a[href]")) {
      if (!link.dataset.i18nBaseHref) link.dataset.i18nBaseHref = link.getAttribute("href");
      link.setAttribute("href", languageUrl(link.dataset.i18nBaseHref));
    }
  }

  function syncControls() {
    for (const button of document.querySelectorAll("[data-language]")) {
      const active = button.dataset.language === language;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", String(active));
    }
  }

  function writeCurrentUrl() {
    const url = new URL(location.href);
    url.searchParams.set("lang", language);
    history.replaceState(history.state, "", `${url.pathname}${url.search}${url.hash}`);
  }

  function setLanguage(nextLanguage, options = {}) {
    if (!SUPPORTED.has(nextLanguage)) return;
    language = nextLanguage;
    try { localStorage.setItem(STORAGE_KEY, language); } catch (_) { /* local preference is optional */ }
    if (options.updateUrl !== false) writeCurrentUrl();
    translateStatic();
    localizeLinks();
    syncControls();
    document.dispatchEvent(new CustomEvent("pixan:languagechange", { detail: { language } }));
  }

  function init() {
    writeCurrentUrl();
    translateStatic();
    localizeLinks();
    syncControls();
    document.querySelectorAll("[data-language]").forEach((button) => {
      button.addEventListener("click", () => setLanguage(button.dataset.language));
    });
  }

  window.SiteI18n = {
    getLanguage: () => language,
    isFinnish: () => language === "fi",
    pick,
    setLanguage,
    translateStatic,
    localizeLinks,
    languageUrl
  };

  init();
})();
