---
id: REPAIR-MANAGED-TOOL-LIFECYCLE-01
version: "0.1"
status: draft
created: 2026-11-10
cycle: managed-tool-lifecycle-implementation-20261110
current_repair_round: 0
proposed_repair_round: 1
author: /root/managed_lifecycle_planner
integration_owner: /root/managed_lifecycle_implementer
---

# Naprawa 1: dowody zakończonego uninstall

Podstawa pozostaje niezmienna: `dev/docs/history/managed-tool-lifecycle-implementation-20261110/baseline-1/baseline.json`,
SPEC-MANAGED-TOOL-LIFECYCLE 0.3 (`62a53a9ae528dba9ca1d0943c014c557490bec897d638b998902ca16fe56ffbb`)
i PLAN-MANAGED-TOOL-LIFECYCLE 0.2 (`e7d504fe7c5a69a400c9ccae549c4fcb0225dcb980c105ae5e45f4c89a5e7c23`).
Audit 0: `audit-0.md` / `audit-0.toon`, Findings A0-001 high i A0-002 medium. Przedmiot rundy 0:
88 ścieżek `increment-03/source-hashes.json`, source HEAD `9a223dcca76072eb9035316d25abf972902d3289`.
Planista zweryfikował oba snapshoty oraz 88/88 bieżących źródeł; nie wykonywał testów ani zmian projektu.

To zwykła korekta implementacji w ramach kroku 10 workflowu. Nie zmienia produktu, 22 REQ ani 24 AC.
Naprawia REQ-004/008/009/016 i AC-007/017 (A0-001) oraz REQ-011/013 i AC-015 (A0-002).
W szczególności nie zmienia udowodnionej granicy B/C, definicji własności ani semantyki częściowego usunięcia.
Koordynator zwiększy `repair_round` z 0 do 1 dopiero przy starcie wykonania; planista tego nie robi.

## Przyczyna i wymagany wynik

`managed/uninstall.sh:22–31` bierze wszystkie zapisane release receipts za wymagany zakres nowej operacji,
także nieistniejące roots zakończonego uninstall. `ms_journal_begin` dopiero po tym preflight wywołuje
`ms_journal_archive`, które usuwa te receipts (`managed/journal.sh:55–65`). Nowy running item pozostaje
bez referencji potrzebnych do poprawnego remove-intent; common gate słusznie odmawia jego nadpisania.
`commands/tool_status.sh:107–115` analogicznie wybiera historyczny selector root bez członkostwa,
a dalszy health check nadaje mu missing/broken. Oba błędy dotyczą czasu życia tych samych dowodów.

Zakończony uninstall atomowo zapisał member=false; jego receipts mogą pozostać historią, lecz nie są
aktualnym wymaganym zakresem ani dowodem zdrowia nieobecnej instalacji. Trzeba odróżnić je od dowodów
pending/failed/unresolved, które nadal chronią dane i pozwalają recovery. Nie naprawiać widoku zapisem.

## Kolejność i własność

Jedyny właściciel kodu, testów i integracji: `/root/managed_lifecycle_implementer`. Zachowuje zmiany człowieka,
w tym pins z HEAD 9a, oraz cudze artefakty. Nie pracuje sam w repozytorium. Koordynator posiada historię
i decyzję o starcie rundy; niezależny `/root/managed_lifecycle_auditor` ponownie oceni zintegrowany wynik.

1. **R1 — odtwarzalny punkt przed naprawą.** Przed pierwszą edycją każdego istniejącego publicznego pliku
   przeznaczonego do zmiany zapisać jego dokładne bajty w historii naprawy, sprawdzić SHA-256 względem
   immutable `increment-03/source-hashes.json` i zachować mapę source→snapshot/hash. Dla ewentualnego nowego
   pliku zapisać jawny znacznik wcześniejszej nieobecności; nie tworzyć go przed tą kontrolą. Dotyczy również
   zmienianych testów. Bez zgodności zatrzymać wykonanie i zgłosić kolizję koordynatorowi.
   Nie kopiować całego checkoutu, konfiguracji prywatnej lub raw scratch. Zachować audit 0, manifest 88 plików,
   wyniki i zatwierdzone bajty bez nadpisania. Runda 1 ma własne result/audit/evidence.
