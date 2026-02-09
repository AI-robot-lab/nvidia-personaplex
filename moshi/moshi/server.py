# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: MIT
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.


# Copyright (c) Kyutai, all rights reserved.
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import argparse
import asyncio
from dataclasses import dataclass
import random
import os
from pathlib import Path
import tarfile
import time
import secrets
import sys
from typing import Literal, Optional

import aiohttp
from aiohttp import web
from huggingface_hub import hf_hub_download
import numpy as np
import sentencepiece
import sphn
import torch
import random

from .client_utils import make_log, colorize
from .models import loaders, MimiModel, LMModel, LMGen
from .utils.connection import create_ssl_context, get_lan_ip
from .utils.logging import setup_logger, ColorizedLog


logger = setup_logger(__name__)
DeviceString = Literal["cuda"] | Literal["cpu"] #| Literal["mps"]

def torch_auto_device(requested: Optional[DeviceString] = None) -> torch.device:
    """
    Automatyczny wybór urządzenia obliczeniowego (GPU/CPU).
    
    Funkcja ta decyduje gdzie będą wykonywane obliczenia modelu:
    - Najpierw sprawdza czy użytkownik wymaga konkretnego urządzenia (requested)
    - Jeśli nie, preferuje GPU CUDA (znacznie szybsze dla modeli AI)
    - W ostateczności wybiera CPU (wolniejsze, ale zawsze dostępne)
    
    Dla robota: Jeśli robot ma GPU NVIDIA - użyje go automatycznie.
    Jeśli nie ma - użyje CPU (może być za wolne dla real-time).
    
    Args:
        requested: Opcjonalne wymuszenie urządzenia ("cuda" lub "cpu")
    
    Returns:
        torch.device: Obiekt reprezentujący wybrane urządzenie
    """
    if requested is not None:
        return torch.device(requested)
    if torch.cuda.is_available():
        return torch.device("cuda")
    #elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
    #    return torch.device("mps")
    return torch.device("cpu")


def seed_all(seed):
    """
    Ustawia ziarno (seed) dla wszystkich generatorów liczb losowych.
    
    Dlaczego to jest ważne?
    - Modele AI używają losowości podczas generowania odpowiedzi
    - To samo ziarno = te same wyniki (reprodukowalność eksperymentów)
    - Przydatne do testowania i debugowania
    
    Funkcja ustawia seed dla:
    1. torch (biblioteka PyTorch)
    2. torch.cuda (obliczenia na GPU)
    3. random (standardowa biblioteka Python)
    4. numpy (biblioteka do obliczeń numerycznych)
    
    Args:
        seed: Liczba całkowita jako ziarno (np. 42424242)
    """
    # Ustaw seed dla PyTorch (CPU)
    torch.manual_seed(seed)
    
    # Ustaw seed dla PyTorch (GPU) - tylko jeśli GPU jest dostępne
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)  # dla konfiguracji z wieloma GPU
    
    # Ustaw seed dla standardowego generatora Python
    random.seed(seed)
    
    # Ustaw seed dla NumPy
    np.random.seed(seed)
    
    # Wyłącz deterministyczne zachowanie cuDNN (dla lepszej wydajności)
    # W trybie produkcyjnym można to włączyć dla pełnej reprodukowalności
    torch.backends.cudnn.deterministic = False
    torch.backends.cudnn.benchmark = False


def wrap_with_system_tags(text: str) -> str:
    """
    Opakowuje tekst promptu w znaczniki systemowe wymagane przez model.
    
    Model PersonaPlex oczekuje promptów w specjalnym formacie:
    "<system> treść promptu <system>"
    
    Znaczniki <system> informują model, że to jest instrukcja systemowa,
    a nie część rozmowy użytkownika.
    
    Przykład:
        Input:  "You are a friendly robot assistant."
        Output: "<system> You are a friendly robot assistant. <system>"
    
    Jeśli tekst już ma znaczniki - nie dodaje ich ponownie.
    
    Args:
        text: Tekst promptu do opakowania
    
    Returns:
        str: Tekst z dodanymi znacznikami systemowymi
    """
    cleaned = text.strip()
    
    # Sprawdź czy prompt już ma znaczniki - jeśli tak, zwróć bez zmian
    if cleaned.startswith("<system>") and cleaned.endswith("<system>"):
        return cleaned
    
    # Dodaj znaczniki systemowe
    return f"<system> {cleaned} <system>"


