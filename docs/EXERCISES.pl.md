# Ćwiczenia Praktyczne - PersonaPlex dla Studentów

## 📘 O tym dokumencie

Ten zbiór ćwiczeń został przygotowany aby pomóc studentom Politechniki Rzeszowskiej opanować PersonaPlex krok po kroku. Ćwiczenia są podzielone według poziomu trudności i obszarów tematycznych.

**Struktura:**
- 🟢 Łatwe - podstawy, dla początkujących
- 🟡 Średnie - wymagają zrozumienia systemu
- 🔴 Trudne - zaawansowane, dla ambitnych
- 🟣 Projekt - kompleksowe zadania projektowe

---

## 📋 Wymagania wstępne

Przed rozpoczęciem upewnij się że:
- [ ] Zainstalowałeś PersonaPlex ([QUICK_START.pl.md](QUICK_START.pl.md))
- [ ] Przetestowałeś tryb offline
- [ ] Uruchomiłeś serwer i interfejs webowy
- [ ] Przeczytałeś dokumentację podstawową ([README.pl.md](../README.pl.md))

---

## 🟢 Ćwiczenia Łatwe - Podstawy

### Ćwiczenie 1.1: Pierwsze pytanie i odpowiedź

**Cel:** Naucz się używać trybu offline do generowania odpowiedzi.

**Zadanie:**
1. Nagraj własne pytanie WAV (5 sekund)
2. Uruchom PersonaPlex offline z domyślnymi ustawieniami
3. Odsłuchaj odpowiedź
4. Przeczytaj transkrypcję JSON

**Kroki:**
```bash
# 1. Nagraj pytanie
arecord -f S16_LE -r 24000 -c 1 -d 5 pytanie1.wav
# Zadaj pytanie: "What is artificial intelligence?"

# 2. Uruchom PersonaPlex
python -m moshi.offline \
  --voice-prompt "NATM1.pt" \
  --input-wav "pytanie1.wav" \
  --output-wav "odpowiedz1.wav" \
  --output-text "odpowiedz1.json" \
  --seed 42424242

# 3. Odsłuchaj
aplay odpowiedz1.wav

# 4. Przeczytaj transkrypcję
cat odpowiedz1.json | python -m json.tool
```

**Kryteria sukcesu:**
- [ ] Pytanie nagrywa się poprawnie (słychać wyraźnie)
- [ ] Model generuje odpowiedź bez błędów
- [ ] Odpowiedź ma sens i jest związana z pytaniem
- [ ] Plik JSON zawiera transkrypcję

**Pytania do refleksji:**
1. Ile czasu zajęło generowanie odpowiedzi?
2. Czy odpowiedź była naturalna?
3. Czy głos brzmiał jak prawdziwa osoba?

---

### Ćwiczenie 1.2: Porównanie głosów

**Cel:** Poznaj dostępne głosy i wybierz najlepszy dla projektu.

**Zadanie:**
Wygeneruj odpowiedzi na to samo pytanie używając 6 różnych głosów.

**Kroki:**
```bash
# Przygotuj pytanie (jedno dla wszystkich)
echo "Hello, can you tell me about robotics?" | \
  pico2wave -w pytanie2.wav && \
  sox pytanie2.wav -r 24000 pytanie2_24k.wav

# Lub nagraj własne:
arecord -f S16_LE -r 24000 -c 1 -d 5 pytanie2.wav

# Testuj różne głosy
for voice in NATM0 NATM1 NATF0 NATF1 VARM0 VARF0; do
  echo "Testing voice: $voice"
  python -m moshi.offline \
    --voice-prompt "${voice}.pt" \
    --input-wav "pytanie2.wav" \
    --output-wav "odpowiedz_${voice}.wav" \
    --output-text "odpowiedz_${voice}.json" \
    --seed 42424242
  
  echo "Playing: $voice"
  aplay "odpowiedz_${voice}.wav"
  sleep 2
done
```

**Utwórz tabelę porównawczą:**

| Głos | Płeć | Kategoria | Naturalne (1-5) | Wyraziste (1-5) | Ulubione? |
|------|------|-----------|-----------------|-----------------|-----------|
| NATM0 | M | Natural | | | |
| NATM1 | M | Natural | | | |
| NATF0 | F | Natural | | | |
| NATF1 | F | Natural | | | |
| VARM0 | M | Variety | | | |
| VARF0 | F | Variety | | | |

