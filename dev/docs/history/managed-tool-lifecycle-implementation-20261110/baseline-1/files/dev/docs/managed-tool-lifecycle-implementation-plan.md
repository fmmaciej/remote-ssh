---
id: PLAN-MANAGED-TOOL-LIFECYCLE
version: "0.2"
status: draft
created: 2026-11-10
updated: 2026-11-10
specification: SPEC-MANAGED-TOOL-LIFECYCLE@0.3
specification_sha256: 62a53a9ae528dba9ca1d0943c014c557490bec897d638b998902ca16fe56ffbb
implementation_cycle: managed-tool-lifecycle-implementation-20261110
author: /root/managed_lifecycle_planner
integration_owner: /root/managed_lifecycle_implementer
---

# Plan automatycznego cyklu życia narzędzi

## Podstawa, rezultat i granice

Podstawą jest [manifest zaakceptowanej specyfikacji](history/managed-tool-lifecycle-20261110/baseline-1/baseline.json),
nie zmienny dokument roboczy. Jego jedyna kopia to `files/dev/docs/managed-tool-lifecycle-specification.md`:
SPEC-MANAGED-TOOL-LIFECYCLE 0.3, hash jak wyżej, bez zależności. Linki kopii rozwiązywać względem
`source: dev/docs/managed-tool-lifecycle-specification.md`. [Historia, zdarzenie 13](history/managed-tool-lifecycle-20261110/events.md)
potwierdza akceptację człowieka; [review 2](history/managed-tool-lifecycle-20261110/review-2.md) ma Pass.
Kod: `15bcb79cee2d1959074d4c70e164d0cae75ee8e2`; rozpoznanie nie wykazało śledzonych zmian.
Istniejące nieśledzone dokumenty specyfikacji/historii zachować. Nie odczytywano `dev/.env` ani danych hosta.

Rezultat: addytywne `install TOOL...` / `install --profile mini|quick|full`, jawne `uninstall TOOL...`,
`update` utrzymujący automatyczny zestaw oraz odczytowe `list` i `check` z diagnostyką środowiska.
Bare install/uninstall oraz usunięte wejścia mają zakończyć się 1 przed migracją i jakimkolwiek zapisem.
Zakres obejmuje pełną gramatykę/statusy/kody ze specyfikacji, bootstrap i bieżące instrukcje.
Wyłączenia: nowe wersje/assety/platformy, live asset checks, migracja rzeczywistych hostów, publikacja,
Git mutacje, automatyczny prune, przebudowa shell, aktywacja biblioteki w otwartej sesji i fzf faza 2.
Profile zachowują bieżący skład z [tool_sets.sh](../../tools/lib/install/tool_sets.sh); nie zapisujemy profilu.

To szkic do osobnego przeglądu i jawnej akceptacji planu, bez upoważnienia do implementacji.
Docelowy dokument po akceptacji: `dev/docs/managed-tool-lifecycle-implementation-plan.md`;
historia cyklu: `dev/docs/history/managed-tool-lifecycle-implementation-20261110/`.
Obecnie obie ścieżki pozostają nieutworzone; jedyny zapis planisty to scratch `/private/tmp/...planning-20261110/`.

## Rozpoznanie i wybory konstrukcyjne

[release.sh](../../tools/lib/common/release.sh) łączy dowód własności, istniejący payload i bieżącą definicję.
[tool_inventory.sh](../../tools/lib/install/tool_inventory.sh) przez to gubi broken i alias-only;
[install/install.sh](../../tools/lib/install/install.sh) pomija zdrowie aliasów, a publikacja niskopoziomowa
akceptuje dowolny symlink. [install.sh](../../tools/lib/commands/install.sh) zapisuje zestaw dopiero po paczce.
[update.sh](../../tools/lib/commands/update.sh) odświeża kod przed odtworzeniem zestawu przez pusty install;
[uninstall.sh](../../tools/lib/commands/uninstall.sh) zmienia expected-tools i może zgubić błąd enumeracji.
To miejsca integracji, nie powód do osłabienia dotychczasowej ochrony [prune](../../tools/lib/commands/prune.sh).

