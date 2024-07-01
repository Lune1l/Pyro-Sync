import pandas as pd
import time
import threading
from datetime import datetime
import vlc
import TermTk as ttk

# Charger et vérifier le fichier CSV
def load_config(file_path):
    df = pd.read_csv(file_path)
    df['lines'] = df['lines'].apply(eval)  # Convertir les lignes en liste d'entiers
    return df

# Charger la piste musicale
def load_audio(file_path):
    return vlc.MediaPlayer(file_path)

# Fonction pour gérer l'exécution du timecode
def execute_timecode(config, audio, table_frame, pyro_crew_labels, reset_button, stop_event, test_mode=False, timecode_viewer=None):
    start_time = time.time()
    audio.play()  # Jouer la piste audio

    if test_mode:
        log("[Sys Inf] - [FIRE MODE ACTIVATED]", technical=True)

    def update_timecode_viewer():
        while audio.is_playing() and not stop_event.is_set():
            elapsed_time = time.time() - start_time
            minutes, seconds = divmod(elapsed_time, 60)
            timecode_viewer.setText("Timecode : "+f"{int(minutes):02}:{seconds:05.2f}")
            time.sleep(0.01)

    if timecode_viewer:
        threading.Thread(target=update_timecode_viewer, daemon=True).start()

    for index, row in config.iterrows():
        if stop_event.is_set():
            break

        timecode = row['timecode']
        district = row['district']
        lines = row['lines']
        firing_type = row['firing_type']
        target_time = start_time + timecode_to_seconds(timecode)
        
        while time.time() < target_time:
            if stop_event.is_set():
                break
            remaining_time = target_time - time.time()
            if remaining_time <= 10:  # Mettre à jour le statut à '[NEXT][WAITING]' avec un compte à rebours de 10 secondes
                update_row_status(table_frame, index, '[NEXT][WAITING]', remaining_time, ttk.TTkColor.YELLOW)
            # Mise à jour des labels PYRO CREW
            update_pyro_crew_labels(pyro_crew_labels, config, index, remaining_time)
            time.sleep(0.5)
        
        if stop_event.is_set():
            break

        update_row_status(table_frame, index, '[FIRED]', 0, ttk.TTkColor.RED, blink=True)
        if test_mode:
            log(f"[TEST MODE FIRED] {timecode} - District: {district}, Lines: {lines}, Type: {firing_type}")
        else:
            log(f"[FIRED] {timecode} - District: {district}, Lines: {lines}, Type: {firing_type}")
        update_row_status(table_frame, index, '[FIRED]', 0, ttk.TTkColor.WHITE, blink=False)
        
        # Mise à jour des labels PYRO CREW
        update_pyro_crew_labels(pyro_crew_labels, config, index + 1)

    log("[Sys Inf] - [END OF SHOW]", technical=True)
    log("[Sys Inf] - End of audio playback", technical=True)
    reset_button.setEnabled(True)  # Activer le bouton de réinitialisation

# Fonction pour convertir le timecode en secondes
def timecode_to_seconds(timecode):
    h, m, s = map(float, timecode.split(':'))
    return h * 3600 + m * 60 + s

# Logger des événements
def log(message, technical=False):
    log_viewer.append(message)
    if technical:
        log_viewer.setColor(ttk.TTkColor.CYAN)
    log_viewer.update()

# Mettre à jour le statut de la ligne dans le tableau
def update_row_status(table_frame, row_index, status_text, countdown, color, blink=False):
    status_label = table_frame.layout().itemAtPosition(row_index + 1, 5).widget()
    countdown_label = table_frame.layout().itemAtPosition(row_index + 1, 6).widget()
    status_label.setText(f"{status_text} {int(countdown)}s" if countdown > 0 else status_text)
    countdown_label.setText(f"{int(countdown)}")
    if countdown == 0:
        countdown_label.setText("")

    if blink:
        def blink_label():
            for _ in range(4):  # Clignote 4 fois
                status_label.setColor(ttk.TTkColor.WHITE if status_label.color() == ttk.TTkColor.RED else ttk.TTkColor.RED)
                time.sleep(0.5)
            status_label.setColor(color)

        threading.Thread(target=blink_label, daemon=True).start()
    else:
        status_label.setColor(color)

