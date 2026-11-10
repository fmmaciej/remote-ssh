---
id: SPEC-MANAGED-TOOL-LIFECYCLE
version: "0.1"
status: draft
created: 2026-11-10
updated: 2026-11-10
dependencies: []
---

# Uproszczony cykl życia narzędzi remote-ssh

Dokument ustala rezultat zmiany istniejącego projektu, bez planu implementacji.
Jest samodzielnym szkicem do niezależnego przeglądu i akceptacji człowieka;
zaakceptowanie kierunku rozmowy nie oznacza akceptacji tej wersji dokumentu.
Wymagania opisują docelowy kontrakt. Format stanu, schemat danych, podział
modułów i kolejność prac pozostają przedmiotem późniejszego planowania.

## Problem, odbiorca i efekt

Odbiorcą jest użytkownik utrzymujący własne środowisko remote-ssh na lokalnym
lub zdalnym hoście. Chce wybrać profil albo pojedyncze narzędzia, później
je dodawać i usuwać, a następnie jednym `update` aktualizować projekt oraz
swój faktycznie zarządzany zestaw.

Dziś te potrzeby dzielą się między `install`, `tool install`, `tool list`,
`check` i `doctor`. Ręczny `expected-tools` dubluje informację o instalacjach,
a zwykły `install rg` zastępuje w nim wcześniejszy zestaw. Następny `update`
może więc utrzymywać tylko ostatnio wskazane narzędzie. Człowiek poinformował
o wykonaniu `remote-ssh install flyline`; ryzyko nadpisania listy do samego
`flyline` wynika z kodu (F-002), a nie z odczytu zawartości jego pliku.
Nie wykonywano inspekcji rzeczywistego hosta w ramach tej specyfikacji.

Efektem ma być jeden prosty interfejs: `install`, `uninstall`, `update`,
`list`, `check`. Instalator sam pamięta skutecznie objęte zarządzaniem
instalacje. Profil jest jednorazowym skrótem wyboru, a nie deklaracją stanu
pożądanego. Użytkownik nie synchronizuje ręcznie drugiej listy narzędzi.

## Podstawa i rodzaje ustaleń

Rozpoznanie dotyczy commita
`15bcb79cee2d1959074d4c70e164d0cae75ee8e2`. Odnośniki poniżej wskazują źródła
w repozytorium; przy ocenie faktów F-* właściwa jest ich treść z tego commita.
Nie uruchamiano instalacji, sieci, migracji hosta ani testów runtime.

### Fakty ze źródeł

| ID | Obserwacja i dowód |
| --- | --- |
| F-001 | [Dispatcher CLI](../../bin/remote-ssh), `remote_ssh_usage` i `main`, publikuje osobne `tool` i `doctor`. [install.sh](../../tools/lib/commands/install.sh), `remote_ssh_cmd_install_main`, obsługuje nazwy, profile, `--full`, `--yes`, `--skip-unsupported` i reinstalację zapisanej listy bez argumentów. |
| F-002 | [expected_tools.sh](../../tools/lib/install/expected_tools.sh), `write_expected_tools`, zapisuje cały przekazany zestaw od nowa. [install.sh](../../tools/lib/commands/install.sh) robi to po instalacji wybranych narzędzi. [Testy](../tests/test_install_expected_tools.py), `test_install_command_saves_selected_expected_tools` i `test_tool_install_does_not_change_expected_tools`, potwierdzają różne skutki obu ścieżek instalacji. |
| F-003 | [tool_inventory.sh](../../tools/lib/install/tool_inventory.sh), `managed_tool_installed`, wymaga działającego payloadu i dowodu wydania. [tool.sh](../../tools/lib/commands/tool.sh) buduje listę z bieżących definicji. [test_tool_list.py](../tests/test_tool_list.py), `test_invalid_or_unmanaged_installation_is_not_installed`, traktuje m.in. usunięty payload jako `available`, bez wiersza `--installed`. To nie jest pełna ewidencja uszkodzonych instalacji. |
| F-004 | [release.sh](../../tools/lib/common/release.sh), `remote_ssh_release_validate` i `remote_ssh_release_for_link`, waliduje znacznik jako dane, fizyczne granice prefiksu, nazwę wydania, definicję i istniejący payload. Sam katalog nazwany jak narzędzie nie dowodzi własności. [test_release_ownership.py](../tests/test_release_ownership.py) obejmuje obce katalogi, fałszywe znaczniki, ścieżki wychodzące poza wydanie i kod w polach danych. |
| F-005 | [install/install.sh](../../tools/lib/install/install.sh) sprawdza przypiętą wersję lokalną, a [install-tool/install.sh](../../tools/lib/install-tool/install.sh) przygotowuje nowe wydanie przed przełączeniem linków. Częściowo wykonana paczka może zostawić pierwsze narzędzie zainstalowane; [test_install_cli.py](../tests/test_install_cli.py), `test_tool_batch_failure_stops_without_completion`, sprawdza zatrzymanie i brak fałszywego komunikatu końcowego. |
| F-006 | [update.sh](../../tools/lib/commands/update.sh) pobiera upstream, resetuje śledzone pliki, zachowuje nieśledzone i uruchamia `install` bez nazw w nowym procesie ze świeżego checkoutu. [test_update.py](../tests/test_update.py) pokrywa błędy fetch/reset, nieśledzone pliki i przekazanie błędu odświeżonego instalatora. |
| F-007 | [check.sh](../../tools/lib/commands/check.sh) opiera domyślny zestaw na `expected-tools`; `--strict` zmienia kod wyniku przy problemach. [doctor.sh](../../tools/lib/commands/doctor.sh) dodaje wymagania środowiska, repozytorium, PATH, ładowanie rc i opcjonalne helpery oraz wskazówki fzf. |
| F-008 | [tool_sets.sh](../../tools/lib/install/tool_sets.sh) jest źródłem aktualnych profili; [runme.sh](../../runme.sh) ma edytowalny pierwszy wybór `RUNME_TOOLS`, przekazuje jawne argumenty do `install` i obsługuje `REMOTE_SSH_REF`. |
| F-009 | [uninstall.sh](../../tools/lib/commands/uninstall.sh) bez nazw wybiera wykryte zarządzane narzędzia; z nazwami usuwa potwierdzone linki/wydania, chroni obce ścieżki i przepisuje `expected-tools`. [prune.sh](../../tools/lib/commands/prune.sh) zachowuje konserwatywny, domyślnie informacyjny cleanup nieaktywnych wydań. |
| F-010 | [AGENTS.md](../../AGENTS.md), [docs/tools.md](../../docs/tools.md) i [docs/install.md](../../docs/install.md) opisują przypięte assety, układy `binary`, `bundle`, `bash-builtin`, Bash 3.2 dla zarządzania, publikację CLI bez edycji startup files i granice własności. [Testy bibliotek](../tests/test_install_library.py) rozdzielają instalację biblioteki od aktywacji w nowej powłoce. |
| F-011 | [Plan wycofania fzf](fzf-retirement-plan.md) ma zakończoną fazę 1 i niezrealizowaną bramkę migracji hostów przed fazą 2. `tools/defs/fzf.sh` pozostaje; prywatny `shell/navi-bin/fzf` jest adapterem skim, a nie wycofywanym pakietem. |