**Stan lokalizacji.** Przechowywać wewnątrz efektywnego prefiksu:
`$INSTALL_PREFIX/.remote-ssh-managed/locations/<numer>/state`. Nie wymagać zapisu do rodzica prefiksu.
Root metadanych ma własny magic/schema; tylko realne, należące do użytkownika katalogi 0700 i pliki 0600.
Kompletny skan slotów wybiera dokładnie jeden po pełnej parze fizycznych, absolutnych prefix/bin;
zero dopasowań oznacza nową lokalizację tylko przy poprawnej strukturze, duplikat lub wadliwy slot daje błąd.
Nowy slot publikować z kompletnego katalogu roboczego przez rename w tym samym filesystemie.
Względne override zamienić na absolutne względem wejściowego PWD; istniejące katalogi przez `pwd -P`,
nieistniejący ogon względem najbliższego istniejącego rodzica; po mkdir ponownie sprawdzić tę samą tożsamość.
XDG nie wybiera stanu. Każdy rekord zawiera obie ścieżki; obcy/podmieniony rekord jest błędem, nie pustym zestawem.
Pary współdzielące prefix/bin muszą respektować cudze zapisane claims; wspólny aktywny link jest kolizją,
nie powodem przejęcia. Nie skanować ani nie sprzątać dawnych lokalizacji po zmianie override.

**Format.** Jeden plik binarny z polami rozdzielonymi NUL, stałym nagłówkiem i typowanymi rekordami
o jawnych licznościach: schema, para, generation, adoption_done; członkowie; zachowane metadane narzędzi;
dowody wydań/linków; bieżący journal paczki i wyniki każdej pozycji. Bash 3.2 obsługuje `read -r -d ''`.
Parser jest danymi, nigdy `source`/`eval`; odrzuca nieznane/powtórzone pola, ucięcie, nadmiar i złą tożsamość.
NUL zachowuje spacje, znaki nowej linii i separatory w dozwolonych ścieżkach/aliasach bez nowych zależności.
`state` brakujący w istniejącym slocie, nieczytelny, symlink lub niepoprawny blokuje operację.
Zmiana stanu: prywatny sibling temp, pełna serializacja, zamknięcie, ponowny parse i rename nad sprawdzonym
własnym zwykłym plikiem; błąd pozostawia poprzednią generację. Nigdy fallback do pustego stanu.
Pozostałości temp nie są sukcesem ani źródłem członkostwa; nie usuwać ich na podstawie samej nazwy.

**Własność oddzielona od zdrowia (P0-001).** Zachować formaty 1/2 i osobne predykaty:
(A) identyfikacja/członkostwo, (B) naprawa dokładnego selektora, (C) rekursywne usunięcie wydania.
C wymaga każdorazowo żywego odpowiednika obecnego validatora: realnego bezpośredniego dziecka fizycznego
prefiksu; własnego regularnego, czytelnego niesymlinkowanego markera ze ścisłym formatem/nazwą/wersją/layoutem;
bezpiecznego względnego membera; wszystkich składowych jego rodzica jako realnych katalogów bez symlinków;
fizycznego rodzica wewnątrz wydania i istniejącego regularnego niesymlinkowanego membera (library też readable).
Brak membera/rodzica, podmiana markera/rodzica/leaf albo niespełnione granice nie pozwalają na `rm -rf`,
także dla zapisanej lub retired nazwy. Receipt nigdy nie zastępuje utraconej żywej przesłanki C.
B może dopuścić brak membera, bo rusza wyłącznie dokładny symlink: aktualny literalny target musi odpowiadać
zweryfikowanemu receipt i żywemu poprawnemu markerowi; root i wszystkie istniejące składowe rodzica są
realne/zawarte, a istniejący leaf regularny bez symlinka. Brak któregoś rodzica, obcy/broken symlink leaf,
wadliwy marker, zwykły plik zamiast selektora lub inny target -> protected, bez zastąpienia.
Brak selektora pozwala utworzyć nowy, lecz nie usuwać starego wydania. Zdrowie nie usuwa członkostwa.
Definicja lub zachowane zweryfikowane metadane identyfikują retired; nie wykonywać danych stanu jako kodu.
Uninstall przy niewystarczającym C dla wymaganego zapisanego zakresu przerywa i zachowuje zarządzanie;
nieznana nieudowodniona pozostałość poza tym zakresem pozostaje protected bez blokowania pełnego sukcesu.
Prune zachowuje C, wymóg bieżącej znanej definicji i dry-run; dodatkowa ochrona journal/claims poniżej.
Chronić też niebezpieczne `.active`; rewalidować żywy dowód i target bezpośrednio przed każdą mutacją.

