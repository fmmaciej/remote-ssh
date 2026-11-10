# Niezależny audyt implementacji 0

**Wynik: Findings.** Dwie wymagane poprawki dotyczą traktowania dowodów zakończonego uninstall jako nadal bieżącej instalacji. Pierwsza może trwale zablokować kolejne operacje lifecycle. Specyfikacja i zaakceptowany plan nie wymagają zmiany.

- Cykl: `managed-tool-lifecycle-implementation-20261110`; `repair_round: 0`.
- Podstawa: `dev/docs/history/managed-tool-lifecycle-implementation-20261110/baseline-1/baseline.json`; dokładne snapshoty `SPEC-MANAGED-TOOL-LIFECYCLE@0.3` i `PLAN-MANAGED-TOOL-LIFECYCLE@0.2` zweryfikowane.
- Kod bazowy: `9a223dcca76072eb9035316d25abf972902d3289`. Przedmiot: 88 wpisów `increment-03/source-hashes.json`; wszystkie zgodne przed i po niezależnych sprawdzeniach.
- Audytor: `/root/managed_lifecycle_auditor`, bez autorstwa specyfikacji, planu lub implementacji. Bez edycji przedmiotu i historii; własne zapisy tylko w przydzielonym scratch.

## Wymagane poprawki

### A0-001 — ponowny uninstall tworzy nierozliczalny journal i blokuje dalszą pracę

**Waga: wysoka.** Dotyczy REQ-004, REQ-008, REQ-009 i REQ-016, w szczególności no-op z AC-007 oraz odzyskiwalności z AC-017.

Reprodukcja w całkowicie syntetycznym offline fixture, na obu interpreterach:

```text
install rg --yes       -> 0
uninstall rg --yes     -> 0
uninstall rg --yes     -> 1, "Uninstall incomplete: rg"
install fd --yes       -> 1, "Preflight changed or is protected; retry install."
```

`tools/lib/managed/uninstall.sh:22` zbiera dawne rekordy release. Linie 26–31 dodają do zakresu również nieistniejące wydanie, którego członkostwo i payload poprawnie usunęła poprzednia operacja. Preflight kwalifikuje więc powtórzenie jako nową operację zamiast no-op. `tools/lib/managed/journal.sh:55` usuwa te stare receipts przy archiwizacji zakończonego uninstall, już po wyliczeniu zakresu następnej operacji. Nowy journal/item zostaje zapisany, ale utworzenie remove-intent nie przechodzi walidacji bez usuniętych receipts. Na dysku pozostaje `phase=tools`, item `running` bez wystarczających intencji. Wspólna bramka recovery blokuje następny install; zwykłe ponowienie nie naprawia wyniku.

Dowody: `auditor-safe/test_audit_sequences.py::test_repeated_successful_uninstall_is_readonly_noop` — 2 niepowodzenia; `auditor-safe/test_audit_followup.py::test_repeat_uninstall_does_not_block_later_unrelated_install` — 2 niepowodzenia. Oba przypadki występują w Bash 3.2.57 i 5.3.20. Logi i JUnit pochodzą wyłącznie ze świeżego allowlisted runnera.

Wymagany rezultat naprawy: dowody zakończonego uninstall pozostają historią/recovery evidence, lecz nie stają się nowym wymaganym zakresem nieobecnego narzędzia. Powtórny uninstall ma dać 0 bez zmian stanu/ścieżek; następny install/update ma nadal działać. Nie usuwać ani nie zastępować nierozstrzygniętych dowodów rzeczywiście nieukończonej operacji. Test odbioru musi zawierać **natychmiastowe powtórzenie po sukcesie**, a nie tylko uninstall narzędzia nigdy nieinstalowanego. Dotychczasowy `test_uninstall_known_absent_is_readonly_noop` obejmuje właśnie ten drugi przypadek, dlatego pełny smoke nie wykrył tej sekwencji.

### A0-002 — list przedstawia zakończony uninstall jako brakującą/uszkodzoną instalację

**Waga: średnia.** Dotyczy REQ-011/REQ-013 oraz tabeli statusów (`available` wobec missing/broken), odbioru AC-015.

