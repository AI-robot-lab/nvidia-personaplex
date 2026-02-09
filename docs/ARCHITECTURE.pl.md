# Architektura PersonaPlex - Przewodnik dla Studentów

## Wprowadzenie

Ten dokument wyjaśnia jak działa PersonaPlex od środka - jego architekturę, główne komponenty i przepływ danych. Jest przeznaczony dla studentów Politechniki Rzeszowskiej uczących się pracy z robotem humanoidalnym Unitree G1 EDU.

## Spis treści

1. [Przegląd wysokiego poziomu](#przegląd-wysokiego-poziomu)
2. [Główne komponenty](#główne-komponenty)
3. [Przepływ danych](#przepływ-danych)
4. [Dwa tryby pracy](#dwa-tryby-pracy)
5. [Kluczowe koncepty](#kluczowe-koncepty)
6. [Pytania i odpowiedzi](#pytania-i-odpowiedzi)

## Przegląd wysokiego poziomu

### Czym jest PersonaPlex?

PersonaPlex to **system konwersacyjny mowy-do-mowy** (speech-to-speech) działający w **trybie full-duplex**. Co to oznacza?

- **Mowa-do-mowy**: Wejście to audio (głos), wyjście to audio (głos) - bez pośredniego tekstu
- **Full-duplex**: Może jednocześnie słuchać i mówić, jak w prawdziwej rozmowie między ludźmi
- **Real-time**: Działa w czasie rzeczywistym z niskim opóźnieniem (< 200ms)

### Dla kogo jest ten system?

PersonaPlex jest idealny dla:
- 🤖 **Robotów humanoidalnych** - naturalna komunikacja głosowa
- 📞 **Systemów IVR** - inteligentna obsługa klienta  
- 🎓 **Asystentów edukacyjnych** - nauczanie i wyjaśnianie
- 🏥 **Aplikacji healthcare** - wsparcie i informacja

## Główne komponenty

System składa się z kilku kluczowych komponentów:

### 1. Mimi - Model Kompresji Audio

**Co robi:** Kompresuje i dekompresuje audio  
**Dlaczego:** Surowe audio jest za duże - Mimi zmniejsza je do małych "codes"

```
Audio PCM (duże) → Mimi Encoder → Codes (małe) → Mimi Decoder → Audio PCM (duże)
```

**Analogia:** Jak algorytm ZIP dla plików - zmniejsza rozmiar, zachowując jakość.

**Technicznie:**
- Sample rate: 24000 Hz (24000 próbek na sekundę)
- Frame rate: 12.5 Hz (12.5 ramek na sekundę)  
- Każda ramka = 24000/12.5 = 1920 próbek = 80ms audio
- Kompresja: ~100x mniejszy rozmiar

**W kodzie:**
```python
# Enkodowanie (kompresja)
codes = mimi.encode(audio_chunk)  # [B, C, samples] → [B, K, frames]

# Dekodowanie (dekompresja)
audio = mimi.decode(codes)  # [B, K, frames] → [B, C, samples]
```

### 2. Moshi LM - Model Językowy

**Co robi:** "Mózg" systemu - generuje odpowiedzi (tekst + audio)  
**Dlaczego:** To tutaj dzieje się "myślenie" i decyzje o tym co powiedzieć

```
Codes wejściowe → Moshi LM → Tokeny wyjściowe (tekst + audio)
```

**Architektura:**
- Bazuje na transformerze (jak GPT, ale dla audio)
- Multi-stream: Obsługuje wiele strumieni jednocześnie
  - Strumień 0: Tekst (słowa)
  - Strumienie 1-8: Audio (8 codebooków Mimi)

**Kluczowe cechy:**
- **Autoregressive**: Generuje krok po kroku
- **Full-duplex aware**: Wie o obu stronach rozmowy
- **Persona-controlled**: Można kontrolować osobowość przez prompty

**W kodzie:**
```python
# Jeden krok generowania
tokens = lm_gen.step(input_codes)  # [B, K_in, T] → [B, K_out, T]
# tokens[0] = tekst
# tokens[1:9] = audio (8 codebooków)
```

### 3. Tokenizer - Konwersja Tekstu

**Co robi:** Zamienia tekst ↔ liczby  
**Dlaczego:** Model pracuje na liczbach, nie na słowach

```
"Hello" → Tokenizer → [123, 456] → Model → [789] → Tokenizer → "Hi"
```

**Szczegóły:**
- Używa SentencePiece (algorytm BPE)
- Rozbija słowa na podjednostki (subwords)
- Symbol ▁ oznacza spację

**Przykład:**
```
"Cześć jak się masz?" 
→ ["▁Cz", "eść", "▁jak", "▁się", "▁masz", "?"]
→ [1234, 567, 8901, 2345, 6789, 111]
```

### 4. LMGen - Generator Wysokiego Poziomu

**Co robi:** Zarządza procesem generowania (wrapper na LM)  
**Dlaczego:** Upraszcza użycie modelu - obsługuje streaming, prompty, sampling

**Funkcje:**
- Zarządza stanem streaming
- Ładuje voice prompts (embeddingi głosu)
- Ładuje text prompts (instrukcje dla modelu)
- Kontroluje sampling (temperatura, top-k)

**W kodzie:**
```python
lm_gen = LMGen(
    lm,                                    # Model językowy
    audio_silence_frame_cnt=6,             # Cisza po promptach
    sample_rate=24000,                     # Sample rate audio
    device="cuda",                         # GPU/CPU
    frame_rate=12.5,                       # Frame rate
    temp=0.8,                              # Temperatura audio
    temp_text=0.7,                         # Temperatura tekstu
    top_k=250,                             # Top-k audio
    top_k_text=25                          # Top-k tekstu
)
```

## Przepływ danych

### Tryb Real-Time (server.py)

```
┌─────────────┐
│  Mikrofon   │
│  Użytkownika│
└──────┬──────┘
       │ PCM Audio
       ▼
┌──────────────┐
│ Opus Encode  │  ← Kompresja dla sieci
└──────┬───────┘
       │ Opus Bytes
       ▼
┌──────────────┐
│  WebSocket   │  ← Transmisja
└──────┬───────┘
       │ Opus Bytes
       ▼
┌──────────────┐
│ Opus Decode  │  ← Dekompresja
└──────┬───────┘
       │ PCM Audio
       ▼
┌──────────────┐
│ Mimi Encode  │  ← Kompresja AI
└──────┬───────┘
       │ Codes
       ▼
┌──────────────┐
│  Moshi LM    │  ← Generowanie odpowiedzi
└──────┬───────┘
       │ Tokens (text + audio)
       ▼
┌──────────────┐
│ Mimi Decode  │  ← Dekompresja AI
└──────┬───────┘
       │ PCM Audio
       ▼
┌──────────────┐
│ Opus Encode  │  ← Kompresja dla sieci
└──────┬───────┘
       │ Opus Bytes
       ▼
┌──────────────┐
│  WebSocket   │  ← Transmisja
└──────┬───────┘
       │ Opus Bytes
       ▼
┌──────────────┐
│ Opus Decode  │  ← Dekompresja
└──────┬───────┘
       │ PCM Audio
       ▼
┌──────────────┐
│  Głośnik     │
│  Robota      │
└──────────────┘
```

**Równoległe strumienie:**
- Strumień IN: Mikrofon → Serwer (ciągle)
- Strumień OUT: Serwer → Głośnik (ciągle)
- Oba działają jednocześnie (full-duplex!)

### Tryb Offline (offline.py)

```
┌──────────────┐
│ Plik WAV     │
│ (pytanie)    │
└──────┬───────┘
       │ PCM Audio (cały plik)
       ▼
┌──────────────┐
│ Mimi Encode  │  ← Kompresja ramka po ramce
└──────┬───────┘
       │ Codes
       ▼
┌──────────────┐
│  Moshi LM    │  ← Generowanie ramka po ramce
└──────┬───────┘
       │ Tokens (text + audio)
       ▼
┌──────────────┐
│ Mimi Decode  │  ← Dekompresja ramka po ramce
└──────┬───────┘
       │ PCM Audio (akumulacja)
       ▼
┌──────────────┐
│ Plik WAV     │
│ (odpowiedź)  │
└──────────────┘
```

**Różnice vs Real-Time:**
- Brak WebSocket - wszystko lokalne
- Przetwarzanie całego pliku naraz
- Prostsze (brak concurrent tasks)
- Wolniejsze (ale nie ma wymagania real-time)

## Dwa tryby pracy

### 1. Tryb Real-Time (server.py)

**Kiedy używać:**
- ✅ Interakcje z robotem w czasie rzeczywistym
- ✅ Demonstracje na żywo
- ✅ Rzeczywiste zastosowania produkcyjne

**Jak uruchomić:**
```bash
SSL_DIR=$(mktemp -d)
python -m moshi.server --ssl "$SSL_DIR" --host 0.0.0.0 --port 8998
```

**Komponenty:**
- `ServerState`: Zarządza stanem serwera
- `handle_chat`: Obsługuje połączenie WebSocket
- `recv_loop`: Odbiera audio od klienta
- `opus_loop`: Przetwarza i generuje
- `send_loop`: Wysyła audio do klienta

**Kluczowe:**
- Trzy pętle działają równolegle (asyncio)
- Lock zapewnia że tylko jedna sesja na raz
- Opus kompresja dla efektywnej transmisji

### 2. Tryb Offline (offline.py)

**Kiedy używać:**
- ✅ Testy i eksperymenty
- ✅ Generowanie przykładów
- ✅ Debugowanie zachowania
- ✅ Batch processing

**Jak uruchomić:**
```bash
python -m moshi.offline \
  --voice-prompt "NATM1.pt" \
  --text-prompt "You are a helpful robot." \
  --input-wav "question.wav" \
  --output-wav "answer.wav" \
  --output-text "answer.json" \
  --seed 42424242
```

**Komponenty:**
- `run_inference`: Główna funkcja przetwarzania
- `warmup`: Rozgrzewka modeli
- Pętla przetwarzania ramek

**Kluczowe:**
- Synchroniczne (brak asyncio)
- Reprodukowalne (seed)
- Prosty do testowania

## Kluczowe koncepty

### 1. Streaming

**Co to jest?**  
Przetwarzanie danych małymi fragmentami (ramkami) zamiast całości naraz.

**Dlaczego?**
- ✅ Niskie opóźnienie (real-time)
- ✅ Stała pamięć (nie rośnie z czasem)
- ✅ Responsywne (szybko reaguje)

**W kodzie:**
```python
# Włącz streaming (batch_size=1)
mimi.streaming_forever(1)
lm_gen.streaming_forever(1)

# Resetuj stan (na początku rozmowy)
mimi.reset_streaming()
lm_gen.reset_streaming()
```

### 2. Ramki (Frames)

**Co to jest?**  
Mały fragment audio (np. 80ms).

**Dlaczego ramki?**
- Model przetwarza ramka po ramce
- Każda ramka to 1920 próbek @ 24kHz
- Odpowiada 1/12.5s = 80ms

**Wizualizacja:**
```
Audio:  |----1920 próbek----|----1920 próbek----|----1920 próbek----|
        |     Ramka 0        |     Ramka 1        |     Ramka 2        |
Czas:   0ms                  80ms                 160ms                240ms
```

### 3. Codebooki (Codebooks)

**Co to jest?**  
Sposób reprezentacji audio w skompresowanej formie.

**Mimi używa 8 codebooków:**
- Każdy codebook = jedna "warstwa" informacji
- Razem tworzą pełną reprezentację audio
- Hierarchiczne: 1 = gruba struktura, 8 = drobne detale

**Analogia:**  
Jak malowanie obrazu warstwami:
- Warstwa 1: Ogólny szkic
- Warstwa 2: Główne kolory
- Warstwa 3-8: Coraz więcej detali

### 4. Multi-stream Generation

**Co to jest?**  
Model generuje wiele strumieni jednocześnie.

**Struktura:**
```
Stream 0:  [Tekst]     [Tekst]     [Tekst]     ...
Stream 1:  [Audio-1]   [Audio-1]   [Audio-1]   ...
Stream 2:  [Audio-2]   [Audio-2]   [Audio-2]   ...
...
Stream 8:  [Audio-8]   [Audio-8]   [Audio-8]   ...
```

**W kodzie:**
```python
tokens = lm_gen.step(input_codes)
# tokens ma kształt [B, 9, T]
# tokens[:, 0, :] = strumień tekstowy
# tokens[:, 1:9, :] = 8 strumieni audio
```

### 5. Prompty

**Text Prompt:**
Definiuje rolę i zachowanie modelu.

```python
text_prompt = """
You are G1, a helpful robot assistant.
You speak clearly and are friendly.
"""
```

**Voice Prompt:**
Definiuje głos modelu (barwa, intonacja).

```python
voice_prompt = "NATM1.pt"  # Naturalny męski głos 1
```

**System Tags:**
Prompty muszą być opakowane w znaczniki:
```
<system> [treść promptu] <system>
```

### 6. Sampling

**Co to jest?**  
Sposób wybierania następnego tokena z dystrybucji prawdopodobieństwa.

**Parametry:**

**Temperatura (temp):**
- Niższa (0.1-0.5) = konserwatywne, przewidywalne
- Wyższa (0.8-1.2) = kreatywne, zróżnicowane

**Top-K:**
- Rozważa tylko K najbardziej prawdopodobnych tokenów
- Mniejsze K = bardziej fokus
- Większe K = więcej różnorodności

**Greedy:**
- Zawsze wybiera najbardziej prawdopodobny token
- Deterministyczne (z tym samym seed zawsze to samo)

**W kodzie:**
```python
lm_gen = LMGen(
    lm,
    temp=0.8,        # Temperatura audio
    temp_text=0.7,   # Temperatura tekstu  
    top_k=250,       # Top-K audio
    top_k_text=25    # Top-K tekstu
)
```

## Pytania i odpowiedzi

### Q: Dlaczego są dwa modele Mimi (mimi i other_mimi)?

**A:** To optymalizacja dla full-duplex:
- `mimi` - enkoduje wejście i dekoduje wyjście główne
- `other_mimi` - "drugi kanał" dla synchronizacji
- Oba pracują równolegle dla lepszej wydajności

### Q: Co to jest warmup i dlaczego jest potrzebny?

**A:** Warmup inicjalizuje GPU:
- Pierwsze uruchomienie jest zawsze wolne (alokacja, kompilacja)
- CUDA graphs muszą być zbudowane
- Po warmup model działa stabilnie i szybko

### Q: Dlaczego frame_size = 1920 próbek?

**A:** Bo:
- Sample rate = 24000 Hz
- Frame rate = 12.5 Hz
- Frame size = 24000 / 12.5 = 1920 próbek
- To daje 80ms na ramkę (1/12.5 = 0.08s)

### Q: Co się dzieje gdy użytkownik przerywa modelowi?

**A:** Model naturalnie obsługuje przerwania:
- Tryb full-duplex - wejście jest ciągle przetwarzane
- Model "słyszy" że użytkownik mówi
- Może zareagować (przestać, odpowiedzieć, itp.)
- To jest trenowane zachowanie modelu

### Q: Jak działa CPU offload?

**A:** Gdy GPU ma mało pamięci:
```bash
python -m moshi.server --cpu-offload
```
- Część warstw LM przeniesiona na CPU
- Wolniejsze ale działa
- Wymaga pakietu `accelerate`

### Q: Czy mogę użyć własnego głosu?

**A:** Tak! Dwie opcje:
1. Nagrać WAV głosu (5-10 sekund czystego audio)
2. Wygenerować embeddingi z WAV i zapisać jako .pt

```bash
# Użyj custom WAV
--voice-prompt /path/to/my_voice.wav

# Lub zapisz embeddingi
--voice-prompt /path/to/my_voice.pt
```

### Q: Jak zmienić osobowość robota?

**A:** Przez text prompt:
```python
# Przyjazny nauczyciel
text_prompt = "You are a friendly teacher. Explain things clearly."

# Profesjonalny asystent
text_prompt = "You are a professional assistant. Be concise and formal."

# Wesoły kompan
text_prompt = "You are a cheerful companion. Be enthusiastic and fun!"
```

### Q: Czy mogę używać PersonaPlex w innych językach?

**A:** Model jest trenowany głównie na angielskim, ale:
- Może rozumieć i odpowiadać w innych językach
- Jakość zależy od języka
- Polski powinien działać częściowo
- Najlepsze wyniki dla angielskiego

### Q: Jak debugging gdy coś nie działa?

**A:** Kroki diagnostyczne:

1. **Sprawdź logi:**
```bash
# Uruchom z większą ilością logów
python -m moshi.server --ssl "$SSL_DIR" 2>&1 | tee server.log
```

2. **Przetestuj offline:**
```bash
# Prostszy do debugowania
python -m moshi.offline --input-wav test.wav --output-wav out.wav ...
```

3. **Sprawdź GPU:**
```bash
nvidia-smi  # Czy GPU jest widoczne?
python -c "import torch; print(torch.cuda.is_available())"
```

4. **Sprawdź audio:**
```bash
# Nagraj testowy plik
arecord -f S16_LE -r 24000 -c 1 test.wav -d 5
# Odtwórz
aplay test.wav
```

## Podsumowanie

PersonaPlex to zaawansowany system konwersacyjny składający się z:

**Komponenty:**
- 🎙️ Mimi - Kompresja/dekompresja audio
- 🧠 Moshi - Model językowy (generowanie)
- 📝 Tokenizer - Konwersja tekstu
- 🎛️ LMGen - Zarządzanie wysokopoziomowe

**Tryby:**
- ⚡ Real-time (server.py) - dla produkcji
- 📁 Offline (offline.py) - dla testów

**Kluczowe cechy:**
- Full-duplex (słucha i mówi jednocześnie)
- Real-time (< 200ms opóźnienie)
- Persona-controlled (kontrola przez prompty)
- Voice-controlled (różne głosy)

**Zastosowania:**
- 🤖 Roboty humanoidalne
- 📞 Systemy IVR
- 🎓 Asystenci edukacyjni
- 🏥 Healthcare

**Dla studentów PR:**
Rozumiejąc tę architekturę jesteście przygotowani do:
- Integracji z robotem Unitree G1
- Dostosowania zachowania przez prompty
- Debugowania problemów
- Optymalizacji wydajności
- Rozwoju własnych aplikacji

---

**Dodatkowe zasoby:**
- Paper: https://research.nvidia.com/labs/adlr/files/personaplex/personaplex_preprint.pdf
- Demo: https://research.nvidia.com/labs/adlr/personaplex/
- Discord: https://discord.gg/5jAXrrbwRb
- Issues: https://github.com/AI-robot-lab/nvidia-personaplex/issues

**Powodzenia w pracy z PersonaPlex i robotem Unitree G1! 🤖🎓**