### Decyzje człowieka

Poniższe decyzje przekazał koordynator z rozmowy; nie są wnioskami
wyprowadzonymi z bieżącego kodu.

| ID | Decyzja |
| --- | --- |
| D-001 | Publiczny cykl życia to `install --profile quick` (profile `mini`, `quick`, `full`), `install rg fd sk`, `uninstall navi`, `update`, `list`, `check`. |
| D-002 | Instalacja jest addytywna. Profil jest wyłącznie skrótem jawnego wyboru. Późniejsza zmiana profilu nie dodaje narzędzi i nie przywraca odinstalowanych. Ponowne `install <nazwa>` sprawdza i w razie potrzeby naprawia instalację. |
| D-003 | `install` bez wyboru pokazuje użycie; nie reinstaluje zapisanego zestawu i nie ma ukrytej naprawy wszystkich narzędzi. |
| D-004 | Usuwamy namespace `tool`, `doctor`, flagi `--full`, `--skip-unsupported` i `--strict` bez aliasów zgodności. `check` sam zwraca niepowodzenie przy niezdrowym stanie. |
| D-005 | Automatyczny stan instalatora zastępuje ręczny `expected-tools`; plik nie steruje runtime. Jednorazowe przejęcie udowodnionych istniejących instalacji jest migracją danych. |
| D-006 | `uninstall` wymaga nazw. Bez nich pokazuje użycie i niczego nie usuwa. Zachowujemy `--yes` dla instalacji i odinstalowania. |
| D-007 | `update` aktualizuje projekt i naprawia brakujące lub uszkodzone zapisane instalacje. Odinstalowanie usuwa obowiązek utrzymywania narzędzia; `update` nie może go przywrócić. |
| D-008 | Zachowujemy filtry `list --installed` i `list --all` oraz opcjonalne nazwy w `check`. |
| D-011 | Gdy uninstall nie może bezpiecznie ustalić własnych ścieżek do usunięcia, przerywa i zachowuje stan zarządzania do czasu naprawy. Nie kończy zarządzania po cichu przy niebezpiecznym lub niepełnym usunięciu. |

### Wiążące odziedziczone ograniczenia projektu i zakresu

Poniższe ograniczenia wynikają z instrukcji projektu i granic zlecenia
koordynatora, a nie z osobnych deklaracji człowieka o każdym szczególe.

| ID | Ograniczenie i źródło |
| --- | --- |
| C-001 | Zachowujemy pozostałe zachowania shell/setup/ssh/git/prune/scripts/guide/update-check, ochronę własności, niezmienne wydania, istniejące układy, Bash 3.2, przypięte assety i brak nowych zależności runtime. Instalator nie edytuje startup files, a narzędzia zewnętrzne w PATH pozostają poza zarządzaniem. Źródło: AGENTS.md (F-010) i przydzielony zakres zmiany. |
| C-002 | Ta zmiana nie realizuje fazy 2 wycofania fzf, nie usuwa definicji fzf ani prywatnego adaptera Navi. Późniejsza implementacja ma poprawić zależne instrukcje starego CLI i ręcznego utrzymywania expected-tools. Źródło: F-011 i przydzielony zakres zmiany. |

Konsekwencja D-005 i granicy własności: nazwa obecna wyłącznie w starym
`expected-tools` nie uprawnia do instalacji ani przejęcia czegokolwiek.
Migracja musi odnaleźć wszystkie udowodnione aktywne instalacje, również
nieobecne w tym pliku; nie może zakładać, że jego ostatnia treść jest kompletna.

Pozostałe szczegóły interfejsu i wymagania graniczne w tym szkicu są jawną
propozycją kontraktu do akceptacji wraz z dokumentem, a nie dodatkowymi
cytatami decyzji człowieka. Założenia i stan pytań są na końcu.

## Zakres i wyłączenia

Zakres obejmuje wybór narzędzi, trwałą informację o objęciu zarządzaniem,
jednorazową migrację istniejących instalacji, instalację/naprawę, odinstalowanie,
aktualizację zestawu oraz dwa raporty. Obejmuje kontrakt bootstrapu i korektę
aktualnej dokumentacji użytkowej oraz instrukcji projektowych zależnych od
tego interfejsu. Kryteria obejmują istotne regresje obecnego projektu.

Poza zakresem są: implementacja, jej plan, nowe wersje narzędzi i assety,
nowe platformy lub układy, package managery, source builds, synchronizacja
hostów, migracja rzeczywistego hosta, automatyczna zmiana konfiguracji findera,
przebudowa powłoki, aktywacja bibliotek w już otwartej sesji, zmiana polityki
resetowania checkoutu, automatyczne prune oraz faza 2 wycofania fzf.
Nie powstaje drugi katalog pakietów ani ręczna lista desired tools.

## Pojęcia i obserwowalny model

- **Katalog** to bieżące definicje przypiętych narzędzi. Obecność w katalogu
  nie oznacza instalacji ani obowiązku utrzymywania.
- **Zestaw zarządzany** to narzędzia skutecznie zainstalowane przez nowy cykl
  życia lub jednorazowo przejęte z dowodem własności, których użytkownik
  następnie nie odinstalował. Utrata pliku lub linku nie usuwa członkostwa.
- **Stan instalatora** to automatyczna trwała informacja potrzebna do odtworzenia
  tego członkostwa, diagnozy oraz bezpiecznego wznowienia. Nie jest edytowaną
  przez użytkownika deklaracją profilu ani desired-tools.
- **Aktywna instalacja** jest wskazana przez link narzędzia/aliasu w efektywnym
  bin albo aktywny link biblioteki w efektywnym prefiksie. Nieaktywny katalog
  wydania sam w sobie nie jest aktywną instalacją ani członkiem zestawu.
- **Dowód własności** rozdziela identyfikację narzędzia od zdrowia payloadu.
  Brakujący payload można zdiagnozować na podstawie wcześniej zapisanego stanu;
  sam brak payloadu nie pozwala wymyślić własności starego katalogu.
- **Narzędzie wycofane (`retired`)** ma zachowany zapis zarządzania, ale brak
  definicji w aktualnym katalogu. Zachowana definicja fzf w fazie 1 nie jest
  takim przypadkiem; jego ostrzeżenie o migracji jest informacyjne.

Stan i dowody należą do konkretnej instalacji określonej przez efektywne
`INSTALL_PREFIX` i `INSTALL_BIN_DIR`. Zmiana override lub XDG
nie może przypisać obcej instalacji do bieżącego zestawu ani posprzątać
starych lokalizacji. Dokładny sposób identyfikacji i przechowywania tego
powiązania wybierze plan.

## Wymagania