**Kryteria sukcesu:**
- [ ] Wygenerowałeś 6 odpowiedzi
- [ ] Odsłuchałeś wszystkie
- [ ] Wypełniłeś tabelę ocen
- [ ] Wybrałeś ulubiony głos

**Pytania do refleksji:**
1. Czy NAT (Natural) brzmiały naturalniej niż VAR (Variety)?
2. Który głos byłby najlepszy dla robota przewodnika?
3. Który dla asystenta technicznego?

---

### Ćwiczenie 1.3: Eksperymenty z seed

**Cel:** Zrozum jak działa reprodukowalność z użyciem seed.

**Zadanie:**
1. Wygeneruj 2 odpowiedzi z tym samym seed
2. Wygeneruj 2 odpowiedzi z różnymi seed
3. Porównaj wyniki

**Kroki:**
```bash
# Test 1: Ten sam seed (powinny być identyczne)
python -m moshi.offline \
  --voice-prompt "NATM1.pt" \
  --input-wav "pytanie2.wav" \
  --output-wav "seed_a1.wav" \
  --seed 12345

python -m moshi.offline \
  --voice-prompt "NATM1.pt" \
  --input-wav "pytanie2.wav" \
  --output-wav "seed_a2.wav" \
  --seed 12345

# Test 2: Różne seedy (powinny być różne)
python -m moshi.offline \
  --voice-prompt "NATM1.pt" \
  --input-wav "pytanie2.wav" \
  --output-wav "seed_b1.wav" \
  --seed 11111

python -m moshi.offline \
  --voice-prompt "NATM1.pt" \
  --input-wav "pytanie2.wav" \
  --output-wav "seed_b2.wav" \
  --seed 99999

# Porównaj pliki
ls -lh seed_*.wav
md5sum seed_a1.wav seed_a2.wav  # Powinny być identyczne
md5sum seed_b1.wav seed_b2.wav  # Powinny być różne
```

**Kryteria sukcesu:**
- [ ] seed_a1.wav i seed_a2.wav są identyczne (ten sam MD5)
- [ ] seed_b1.wav i seed_b2.wav są różne
- [ ] Rozumiesz kiedy używać seed

**Pytania do refleksji:**
1. Dlaczego reprodukowalność jest ważna w badaniach?
2. Kiedy chcesz używać seed, a kiedy nie?
3. Czy seed wpływa tylko na audio czy też na tekst?

---

## 🟡 Ćwiczenia Średnie - Customizacja

### Ćwiczenie 2.1: Tworzenie promptu osobowości

**Cel:** Naucz się projektować skuteczne text prompty dla różnych scenariuszy.

**Zadanie:**
Utwórz 3 różne osobowości robota i przetestuj każdą.

**Scenariusze:**
1. **Robot przewodnik muzealny** (przyjazny, edukacyjny)
2. **Asystent laboratoryjny** (precyzyjny, profesjonalny)
3. **Kompan konwersacyjny** (swobodny, empatyczny)

**Szablon promptu:**
```
You are [NAZWA], a [ROLA] robot at [MIEJSCE].
You [GŁÓWNA FUNKCJA].
You speak in a [TON/STYL] manner.
You have knowledge about [DZIEDZINY].
[DODATKOWE INFORMACJE].
```

**Przykład - Robot muzealny:**
```bash
cat > prompt_muzeum.txt << 'EOF'
You are ARTie, a museum guide robot at the National Museum of Technology.
You provide engaging explanations about exhibits to visitors of all ages.
You speak in an enthusiastic and educational manner.
You have knowledge about robotics, space exploration, computing history, and engineering.
You enjoy telling stories and making complex topics accessible.
You can answer questions about specific exhibits and recommend tour routes.
EOF

# Testuj z pytaniami
python -m moshi.offline \
  --voice-prompt "NATM1.pt" \
  --text-prompt "$(cat prompt_muzeum.txt)" \
  --input-wav "pytanie_muzeum.wav" \
  --output-wav "odpowiedz_muzeum.wav" \
  --seed 42424242
```

