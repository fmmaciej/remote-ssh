# Managed tool lifecycle — historia przygotowania specyfikacji

- Task ID: `managed-tool-lifecycle-20261110`.
- Projekt: `remote-ssh` (projekt zewnętrzny).
- Stan: `completed`.
- `specification_revision_round: 2`.
- Koordynator: `/root`.
- Autor specyfikacji: `/root/managed_lifecycle_analyst` — osobna instancja, rola analityka wymagań, jedyny autor szkicu.
- Audytor: `/root/managed_lifecycle_auditor` — osobna instancja, bez udziału w autorstwie; właściciel niezależnego przeglądu 0.
- Podstawa kodu: `15bcb79cee2d1959074d4c70e164d0cae75ee8e2`; początkowo czysty `main`, zgodny z `origin/main`.
- Dokument: `SPEC-MANAGED-TOOL-LIFECYCLE`, wersja `0.3`, zaakceptowana przez człowieka; źródło: `dev/docs/managed-tool-lifecycle-specification.md`.
- Manifest zaakceptowanej podstawy: `baseline-1/baseline.json` (specyfikacja 0.3, bez wymaganych zależności dokumentowych).
- Blokady: brak; wskazany zakres specyfikacji zaakceptowany.
- Następne działanie: przygotowanie planu w osobnej ścieżce po jego zleceniu; akceptacja specyfikacji nie autoryzuje automatycznie planu ani wykonania.

## Zdarzenia

### 1. 2026-11-10 — zakres i decyzje człowieka

Użytkownik zaakceptował kierunek czystego interfejsu i polecił kontynuować
przygotowanie zmiany. Decyzje wejściowe: instalacja z jawnymi nazwami lub
profilem, instalacja addytywna, profil jako skrót nazw, brak ukrytego trybu
`install` bez argumentów, powtórna instalacja narzędzia służy sprawdzeniu lub
naprawie, `update` utrzymuje faktycznie zarządzany zestaw, `uninstall <narzędzie>`
kończy utrzymywanie, `list` i `check` w głównym CLI. Usunąć przestrzeń `tool`
i komendę `doctor`; nie zachowywać aliasów dla zgodności wstecznej.
`expected-tools` przestaje sterować środowiskiem. Stan zarządzania zapisuje
instalator automatycznie; istniejące udowodnione instalacje wymagają
jednorazowej migracji danych.

Akceptacja kierunku nie jest akceptacją nieistniejącej jeszcze konkretnej
specyfikacji, planu ani implementacji. Zmiana cyklu życia nie usuwa definicji
fzf — jej dotychczasowa bramka migracji hostów pozostaje odrębna.

### 2. 2026-11-10 — przygotowanie kontekstu i przydział analityka

Koordynator zastosował workflow Kei `specification-prepare`, potwierdził
kontekst projektu zewnętrznego (`ready`) oraz stan repozytorium. Przydzielił
`/root/managed_lifecycle_analyst` rolę analityka i autorstwo wyłącznie nowej
specyfikacji. Analityk rozpoznaje kod, testy i dokumentację read-only.
Współdzielony workspace: zachować wcześniejsze i cudze zmiany; bez zmian
runtime, konfiguracji użytkownika, operacji Git i odczytu sekretów.

Analityk zapisuje autorski szkic w katalogu tymczasowym. Koordynator publikuje
identyczne bajty w repozytorium zewnętrznym z zachowaniem granic filesystemu.
Koordynator jest właścicielem historii i mechanicznej publikacji, nie autorem
specyfikacji ani jej niezależnym audytorem.

### 3. 2026-11-10 — zamknięcie decyzji interfejsu i napraw

Analityk wskazał nieustalone zachowania, koordynator przedstawił pytania.
Użytkownik jawnie wybrał wszystkie poniższe warianty w odpowiedzi na
`request_user_input_async` (`call_86da5ae1a9c9440ea5fff3fb3b6a6900`):

1. `uninstall` wymaga nazw; wywołanie bez nazw pokazuje pomoc i niczego nie usuwa.
2. `update` aktualizuje oraz naprawia brakujące lub uszkodzone instalacje
   zapisane jako zarządzane; narzędzia usunięte przez `uninstall` nie wracają.
3. Zachować `list --installed` / `--all` i `check [nazwy]`, a także `--yes`.
   Usunąć `--full`, `--skip-unsupported` i `--strict`; `check` domyślnie
   zwraca błąd przy wykrytej usterce.