| ID | Kontrakt docelowy |
| --- | --- |
| REQ-001 | Publiczne komendy i walidacja odpowiadają sekcji interfejsu. Usunięte wejścia są błędami bez skutków ubocznych; nie przekierowują na nowe komendy. `install` i `uninstall` bez wyboru pokazują właściwe użycie, kończą się niepowodzeniem i nie inicjalizują ani nie migrują stanu. |
| REQ-002 | `install` nazw lub profilu dodaje wyłącznie skutecznie zainstalowane wybrane narzędzia do istniejącego zestawu. Nie usuwa ani nie zastępuje innych członków. Duplikaty nie powodują wielokrotnej operacji. Profil rozwija się przy tym konkretnym wywołaniu; nie jest zapamiętywaną subskrypcją. |
| REQ-003 | Ponowne `install <nazwa>` weryfikuje przypiętą wersję, layout, wymagane linki/aliasy i zdrowie lokalnej instalacji. Zdrową, kompletną instalację wykorzystuje ponownie bez pobrania; starą, brakującą lub uszkodzoną naprawia. Zewnętrzny odpowiednik w PATH nie spełnia instalacji zarządzanej i nie jest przejmowany ani usuwany. |
| REQ-004 | Stan jest utrzymywany automatycznie po rzeczywistych wynikach operacji, z zachowaniem wcześniejszych członków i informacji o brakach/uszkodzeniach. Użytkownik nie poprawia go ręcznie przy zwykłym install/uninstall/update. Nieczytelny, uszkodzony, obcy lub niespójny stan daje rozpoznawalny błąd i chroni dane; nie jest traktowany jako pusty nowy zestaw. |
| REQ-005 | Przed pierwszą skuteczną mutującą operacją nowego cyklu życia zachodzi jednorazowe przejęcie wszystkich udowodnionych aktywnych zarządzanych instalacji danej lokalizacji. Nie wymaga kompletnego `expected-tools`, obejmuje `binary`, `bundle`, `bash-builtin` i starsze przypięte wersje z dowodem. Nie przejmuje zewnętrznych narzędzi, samych nazw expected-only, nieaktywnych wydań ani nieudowodnionych pozostałości. Po zakończeniu nie uruchamia ponownie importu starej listy lub profilu. |
| REQ-006 | `list` i `check` są wyłącznie odczytowe, także przed migracją i przy błędach. Mogą obliczyć i opisać wykryte instalacje oczekujące na przejęcie, lecz nie zapisują stanu, znacznika migracji, cache, katalogów, configów ani linków. Nie pobierają niczego, nie uruchamiają binariów zarządzanych narzędzi i nie ładują bibliotek. Nieudana inwentaryzacja nie oznacza pustego zestawu. |
| REQ-007 | `expected-tools` nie wybiera narzędzi dla żadnej komendy runtime. Jego dawne wpisy mogą zostać odczytane wyłącznie jako diagnostyczne wskazówki w jednorazowej migracji, nigdy jako dowód własności lub żądanie instalacji. Migracja nie edytuje, nie usuwa i nie przepisuje tego pliku; raportuje ignorowane wskazówki. Późniejsze zmiany jego treści nie wpływają na zestaw. |
| REQ-008 | `uninstall <nazwa ...>` usuwa wskazane narzędzia z utrzymywanego zestawu i usuwa wyłącznie udowodnione własne linki/wydania. Nie usuwa innych członków, CLI, checkoutu, ustawień SSH/Git, startup files ani zewnętrznych odpowiedników w PATH. Ponowne usunięcie nieobecnego znanego narzędzia jest czytelnym sukcesem bez zmiany. Zapisana nazwa pozostaje rozpoznawana także bez definicji; bez dostatecznego dowodu własnych ścieżek operacja przerywa przed kasowaniem i zachowuje członkostwo. Niepełne usunięcie lub błąd I/O także nie kończą zarządzania nieukończonym narzędziem. Dopiero skuteczny uninstall znosi obowiązek naprawy przez update. |
| REQ-009 | `update` zachowuje obecny refresh projektu, po czym kod ze świeżego checkoutu aktualizuje i naprawia wyłącznie zapisany zestaw, w tym jego brakujące/uszkodzone instalacje. Nie wywołuje semantyki pustego `install`. Nie dodaje nowych członków profilu, nie instaluje pozycji expected-only i nie przywraca skutecznie odinstalowanych. Pusty zestaw pozwala zaktualizować sam projekt. |
| REQ-010 | Zestaw sprzed refreshu i jego dowody nie giną po zmianie definicji. Brak nowej definicji (`retired`) lub pasującego assetu (`unsupported`) jest widoczny w obu raportach; `update` nie zapomina wpisu, nie usuwa starej instalacji, nie wybiera innego pakietu i nie zgłasza pełnego sukcesu. Dane niedostateczne do bezpiecznej operacji pozostają chronione. |
| REQ-011 | `list` pokazuje katalog oraz stan zarządzania/instalacji według tabeli raportów, w stabilnym porządku alfabetycznym po nazwie narzędzia. Aliasy nie tworzą osobnych narzędzi. Zapisane missing/broken/retired i udowodnione instalacje oczekujące na przejęcie nie znikają przez filtr zdrowych payloadów. Brak wyników jest czytelnym sukcesem. |
| REQ-012 | `check` łączy diagnostykę środowiska z diagnostyką zestawu zarządzanego lub jawnie podanych nazw. Podaje problemy i konkretne następne działania z nowego CLI. Weryfikuje wersję, layout, payload, aliasy, własność, PATH lub link biblioteki, nie utożsamiając biblioteki z executable w PATH. Brak narzędzi wybranych do zarządzania sam w sobie nie jest awarią środowiska. |
| REQ-013 | Oba raporty rozróżniają brak członkostwa, missing, broken, starą wersję, brak wsparcia platformy, wycofaną definicję i nieudowodnioną własność. `check` dodatkowo rozróżnia external-only, kolizję, PATH shadowing i brak bin w PATH oraz problemy aliasów. Informacyjna wskazówka migracji fzf nie psuje zdrowego wyniku. |
| REQ-014 | Każde kasowanie lub zastąpienie istniejącej ścieżki wymaga odpowiedniego dowodu własności; zapis członkostwa sam nie nadaje własności obcemu plikowi. Zwykłe pliki, obce linki, symlinkowane rekordy, ścieżki wychodzące poza granice, nieznane/nieudowodnione katalogi i niebezpieczne `.active` są chronione. Uszkodzenie nie osłabia kryteriów kasowania. Przed zależną mutacją błąd odczytu/inwentaryzacji przerywa operację zamiast tworzyć niepełny pozornie poprawny obraz. |
| REQ-015 | Pojedyncza instalacja zachowuje staging nowego wydania i niezmienność wcześniejszych wydań. Błąd pobrania, checksumu, ekstrakcji, kwalifikacji biblioteki lub publikacji nie usuwa wcześniej działającego payloadu. Stan nie deklaruje zakończonej operacji przed jej rzeczywistym ukończeniem. `prune` nadal sam decyduje o nieaktywnych wydaniach i nie zachodzi automatycznie. |
| REQ-016 | Paczka operacji nie jest obiecywana jako jedna transakcja. Po błędzie lub przerwaniu raport i trwały stan muszą pozwalać odróżnić ukończone narzędzia, nieukończone narzędzia i zakres jeszcze niewykonany. Wcześniejsze sukcesy nie giną ani nie są cofane przez sam błąd kolejnej pozycji; nieukończone nowe narzędzie nie staje się członkiem. Po bezpiecznym wznowieniu nie wolno utracić zestawu ani wskrzesić zakończonego uninstall. |
| REQ-017 | Wybór, walidacja wejścia, granic stanu i kolizji oraz czytelny podgląd poprzedzają potwierdzenie i zależne zapisy. Install/uninstall bez `--yes` wymagają potwierdzenia TTY; odpowiedź odmowna, EOF lub brak TTY kończy się niepowodzeniem bez zapisu. `--yes` umożliwia skrypty, ale nie obchodzi walidacji, własności, checksumów lub kwalifikacji. `update` nie prosi o ponowny wybór już zarządzanego zestawu. |
| REQ-018 | Zachowane są istniejące przypięte manifesty, wybór platformy/libc, checksumy i ograniczenia formatów assetów oraz układów `binary`, `bundle`, `bash-builtin`. Zarządzanie pozostaje zgodne z Bash 3.2 i nie otrzymuje nowych zależności runtime. Ładowanie biblioteki nadal wymaga osobno zakwalifikowanego Bash >= 4.4, a zmiana aktywnego linku dotyczy nowych powłok. |
| REQ-019 | Instalacja nadal publikuje tylko CLI jako bezpośredni absolutny symlink do właściwego checkoutu, zachowuje bezpieczne kolizje i footer z efektywnymi ścieżkami; inne helpery i środowisko wymagają jawnego `shell`. `runme.sh` zachowuje edytowalny pierwszy wybór, forward jawnych argumentów bez własnej interpretacji oraz obecny `REMOTE_SSH_REF` i refresh. Ponowne jawne uruchomienie bootstrapu jest wyborem install, a nie automatyczną subskrypcją profilu. |
| REQ-020 | Zachowania poza cyklem życia, wskazane w C-001, pozostają bez zmian; aktualizowane są tylko komunikaty zależne od nowego CLI. `update check` i check przy logowaniu zachowują dotychczasową informacyjną semantykę, throttle, toggle i jawny zapis cache, bez fetch/pull/install/reset. Ta funkcja nie jest diagnostyczną komendą `check`. |
| REQ-021 | Zachowane są definicja/manifest fzf, bramka jego wycofania, adapter `shell/navi-bin/fzf`, izolacja Navi i jawny pass-through zewnętrznego findera. Nowy `check` przejmuje informacyjną wskazówkę migracji z `doctor`, gdy istnieje zarządzane fzf lub dawna wskazówka fzf w migracji. Sam zewnętrzny fzf nie uruchamia sugestii usunięcia. Żadna komenda nie zamienia fzf na sk ani nie zmienia preferencji findera automatycznie. |
| REQ-022 | Bieżące helpy, guide, README, instrukcje projektowe i dokumentacja użytkowa opisują jeden nowy kontrakt, automatyczny stan i bezpieczną migrację. Nie instruują już ręcznego utrzymywania expected-tools ani używania usuniętych komend/flag. Niezmienne historyczne dowody pozostają historią; dokumenty nadal używane operacyjnie wymagają czytelnego odsyłacza do aktualnego kontraktu. |

