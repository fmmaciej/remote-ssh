# Przegląd specyfikacji 1 — managed tool lifecycle

**Wynik: Findings.** Obie wymagane uwagi z przeglądu 0 są zamknięte. Nowe AC-023 wymaga jednej wąskiej korekty danych scenariusza; nie wymaga nowej decyzji produktu.

- Przedmiot: `dev/docs/managed-tool-lifecycle-specification.md`, `SPEC-MANAGED-TOOL-LIFECYCLE` `0.2`, `draft`.
- SHA-256: `6eb7ea485057b18b9e139fffa270ce2eacf2c00603c90cc771c347551a03cfd8` — potwierdzony.
- Przegląd 1; `specification_revision_round: 1`; manifest: brak. Podstawa źródeł nadal `15bcb79cee2d1959074d4c70e164d0cae75ee8e2`.
- Audytor: `/root/managed_lifecycle_auditor`, bez udziału w autorstwie. Dokument, runtime, konfiguracja i Git pozostały bez zmian.
- Zakres: różnica względem zachowanego 0.1, zamknięcie R0-001/R0-002 oraz spójność dotkniętych REQ/CLI/UC/AC, w tym AC-022–024. Dowody źródłowe przeglądu 0 zachowują ważność przy niezmienionym HEAD; nie powtarzano szerokiego rozpoznania.

## Zamknięcie poprzednich uwag

| Uwaga | Ocena | Dowód |
| --- | --- | --- |
| R0-001 | zamknięta | AC-004 i AC-008 używają `install --profile quick --yes`, zgodnie z gramatyką. Nie dodano aliasu pozycyjnego profilu. |
| R0-002 | zamknięta | D-012 odzwierciedla jawny wybór człowieka ze zdarzenia 8 historii. REQ-008 i REQ-015 określają usunięcie wszystkich potwierdzonych własnych aktywnych i nieaktywnych wydań wybranej nazwy. Tabela uninstall, opis niepełnych operacji, UC-003 oraz AC-007/AC-010/AC-022 są zgodne. |
| S0-001 | uwzględniona częściowo poprawnie | REQ-005 i opis migracji precyzują zachowanie zestawu sprzed pierwszego refreshu. AC-023 dodaje przekrój layoutów i utratę definicji, lecz jego dane aliasu wymagają R1-001 poniżej. |
| S0-002 | uwzględniona | AC-024 sprawdza różne pary prefix/bin, podmieniony przez XDG obcy rekord oraz brak resurrection po powrocie do właściwej lokalizacji. |

AC-022 poprawnie odróżnia nieudowodniony katalog poza własnym zakresem kasowania od podmienionego wymaganego aktywnego linku. Pierwszy pozostaje chroniony i nie blokuje kompletnego własnego uninstall; drugi wymaga błędu przed kasowaniem i zachowania członkostwa. D-011 nie zostało osłabione. Niepełne usunięcie potwierdzonego własnego zakresu nadal zachowuje zarządzanie.

## Wymagana korekta

| ID | Waga | Miejsce | Problem i wymagany wynik |
| --- | --- | --- | --- |
| R1-001 | średnia | `dev/docs/managed-tool-lifecycle-specification.md`, AC-023 | Scenariusz wymaga starszego rg aktywnego wyłącznie przez „własny alias”, ale w przypiętej podstawie `tools/defs/rg.sh` nie deklaruje żadnego `BINARY_ALIASES`. Żaden z pięciu wybranych w AC narzędzi nie daje tu nazwanego aliasu, który scenariusz mógłby uznać za własny zgodnie z zachowywanymi definicjami. Kryterium nie wskazuje też jawnie syntetycznego wcześniejszego katalogu z takim aliasem. Odbiór nie powinien wymagać dodania aliasu do rzeczywistych definicji ani uznania dowolnego symlinku za własny. Użyć rzeczywistego deklarowanego aliasu, np. `nu`/`nushell`, aktualizując skład i liczbę członków scenariusza, albo jawnie zdefiniować bezpieczny syntetyczny katalog testowy z deklarowanym aliasem. Zachować osobne pokrycie starszego rg, bundle, bash-builtin i utraty definicji po pierwszym refreshu. |

Dowód: `tools/defs/rg.sh` deklaruje `BINARY_NAME="rg"` i nie zawiera `BINARY_ALIASES`; `tools/defs/nu.sh` deklaruje `BINARY_ALIASES=("nushell")`. `nvim` ma `INSTALL_LAYOUT="bundle"`, a `flyline` — `bash-builtin`, więc pozostały przekrój AC-023 odpowiada źródłom. Problem dotyczy sprawdzalności nowego konkretnego AC, a nie wyboru architektury implementacji.