Koordynator przekazał decyzje autorowi. Stan: `drafting`, rewizja nadal 0.
Jako konsekwencję wcześniejszej decyzji o utrzymywaniu rzeczywistych instalacji
ustalono w szkicu: wpis tylko w dawnym `expected-tools`, bez dowodu zarządzanej
instalacji, nie upoważnia do automatycznej instalacji lub przejęcia własności.
Nie jest to odrębna wypowiedź użytkownika; specyfikacja ma wyraźnie odróżnić
wniosek od jawnych decyzji i faktów ze źródeł.

### 4. 2026-11-10 — decyzja o błędzie odinstalowania

Analityk zgłosił niejednoznaczność stanu po odinstalowaniu przy niewystarczającym
dowodzie własności. Użytkownik jawnie zdecydował: „Przerwij i zachowaj stan
zarządzania do naprawy”, odpowiadając na `request_user_input_async`
(`call_7ae5cf62289e44779c571f502e5b64f0`). Koordynator przekazał decyzję autorowi.
Nie wolno domniemywać zakończenia zarządzania po niebezpiecznym lub
niekompletnym usunięciu. Stan: `drafting`; rewizja 0; brak otwartych decyzji
produktowych zgłoszonych przez autora.

### 5. 2026-11-10 — szkic 0.1 przekazany do przeglądu 0

Autor zakończył wersję `0.1` dokumentu `SPEC-MANAGED-TOOL-LIFECYCLE`.
SHA-256: `7bb447b30f57b8a2cf391262bf0996a80f0eec1df1d0e8caa43091c7abb7e958`.
Koordynator zachował dokładne bajty jako `draft-0.1.md` i publikuje je bez
zmian jako bieżącą specyfikację. Przekazanie autora: `analyst-handoff-0.1.toon`.
Autor zgłosił 22 wymagania, 21 AC, 9 UC i 48 poprawnych lokalnych linków.
Nie są to wyniki testów implementacji. Brak otwartych pytań autora.
Stan `reviewing`; `specification_revision_round: 0`; manifestu zatwierdzonej
podstawy nadal brak. Następny etap: osobny audytor, przegląd 0 bez edycji.

### 6. 2026-11-10 — przydział niezależnego audytora

Koordynator przydzielił `/root/managed_lifecycle_auditor` rolę audytora
specyfikacji. Instancja jest inna niż autor i koordynator, nie uczestniczyła
w autorstwie. Przedmiot: dokładna wersja 0.1 i hash ze zdarzenia 5, bez
wymaganych zależności dokumentowych. Raport: `review-0.md`, przekazanie:
`review-0.toon`. Audytor pracuje read-only wobec przedmiotu oceny;
sprawdza jakość specyfikacji, a nie spełnienie jej przez istniejący runtime.
Stan: `reviewing`; rewizja 0; następne działanie: wynik niezależnego przeglądu.

### 7. 2026-11-10 — wynik przeglądu 0 i rozpoczęcie rewizji 1

Niezależny audytor zwrócił `Findings` dla dokładnej wersji 0.1.
Raport: `review-0.md`; przekazanie: `review-0.toon`. Pokrycie: wszystkie
22 REQ, bez deklaracji spełnienia przez runtime. Wymagane korekty:
R0-001 — poprawić składnię `install --profile quick` w AC;
R0-002 — określić zakres usuwania starych własnych wydań i relację do prune.
Opcjonalne S0-001/S0-002 dotyczą mocniejszego odbioru już opisanej migracji
i izolacji lokalizacji. Brak blokad dostępu; runtime testów nie wykonywano.

Koordynator rozpoczyna rewizję 1 (`specification_revision_round: 1`)
i ponownie przydziela tego samego autora. Nowy szkic: 0.2; historia 0.1
i raport 0 pozostają zachowane. Pytanie o zakres kasowania R0-002 skierowano
do człowieka przez `request_user_input_async`; rekomendacja zachowuje
dotychczasowe usuwanie wszystkich potwierdzonych wydań wybranej nazwy.
Do odpowiedzi autor poprawia wyłącznie niezależne fragmenty.

### 8. 2026-11-10 — decyzja o starszych wydaniach przy uninstall

