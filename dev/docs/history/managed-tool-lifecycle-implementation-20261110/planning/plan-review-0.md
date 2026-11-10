# Niezależny przegląd planu 0

**Wynik: Findings.** Plan 0.1 mapuje cały zaakceptowany zakres, lecz wymaga trzech wąskich korekt technicznych przed akceptacją. Nie jest to audyt implementacji ani ponowny przegląd potrzeb produktu.

- Przedmiot: `PLAN-MANAGED-TOOL-LIFECYCLE` 0.1, `/private/tmp/remote-ssh-managed-lifecycle-planning-20261110/managed-tool-lifecycle-implementation-plan-0.1.md`.
- Zweryfikowany SHA-256 planu: `f1e8b87976356e345c6c0f11ecc27e4976b1fbb44fbaab9e2a9eb984a053c0ab`.
- Podstawa: manifest `dev/docs/history/managed-tool-lifecycle-20261110/baseline-1/baseline.json`; dokładna kopia `SPEC-MANAGED-TOOL-LIFECYCLE@0.3`, SHA-256 `62a53a9ae528dba9ca1d0943c014c557490bec897d638b998902ca16fe56ffbb`; akceptacja w zdarzeniu 13 historii.
- Kod: HEAD `15bcb79cee2d1959074d4c70e164d0cae75ee8e2`, bez zmian śledzonych plików. Audytor `/root/managed_lifecycle_auditor` nie jest autorem planu ani przyszłym implementatorem.

## Wymagane korekty

| ID | Waga | Miejsce planu | Problem, wpływ i wąska korekta |
| --- | --- | --- | --- |
| P0-001 | wysoka | „Własność oddzielona od zdrowia”, linie 71–82; T1/T3/T4 i V2/V3 | Plan pozwala uznać zapisane wydanie bez payloadu za własne na podstawie żywego markera i wcześniejszego receipt, lecz nie ustala pełnego odpowiednika dotychczasowego **żywego** warunku kasowania. Obecny validator wymaga aktualnego regularnego, niesymlinkowanego membera i fizycznie zawartego rodzica; sam zapis dawnego poprawnego markera/membera nie dowodzi bieżącego drzewa. Nie wolno po rozdzieleniu health/proof przenieść tych kontroli wyłącznie do health i dopuścić rekursywnego kasowania po ich porażce. Rozdzielić warunki bezpiecznej naprawy/przełączenia dokładnego własnego linku od warunków usunięcia całego wydania. Jawnie określić żywą walidację wszystkich istniejących składowych ścieżki, markera, granic i targetu dla missing/broken/retired; brak dostatecznego dowodu ma zachować ochronę i członkostwo. Jeżeli plan zachowuje payload-independent deletion, musi wskazać, czym aktualny dowód jest co najmniej równie silny, zamiast samym receipt zastępować utraconą przesłankę. Dodać do V2/V3 scenariusze: uprzednio poprawny zapis, potem brak membera oraz podmiana jego rodzica/markera/finalnej ścieżki, w tym uszkodzony symlink i obce pliki. |
| P0-002 | wysoka | „Konkurencja bez flock”, linie 93–106; wrapper prune, linia 81; T2/T7 | Zapis locków wewnątrz każdego prefix/bin/checkout jest wymagany także dla `prune --apply`. To odbiera istniejące wsparcie odczytowego bin: `test_prune_accepts_readonly_bin_and_unusual_custom_alias` sprawdza sukces apply przy mode 0555 bin. Ponadto wrapper wymienia ochronę aktywnych odnośników, lecz nie ochronę finalnego wydania wskazanego przez pending journal: po crashu między stage→release a publikacją linku taki katalog wygląda jak nieaktywna kandydatura do prune. Same locks nie chronią go po śmierci writera. Doprecyzować zestawy blokad per komenda/storage bez nowego wymogu zapisu do bin/checkout dla prune; dodać odczytową ochronę wydań wskazanych przez nierozliczone journal/receipts i claims innych lokalizacji wspólnego prefiksu, bez wykonywania ich recovery przez prune. Niepełny/nieczytelny obraz claims musi blokować zależne kasowanie. Jawnie przypisać `tools/lib/commands/prune.sh` zadaniu/właścicielowi. Zachować test readonly bin i dodać testy prune-versus-publication oraz crash→pending-release→prune→wznowienie, w tym drugi slot lokalizacji. Zachować konserwatywny zakres i default dry-run prune. |
| P0-003 | wysoka | Ogólna sekwencja migracji/checkpointów, linie 110–128; recovery uninstall, linie 151–158; update, linie 160–167 | Recovery poprzedniego journalu jest wyraźnie wymagane przed nową paczką tylko dla update. Ogólna sekwencja przechodzi do zapisu nowego journalu, nie określając wspólnej bramki dla install/uninstall. Przykład: uninstall usunął cały własny zakres navi, proces zginął przed zapisem member=false; następny `install rg` nie może nadpisać jedynego journalu tego zakończonego uninstall, zostawić navi członkiem i później wskrzesić go przez update. Wymagać dla wszystkich wejść lifecycle (także wrappera niskopoziomowego) normalizacji/recovery istniejącego journalu pod blokadą **przed jego zastąpieniem i ustaleniem nowej paczki**. Ustalić bezpieczny wynik dla journalu nierozstrzygalnego: ochrona, błąd i brak nadpisania dowodów. Nie oznacza to automatycznej zgody na dokończenie niepewnego kasowania. Dodać test zakończony-na-dysku-uninstall → SIGKILL → unrelated install → update oraz analogiczny test wcześniejszego ukończonego install. |

