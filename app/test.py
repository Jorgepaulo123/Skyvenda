import keyboard

def capturar_codigo():
    print("Aguardando leitura do código de barras...")
    codigo_barras = ""
    while True:
        event = keyboard.read_event()
        if event.event_type == keyboard.KEY_DOWN:
            key = event.name
            if key == 'enter':
                print(f"Código de barras lido: {codigo_barras}")
                codigo_barras = ""  # Reinicia para o próximo código
            else:
                codigo_barras += key

if __name__ == "__main__":
    capturar_codigo()