**Zdrowie.** Wspólny model inventory/status ocenia członkostwo niezależnie od wersji/layoutu/payloadu,
obsługi platformy i PATH. Dla binary sprawdza właściwy regularny executable i wszystkie wymagane aliasy;
dla bundle także zachowaną listę plików/danych ze stagingu i deklarowane wymagane ścieżki;
dla biblioteki readable member, format 2, dokładny mapping/libc i własny absolutny `.active/TOOL`.
Do `nvim.sh` dodać tylko metadane wymagania `share/nvim/runtime`; przypięte wersje/assety pozostają identyczne.
W migracji starszy bundle sprawdzać według znacznika i tych wymagań; brak dawnych danych nie gubi członkostwa.
Wersję brać ze znacznika; raporty nie uruchamiają `--version`, payloadu, library probe ani `enable -f`.
Odczytowe zdrowie plików nie zastępuje kwalifikacji ABI wykonywanej podczas instalacji biblioteki.

**Konkurencja bez flock (P0-002).** Zestawy blokad: install/uninstall i wrapper — prefix oraz bin,
jeśli zmienią selektory executable; biblioteki/zmiany samego stanu — prefix; update dodatkowo checkout
na refresh; `prune --apply` wyłącznie prefix. Storage każdego locka wewnątrz blokowanego rootu, bez zapisu
do jego rodzica; prune nie wymaga zapisywalnego bin ani checkoutu. Zestaw ustalić odczytowo również z
poprzedniego journalu, następnie zweryfikować pod locks w stałym porządku, shared root raz; zmiana zestawu
wymaga ponownego acquire, bez mutacji. Stan jest związany wyłącznie z parą prefix/bin, nie checkoutem.
Lock storage tworzyć dopiero po zgodzie dla install/uninstall. Użyć bakery, bez automatycznego `rm` stale mkdir:
atomowe mkdir unikalnego `p<PID>-<nonce>` oznacza choosing; potem atomowo opublikowany dodatni ticket
`1 + max` istniejących żywych ticketów. Przed wejściem czekać na zakończenie choosing i mniejsze pary
`(ticket, token)`; nowy uczestnik widzi już opublikowany ticket. Pełny skan i błędy odczytu są obowiązkowe.
Ticket martwego PID ignorować bez kasowania; żywy/niepewny PID (także reuse) traktować konserwatywnie busy.
Timeout daje 1 bez wejścia w sekcję mutacji. EXIT/HUP/INT/TERM usuwa tylko własny zweryfikowany ticket.
Po SIGKILL następny lifecycle odzyskuje journal; prune tylko ignoruje martwy ticket, bez wyścigu reclaimers.
Wyłącznie proces właściciela publikuje linki/stan; dzieci przygotowują prywatny staging bez publikacji.
Po refreshu `exec` świeżego prywatnego continuation zachowuje PID/ticket; waliduje token/parę/generation.
Prune pod prefix lock czyta kompletnie wszystkie sloty/claims i journals/receipts bez ich recovery.
Chroni aktywne odnośniki, wszystkie pending staging/final releases także po śmierci writera oraz claims
innej pary lokalizacji wspólnego prefiksu. Niepełny/nieczytelny obraz blokuje kasowanie; przed każdym
usunięciem ponowny guard C i claims. Dry-run pozostaje odczytowy, bez inicjalizacji stanu lub lock storage.
Raporty nie biorą zapisywalnej blokady: czytają generation i żywe tickety przed/po pełnym inventory;
zmiana lub równoległy writer daje czytelne retry/1 zamiast pozornie spójnego pustego raportu.

## Migracja, checkpointy i odzyskiwanie

1. Parser całych argv, nazwy/profil, platforma, stan i pełny plan kolizji są odczytowe. `--help` nie maskuje
   złych argumentów. Bare/removed entries kończą tu; odmowa/EOF/brak TTY niczego nie zapisuje.
2. Przed pierwszą potwierdzoną mutacją zbudować w pamięci kompletny inventory bin, `.active` i bezpośrednich
   wydań prefiksu. `find -print0` czytać do tablic przez strumień z jawnym końcowym statusem producenta;
   bez plików tymczasowych dla raportów i bez utraty błędów przez process substitution/pipeline.
   Sprawdzić finalny trailer/status i dopiero potem interpretować komplet; częściowy wynik daje błąd.
