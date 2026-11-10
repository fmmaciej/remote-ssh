# Niezależny przegląd planu 1

**Wynik: Pass.** P0-001, P0-002 i P0-003 są zamknięte. Brak wymaganych korekt i nowych sugestii. Ocena dotyczy pokrycia i wykonalności planu, nie działania implementacji.

- Plan: `PLAN-MANAGED-TOOL-LIFECYCLE` 0.2, `/private/tmp/remote-ssh-managed-lifecycle-planning-20261110/managed-tool-lifecycle-implementation-plan-0.2.md`.
- Zweryfikowany SHA-256: `e7d504fe7c5a69a400c9ccae549c4fcb0225dcb980c105ae5e45f4c89a5e7c23`.
- Podstawa: zaakceptowany manifest `dev/docs/history/managed-tool-lifecycle-20261110/baseline-1/baseline.json`, `SPEC-MANAGED-TOOL-LIFECYCLE@0.3`, snapshot SHA-256 `62a53a9ae528dba9ca1d0943c014c557490bec897d638b998902ca16fe56ffbb`.
- Kod nadal `15bcb79cee2d1959074d4c70e164d0cae75ee8e2`; brak zmian śledzonych plików. Audytor `/root/managed_lifecycle_auditor` pozostaje osobny od autora planu i przyszłego implementatora.

## Zamknięcie wymaganych uwag

| Uwaga | Ocena i dowód |
| --- | --- |
| P0-001 | **Zamknięta.** Plan rozdziela identyfikację A, naprawę dokładnego selektora B i rekursywne kasowanie wydania C. C zachowuje żywy regularny marker/member, bezpieczną nazwę i wersję, wszystkie rzeczywiste składowe rodzica oraz fizyczne zawarcie. Receipt nie zastępuje brakującej przesłanki C. B może naprawić tylko dokładny obecny własny symlink przy aktualnym markerze i bezpiecznym rodzicu; nie daje prawa usunięcia starego wydania. Brak dostatecznego C dla wymaganego zapisanego zakresu pozostawia członkostwo. V2/V3 dodają scenariusze recorded→missing/podmiana, także retired i trzy layouty. |
| P0-002 | **Zamknięta.** Zestawy blokad są rozpisane per komenda; prune apply używa tylko prefiksu i nie wymaga zapisu do bin/checkout. T7 jawnie przypisuje fasadę `commands/prune.sh` właścicielowi integracji. Prune kompletnie odczytuje claims oraz journal/receipts wszystkich slotów, chroni pending staging/final release po śmierci writera i claims innych par, nie wykonuje ich recovery i blokuje kasowanie przy niepełnym obrazie. V3/V6 obejmują readonly bin/checkout, concurrent publication, crash→pending release→prune→retry i drugi slot. |
| P0-003 | **Zamknięta.** Wspólna bramka pod locks obowiązuje każdy install/uninstall/update i wrapper przed nową paczką lub nadpisaniem journalu. Udowodnione ukończenie finalizuje członkostwo; znany częściowy wynik zachowuje wcześniejsze członkostwo i dowody bez automatycznej zgody na dalsze kasowanie. Nierozstrzygalny journal daje protected/1 bez zastąpienia dowodów. Po normalizacji następuje ponowny preflight. V3 zawiera oba łańcuchy crash→unrelated install: ukończony-na-dysku uninstall bez resurrection i wcześniejszy ukończony install bez utraty sukcesu. |

Diff 0.1→0.2 ogranicza się do wersji, trzech wymaganych korekt, odpowiadających im wpisów właściciela/testów oraz noty rewizji. Nie zmieniono zaakceptowanych potrzeb produktu ani zakresu. Konstrukcja locków/journalu nadal wymaga rzeczywistych testów w implementacji; Pass planu nie jest dowodem poprawności gotowego algorytmu.

## Pełne pokrycie

`met` oznacza pokrycie i wykonalność **w planie**. Wszystkie 22 REQ i 24 AC nadal mają unikalne mapowanie do T1–T7 oraz V1–V6. Niezmienione oceny dziedziczone są z raportu plan-review-0; wcześniejsze `unmet` oceniono ponownie po korektach.