## Interfejs CLI

Poniższa gramatyka jest propozycją wiążącego interfejsu tej wersji.
`TOOL` oznacza dokładną, rozróżniającą wielkość liter nazwę narzędzia
z katalogu; dla uninstall/check dopuszcza też zachowaną nazwę z własnego
stanu, zgodnie z kontraktem narzędzia wycofanego. Nie jest nazwą binarnego
aliasu, ścieżką, wzorcem glob ani dowolnym poleceniem powłoki.

```text
remote-ssh install [--yes] TOOL [TOOL ...]
remote-ssh install --profile {mini|quick|full} [--yes]
remote-ssh uninstall [--yes] TOOL [TOOL ...]
remote-ssh update
remote-ssh list [--installed | --all]
remote-ssh check [TOOL ...]
```

`-h`/`--help` przy każdej z tych komend pokazuje jej użycie; główny
`remote-ssh help` i `remote-ssh --help` pozostają zwięzłym spisem.
`--profile=quick` jest równoważne `--profile quick`. Pozycja `--yes` względem
nazw jest dowolna. Jednokrotne powtórzenie `--yes` lub identycznego filtra
list nie rozszerza działania. Wielokrotny wybór `--profile`, również tej samej
wartości, jest błędem. Nazwy narzędzi są deduplikowane z zachowaniem pierwszej
kolejności. Nie ma nowego stdin z listą narzędzi, interaktywnego pickera,
flagi repair-all ani opcji wyboru nieprzypiętej wersji.

| Wejście | Walidacja, domyślne zachowanie i wynik |
| --- | --- |
| `install rg fd sk` | Waliduje wszystkie nazwy przed zmianami. Nieznana nazwa odrzuca całe wywołanie bez instalacji znanych pozycji. Narzędzia bez assetu dla hosta są jawnie pomijane, pozostałe instalowane. Jeśli nie ma żadnej wspieranej pozycji, błąd bez instalacji. Po podglądzie i potwierdzeniu sukces dodaje narzędzia do dotychczasowego zestawu. |
| `install --profile quick` | Rozwija wskazany profil z bieżącego katalogu, filtruje platformę, pokazuje wybór i pominięcia. Nie można łączyć z jawnymi nazwami. Nieznany/pusty profil, brak wartości i wielokrotny profil są błędami. |
| `install` / `install --yes` | Użycie i kod 1; nie odtwarza zestawu, nie pobiera i nie migruje danych. |
| `uninstall navi` | Wybiera wyłącznie navi, pokazuje własne ścieżki do usunięcia, chronione pozostałości i zmianę członkostwa. Usunięcie znanego nieobecnego narzędzia jest no-op. Nieznana nazwa spoza katalogu i własnego stanu jest błędem całego wywołania przed zapisami. Nazwa retired z własnego stanu jest rozpoznawana, ale kasowanie nadal wymaga pełnego niezależnego dowodu własności. Niedostateczny dowód przerywa przed usunięciem; niepełna operacja zachowuje zarządzanie i zwraca 1. |
| `uninstall` / `uninstall --yes` | Użycie i kod 1; nigdy domyślne remove-all. |
| `update` | Bez dodatkowych nazw/flag. Refresh checkoutu, potem aktualizacja/naprawa zestawu ze świeżego kodu. Nie jest nowym wyborem instalacji; działa bez TTY. Raportuje osobno wynik projektu i narzędzi. |
| `list` | Pokazuje katalog wspierany na hoście oraz wszystkie zapisane lub udowodnione aktywne instalacje, także niesprawne/unsupported/retired. Nie ma potrzeby uprzedniego install lub istnienia expected-tools. |
| `list --installed` | Ogranicza do zapisanego zestawu i udowodnionych aktywnych instalacji oczekujących na migrację. Nazwa filtra nie ukrywa zapisanych missing/broken/retired. |
| `list --all` | Dodatkowo pokazuje niewspierane pozycje katalogu bez instalacji. Nie łączy się z `--installed`. |
| `check` | Zawsze sprawdza środowisko; narzędzia: zapisany zestaw albo przed migracją udowodnione aktywne instalacje. Brak zestawu jest raportem `brak zarządzanych narzędzi`, a nie powodem instalacji profilu. |
| `check rg fd` | Sprawdza środowisko i tylko wskazane narzędzia; pozwala wykazać brak/external-only znanej pozycji spoza zestawu. Nie zmienia członkostwa i nie sprawdza pozostałych narzędzi jako części tego zakresu. Nieznana nazwa to błąd wejścia, nie wywołanie dowolnego programu. |