3. Adopcja opiera się na żywym dowodzie aktywności: główny link lub zadeklarowany alias -> poprawne własne
   wydanie. Skanować wszystkie linki, a nie tylko dzisiejsze główne nazwy. `nushell` daje jednego członka nu.
   Objąć starszą wersję, binary, bundle i bibliotekę; zapisać dowody oraz potrzebne dawne aliasy/metadane.
   Same nieaktywne wydania są dowodami do późniejszego uninstall, nigdy nowymi członkami.
   Expected-only i nieudowodnione broken pozostałości to protected/ignored. Legacy expected-tools czytać
   wyłącznie jako ignorowane wskazówki tej migracji; zachować bajty, nie przywracać z niego zestawu.
4. Po podglądzie i potwierdzeniu acquire locks oraz wspólna bramka recovery poprzedniego journalu (P0-003)
   dla KAŻDEGO install/uninstall/update, także wrappera. Przed ustaleniem nowej paczki lub nadpisaniem journalu
   rozliczyć udowodniony ukończony install/uninstall, włącznie z zapisem członkostwa. Częściowy wynik można
   zamknąć jako failed z zachowanym member i trwałymi dowodami tylko po kompletnym bezpiecznym rozpoznaniu;
   nie oznacza to zgody na dalsze kasowanie. Nierozstrzygalny journal -> protected/1, bez zastąpienia dowodów.
   Rozliczone wyniki zachować w stanie przy założeniu nowego journalu. Po normalizacji ponowić pełny preflight;
   zmiana wyboru/kolizji kończy 1 zamiast rozszerzenia dawnej zgody. Dopiero potem adopcja i nowa paczka.
   Kompletną adopcję publikować z `adoption_done=1`; przed publikacją brak przejęcia, po niej brak reimportu.
5. Nowy journal zapisuje kolejność i `queued/running/completed/failed/not-run`, cel oraz membership-before.
   Każdy ukończony tool publikuje swój wynik i członkostwo w tej samej nowej generacji; kolejny dopiero potem.
   Pierwszy błąd zatrzymuje paczkę. Raport rozróżnia sukcesy, błąd i niewykonany ogon; wcześniejsze sukcesy zostają.

**Install / naprawa per narzędzie:**

- Zdrowy pinned release ze wszystkimi aliasami: bez download, zapisać rzeczywiste członkostwo/wynik.
- Przed stagingiem journal przechowuje stare dokładne targety/absencje i dozwolone ścieżki publikacji.
  Przygotować nowe unikalne wydanie, zachować dotychczasowe; checksum/extract/probe kończy przed przełączeniem.
  Zakończony staging dostarcza walidowany receipt: marker, docelowy basename, layout/member i manifest danych.
  Receipt wraz z intencją rename zapisać w stanie przed przeniesieniem stagingu na finalny release.
- Przed każdym przełączeniem zapisać intencję linku; powtórzyć guard własności, wykonać przełączenie,
  zweryfikować dokładny nowy target. Cofanie rusza tylko link nadal wskazujący udowodnione nowe wydanie;
  odtwarza udowodniony stary target lub usuwa własny nowy link, nigdy podstawiony obcy obiekt.
- Dopiero wszystkie wymagane linki/assety/manifest zdrowe -> atomowy stan member+completed.
  Crash po publikacji linków przed zapisem: recovery potwierdza pełny receipt i kończy rzeczywisty sukces.
  Crash/awaria w połowie aliasów: bez fałszywego nowego członka; bezpieczne cofnięcie własnych przełączeń,
  zachowany wcześniejszy member, journal incomplete gdy cofnięcie nie jest bezpieczne lub I/O zawiedzie.
  Nowy częściowy tool nie jest dodawany przez późniejszy update; nieaktywne wydanie pozostaje bez auto-prune.

**Uninstall per narzędzie:**

- Najpierw preflight całego wyboru, także wszystkich wymaganych zapisanych/aktualnych aktywnych nazw/aliasów.
  Podmieniony aktywny link/niebezpieczna `.active` przerywa przed kasowaniem dowolnego wybranego narzędzia.
  Pełny skan zbiera wszystkie potwierdzone własne wydania nazwy, również inactive; reszta jest protected.