# Mettre à jour les labels PYRO CREW
def update_pyro_crew_labels(pyro_crew_labels, config, current_index, remaining_time=0):
    if current_index < len(config):
        row = config.iloc[current_index]
        pyro_crew_labels[0].setText(f"Current: {row['timecode']} - District: {row['district']}, Lines: {row['lines']}, Type: {row['firing_type']} - Countdown: {int(remaining_time)}s")
    else:
        pyro_crew_labels[0].setText("Current: None")
    
    if current_index + 1 < len(config):
        next_row = config.iloc[current_index + 1]
        pyro_crew_labels[1].setText(f"Next: {next_row['timecode']} - District: {next_row['district']}, Lines: {next_row['lines']}, Type: {next_row['firing_type']}")
    else:
        pyro_crew_labels[1].setText("Next: None")

# Interface utilisateur TermTk
def start_ui(config_path, audio_path):
    root = ttk.TTk()
    root.setLayout(ttk.TTkVBoxLayout())

    # Charger la configuration et l'audio
    config = load_config(config_path)

    # Ajout du texte "Aimonino Pyro" en ASCII art avec "Fireworks FiringSystem" en dessous
    ascii_art = """
     _ __              ()                 
    ' )  )             /\                 
     /--'__  , __  __ /  )  __  , ____  _.
    /   / (_/_/ (_(_)/__/__/ (_/_/ / <_(__
           /                  /           
                '                  '                     
    Lune1l Pyro - Fireworks FiringSystem v0.1.3
    """
    ascii_label = ttk.TTkLabel(text=ascii_art, alignment=ttk.TTkK.CENTER_ALIGN)
    root.layout().addWidget(ascii_label)

    # Horloge et timecode centrés
    top_frame = ttk.TTkFrame(border=False, layout=ttk.TTkGridLayout())
    clock_label = ttk.TTkLabel(text="", maxHeight=1, alignment=ttk.TTkK.CENTER_ALIGN)
    top_frame.layout().addWidget(clock_label, 0, 0, 1, 3)
    timecode_viewer = ttk.TTkLabel(text="Timecode : 00:00.00", maxHeight=1, alignment=ttk.TTkK.CENTER_ALIGN)
    top_frame.layout().addWidget(timecode_viewer, 1, 0, 1, 3)
    root.layout().addWidget(top_frame)

    # Mettre à jour l'horloge toutes les secondes
    def update_clock():
        while True:
            clock_label.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            time.sleep(1)

    clock_thread = threading.Thread(target=update_clock, daemon=True)
    clock_thread.start()

    # Tableau avec les lignes, district, type et leur état
    main_frame = ttk.TTkFrame(border=False, layout=ttk.TTkHBoxLayout())
    schedule_frame = ttk.TTkFrame(title="Fireworks Schedule", border=True, layout=ttk.TTkGridLayout(), maxHeight=40)  # Ajustement de la hauteur maximale
    headers = ['N°', 'Timecode', 'District', 'Lines', 'Type', 'Status', 'Countdown']
    col_widths = [3, 15, 8, 15, 15, 15, 10]  # Ajustement des largeurs des colonnes
    
    for col, (header, width) in enumerate(zip(headers, col_widths)):
        header_label = ttk.TTkLabel(text=header, maxWidth=width, alignment=ttk.TTkK.CENTER_ALIGN)
        schedule_frame.layout().addWidget(header_label, 0, col)

    row_offset = 1
    for index, row in config.iterrows():
        schedule_frame.layout().addWidget(ttk.TTkLabel(text=str(index+1), maxWidth=col_widths[0], alignment=ttk.TTkK.CENTER_ALIGN), row_offset + index, 0)
        schedule_frame.layout().addWidget(ttk.TTkLabel(text=row['timecode'], maxWidth=col_widths[1], alignment=ttk.TTkK.CENTER_ALIGN), row_offset + index, 1)
        schedule_frame.layout().addWidget(ttk.TTkLabel(text=row['district'], maxWidth=col_widths[2], alignment=ttk.TTkK.CENTER_ALIGN), row_offset + index, 2)
        schedule_frame.layout().addWidget(ttk.TTkLabel(text=str(row['lines']), maxWidth=col_widths[3], alignment=ttk.TTkK.CENTER_ALIGN), row_offset + index, 3)
        schedule_frame.layout().addWidget(ttk.TTkLabel(text=row['firing_type'], maxWidth=col_widths[4], alignment=ttk.TTkK.CENTER_ALIGN), row_offset + index, 4)
        status_label = ttk.TTkLabel(text='[WAITING]', maxWidth=col_widths[5], alignment=ttk.TTkK.CENTER_ALIGN)
        schedule_frame.layout().addWidget(status_label, row_offset + index, 5)
        countdown_label = ttk.TTkLabel(text='', maxWidth=col_widths[6], alignment=ttk.TTkK.CENTER_ALIGN)  # Countdown column visible
        schedule_frame.layout().addWidget(countdown_label, row_offset + index, 6)

    main_frame.layout().addWidget(schedule_frame)

    # PYRO CREW Widget
    pyro_crew_frame = ttk.TTkFrame(title="PYRO CREW", border=True, layout=ttk.TTkVBoxLayout())
    current_line_label = ttk.TTkLabel(text="Current: None")
    next_line_label = ttk.TTkLabel(text="Next: None")
    pyro_crew_frame.layout().addWidget(current_line_label)
    pyro_crew_frame.layout().addWidget(next_line_label)
    main_frame.layout().addWidget(pyro_crew_frame)

    root.layout().addWidget(main_frame)

    # Logs de déclenchement
    global log_viewer
    log_viewer = ttk.TTkTextEdit(readOnly=True)
    log_frame = ttk.TTkFrame(title="Logs", border=True, layout=ttk.TTkVBoxLayout())
    log_frame.layout().addWidget(log_viewer)
    root.layout().addWidget(log_frame)

    # Menu de commandes
    command_menu = ttk.TTkFrame(border=False, layout=ttk.TTkHBoxLayout())
    start_test_button = ttk.TTkButton(text="-- FIRE --", maxWidth=20)
    stop_button = ttk.TTkButton(text="STOP", maxWidth=20)
    reset_button = ttk.TTkButton(text="Reset", maxWidth=20, enabled=False)  # Initialement désactivé
    quit_button = ttk.TTkButton(text="Quit", maxWidth=20)
    command_menu.layout().addWidget(start_test_button)
    command_menu.layout().addWidget(ttk.TTkSpacer())
    command_menu.layout().addWidget(stop_button)
    command_menu.layout().addWidget(ttk.TTkSpacer())
    command_menu.layout().addWidget(reset_button)
    command_menu.layout().addWidget(ttk.TTkSpacer())
    command_menu.layout().addWidget(quit_button)
    root.layout().addWidget(command_menu)

    # Événements des boutons
    stop_event = threading.Event()
    audio_player = [None]  # Utilisation d'une liste pour garder une référence mutable à l'instance audio

    def on_fire():
        stop_event.clear()
        reset_button.setEnabled(False)
        reset_ui(config_path, schedule_frame)
        start_timecode_execution(config_path, audio_path, schedule_frame, [current_line_label, next_line_label], reset_button, stop_event, audio_player, test_mode=True, timecode_viewer=timecode_viewer)

    def on_stop():
        stop_event.set()
        if audio_player[0]:
            audio_player[0].stop()
        reset_button.setEnabled(True)
        log("[Sys Inf] - [STOPPED]", technical=True)

    def on_reset():
        reset_ui(config_path, schedule_frame)
        reset_button.setEnabled(False)  # Désactiver le bouton après réinitialisation
        log("[Sys Inf] - [RESET]", technical=True)

    def on_quit():
        on_stop()
        root.quit()

    start_test_button.clicked.connect(on_fire)
    stop_button.clicked.connect(on_stop)
    reset_button.clicked.connect(on_reset)
    quit_button.clicked.connect(on_quit)

    root.mainloop()

# Lancer l'exécution du timecode dans un thread séparé
def start_timecode_execution(config_path, audio_path, table_frame, pyro_crew_labels, reset_button, stop_event, audio_player, test_mode=False, timecode_viewer=None):
    config = load_config(config_path)
    audio = load_audio(audio_path)
    audio_player[0] = audio  # Stocker l'instance audio dans la liste mutable

    execution_thread = threading.Thread(target=execute_timecode, args=(config, audio, table_frame, pyro_crew_labels, reset_button, stop_event, test_mode, timecode_viewer))
    execution_thread.start()

# Fonction pour réinitialiser l'interface utilisateur
def reset_ui(config_path, table_frame):
    config = load_config(config_path)
    row_offset = 1
    for index, row in config.iterrows():
        table_frame.layout().itemAtPosition(row_offset + index, 5).widget().setText('[WAITING]')
        table_frame.layout().itemAtPosition(row_offset + index, 5).widget().setColor(ttk.TTkColor.WHITE)
        table_frame.layout().itemAtPosition(row_offset + index, 6).widget().setText('')

# Chemins vers les fichiers
config_path = 'config.csv'
audio_path = 'audio.mp3'

# Démarrer l'interface utilisateur
start_ui(config_path, audio_path)