Początkowy skład profili zostaje zachowany z F-008:

```text
mini   rg fd sd
quick  rg fd sd bat starship eza zoxide sk navi atuin
full   fd rg sd dust sk bat bottom procs yazi nvim zellij nu starship eza zoxide atuin navi bssh
```

Flyline pozostaje poza profilami; `install flyline` korzysta z tego samego
cyklu życia. Edycja profili w przyszłym checkoutcie wpływa dopiero na kolejne
jawne `install --profile ...`. Jawny ponowny wybór profilu może ponownie
dodać wcześniej odinstalowane narzędzie, bo jest nowym poleceniem człowieka;
sam `update` i odczyt profilu nie mogą tego zrobić.

### Wejście, wyjście, błędy i kody

Wejściem są argumenty i istniejące zmienne konfiguracji ścieżek projektu,
w tym `REMOTE_ENV_DIR`, `INSTALL_PREFIX`, `INSTALL_BIN_DIR`, XDG i PATH.
Obecne domyślne prefix/bin pozostają `~/.local/opt` i `~/.local/bin`.
Nie dodaje się ręcznie utrzymywanej konfiguracji narzędzi. Stdin służy
wyłącznie potwierdzeniu install/uninstall; domyślną odpowiedzią jest odmowa.
Przekierowany stdin bez `--yes` nie jest domyślną zgodą.

Czytelny stdout zawiera wybór, wynik per narzędzie i podsumowanie lub raport.
Diagnostyka błędów i użycie po błędzie trafiają na stderr; pomoc na żądanie
na stdout. Komunikaty mogą pozostać po angielsku, jak bieżące CLI. Kontrakt
wiąże znaczenie informacji i etykiety statusów, nie szerokości kolumn,
kolory, pełne zdania lub format przeznaczony do maszynowego parsowania.

| Kod | Znaczenie |
| --- | --- |
| `0` | Poprawna pomoc, kompletny sukces operacji, jawny no-op lub kompletny raport list. Dla check: poprawne środowisko i brak problemów w wybranym zakresie narzędzi. Pojedyncze pominięcia unsupported w install nie psują wyniku, jeśli wspierany niepusty wybór zakończył się sukcesem i pominięcia są jawne. |
| `1` | Błędna składnia/nazwa/opcja, pusty wybór install/uninstall, odmowa/brak potwierdzenia, brak wspieranego wyboru, niezdrowy check, błąd stanu/inwentaryzacji, chroniona kolizja lub nieukończona operacja narzędzi. list zwraca 1 przy niemożności rzetelnego raportu, ale nie z powodu samego widocznego broken/missing/retired. |
| `127` | Zachowany szczególny przypadek braku git dla update lub runme. |
| Kod błędu git | Zachowane przekazanie niezerowego kodu fetch/reset; brak późniejszej instalacji. |
| Niezerowy po sygnale | Przerwana operacja nie jest sukcesem. Nie wymaga się własnych numerów dla każdego sygnału; obowiązuje odzyskiwalność i brak fałszywego zakończenia z REQ-016. |

Walidacja obejmuje całe argumenty także przy obecnym `--help`: pomoc nie
legalizuje nieznanej opcji, sprzecznych filtrów lub niepoprawnego wyboru.
Nieznane flagi i dodatkowe argumenty update/list są błędem. Usunięte
`remote-ssh tool ...`, `remote-ssh doctor`, `install --full`,
`install --skip-unsupported` i `check --strict` zwracają 1 bez migracji,
instalacji, diagnostyki starej komendy ani aliasu do nowego zachowania.
Dotychczasowe, niezwiązane kody innych komend pozostają poza tą zmianą.

### Raporty i statusy

`list` pokazuje co najmniej nazwę, członkostwo lub oczekujące przejęcie,
stan lokalny oraz wsparcie bieżącej definicji. `check` dodaje efektywne
ścieżki, oczekiwaną i wykrytą wersję, target linku, wynik PATH dla executable,
problemy aliasów, zakres raportu i następne działanie. Może pokazać wiele
etykiet dla jednego narzędzia; np. `broken` i `unsupported` nie wykluczają się.

| Status/informacja | Znaczenie i skutek check |
| --- | --- |
| `available` | Znana wspierana pozycja bez zarządzanej instalacji i bez zarejestrowanej awarii. Sama dostępność w list nie jest problemem. Jawny check niezainstalowanej nazwy wykazuje missing lub external-only. |
| `installed` / `ok` | Udowodniona kompletna lokalna instalacja; check dodatkowo wymaga zgodnej przypiętej wersji i poprawnego PATH/aliasów albo linku biblioteki. |
| `adoption-pending` | Przed pierwszą mutacją wykryto udowodnioną instalację, lecz niczego jeszcze nie zapisano. Sam ten fakt nie psuje check. |
| `missing` | Narzędzie jest zapisane, ale brak wymaganego aktywnego linku/payloadu, albo jawnie sprawdzana nazwa nie ma instalacji. Nie usuwa członkostwa. Check 1; dla zapisanego wpisu naprawa przez update lub install nazwy. |
| `broken` | Link istnieje, ale jest przerwany, payload nie jest właściwym plikiem/nie ma uprawnień, brakuje wymaganego aliasu lub instalacja ma niespójny layout/dowody. Check 1, z przyczyną i granicą możliwej naprawy. Nie jest prezentowane tylko jako available. |
| `stale` | Udowodniona wersja różni się od przypiętej. Check 1; update lub install nazwy aktualizuje ją bez zmiany członkostwa. |
| `unsupported` | Aktualna definicja nie ma assetu dla wykrytej platformy. Nieznana nazwa to osobny błąd. Check zapisanego/jawnie wybranego unsupported daje 1; instalacja pozostaje chroniona. |
| `retired` | Wpis istnieje w stanie, ale nie ma bieżącej definicji. Check i update 1, bez instalowania zamiennika i bez milczącego skasowania wpisu. Jawny uninstall może go usunąć tylko z dostatecznym dowodem własności; w przeciwnym razie 1, ochrona ścieżek i zachowanie zarządzania do naprawy. |
| `protected` / `unmanaged-local` | Ścieżka lub pozostałość nie ma dostatecznego dowodu własności. Nie staje się członkiem przez nazwę, zgodny prefix, expected-tools lub obecność w PATH. Check jawnej/zapisanej pozycji z kolizją daje 1. |
| `external-only` | W PATH jest narzędzie, ale brak zarządzanej instalacji w sprawdzanym zakresie. Check 1; zewnętrzny plik pozostaje bez zmian. |
| `path-shadowed` / `local-not-in-path` | Lokalna instalacja executable istnieje, lecz nie wygrywa w PATH lub nie jest w nim osiągalna. Check 1 i wskazówka ścieżki. Porównanie zachowuje fizyczną tożsamość katalogów, relatywne i puste wpisy PATH. Biblioteka nie dostaje tego błędu tylko dlatego, że nie ma executable. |
| `migration-needed` dla fzf | Informacyjna wskazówka instalacji i weryfikacji sk, sprawdzenia pickerów w nowym shell i jawnego uninstall fzf; bez automatycznej zmiany. Samo ostrzeżenie nie zmienia zdrowego kodu check. |