- Przed kasowaniem journal zachowuje kompletny zakres, dosłowne dowody oraz intencję usunięcia każdej ścieżki.
  Rewalidować bezpośrednio przed unlink/rm; brak już usuniętej ścieżki jest rozpoznawany tylko wraz z intencją.
  Po każdym usunięciu checkpoint; po pełnym rescanie zakresu publikować brak członka+completed razem.
- I/O/przerwanie z pozostałym własnym zakresem: członek zostaje, wynik 1/incomplete; update może go naprawić.
  Gdy cały zakres usunięto, lecz zapis zakończenia nie doszedł: recovery sprawdza intencje, brak własnego zakresu
  i brak podstawionych wymaganych ścieżek, kończy uninstall przed dowolną następną paczką. Nie wskrzesza go.
  Sam brak linku bez wcześniejszego journalu nie oznacza rezygnacji z zarządzania. Protected pozostałość poza
  zakresem nie blokuje sukcesu; wadliwy wymagany dowód lub niepełne kasowanie nie odłącza członkostwa.

**Update:** po walidacji i locks zakończyć recovery oraz jednorazową adopcję przed `fetch/reset`.
Zapisać cały zestaw i dowody sprzed refreshu oraz etap `project-refresh`; zachować obecne kody git/127 i cache.
Błąd fetch/reset nie uruchamia instalacji. Po sukcesie oznaczyć projekt jako odświeżony, `exec` świeży
prywatny continuation (bez nowej publicznej flagi/komendy) i uruchomić engine wyłącznie dla zapisanych nazw.
Brak definicji/assetu daje retired/unsupported i wynik 1, bez skasowania dowodów; pozostały zakres ma jawny wynik.
Pusty zestaw aktualizuje sam projekt. Po błędzie narzędzi komunikat mówi, że checkout już odświeżono;
nie deklaruje rollbacku. Journal o niepewnym wyniku refreshu wymaga ponownego sprawdzenia checkoutu,
nie domniemania sukcesu; nigdy nie wraca do pustego publicznego install ani listy profilu.

## Zadania, pliki i kolejność

Jedyny przyszły implementator i właściciel integracji: `/root/managed_lifecycle_implementer` (I).
Nie jest jeszcze uruchomiony/upoważniony. Zachowuje wcześniejsze i cudze zmiany; nie pracuje sam w repo.
Wszystkie poniższe kroki są sekwencyjne, bo dzielą guards, loader i testowe fixtures; brak korzyści z ich rozdzielania.
Osobny audytor implementacji musi być inną instancją niż planista i I. Koordynator prowadzi decyzje/historię.

| Zadanie | Zależność; własność I; odbiór przyrostu |
| --- | --- |
| T1 — dowody i inventory | Start; `common/release.sh`, `install/tool_inventory.sh`, `commands/tool_status.sh`, `install-tool/defs.sh`, `tools/defs/nvim.sh`; rozdzielić proof/health, status I/O, zachowane metadata retired i wymagania/manifest bundle; V2/V4. |
| T2 — stan, locks, recovery | T1; nowe `tools/lib/managed/{state,lock,inventory,migration,journal,recovery}.sh`, loader `tools/lib/managed.lib.sh`, `env.sh`; parser NUL, para/slots, adoption, per-tool checkpoints i ticket locks; V2/V3/V5. |
| T3 — bezpieczny engine install | T2; nowe `managed/install.sh`, `install/{install,dirs,defaults,tool_sets}.sh`, `install-tool/{main,install,download}.sh`, `install.lib.sh`, `install-tool.lib.sh`, `tools/install-tool.sh`; reuse, alias guards, staging receipts i rollback; V1/V2/V3/V4. |
| T4 — CLI install/uninstall | T3; `commands/{install,uninstall}.sh`, nowe `managed/uninstall.sh`; pełna walidacja/podgląd/TTY, additive state, wszystkie własne wydania, no-args nonmutation; V1/V2/V3. |
| T5 — update ze świeżego kodu | T4; `commands/update.sh`, nowe prywatne `managed/continue-update.sh`; adoption przed refresh, zapis etapów, exec i repair-set, zachować `update/check.sh`; V3/V5. |
| T6 — raporty i routing | T5; `bin/remote-ssh`, `commands.lib.sh`, nowe `commands/list.sh`, `commands/check/{environment,render}.sh`, `commands/check.sh`, `tool_status.sh`; wycofać ładowanie/fasady `tool.sh` i `doctor.sh`, przenieść potrzebną diagnostykę; V1/V4/V5. |
| T7 — bootstrap, teksty, prune i regresje | T6; `commands/prune.sh` — prefix-only lock, komplet claims/pending-receipts i guard C bez recovery; `runme.sh` tylko zależne teksty/forward, guide, rc i dokumenty; fixtures/testy, integracja; V1–V6. |

