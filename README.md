# AC Telemetry
A tool for recording and analyzing Assetto Corsa telemetry:  
comparing laps against a reference lap based on distance, and calculating time lost in individual corners.

Reads telemetry from shared memory, segments laps, aligns them to a common grid, and calculates the time delta relative to a reference lap.  
Currently, it does not yet correctly identify corners.  

Was tested on Monza.  

Requirements:  
only windows  
python 3.10+  
'pip install -r requirements.txt'  


HOW 2 RUN:  
launch the game and get on the track (any car, make sure the track have tag "circuit")
python ac_record.py — record (to stop press Ctrl + C), will create `session_*.csv`
python plot_lap.py session_*.csv 2` — selected lap plot (2nd lap given as example)
python analyze_laps.py session_*.csv` — compare laps and delta
python corners.py session_*.csv` — _time loss on corner_  

Also make sure you dont cut the track cuz comparing would not be correct.