Diagnostyka środowiska obejmuje dotychczasowy potrzebny zakres doctor:
wymagane narzędzia runtime i warunkowe wymagania wybranego assetu,
spójność wskazanego/uruchomionego checkoutu, stan Git, obecność bin w PATH,
dostępność rc oraz optional helpers (`python3`, `ssh`, `sk` dla sshf).
Brak optional helpera jest ostrzeżeniem; brak wymaganej capability jest
błędem. Brudny checkout jest informacją, zgodnie z dotychczasowym raportem.
Weryfikacja rc ma pozostać bez skutków ubocznych; check nie uruchamia
sesyjnych importów, hooków sieciowych ani inicjalizacji bibliotek.

## Migracja i niepełne operacje

Migracja nie jest rekoncyliacją profilu ani starej konfiguracji. Przed jej
zapisem instalator musi mieć kompletny obraz potrzebnych aktywnych linków
bin i bibliotek. Błąd odczytu, niemożność enumeracji lub niebezpieczna
lokalizacja daje błąd przed zależną mutacją. Raport rozróżnia: udowodnione
instalacje do przejęcia, chronione niejednoznaczne pozostałości, nieaktywne
wydania oraz ignorowane stare wskazówki. Nie musi wypisywać całego starego
pliku i nie interpretuje jego treści jako kodu.

Szczególnie wymagany jest przypadek: aktywne własne rg/fd/sk/flyline,
`expected-tools` zawierający tylko flyline. Pierwsza prawidłowa operacja
mutująca przejmuje wszystkie cztery. Odmowa potwierdzenia nie zapisuje
przejęcia. Późniejszy `update` nie redukuje zestawu do flyline.

Przed powstaniem wiarygodnego stanu przerwany link lub brak payloadu może
pozbawić starą instalację dowodu. Taka pozostałość jest widoczna i chroniona;
nie nazywa się jej bezwarunkowo zainstalowaną ani automatycznie nie przejmuje.
`install <nazwa>` może naprawić ją wyłącznie przy spełnieniu zwykłych granic
własności i kolizji. Samo polecenie install nie daje prawa do zastąpienia
obcego pliku. Po powstaniu stanu utrata payloadu daje missing/broken dla
zachowanego członka, bez utraty informacji o potrzebie naprawy.

Przerwanie migracji/zapisu stanu nie może oznaczyć niepełnego rozpoznania
jako zakończonego ani obrócić starego zestawu w pusty. Powtórzenie operacji
ma bezpiecznie odzyskać ten sam zestaw i uwzględnić rzeczywiste ukończone
wyniki. Błąd po skutecznej instalacji pierwszego narzędzia w paczce nie może
zgubić go tylko dlatego, że drugie się nie zainstalowało. Nie obiecuje się
rollbacku całego checkoutu po refreshu ani całej paczki narzędzi.

Niebezpieczny wybór uninstall jest odrzucany przed kasowaniem któregokolwiek
z wybranych narzędzi. Jeżeli błąd I/O lub przerwanie wystąpi dopiero w trakcie
usuwania, nieukończone narzędzie pozostaje w zestawie z widocznym problemem;
update może je naprawić, bo uninstall nie zakończył się sukcesem. Narzędzie
usunięte skutecznie wcześniej w paczce pozostaje wyłączone z utrzymywania.
Stan nie może na podstawie samego braku linku uznać przerwanego usuwania
za świadome zakończenie zarządzania.

Jeżeli po refreshu projektu instalacja narzędzi się nie powiedzie, wynik
wyraźnie mówi, że projekt został już odświeżony, które narzędzia ukończono
i co pozostało. Nie zgłasza pełnego sukcesu ani automatycznego rollbacku.
Błąd fetch/reset zatrzymuje operację przed zmianą narzędzi i zachowuje
obecne zasady cache update-check. Bezpieczna kolejność wewnętrzna, checkpointy,
konkurencja i odzyskiwanie zapisu należą do planu, ale muszą spełniać te wyniki.

## Przypadki użycia

| ID | Aktor, cel i warunki | Przebieg → wynik | Warianty/błędy | Powiązania |
| --- | --- | --- | --- | --- |
| UC-001 | Człowiek, pierwszy wybór; dostępny checkout i wspierany host. | `install --profile quick`, podgląd, potwierdzenie → CLI i wspierane pozycje quick zainstalowane, automatyczny zestaw zapisany. | `--yes` dla skryptu; odmowa bez zapisów; unsupported jawnie pominięte; pusty wspierany wybór błędem. | REQ-001–005, REQ-017–019; AC-001–004, AC-019. |
| UC-002 | Człowiek, dodanie narzędzia; rg/fd już zarządzane. | `install sk --yes` → sk dodane, rg/fd zachowane; ponowne `install sk --yes` sprawdza lokalną instalację. | Stare/brakujące/uszkodzone sk naprawione; obcy sk w PATH nietknięty; kolizja lokalna chroniona. | REQ-002–004, REQ-014–016; AC-004–006, AC-016. |
| UC-003 | Człowiek, usunięcie navi z quick. | `uninstall navi`, podgląd, potwierdzenie → własne navi usunięte, pozostały zestaw zachowany. `update` nie odtwarza navi. | Bare uninstall nic nie usuwa; nieobecna znana nazwa no-op; nieznana odrzuca cały wybór; ścieżki obce chronione. | REQ-001, REQ-008–010, REQ-014, REQ-017; AC-001–003, AC-007–009. |
| UC-004 | Człowiek, bieżące utrzymanie; zapisane rg/fd/sk, brak linku fd. | `update` → odświeżony projekt, przypięte wersje zestawu, fd naprawione. | Błąd fetch/reset bez instalacji; pusty zestaw aktualizuje tylko projekt; retired/unsupported widoczne, nie usuwane. | REQ-004, REQ-009–010, REQ-015–016; AC-008–010, AC-017. |
| UC-005 | Człowiek, migracja starszego hosta; własne aktywne rg/fd/sk/flyline, legacy lista tylko flyline. | `list`/`check` pokazują wykryte instalacje bez zapisu. Następny potwierdzony install, uninstall albo update przejmuje udowodniony zestaw, wykonując swój jawny wybór. | Expected-only, nieaktywne i nieudowodnione pozostałości bez adopcji; odmowa i read-only nie kończą migracji; błąd enumeracji zatrzymuje. | REQ-004–007, REQ-014, REQ-016; AC-011–014, AC-017. |
| UC-006 | Człowiek, rozeznanie katalogu/stanu; żaden install nie jest wymagany. | `list`, `list --installed`, `list --all` → odpowiedni alfabetyczny raport bez sieci i zapisów. | Brak wyników sukcesem; broken/missing/retired pozostają widoczne; nieznana flaga lub konflikt filtrów błędem. | REQ-006, REQ-010–011, REQ-013; AC-012, AC-014–015. |
| UC-007 | Człowiek lub skrypt, kontrola środowiska i instalacji. | `check` albo `check rg fd` → zakres, szczegóły środowiska i narzędzi, następne działania, 0 tylko przy zdrowym zakresie. | Shadowing, missing alias, library bez executable, env mismatch i pusty zestaw są rozróżnione; brak optional helpera ostrzeżeniem. | REQ-006, REQ-012–013, REQ-018; AC-012, AC-015–016, AC-018. |
| UC-008 | Człowiek/skrypt, częściowo nieudana paczka. | `install rg fd sk --yes`, błąd fd po sukcesie rg → rg zachowane i zapisane, fd bez fałszywego sukcesu, sk jawnie niewykonane; wynik niezerowy. | Przerwanie publikacji/zapisu lub uninstall wymaga bezpiecznego odzyskania rzeczywistych wyników; wcześniejsza działająca wersja chroniona. | REQ-004, REQ-014–017; AC-016–017. |
| UC-009 | Człowiek, migracja findera fzf. | `install sk`, `check sk`, weryfikacja pickerów w nowej sesji, `uninstall fzf` → sk pozostaje, własne fzf usunięte na jawny wybór. | Zewnętrzne fzf i prywatny adapter pozostają; nie ma ręcznej synchronizacji expected-tools; usunięcie definicji nie należy do zadania. | REQ-007–008, REQ-021–022; AC-020–021. |

