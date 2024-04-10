import sys

def log(msg, end='\n'):
    #print(msg, end=None)
    # my terminal wasn't showing realtime updates by default, so I had to add flush
    sys.stdout.write(f'{msg}{end}')
    sys.stdout.flush()

