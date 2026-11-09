# Documentele electrocasnicelor

Set demonstrativ pentru România, verificat pe **9 noiembrie 2026**.
Am ales modele după disponibilitatea documentelor oficiale, fără clasament de produse.
Nu sunt aparatele personale ale unui cumpărător și nu există certificate completate cu date personale.

## Ce am colectat

- **10 manuale de utilizare**, în PDF.
- **3 documente generale de garanție**, comune pe producător.
- În total: **10 perechi aparat–manual–garanție, 13 fișiere unice**.
- 9 manuale conțin română; manualul frigiderului verificat este în engleză.
- Toate PDF-urile au text extractibil. Originalele nu au fost decupate sau traduse.

Garanțiile comune sunt păstrate o singură dată, ca să nu indexăm același text de mai multe ori.
Legăturile fiecărui aparat sunt în [catalog.json](catalog.json).

| Aparat | Model și suport oficial | Manual oficial | Garanție |
| --- | --- | --- | --- |
| Frigider / combină frigorifică | [Bosch KFN96VPEA](https://www.bosch-home.ro/supportdetail/product/KFN96VPEA/01) | [EN, 32 pagini](https://media3.bosch-home.com/Documents/9001690354_A.pdf) | G1 |
| Mașină de spălat rufe | [Bosch WGG244Z2BY](https://www.bosch-home.ro/ro/mkt-product/masini-de-spalat-rufe-si-uscatoare/masini-de-spalat-rufe/masini-de-spalat-rufe-cu-incarcare-frontala/WGG244Z2BY) | [RO, 56 pagini](https://media3.bsh-group.com/Documents/9001916486_A.pdf) | G1 |
| Uscător de rufe | [Bosch WTH85207BY](https://www.bosch-home.ro/ro/mkt-product/masini-de-spalat-rufe-si-uscatoare/uscatoare-de-rufe/uscatoare-cu-pompa-de-cadura/WTH85207BY) | [RO, 48 pagini](https://media3.bsh-group.com/Documents/9001746360_B.pdf) | G1 |
| Mașină de spălat vase | [Bosch SMS4HVI02E](https://www.bosch-home.co.uk/supportdetail/product/SMS4HVI02E/75) | [RO, 56 pagini](https://media3.bosch-home.com/Documents/9001902771_C.pdf) | G1 |
| Cuptor cu microunde | [Bosch FFL020MS2](https://www.bosch-home.ro/ro/mkt-product/aparate-pentru-gatit/microunde/cuptor-cu-microunde-independent/FFL020MS2) | [RO, 20 pagini](https://media3.bosch-home.com/Documents/9001625725_I.pdf) | G1 |
| Aparat de cafea | [Philips EP2220/10](https://www.philips.ro/c-p/EP2220_10/-/support) | [Multilingv, 635 pagini](https://dam.versuni.com/m/43f5d99f5574a42e/original/CO_2025_800-Series_1200-Series_2200-Series_3200-Series_Manual-Philips_EU9.pdf) | G2 |
| Blender | [Philips HR3760/00](https://www.philips.ro/c-p/HR3760_00/7000-series-high-speed-blender/support) | [Multilingv, 50 pagini](https://dam.versuni.com/m/6ed49ddaed94eec9/original/3000-088-3641-3_EU9_2-2_HR3760_UM_V3-1-DFU.pdf) | G2 |
| Friteuză cu aer cald | [Philips HD9252/90](https://www.home.id/ro-RO/HD9252) | [RO, 24 pagini](https://dam.versuni.com/m/68bf55e3b6eaf085/original/Airfryer-Spectre-HD925x-User-Manual-RO.pdf) | G2 |
| Aspirator fără sac | [Samsung VC07M2110SB/GE](https://www.samsung.com/ro/support/model/VC07M2110SB/GE/) | [RO, 20 pagini](https://downloadcenter.samsung.com/content/UM/202603/20260326100857540/O-DJ68-00758L-09_IB_VC2100_GE_RO_251203.pdf) | G3 |
| Aspirator robot | [Samsung VR05R5050WK/OL](https://www.samsung.com/ro/support/model/VR05R5050WK/OL/) | [RO complet, 15 pagini PDF](https://downloadcenter.samsung.com/content/PM/202007/20200710133232637/FR/i5_SR_A5_full_version_20200527-Romanian.pdf) | G3 |

## Documentele de garanție

- **G1 — Bosch/BSH:** [condiții generale oficiale](https://media3.bsh-group.com/Documents/8001253266_B.pdf), versiune 01/2022. Secțiunea România este la paginile PDF **19–20**, împărțind paginile cu alte limbi.
- **G2 — Philips Home/Versuni:** [politica oficială România](https://www.home.id/ro-RO/warranty). Pagina HTML a fost convertită în TXT, cu URL și data consultării. Am păstrat condițiile, nu doar formularul pentru ștampila vânzătorului. La indexarea TXT, pagina este 1.
- **G3 — Samsung:** [certificatul general România](https://images.samsung.com/is/content/samsung/assets/ro/terms-and-conditions/warranty-certificate-romanian-version-June2026.pdf), versiune 06/2026, 2 pagini PDF. Formularul este necompletat, dar include condițiile.

Aceste documente descriu condiții generale. Nu dovedesc data cumpărării, înregistrarea
într-o promoție sau eligibilitatea unui aparat personal pentru o extensie de garanție.
De exemplu, extensiile descrise pentru JetBot nu se atribuie automat robotului VR05R5050WK.
Pentru un caz real contează documentele și condițiile aplicabile la cumpărare.

## Unde sunt fișierele

Documentele descărcate sunt în `documente/`, local. Nu republicăm PDF-urile
producătorilor în repository; catalogul păstrează linkurile oficiale și amprentele SHA256.

Pentru a descărca sau verifica din nou setul, din `AI-Agentic-Application`:

```powershell
.\.venv\Scripts\python.exe -X utf8 proiect_final/electrocasnice/descarca_documente.py
```

Scriptul refolosește fișierele existente și verifică textul, familia/modelul unde
apare în PDF și amprentele documentelor. Dacă o sursă se schimbă, cere reverificarea.
Rezultatul local, cu pagini, dimensiuni și erori, este în `verificare_locala.json`.
Nu există apeluri LLM sau consum de credit API în această colectare.

## Lucruri importante pentru RAG

- `catalog.json` asociază separat manualul și garanția fiecărui model. Nu amestecăm condiții între mărci sau serii.
- Manualul EP2220 are româna la paginile PDF **348–369**; HR3760 la **24–26**. Intervalele sunt notate în catalog.
- Manualele comune unei familii pot include funcții sau accesorii opționale. Codul comercial complet nu înseamnă că toate variantele au aceleași accesorii.
- Manualul robotului are pagini tipărite alăturate: 15 pagini PDF, cu numerotare tipărită până la 29. Citările trebuie să folosească pagina fizică din PDF.
- Pentru mașina de spălat vase, suportul verificat este UK, dar manualul ales este RO și documentul de garanție este pentru România.
- Setul este separat de exemplele inițiale din `proiect_final/data_sources`. Programele actuale nu citesc automat acest catalog. Integrarea trebuie să țină cont de model, limbă și tipul documentului.

## Întrebări potrivite pentru demonstrație

1. Ce documente cere garanția producătorului pentru o solicitare de service?
2. Ce spune manualul modelului ales despre curățarea filtrului?
3. Ce întreținere descrie manualul aparatului de cafea și la ce pagini?
4. Se referă o extensie din certificat la întregul aparat sau la o componentă și ce serii sunt menționate?
5. Dacă lipsesc data cumpărării sau un certificat personal, ce nu poate fi stabilit doar din aceste documente?

Datele provin exclusiv din paginile și documentele oficiale legate mai sus.