Niskopoziomowy `tools/install-tool.sh` nie może omijać stanu: zachować sprawdzenie opcjonalnej przypiętej
wersji, a poprawną instalację kierować do wspólnego engine z potwierdzeniem i bramką poprzedniego journalu.
Wewnętrzna instalacja wywołuje prywatny worker stagingu, bez rekurencji przez ten skrypt i bez publicznego bypassu.
Dotychczasowe testy payloadów przenieść na `remote-ssh install TOOL --yes`, pozostawiając testy odrzucenia
nieprzypiętych wersji. Nie dokumentować ścieżki skryptowej jako alternatywnej instrukcji użytkowej.
Wycofać runtime import/zapis `expected_tools.sh` oraz `read_expected_tools_for_current_platform`;
zachować wyłącznie ograniczony parser wskazówek w migration. Usunąć nieużywane stare fasady po przepięciu.
Diagnostykę rc z doctor zastąpić odczytem/sprawdzeniem składni w `bash -n`, bez source rc/hooków/importów.

T7 dokumenty: [AGENTS](../../AGENTS.md), [README](../../README.md), [install](../../docs/install.md),
[tools](../../docs/tools.md), [helpers](../../docs/shell/helpers.md), [flyline](../../docs/shell/flyline.md),
`commands/guide/{sections,tools}.sh`, `shell/rc.d/21-zoxide.sh` oraz bieżące odnośniki w dev dokumentacji.
[Plan fzf](fzf-retirement-plan.md): zachować zapis fazy 1 i dowody, dodać aktualny wariant host gate:
`install sk`, `check sk`, nowe pickery w nowej sesji, jawny `uninstall fzf`; bez expected-tools edit.
Nie zmieniać `defs/fzf.sh`, przypiętych map/checksumów ani `shell/navi-bin/{navi,fzf}`.

## Weryfikacja i kompletne pokrycie

V1–V6 poniżej to plan odbioru, nie wykonane testy. Nowe testy publicznych komend jako pytest subprocess;
używać izolowanych HOME/prefix/bin/XDG i lokalnego transportu. Nie mockować engine/ownership/state.

- **V1 CLI/wybór:** `test_entrypoint.py`, `test_install_cli.py`, przekształcony `test_install_expected_tools.py`
  w `test_managed_lifecycle.py`, `test_uninstall.py`, `test_runme.py`: pełna tabela argv/help/TTY, nieznane,
  profile/deduplikacja, removed entries, snapshot wszystkich ścieżek oraz sentinel sieci przed odmową/błędem.
- **V2 proof/migracja:** `test_release_ownership.py`, `test_tool_link_state.py`, nowe `test_managed_state.py`:
  trzy layouty, old version, nu alias-only, expected-only, inactive, foreign, odczyt/partial find/readlink I/O.
  Po poprawnym zapisie usunąć member, podmienić rodzica/marker/leaf (symlink, dangling, directory), selektor
  na obcy zwykły plik/link: osobno wynik B i odmowa C, retained member; także retired i wszystkie layouty.
  Sprawdzić writable prefix z niewritable rodzicem i fizyczne aliasy ścieżek.
- **V3 awarie:** nowe `test_managed_recovery.py` i `test_managed_concurrency.py`, rozszerzone
  `test_install_failures.py`/`test_update.py`/`test_uninstall.py`: stuby transportu i kontrolowane błędy
  mkdir/ln/mv/rm/read/write, bariery subprocess oraz TERM/SIGKILL przed/po każdym checkpointcie.
  Macierz: adopcja; drugie narzędzie; stage->release; każdy alias; finalny stan; każde kasowanie; finalny
  uninstall receipt; refresh->exec. Sprawdzić retry, rollback tylko własnego linku, nieukończony nowy tool,
  ukończony-on-disk uninstall -> SIGKILL -> unrelated install -> update bez resurrection; analogiczny install
  zachowuje poprzedni sukces. Nierozstrzygalnego journalu nie nadpisuje żadne wejście, włącznie z wrapperem.
  Dwa writers, choosing, martwy PID, odmowa i read-only raport; awarie/podmiany z V2 także między checkpointami.