@dataclass
class ServerState:
    """
    Stan serwera PersonaPlex - przechowuje wszystkie komponenty potrzebne do działania.
    
    Ta klasa zarządza:
    - Modelami audio (Mimi - kompresja/dekompresja)
    - Modelem językowym (LM - generowanie odpowiedzi)
    - Tokenizerem tekstu (konwersja słowa ↔ liczby)
    - Blokadą (lock) dla bezpiecznej obsługi wielu klientów
    
    Dlaczego dwa modele Mimi (mimi i other_mimi)?
    - Jeden enkoduje audio użytkownika (wejście)
    - Drugi dekoduje audio robota/asystenta (wyjście)
    - Oba działają jednocześnie (full-duplex)
    
    Zastosowanie w robotyce:
    - Jeden ServerState obsługuje jednego klienta (np. jednego robota)
    - Lock zapewnia że w danym momencie tylko jedna rozmowa jest aktywna
    """
    mimi: MimiModel                                    # Model kompresji audio - dla wejścia
    other_mimi: MimiModel                              # Model kompresji audio - dla wyjścia
    text_tokenizer: sentencepiece.SentencePieceProcessor  # Tokenizer tekstu
    lm_gen: LMGen                                      # Generator modelu językowego
    lock: asyncio.Lock                                 # Blokada dla synchronizacji

    def __init__(self, mimi: MimiModel, other_mimi: MimiModel, text_tokenizer: sentencepiece.SentencePieceProcessor,
                 lm: LMModel, device: str | torch.device, voice_prompt_dir: str | None = None,
                 save_voice_prompt_embeddings: bool = False):
        """
        Inicjalizacja stanu serwera - konfiguracja wszystkich komponentów.
        
        Krok po kroku co się dzieje:
        1. Zapisuje referencje do modeli (Mimi, LM, tokenizer)
        2. Oblicza frame_size - rozmiar pojedynczego fragmentu audio
        3. Tworzy LMGen - generator wysokiego poziomu zarządzający modelem
        4. Włącza tryb streaming dla wszystkich modeli (dla real-time)
        
        Args:
            mimi: Model Mimi do enkodowania audio wejściowego
            other_mimi: Model Mimi do dekodowania audio wyjściowego  
            text_tokenizer: Tokenizer do konwersji tekst ↔ tokeny
            lm: Model językowy (LM) - serce systemu
            device: Urządzenie obliczeniowe (GPU/CPU)
            voice_prompt_dir: Katalog z plikami głosów (embeddings)
            save_voice_prompt_embeddings: Czy zapisywać embeddings głosów
        """
        # Zapisz komponenty jako atrybuty klasy
        self.mimi = mimi
        self.other_mimi = other_mimi
        self.text_tokenizer = text_tokenizer
        self.device = device
        self.voice_prompt_dir = voice_prompt_dir
        
        # Oblicz rozmiar ramki audio w próbkach
        # sample_rate = ile próbek na sekundę (np. 24000 Hz)
        # frame_rate = ile ramek na sekundę (np. 12.5 Hz)
        # frame_size = sample_rate / frame_rate = ile próbek w jednej ramce
        self.frame_size = int(self.mimi.sample_rate / self.mimi.frame_rate)
        
        # Utwórz generator modelu - zarządza generowaniem odpowiedzi
        self.lm_gen = LMGen(lm,
                            # Ile ramek ciszy po promptach (0.5s * frame_rate)
                            audio_silence_frame_cnt=int(0.5 * self.mimi.frame_rate),
                            sample_rate=self.mimi.sample_rate,
                            device=device,
                            frame_rate=self.mimi.frame_rate,
                            save_voice_prompt_embeddings=save_voice_prompt_embeddings,
        )
        
        # Utwórz blokadę asyncio - zapewnia że tylko jedna rozmowa na raz
        self.lock = asyncio.Lock()
        
        # Włącz tryb streaming dla wszystkich modeli
        # Tryb streaming = przetwarzanie w małych fragmentach (real-time)
        # Argument 1 = batch size (ile próbek jednocześnie)
        self.mimi.streaming_forever(1)
        self.other_mimi.streaming_forever(1)
        self.lm_gen.streaming_forever(1)
    
    def warmup(self):
        """
        Rozgrzewka modelu - przygotowanie do pracy w czasie rzeczywistym.
        
        Dlaczego to jest potrzebne?
        - Pierwsze uruchomienie GPU jest zawsze wolniejsze (inicjalizacja)
        - CUDA graphs i inne optymalizacje wymagają "rozgrzania"
        - Po warmup'ie model działa znacznie szybciej i bardziej przewidywalnie
        
        Co się dzieje w tej funkcji:
        1. Tworzy sztucznie puste dane audio (zera)
        2. Przepuszcza je przez cały pipeline modelu
        3. Powtarza 4 razy aby wszystko było zainicjalizowane
        4. Synchronizuje GPU (czeka na zakończenie obliczeń)
        
        Dla robota: Wywołaj tę funkcję raz po starcie, zanim zaczniesz
        prawdziwe rozmowy. Dzięki temu pierwsze odpowiedzi nie będą wolniejsze.
        """
        # Powtórz proces 4 razy dla pełnej inicjalizacji
        for _ in range(4):
            # Utwórz fragment audio wypełniony zerami (cisza)
            # Kształt: [batch=1, channels=1, samples=frame_size]
            chunk = torch.zeros(1, 1, self.frame_size, dtype=torch.float32, device=self.device)
            
            # KROK 1: Enkoduj audio do codes (kompresja)
            codes = self.mimi.encode(chunk)
            
            # Enkoduj również przez drugi Mimi (dla symetrii)
            _ = self.other_mimi.encode(chunk)
            
            # KROK 2: Przepuść każdą ramkę przez generator LM
            for c in range(codes.shape[-1]):
                # Wygeneruj tokeny dla jednej ramki
                tokens = self.lm_gen.step(codes[:, :, c: c + 1])
                
                # Jeśli generator jeszcze nie jest gotowy - pomiń
                if tokens is None:
                    continue
                
                # KROK 3: Dekoduj wygenerowane tokeny audio do PCM
                # tokens[:, 1:9] = kanały audio (8 codebooków)
                _ = self.mimi.decode(tokens[:, 1:9])
                _ = self.other_mimi.decode(tokens[:, 1:9])
        
        # Poczekaj aż GPU zakończy wszystkie operacje
        if self.device.type == 'cuda':
            torch.cuda.synchronize()


    async def handle_chat(self, request):
        """
        Główna funkcja obsługująca połączenie WebSocket z klientem.
        
        To jest serce serwera - zarządza całą sesją rozmowy:
        1. Nawiązuje połączenie WebSocket
        2. Ładuje konfigurację (głos, prompt tekstowy)
        3. Przetwarza prompty systemowe (voice + text)
        4. Uruchamia pętle komunikacji:
           - recv_loop: Odbiera audio od użytkownika
           - opus_loop: Przetwarza audio i generuje odpowiedzi
           - send_loop: Wysyła wygenerowane audio do użytkownika
        
        Dla robota: To jest główna funkcja którą wywołujesz gdy robot
        chce rozpocząć rozmowę. Działa asynchronicznie (async/await).
        
        Args:
            request: Obiekt żądania HTTP zawierający parametry połączenia
        
        Returns:
            WebSocketResponse: Obiekt połączenia WebSocket
        """
        # KROK 1: Inicjalizacja WebSocket
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        # Utwórz kolorowy logger dla tej sesji (łatwiej debugować)
        clog = ColorizedLog.randomize()
        
        # Pobierz informacje o kliencie (dla logowania)
        peer = request.remote  # Adres IP klienta
        peer_port = request.transport.get_extra_info("peername")[1]  # Port klienta
        clog.log("info", f"Incoming connection from {peer}:{peer_port}")

        # OPCJONALNE: Parametry sampling (zakomentowane - używamy domyślnych)
        # Możesz je odkomentować i dostosować dla różnych zachowań modelu
        # self.lm_gen.temp = float(request.query["audio_temperature"])
        # self.lm_gen.temp_text = float(request.query["text_temperature"])
        # self.lm_gen.top_k_text = max(1, int(request.query["text_topk"]))
        # self.lm_gen.top_k = max(1, int(request.query["audio_topk"]))
        
        # KROK 2: Konstruuj pełną ścieżkę do pliku voice prompt
        requested_voice_prompt_path = None
        voice_prompt_path = None
        
        if self.voice_prompt_dir is not None:
            # Pobierz nazwę pliku głosu z parametrów zapytania (np. "NATM1.pt")
            voice_prompt_filename = request.query["voice_prompt"]
            requested_voice_prompt_path = None
            
            if voice_prompt_filename is not None:
                # Połącz katalog z nazwą pliku
                requested_voice_prompt_path = os.path.join(self.voice_prompt_dir, voice_prompt_filename)
            
            # Sprawdź czy plik istnieje - jeśli nie, zgłoś błąd
            if requested_voice_prompt_path is None or not os.path.exists(requested_voice_prompt_path):
                raise FileNotFoundError(
                    f"Requested voice prompt '{voice_prompt_filename}' not found in '{self.voice_prompt_dir}'"
                )
            else:
                voice_prompt_path = requested_voice_prompt_path
        
        # KROK 3: Załaduj voice prompt jeśli się zmienił
        if self.lm_gen.voice_prompt != voice_prompt_path:
            if voice_prompt_path.endswith('.pt'):
                # Załaduj pre-zapisane embeddingi głosu (szybsze)
                self.lm_gen.load_voice_prompt_embeddings(voice_prompt_path)
            else:
                # Załaduj i przetwórz plik audio głosu (wolniejsze)
                self.lm_gen.load_voice_prompt(voice_prompt_path)
        
        # KROK 4: Przygotuj text prompt (instrukcje dla modelu)
        # Tokenizacja: zamiana tekstu na sekwencję liczb (tokenów)
        self.lm_gen.text_prompt_tokens = self.text_tokenizer.encode(wrap_with_system_tags(request.query["text_prompt"])) if len(request.query["text_prompt"]) > 0 else None
        
        # KROK 5: Pobierz seed dla reprodukowalności (opcjonalnie)
        seed = int(request["seed"]) if "seed" in request.query else None

        async def recv_loop():
            """
            Pętla odbierania wiadomości WebSocket od klienta.
            
            Ta funkcja asynchroniczna:
            - Nasłuchuje na wiadomości przychodzące przez WebSocket
            - Rozpoznaje typ wiadomości (audio, zamknięcie, błąd)
            - Przekazuje audio do opus_reader do dekodowania
            - Ustawia flagę 'close' gdy połączenie się kończy
            
            Dla robota: Ta pętla odbiera strumień audio z mikrofonu robota/użytkownika.
            """
            nonlocal close
            try:
                # Iteruj przez wszystkie przychodzące wiadomości
                async for message in ws:
                    # Obsługa błędów połączenia
                    if message.type == aiohttp.WSMsgType.ERROR:
                        clog.log("error", f"{ws.exception()}")
                        break
                    
                    # Połączenie zamknięte przez drugą stronę
                    elif message.type == aiohttp.WSMsgType.CLOSED:
                        break
                    
                    # Żądanie zamknięcia połączenia
                    elif message.type == aiohttp.WSMsgType.CLOSE:
                        break
                    
                    # Sprawdź czy to wiadomość binarna (audio)
                    elif message.type != aiohttp.WSMsgType.BINARY:
                        clog.log("error", f"unexpected message type {message.type}")
                        continue
                    
                    # Pobierz dane wiadomości
                    message = message.data
                    
                    # Sprawdź czy to bytes (dane binarne)
                    if not isinstance(message, bytes):
                        clog.log("error", f"unsupported message type {type(message)}")
                        continue
                    
                    # Pomiń puste wiadomości
                    if len(message) == 0:
                        clog.log("warning", "empty message")
                        continue
                    
                    # PROTOKÓŁ: Pierwszy bajt określa typ wiadomości
                    kind = message[0]
                    
                    if kind == 1:  # Typ 1 = audio data
                        # Reszta wiadomości to skompresowane audio (Opus)
                        payload = message[1:]
                        # Dodaj do bufora opus_reader do dekodowania
                        opus_reader.append_bytes(payload)
                    else:
                        clog.log("warning", f"unknown message kind {kind}")
            finally:
                # Zawsze ustaw flagę zamknięcia gdy pętla się kończy
                close = True
                clog.log("info", "connection closed")

        async def opus_loop():
            """
            Główna pętla przetwarzania audio - serce systemu real-time.
            
            Ta funkcja:
            1. Odbiera zdekodowane PCM audio z opus_reader
            2. Akumuluje je w buforze do pełnej ramki (frame)
            3. Enkoduje ramkę do codes przez Mimi
            4. Przepuszcza przez model LM (generuje odpowiedź)
            5. Dekoduje odpowiedź do PCM
            6. Wysyła przez opus_writer do klienta
            7. Dekoduje i wysyła tokeny tekstowe
            
            To jest główna pętla full-duplex - działa równolegle z recv_loop i send_loop.
            
            Dla robota: To tutaj dzieje się "magia" - audio wejściowe zamienia się
            w odpowiedź audio i tekst w czasie rzeczywistym.
            """
            # Bufor akumulujący PCM audio do pełnej ramki
            all_pcm_data = None

            while True:
                # Sprawdź czy połączenie zamknięte - jeśli tak, zakończ
                if close:
                    return
                
                # Krótkie oczekiwanie aby nie zajmować 100% CPU
                await asyncio.sleep(0.001)
                
                # Odczytaj zdekodowane PCM z opus_reader
                pcm = opus_reader.read_pcm()
                
                # Jeśli brak danych - kontynuuj czekanie
                if pcm.shape[-1] == 0:
                    continue
                
                # KROK 1: Akumuluj PCM w buforze
                if all_pcm_data is None:
                    all_pcm_data = pcm
                else:
                    # Dołącz nowe dane do istniejącego bufora
                    all_pcm_data = np.concatenate((all_pcm_data, pcm))
                
                # KROK 2: Przetwarzaj pełne ramki
                # Dopóki mamy wystarczająco danych dla pełnej ramki
                while all_pcm_data.shape[-1] >= self.frame_size:
                    be = time.time()  # Timestamp początkowy (dla debugowania)
                    
                    # Wytnij jedną ramkę z bufora
                    chunk = all_pcm_data[: self.frame_size]
                    all_pcm_data = all_pcm_data[self.frame_size:]
                    
                    # Konwersja numpy → torch tensor i przeniesienie na GPU/CPU
                    chunk = torch.from_numpy(chunk)
                    chunk = chunk.to(device=self.device)[None, None]  # Dodaj wymiary batch i channel
                    
                    # KROK 3: Enkoduj audio użytkownika do codes (kompresja)
                    codes = self.mimi.encode(chunk)
                    _ = self.other_mimi.encode(chunk)  # Enkoduj też przez drugi Mimi (synchronizacja)
                    
                    # KROK 4: Przepuść przez model LM krok po kroku
                    for c in range(codes.shape[-1]):
                        # Wygeneruj tokeny odpowiedzi (tekst + audio) dla jednej ramki codes
                        tokens = self.lm_gen.step(codes[:, :, c: c + 1])
                        
                        # Jeśli model jeszcze nie jest gotowy - pomiń
                        if tokens is None:
                            continue
                        
                        # Sprawdź kształt: powinno być dep_q+1 kanałów (tekst + 8 audio)
                        assert tokens.shape[1] == self.lm_gen.lm_model.dep_q + 1
                        
                        # KROK 5: Dekoduj tokeny audio do PCM
                        # tokens[:, 1:9] = 8 codebook'ów audio (pomijamy kanał tekstowy [0])
                        main_pcm = self.mimi.decode(tokens[:, 1:9])
                        _ = self.other_mimi.decode(tokens[:, 1:9])  # Dekoduj też przez drugi Mimi
                        
                        # Przenieś PCM z GPU na CPU (dla dalszego przetwarzania)
                        main_pcm = main_pcm.cpu()
                        
                        # KROK 6: Wyślij wygenerowane PCM do opus_writer (do kompresji)
                        opus_writer.append_pcm(main_pcm[0, 0].numpy())
                        
                        # KROK 7: Przetwórz token tekstowy
                        text_token = tokens[0, 0, 0].item()  # Pierwszy kanał = tekst
                        
                        # Jeśli to nie jest token specjalny (padding, etc.)
                        if text_token not in (0, 3):
                            # Dekoduj token → słowo/fragment słowa
                            _text = self.text_tokenizer.id_to_piece(text_token)  # type: ignore
                            # Zamień znacznik _ na spację (convention SentencePiece)
                            _text = _text.replace("▁", " ")
                            # Wyślij tekst do klienta (typ wiadomości 0x02)
                            msg = b"\x02" + bytes(_text, encoding="utf8")
                            await ws.send_bytes(msg)
                        else:
                            # Token specjalny - loguj dla debugowania
                            text_token_map = ['EPAD', 'BOS', 'EOS', 'PAD']

        async def send_loop():
            """
            Pętla wysyłania audio do klienta przez WebSocket.
            
            Ta funkcja:
            - Odczytuje skompresowane audio (Opus) z opus_writer
            - Wysyła je przez WebSocket do klienta
            - Działa w nieskończonej pętli aż do zamknięcia połączenia
            
            Protokół: Typ wiadomości 0x01 = audio data
            
            Dla robota: Ta pętla wysyła wygenerowane odpowiedzi audio
            do głośników robota/użytkownika.
            """
            while True:
                # Sprawdź czy połączenie zamknięte
                if close:
                    return
                
                # Krótkie oczekiwanie
                await asyncio.sleep(0.001)
                
                # Odczytaj skompresowane audio z opus_writer
                msg = opus_writer.read_bytes()
                
                # Jeśli są dane - wyślij je
                if len(msg) > 0:
                    # Prefiks 0x01 = typ wiadomości "audio"
                    await ws.send_bytes(b"\x01" + msg)

        # GŁÓWNA CZĘŚĆ handle_chat - orchestracja całej sesji
        
        clog.log("info", "accepted connection")
        
        # Loguj konfigurację sesji
        if len(request.query["text_prompt"]) > 0:
            clog.log("info", f"text prompt: {request.query['text_prompt']}")
        if len(request.query["voice_prompt"]) > 0:
            clog.log("info", f"voice prompt: {voice_prompt_path} (requested: {requested_voice_prompt_path})")
        
        # Flaga kontrolująca zakończenie pętli
        close = False
        
        # SEKCJA KRYTYCZNA: Tylko jedna sesja na raz (dzięki lock)
        async with self.lock:
            # Ustaw seed jeśli podany (dla reprodukowalności)
            if seed is not None and seed != -1:
                seed_all(seed)

            # Utwórz enkoder/dekoder Opus dla tej sesji
            opus_writer = sphn.OpusStreamWriter(self.mimi.sample_rate)
            opus_reader = sphn.OpusStreamReader(self.mimi.sample_rate)
            
            # Zresetuj stan streaming wszystkich modeli (czyści bufory)
            self.mimi.reset_streaming()
            self.other_mimi.reset_streaming()
            self.lm_gen.reset_streaming()
            
            async def is_alive():
                """
                Sprawdza czy klient jest wciąż połączony.
                
                Używane podczas ładowania promptów systemowych - jeśli klient
                się rozłączy w trakcie, przerywamy przetwarzanie.
                """
                if close or ws.closed:
                    return False
                try:
                    # Sprawdź czy przyszła wiadomość o rozłączeniu (timeout 10ms)
                    msg = await asyncio.wait_for(ws.receive(), timeout=0.01)
                    if msg.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                        return False
                except asyncio.TimeoutError:
                    # Brak wiadomości = klient prawdopodobnie wciąż żyje
                    return True
                except aiohttp.ClientConnectionError:
                    return False
                return True
            
            # KROK A: Przetwórz prompty systemowe (text + voice)
            # Używamy mimi do enkodowania voice prompt, potem resetujemy
            await self.lm_gen.step_system_prompts_async(self.mimi, is_alive=is_alive)
            self.mimi.reset_streaming()
            clog.log("info", "done with system prompts")
            
            # KROK B: Wyślij handshake (potwierdzenie gotowości)
            if await is_alive():
                # Wiadomość 0x00 = handshake
                await ws.send_bytes(b"\x00")
                clog.log("info", "sent handshake bytes")
                
                # KROK C: Uruchom wszystkie trzy pętle równolegle
                tasks = [
                    asyncio.create_task(recv_loop()),   # Odbieranie audio od użytkownika
                    asyncio.create_task(opus_loop()),   # Przetwarzanie i generowanie
                    asyncio.create_task(send_loop()),   # Wysyłanie audio do użytkownika
                ]

                # Czekaj aż którakolwiek pętla się zakończy
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                
                # Wymuś zakończenie pozostałych zadań
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                await ws.close()
                clog.log("info", "session closed")
                # await asyncio.gather(opus_loop(), recv_loop(), send_loop())
        clog.log("info", "done with connection")
        return ws