P0-001 dotyczy zachowania REQ-014 i D-011, nie nowego żądania produktu. Plan może zachować konserwatywną odmowę kasowania przy niewystarczającym dowodzie. Nie stwierdzono potrzeby zmiany zaakceptowanej specyfikacji. P0-002/P0-003 są zwykłymi poprawkami technicznymi planu.

Sugestie opcjonalne: brak; nie dodaje się funkcji ani rozszerzeń zakresu.

## Pokrycie wymagań i AC

`met` oznacza dostateczne **pokrycie i wykonalność w planie**, nie działający runtime. Wszystkie 22 REQ i wszystkie 24 AC mają unikalny wiersz mapowania do zadań i V1–V6. Obecność wiersza nie znosi problemów technicznych poniżej.

| REQ | Ocena | Podstawa |
| --- | --- | --- |
| REQ-001 | met | T4/T6, V1: pełna gramatyka, bare/removed nonmutation i help. |
| REQ-002 | met | T3/T4, V1/V5: additive, profile i dedup bez subskrypcji. |
| REQ-003 | met | T1/T3, V2/V4: reuse/repair, aliasy, zewnętrzny PATH i kolizje; destrukcyjny guard wymaga osobnej P0-001. |
| REQ-004 | unmet | T2–T5 pokrywają format i wyniki, ale P0-003 wymaga bramki odzyskania przed nadpisaniem journalu. |
| REQ-005 | met | T1/T2/T5, V2/V3/V5: pełna adopcja przed refresh, alias-only i trzy layouty. |
| REQ-006 | met | T1/T6, V1/V4: raport bez zapisu/cache/exec/load, generacje i writer retry. |
| REQ-007 | met | T2/T4/T5/T7: legacy hints bez wyboru, edycji lub późniejszego importu. |
| REQ-008 | unmet | Pełny zakres uninstall i checkpointy są opisane; P0-001/P0-003 muszą zachować dowód i ukończone usunięcie. |
| REQ-009 | unmet | Pre-refresh adopcja/exec/repair-set są wykonalne; P0-003 zostawia drogę do resurrection po innej komendzie. |
| REQ-010 | met | T1/T2/T4–T6 zachowują metadata i retired/unsupported; P0-001 obowiązuje przy kasowaniu. |
| REQ-011 | met | T1/T6, V4/V5: union katalogu i stanu, filtry, porządek, broken/retired. |
| REQ-012 | met | T1/T6, V4: środowisko, zakres, PATH i library; rc przez bash -n bez hooków. |
| REQ-013 | met | T1/T6, V4/V6: statusy, kody i informacyjny fzf. |
| REQ-014 | unmet | P0-001: receipt nie może milcząco zastąpić żywych strukturalnych przesłanek kasowania. |
| REQ-015 | unmet | Staging/immutability/rollback są szczegółowe; P0-002 narusza zachowywany kontrakt prune. |
| REQ-016 | unmet | Journal per tool i intencje są opisane; P0-003 potrzebna dla dowolnej kolejnej komendy, P0-002 dla ochrony jego wydania przed prune. |
| REQ-017 | met | T2/T4/T7, V1/V3: odczytowy preflight, potwierdzenie, rewalidacja pod locks. |
| REQ-018 | met | T1/T3/T6/T7, V2/V4/V6: bez nowych deps, Bash 3.2, przypięte assety i jawny ABI skip. |
| REQ-019 | met | T3/T4/T7, V1/V6: CLI publication, footer, startup protection i runme/REF. |
| REQ-020 | unmet | Weryfikacja regresji jest szeroka, ale P0-002 zmienia wsparcie prune z readonly bin. |
| REQ-021 | met | T6/T7, V6: fzf manifest i adapter nietknięte, gate i prywatny pass-through. |
| REQ-022 | met | T6/T7, V1/V6: bieżące instrukcje i teksty mają właściciela; historia pozostaje historią. |

