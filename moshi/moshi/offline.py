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

"""
Tryb offline PersonaPlex - przetwarzanie audio bez serwera WebSocket.

=== CO TO JEST? ===
Ten skrypt umożliwia użycie PersonaPlex bez uruchamiania serwera.
Zamiast komunikacji w czasie rzeczywistym:
- Wczytuje plik WAV z pytaniem użytkownika
- Generuje odpowiedź (audio + tekst)
- Zapisuje wynik do plików

=== PRZEPŁYW WYSOKIEGO POZIOMU ===
1. Załaduj modele (Mimi encoder/decoder, Moshi LM, tokenizer) - tak samo jak server.py
2. Rozgrzej modele (warmup) - inicjalizacja CUDA graphs i stanu streaming
3. Faza promptów:
   - Załaduj tokeny tekstu systemowego
   - Załaduj voice prompt WAV (głos agenta)
4. Faza streaming-like:
   - Wczytaj ramki audio użytkownika z pliku WAV
   - Autoregressywnie generuj tekst + audio agenta dla każdego kroku
   - Dekoduj ramki audio
5. Połącz wygenerowane ramki i zapisz WAV o tym samym czasie trwania co input

=== ZASTOSOWANIE W ROBOTYCE ===
Tryb offline jest przydatny do:
- Testowania i debugowania bez potrzeby real-time
- Generowania demonstracji i przykładów
- Batch processing wielu pytań
- Ewaluacji jakości odpowiedzi

=== RÓŻNICE VS SERVER.PY ===
- Brak WebSocket - wszystko działa lokalnie
- Brak interakcji w czasie rzeczywistym
- Przetwarza całe pliki naraz
- Prostszy w użyciu do testów

Ten skrypt używa tych samych helperów z lm.py (load_audio, _iterate_audio, 
encode_from_sphn) aby zachować zgodność z logiką feeding voice-prompt w serwerze.
"""

import argparse
import os
import tarfile
from pathlib import Path
import json
from typing import Optional, List

import numpy as np
import torch
import sentencepiece
import sphn
from huggingface_hub import hf_hub_download

from .client_utils import make_log
from .models import loaders, LMGen, MimiModel
from .models.lm import load_audio as lm_load_audio
from .models.lm import _iterate_audio as lm_iterate_audio
from .models.lm import encode_from_sphn as lm_encode_from_sphn


def log(level: str, msg: str):
    """
    Prosta funkcja logowania - wypisuje wiadomości z poziomem (info/error/warning).
    """
    print(make_log(level, msg))


def seed_all(seed: int):
    """
    Ustawia ziarno (seed) dla wszystkich generatorów losowych.
    
    DLACZEGO TO JEST WAŻNE W TRYBIE OFFLINE?
    W trybie offline seed jest kluczowy dla reprodukowalności:
    - To samo pytanie + ten sam seed = dokładnie ta sama odpowiedź
    - Przydatne do testów porównawczych
    - Umożliwia debugging (możesz powtórzyć dokładnie to samo zachowanie)
    
    Strategia seedowania jest taka sama jak w server.py dla spójności.
    
    Args:
        seed: Liczba całkowita jako ziarno (np. 42424242)
    """
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    import random
    import numpy as _np
    random.seed(seed)
    _np.random.seed(seed)
    torch.backends.cudnn.deterministic = False
    torch.backends.cudnn.benchmark = False


def wrap_with_system_tags(text: str) -> str:
    """
    Opakowuje prompt tekstowy w znaczniki systemowe <system>...</system>.
    
    To samo zachowanie jak w server.py - model wymaga tego formatu.
    
    Przykład:
        Input:  "You are a helpful robot."
        Output: "<system> You are a helpful robot. <system>"
    
    Args:
        text: Tekst promptu
    
    Returns:
        Tekst z dodanymi znacznikami
    """
    cleaned = text.strip()
    if cleaned.startswith("<system>") and cleaned.endswith("<system>"):
        return cleaned
    return f"<system> {cleaned} <system>"


