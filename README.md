# ADSC32

Dieses Repository enthält den Code-Teil der Studienarbeit für das Modul ADSC32 Applied Data Science III: Softwareparadigmen (Exam performance). 

Der Ordner `simulation` umfasst sämtliche Python-Dateien, die zur Ausführung und Steuerung der Simulation benötigt werden:
- `funktionen.py`: Enthält alle definierten Hilfsfunktionen, welche innerhalb der Simulation verwendet werden.
- `main.py`: Startdatei zur Ausführung der gesamten Simulation.
- `parameter.py`: In dieser Datei werden die zugrundeliegenden globalen Paramter definiert.
- `simulation.py`: Diese Datei beinhaltet die gesamte Simulationslogik. 

Die in der Simulation generierten Grafiken sowie die Ergebnistabelle im CSV-Format werden im Ordner `output`  gespeichert.


### Installation

1. **Klonen Sie das Repository und wechseln Sie in das Verzeichnis**

    ```bash
    git clone git@github.com:juliisch/ADSC32.git
    ```
    ```bash
    cd ADSC32
    ```


2. **Setze eine virtuelle Umgebung auf**
    ```bash
    python3 -m venv adsc_env
    ```
    ```bash
    source adsc_env/bin/activate
    ```
    ```bash
    pip install ipykernel
    ```

    ```bash
    python -m ipykernel install --user --name=adsc_env --display-name "Python (adsc_env)"
    ```

3. **Bibliotheken installieren**

    Installieren Sie die benötigten Bibliotheken über die Datei `requirements.txt`.

    ```bash
    pip install -r requirements.txt
    ```

    Nach der Installation der Bibliotheken ist es erforderlich, das Programm neu zu starten, damit diese wirksam werden.

4. **Führen Sie das Simulation aus**

    Führen Sie die Datei `simulation/main.py` aus. Die Ausführung kann einige Minuten dauern.

    Alternativ kann auch der folgende Shell Befehlt ausgeführt werden:

    ```bash
    python simulation/main.py
    ```

