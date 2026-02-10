# Często Zadawane Pytania (FAQ) - PersonaPlex

## Spis treści

1. [Podstawy](#podstawy)
2. [Instalacja i konfiguracja](#instalacja-i-konfiguracja)
3. [Użytkowanie](#użytkowanie)
4. [Wydajność i optymalizacja](#wydajność-i-optymalizacja)
5. [Integracja z robotem](#integracja-z-robotem)
6. [Problemy techniczne](#problemy-techniczne)
7. [Rozwój i customizacja](#rozwój-i-customizacja)

---

## Podstawy

### Co to jest PersonaPlex?

PersonaPlex to model konwersacyjny speech-to-speech (mowa-do-mowy) działający w trybie full-duplex. Oznacza to, że:
- **Wejście:** Głos użytkownika (audio)
- **Wyjście:** Głos asystenta/robota (audio)
- **Full-duplex:** Może słuchać i mówić jednocześnie, jak w naturalnej rozmowie

### Czym różni się od ChatGPT/innych chatbotów?

| Feature | PersonaPlex | Tradycyjny chatbot |
|---------|-------------|-------------------|
| Wejście | Audio (głos) | Tekst |
| Wyjście | Audio (głos) | Tekst |
| Opóźnienie | < 200ms | Zależy od TTS |
| Full-duplex | Tak (może przerywać) | Nie (turn-based) |
| Kontrola głosu | Tak | Tylko przez TTS |

**Kluczowa różnica:** PersonaPlex generuje audio bezpośrednio, bez pośrednictwa tekstu. To znacznie zmniejsza opóźnienie i umożliwia naturalne interakcje.

### Co to znaczy "full-duplex"?

W kontekście rozmowy:
- **Half-duplex (tradycyjne):** Jedna osoba mówi → druga słucha → zamienia się
- **Full-duplex (PersonaPlex):** Obie strony mogą mówić i słuchać jednocześnie

Analogia: Rozmowa telefoniczna (full-duplex) vs walkie-talkie (half-duplex).

### Jakie języki są obsługiwane?

PersonaPlex jest trenowany głównie na **języku angielskim**. Jednak:
- ✅ Najlepsza jakość: angielski
- ⚠️ Częściowe wsparcie: inne języki (polski, hiszpański, francuski, etc.)
- ❌ Brak wsparcia: języki z innym alfabetem bez korpusu treningowego

**Dla polskiego:** Model może rozumieć i odpowiadać po polsku, ale jakość będzie niższa niż dla angielskiego.

### Czy mogę użyć PersonaPlex bez GPU?

**Tak, ale...**
- **Z GPU:** Szybkie (~200ms opóźnienie), zalecane dla real-time
- **Bez GPU (tylko CPU):** Wolniejsze (1-5s opóźnienie), trudne dla real-time

**Rozwiązania dla CPU:**
- Tryb offline: Działa dobrze, tylko wolniej
- CPU offload: Część obliczeń na CPU, część na GPU
- Serwer zdalny: Robot używa zdalnego serwera z GPU przez sieć

### Ile pamięci GPU jest potrzebne?

**Wymagania VRAM:**
- **Minimum:** 8GB (RTX 3060, RTX 2080 Ti)
- **Zalecane:** 12GB+ (RTX 3090, RTX 4090, A100)
- **Z CPU offload:** 6GB może wystarczyć

**Optymalizacje:**
- Użyj `--cpu-offload` jeśli masz < 12GB
- Zamknij inne aplikacje używające GPU
- Rozważ kwantyzację (nie jest domyślnie wspierana)

---

## Instalacja i konfiguracja

### Jak zainstalować PersonaPlex na Ubuntu?

Zobacz [QUICK_START.pl.md](QUICK_START.pl.md) dla szczegółowego przewodnika.

**Skrócona wersja:**
```bash
# 1. Zainstaluj zależności systemowe
sudo apt install libopus-dev

# 2. Sklonuj repo
git clone https://github.com/AI-robot-lab/nvidia-personaplex.git
cd nvidia-personaplex

# 3. Utwórz środowisko wirtualne
python3 -m venv personaplex_env
source personaplex_env/bin/activate

# 4. Zainstaluj pakiet
pip install moshi/.

# 5. Ustaw token Huggingface
export HF_TOKEN=your_token_here
```

### Czy mogę zainstalować na Windows?

**Tak, ale z ograniczeniami:**
- Instalacja jest możliwa
- Niektóre zależności mogą wymagać kompilacji (wymaga Visual Studio)
- Zalecamy WSL2 (Windows Subsystem for Linux) dla łatwiejszej instalacji

**Rekomendacja:** Użyj Ubuntu w WSL2 i postępuj według normalnej instrukcji.

### Co to jest token Huggingface i jak go uzyskać?

Token Huggingface to klucz dostępu do pobierania modeli z platformy Huggingface.

**Kroki:**
1. Utwórz konto: https://huggingface.co/join
2. Zaakceptuj licencję: https://huggingface.co/nvidia/personaplex-7b-v1
3. Wygeneruj token: https://huggingface.co/settings/tokens (typ: Read)
4. Ustaw w środowisku: `export HF_TOKEN=your_token`

### Jak sprawdzić czy GPU jest używane?

**Metoda 1: nvidia-smi**
```bash
# W jednym terminalu: uruchom PersonaPlex
python -m moshi.server --ssl "$SSL_DIR"

# W drugim terminalu: monitoruj GPU
watch -n 1 nvidia-smi

# Powinieneś zobaczyć:
# - python process używający GPU
# - Wykorzystanie pamięci (np. 8000MB / 12000MB)
# - Wykorzystanie GPU (np. 80%)
```

**Metoda 2: PyTorch check**
```bash
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
# Powinno wyświetlić: CUDA available: True
```

### Czy muszę pobierać model za każdym razem?

**Nie!** Model pobiera się tylko raz i jest cache'owany lokalnie.

**Lokalizacja cache:**
```bash
# Linux/Mac
~/.cache/huggingface/hub/models--nvidia--personaplex-7b-v1/

# Windows
C:\Users\<username>\.cache\huggingface\hub\models--nvidia--personaplex-7b-v1\
```

**Rozmiar:** ~3GB

---

## Użytkowanie

### Jak wybrać odpowiedni głos?

PersonaPlex oferuje 18 głosów w 4 kategoriach:

**Natural (NAT) - Najlepsze dla robotów:**
- **NATF0-3:** Naturalne głosy kobiece
- **NATM0-3:** Naturalne głosy męskie
- Charakterystyka: Najbardziej jak prawdziwe ludzkie rozmowy

**Variety (VAR) - Więcej różnorodności:**
- **VARF0-4:** Zróżnicowane głosy kobiece
- **VARM0-4:** Zróżnicowane głosy męskie
- Charakterystyka: Bardziej ekspresywne, zróżnicowane intonacje

**Rekomendacja dla robota humanoidalnego:**
1. Zacznij od NATM1 lub NATF2 (najbardziej neutralne)
2. Przetestuj kilka opcji z tym samym pytaniem
3. Wybierz najlepiej pasujący do kontekstu (nauczyciel, przewodnik, asystent)

### Jak napisać dobry text prompt?

**Struktura skutecznego promptu:**
```
1. Rola: Kim jesteś?
2. Kontekst: Gdzie i po co?
3. Zachowanie: Jak masz się zachowywać?
4. Informacje: Jakie fakty posiadasz?
```

**Przykład - dobry prompt:**
```
You are G1, a museum guide robot at the National Museum of Technology.
You provide engaging explanations about exhibits.
You speak clearly and enthusiastically.
You know about robotics, AI, space exploration, and computing history.
Available exhibits: Mars rover, IBM mainframe, first industrial robot, quantum computer.
```

**Przykład - słaby prompt:**
```
You are a robot.  # Za ogólne, brak kontekstu
```

**Wskazówki:**
- Bądź konkretny
- Użyj 3-7 zdań
- Dodaj fakty/wiedzę którą ma posiadać
- Określ ton/styl komunikacji
- Przetestuj z różnymi pytaniami

### Co to jest seed i kiedy go używać?

**Seed** to liczba kontrolująca losowość generowania.

**Ten sam seed = te same wyniki:**
```bash
# Uruchom dwa razy z tym samym seed
python -m moshi.offline --input-wav "test.wav" --output-wav "out1.wav" --seed 42
python -m moshi.offline --input-wav "test.wav" --output-wav "out2.wav" --seed 42
# out1.wav i out2.wav będą identyczne
```

**Kiedy używać:**
- ✅ Testy (chcesz reprodukowalnych wyników)
- ✅ Debugowanie (łatwiej znaleźć przyczynę problemu)
- ✅ Porównania (testowanie różnych konfiguracji)
- ❌ Produkcja (chcesz naturalnej różnorodności)

**Zalecane seedy dla testów:** 42, 123456, 42424242 (łatwe do zapamiętania)

### Jak nagrać dobrej jakości pytanie WAV?

**Parametry nagrania:**
```bash
arecord -f S16_LE -r 24000 -c 1 -d 10 pytanie.wav
```
- `-f S16_LE`: Format 16-bit signed little-endian
- `-r 24000`: Sample rate 24000 Hz (wymagane przez PersonaPlex)
- `-c 1`: Mono (1 kanał)
- `-d 10`: Długość 10 sekund

**Wskazówki dla jakości:**
- Używaj dobrego mikrofonu (USB zalecane)
- Nagraj w cichym pomieszczeniu
- Mów wyraźnie, nie za głośno
- Odległość od mikrofonu: 10-20 cm
- Unikaj klaskania, stuków, hałasu

### Czy mogę przerwać modelowi w połowie zdania?

**Tak! To jedna z kluczowych cech PersonaPlex.**

W trybie full-duplex:
- Model ciągle "słucha" wejścia
- Gdy użytkownik zaczyna mówić → model "wie" o tym
- Model może zareagować (przestać, odpowiedzieć, itp.)
- To jest trenowane zachowanie

**W praktyce:**
- Tryb real-time (server): Działa automatycznie
- Tryb offline: Nie ma przerywania (przetwarzanie całego pliku)

### Jak zmienić parametry sampling (temperatura, top-k)?

**W kodzie (server.py lub offline.py):**

Znajdź utworzenie `LMGen` i dodaj parametry:
```python
lm_gen = LMGen(
    lm,
    # ... inne parametry ...
    temp=0.8,        # Temperatura dla audio (domyślnie ~0.8)
    temp_text=0.7,   # Temperatura dla tekstu (domyślnie ~0.7)
    top_k=250,       # Top-K dla audio (domyślnie 250)
    top_k_text=25    # Top-K dla tekstu (domyślnie 25)
)
```

**Co robią parametry:**
- **Temperatura (temp):** Wyższa = bardziej kreatywne, niższa = bardziej konserwatywne
- **Top-K:** Ile najlepszych tokenów brać pod uwagę (niższe = więcej fokus, wyższe = więcej różnorodności)

**Rekomendacje:**
- Dla konserwatywnych odpowiedzi: temp=0.5, top_k=100
- Dla kreatywnych odpowiedzi: temp=1.0, top_k=500
- Dla balanced: użyj domyślnych

---

## Wydajność i optymalizacja

### Model działa wolno - jak przyspieszyć?

**Diagnostyka:**
```bash
# Sprawdź wykorzystanie GPU
nvidia-smi

# Sprawdź czy model jest na GPU
python -c "import torch; print(torch.cuda.is_available())"
```

**Optymalizacje:**

**1. Użyj mocniejszego GPU**
- RTX 3090, RTX 4090, A100, H100

**2. CPU offload (jeśli mało VRAM)**
```bash
python -m moshi.server --ssl "$SSL_DIR" --cpu-offload
```

**3. Zamknij inne aplikacje**
- Przeglądarka, edytor kodu, inne modele AI

**4. Użyj najnowszych sterowników NVIDIA**
```bash
nvidia-smi  # Sprawdź wersję
# Zaktualizuj ze strony NVIDIA jeśli stare
```

**5. Włącz CUDA graphs (domyślnie włączone po warmup)**
- Warmup automatycznie inicjalizuje CUDA graphs
- Nie pomijaj warmup!

### Ile czasu zajmuje pierwsze uruchomienie?

**Breakdown:**
1. **Pobieranie modelu:** 5-10 minut (3GB, jednorazowo)
2. **Ładowanie do pamięci:** 30-60 sekund
3. **Warmup:** 20-40 sekund
4. **Pierwsze generowanie:** Szybkie (już rozgrzane)

**Kolejne uruchomienia:**
- Ładowanie: 30-60s (model w cache)
- Warmup: 20-40s
- Gotowe do użycia!

### Co to jest warmup i czy mogę go pominąć?

**Warmup** to inicjalizacja GPU przed prawdziwą pracą.

**Co się dzieje podczas warmup:**
- Alokacja pamięci GPU
- Kompilacja CUDA kernels
- Budowa CUDA graphs
- Inicjalizacja stanu streaming

**Czy mogę pominąć?**
- ❌ **Nie zalecamy!** Pierwsze odpowiedzi będą bardzo wolne
- ✅ Możliwe, ale jakość real-time ucierpi

**Dlaczego warto:**
- Stabilne opóźnienia
- Szybsze generowanie
- Przewidywalna wydajność

### Jak zmniejszyć użycie pamięci GPU?

**Opcja 1: CPU offload**
```bash
python -m moshi.server --ssl "$SSL_DIR" --cpu-offload
```
- Część warstw na CPU
- Zmniejsza VRAM o ~40%
- Zwiększa opóźnienie o ~20-50%

**Opcja 2: Batch size = 1 (domyślne)**
- PersonaPlex już używa najmniejszego batch size
- Nie da się bardziej zmniejszyć

**Opcja 3: Zamknij inne aplikacje używające GPU**
```bash
# Sprawdź co używa GPU
nvidia-smi

# Zabij procesy jeśli niepotrzebne
kill -9 <PID>
```

### Czy mogę uruchomić wiele instancji jednocześnie?

**Teoretycznie tak, ale...**

**Ograniczenia:**
- Każda instancja = ~8GB VRAM
- GPU z 24GB VRAM = maksymalnie 2-3 instancje
- CPU offload pozwala na więcej, ale wolniej

**Rekomendacja:**
- **Dla produkcji:** Używaj load balancera i wielu serwerów
- **Dla testów:** Jedna instancja wystarczy
- **Dla robota:** Jedna instancja per robot

**Architektura dla wielu robotów:**
```
Robot 1 ──┐
Robot 2 ──┼──> Load Balancer ──┬──> Server 1 (GPU 1)
Robot 3 ──┘                     ├──> Server 2 (GPU 2)
                                └──> Server 3 (GPU 3)
```

---

## Integracja z robotem

### Jak połączyć PersonaPlex z robotem Unitree G1?

Zobacz szczegółowy przewodnik: [UNITREE_G1_GUIDE.pl.md](UNITREE_G1_GUIDE.pl.md)

**Kroki wysokiego poziomu:**
1. Uruchom serwer PersonaPlex (lokalnie lub zdalnie)
2. Utwórz interfejs audio dla robota (mikrofony + głośniki)
3. Zaimplementuj klienta WebSocket w Pythonie
4. Podłącz do systemu kontroli robota (ROS 2)

### Czy mogę używać PersonaPlex z ROS 2?

**Tak!** Możliwe podejścia:

**Opcja 1: Bezpośrednie połączenie WebSocket**
```python
# W node ROS 2
import rclpy
import asyncio
import websockets

class PersonaPlexNode(Node):
    def __init__(self):
        super().__init__('personaplex_node')
        # Połącz do serwera PersonaPlex
        self.ws = await websockets.connect('wss://localhost:8998')
        # ...
```

**Opcja 2: Bridge node**
```
PersonaPlex Server <──> Bridge Node <──> ROS 2 Topics
                       (WebSocket)      (audio_in, audio_out, text)
```

**Korzyści:**
- Modularność
- Łatwe testowanie
- Możliwość wymiany komponentów

### Gdzie uruchomić serwer - na robocie czy zdalnie?

**Opcja A: Lokalnie na robocie**
- ✅ Bardzo niskie opóźnienie
- ✅ Brak zależności od sieci
- ❌ Wymaga mocnego GPU na robocie
- ❌ Większe zużycie energii

**Opcja B: Zdalny serwer GPU**
- ✅ Nie wymaga GPU na robocie
- ✅ Łatwiej skalować (wiele robotów → jeden serwer)
- ❌ Wyższe opóźnienie (+50-200ms)
- ❌ Wymaga stabilnej sieci

**Rekomendacja dla G1 EDU:**
- **Prototyp/testy:** Zdalny serwer (łatwiej debugować)
- **Demo/produkcja:** Lokalnie (lepsze user experience)

### Jak obsłużyć audio w systemie robota?

**Pipeline audio:**
```
Mikrofon → PortAudio/ALSA → PCM → Opus Encoder → WebSocket → PersonaPlex
PersonaPlex → WebSocket → Opus Decoder → PCM → PortAudio/ALSA → Głośniki
```

**Biblioteki pomocnicze:**
- **sphn:** Enkoder/dekoder Opus (używany przez PersonaPlex)
- **sounddevice:** Obsługa urządzeń audio w Pythonie
- **pyaudio:** Alternatywa dla sounddevice

**Przykład kodu (uproszczony):**
```python
import sounddevice as sd
import sphn

# Inicjalizacja
opus_writer = sphn.OpusStreamWriter(24000)
opus_reader = sphn.OpusStreamReader(24000)

# Nagrywanie z mikrofonu
def callback(indata, frames, time, status):
    # Enkoduj PCM → Opus
    opus_writer.append_pcm(indata[:, 0])
    opus_bytes = opus_writer.read_bytes()
    # Wyślij przez WebSocket
    await ws.send(opus_bytes)

# Uruchom stream
stream = sd.InputStream(callback=callback, samplerate=24000, channels=1)
stream.start()
```

---

## Problemy techniczne

### Model nie generuje sensownych odpowiedzi

**Możliwe przyczyny:**

**1. Słaba jakość audio wejściowego**
- Sprawdź nagranie: `aplay pytanie.wav`
- Upewnij się że sample rate = 24000 Hz
- Usuń hałas tła

**2. Nieprawidłowy text prompt**
- Prompt musi być w języku angielskim
- Użyj znaczników `<system>` (funkcja robi to automatycznie)
- Sprawdź czy prompt ma sens

**3. Problem z voice prompt**
- Sprawdź czy plik voice prompt istnieje
- Użyj predefiniowanych głosów (NATM1.pt, etc.)

**4. Model nie został poprawnie załadowany**
- Sprawdź logi podczas uruchamiania
- Poszukaj błędów pobierania z Huggingface
- Sprawdź czy token HF_TOKEN jest ustawiony

**Debugowanie:**
```bash
# Przetestuj z znanym przykładem
python -m moshi.offline \
  --voice-prompt "NATM1.pt" \
  --input-wav "assets/test/input_assistant.wav" \
  --output-wav "test_out.wav" \
  --output-text "test_out.json" \
  --seed 42424242

# Jeśli to działa → problem jest w Twoim wejściu
# Jeśli to nie działa → problem z instalacją
```

### Połączenie WebSocket się rozłącza

**Możliwe przyczyny:**

**1. Timeout sieci**
- Zwiększ timeout w konfiguracji WebSocket
- Sprawdź stabilność połączenia: `ping <server_ip>`

**2. Serwer się crashes**
- Sprawdź logi serwera
- Poszukaj błędów CUDA (out of memory, etc.)
- Spróbuj `--cpu-offload`

**3. Problem z certyfikatem SSL**
- Użyj self-signed cert dla testów
- Sprawdź czy przeglądarka zaakceptowała certyfikat

**4. Firewall blokuje połączenie**
- Otwórz port 8998 w firewall
- Ubuntu: `sudo ufw allow 8998`

**Debugowanie:**
```bash
# W logach serwera poszukaj:
# - "connection closed" - normalne zakończenie
# - "error" - problem
# - stack trace - błąd krytyczny

# Sprawdź czy port jest otwarty
netstat -tuln | grep 8998

# Sprawdź czy możesz się połączyć
curl -k https://localhost:8998
```

### "FileNotFoundError: voices.tgz"

**Przyczyna:** Model nie może znaleźć plików z głosami.

**Rozwiązanie:**
```bash
# 1. Sprawdź token HF
echo $HF_TOKEN

# 2. Zaakceptuj licencję
# Przejdź do: https://huggingface.co/nvidia/personaplex-7b-v1

# 3. Ręcznie pobierz voices.tgz
huggingface-cli download nvidia/personaplex-7b-v1 voices.tgz

# 4. Rozpakuj
cd ~/.cache/huggingface/hub/models--nvidia--personaplex-7b-v1/snapshots/<hash>/
tar -xzf voices.tgz
```

### Przeglądarka nie pyta o dostęp do mikrofonu

**Przyczyny i rozwiązania:**

**1. Strona nie jest HTTPS**
- Przeglądarki wymagają HTTPS dla mikrofonu
- Sprawdź czy używasz `https://` (nie `http://`)

**2. Dostęp już jest zablokowany**
- Sprawdź ustawienia: chrome://settings/content/microphone
- Usuń blokadę dla localhost:8998

**3. Mikrofon jest używany przez inną aplikację**
```bash
# Linux: Sprawdź co używa mikrofonu
lsof /dev/snd/*
# Zamknij inne aplikacje (Zoom, Skype, etc.)
```

**4. Brak mikrofonu w systemie**
```bash
# Lista dostępnych mikrofonów
arecord -l

# Test mikrofonu
arecord -d 5 test.wav
aplay test.wav
```

---

## Rozwój i customizacja

### Jak dodać własny głos?

**Opcja 1: Użyj pliku WAV (prostsze)**
```bash
# Nagraj 5-10 sekund czystego audio głosu
arecord -f S16_LE -r 24000 -c 1 -d 10 moj_glos.wav

# Użyj jako voice prompt
python -m moshi.offline \
  --voice-prompt "moj_glos.wav" \
  --input-wav "pytanie.wav" \
  --output-wav "odpowiedz.wav"
```

**Opcja 2: Generuj embeddingi (szybsze)**
```python
# W kodzie (wymaga modyfikacji)
lm_gen.load_voice_prompt("moj_glos.wav")
lm_gen.save_voice_prompt_embeddings("moj_glos.pt")

# Następnie możesz użyć .pt zamiast .wav (szybsze)
```

**Wskazówki dla jakości:**
- Użyj wysokiej jakości nagrania (profesjonalny mikrofon)
- Osoba mówi naturalnie, nie monotonnie
- Bez hałasu tła
- 5-10 sekund ciągłej mowy

### Jak zmodyfikować kod dla własnych potrzeb?

**Struktura kodu:**
```
moshi/moshi/
├── server.py          # Serwer WebSocket (real-time)
├── offline.py         # Tryb offline (batch processing)
├── models/
│   ├── lm.py         # Model językowy (LMGen, LMModel)
│   ├── compression.py # Mimi (kompresja audio)
│   └── loaders.py    # Ładowanie modeli
├── utils/
│   ├── connection.py # WebSocket utilities
│   └── sampling.py   # Algorytmy sampling
```

**Przykład: Dodaj logging transkrypcji**
```python
# W server.py, w opus_loop(), po dekodowaniu tokena tekstowego:
if text_token not in (0, 3):
    _text = self.text_tokenizer.id_to_piece(text_token)
    _text = _text.replace("▁", " ")
    
    # DODAJ: Zapisz transkrypcję do pliku
    with open("transkrypcja.txt", "a") as f:
        f.write(_text)
    
    msg = b"\x02" + bytes(_text, encoding="utf8")
    await ws.send_bytes(msg)
```

### Czy mogę dostroić (fine-tune) model?

**Teoretycznie tak, ale...**

PersonaPlex bazuje na Moshi, który jest dużym modelem (7B parametrów).

**Wyzwania:**
- Wymaga dużego korpusu danych (tysiące godzin audio)
- Wymaga bardzo mocnego GPU (8x A100)
- Wymaga specjalistycznej wiedzy (deep learning, speech)

**Alternatywy:**
- **Promptowanie:** Dostosuj zachowanie przez text prompt (prostsze)
- **Voice cloning:** Użyj własnego głosu przez voice prompt (prostsze)
- **Few-shot learning:** Dodaj przykłady w prompcie (nie wspierane natywnie)

**Dla większości przypadków:** Promptowanie + voice prompt wystarczą!

### Jak zintegrować z innymi systemami AI?

**Przykład: Dodaj vision (rozpoznawanie obrazu)**
```python
# Architektura
Robot Camera → YOLO/ResNet → Object Detection → Text Description
                                                       ↓
PersonaPlex ← Text Prompt (enriched with vision info) ←
```

**Kod (szkic):**
```python
# 1. Wykryj obiekty
objects = yolo_model.detect(image)
objects_text = ", ".join([obj.name for obj in objects])

# 2. Wzbogać prompt
text_prompt = f"""
You are a robot assistant.
You can see the following objects: {objects_text}.
Answer questions about what you see.
"""

# 3. Użyj z PersonaPlex
lm_gen.text_prompt_tokens = tokenizer.encode(wrap_with_system_tags(text_prompt))
```

### Gdzie znaleźć więcej przykładów kodu?

**W repozytorium:**
- `moshi/moshi/server.py` - pełny przykład serwera real-time
- `moshi/moshi/offline.py` - przykład batch processing
- `client/src/` - przykład klienta webowego (TypeScript)

**Społeczność:**
- **GitHub Issues:** https://github.com/AI-robot-lab/nvidia-personaplex/issues
- **Discord:** https://discord.gg/5jAXrrbwRb
- **Paper:** https://research.nvidia.com/labs/adlr/files/personaplex/personaplex_preprint.pdf

**Przykłady community:**
- Sprawdź forks repozytorium na GitHubie
- Poszukaj "personaplex" na GitHubie
- Discord - kanał #showcase

---

## Dodatkowe zasoby

### Dokumentacja
- [README.pl.md](../README.pl.md) - Główna dokumentacja
- [QUICK_START.pl.md](QUICK_START.pl.md) - Szybki start
- [ARCHITECTURE.pl.md](ARCHITECTURE.pl.md) - Architektura systemu
- [UNITREE_G1_GUIDE.pl.md](UNITREE_G1_GUIDE.pl.md) - Integracja z robotem
- [START_TUTAJ.pl.md](START_TUTAJ.pl.md) - Przewodnik dla studentów

### Linki zewnętrzne
- **Paper:** https://research.nvidia.com/labs/adlr/files/personaplex/personaplex_preprint.pdf
- **Demo:** https://research.nvidia.com/labs/adlr/personaplex/
- **Huggingface:** https://huggingface.co/nvidia/personaplex-7b-v1
- **Discord:** https://discord.gg/5jAXrrbwRb
- **GitHub:** https://github.com/AI-robot-lab/nvidia-personaplex

---

**Nie znalazłeś odpowiedzi?**
- Otwórz Issue na GitHubie
- Zapytaj na Discordzie
- Sprawdź dokumentację techniczną w kodzie

*FAQ przygotowane dla studentów Politechniki Rzeszowskiej - Luty 2026*
