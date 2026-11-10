# Przegląd specyfikacji 0 — managed tool lifecycle

**Wynik: Findings.** Wymagane są dwie korekty kontraktu. Nie jest to audyt implementacji ani akceptacja potrzeb za człowieka.

- Dokument: `dev/docs/managed-tool-lifecycle-specification.md`, `SPEC-MANAGED-TOOL-LIFECYCLE`, wersja `0.1`, status `draft`.
- SHA-256 sprawdzonych bajtów: `7bb447b30f57b8a2cf391262bf0996a80f0eec1df1d0e8caa43091c7abb7e958`.
- Podstawa kodu: `15bcb79cee2d1959074d4c70e164d0cae75ee8e2`; HEAD zgodny, brak zmian śledzonych plików podczas przeglądu.
- Przegląd 0; `specification_revision_round: 0`; manifest: brak, dokument niezatwierdzony.
- Audytor: `/root/managed_lifecycle_auditor`, osobna instancja bez udziału w autorstwie. Przedmiot oceny pozostał bez zmian.
- Zakres: samodzielna specyfikacja zmiany i jej niezbędny kontekst źródłowy. Odczytano bieżące kontrakty Kei, główny projektowy `AGENTS.md`, historię zadania i przekazanie autora.

## Wymagane korekty

| ID | Waga | Miejsce | Ustalenie i wymagany wynik |
| --- | --- | --- | --- |
| R0-001 | średnia | Specyfikacja: AC-004 i AC-008, linie 354 i 358; gramatyka: linie 168–176 i 193–194 | Kryteria używają `install quick` jako instalacji profilu. Gramatyka traktuje argument pozycyjny jako dokładną nazwę narzędzia i wymaga `install --profile quick` dla profilu. `quick` nie jest narzędziem katalogu. Poprawić te konkretne przykłady, aby odbiór nie wymagał sukcesu dla wejścia, które kontrakt każe odrzucić. Nie dodawać aliasu ani nowej składni. |
| R0-002 | średnia | Specyfikacja: REQ-008, REQ-015, tabela uninstall i AC-007/AC-010; linie 149, 156, 196, 357 i 360 | Nie jest jednoznaczny zakres kasowania wydań wybranego narzędzia. REQ-008 pozwala usuwać własne „linki/wydania”, natomiast REQ-015 pozostawia decydowanie o nieaktywnych wydaniach `prune`. Nie wiadomo, czy poprawny uninstall usuwa tylko aktywne/zapisane wydanie, czy także wszystkie udowodnione nieaktywne wydania tej samej nazwy. Oba warianty dają różny stan dysku i różne granice „niepełnego usunięcia” z D-011. Jawnie określić oczekiwany zakres oraz warunek kompletnego uninstall; dodać AC z aktywnym wydaniem, starszym własnym wydaniem i nieudowodnioną pozostałością. Zachowanie istniejącego kodu można zaproponować do akceptacji dokumentu, ale nie wolno traktować samego faktu F-009 jako decyzji człowieka. |

Dowód istotności R0-002: bieżący `tools/lib/commands/uninstall.sh`, funkcja `remote_ssh_cmd_uninstall_collect_release_dirs_for_tool`, zbiera wszystkie udowodnione wydania wybranej nazwy w prefiksie. `dev/tests/test_uninstall.py::test_uninstall_scans_symlinked_prefix_and_preserves_foreign_paths` sprawdza usunięcie aktywnego oraz starego własnego wydania także przy jawnym wyborze nazwy, zachowując nieoznaczony katalog i obce ścieżki. Specyfikacja powinna jawnie zachować ten efekt albo jawnie zaproponować jego zmianę.

R0-001 nie wymaga nowej decyzji produktu. R0-002 wymaga jawnego kontraktu zakresu usuwania i jego akceptacji przez człowieka wraz z konkretną wersją dokumentu; audytor nie wybiera wariantu za człowieka. Pozostałe A-001–A-003 i proponowane szczegóły CLI nadal podlegają zwykłej akceptacji szkicu.

## Sugestie opcjonalne

| ID | Miejsce | Sugestia |
| --- | --- | --- |
| S0-001 | REQ-005, REQ-009–010; AC-011/AC-017 | Wzmocnić odbiór migracji scenariuszem pierwszego `update` bez nowego stanu: legacy lista zawiera tylko flyline, świeży checkout usuwa jedną wcześniej znaną definicję. Sprawdzić zachowanie całego udowodnionego zestawu i dowodów sprzed refreshu oraz widoczny retired. Uzupełnić przekrój migracji o bundle, starszą wersję i aktywność wyłącznie przez własny alias. Wynik wymagany już przez kontrakt; sugestia dotyczy precyzji jego odbioru. |
| S0-002 | Model lokalizacji, linie 132–136; REQ-004/REQ-014 | Dodać konkretny AC dla różnych efektywnych par prefix/bin i zmian XDG, potwierdzający brak przejęcia obcego stanu, kasowania poprzedniej lokalizacji i utraty skutecznego uninstall. |

## Pokrycie REQ

`met` oznacza jakość i sprawdzalność kontraktu specyfikacji, nie spełnienie wymagania przez istniejący runtime. Wiersze `unmet` wskazują potrzebną korektę dokumentu.

