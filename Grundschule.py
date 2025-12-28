import random


max_Anzahl = 30
min_bewerber = 50
max_bewerber = 120

# Ausgangssituation
classes = [3,3,3,3]
pupils = [90,90,90,90]

anzahl_abgeschlossen = []

for i in range(21): # 20 Jahre
    print(f"Jahr {i}")
    anzahl_bewerber = random.randint(min_bewerber, max_bewerber)
    print(f"Anzahl Bewerber: {anzahl_bewerber}")

    if anzahl_bewerber >= random.randint(90, 250): # int(random.gauss(100,25))
        anzahl_klassen = 4
    else:
        anzahl_klassen = 3

    anzahl_schueler_temp = max(anzahl_klassen * max_Anzahl,anzahl_bewerber)
    print(f"Anzahl Schueler: {anzahl_schueler_temp}")

    abgeschlossen = pupils[-1]
    anzahl_abgeschlossen.append((i, abgeschlossen)) 

    pupils.pop(0)
    pupils.append(anzahl_schueler_temp)
    classes.pop(0)
    classes.append(anzahl_klassen)

    print(f"Schüler {pupils}")
    print(f"Klasse {classes}")
    print("")