| REQ | Ocena | Podstawa |
| --- | --- | --- |
| REQ-001 | met | Dziedziczone: T4/T6, V1; gramatyka i nonmutation. |
| REQ-002 | met | Dziedziczone: T3/T4, V1/V5; additive/profile/dedup. |
| REQ-003 | met | Dziedziczone: T1/T3, V2/V4; naprawa i external protection, uściślone B/C. |
| REQ-004 | met | Ponownie: wspólna bramka P0-003 zachowuje wcześniejsze wyniki i dowody. |
| REQ-005 | met | Dziedziczone: pełna adopcja przed refresh i wszystkie layouty/aliasy. |
| REQ-006 | met | Dziedziczone: raporty read-only, bez payload exec/library load/cache. |
| REQ-007 | met | Dziedziczone: legacy hints bez kontroli runtime lub edycji. |
| REQ-008 | met | Ponownie: C, retained state i bramka poprzedniego journalu; P0-001/P0-003. |
| REQ-009 | met | Ponownie: bramka usuwa drogę resurrection przez unrelated install; fresh-code engine bez zmiany. |
| REQ-010 | met | Dziedziczone i uściślone: retained metadata retired/unsupported, C nie słabnie. |
| REQ-011 | met | Dziedziczone: union/filter/sort i widoczność broken/retired. |
| REQ-012 | met | Dziedziczone: środowisko/zakres/PATH/library i rc bez hooków. |
| REQ-013 | met | Dziedziczone: statusy, kody i informacyjny fzf. |
| REQ-014 | met | Ponownie: jawny żywy C oraz ograniczony B; receipt nie autoryzuje rekursywnego kasowania. |
| REQ-015 | met | Ponownie: staging/immutability zachowane, poprawione prune locks i pending protection. |
| REQ-016 | met | Ponownie: wspólna normalizacja journalu i ochrona pending releases przed prune. |
| REQ-017 | met | Dziedziczone i uściślone: zgoda, locked revalidation i ponowny preflight po recovery. |
| REQ-018 | met | Dziedziczone: Bash 3.2, brak nowych deps, assety/layouty i jawna granica ABI. |
| REQ-019 | met | Dziedziczone: CLI-only publication, footer/startup i runme/REF. |
| REQ-020 | met | Ponownie: prune zachowuje readonly bin/checkout, inne regresje V6 bez zmiany. |
| REQ-021 | met | Dziedziczone: fzf definition/adapter i bramka fazy 2. |
| REQ-022 | met | Dziedziczone: bieżące instrukcje/teksty i nieprzepisywana historia. |

Korekty są zgodne z dotkniętym odbiorem AC-005/AC-006/AC-008/AC-010/AC-014/AC-017/AC-020/AC-022/AC-024; pozostałe mapowania i zakres V1–V6 pozostają bez zmian. Nie stwierdzono wymaganej luki w mapowaniu.

## Faktyczne sprawdzenia i ograniczenia

- Zweryfikowano dokładny hash, cały diff, przekazanie i check autora 0.2; 327 linii, 28 431 bajtów, 22/24 unikalne sekwencyjne wiersze i 18 poprawnych lokalnych linków względem docelowego źródła planu.
- Potwierdzono niezmienione bajty planu 0.1 i zaakceptowanego snapshotu specyfikacji. Wykorzystano poprzednie bounded source evidence; bez ponownego pełnego discovery.
- Przyszły plan projektowy i historia cyklu implementacji nadal nie istnieją. Własne zapisy ograniczono do tych dwóch autoryzowanych raportów scratch. Bez testów runtime, sieci, sekretów, danych hosta, konfiguracji lub mutacji Git.
- Brak wymaganych korekt, sugestii opcjonalnych, blokad i nowych decyzji produktu. Człowiek nadal musi zatwierdzić konkretny plan. Implementacja nie rozpoczęła się i pozostaje nieautoryzowana; licznik jej napraw nadal 0.