- **V4 raport/layout:** `test_tool_list.py` przenieść na top-level list, `test_check.py`, `test_doctor.py`
  przenieść na część środowiskową check, `test_install_{binary,bundle,library}.py`, `test_tool_assets.py`:
  wszystkie statusy/filtry/kody, PATH fizyczny/relatywny/pusty, aliasy, required bundle data, no exec/load/cache.
  Biblioteki: offline mocked probe sprawdza przepływ/checksum/member/libc i ochronę starych plików;
  natywna kwalifikacja tylko na jawnie dostępnym zgodnym Bash >=4.4 i właściwej bibliotece, bez pobierania.
  Brak natywnego środowiska oznacza jawne skipped/unverifiable dla ABI, nigdy dowód z samego stubu.
- **V5 update/izolacja:** lokalne upstream checkouty w `test_update.py`; dokładny AC-023: rg/fd/sk/flyline/nvim/nu,
  stary rg i nu wyłącznie przez nushell, expected tylko flyline, świeży kod bez definicji rg. Zachować sześć nazw,
  retired i niezerowy wynik; AC-024 A/B/XDG/corrupt/copy-record oraz pusty zestaw i brak wskrzeszenia navi.
- **V6 regresje/odbiór:** `test_fzf_retirement.py`, `test_prune.py`, `test_guide.py`, dotychczasowe shell/setup/SSH/Git/
  scripts/update-check/Navi tests; readonly bin 0555/custom alias i readonly checkout dla prune --apply.
  V3/V6: prune-versus-publication oraz SIGKILL po stage->release -> prune -> retry; pending release nie znika,
  także z journalu drugiego slotu; niepełne claims blokują kasowanie, prune nie wykonuje ich recovery.
  Targeted pytest po przyrostach, potem jeden pełny `just smoke`.
  RUNTIME_BASHES musi faktycznie zawierać Bash 3.2 oraz dostępny nowy Bash; wykazać env-bash dzieci.
  Nie pobierać Navi/skim/native library ani nie wykonywać `test-assets-live`; podać powody real-binary skips.

| REQ | Zadania | Odbiór |
| --- | --- | --- |
| REQ-001 | T4,T6 | V1: AC-001–003 |
| REQ-002 | T3,T4 | V1,V5: AC-004,008 |
| REQ-003 | T1,T3 | V2,V4: AC-005–006,018 |
| REQ-004 | T2–T5 | V2,V3,V5: AC-004,009–011,014,017,024 |
| REQ-005 | T1,T2,T5 | V2,V3,V5: AC-011–014,023–024 |
| REQ-006 | T1,T6 | V1,V4: AC-002,012,014–016 |
| REQ-007 | T2,T4,T5,T7 | V1,V2,V5: AC-011,013,021 |
| REQ-008 | T2,T4 | V1,V2,V3: AC-007–010,022 |
| REQ-009 | T2,T5 | V3,V5: AC-008–010,017,023–024 |
| REQ-010 | T1,T2,T4–T6 | V2,V4,V5: AC-010,015,023 |
| REQ-011 | T1,T6 | V4,V5: AC-009,012,015,023 |
| REQ-012 | T1,T6 | V4: AC-016,018 |
| REQ-013 | T1,T6 | V4,V6: AC-009–010,015–016,021 |
| REQ-014 | T1–T5 | V2,V3,V5: AC-005–006,010,013–014,017,022–024 |
| REQ-015 | T3,T4,T7 | V3,V4,V6: AC-005,017–018,020,022 |
| REQ-016 | T2–T5 | V3,V5: AC-017,022–023 |
| REQ-017 | T2,T4,T7 | V1,V3: AC-003,017,019,022 |
| REQ-018 | T1,T3,T6,T7 | V2,V4,V6: AC-018,020,023 |
| REQ-019 | T3,T4,T7 | V1,V6: AC-007,019–020 |
| REQ-020 | T5–T7 | V6: AC-020 |
| REQ-021 | T6,T7 | V6: AC-021 |
| REQ-022 | T6,T7 | V1,V6: AC-001,020–021 |