Bezpośrednio po poprawnym `install rg --yes` i `uninstall rg --yes`, `list` daje 0, ale wiersz brzmi:

```text
rg  unmanaged  supported  missing broken last=uninstall:completed
```

`tools/lib/commands/tool_status.sh:107` wybiera usunięty root z historycznych selector receipts także bez członkostwa. Linie 142–144 uznają ten dawny root za podstawę missing, a późniejszy health check dodaje broken. Znana wspierana pozycja poprawnie usunięta, bez rzeczywistej awarii, powinna być dostępna i niezarządzana. Dopiero jawny check nieinstalowanej nazwy ma diagnozować missing/external-only.

Dowód: `auditor-safe/test_audit_sequences.py::test_successfully_uninstalled_tool_is_available_in_catalog` — 2 niepowodzenia na obu Bash. Klasyfikacja musi być poprawna już przed jakąkolwiek następną mutacją. Raport nie może archiwizować journalu ani zapisywać stanu w celu naprawienia samego widoku. Zachować widoczność faktycznie zarządzanych missing/broken oraz failed/not-run.

## Zgodność z planem i istotne wyniki pozytywne

T1–T7 są zintegrowane: osobne A/B/C, NUL state związany z fizyczną parą prefix/bin, pełna adopcja przed refresh, checkpointy per narzędzie, wspólna bramka poprzedniego journalu, świeży exec update, raporty read-only i prefix-only prune. Registered child/inflight chroni operację także po SIGKILL właściciela; pending/all-slot claims nie są odzyskiwane przez prune. Błędy A0-001/A0-002 są błędami implementacji kwalifikacji zakończonych receipts, a nie powodem osłabienia planu lub wymagań.

Niezależnie uruchomiono przez opublikowany `run_isolated_verification.py` 11 funkcji krytycznych testów, dających **66 passed**, bez skipów, w 84,53 s. Obejmują A/B/C, pair/newline state, crash-completed uninstall przed unrelated install, retired/missing deletion guards, child liveness, pending prune, read-only/environment side effects i generation fence, pierwsze update sześciu narzędzi oraz natywny lokalny Git maintenance/fsmonitor. Nie powtarzano pełnego smoke wyłącznie dla potwierdzenia.

## Pokrycie wszystkich REQ

`met` oznacza zgodność sprawdzoną przez inspekcję i wskazane dowody, w granicach opisanych niżej. Pełny smoke i mapowanie autora są dowodami pomocniczymi, nie zastępują niezależnego rozstrzygnięcia.