2. **R2 — regresje publiczne przed poprawką.** W istniejących `dev/tests/test_managed_uninstall.py`,
   `test_managed_reports.py` i, dla sekwencji recovery, `test_managed_public_faults.py` lub
   `test_managed_recovery.py` dodać przypadki odbioru poniżej. Wykorzystywać `EngineEnv`, realny lifecycle,
   lokalne assety/upstream i oba runtime Bash; nie mockować journalu, stanu, preflight lub klasyfikatora.
   Zachowane `auditor-safe/test_audit_sequences.py` i `test_audit_followup.py` są wzorem reprodukcji,
   pozostają niezmienione. Red run tylko właściwych nowych przypadków przez opublikowany runner.
3. **R3 — zakres i kolejność nowej operacji (A0-001).** W `tools/lib/managed/journal.sh` wydzielić mały
   wspólny odczytowy predykat kwalifikacji historycznych receipts: brak członkostwa oraz faktycznie ukończony
   uninstall danej nazwy, z pierwszeństwem bieżącego item nad archived result. Pending/running/queued,
   failed/not-run lub nierozstrzygnięta operacja nie spełniają predykatu. Nie rozstrzygać go samym brakiem root.
   W `managed/uninstall.sh` wykluczyć takie historyczne release receipts z nowego required scope oraz
   historyczny selector-root fallback dla nieistniejącej ścieżki. W `managed/install.sh::ms_tool_selectors`
   tą samą regułą wyłączyć historyczne custom selector rows; zachować rozpoznanie nazw/metadanych i aktualnych
   deklarowanych aliasów. Nadal wykonywać pełny live inventory, claims i guards: rzeczywiście obecne własne
   wydanie/link mogą dać aktualny zakres, a obca wymagana ścieżka nadal przerywa przed kasowaniem.
   Samo historyczne `last=uninstall:completed` nie może uruchomić journalu dla nieobecnego narzędzia.
4. **R4 — archiwizacja bez unieważniania preflight.** W `journal.sh` oraz jego wywołaniach w
   `tools/lib/commands/{install,uninstall}.sh` i `managed/update.sh` zapewnić kolejność pod właściwymi locks:
   state load → dotychczasowy recovery gate → rozliczenie/archiwizacja settled journalu w pamięci → ostateczny
   preflight z aktualnych dowodów → snapshot/lock-set checks → utworzenie nowego journalu i wspólny commit.
   Nie odkładać usuwania starych receipts do miejsca, które może usunąć dowód zebrany już przez nowy preflight.
   `ms_journal_begin` ma odrzucić nieprzygotowany/nierozliczony poprzedni journal zamiast cicho go zastępować.
   Normalizacja in-memory jest zapisywana dopiero wraz z rzeczywistą nową operacją; poprawny pusty wybór
   powtórnego uninstall wraca 0 przed tworzeniem locks/katalogów, archiwizacją na dysku i nowym itemem.
   Wrapper korzysta z tego samego wejścia; continuation bieżącego update nie jest nową paczką do archiwizacji.
   Genuinely unresolved journal pozostaje chroniony i niezmieniony. Bez automatycznej zgody na dalsze kasowanie.
5. **R5 — raport bez wskrzeszania historycznego root (A0-002).** W `commands/tool_status.sh` użyć tej samej
   kwalifikacji przy zapisanym root/B fallback: terminal uninstall bez członkostwa nie nadaje historycznym
   receipts roli bieżącego health root. Najpierw nadal badać rzeczywiste selektory/kolizje. W katalogu wspierana
   nieobecna pozycja ma unmanaged+available, opcjonalnie `last=uninstall:completed`; bez sztucznego missing/broken.
   `list --installed` ją pomija. Jawny `check TOOL` nadal daje 1 i missing/external-only. Zachować faktyczne
   managed missing/broken, retired/unsupported, failed/not-run i pending oraz generation/child fence.
   Nie uruchamiać archive/recovery ani state commit z list/check. Nie rozszerzać tej korekty na claims/prune
   lub żywe guards; ich dowody i dotychczasowe odmowy pozostają obowiązujące.
6. **R6 — integracja i dowód końcowy.** Po targeted green wykonać wymagany pełny `just smoke` wyłącznie przez
   `increment-03/run_isolated_verification.py` w trybie `smoke`, ze świeżym label/output/synthetic HOME.
   Przed przekazaniem zamrozić dokładny zestaw poprawionych publicznych źródeł/testów: union 88 ścieżek
   audit 0 i nowych własnych plików, z hashami/nieobecnościami, rzeczywistym HEAD i mapą delta do before bytes.
   Source fence każdego runu ma `source_unchanged=true`; po finalnym teście i przed audytem ponownie porównać
   subject z rzeczywistymi plikami. Oddać audytorowi niezmienny plan, snapshoty przed naprawą, result, final
   subject i safe log/JUnit/skips. Wstrzymać dalsze edycje ocenianego subject do wyniku audytu.