## Kryteria akceptacji

Kryteria dotyczą późniejszej implementacji. Ich istnienie nie oznacza, że
zostały już sprawdzone lub że należy wykonać implementację w tym workflowie.
W scenariuszach z siecią dopuszczalne jest offline podstawienie transportu
z zachowaniem zachowania publicznego CLI; prawdziwe instalacje i live asset
checks nie są warunkiem przygotowania specyfikacji.

| ID | Obserwowalny odbiór | Wymagania |
| --- | --- | --- |
| AC-001 | `tool install rg`, `tool list`, `doctor`, `install --full`, `install --skip-unsupported`, `check --strict` kończą się 1. Snapshoty stanu, configów, linków i wydań pozostają bez zmian; nie wykonano sieci lub starej operacji. Help wskazuje wyłącznie nowy cykl życia. | REQ-001, REQ-022. |
| AC-002 | Na istniejącej oraz nowej lokalizacji bare install/uninstall, również z samym `--yes`, pokazują użycie, zwracają 1 i niczego nie zmieniają. `--help` na poprawnym wejściu daje 0, stdout i brak skutków ubocznych. | REQ-001, REQ-006. |
| AC-003 | Nieznana nazwa w paczce ze znanymi, pusty/nieznany lub podwójny profil, profil z nazwą, konflikt filtrów i nieznana flaga są odrzucane przed zapisami. `--help` nie ukrywa wadliwego wejścia. Bez --yes brak TTY, EOF i odmowa nie publikują CLI, nie instalują, nie usuwają i nie zapisują migracji. | REQ-001–002, REQ-017. |
| AC-004 | Po `install rg fd --yes`, a potem `install sk --yes`, zestaw obejmuje rg/fd/sk. Install quick nie usuwa już zarządzanego narzędzia spoza quick. Powtórzone nazwy wykonują jedną operację. `--profile quick` i `--profile=quick` dają taki sam wybór. | REQ-002, REQ-004. |
| AC-005 | Drugi install zdrowej przypiętej nazwy nie pobiera assetu. Przypadki starszej wersji, brakującego linku, usuniętego payloadu oraz brakującego/starego aliasu są naprawiane albo dają konkretną chronioną kolizję, nigdy fałszywe pominięcie jako zdrowe. | REQ-003–004, REQ-014–015. |
| AC-006 | Zewnętrzny rg w PATH nie staje się członkiem; install rg tworzy własną instalację bez zmiany zewnętrznego pliku. Lokalny obcy zwykły plik/link blokuje zastąpienie i pozostaje bez zmian. Równoważny systemowy plik nie jest dowodem zarządzania. | REQ-003, REQ-014. |
| AC-007 | Po uninstall navi ze wspólnego zestawu znika wyłącznie navi, zewnętrzny odpowiednik i CLI pozostają. Ponowny uninstall znanego nieobecnego navi jest no-op 0. Żaden z tych wyników nie wymaga ręcznej edycji drugiej listy. | REQ-004, REQ-008, REQ-019. |
| AC-008 | Po instalacji quick, uninstall navi i dodaniu nowego narzędzia do definicji quick, update ani nie przywraca navi, ani nie dodaje nowej pozycji. Jawny późniejszy install quick może je dodać jako nowy wybór. | REQ-002, REQ-008–009. |
| AC-009 | Zapisany brakujący fd i broken sk są wykazane przez list/check, pozostają członkami i update je naprawia. Pusty zapisany zestaw pozwala update odświeżyć sam projekt bez instalacji profilu. | REQ-004, REQ-009, REQ-011–013. |
| AC-010 | Usunięcie definicji zapisanego narzędzia daje widoczny retired w list/check i błąd aktualizacji narzędzi, bez utraty wpisu lub kasowania payloadu. Utrata assetu dla platformy daje unsupported z wykrytą platformą. Uninstall rozpoznaje tę nazwę ze stanu. Jeśli brak dostatecznego dowodu własnych ścieżek, zwraca 1 bez kasowania i zachowuje członkostwo; niepełne usunięcie także nie odłącza zarządzania. Przy kompletnym dowodzie skuteczny uninstall usuwa wpis i update go nie odtwarza. | REQ-010, REQ-013–014. |
| AC-011 | Migracja aktywnych własnych rg/fd/sk/flyline przy legacy expected-tools zawierającym tylko flyline przejmuje wszystkie cztery. Działa również bez legacy pliku. Jego bajty nie zmieniają się, a późniejsze edycje nie zmieniają zestawu. | REQ-004–005, REQ-007. |
| AC-012 | Przed migracją i po niej list/check, również przy braku katalogów i awarii, nie tworzą ani nie modyfikują stanu, cache, configów, linków lub payloadu, nie wykonują sieci i nie uruchamiają sentinel binariów/bibliotek. Raport przed migracją pokazuje adoption-pending. | REQ-006, REQ-011–013. |
| AC-013 | Legacy expected-only, katalog nieaktywnego wydania, nieoznaczony katalog, obcy link i nieudowodniona broken pozostałość nie stają się członkami i nie powodują instalacji przez update. Są rozróżnione w raporcie migracji; znana nazwa i zgodny prefix nie zastępują dowodu. | REQ-005–007, REQ-014. |
| AC-014 | Nieczytelny/uszkodzony stan oraz nieudana lub częściowa enumeracja aktywnych linków dają błąd; zestaw nie jest zerowany i nie powstaje znacznik pomyślnej migracji. Próby wyjścia poza prefiks, podmiany znacznika symlinkiem i niebezpiecznej .active nie prowadzą do przejęcia/kasowania. | REQ-004–006, REQ-014. |
| AC-015 | Domyślna list pokazuje wspierany katalog i wszystkie zapisane/pending instalacje; --installed zachowuje missing/broken/retired, --all dodaje niewspierany katalog. Aliasy nie dają dodatkowych wierszy; sortowanie alfabetyczne. Puste wyniki 0. list z rzetelnie wykrytą awarią narzędzia 0; błąd odczytu uniemożliwiający raport 1. | REQ-010–011, REQ-013. |
| AC-016 | Check zdrowego wybranego zakresu daje 0; missing, broken, stale, unsupported/retired, external-only, shadowing, brak wymaganego aliasu i kolizja dają 1 z przyczyną. Fizycznie równoważne bin/PATH nie powodują fałszywego shadowing. Jawne nazwy ograniczają narzędzia, lecz zachowują część środowiskową. | REQ-006, REQ-012–014. |
| AC-017 | Awaria drugiego narzędzia po sukcesie pierwszego i przerwania podczas migracji, publikacji oraz zapisu nie tracą wcześniejszego zestawu, nie zapisują fałszywego sukcesu i dają odzyskiwalny wynik. Po bezpiecznym wznowieniu ukończony uninstall nie jest odtworzony. Błąd fetch/reset nie instaluje; błąd po skutecznym refreshu ujawnia częściowy wynik bez deklaracji rollbacku checkoutu. | REQ-004–005, REQ-009, REQ-014–016. |
| AC-018 | Binary, bundle z wymaganymi danymi i bash-builtin zachowują przypięte assety i wybór platformy/libc. Zarządzanie działa w Bash 3.2. Błąd checksumu/ekstrakcji/probe biblioteki pozostawia stare działające wydanie; library nie wymaga executable w bin/PATH i nie zostaje załadowana przez list/check. | REQ-003, REQ-015, REQ-018. |
| AC-019 | Runme bez args przekazuje swój jawny pierwszy wybór, z args przekazuje je bez interpretacji; wybór --profile i --yes trafia do install. REF/refresh zachowują dotychczasowe zasady. Instalacja publikuje wyłącznie kanoniczny CLI, zachowuje kolizje i efektywne ścieżki footera oraz pozostawia wszystkie startup files bez zmian. | REQ-017–019. |
| AC-020 | Przed i po zmianie semantyka shell/setup/ssh/git/prune/scripts/guide i update check pozostaje taka sama w zakresie spoza nowego cyklu życia; informacyjne update checks nie wykonują refreshu/instalacji. Wskazówki CLI używają nowych nazw. Nie powstają runtime zależności z dev tooling. | REQ-018–020, REQ-022. |
| AC-021 | Definicja fzf i jej przypięte assety/checksumy oraz prywatny adapter pozostają. Check zarządzanego fzf daje informacyjną wskazówkę, również gdy sk już istnieje; zewnętrzne fzf samo jej nie wywołuje. Procedura migracji używa install sk, check sk i jawnego uninstall fzf, bez ręcznej edycji expected-tools i bez automatycznej zmiany findera lub usunięcia pakietu. | REQ-007, REQ-021–022. |