**Zadanie do wykonania:**
1. Napisz 3 prompty (muzeum, laboratorium, kompan)
2. Przygotuj 2-3 pytania dla każdego scenariusza
3. Wygeneruj odpowiedzi
4. Oceń czy odpowiedzi pasują do osobowości

**Kryteria sukcesu:**
- [ ] Każdy prompt ma jasną strukturę (rola, funkcja, styl, wiedza)
- [ ] Odpowiedzi modelu pasują do zdefiniowanej osobowości
- [ ] Model używa terminologii odpowiedniej dla kontekstu
- [ ] Styl komunikacji różni się między scenariuszami

**Pytania do refleksji:**
1. Który prompt działał najlepiej? Dlaczego?
2. Czy model trzymał się osobowości w dłuższej rozmowie?
3. Jak długi powinien być prompt aby był skuteczny?

---

### Ćwiczenie 2.2: Real-time interakcja

**Cel:** Przetestuj system w trybie real-time z interfejsem webowym.

**Zadanie:**
1. Uruchom serwer PersonaPlex
2. Przeprowadź 5-minutową rozmowę przez interfejs webowy
3. Przetestuj różne funkcje (przerywanie, pauzy)
4. Zapisz obserwacje

**Kroki:**
```bash
# 1. Uruchom serwer
SSL_DIR=$(mktemp -d)
python -m moshi.server --ssl "$SSL_DIR"

# 2. Otwórz przeglądarkę: https://localhost:8998
# 3. Skonfiguruj:
#    - Voice: NATF2
#    - Text Prompt: "You enjoy having a good conversation."
# 4. Kliknij Start i rozmawiaj
```

**Scenariusze do przetestowania:**

**A) Normalna rozmowa**
- Zadaj pytanie i poczekaj na pełną odpowiedź
- Oceń opóźnienie (ile czasu od końca pytania do początku odpowiedzi)
- Oceń naturalność

**B) Przerywanie**
- Zacznij zadawać pytanie
- Przerwij w połowie
- Zadaj nowe pytanie
- Sprawdź czy model reaguje

**C) Pauzy**
- Zadaj pytanie
- Zamilknij na 5 sekund
- Kontynuuj rozmowę
- Sprawdź czy model czeka czy mówi dalej

**D) Back-channel (potwierdzenia)**
- Podczas odpowiedzi modelu mów: "mm-hmm", "yes", "ok"
- Sprawdź czy model to rozpoznaje

**Formularz obserwacji:**

| Aspekt | Ocena (1-5) | Uwagi |
|--------|-------------|-------|
| Opóźnienie | | ms od końca pytania do początku odpowiedzi |
| Naturalność głosu | | Czy brzmi jak człowiek? |
| Reakcja na przerwania | | Czy model reaguje? |
| Obsługa pauz | | Czy czeka czy mówi dalej? |
| Back-channel | | Czy rozpoznaje potwierdzenia? |
| Jakość transkrypcji | | Czy tekst jest dokładny? |

**Kryteria sukcesu:**
- [ ] Przeprowadziłeś 5-minutową rozmowę
- [ ] Przetestowałeś wszystkie scenariusze (A-D)
- [ ] Wypełniłeś formularz obserwacji
- [ ] Rozumiesz różnicę między half-duplex a full-duplex

---

### Ćwiczenie 2.3: Własny głos (voice cloning)

**Cel:** Naucz się używać własnego głosu jako voice prompt.

**Zadanie:**
1. Nagraj wysokiej jakości próbkę swojego głosu
2. Użyj jej jako voice prompt
3. Porównaj z predefiniowanymi głosami

**Kroki:**

**1. Nagraj próbkę głosu (5-10 sekund)**
```bash
# Przygotuj tekst do nagrania (mów naturalnie, nie monotonnie)
# Przykład: "Hello, my name is [twoje imię]. I am a student at Rzeszów University of Technology. I am learning about conversational AI and robotics."

# Nagraj w cichym pomieszczeniu
arecord -f S16_LE -r 24000 -c 1 -d 10 moj_glos_raw.wav

# Odsłuchaj aby sprawdzić jakość
aplay moj_glos_raw.wav
# Jeśli za cicho/głośno - dostosuj poziom mikrofonu i nagraj ponownie
```

