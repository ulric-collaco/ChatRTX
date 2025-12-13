# status.py
### init
this sets up the status modes message and progress in a dict\
default is idle with progress zero

### update
helps update the state\
calls notify listeners

### notify listeners
data is formatted as an sse and is looped to every active listener

### listen
this is used to add a llistener