Mapowanie AC-001–024 jest kompletne i bez duplikatów. P0-001 dotyka zwłaszcza odbioru AC-005/AC-006/AC-010/AC-014/AC-022; P0-002 — AC-017/AC-020/AC-024 i regresji prune; P0-003 — AC-017 oraz braku resurrection z AC-008/AC-022/AC-024. Po doprecyzowaniu planu potrzebna jest ponowna ocena tych powiązań.

## Faktycznie sprawdzone i granice

- Przeczytano pełne 300 linii konkretnego planu, przekazanie i check autora; zweryfikowano manifest i hash zamrożonego snapshotu, akceptację oraz hash planu.
- Niezależnie potwierdzono 22/24 dokładne unikalne wiersze mapowania i 18 istniejących lokalnych linków rozwiązanych względem przyszłego `dev/docs/managed-tool-lifecycle-implementation-plan.md`.
- Wykorzystano wcześniejsze dowody niezmienionego kodu/specyfikacji. Dodatkowy odczyt ograniczono do live ownership validatora, prune, definicji i wskazanych testów guardów/readonly bin. Nie wykonywano testów ani eksperymentów.
- Bakery tickets z choosing/ticket, wspólną kolejnością rootów, konserwatywnym PID reuse i exec zachowującym PID są sensownym kierunkiem bez flock. Ich poprawność pozostaje do wykazania failure-injection/concurrency z V3; ten przegląd nie dowodzi algorytmu ani implementacji.
- Zaakceptowany model wiąże stan z **efektywną parą prefix/bin** (snapshot, linie 133–137). Nie zawiera wymagania związania rekordu z fizycznym checkoutem; nie dodano takiej wymaganej poprawki. Spójność checkoutu i bezpieczna publikacja CLI pozostają oddzielnymi wymaganiami.
- Przyszły plan projektowy i historia cyklu implementacji nadal nie istnieją. Raport znajduje się wyłącznie w autoryzowanym scratch. Nie odczytano sekretów/dev/.env/danych hosta; bez sieci, mutacji Git lub runtime.
- Następny krok: wąska rewizja planisty, niezależny ponowny przegląd, potem przedstawienie konkretnego planu człowiekowi. Nie rozpoczęto implementacji i nie zużyto jej rund naprawczych.