**2. Przetwórz nagranie (opcjonalnie)**
```bash
# Usuń początkową ciszę i normalizuj głośność (wymaga sox)
sox moj_glos_raw.wav moj_glos.wav silence 1 0.1 1% reverse silence 1 0.1 1% reverse norm
```

**3. Użyj jako voice prompt**
```bash
# Test z własnym głosem
python -m moshi.offline \
  --voice-prompt "moj_glos.wav" \
  --input-wav "pytanie_test.wav" \
  --output-wav "odpowiedz_moj_glos.wav" \
  --seed 42424242

# Porównaj z predefiniowanym głosem
python -m moshi.offline \
  --voice-prompt "NATM1.pt" \
  --input-wav "pytanie_test.wav" \
  --output-wav "odpowiedz_natm1.wav" \
  --seed 42424242

# Odsłuchaj oba
aplay odpowiedz_moj_glos.wav
aplay odpowiedz_natm1.wav
```

**Kryteria sukcesu:**
- [ ] Nagranie jest wyraźne (brak szumów, hałasu)
- [ ] Model wygenerował odpowiedź z Twoim głosem
- [ ] Głos w odpowiedzi przypomina Twoją barwę

**Pytania do refleksji:**
1. Czy model dobrze odwzorował Twój głos?
2. Jakie różnice zauważyłeś vs predefiniowane głosy?
3. Jak jakość nagrania wpływa na wynik?

---

## 🔴 Ćwiczenia Trudne - Zaawansowane

### Ćwiczenie 3.1: Integracja z ROS 2

**Cel:** Połącz PersonaPlex z systemem ROS 2 dla komunikacji z robotem.

**Wymagania:**
- ROS 2 (Humble lub nowsze)
- Python rclpy library
- Podstawowa znajomość ROS 2

**Zadanie:**
Utwórz ROS 2 node który:
1. Subskrybuje topic `/audio_in` (audio z mikrofonu robota)
2. Wysyła audio do serwera PersonaPlex
3. Odbiera odpowiedzi (audio + tekst)
4. Publikuje na topicach `/audio_out` i `/text_out`

**Szkielet kodu:**
```python
#!/usr/bin/env python3
"""
ROS 2 Node dla integracji PersonaPlex
"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from audio_common_msgs.msg import AudioData
import asyncio
import websockets
import sphn

class PersonaPlexNode(Node):
    def __init__(self):
        super().__init__('personaplex_node')
        
        # Publishers
        self.audio_out_pub = self.create_publisher(AudioData, '/audio_out', 10)
        self.text_out_pub = self.create_publisher(String, '/text_out', 10)
        
        # Subscribers
        self.audio_in_sub = self.create_subscription(
            AudioData,
            '/audio_in',
            self.audio_in_callback,
            10
        )
        
        # PersonaPlex connection
        self.ws = None
        self.opus_writer = sphn.OpusStreamWriter(24000)
        self.opus_reader = sphn.OpusStreamReader(24000)
        
        # TODO: Zaimplementuj połączenie WebSocket
        # TODO: Zaimplementuj pętle recv/send
        
    def audio_in_callback(self, msg):
        """Callback dla audio z mikrofonu robota"""
        # TODO: Enkoduj audio → Opus → wyślij przez WebSocket
        pass
    
    async def connect_to_personaplex(self):
        """Nawiąż połączenie z serwerem PersonaPlex"""
        # TODO: Zaimplementuj
        pass

def main(args=None):
    rclpy.init(args=args)
    node = PersonaPlexNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

**Zadania do wykonania:**
1. Zaimplementuj pełny node według szkieletu
2. Przetestuj z `ros2 topic pub` i `ros2 topic echo`
3. Dodaj obsługę błędów i reconnect
4. Napisz launch file
5. Udokumentuj kod

**Kryteria sukcesu:**
- [ ] Node uruchamia się bez błędów
- [ ] Audio publikowane na `/audio_in` dociera do PersonaPlex
- [ ] Odpowiedzi publikowane na `/audio_out` i `/text_out`
- [ ] Node obsługuje rozłączenia i reconnect
- [ ] Kod jest udokumentowany

**Wskazówka:** Zobacz pełny przykład w [UNITREE_G1_GUIDE.pl.md](UNITREE_G1_GUIDE.pl.md)

---

### Ćwiczenie 3.2: Monitoring i metryki

**Cel:** Zaimplementuj system monitoringu wydajności PersonaPlex.

**Zadanie:**
Napisz skrypt który mierzy i loguje:
1. Opóźnienie (latency) - czas od końca pytania do początku odpowiedzi
2. Wykorzystanie GPU (memory, compute)
3. Przepustowość (audio frames/sec)
4. Jakość audio (SNR, clarity)

**Struktura projektu:**
```
monitoring/
├── monitor.py           # Główny skrypt
├── metrics.py           # Obliczanie metryk
├── logger.py            # Zapisywanie do plików/bazy
└── dashboard.py         # Wizualizacja (opcjonalnie)
```

**Przykład monitor.py:**
```python
#!/usr/bin/env python3
"""
System monitoringu dla PersonaPlex
"""
import time
import psutil
import GPUtil
import numpy as np
from dataclasses import dataclass
from typing import List