def warmup(mimi: MimiModel, other_mimi: MimiModel, lm_gen: LMGen, device: str, frame_size: int):
    """
    Rozgrzewka modelu - inicjalizacja CUDA graphs i stanu streaming.
    
    DLACZEGO WARMUP W TRYBIE OFFLINE?
    Nawet w trybie offline warmup jest potrzebny:
    - Pierwsze uruchomienie GPU jest wolne (alokacja pamięci, kompilacja)
    - CUDA graphs wymagają inicjalizacji
    - Po warmup model działa szybciej i bardziej przewidywalnie
    
    Ta funkcja replikuje dokładnie to samo zachowanie co server.py:
    zera → encode → LMGen.step → decode
    
    Args:
        mimi: Model Mimi do enkodowania
        other_mimi: Drugi model Mimi
        lm_gen: Generator LM
        device: Urządzenie (cuda/cpu)
        frame_size: Rozmiar ramki w próbkach
    """
    for _ in range(4):
        chunk = torch.zeros(1, 1, frame_size, dtype=torch.float32, device=device)
        codes = mimi.encode(chunk)
        _ = other_mimi.encode(chunk)
        for c in range(codes.shape[-1]):
            tokens = lm_gen.step(codes[:, :, c : c + 1])
            if tokens is None:
                continue
            # Dekoduj kanały audio agenta aby upewnić się że grafy/stany decode są gotowe
            _ = mimi.decode(tokens[:, 1:9])
            _ = other_mimi.decode(tokens[:, 1:9])
    if torch.cuda.is_available():
        torch.cuda.synchronize()


def decode_tokens_to_pcm(mimi: MimiModel, other_mimi: MimiModel, lm_gen: LMGen, tokens: torch.Tensor) -> np.ndarray:
    """
    Dekoduje jeden krok tokenów modelu do PCM używając Mimi.
    
    tokens ma kształt [B, dep_q+1, 1] gdzie:
    - B = batch size (zazwyczaj 1)
    - dep_q+1 = liczba kanałów (1 tekstowy + dep_q audio)
    - 1 = jedna ramka czasu
    
    Kanały 1..dep_q to codebooki audio agenta (pomijamy kanał 0 który jest tekstem).
    
    Args:
        mimi: Model Mimi do dekodowania
        other_mimi: Drugi model Mimi (synchronizacja)
        lm_gen: Generator LM (nie używany bezpośrednio)
        tokens: Tensory tokenów do zdekodowania
    
    Returns:
        Tablica numpy 1D float32 (mono) dla bieżącej ramki PCM
    """
    # Dekoduj tokeny audio (kanały 1-8) do PCM
    pcm = mimi.decode(tokens[:, 1:9])
    _ = other_mimi.decode(tokens[:, 1:9])  # Synchronizacja
    
    # Przenieś na CPU i konwertuj do numpy
    # [0, 0] = pierwszy element batcha, pierwszy kanał
    pcm = pcm.detach().cpu().numpy()[0, 0]
    return pcm


def _get_voice_prompt_dir(voice_prompt_dir: Optional[str], hf_repo: str) -> Optional[str]:
    """
    Pobiera katalog z plikami voice prompts.
    
    Jeśli voice_prompt_dir nie jest podany:
      - Pobiera voices.tgz z Huggingface
      - Rozpakowuje raz (cache)
      - Zwraca katalog
    
    Jeśli voice_prompt_dir jest podany:
      - Zwraca go bezpośrednio
    
    Args:
        voice_prompt_dir: Opcjonalna ścieżka do katalogu
        hf_repo: Repozytorium Huggingface
    
    Returns:
        Ścieżka do katalogu z głosami
    """
    if voice_prompt_dir is not None:
        return voice_prompt_dir

    log("info", "retrieving voice prompts")
    
    # Pobierz archiwum z HF (cache'owane lokalnie)
    voices_tgz = hf_hub_download(hf_repo, "voices.tgz")
    voices_tgz = Path(voices_tgz)
    voices_dir = voices_tgz.parent / "voices"

    # Rozpakuj jeśli trzeba
    if not voices_dir.exists():
        log("info", f"extracting {voices_tgz} to {voices_dir}")
        with tarfile.open(voices_tgz, "r:gz") as tar:
            tar.extractall(path=voices_tgz.parent)

    if not voices_dir.exists():
        raise RuntimeError("voices.tgz did not contain a 'voices/' directory")

    return str(voices_dir)


