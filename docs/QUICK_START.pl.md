# Szybki Start - PersonaPlex dla Studentów

## 🎯 Cel tego przewodnika

Ten dokument przeprowadzi Cię przez **kompletny proces** uruchomienia PersonaPlex od zera do pierwszej działającej rozmowy. Każdy krok jest wyjaśniony szczegółowo.

---

## ⏱️ Czas realizacji: ~45 minut

- Instalacja: 20 minut
- Pierwszy test offline: 10 minut  
- Uruchomienie serwera: 10 minut
- Eksperymentowanie: 5 minut

---

## 📋 Wymagania wstępne

### Sprzęt

**Minimalne:**
- CPU: 4 rdzenie
- RAM: 8GB
- GPU: NVIDIA z 8GB VRAM (np. RTX 3060) **LUB** CPU z 16GB RAM
- Dysk: 20GB wolnej przestrzeni

**Zalecane:**
- CPU: 8+ rdzeni
- RAM: 16GB
- GPU: NVIDIA RTX 3090, A100, lub nowsze
- Dysk: 30GB wolnej przestrzeni

### Oprogramowanie

- **System operacyjny**: Ubuntu 20.04+ (zalecane), inne Linux, macOS
- **Python**: 3.9 lub nowszy
- **Sterowniki NVIDIA**: Najnowsze (dla GPU)
- **CUDA**: 11.8 lub nowsze (dla GPU)

---

## 🚀 Krok po kroku - Instalacja

### Krok 1: Sprawdź środowisko Python

```bash
# Sprawdź wersję Pythona (powinna być >= 3.9)
python3 --version

# Sprawdź czy pip jest zainstalowany
python3 -m pip --version
```

**Jeśli nie masz Pythona 3.9+:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.9 python3.9-venv python3-pip

# macOS (z Homebrew)
brew install python@3.9
```

### Krok 2: Sprawdź GPU (opcjonalnie)

```bash
# Sprawdź czy GPU jest widoczne
nvidia-smi

# Sprawdź czy PyTorch widzi GPU
python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

**Jeśli nvidia-smi nie działa:**
- Zainstaluj sterowniki NVIDIA ze strony producenta
- Możesz też pracować bez GPU (wolniej, ale możliwe)

### Krok 3: Sklonuj repozytorium

```bash
# Przejdź do katalogu gdzie chcesz mieć projekt
cd ~

# Sklonuj repozytorium
git clone https://github.com/AI-robot-lab/nvidia-personaplex.git
cd nvidia-personaplex

# Sprawdź czy sklonowało się poprawnie
ls -la
# Powinieneś zobaczyć: README.md, moshi/, client/, docs/, etc.
```

### Krok 4: Zainstaluj zależności systemowe

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install libopus-dev build-essential

# Fedora/RHEL
sudo dnf install opus-devel gcc gcc-c++

# macOS
brew install opus
```

**Co to jest Opus?**
Opus to kodek audio używany do kompresji strumieni audio w czasie rzeczywistym. Jest niezbędny dla komunikacji przez WebSocket.

### Krok 5: Utwórz środowisko wirtualne

```bash
# Utwórz środowisko wirtualne Python
python3 -m venv personaplex_env

# Aktywuj środowisko
source personaplex_env/bin/activate  # Linux/macOS
# LUB
# personaplex_env\Scripts\activate  # Windows

# Upewnij się że jesteś w środowisku (powinieneś zobaczyć (personaplex_env) przed znakiem zachęty)
which python
# Powinno wyświetlić ścieżkę do personaplex_env/bin/python
```

**Dlaczego środowisko wirtualne?**
- Izoluje zależności projektu od reszty systemu
- Unika konfliktów wersji pakietów
- Łatwe do usunięcia gdy już nie potrzebujesz

### Krok 6: Zainstaluj PersonaPlex

```bash
# Upewnij się że jesteś w katalogu nvidia-personaplex z aktywnym środowiskiem
cd ~/nvidia-personaplex
source personaplex_env/bin/activate

# Zainstaluj pakiet
pip install moshi/.

# To zajmie kilka minut - pobiera i instaluje wszystkie zależności
```

**Dla GPU Blackwell (RTX 50xx):**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130
```

### Krok 7: Konfiguracja Huggingface