| REQ | Ocena | Dowód/ograniczenie |
| --- | --- | --- |
| REQ-001 | met | Dispatcher i pełne parsowanie fasad; brak starych namespaces/flag, bare nonmutation; świeży final smoke i mapped CLI cases. |
| REQ-002 | met | Addytywne member+completed, profile/dedup; `test_managed_lifecycle` i `test_managed_profiles`, source install/journal. |
| REQ-003 | met | Staging/reuse, alias health i B dla dokładnego własnego selektora; source oraz mapped repair cases. Nie znosi A0-001 dla późniejszej sekwencji. |
| REQ-004 | unmet | A0-001: poprawny zakończony uninstall może zostać zamieniony w nierozliczalny nowy journal, blokując zwykłe utrzymanie. |
| REQ-005 | met | Niezależne first-update/adoption checks, wszystkie layouty, stary rg i nu/nushell; dowody przed refresh zachowane. |
| REQ-006 | met | Buffered list/check, generation/inflight fence, brak source rc/payload execution; niezależne read-only/side-effect testy i source. |
| REQ-007 | met | Expected-tools tylko legacy hints; selection z argv lub member rows, bez pliku desired/profile subscription; source i final cases. |
| REQ-008 | unmet | A0-001: drugi poprawny uninstall nie jest no-op 0; po sukcesie tworzy uszkodzoną operację mimo braku członkostwa i payloadu. |
| REQ-009 | unmet | Zwykły update jest poprawnie pokryty; A0-001 pozostawia journal, którego wspólna bramka nie rozliczy, uniemożliwiając dalsze utrzymanie po legalnej sekwencji. |
| REQ-010 | met | Retired/unsupported zachowane; niezależne retired live C i first-update loss-of-definition; bez kasowania/zapominania członka. |
| REQ-011 | unmet | A0-002: katalog po udanym uninstall pokazuje historyczną instalację jako missing/broken. |
| REQ-012 | met | Merged environment/tool scope, syntax-only rc, bez index/fsmonitor writes; niezależne sentinele i mapped check tests. |
| REQ-013 | unmet | A0-002: brak członkostwa po ukończonym uninstall nie jest prawidłowo oddzielony od awarii aktywnej/zapisanej instalacji. |
| REQ-014 | met | Żywy C wymaga regularnego marker/member i bezpiecznych rodziców; B nie daje prawa rm-rf. Niezależne proof/missing/retired i child tests. |
| REQ-015 | met | Staging przed linkami, stare release zachowane, guarded rollback; pending claims/prune i checksum/library flow w final suite. |
| REQ-016 | unmet | A0-001: późniejszy no-op traci spójność z poprzednim ukończonym wynikiem i tworzy nierozliczalny running journal. Inne kontrolowane crash cases przeszły. |
| REQ-017 | met | Odczytowy preflight/preview, TTY/EOF/--yes i locked revalidation; fasady/source oraz final nonmutation tests. |
| REQ-018 | met | Management działa w Bash 3.2/5.3, zachowane assety/libc/checksum/layouty i granica probe. Natywnej ABI Flyline nie kwalifikowano — pozostaje unverifiable, nie jest dowodzona stubami. |
| REQ-019 | met | Canonical CLI publication i startup protection; source oraz 33 mapped CLI/runme cases w final JUnit. |
| REQ-020 | met | Konserwatywny prune, readonly bin/checkout i niezwiązane regresje; niezależne prune/native Git checks plus final suite; bez rzeczywistego hosta. |
| REQ-021 | met | Definicja fzf i oba prywatne adaptery zachowane; 28 niezależnych porównań preservation, mapped fzf/Navi offline cases. Native pickery bez kwalifikacji. |
| REQ-022 | met | Bieżący help/guide/docs używają nowego CLI; historyczne cytowania pozostają historyczne. Mapped guide/docs checks i inspekcja dispatcher/fasad. |

## Pokrycie wszystkich 24 AC

| AC | Ocena | Podstawa |
| --- | --- | --- |
| AC-001 | met | Removed inputs i snapshot nonmutation w final mapped cases; source routing. |
| AC-002 | met | Bare/help na nowej/starej lokalizacji; final mapped cases. |
| AC-003 | met | Całe argv/profil/TTY/EOF/odmowa; fasady i final cases. |
| AC-004 | met | Additive/profile/dedup; install engine i final lifecycle/profile cases. |
| AC-005 | met | Reuse i naprawa alias/payload/layout albo protected collision; proof/engine/reports. |
| AC-006 | met | External PATH i obcy local file/link chronione; source B/C oraz mapped cases. |
| AC-007 | unmet | A0-001, natychmiastowy drugi uninstall zwraca 1 i psuje journal. |
| AC-008 | met | Zmiana profilu nie przywraca uninstall ani nie dodaje pozycji; mapped update/profile cases. |
| AC-009 | met | Missing/broken members i empty update; mapped reports/update cases, source member list. |
| AC-010 | met | Retired/unsupported i bezpieczny uninstall z C; niezależne retired proof plus mapped cases. |
| AC-011 | met | Adopcja wszystkich aktywnych mimo niepełnego/brakującego expected-tools; source i niezależne AC-023. |
| AC-012 | met | Odczytowe raporty, no exec/load/cache, sentinel i generation fence; niezależne testy. |
| AC-013 | met | Expected-only/inactive/unproved remnants nie stają się member; source migration i mapped cases. |
| AC-014 | met | Strict state/complete inventory/marker/parent/.active fail closed; niezależne proof i mapped corruption cases. |
| AC-015 | unmet | A0-002, katalog ma fałszywe missing/broken po udanym uninstall. |
| AC-016 | met | Health/scope/PATH/alias/environment kody w final cases; niezależne side-effect check. |
| AC-017 | unmet | A0-001 narusza odzyskiwalny spójny wynik; 66 niezależnych istniejących cases przechodzi, ale nie obejmują drugiego uninstall po sukcesie. |
| AC-018 | met | Offline trzy layouty/Bash/libc/checksum/probe boundary. Realna ABI Flyline i realne asset installs nieprzetestowane. |
| AC-019 | met | Runme/REF/forward, CLI/footer/startup snapshots w final suite. |
| AC-020 | met | Niezwiązane regresje i informational checks w final suite; prune/native Git dodatkowo sprawdzone niezależnie. |
| AC-021 | met | Zachowane manifesty/adapter, informacyjny hint i jawna migracja; preservation i final fzf cases. |
| AC-022 | met | Pełny own uninstall i protected/foreign-active abort; mapped public cases i source C/preflight. |
| AC-023 | met | Dokładny first update sześciu narzędzi uruchomiony niezależnie na obu Bash. |
| AC-024 | met | Pair-only storage, fizyczne/newline paths, all-slot claims/XDG w source/final cases; niezależny roundtrip test. |