@dataclass
class Metrics:
    timestamp: float
    latency_ms: float
    gpu_memory_mb: float
    gpu_utilization: float
    frames_per_sec: float
    audio_snr_db: float

class PersonaPlexMonitor:
    def __init__(self):
        self.metrics: List[Metrics] = []
        
    def measure_latency(self, start_time: float) -> float:
        """Zmierz opóźnienie od początku pytania"""
        return (time.time() - start_time) * 1000  # ms
    
    def measure_gpu(self) -> tuple:
        """Zmierz wykorzystanie GPU"""
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu = gpus[0]
            return gpu.memoryUsed, gpu.load * 100
        return 0.0, 0.0
    
    def measure_audio_quality(self, audio: np.ndarray) -> float:
        """Oszacuj SNR audio"""
        # TODO: Zaimplementuj obliczanie SNR
        pass
    
    def log_metrics(self, metrics: Metrics):
        """Zapisz metryki"""
        self.metrics.append(metrics)
        # TODO: Zapisz do pliku CSV lub bazy danych
    
    def generate_report(self):
        """Generuj raport statystyczny"""
        # TODO: Oblicz średnie, min, max, percentyle
        pass

# TODO: Zintegruj z PersonaPlex server.py lub offline.py
```

**Zadania:**
1. Zaimplementuj wszystkie TODO
2. Zintegruj z server.py (dodaj wywołania monitora)
3. Przeprowadź 10-minutową sesję testową
4. Wygeneruj raport z wykresami

**Metryki do zmierzenia:**
- Średnie opóźnienie
- 95-percentyl opóźnienia (najważniejszy!)
- Maksymalne zużycie GPU memory
- Średnie wykorzystanie GPU
- Liczba ramek na sekundę
- Jakość audio (SNR)

**Kryteria sukcesu:**
- [ ] Monitor działa bez wpływu na wydajność
- [ ] Wszystkie metryki są mierzone poprawnie
- [ ] Raport zawiera statystyki i wykresy
- [ ] Rozumiesz co wpływa na wydajność

---

### Ćwiczenie 3.3: Multi-modal rozszerzenie

**Cel:** Dodaj do PersonaPlex możliwość "widzenia" przez integrację z modelem vision.

**Zadanie:**
Utwórz system który:
1. Analizuje obraz z kamery robota (YOLO/ResNet)
2. Generuje opis wykrytych obiektów
3. Wzbogaca text prompt o informacje wizualne
4. PersonaPlex odpowiada biorąc pod uwagę co "widzi"

**Architektura:**
```
Camera → [Vision Model] → Objects List → [Prompt Enrichment] → PersonaPlex
                                                                      ↓
User Audio ────────────────────────────────────────────────────────→ ↓
                                                                      ↓
                                                  Response Audio ←────┘
```

**Szkielet kodu:**
```python
#!/usr/bin/env python3
"""
Multi-modal PersonaPlex - vision + audio
"""
import cv2
import torch
from ultralytics import YOLO  # YOLOv8
import numpy as np