PersonaPlex pobiera wagi modelu z platformy Huggingface. Potrzebujesz tokena dostępu.

**7.1. Utwórz konto na Huggingface**
- Przejdź do https://huggingface.co/join
- Zarejestruj się (darmowe)

**7.2. Zaakceptuj licencję modelu**
- Przejdź do https://huggingface.co/nvidia/personaplex-7b-v1
- Kliknij "Agree and access repository"

**7.3. Wygeneruj token dostępu**
- Przejdź do https://huggingface.co/settings/tokens
- Kliknij "New token"
- Nadaj nazwę (np. "personaplex")
- Typ: "Read"
- Skopiuj token (wyświetli się tylko raz!)

**7.4. Ustaw token w środowisku**
```bash
# Zastąp YOUR_TOKEN_HERE swoim tokenem
export HF_TOKEN=YOUR_TOKEN_HERE

# Aby token był dostępny w przyszłości, dodaj go do ~/.bashrc
echo 'export HF_TOKEN=YOUR_TOKEN_HERE' >> ~/.bashrc
```

---

## 🧪 Pierwszy test - Tryb offline

Tryb offline to najprostszy sposób na przetestowanie czy wszystko działa.

### Krok 1: Przygotuj plik audio z pytaniem

**Opcja A: Nagraj własne pytanie**
```bash
# Nagraj 5 sekund audio (mikrofon → plik WAV)
arecord -f S16_LE -r 24000 -c 1 -d 5 test_pytanie.wav

# Odtwórz aby sprawdzić czy nagrało się poprawnie
aplay test_pytanie.wav
```

**Opcja B: Użyj przykładowego pliku**
```bash
# Repozytorium zawiera przykładowe pliki
ls assets/test/
# Zobaczysz: input_assistant.wav, input_service.wav
```

### Krok 2: Uruchom tryb offline

```bash
# Aktywuj środowisko jeśli jeszcze nie jest aktywne
source personaplex_env/bin/activate

# Uruchom tryb offline z przykładowym plikiem
python -m moshi.offline \
  --voice-prompt "NATM1.pt" \
  --input-wav "assets/test/input_assistant.wav" \
  --output-wav "odpowiedz.wav" \
  --output-text "odpowiedz.json" \
  --seed 42424242

# To zajmie chwilę przy pierwszym uruchomieniu (pobieranie modelu)
```

**Co się dzieje:**
1. Model pobiera się z Huggingface (jednorazowo, ~3GB)
2. Model ładuje się do pamięci GPU/CPU
3. Przeprowadza się warmup (inicjalizacja)
4. Przetwarza plik wejściowy ramka po ramce
5. Generuje odpowiedź (audio + tekst)
6. Zapisuje wyniki do plików

**Oczekiwany czas:**
- Pierwsze uruchomienie: 5-15 minut (pobieranie modelu)
- Kolejne uruchomienia: 1-3 minuty

### Krok 3: Sprawdź wyniki

```bash
# Odtwórz wygenerowaną odpowiedź
aplay odpowiedz.wav

# Przejrzyj transkrypcję tekstową
cat odpowiedz.json | python -m json.tool
```

**Plik JSON zawiera:**
- Transkrypcję odpowiedzi modelu
- Metadata (tokeny, timestampy)

### Krok 4: Eksperymentuj z parametrami

```bash
# Spróbuj innego głosu (kobiecy, naturalny)
python -m moshi.offline \
  --voice-prompt "NATF2.pt" \
  --input-wav "assets/test/input_assistant.wav" \
  --output-wav "odpowiedz_f2.wav" \
  --output-text "odpowiedz_f2.json" \
  --seed 42424242

# Dodaj własny prompt tekstowy
python -m moshi.offline \
  --voice-prompt "NATM1.pt" \
  --text-prompt "You are a helpful robot assistant in a museum." \
  --input-wav "test_pytanie.wav" \
  --output-wav "odpowiedz_robot.wav" \
  --output-text "odpowiedz_robot.json" \
  --seed 42424242
```

---

## 🌐 Uruchomienie serwera WebSocket

Serwer umożliwia interakcję w czasie rzeczywistym przez interfejs webowy.

### Krok 1: Uruchom serwer