Użytkownik jawnie wybrał „Usuń wszystkie potwierdzone wydania” w odpowiedzi
na `request_user_input_async` (`call_4a49074a242147ae98afb352d8a4b8dc`).
Odinstalowanie wybranej nazwy obejmuje potwierdzone własne wydanie aktywne
oraz starsze nieaktywne wydania tej nazwy. Obce i nieudowodnione pozostałości
pozostają chronione. Wcześniejsza decyzja o przerwaniu i zachowaniu stanu
przy niebezpiecznym lub niekompletnym usunięciu nadal obowiązuje.
Koordynator przekazał wybór autorowi do jednoznacznego kontraktu i AC-022.
Stan `drafting`; rewizja 1; brak pozostałych pytań produktowych.

### 9. 2026-11-10 — szkic 0.2 i przydział przeglądu 1

Autor zakończył rewizję 1: `SPEC-MANAGED-TOOL-LIFECYCLE`, wersja `0.2`.
SHA-256: `6eb7ea485057b18b9e139fffa270ce2eacf2c00603c90cc771c347551a03cfd8`.
Dokładna kopia: `draft-0.2.md`; przekazanie: `analyst-handoff-0.2.toon`.
R0-001 poprawiono bez aliasu. R0-002 opisuje wszystkie potwierdzone aktywne
i nieaktywne wydania, chronione pozostałości poza zakresem oraz obowiązek
przerwania przy niepewnej własności ścieżek koniecznych do operacji.
AC-022 sprawdza granicę kompletności. Opcjonalne sugestie ujęto przez
AC-023/024 (pierwszy update/migracja, izolacja lokalizacji i XDG).
Autor zgłosił 22 REQ, 24 AC, 9 UC i 48 lokalnych linków; nie testował runtime.

Koordynator ponownie przydziela `/root/managed_lifecycle_auditor` niezależny
przegląd konkretnej wersji 0.2, z uwzględnieniem raportu 0 i powyższej
decyzji człowieka. Audytor pozostaje bez udziału w autorstwie i nie edytuje
przedmiotu. Rewizja nadal 1 (limit 2); stan `reviewing`. Raport przeglądu 1
ma nazwę `review-1.md`, przekazanie `review-1.toon`.

### 10. 2026-11-10 — wynik przeglądu 1 i rozpoczęcie rewizji 2

Audytor zwrócił `Findings` dla dokładnej wersji 0.2. Raport: `review-1.md`;
przekazanie: `review-1.toon`. R0-001 oraz R0-002 zamknięte. Jedyna wymagana
nowa korekta R1-001: AC-023 używa nieistniejącego własnego aliasu rg; należy
użyć rzeczywistej pary nu/nushell i dostosować zestaw/liczność scenariusza.
Nie potrzeba nowej decyzji produktu. Pokrycie specyfikacji: 21 REQ met,
REQ-005 unmet wyłącznie z powodu niejasnego fixture; bez oceny runtime.

Koordynator rozpoczyna rewizję 2 (`specification_revision_round: 2`, limit 2).
Ten sam autor otrzymał wyłącznie poprawkę przykładu oraz wersji/historii,
bez dalszych opcjonalnych rozszerzeń. Docelowy szkic: 0.3. Poprzednie bajty
i raporty zachowane. Stan `drafting`, brak pytań produktu i blokad dostępu.
Po poprawce nastąpi przegląd 2 przez tę samą niezależną instancję.

### 11. 2026-11-10 — szkic 0.3 i przydział przeglądu 2

Autor zakończył minimalną rewizję 2: `SPEC-MANAGED-TOOL-LIFECYCLE` 0.3.
SHA-256: `62a53a9ae528dba9ca1d0943c014c557490bec897d638b998902ca16fe56ffbb`.
Dokładna kopia: `draft-0.3.md`; przekazanie: `analyst-handoff-0.3.toon`.
Zmiana dotyczy AC-023: rzeczywisty alias nu/nushell, zgodny sześciopozycyjny
zestaw; stary rg, bundle, builtin i utrata definicji po refreshu zachowane.
Poza tym zmieniono wyłącznie wersję i historię. Autor nie zgłosił blokad.