def _get_voice_prompt_dir(voice_prompt_dir: Optional[str], hf_repo: str) -> Optional[str]:
    """
    Pobiera katalog z plikami głosów (voice prompts).
    
    Jeśli voice_prompt_dir nie jest podany:
      - Pobiera voices.tgz z Huggingface
      - Rozpakowuje go raz (cache'uje)
      - Zwraca ścieżkę do rozpakowanego katalogu
    
    Jeśli voice_prompt_dir jest podany:
      - Po prostu zwraca go (użytkownik podał własny katalog)
    
    Args:
        voice_prompt_dir: Opcjonalna ścieżka do katalogu z głosami
        hf_repo: Nazwa repozytorium Huggingface
    
    Returns:
        Ścieżka do katalogu z plikami głosów
    """
    if voice_prompt_dir is not None:
        return voice_prompt_dir

    logger.info("retrieving voice prompts")

    # Pobierz voices.tgz z Huggingface (cache'owane lokalnie)
    voices_tgz = hf_hub_download(hf_repo, "voices.tgz")
    voices_tgz = Path(voices_tgz)
    voices_dir = voices_tgz.parent / "voices"

    # Rozpakuj jeśli jeszcze nie rozpakowane
    if not voices_dir.exists():
        logger.info(f"extracting {voices_tgz} to {voices_dir}")
        with tarfile.open(voices_tgz, "r:gz") as tar:
            tar.extractall(path=voices_tgz.parent)

    if not voices_dir.exists():
        raise RuntimeError("voices.tgz did not contain a 'voices/' directory")

    return str(voices_dir)