Sugestie opcjonalne: brak nowych. Po R1-001 nie pozostaje zgłoszona otwarta decyzja produktu; nadal potrzebna jest akceptacja konkretnego szkicu przez człowieka po Pass.

## Pokrycie wszystkich REQ

Ocena dotyczy **kontraktu specyfikacji**, nie implementacji. `met` nie oznacza zaliczenia AC przez runtime. Niezmienione obszary zachowują uzasadnienia z raportu 0.

| REQ | Ocena | Dowód lub uzasadnienie |
| --- | --- | --- |
| REQ-001 | met | R0-001 zamknięta; gramatyka i AC-001–004/AC-008 zgodne. |
| REQ-002 | met | Poprawione AC-004/AC-008 zachowują addytywność i profil bez subskrypcji. |
| REQ-003 | met | Bez zmiany; UC-002, AC-005–006/AC-018 określają naprawę i ochronę external PATH. |
| REQ-004 | met | AC-009/AC-014/AC-017 oraz nowe AC-022/AC-024 zachowują wyniki i izolują stan. |
| REQ-005 | unmet | Obowiązek adopcji i ochrony dowodów jest jasny, ale nowy konkretny odbiór alias-only w AC-023 wymaga poprawienia danych zgodnie z R1-001. |
| REQ-006 | met | Read-only bez payload execution i library load pozostaje jednoznaczne; AC-012/AC-014. |
| REQ-007 | met | AC-011/AC-013/AC-021 oraz nowe scenariusze nie przywracają runtime kontroli expected-tools. |
| REQ-008 | met | D-012, precyzyjny własny zakres, niezależna ochrona wymaganej aktywnej ścieżki; AC-007/AC-010/AC-022. |
| REQ-009 | met | AC-008–009/AC-017/AC-022/AC-024 zachowują naprawę i brak resurrection. |
| REQ-010 | met | Zachowanie dowodów, retired/unsupported i brak cichej utraty wpisu; AC-010 i doprecyzowane pierwsze update. R1-001 nie podważa tego wyniku dla pozostałych danych. |
| REQ-011 | met | List zachowuje missing/broken/retired; alias nie daje drugiego członka; AC-015. |
| REQ-012 | met | Bez zmiany; UC-007, AC-016/AC-018 obejmują diagnostykę środowiska, wyboru i bibliotek. |
| REQ-013 | met | Bez zmiany; tabela statusów i AC-009–010/AC-015–016/AC-021. |
| REQ-014 | met | Dowód kasowania niezależny od członkostwa; AC-022/AC-024 wzmacniają wymagania ochrony. |
| REQ-015 | met | R0-002 zamknięta: brak automatycznego prune w install/update, odrębny jawny prune, pełny własny zakres uninstall. Staging/immutability bez zmiany. |
| REQ-016 | met | Per-tool completion i odzyskiwalność pozostają zgodne z pełnym zakresem kasowania; AC-017/AC-022. |
| REQ-017 | met | Walidacja/podgląd/potwierdzenie przed kasowaniem i zapisem; AC-003/AC-019/AC-022. |
| REQ-018 | met | Zachowane layouty, przypięte assety, Bash 3.2, kwalifikacja bibliotek i brak zależności; AC-018/AC-020. |
| REQ-019 | met | Bez zmiany; AC-019 zachowuje wyłączną publikację CLI, bootstrap, REF i startup files. |
| REQ-020 | met | Bez zmiany; AC-020 i odróżnienie informacyjnego update-check. |
| REQ-021 | met | Bez zmiany; UC-009/AC-021 zachowują fazę 1 fzf, adapter i bramkę fazy 2. |
| REQ-022 | met | Bez zmiany; zakres bieżącej dokumentacji i historycznych dowodów jednoznaczny. |

## Faktycznie wykonane sprawdzenia i granice

- Zweryfikowano hash 0.2, zachowany hash 0.1, różnicę wersji oraz historię i przekazanie autora 0.2.
- Niezależnie potwierdzono 22 unikalne sekwencyjne REQ, 24 AC, 9 UC, 48 istniejących linków wewnątrz projektu i brak przykładów `install quick`.
- HEAD nadal odpowiada podstawie; brak modyfikacji śledzonych plików. Uzupełniający odczyt ograniczono do deklaracji layoutów i aliasów w sześciu wskazanych definicjach.
- Nie wykonano runtime testów, sieci, host migration ani instalacji/usuwania; nie odczytano sekretów, `dev/.env` ani rzeczywistego expected-tools. Nie weryfikowano implementacji nowego kontraktu.
- Nie ma blokady dostępu ani problemu niezależności. Następne działanie: jedna wąska korekta R1-001 przez autora w pozostałym limicie rewizji, a potem niezależny przegląd konkretnej nowej wersji. Akceptacja dokumentu i rozpoczęcie implementacji nadal są osobnymi decyzjami.