## Odbiór naprawy

Wszystkie przypadki na Bash 3.2.57 i dostępnej Bash 5.3.20, publicznym subprocess CLI, bez sieci:

| Przypadek | Wymagany wynik |
| --- | --- |
| Install rg → uninstall rg → natychmiast uninstall rg ponownie | 0/0/0; ostatnia operacja jest no-op. Pełny snapshot przed/po ostatnim wywołaniu: state bytes/generation/journal, inventory i modes/mtime ścieżek prefix/bin, targety linków, payloady oraz syntetyczne config/startup nie zmieniają się; bez nowego running item, ticket lub download. |
| Raport natychmiast po pierwszym sukcesie, przed kolejną mutacją | Default list i --all: rg unmanaged+available, bez missing/broken; --installed nie zawiera rg. Każdy raport 0 i identyczny snapshot. Opcjonalna historia ostatniej operacji dozwolona. |
| Jawny check rg po uninstall | Przy poprawnym syntetycznym środowisku daje 1 z missing; wariant external-only także 1, zewnętrzny plik nietknięty. Nie tworzy członkostwa i nie zapisuje historii. |
| Repeat no-op → unrelated install fd → update | fd zarządzane/zdrowe, update 0 w lokalnym upstream; rg nie wraca, journal nie jest osierocony. Sprawdzić faktyczne członkostwo i aktywne ścieżki, nie tylko kod. |
| Mixed: usunięte nu + nadal zarządzane rg → uninstall nu rg | nu no-op, rg poprawnie usunięte; bez fałszywych scope/intents nu. Wariant podmienionej wymaganej ścieżki rg daje 1 przed kasowaniem i zachowuje pełny snapshot. |
| Nowy żywy dowód po historycznym sukcesie | Syntetyczne poprawne własne inactive wydanie w prefiksie znanej nazwy po uninstall jest wybrane jawnie i usunięte z żywym C; wcześniejsza archiwizacja nie kasuje dopiero zebranego receipt. Obca pozostałość pozostaje protected. |
| Pending/failed/unresolved wobec historycznej nazwy | SIGKILL po usunięciu na dysku przed member=false nadal kończy recovery przed unrelated install/update; częściowy unlink/rm zachowuje członka i dowody. Podmiana member/parent/marker/selector blokuje nowe batch bez nadpisania; nie traktować tego jak terminalnego no-op. |
| Widoczność innego wyniku | Wspólny stan z terminal uninstall jednego narzędzia i rzeczywistym managed missing/broken albo failed/not-run drugiego zachowuje wszystkie właściwe statusy i filtry. Klasyfikacja musi być per-tool. |

Targeted run obejmuje nowe przypadki oraz istniejące `test_managed_{uninstall,reports,recovery,public_faults,update,prune}.py`
i odpowiednie lifecycle/install-engine guards. Zachować szczególnie crash-completed uninstall przed unrelated install,
live B/C dla missing/retired, all-slot/pending claims, readonly bin/checkout prune oraz report generation/child fence.
Następnie jeden pełny smoke; powtórzyć tylko po zmianie lub nowym niezamkniętym błędzie. Raportować rzeczywiste
liczby i skips z obu runów, bez przenoszenia dawnych 1863 passed na nowy subject. Audytor niezależnie powtórzy
sześć uprzednio nieudanych prób i oceni pełne 22 REQ/24 AC z uwzględnieniem niezmienionych dowodów.

## Granice i następne działanie

Tylko publiczne własne pliki naprawy; bez edycji assetów/pins, fzf definicji/gate/private Navi adaptera,
zmian Bash/runtime dependencies, native ABI twierdzeń, host install, startup/Git config ani operacji Git.
Restricted smoke01/02, stare raw scratch/private archive i oryginalne `dev/.env`/user.local pozostają poza
odczytem/hashowaniem/promocją. Każdy subprocess testowy idzie przez opublikowany runner; nie uruchamiać
pytest/smoke bez niego, nie pobierać bibliotek/assetów i nie używać live checks.
Nie wykryto luki wymagań. Koordynator zachowuje ten plan i przydziela wykonanie oryginalnemu implementatorowi;
po rzeczywistym starcie runda 1, po integracji niezależny re-audyt. Do tego czasu stan pozostaje repair_planning/0.
