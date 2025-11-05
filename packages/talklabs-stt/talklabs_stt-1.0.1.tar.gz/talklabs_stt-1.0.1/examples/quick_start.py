#!/usr/bin/env python3
"""
Quick Start - Menu Interativo
Escolha entre REST API ou WebSocket Streaming
"""
import os
import asyncio
from dotenv import load_dotenv
from talklabs_stt import STTClient

load_dotenv()

API_KEY = os.getenv("TALKLABS_STT_API_KEY")
AUDIO_FILE = "/home/TALKLABS/STT/teste_base_bookplay.wav"

def rest_example():
    """Exemplo REST API (síncrono)"""
    print("\n🎤 === REST API ===\n")
    
    client = STTClient(api_key=API_KEY)
    
    print(f"📂 Transcrevendo: {AUDIO_FILE}")
    result = client.transcribe_file(
        AUDIO_FILE,
        model="large-v3",
        language="pt"
    )
    
    transcript = result["results"]["channels"][0]["alternatives"][0]["transcript"]
    confidence = result["results"]["channels"][0]["alternatives"][0]["confidence"]
    duration = result["metadata"]["duration"]
    
    print(f"\n✅ Transcrição completa!")
    print(f"Duração: {duration:.2f}s")
    print(f"Confiança: {confidence:.2%}")
    print(f"\nTexto: {transcript}\n")

async def websocket_example():
    """Exemplo WebSocket (assíncrono)"""
    print("\n🎤 === WebSocket Streaming ===\n")
    
    client = STTClient(api_key=API_KEY)
    
    print(f"📂 Streaming: {AUDIO_FILE}\n")
    
    def on_transcript(data):
        transcript = data["channel"]["alternatives"][0]["transcript"]
        is_final = data["is_final"]
        
        if is_final:
            print(f"✅ FINAL: {transcript}")
        else:
            print(f"⏳ Interim: {transcript}")
    
    await client.transcribe_stream(
        AUDIO_FILE,
        interim_results=True,
        on_transcript=on_transcript
    )
    
    print("\n🎉 Streaming finalizado!\n")

def main():
    print("\n" + "="*50)
    print("  TalkLabs STT - Quick Start")
    print("="*50)
    print("\nEscolha o modo de transcrição:")
    print("  1. REST API (síncrono)")
    print("  2. WebSocket Streaming (assíncrono)")
    print()
    
    choice = input("Escolha (1 ou 2): ").strip()
    
    if choice == "1":
        rest_example()
    elif choice == "2":
        asyncio.run(websocket_example())
    else:
        print("❌ Opção inválida!")

if __name__ == "__main__":
    main()