```bash
# Aktywuj środowisko
source personaplex_env/bin/activate

# Utwórz tymczasowy katalog dla certyfikatów SSL
SSL_DIR=$(mktemp -d)

# Uruchom serwer
python -m moshi.server --ssl "$SSL_DIR"

# Serwer uruchomi się i wyświetli informacje:
# - Adres IP i port (np. https://192.168.1.100:8998)
# - Miejsce gdzie są certyfikaty SSL
```

**Jeśli GPU ma mało pamięci:**
```bash
# Użyj CPU offload (niektóre warstwy na CPU)
python -m moshi.server --ssl "$SSL_DIR" --cpu-offload
```

### Krok 2: Otwórz interfejs webowy

```bash
# Serwer lokalny (na tym samym komputerze)
# Otwórz przeglądarkę i przejdź do:
https://localhost:8998

# Zdalny serwer (z innego komputera)
# Użyj adresu IP wyświetlonego przez serwer:
# https://192.168.1.100:8998
```

**Przeglądarka wyświetli ostrzeżenie o certyfikacie:**
- To normalne (self-signed certificate)
- Kliknij "Advanced" / "Zaawansowane"
- Kliknij "Proceed anyway" / "Kontynuuj mimo to"

### Krok 3: Zezwól na dostęp do mikrofonu

- Przeglądarka zapyta o dostęp do mikrofonu
- Kliknij "Allow" / "Zezwól"
- Jeśli nie widzisz zapytania - sprawdź ustawienia przeglądarki

### Krok 4: Skonfiguruj rozmowę

W interfejsie webowym:
1. **Voice**: Wybierz głos (np. NATM1, NATF2)
2. **Text Prompt**: Wpisz instrukcję dla modelu (np. "You are a friendly teacher.")
3. **Kliknij "Start"**

### Krok 5: Rozmawiaj!

- Mów do mikrofonu
- Model będzie odpowiadać w czasie rzeczywistym
- Możesz przerywać modelowi (jak w prawdziwej rozmowie)
- Transkrypcja pojawi się na ekranie

### Krok 6: Zatrzymaj serwer

```bash
# W terminalu gdzie uruchomiłeś serwer:
# Naciśnij Ctrl+C aby zatrzymać
```

---

## 🎓 Ćwiczenia praktyczne

### Ćwiczenie 1: Własne pytanie (łatwe)

**Cel:** Naucz się nagrywać własne pytania i generować odpowiedzi.

**Zadanie:**
1. Nagraj pytanie WAV (5-10 sekund)
2. Uruchom tryb offline ze swoim plikiem
3. Odsłuchaj odpowiedź

**Kryteria sukcesu:**
- ✅ Plik WAV nagrywa się poprawnie
- ✅ Model generuje odpowiedź audio
- ✅ Odpowiedź jest sensowna

### Ćwiczenie 2: Różne głosy (łatwe)

**Cel:** Poznaj dostępne głosy i wybierz najlepszy dla projektu.

**Zadanie:**
1. Przetestuj co najmniej 4 różne głosy (NATM0-3, NATF0-3)
2. Użyj tego samego pytania dla wszystkich
3. Porównaj wyniki

**Kryteria sukcesu:**
- ✅ Wygenerowałeś 4 odpowiedzi
- ✅ Zauważyłeś różnice w głosach
- ✅ Wybrałeś ulubiony głos

### Ćwiczenie 3: Własna osobowość (średnie)

**Cel:** Naucz się tworzyć custom prompty tekstowe.

**Zadanie:**
1. Zaprojektuj osobowość dla robota (np. "nauczyciel fizyki")
2. Napisz text prompt (3-5 zdań)
3. Przetestuj z 3 różnymi pytaniami

**Przykład promptu:**
```
You are a physics teacher robot at a university.
You explain complex concepts in simple terms.
You use analogies and examples from everyday life.
You are patient and encouraging.
```

**Kryteria sukcesu:**
- ✅ Prompt ma sensowną strukturę
- ✅ Odpowiedzi modelu pasują do osobowości
- ✅ Przetestowałeś z różnymi pytaniami

### Ćwiczenie 4: Real-time rozmowa (średnie)

**Cel:** Przetestuj system w trybie real-time.

**Zadanie:**
1. Uruchom serwer WebSocket
2. Przeprowadź 5-minutową rozmowę
3. Wypróbuj przerywanie modelowi
4. Zapisz obserwacje

