# run usage

`python server.py`

# build exe

`pyinstaller --onefile --icon=_images/logo.ico server.py`

# build exe senza terminale

`pyinstaller --onefile --noconsole --icon=_images/logo.ico server.py`


-----------------------------------------------------------------------

# Exe usage
## DEFAULT (versione potente che va con molti robot)
`start server.exe`

oppure 

`start server.exe --no-iodebug`

## VERISIONE DEBUG
`start server.exe --iodebug`