def run_inference(
    input_wav: str,
    output_wav: str,
    output_text: str,
    text_prompt: str,
    voice_prompt_path: str,
    tokenizer_path: Optional[str],
    moshi_weight: Optional[str],
    mimi_weight: Optional[str],
    hf_repo: str,
    device: str,
    seed: Optional[int],
    temp_audio: float,
    temp_text: float,
    topk_audio: int,
    topk_text: int,
    greedy: bool,
    save_voice_prompt_embeddings: bool,
    cpu_offload: bool = False,
):
    """
    Uruchamia offline inference używając pliku WAV jako strumienia użytkownika.
    
    === GŁÓWNA FUNKCJA TRYBU OFFLINE ===
    
    Ta funkcja jest sercem trybu offline. Wykonuje pełny pipeline:
    
    PRZYGOTOWANIE:
    1. Ładuje/inicjalizuje modele i tokenizer
    2. Wykonuje warmup
    3. Ładuje tokeny tekstu systemowego i voice prompt
    
    PRZETWARZANIE:
    4. Uruchamia fazy promptów (text + voice + cisze) przez LMGen.step_system_prompts
    5. Strumieniuje ramki WAV użytkownika do kanałów wejściowych
    6. Samplinguje outputy modelu (tekst + audio agenta)
    
    ZAPIS WYNIKÓW:
    7. Dekoduje i zapisuje WAV wyjściowy o tym samym czasie trwania co wejście
    8. Zapisuje transkrypcję tekstową do JSON
    
    === ZASTOSOWANIE DLA ROBOTA ===
    Używaj tej funkcji gdy:
    - Chcesz przetestować odpowiedź na konkretne pytanie
    - Potrzebujesz wygenerować demo bez real-time
    - Debugujesz zachowanie modelu
    - Batch processing wielu pytań
    
    === PARAMETRY ===
    
    Args:
        input_wav: Ścieżka do pliku WAV z pytaniem użytkownika
        output_wav: Ścieżka gdzie zapisać odpowiedź audio
        output_text: Ścieżka gdzie zapisać transkrypcję JSON
        text_prompt: Prompt tekstowy definiujący rolę (np. "You are a robot assistant")
        voice_prompt_path: Ścieżka do pliku głosu (WAV lub .pt embeddings)
        tokenizer_path: Ścieżka do tokenizera (opcjonalnie, pobierze z HF)
        moshi_weight: Ścieżka do wag Moshi (opcjonalnie, pobierze z HF)
        mimi_weight: Ścieżka do wag Mimi (opcjonalnie, pobierze z HF)
        hf_repo: Repozytorium Huggingface do pobrania modeli
        device: Urządzenie obliczeniowe ("cuda" lub "cpu")
        seed: Ziarno dla reprodukowalności (None lub -1 = losowe)
        temp_audio: Temperatura sampling dla audio (wyższe = bardziej losowe)
        temp_text: Temperatura sampling dla tekstu
        topk_audio: Top-k sampling dla audio (mniejsze = bardziej konserwatywne)
        topk_text: Top-k sampling dla tekstu
        greedy: Jeśli True, używa greedy decoding zamiast sampling
        save_voice_prompt_embeddings: Czy zapisać embeddingi głosu do pliku .pt
        cpu_offload: Czy przenieść warstwy LM na CPU (oszczędza pamięć GPU)
    
    Returns:
        None (zapisuje wyniki do plików)
    """
    # KROK 0: Ustaw seed jeśli podany
    if seed is not None and seed != -1:
        seed_all(seed)

    # Inkrementuj licznik pobrań (dla statystyk HF)
    # Nie martw się o podwójne liczenie - config.json jest cache'owany
    hf_hub_download(hf_repo, "config.json")

    # ========== KROK 1: Załaduj modele Mimi (encodery/dekodery) ==========
    log("info", "loading mimi")
    if mimi_weight is None:
        # Pobierz z Huggingface jeśli nie podano lokalnej ścieżki
        mimi_weight = hf_hub_download(hf_repo, loaders.MIMI_NAME)  # type: ignore
    
    # Załaduj dwa modele Mimi (jeden dla wejścia, drugi dla wyjścia)
    mimi = loaders.get_mimi(mimi_weight, device)
    other_mimi = loaders.get_mimi(mimi_weight, device)
    log("info", "mimi loaded")

    # ========== KROK 2: Załaduj tokenizer ==========
    if tokenizer_path is None:
        tokenizer_path = hf_hub_download(hf_repo, loaders.TEXT_TOKENIZER_NAME)  # type: ignore
    text_tokenizer = sentencepiece.SentencePieceProcessor(tokenizer_path)  # type: ignore

    # ========== KROK 3: Załaduj model językowy Moshi i ustaw tryb eval ==========
    log("info", "loading moshi")
    if moshi_weight is None:
        moshi_weight = hf_hub_download(hf_repo, loaders.MOSHI_NAME)  # type: ignore
    lm = loaders.get_moshi_lm(moshi_weight, device=device, cpu_offload=cpu_offload)
    lm.eval()  # Tryb ewaluacji (wyłącza dropout, itp.)
    log("info", "moshi loaded")

    # ========== KROK 4: Konstruuj LMGen (tak samo jak ServerState w server.py) ==========
    # Oblicz rozmiar ramki
    frame_size = int(mimi.sample_rate / mimi.frame_rate)
    
    # Utwórz generator wysokiego poziomu
    lm_gen = LMGen(
        lm,
        # Ile ramek ciszy po promptach (0.5 sekundy)
        audio_silence_frame_cnt=int(0.5 * mimi.frame_rate),
        sample_rate=mimi.sample_rate,
        device=device,
        frame_rate=mimi.frame_rate,
        save_voice_prompt_embeddings=save_voice_prompt_embeddings,
        use_sampling=not greedy,  # Sampling vs greedy
        temp=temp_audio,           # Temperatura audio
        temp_text=temp_text,       # Temperatura tekstu
        top_k=topk_audio,          # Top-k audio
        top_k_text=topk_text,      # Top-k tekstu
    )
    
    # Włącz tryb streaming (tak samo jak serwer)
    mimi.streaming_forever(1)
    other_mimi.streaming_forever(1)
    lm_gen.streaming_forever(1)

    # ========== KROK 5: Warmup modelu ==========
    log("info", "warming up the model")
    warmup(mimi, other_mimi, lm_gen, device, frame_size)

    # ========== KROK 6: Konfiguracja promptów (text + voice) ==========
    # Tokeny tekstu systemowego (k=0) i audio voice-prompt (k=1..dep_q) są wymuszone
    if voice_prompt_path.endswith('.pt'):
        # Załaduj pre-zapisane embeddingi głosu (szybsze)
        lm_gen.load_voice_prompt_embeddings(voice_prompt_path)
    else:
        # Załaduj i przetworz plik WAV głosu
        lm_gen.load_voice_prompt(voice_prompt_path)
    
    # Tokenizuj prompt tekstowy
    lm_gen.text_prompt_tokens = (
        text_tokenizer.encode(wrap_with_system_tags(text_prompt)) if len(text_prompt) > 0 else None
    )

    # ========== KROK 7: Reset streaming i uruchom fazy promptów ==========
    # Kolejność faz:
    #    - Injection voice prompt
    #    - Cisza audio
    #    - Injection text prompt  
    #    - Końcowa cisza audio
    mimi.reset_streaming()
    other_mimi.reset_streaming()
    lm_gen.reset_streaming()
    lm_gen.step_system_prompts(mimi)
    # Reset mimi streaming after voice prompt encoding
    mimi.reset_streaming()

    # 8) Load and iterate user audio frames for feeding into the input channels
    sample_rate = mimi.sample_rate
    user_audio = lm_load_audio(input_wav, sample_rate)  # (C, T) at model SR

    # 9) Encode user audio with Mimi (same iterator logic used for voice prompts),
    #    and step the model one frame at a time, collecting decoded PCM frames
    generated_frames: List[np.ndarray] = []
    generated_text_tokens: List[str] = []
    total_target_samples = user_audio.shape[-1]

    for user_encoded in lm_encode_from_sphn(
        mimi,
        lm_iterate_audio(
            user_audio, sample_interval_size=lm_gen._frame_size, pad=True
        ),
        max_batch=1,
    ):
        # user_encoded: [1, K, T]. Feed one step at a time (usually T==1)
        steps = user_encoded.shape[-1]
        for c in range(steps):
            step_in = user_encoded[:, :, c : c + 1]
            # Feed user-side input channels; text + agent audio are sampled
            tokens = lm_gen.step(step_in)
            if tokens is None:
                continue
            # Decode current sampled agent frame to PCM
            pcm = decode_tokens_to_pcm(mimi, other_mimi, lm_gen, tokens)
            generated_frames.append(pcm)
            # Decode text token
            text_token = tokens[0, 0, 0].item()
            if text_token not in (0, 3):
                _text = text_tokenizer.id_to_piece(text_token)  # type: ignore
                _text = _text.replace("▁", " ")
                log("info", f"text token '{_text}'")
                generated_text_tokens.append(_text)
            else:
                text_token_map = ['EPAD', 'BOS', 'EOS', 'PAD']
                log("info", f"text token '{text_token_map[text_token]}'")
                generated_text_tokens.append(text_token_map[text_token])

    if len(generated_frames) == 0:
        log("error", "No audio frames were generated. Check input file and configuration.")
        return

    # 10) Concatenate frames and trim/pad to match input duration
    output_pcm = np.concatenate(generated_frames, axis=-1)
    if output_pcm.shape[-1] > total_target_samples:
        output_pcm = output_pcm[:total_target_samples]
    elif output_pcm.shape[-1] < total_target_samples:
        pad_len = total_target_samples - output_pcm.shape[-1]
        output_pcm = np.concatenate(
            [output_pcm, np.zeros(pad_len, dtype=output_pcm.dtype)], axis=-1
        )

    # 11) Write mono WAV at model sample rate
    sphn.write_wav(output_wav, output_pcm, sample_rate)
    log("info", f"Wrote output audio to {output_wav}")

    # 12) Write text tokens
    with open(output_text, "w") as file:
        json.dump(generated_text_tokens, file, ensure_ascii=False)
    log("info", f"Wrote output text to {output_text}")    