| AC | Zadania | Konkretna grupa odbioru |
| --- | --- | --- |
| AC-001 | T4,T6,T7 | V1 removed inputs i snapshot bez zmian |
| AC-002 | T4,T6 | V1 bare/help na nowej i starej lokalizacji |
| AC-003 | T4,T6 | V1 cała gramatyka, TTY/EOF/odmowa |
| AC-004 | T2–T4 | V1 additive/profile/dedup |
| AC-005 | T1,T3 | V2,V4 reuse i naprawa/chroniona kolizja |
| AC-006 | T1,T3 | V2 external PATH i local foreign |
| AC-007 | T2,T4 | V1,V2 uninstall wszystkich własnych wydań/no-op |
| AC-008 | T4,T5 | V5 profil zmieniony po uninstall |
| AC-009 | T2,T5,T6 | V4,V5 missing/broken i empty update |
| AC-010 | T1,T2,T4–T6 | V2,V5 retired/unsupported, safe retired uninstall |
| AC-011 | T1,T2 | V2 adopcja czterech bez/ze starą listą |
| AC-012 | T1,T6 | V4 read-only sentinel i filesystem snapshot |
| AC-013 | T1,T2 | V2 rejected adoption candidates |
| AC-014 | T1,T2,T6 | V2 partial enumeration/state corruption/escape |
| AC-015 | T1,T6 | V4 kompletne union/filter/sort/exit |
| AC-016 | T1,T6 | V4 health/env/PATH/alias zakres i kody |
| AC-017 | T2–T5 | V3 wszystkie checkpointy i V5 git failures |
| AC-018 | T1,T3,T6 | V4 trzy layouty, Bash3.2, libc/probe boundary |
| AC-019 | T3,T4,T7 | V1,V6 runme/ref/CLI/footer/startup snapshots |
| AC-020 | T5–T7 | V6 niezwiązane komendy i informational checks |
| AC-021 | T6,T7 | V6 fzf bytes/gate/hints/Navi pass-through |
| AC-022 | T1,T2,T4,T5 | V2,V3 active+inactive+protected/foreign active abort |
| AC-023 | T1,T2,T5,T6 | V5 sześć narzędzi przed pierwszym refresh |
| AC-024 | T2–T6 | V5 pary A/B i XDG oraz tombstone uninstall |

## Integracja, ryzyka i proponowane commity

Główne ryzyko to złożoność journalu/locks; dlatego T2 kończy się failure-injection przed podłączeniem engine.
Stan w prefiksie ogranicza zależność od XDG i zachowuje ustawienia miejsca instalacji, kosztem prywatnych
metadanych obok wydań. Wspólne storage i ścieżki dwóch lokalizacji nie usprawiedliwiają cudzej własności.
Parser dowodu dla retired nie może rozluźnić prune ani zamienić uszkodzonego znacznika w prawo kasowania.
Biblioteka pozostaje granicą natywnej kwalifikacji; raport strukturalny nie obiecuje załadowania w każdej sesji.
Brak nowych decyzji produktu/blokad. Luka specyfikacji wykryta w implementacji wraca do koordynatora,
z dowodem i opcjami; nie redukować wymagań, aby dopasować kod.

Organizacyjne grupy commitów po osobnej autoryzacji: (1) T1–T2 dowody/state/recovery z testami,
(2) T3–T5 engine i mutujący CLI/update, (3) T6 raporty/routing, (4) T7 teksty i końcowe regresje.
To podział review, bez stage/commit obecnie; pośrednie grupy nie są samodzielnymi wdrożeniami nowego CLI.
Przed audytem I integruje wszystkie kroki, zapisuje rzeczywiste komendy/wyniki/skips i listę zmian.
Koordynator dopiero po akceptacji planu zamraża jego bajty/manifest oraz zakłada execution/history,
stan `implementing`, runda 0. Audytor ocenia specyfikację, plan i technikę; naprawy zachowują limit workflow.

Rewizja 0.2 po review 0: wyłącznie P0-001 (żywe C vs dokładny B), P0-002 (prune locks/claims/ownership)
i P0-003 (wspólna bramka journalu), z odpowiadającymi testami. Specyfikacja i zakres pozostają niezmienione.