**Kryteria sukcesu:**
- ✅ Połączenie działa stabilnie
- ✅ Opóźnienie jest akceptowalne (< 1s)
- ✅ Model reaguje na przerwania
- ✅ Rozumiesz jak działa full-duplex

---

## ❓ Rozwiązywanie problemów

### Problem: "CUDA out of memory"

**Objawy:** Błąd podczas ładowania modelu lub podczas przetwarzania.

**Rozwiązanie 1:** Użyj CPU offload
```bash
python -m moshi.server --ssl "$SSL_DIR" --cpu-offload
```

**Rozwiązanie 2:** Użyj tylko CPU (wolniejsze)
```bash
# Zainstaluj PyTorch CPU-only
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Uruchom normalnie
python -m moshi.offline --input-wav "test.wav" --output-wav "out.wav"
```

### Problem: "Permission denied" dla mikrofonu

**Objawy:** Przeglądarka nie pyta o dostęp lub dostęp jest zablokowany.

**Rozwiązanie:**
1. Sprawdź ustawienia przeglądarki: chrome://settings/content/microphone
2. Usuń blokadę dla localhost:8998
3. Odśwież stronę
4. Spróbuj innej przeglądarki (Chrome/Firefox zalecane)

### Problem: Wolne generowanie

**Objawy:** Model generuje odpowiedzi bardzo wolno (> 5 sekund).

**Przyczyny i rozwiązania:**
1. **Brak GPU:** Zainstaluj sterowniki NVIDIA
2. **Słabe GPU:** Użyj mniejszego batch size lub CPU offload
3. **Brak warmup:** Poczekaj aż warmup się zakończy
4. **Przeciążenie systemu:** Zamknij inne aplikacje

### Problem: Model nie pobiera się

**Objawy:** Błąd podczas pobierania z Huggingface.

**Rozwiązanie:**
1. Sprawdź token: `echo $HF_TOKEN`
2. Zaakceptuj licencję na https://huggingface.co/nvidia/personaplex-7b-v1
3. Sprawdź połączenie internetowe
4. Spróbuj ponownie (może być timeout)

### Problem: Jakość audio jest słaba

**Objawy:** Audio brzmi zniekształcone lub przerywa się.

**Rozwiązanie:**
1. Sprawdź sample rate mikrofonu: `arecord -l`
2. Użyj lepszego mikrofonu (USB zalecane)
3. Zmniejsz hałas w pomieszczeniu
4. Sprawdź poziom głośności: `alsamixer`

---

## 📚 Kolejne kroki

Po ukończeniu tego przewodnika powinieneś być gotowy do:

1. **Przeczytania szczegółowej dokumentacji:**
   - [README.pl.md](../README.pl.md) - pełna dokumentacja
   - [ARCHITECTURE.pl.md](ARCHITECTURE.pl.md) - jak działa system
   - [UNITREE_G1_GUIDE.pl.md](UNITREE_G1_GUIDE.pl.md) - integracja z robotem

2. **Eksperymentowania z kodem:**
   - Modyfikacja parametrów sampling
   - Tworzenie własnych promptów
   - Dodawanie nowych funkcjonalności

3. **Integracji z robotem:**
   - Połączenie z systemem kontroli robota
   - Implementacja ROS 2 bridge
   - Testowanie w scenariuszach rzeczywistych

---

## 🆘 Pomoc i wsparcie

### Pytania techniczne
- **Discord:** https://discord.gg/5jAXrrbwRb
- **GitHub Issues:** https://github.com/AI-robot-lab/nvidia-personaplex/issues

### Dokumentacja
- **Paper:** https://research.nvidia.com/labs/adlr/files/personaplex/personaplex_preprint.pdf
- **Demo:** https://research.nvidia.com/labs/adlr/personaplex/
- **Huggingface:** https://huggingface.co/nvidia/personaplex-7b-v1

### Dla wykładowców
Jeśli jesteś wykładowcą potrzebującym dodatkowych materiałów lub masz sugestie, otwórz Issue na GitHubie.

---

**Powodzenia! 🚀🤖**

*Przewodnik przygotowany dla studentów Politechniki Rzeszowskiej - Luty 2026*