## Faktyczne sprawdzenia, źródła i ograniczenia

- Zweryfikowano 88/88 bieżących source hashes oraz oba zamrożone snapshoty. W `auditor-safe/audit-source-coverage-validation.json` zachowano własny receipt, nie polegano wyłącznie na receipt koordynatora.
- Bezpieczny final JUnit niezależnie potwierdza **1863 passed, 56 skipped, 0 failed**. Każdy mapped case z 22 REQ/24 AC istnieje w tym JUnit i ma zgodny wynik; nie oznacza to kompletności asercji, co wykazały nowe próby.
- Niezależne `audit-core`: 66 passed; `audit-sequences`: 4 failed; `audit-followup`: 2 failed. Wszystkie trzy result JSON mają `source_unchanged=true`, brak timeout. Dokładne komendy i argumenty znajdują się w tych result JSON; użyto wyłącznie opublikowanego fixed-allowlist runnera. Własne testy są w scratch, bez zmian projektu.
- Własny `audit-preservation.json` potwierdza 28 porównań z HEAD 9a: wszystkie pins/assety/checksumy, adaptery i wskazane produkcyjne pliki zachowane; dla nvim odjęto wyłącznie dozwoloną linię `BUNDLE_REQUIRED_PATHS`. Brak diff w `dots`, `shell/navi-bin` i tracked fixtures.
- 56 rzeczywistych skips: 4 przypadki PROMPT_COMMAND arrays wymagające Bash 5.1, 26 native-activation cases odrzucanych przez Bash 3.2 przed mutacją, 24 real Navi/skim wymagające jawnych binariów, 1 brak lokalnego pinned Atuin i 1 BASHOPTS niedostępny w Bash 3.2. Nie pobierano binariów i nie traktowano tych skips jako zaliczeń. Natywna ABI Flyline pozostaje osobno **unverifiable/unrun**, a nie rzekomo dowiedziona przez controlled probe.
- Przeczytano bieżące instrukcje/pełne assignment, publiczny runner i sanitized fixtures przed testami, source A/B/C, state/inventory/migration/journal/recovery/locks, install/uninstall/update, raporty i prune. Nie wykonano pełnego dowodu algorytmu bakery ani wyczerpującej analizy każdego możliwego sygnału; rzeczywiste targeted checks i ich granice są podane powyżej.
- Nie czytano ani nie hashowano restricted smoke01/02 log/XML/full-failure JSON, dawnych raw captures, prywatnego archiwum, oryginalnych dev/.env/user.local lub rzeczywistej konfiguracji użytkownika. Wcześniejsza niepewność odczytów prywatnych przez subprocessy pozostaje ujawniona w integration-result; ten audyt jej nie unieważnia ani nie bada ponownie. Brak sieci/live asset checks, real host install, startup/global config lub real checkout Git mutation.
- Sugestie opcjonalne: brak. Następny krok: planner przygotowuje naprawę obu usterek w istniejącym zakresie, następnie implementator i ponowny audyt. Runda naprawy zwiększa się dopiero przy rozpoczęciu jej wykonania. Audytor nie zmienił implementacji i nie autoryzuje sam napraw.