## Dokumentacja zależna

REQ-022 obejmuje co najmniej aktualne opisy w [AGENTS.md](../../AGENTS.md),
[README.md](../../README.md), [docs/install.md](../../docs/install.md),
[docs/tools.md](../../docs/tools.md), [docs/shell/helpers.md](../../docs/shell/helpers.md),
[docs/shell/flyline.md](../../docs/shell/flyline.md) oraz generowane teksty
help/guide w [guide/sections.sh](../../tools/lib/commands/guide/sections.sh)
i [guide/tools.sh](../../tools/lib/commands/guide/tools.sh).
Obejmuje też komunikaty instalacyjne takie jak wskazówka skim w
[shell/rc.d/21-zoxide.sh](../../shell/rc.d/21-zoxide.sh).

Bieżący [plan migracji fzf](fzf-retirement-plan.md) zawiera operacyjne kroki
`tool install`, `check --strict` i ręczną edycję expected-tools. Przyszła
implementacja musi dostarczyć czytelny aktualny wariant tych kroków,
zachowując historyczny zapis ukończonej fazy 1 i nie zmieniając bramki fazy 2.
Zamrożone raporty, snapshoty i dowody dawnych wydań nie są instrukcjami
nowego runtime i nie wymagają przepisywania. Dokumenty wskazujące je jako
aktualną procedurę wymagają przekierowania do aktualnej instrukcji.

Istotne punkty regresji do oceny późniejszego planu znajdują się w
[test_install_cli.py](../tests/test_install_cli.py),
[test_install_expected_tools.py](../tests/test_install_expected_tools.py),
[test_tool_list.py](../tests/test_tool_list.py), [test_check.py](../tests/test_check.py),
[test_doctor.py](../tests/test_doctor.py), [test_uninstall.py](../tests/test_uninstall.py),
[test_update.py](../tests/test_update.py), [test_runme.py](../tests/test_runme.py),
[test_release_ownership.py](../tests/test_release_ownership.py),
[test_prune.py](../tests/test_prune.py), [test_install_library.py](../tests/test_install_library.py)
i [test_install_failures.py](../tests/test_install_failures.py).
To źródła istniejących granic, nie gotowy plan zmian w testach ani wyniki
odbioru nowego kontraktu.

## Założenia, propozycje i pytania

| ID | Rodzaj | Treść i wpływ |
| --- | --- | --- |
| A-001 | Założenie do potwierdzenia przez akceptację szkicu. | Początkowy skład profili pozostaje z F-008; zmiana dotyczy ich semantyki, nie nowego doboru pakietów. Brak blokady przy zachowaniu obecnego składu. |
| A-002 | Propozycja szczegółu interfejsu. | Zachowujemy oba zapisy --profile i dotychczasowe zasady potwierdzania --yes, kody 0/1 oraz szczególne przekazywanie git/127. Pozostałe szczegóły tabeli CLI i statusów podlegają akceptacji tej wersji, nie są niezależnymi decyzjami już zatwierdzonymi. |
| A-003 | Założenie zakresu. | Zmiana nie wprowadza nowego publicznego interfejsu niskopoziomowego tools/install-tool.sh. Nie może on stanowić alternatywnej instrukcji użytkowej omijającej nowe członkostwo; plan rozstrzygnie wewnętrzny podział odpowiedzialności. |
| Q-001 | Decyzja zamknięta przez człowieka (D-011). | Niebezpieczny lub niepełny uninstall nie odłącza zarządzania; przy braku dowodu abort i zachowanie stanu do naprawy. Włączone do REQ-008 i AC-010. |

Nie wybiera się tutaj formatu pliku stanu, jego schematu, liczby plików,
algorytmu checkpointów, locków, nazw funkcji ani konkretnych edycji modułów.
Te decyzje nie mogą osłabić ustalonego cyklu życia, granic własności,
odzyskiwalności, read-only raportów lub założeń minimalnego runtime.

## Historia dokumentu

| Wersja | Data | Stan i zakres |
| --- | --- | --- |
| 0.1 | 2026-11-10 | Pierwszy szkic na podstawie rozpoznania repozytorium i decyzji człowieka przekazanych przez koordynatora. Bez implementacji i bez deklaracji akceptacji. Q-001 zamknięte przez decyzję D-011; brak otwartych blokujących pytań produktu. |
