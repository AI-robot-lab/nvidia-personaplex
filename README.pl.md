# PersonaPlex: Kontrola Głosu i Roli dla Modeli Konwersacyjnych Full Duplex

[![Weights](https://img.shields.io/badge/🤗-Weights-yellow)](https://huggingface.co/nvidia/personaplex-7b-v1)
[![Paper](https://img.shields.io/badge/📄-Paper-blue)](https://research.nvidia.com/labs/adlr/files/personaplex/personaplex_preprint.pdf)
[![Demo](https://img.shields.io/badge/🎮-Demo-green)](https://research.nvidia.com/labs/adlr/personaplex/)
[![Discord](https://img.shields.io/badge/Discord-Join-purple?logo=discord)](https://discord.gg/5jAXrrbwRb)

## Wprowadzenie

PersonaPlex to model konwersacyjny działający w czasie rzeczywistym w trybie full-duplex (pełny dupleks), który umożliwia kontrolę osobowości (persona) poprzez tekstowe prompty roli oraz kondycjonowanie głosu w formacie audio. Wytrenowany na kombinacji syntetycznych i rzeczywistych rozmów, generuje naturalne interakcje głosowe o niskim opóźnieniu z konsekwentną osobowością. PersonaPlex bazuje na architekturze i wagach modelu [Moshi](https://arxiv.org/abs/2410.00037).

### Co to oznacza dla projektu z robotem humanoidalnym?

Ten system umożliwia:
- **Rozmowy w czasie rzeczywistym**: Robot może prowadzić płynne, naturalne konwersacje bez widocznych opóźnień
- **Różne osobowości**: Możliwość zaprogramowania różnych charakterów - od przyjaznego nauczyciela po specjalistę obsługi klienta
- **Full-duplex**: Robot może słuchać i mówić jednocześnie, podobnie jak ludzie w naturalnej rozmowie
- **Kontrola głosu**: Wybór różnych głosów (męskich/damskich, naturalnych/zróżnicowanych)

<p align="center">
  <img src="assets/architecture_diagram.png" alt="Architektura modelu PersonaPlex">
  <br>
  <em>Architektura PersonaPlex</em>
</p>

## Instalacja i uruchomienie

### Wymagania wstępne

Zainstaluj bibliotekę deweloperską kodeka audio [Opus](https://github.com/xiph/opus):

```bash
# Ubuntu/Debian
sudo apt install libopus-dev

# Fedora/RHEL
sudo dnf install opus-devel

# macOS
brew install opus
```

**Uwaga**: Kodek Opus jest niezbędny do kompresji i dekompresji strumieni audio w czasie rzeczywistym.

### Instalacja oprogramowania

Pobierz to repozytorium i zainstaluj za pomocą:
```bash
pip install moshi/.
```

**Dodatkowy krok dla GPU Blackwell** jak sugerowano w (Zobacz https://github.com/NVIDIA/personaplex/issues/2):
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130
```

### Akceptacja licencji modelu

Zaloguj się na swoje konto Huggingface i zaakceptuj licencję modelu PersonaPlex [tutaj](https://huggingface.co/nvidia/personaplex-7b-v1). 

Następnie skonfiguruj uwierzytelnianie Huggingface:
```bash
export HF_TOKEN=<TWÓJ_TOKEN_HUGGINGFACE>
```

**Wyjaśnienie**: Token HF_TOKEN jest potrzebny do automatycznego pobierania wag modelu z platformy Huggingface.

### Uruchomienie serwera

Uruchom serwer dla interakcji na żywo (tymczasowe certyfikaty SSL dla https):
```bash
SSL_DIR=$(mktemp -d); python -m moshi.server --ssl "$SSL_DIR"
```

**Offload CPU:** Jeśli Twoje GPU ma niewystarczającą pamięć, użyj flagi `--cpu-offload` aby przenieść warstwy modelu na CPU. Wymaga to pakietu `accelerate` (`pip install accelerate`):
```bash
SSL_DIR=$(mktemp -d); python -m moshi.server --ssl "$SSL_DIR" --cpu-offload
```

**Wyjaśnienie opcji**:
- `SSL_DIR=$(mktemp -d)`: Tworzy tymczasowy katalog dla certyfikatów SSL
- `--ssl`: Włącza szyfrowane połączenie HTTPS (wymagane przez przeglądarki dla dostępu do mikrofonu)
- `--cpu-offload`: Przydatne gdy GPU ma mało pamięci - część obliczeń przenosi na CPU

Dostęp do interfejsu webowego z przeglądarki pod adresem `localhost:8998` jeśli działa lokalnie, w przeciwnym razie sprawdź link dostępu wyświetlony przez skrypt:
```
Access the Web UI directly at https://11.54.401.33:8998
```

### Ewaluacja offline

Do ewaluacji offline użyj skryptu offline, który strumieniuje plik wav wejściowy i produkuje plik wav wyjściowy z przechwyconego strumienia wyjściowego. Plik wyjściowy będzie miał ten sam czas trwania co plik wejściowy.

Dodaj `--cpu-offload` do dowolnego polecenia poniżej jeśli Twoje GPU ma niewystarczającą pamięć (wymaga pakietu `accelerate`). Lub zainstaluj PyTorch tylko-CPU dla ewaluacji offline na czystym CPU.

**Przykład asystenta:**
```bash
HF_TOKEN=<TOKEN> \
python -m moshi.offline \
  --voice-prompt "NATF2.pt" \
  --input-wav "assets/test/input_assistant.wav" \
  --seed 42424242 \
  --output-wav "output.wav" \
  --output-text "output.json"
```

**Przykład obsługi klienta:**
```bash
HF_TOKEN=<TOKEN> \
python -m moshi.offline \
  --voice-prompt "NATM1.pt" \
  --text-prompt "$(cat assets/test/prompt_service.txt)" \
  --input-wav "assets/test/input_service.wav" \
  --seed 42424242 \
  --output-wav "output.wav" \
  --output-text "output.json"
```

**Wyjaśnienie parametrów**:
- `--voice-prompt`: Wybór głosu dla robota/asystenta (np. NATF2 = naturalny głos kobiecy 2)
- `--text-prompt`: Prompt tekstowy definiujący rolę i osobowość
- `--input-wav`: Plik audio z pytaniem/wypowiedzią użytkownika
- `--seed`: Ziarno losowości dla powtarzalnych wyników
- `--output-wav`: Plik wyjściowy z odpowiedzią audio
- `--output-text`: Plik JSON z transkrypcją tekstową odpowiedzi

## Dostępne głosy

PersonaPlex wspiera szeroki zakres głosów; dostarczamy wstępnie zapakowane embeddingi dla głosów które brzmią bardziej naturalnie i konwersacyjnie (NAT) oraz innych które są bardziej zróżnicowane (VAR). Stały zestaw głosów jest oznaczony:

```
Naturalne (kobiece): NATF0, NATF1, NATF2, NATF3
Naturalne (męskie):  NATM0, NATM1, NATM2, NATM3
Zróżnicowane (kobiece): VARF0, VARF1, VARF2, VARF3, VARF4
Zróżnicowane (męskie):  VARM0, VARM1, VARM2, VARM3, VARM4
```

**Wskazówka**: Dla projektu z robotem humanoidalnym zaleca się rozpocząć od głosów naturalnych (NAT), które brzmią najbardziej jak prawdziwe ludzkie rozmowy.

## Przewodnik po promptowaniu

Model jest wytrenowany na syntetycznych rozmowach dla stałej roli asystenta oraz różnorodnych ról obsługi klienta.

### Rola asystenta

Rola asystenta ma prompt:
```
You are a wise and friendly teacher. Answer questions or provide advice in a clear and engaging way.
```
(Jesteś mądrym i przyjaznym nauczycielem. Odpowiadaj na pytania lub udzielaj rad w jasny i angażujący sposób.)

Użyj tego promptu dla asystenta QA skupionego na kategorii ewaluacji "User Interruption" w [FullDuplexBench](https://arxiv.org/abs/2503.04721).

### Role obsługi klienta

Role obsługi klienta wspierają różnorodne prompty. Oto kilka przykładów dla referencji stylu promptowania:

```
You work for CitySan Services which is a waste management and your name is Ayelen Lucero. Information: Verify customer name Omar Torres. Current schedule: every other week. Upcoming pickup: April 12th. Compost bin service available for $8/month add-on.
```
(Pracujesz dla CitySan Services, firmy zajmującej się gospodarką odpadami i nazywasz się Ayelen Lucero. Informacje: Zweryfikuj nazwisko klienta Omar Torres. Obecny harmonogram: co drugi tydzień. Nadchodzący odbiór: 12 kwietnia. Usługa kompostownika dostępna za 8$/miesiąc jako dodatek.)

```
You work for Jerusalem Shakshuka which is a restaurant and your name is Owen Foster. Information: There are two shakshuka options: Classic (poached eggs, $9.50) and Spicy (scrambled eggs with jalapenos, $10.25). Sides include warm pita ($2.50) and Israeli salad ($3). No combo offers. Available for drive-through until 9 PM.
```
(Pracujesz dla Jerusalem Shakshuka, restauracji i nazywasz się Owen Foster. Informacje: Dostępne są dwie opcje shakshuki: Klasyczna (jajka w koszulkach, $9.50) i Pikantna (jajecznica z jalapeno, $10.25). Dodatki to ciepła pita ($2.50) i sałatka izraelska ($3). Brak ofert combo. Dostępne w drive-through do 21:00.)

```
You work for AeroRentals Pro which is a drone rental company and your name is Tomaz Novak. Information: AeroRentals Pro has the following availability: PhoenixDrone X ($65/4 hours, $110/8 hours), and the premium SpectraDrone 9 ($95/4 hours, $160/8 hours). Deposit required: $150 for standard models, $300 for premium.
```
(Pracujesz dla AeroRentals Pro, firmy wynajmującej drony i nazywasz się Tomaz Novak. Informacje: AeroRentals Pro ma następującą dostępność: PhoenixDrone X ($65/4 godziny, $110/8 godzin), oraz premium SpectraDrone 9 ($95/4 godziny, $160/8 godzin). Wymagana kaucja: $150 dla modeli standardowych, $300 dla premium.)

**Struktura promptu**: 
1. Kim jesteś (rola, firma, imię)
2. Konkretne informacje które posiadasz
3. Szczegóły dotyczące oferty/usług

### Swobodne rozmowy

Model jest również wytrenowany na rzeczywistych rozmowach z [Fisher English Corpus](https://catalog.ldc.upenn.edu/LDC2004T19) z promptami oznaczonymi przez LLM dla otwartych konwersacji. Oto kilka przykładowych promptów dla swobodnych rozmów:

```
You enjoy having a good conversation.
```
(Lubisz dobrą rozmowę.)

```
You enjoy having a good conversation. Have a casual discussion about eating at home versus dining out.
```
(Lubisz dobrą rozmowę. Przeprowadź swobodną dyskusję o jedzeniu w domu kontra w restauracji.)

```
You enjoy having a good conversation. Have an empathetic discussion about the meaning of family amid uncertainty.
```
(Lubisz dobrą rozmowę. Przeprowadź empatyczną dyskusję o znaczeniu rodziny w obliczu niepewności.)

```
You enjoy having a good conversation. Have a reflective conversation about career changes and feeling of home. You have lived in California for 21 years and consider San Francisco your home. You work as a teacher and have traveled a lot. You dislike meetings.
```
(Lubisz dobrą rozmowę. Przeprowadź refleksyjną rozmowę o zmianach kariery i poczuciu domu. Mieszkasz w Kalifornii od 21 lat i uważasz San Francisco za swój dom. Pracujesz jako nauczyciel i dużo podróżujesz. Nie lubisz spotkań.)

Użyj promptu `You enjoy having a good conversation.` dla kategorii ewaluacji "Pause Handling", "Backchannel" i "Smooth Turn Taking" z FullDuplexBench.

## Generalizacja

PersonaPlex dostraja Moshi i korzysta z możliwości generalizacji bazowego LLM [Helium](https://kyutai.org/blog/2025-04-30-helium). Dzięki szerokiemu korpusowi treningowemu, model będzie prawdopodobnie reagował na prompty spoza rozkładu treningowego i prowadził do nieoczekiwanych lub zabawnych rozmów. Zachęcamy do eksperymentowania z różnymi promptami aby przetestować zdolność modelu do obsługi scenariuszy poza jego rozkładem treningowym.

## Zastosowanie w robotyce - Unitree G1 EDU

Aby dowiedzieć się jak zintegrować PersonaPlex z robotem humanoidalnym Unitree G1 EDU, zobacz szczegółowy przewodnik:

📖 **[Przewodnik integracji z robotem Unitree G1 EDU](docs/UNITREE_G1_GUIDE.pl.md)**

## Licencja

Obecny kod jest dostarczany na licencji MIT. Wagi dla modeli są wydane na licencji NVIDIA Open Model.

## Cytowanie

Jeśli używasz PersonaPlex w swoich badaniach, proszę cytuj nasz artykuł:
```bibtex
@article{roy2026personaplex,
  title={PersonaPlex: Voice and Role Control for Full Duplex Conversational Speech Models},
  author={Roy, Rajarshi and Raiman, Jonathan and Lee, Sang-gil and Ene, Teodor-Dumitru and Kirby, Robert and Kim, Sungwon and Kim, Jaehyeon and Catanzaro, Bryan},
  year={2026}
}
```