def _get_static_path(static: Optional[str]) -> Optional[str]:
    """
    Pobiera ścieżkę do plików statycznych interfejsu webowego.
    
    Jeśli static jest None:
      - Pobiera dist.tgz z Huggingface (zbudowany frontend)
      - Rozpakowuje go
      - Zwraca ścieżkę
    
    Jeśli static jest podany:
      - Zwraca go (chyba że "none" - wtedy nie serwuje UI)
    
    Args:
        static: Opcjonalna ścieżka do katalogu z plikami statycznymi
    
    Returns:
        Ścieżka do katalogu static lub None
    """
    if static is None:
        logger.info("retrieving the static content")
        # Pobierz zbudowany frontend z HF
        dist_tgz = hf_hub_download("nvidia/personaplex-7b-v1", "dist.tgz")
        dist_tgz = Path(dist_tgz)
        dist = dist_tgz.parent / "dist"
        
        # Rozpakuj jeśli potrzeba
        if not dist.exists():
            with tarfile.open(dist_tgz, "r:gz") as tar:
                tar.extractall(path=dist_tgz.parent)
        return str(dist)
    elif static != "none":
        # Gdy ustawione na "none" - nie serwujemy UI
        return static
    return None


def main():
    """
    Główna funkcja uruchamiająca serwer PersonaPlex.
    
    Ta funkcja:
    1. Parsuje argumenty wiersza poleceń
    2. Pobiera/ładuje modele (Mimi, Moshi, tokenizer)
    3. Przygotowuje głosy i pliki statyczne
    4. Tworzy ServerState
    5. Wykonuje warmup modeli
    6. Uruchamia serwer HTTP/WebSocket
    
    Dla robota: To jest entry point - uruchom tę funkcję aby
    wystartować serwer do komunikacji z robotem.
    """
    # KROK 1: Parsowanie argumentów
    parser = argparse.ArgumentParser()
    
    # Argumenty sieciowe
    parser.add_argument("--host", default="localhost", type=str,
                       help="Adres hosta (localhost, 0.0.0.0 dla dostępu z sieci)")
    parser.add_argument("--port", default=8998, type=int,
                       help="Port serwera (domyślnie 8998)")
    parser.add_argument("--static", type=str,
                       help="Ścieżka do katalogu z plikami statycznymi UI")
    
    # Tunelowanie (dla zdalnego dostępu)
    parser.add_argument("--gradio-tunnel", action='store_true',
                       help='Aktywuj tunel Gradio (dostęp przez internet)')
    parser.add_argument("--gradio-tunnel-token",
                       help='Token tunelu (opcjonalnie, dla stałego URL)')

    # Ścieżki do modeli (opcjonalne - domyślnie pobiera z HF)
    parser.add_argument("--tokenizer", type=str,
                       help="Ścieżka do lokalnego pliku tokenizera")
    parser.add_argument("--moshi-weight", type=str,
                       help="Ścieżka do lokalnego checkpointu Moshi")
    parser.add_argument("--mimi-weight", type=str,
                       help="Ścieżka do lokalnego checkpointu Mimi")
    parser.add_argument("--hf-repo", type=str, default=loaders.DEFAULT_REPO,
                       help="Repozytorium HF (domyślnie PersonaPlex). "
                            "Użyj dla innego pre-trained modelu.")
    
    # Konfiguracja sprzętowa
    parser.add_argument("--device", type=str, default="cuda",
                       help="Urządzenie do obliczeń (cuda/cpu, domyślnie cuda)")
    parser.add_argument("--cpu-offload", action="store_true",
                       help="Offload warstw LM na CPU gdy brak pamięci GPU. "
                            "Wymaga pakietu 'accelerate'.")
    parser.add_argument(
        "--voice-prompt-dir",
        type=str,
        help=(
            "Directory containing voice prompt files. "
            "If omitted, voices.tgz is downloaded from HF and extracted."
            "Voice prompt filenames from client requests will be joined with this directory path."
        )
    )
    parser.add_argument(
        "--ssl",
        type=str,
        help=(
            "use https instead of http, this flag should point to a directory "
            "that contains valid key.pem and cert.pem files"
        )
    )

    args = parser.parse_args()
    args.voice_prompt_dir = _get_voice_prompt_dir(
        args.voice_prompt_dir,
        args.hf_repo,
    )
    if args.voice_prompt_dir is not None:
        assert os.path.exists(args.voice_prompt_dir), \
            f"Directory missing: {args.voice_prompt_dir}"
    logger.info(f"voice_prompt_dir = {args.voice_prompt_dir}")

    static_path: None | str = _get_static_path(args.static)
    assert static_path is None or os.path.exists(static_path), \
        f"Static path does not exist: {static_path}."
    logger.info(f"static_path = {static_path}")
    args.device = torch_auto_device(args.device)

    seed_all(42424242)

    setup_tunnel = None
    tunnel_token = ''
    if args.gradio_tunnel:
        try:
            from gradio import networking  # type: ignore
        except ImportError:
            logger.error("Cannot find gradio which is required to activate a tunnel. "
                         "Please install with `pip install gradio`.")
            sys.exit(1)
        setup_tunnel = networking.setup_tunnel
        if args.gradio_tunnel_token is None:
            tunnel_token = secrets.token_urlsafe(32)
        else:
            tunnel_token = args.gradio_tunnel_token

    # Download config.json to increment download counter
    # No worries about double-counting since config.json will be cached the second time
    hf_hub_download(args.hf_repo, "config.json")

    logger.info("loading mimi")
    if args.mimi_weight is None:
        args.mimi_weight = hf_hub_download(args.hf_repo, loaders.MIMI_NAME)
    mimi = loaders.get_mimi(args.mimi_weight, args.device)
    other_mimi = loaders.get_mimi(args.mimi_weight, args.device)
    logger.info("mimi loaded")

    if args.tokenizer is None:
        args.tokenizer = hf_hub_download(args.hf_repo, loaders.TEXT_TOKENIZER_NAME)
    text_tokenizer = sentencepiece.SentencePieceProcessor(args.tokenizer)  # type: ignore

    logger.info("loading moshi")
    if args.moshi_weight is None:
        args.moshi_weight = hf_hub_download(args.hf_repo, loaders.MOSHI_NAME)
    lm = loaders.get_moshi_lm(args.moshi_weight, device=args.device, cpu_offload=args.cpu_offload)
    lm.eval()
    logger.info("moshi loaded")
    state = ServerState(
        mimi=mimi,
        other_mimi=other_mimi,
        text_tokenizer=text_tokenizer,
        lm=lm,
        device=args.device,
        voice_prompt_dir=args.voice_prompt_dir,
        save_voice_prompt_embeddings=False,
    )
    logger.info("warming up the model")
    state.warmup()
    app = web.Application()
    app.router.add_get("/api/chat", state.handle_chat)
    if static_path is not None:
        async def handle_root(_):
            return web.FileResponse(os.path.join(static_path, "index.html"))

        logger.info(f"serving static content from {static_path}")
        app.router.add_get("/", handle_root)
        app.router.add_static(
            "/", path=static_path, follow_symlinks=True, name="static"
        )
    protocol = "http"
    ssl_context = None
    if args.ssl is not None:
        ssl_context, protocol = create_ssl_context(args.ssl)
    host_ip = args.host if args.host not in ("0.0.0.0", "::", "localhost") else get_lan_ip()
    logger.info(f"Access the Web UI directly at {protocol}://{host_ip}:{args.port}")
    if setup_tunnel is not None:
        tunnel = setup_tunnel('localhost', args.port, tunnel_token, None)
        logger.info(f"Tunnel started, if executing on a remote GPU, you can use {tunnel}.")
    web.run_app(app, port=args.port, ssl_context=ssl_context)


with torch.no_grad():
    main()