class VisionModule:
    def __init__(self):
        # Załaduj model YOLO
        self.model = YOLO('yolov8n.pt')
        
    def detect_objects(self, image: np.ndarray) -> list:
        """Wykryj obiekty na obrazie"""
        results = self.model(image)
        objects = []
        for r in results:
            for box in r.boxes:
                obj = {
                    'name': self.model.names[int(box.cls)],
                    'confidence': float(box.conf),
                    'bbox': box.xyxy[0].tolist()
                }
                objects.append(obj)
        return objects
    
    def generate_description(self, objects: list) -> str:
        """Generuj opis tekstowy obiektów"""
        if not objects:
            return "I don't see any specific objects."
        
        # Grupuj obiekty
        obj_counts = {}
        for obj in objects:
            name = obj['name']
            obj_counts[name] = obj_counts.get(name, 0) + 1
        
        # Generuj opis
        descriptions = []
        for name, count in obj_counts.items():
            if count == 1:
                descriptions.append(f"a {name}")
            else:
                descriptions.append(f"{count} {name}s")
        
        return "I can see " + ", ".join(descriptions) + "."

class MultiModalPersonaPlex:
    def __init__(self):
        self.vision = VisionModule()
        # TODO: Inicjalizuj PersonaPlex
        
    def process_with_vision(self, image, audio_input):
        """Przetwórz audio z kontekstem wizualnym"""
        # 1. Wykryj obiekty
        objects = self.vision.detect_objects(image)
        vision_desc = self.vision.generate_description(objects)
        
        # 2. Wzbogać prompt
        enriched_prompt = f"""
        You are a robot assistant with vision capabilities.
        {vision_desc}
        Answer questions about what you see or help with tasks.
        """
        
        # 3. Ustaw prompt i przetwórz audio
        # TODO: Zaimplementuj integrację z PersonaPlex
        pass