def main():
    """Parse CLI args and run offline inference."""
    parser = argparse.ArgumentParser(
        description="Offline inference from WAV input using Moshi server components."
    )
    parser.add_argument(
        "--input-wav", required=True, type=str, help="Path to input WAV file (user audio)"
    )
    parser.add_argument(
        "--output-wav", required=True, type=str, help="Path to output WAV file of agent audio to write"
    )
    parser.add_argument(
        "--output-text", required=True, type=str, help="Path to output JSON file of agent text to write"
    )
    parser.add_argument("--text-prompt", default="You are a wise and friendly teacher. Answer questions or provide advice in a clear and engaging way.", type=str, help="Text prompt")

    parser.add_argument(
        "--voice-prompt", required=True, type=str, help="Voice prompt filename (basename) inside --voice-prompt-dir (e.g. 'NATM1.pt')."
    )
    parser.add_argument(
        "--voice-prompt-dir",
        type=str,
        help=(
            "Directory containing voice prompt files. "
            "If omitted, voices.tgz is downloaded from HF and extracted."
            "Voice prompt filenames from -voice-prompt arg will be joined with this directory path."
        )
    )

    # Model assets
    parser.add_argument("--tokenizer", type=str, help="Path to a local tokenizer file.")
    parser.add_argument("--moshi-weight", type=str, help="Path to a local checkpoint file for Moshi.")
    parser.add_argument("--mimi-weight", type=str, help="Path to a local checkpoint file for Mimi.")
    parser.add_argument(
        "--hf-repo",
        type=str,
        default=loaders.DEFAULT_REPO,
        help="HF repo to look into (defaults to pre-trained model repo)",
    )

    # Runtime / sampling controls (mirror UI semantics)
    parser.add_argument(
        "--temp-audio", type=float, default=0.8, help="Audio sampling temperature (default: 0.8)"
    )
    parser.add_argument(
        "--temp-text", type=float, default=0.7, help="Text sampling temperature (default: 0.7)"
    )
    parser.add_argument(
        "--topk-audio", type=int, default=250, help="Audio top-k sampling (default: 250)"
    )
    parser.add_argument(
        "--topk-text", type=int, default=25, help="Text top-k sampling (default: 25)"
    )
    parser.add_argument(
        "--greedy", action="store_true", help="Disable sampling (greedy decoding)"
    )
    parser.add_argument(
        "--device", type=str, default="cuda", help="Device on which to run, defaults to 'cuda'."
    )
    parser.add_argument("--cpu-offload", action="store_true",
                        help="Offload LM model layers to CPU when GPU memory is insufficient. "
                             "Requires 'accelerate' package.")
    parser.add_argument("--seed", type=int, default=-1, help="Seed for reproducibility (-1 disables)")

    args = parser.parse_args()

    # If --voice-prompt-dir is omitted, voices.tgz is downloaded from HF and extracted.
    voice_prompt_dir = _get_voice_prompt_dir(
        args.voice_prompt_dir,
        args.hf_repo,
    )
    if not os.path.exists(voice_prompt_dir):
        raise FileNotFoundError(f"voice_prompt_dir does not exist: {voice_prompt_dir}")
    log("info", f"voice_prompt_dir = {voice_prompt_dir}")

    # Join basename with directory (DO NOT mutate args.voice_prompt)
    voice_prompt_path = os.path.join(voice_prompt_dir, args.voice_prompt)
    if not os.path.exists(voice_prompt_path):
        raise FileNotFoundError(
            f"Voice prompt '{args.voice_prompt}' not found in "
            f"'{voice_prompt_dir}' (resolved: {voice_prompt_path})"
        )

    # Normalize greedy flag behavior (True if present, False otherwise)
    greedy = bool(args.greedy)

    with torch.no_grad():
        run_inference(
            input_wav=args.input_wav,
            output_wav=args.output_wav,
            output_text=args.output_text,
            text_prompt=args.text_prompt,
            voice_prompt_path=voice_prompt_path,
            tokenizer_path=args.tokenizer,
            moshi_weight=args.moshi_weight,
            mimi_weight=args.mimi_weight,
            hf_repo=args.hf_repo,
            device=args.device,
            seed=args.seed,
            temp_audio=args.temp_audio,
            temp_text=args.temp_text,
            topk_audio=args.topk_audio,
            topk_text=args.topk_text,
            greedy=greedy,
            save_voice_prompt_embeddings=False,
            cpu_offload=args.cpu_offload,
        )


if __name__ == "__main__":
    main()