| Wymaganie | Ocena | Dowód lub uzasadnienie |
| --- | --- | --- |
| REQ-001 | unmet | Gramatyka i walidacja są opisane oraz mają AC-001–003, ale R0-001 daje sprzeczny przykład odbioru profilu. |
| REQ-002 | unmet | Addytywność, deduplikacja i brak subskrypcji są jasne; AC-004/AC-008 wymagają poprawnej składni profilu, R0-001. |
| REQ-003 | met | Jawna weryfikacja/naprawa, brak pobrania zdrowego narzędzia i ochrona external PATH; UC-002, AC-005–006/AC-018. |
| REQ-004 | met | Automatyczny stan, zachowanie uszkodzonych członków, ochrona wadliwego stanu; AC-004/AC-009/AC-014/AC-017. |
| REQ-005 | met | Jednorazowa adopcja wszystkich udowodnionych aktywnych instalacji, trzy layouty i stare wersje; UC-005, AC-011/AC-013–014/AC-017; S0-001 wzmacnia przekrój. |
| REQ-006 | met | Wyraźny read-only bez uruchamiania payloadu i bibliotek; UC-005–007, AC-012/AC-014. |
| REQ-007 | met | expected-tools bez sterowania i bez edycji; expected-only nie daje własności; AC-011/AC-013/AC-021. |
| REQ-008 | unmet | Jawne nazwy, retained state przy błędzie i brak resurrection są jasne; dokładny zakres usuwania wydań wymaga R0-002. |
| REQ-009 | met | Refresh oraz świeży kod, naprawa zapisanego zestawu, pusty zestaw i brak przywracania uninstall; UC-004, AC-008–009/AC-017. |
| REQ-010 | met | Zachowanie dowodów oraz retired/unsupported i błędy update; AC-010/AC-015; S0-001 wzmacnia pierwszy refresh. |
| REQ-011 | met | Zakresy list, stabilna kolejność i brak ukrywania missing/broken/retired; UC-006, AC-015. |
| REQ-012 | met | Środowisko plus wybrany zakres narzędzi, konkretne następne działania i rozróżnienie bibliotek; UC-007, AC-016/AC-018. |
| REQ-013 | met | Tabela rozdziela statusy i skutki check; AC-009–010/AC-015–016/AC-021. |
| REQ-014 | met | Własność niezależna od członkostwa; błędy inwentaryzacji, obce ścieżki i .active chronione; AC-006/AC-010/AC-013–014. |
| REQ-015 | unmet | Staging, immutability i ochrona starego payloadu mają AC-005/AC-017–018; relacja zakresu uninstall do nieaktywnych wydań/prune wymaga R0-002. |
| REQ-016 | met | Wyniki per narzędzie, brak obietnicy transakcji całej paczki, odzyskanie bez resurrection; UC-008, AC-017. |
| REQ-017 | met | Walidacja/podgląd przed zgodą i zapisem, TTY/EOF/odmowa/--yes; UC-001/UC-003, AC-003/AC-019. |
| REQ-018 | met | Wiążące layouty, przypięte manifesty/libc/checksumy, Bash 3.2, odrębna kwalifikacja biblioteki i brak nowych zależności; AC-018/AC-020. |
| REQ-019 | met | Sam CLI, bez edycji startup files, jawny shell, runme/REF/forward; UC-001, AC-019. |
| REQ-020 | met | Niezwiązane zachowania i informacyjne update-check odróżnione od top-level check; AC-020. |
| REQ-021 | met | Faza 1 fzf i adapter zachowane, informacyjna migracja, brak automatycznej zmiany findera; UC-009, AC-021. |
| REQ-022 | met | Wskazane bieżące dokumenty, help/guide i operacyjna instrukcja fzf; historia odróżniona od instrukcji; AC-001/AC-020–021. |

## Sprawdzenia i ograniczenia

- Niezależnie potwierdzono 22 unikalne sekwencyjne REQ, 21 AC, 9 UC i 48 istniejących lokalnych linków pozostających w projekcie. Zweryfikowano hash przed i po analizie struktury.
- Potwierdzono istotne fakty F-001–F-009 na dispatcherze, install, expected-tools, inventory, release validator, update, check/doctor, tool sets/runme i uninstall; przeczytano powiązane wybrane asercje testów. F-010 porównano z AGENTS, instalatorem biblioteki i kontraktem wydań; F-011 z planem fzf. Nie jest to pełny audyt kodu ani całych historycznych raportów.
- Bieżący validator własności wymaga definicji i istniejącego payloadu. Specyfikacja poprawnie odróżnia nową trwałą informację o członkostwie od prawa do kasowania; jej wykonalność, format stanu i odporność na awarie będą wymagały późniejszego planu i audytu implementacji.
- Zweryfikowano brak zagnieżdżonych AGENTS w czytanych ścieżkach. Nie odczytano `dev/.env`, sekretów, rzeczywistego expected-tools ani innych danych hosta. Nie wykonano sieci, instalacji, migracji, kasowania ani zmian Git.
- Nie uruchamiano smoke, pytest ani live asset checks. Nie potwierdzają one jakości samego kontraktu, a zadanie nie obejmuje implementacji. Żaden AC nie jest tu oznaczony jako zaliczony runtime.
- Brak blokady dostępu do potrzebnych dowodów. Po korekcie dokumentu potrzebny ponowny niezależny przegląd konkretnej wersji. Po Pass nadal wymagana jest akceptacja człowieka i zamrożenie podstawy; bez automatycznego planowania lub implementacji.