# TODO: Zaimplementuj pełny pipeline
```

**Zadania:**
1. Zaimplementuj pełny pipeline
2. Przetestuj z różnymi obrazami i pytaniami
3. Oceń czy odpowiedzi wykorzystują informacje wizualne
4. Zmierz overhead czasowy (dodatkowe opóźnienie)

**Scenariusze testowe:**
- "What do you see?" (pytanie o opis sceny)
- "How many people are there?" (pytanie o liczenie)
- "What color is the car?" (pytanie o atrybuty)
- "Can you help me find my keys?" (pytanie o obiekt)

**Kryteria sukcesu:**
- [ ] Vision model wykrywa obiekty poprawnie
- [ ] Opis jest generowany i dodawany do promptu
- [ ] PersonaPlex odpowiada biorąc pod uwagę kontekst wizualny
- [ ] Dodatkowe opóźnienie < 200ms
- [ ] System działa stabilnie

---

## 🟣 Projekty Końcowe

### Projekt 1: Robot przewodnik muzealny

**Opis:** Stwórz kompleksowy system robota przewodnika dla muzeum technologii.

**Wymagania funkcjonalne:**
1. **Persona:** Przyjazny przewodnik o imieniu "TECHie"
2. **Wiedza:** Informacje o 5-10 eksponatach
3. **Funkcje:**
   - Odpowiadanie na pytania o eksponaty
   - Rekomendowanie tras zwiedzania
   - Opowiadanie ciekawostek historycznych
   - Rozpoznawanie gdzie stoi użytkownik (przez vision)

**Wymagania techniczne:**
- PersonaPlex (audio)
- YOLO (wykrywanie lokalizacji po eksponatach w tle)
- ROS 2 (integracja z robotem)
- Baza wiedzy (JSON z informacjami o eksponatach)

**Struktura:**
```
museum_guide/
├── config/
│   ├── exhibits.json      # Baza eksponatów
│   └── prompts.txt        # Prompty dla różnych sytuacji
├── src/
│   ├── vision.py          # Moduł rozpoznawania lokalizacji
│   ├── knowledge.py       # Dostęp do bazy wiedzy
│   ├── personaplex_node.py # ROS 2 node
│   └── main.py            # Główny orchestrator
├── launch/
│   └── museum_guide.launch.py
└── README.md
```

**Milestone'y:**
1. [ ] Podstawowa konfiguracja PersonaPlex z odpowiednim głosem i promptem
2. [ ] Baza wiedzy o eksponatach (minimum 5)
3. [ ] System rozpoznawania lokalizacji (vision)
4. [ ] Integracja ROS 2
5. [ ] Testowanie z prawdziwymi użytkownikami
6. [ ] Dokumentacja i demo video

**Deadline:** 4 tygodnie

---

### Projekt 2: Asystent laboratoryjny

**Opis:** Robot asystujący w laboratorium - pomaga z procedurami, odpowiada na pytania techniczne.

**Wymagania funkcjonalne:**
1. **Persona:** Profesjonalny asystent laboratoryjny
2. **Wiedza:** Procedury bezpieczeństwa, obsługa sprzętu
3. **Funkcje:**
   - Prowadzenie przez procedury krok po kroku
   - Odpowiadanie na pytania o sprzęt
   - Przypominanie o zasadach bezpieczeństwa
   - Logowanie wykonanych procedur

**Wymagania techniczne:**
- PersonaPlex
- System zarządzania procedurami (state machine)
- Logging i reporting
- Emergency stop (gdy wykryje niebezpieczną sytuację)

**Milestone'y:**
1. [ ] Definicja 3-5 procedur laboratoryjnych
2. [ ] State machine dla kroków procedury
3. [ ] Integracja z PersonaPlex
4. [ ] System logowania i raportowania
5. [ ] Mechanizm emergency stop
6. [ ] Testy w rzeczywistym środowisku

**Deadline:** 4 tygodnie

---

### Projekt 3: Kompan edukacyjny dla dzieci

**Opis:** Robot pomagający dzieciom w nauce - wyjaśnia pojęcia, zadaje pytania, wspiera rozwój.

**Wymagania funkcjonalne:**
1. **Persona:** Przyjazny, cierpliwy nauczyciel
2. **Wiedza:** Matematyka, nauki przyrodnicze (poziom szkoły podstawowej)
3. **Funkcje:**
   - Wyjaśnianie pojęć prostym językiem
   - Zadawanie pytań sprawdzających
   - Dostosowanie poziomu do dziecka
   - Pozytywne wzmacnianie i motywowanie

**Wymagania techniczne:**
- PersonaPlex z odpowiednim głosem i tonem
- System dostosowania poziomu trudności
- Tracking postępów (które tematy opanowane)
- Interfejs gamification (punkty, nagrody)

**Milestone'y:**
1. [ ] Design persona odpowiedniej dla dzieci
2. [ ] Przygotowanie materiałów edukacyjnych (3-5 tematów)
3. [ ] System poziomów trudności
4. [ ] Mechanizm zadawania pytań i oceny odpowiedzi
5. [ ] Gamification (punkty, progress)
6. [ ] Testy z dziećmi (min. 5 sesji)

**Deadline:** 5 tygodni

---

## 📊 Ocena i kryteria

### Ćwiczenia łatwe (🟢)
- **Wykonanie:** Czy wykonałeś wszystkie kroki?
- **Zrozumienie:** Czy potrafisz wyjaśnić co zrobiłeś?
- **Dokumentacja:** Czy wypełniłeś formularze i odpowiedziałeś na pytania?

### Ćwiczenia średnie (🟡)
- Wszystko z łatwych +
- **Kreatywność:** Czy dodałeś własne pomysły?
- **Jakość:** Czy rozwiązanie jest dopracowane?
- **Analiza:** Czy przeanalizowałeś wyniki?

### Ćwiczenia trudne (🔴)
- Wszystko z średnich +
- **Kod:** Czy kod działa stabilnie i jest czytelny?
- **Testy:** Czy przetestowałeś edge cases?
- **Dokumentacja:** Czy napisałeś README i komentarze?

### Projekty końcowe (🟣)
- Wszystko z trudnych +
- **Kompletność:** Czy zrealizowałeś wszystkie wymagania?
- **Innowacyjność:** Czy dodałeś własne unikalne funkcje?
- **Praktyczność:** Czy system nadaje się do użycia?
- **Prezentacja:** Demo video + dokumentacja

---

## 🆘 Wsparcie

Jeśli utknąłeś:
1. Sprawdź [FAQ.pl.md](FAQ.pl.md)
2. Zapytaj na laboratoriach
3. Discord: https://discord.gg/5jAXrrbwRb
4. GitHub Issues: https://github.com/AI-robot-lab/nvidia-personaplex/issues

**Powodzenia! 🚀📚**

*Ćwiczenia przygotowane dla studentów Politechniki Rzeszowskiej - Luty 2026*