Koordynator ponownie przydziela niezależnego `/root/managed_lifecycle_auditor`
do przeglądu 2 dokładnej wersji 0.3 i zamknięcia R1-001. Wcześniejsze
pokrycie i dowody zachowują ważność dla niezmienionej treści i kodu.
Raport docelowy `review-2.md`, przekazanie `review-2.toon`.
Stan `reviewing`; rewizja 2 (limit wyczerpany, brak automatycznej rundy 3).

### 12. 2026-11-10 — Pass przeglądu 2; oczekiwanie na akceptację 0.3

Niezależny `/root/managed_lifecycle_auditor` zwrócił `Pass` dla
`SPEC-MANAGED-TOOL-LIFECYCLE` 0.3 o SHA-256
`62a53a9ae528dba9ca1d0943c014c557490bec897d638b998902ca16fe56ffbb`.
Raport `review-2.md`, przekazanie `review-2.toon`. R1-001 zamknięte;
R0-001/R0-002 nadal zamknięte; brak wymaganych poprawek lub sugestii.
Wszystkie 22 REQ spełniają kontrakt jakości specyfikacji. To nie odbiór
implementacji i nie decyzja audytora o potrzebach człowieka.

Koordynator potwierdził identyczne bajty bieżącego dokumentu i zachowanej
kopii 0.3, zachowanie 0.1/0.2, dokładnie trzy obszary diff wobec 0.2,
22 REQ, 24 AC, 9 UC i 48 działających lokalnych linków. Dowód:
`document-validation-0.3.json`. Śledzone pliki projektu pozostały bez zmian.
Nie uruchamiano smoke/pytest/live assets, instalacji, migracji hosta, Git
mutacji ani zmian konfiguracji użytkownika. Powstały wyłącznie dokumenty
specyfikacji i jej historia.

Stan `awaiting_decision`; rewizja 2 z 2. Koordynator przedstawia człowiekowi
konkretną wersję 0.3, bez wymaganych zależności dokumentowych (`dependencies: []`).
A-001 zachowuje skład profili, A-002 opisuje proponowane szczegóły CLI/statusów
i kodów, A-003 pozostawia wewnętrzny podział instalatora późniejszemu planowi.
Są jawne w dokumencie i podlegają jego akceptacji. Q-001/Q-002 zamknięte
wcześniejszymi decyzjami człowieka. Manifestu zatwierdzonej podstawy brak,
ponieważ akceptacja dokładnej wersji nie została jeszcze udzielona.

Po zgodzie: zapisać decyzję oraz niezmienne dokładne bajty 0.3 i manifest
`baseline-1/baseline.json`, zgodnie z kontraktem. Nie nadpisywać zaakceptowanych
bajtów. Akceptacja specyfikacji nie autoryzuje automatycznie planu ani
implementacji; nie rozpoczynać ich w tej ścieżce. Jeśli odmowa lub potrzebna
zmiana po wyczerpaniu rund, wrócić do decyzji człowieka o dalszym przebiegu.

### 13. 2026-11-10 — akceptacja specyfikacji 0.3 i zamrożenie podstawy

Człowiek odpowiedział dokładnie „Zatwierdzam” na pytanie koordynatora
„Czy zatwierdzasz specyfikację v0.3?”, z odnośnikiem do konkretnego dokumentu
i raportu niezależnego przeglądu 2 (`Pass`). Jest to akceptacja
`SPEC-MANAGED-TOOL-LIFECYCLE` wersji 0.3, bez wymaganych zależności
dokumentowych (`dependencies: []`), wraz z jawnymi A-001–A-003.
Nie jest to akceptacja planu, implementacji, publikacji ani operacji Git.

Koordynator potwierdził zgodność zaakceptowanego dokumentu z zachowanym
przed akceptacją `draft-0.3.md` i SHA-256
`62a53a9ae528dba9ca1d0943c014c557490bec897d638b998902ca16fe56ffbb`.
Zachowano dokładne zaakceptowane bajty jako
`baseline-1/files/dev/docs/managed-tool-lifecycle-specification.md`
oraz manifest `baseline-1/baseline.json` (schema_version 1).
Treści i frontmatter dokumentu nie przepisano po akceptacji; zaakceptowany
stan i decyzję zapisano w tej historii. Poprzednie wersje i audyty zachowane.

Stan `completed` dotyczy wyłącznie przygotowania i akceptacji wskazanej
specyfikacji. `specification_revision_round: 2` pozostaje bez zmian.
Brak otwartych blokad. Plan i wykonanie pozostają osobnymi etapami.
