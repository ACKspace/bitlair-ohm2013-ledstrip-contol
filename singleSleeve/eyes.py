#!/usr/bin/env python3

import time
import threading
import sys
sys.path.append('../lib')
from strip import *
import random;

import termios, fcntl
fd = sys.stdin.fileno()

width, height = 1,1
oldterm = termios.tcgetattr(fd)
newattr = termios.tcgetattr(fd)
newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO


broker = "192.168.83.50"

# Set terminal settings
termios.tcsetattr(fd, termios.TCSANOW, newattr)
oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

lock = threading.RLock()

e = None
off = [ 0, 0, 0 ]
on = [ 64, 64, 30 ]
on = [ 2, 2, 1 ]

def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    e.cleanup()

class Eye():
    def __init__(self, strip2D, position, color = on, distance = 0):
        self.strip2D = strip2D
        self.position = position
        self.color = color
        self.distance = distance
        self.evil = 0
        self.thread = None
        self.awake = False
        self.draw( off )

    def relocate(self, position):
        self.draw( off )
        self.position = position
        
    def draw(self, color):
        lock.acquire()
        self.strip2D.strip.set( self.position, color )
        self.strip2D.strip.set( self.position + self.distance + 1, color )
        self.strip2D.send()
        lock.release()
  
    def sleep(self, grace = 2.0):
        self.awake = False
    
        # Fall asleep within grace period
        nextThink = random.uniform( 0.0, grace )
        print( "going to sleep in", nextThink )
        
        if ( self.thread ):
            self.thread.cancel()
        self.thread = threading.Timer( nextThink, self.close )
        self.thread.start()

    def wakeup(self, grace = 10.0):
        # Wakeup within grace period
        nextThink = random.uniform( 0.0, grace )
        
        #if ( self.thread ):
        #    self.thread.cancel()
        #self.thread = threading.Timer( nextThink, self.open )
        #self.thread.start()
        if ( not self.thread or not self.awake ):
            print( "waking up in ", nextThink )
            self.thread = threading.Timer( nextThink, self.open )
            self.thread.start()

    def crossover(self, grace = 2.0):
        # Wakeup within grace period
        nextThink = random.uniform( 0.0, grace )
        self.evil = 1

        if ( not self.thread or not self.awake ):
            print( "crossing over in ", nextThink )
            self.thread = threading.Timer( nextThink, self.open )
            self.thread.start()
        else:
            r = int(self.color[0] * (1-self.evil) + 255 * self.evil)
            g = int(self.color[0] * (1-self.evil))
            b = int(self.color[0] * (1-self.evil))
            color = [ r, g, b ]   
            time.sleep( nextThink )         
            self.draw( color )
    
    def open(self):
        self.awake = True
        print( "open" )
        r = int(self.color[0] * (1-self.evil) + 255 * self.evil)
        g = int(self.color[0] * (1-self.evil))
        b = int(self.color[0] * (1-self.evil))
        
        color = [ r, g, b ]    
    
        self.draw( color )

        if ( self.thread ):
            self.thread.cancel()
        self.thread = threading.Timer( random.uniform(1, 10), self.blink )
        self.thread.start()

    def close(self):
        print( "close" )


        if ( self.thread ):
            self.thread.cancel()
            self.thread = None

        self.draw( off )
        self.awake = False

        # Debugging:
        time.sleep( 0.2 )
        if( self.thread and self.thread.is_alive() ):
            self.thread.raise_exception() 
            

    def blink(self):
        # Since this thread can run longer (blink delay), start the thread first
        # so it can be canceled by close within the delay
        self.thread = threading.Timer( random.uniform(1, 10), self.blink )
        self.thread.start()

        self.draw( off )
        time.sleep( random.uniform(0.05, 0.3) )
    
        r = int(self.color[0] * (1-self.evil) + 255 * self.evil)
        g = int(self.color[0] * (1-self.evil))
        b = int(self.color[0] * (1-self.evil))
        
        color = [ r, g, b ]    
    
        self.draw( color )
    
        if random.randint( 0, 50 ) == 0:
            print( "double blink!" )
            time.sleep( random.uniform(0.05, 0.3) )
            self.draw( off )
            time.sleep( random.uniform(0.05, 0.3) )
            self.draw( color )

        # reset evil after blink
        self.evil = 0


class Eyes(Effect):

    def __init__(self, strip2D, pairs, distance):
        super(Eyes, self).__init__(strip2D)
        self.strip2D.strip.clear()
        self.pairs = pairs
        self.distance = distance

    def run(self, runtime = None):
        if ( runtime == None ):
            if ( hasattr( sys, "maxint" ) ): # Python 2
                runtime = sys.maxint
            elif ( hasattr( sys, "maxsize" ) ): # Python 3
                runtime = sys.maxsize
    
        eyes = []
    
        freespots = list( range( 0, self.strip2D.strip.length - self.distance - 1 ) )
    
        for i in range( self.pairs ):
            #freespots.remove( n )
            location = random.choice( freespots )
            #location = random.randint( 0, self.strip2D.strip.length )
            for s in range( location, location + self.distance + 1 ):
                try:
                    freespots.remove( s )
                except: pass

            eyes.append( Eye( self.strip2D, location, on, self.distance ) )

        for eye in eyes:
            eye.wakeup()


        then = now = time.time()
        
        offset = 0
        mode = "sleep"
        
        signal.signal(signal.SIGINT, signal_handler)
        #client.on_message = on_mqtt_message
        
        nextMode = now + random.randint( 2, 30 )
        while (not self.quit) and ((now-then) < runtime):
            now = time.time()
          
            #if ( nextMode < now ):
            #    nextMode = now + random.randint( 2, 30 )
            #    mode = random.choice( [ "sleep", "guard", "wakeup" ] )
            #    print( "mode", mode ) 
            try:
                c = sys.stdin.read(1)
                if c == '\x1b' or c == "q" or c == "Q":
                    self.cleanup()
                    
                elif c == " ":
                    print( "relocate" )
                    eye = random.choice( eyes )
                    location = random.choice( list( range( 0, self.strip2D.strip.length - self.distance - 1 ) ) )
                    eye.relocate( location )
                
                elif c == "w":
                    print( "wakeup" )
                    for eye in eyes:
                        eye.wakeup()
                        
                elif c == "W":
                    print( "wakeup!" )
                    for eye in eyes:
                        eye.wakeup( 1 )
                        
                elif c == "o" or c == "O":
                    print( "open!" )
                    for eye in eyes:
                        eye.open()
                    
                elif c == "s":
                    print( "sleep" )
                    for eye in eyes:
                        eye.sleep()
                        
                elif c == "S":
                    print( "sleep!" )
                    for eye in eyes:
                        eye.sleep( 1 )
                        
                elif c == "c" or c == "C":
                    print( "close!" )
                    for eye in eyes:
                        eye.close()
              
                elif c == "e":
                    print( "todo: random evil" )
                    eye = random.choice( eyes )
                    eye.evil = 1
                    eye.wakeup( 0.5 )
                  
                elif c == "E":
                    print( "todo: all evil" )
                    for eye in eyes:
                        eye.crossover( 0.2 )
                elif c:
                    print("Got character", repr(c), c)
                        
            except IOError: pass
          
            time.sleep( 0.1 );

        self.quit = False
        for eye in eyes:
            eye.close()
        
        sys.exit(0)
    
    def cleanup(self):
        self.quit = True
        print( "cleanup" )
        #client.unsubscribe( "home/groundfloor/entrance/hallway/stat/POWER3" )
        #client.unsubscribe( "cmnd/mancave-melder/POWER1" )
        #client.unsubscribe( "cmnd/steeg-melder/POWER1" )
        #client.disconnect()
        #client.loop_stop()

        termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
        fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)

        self.quit = True


"""
./eyes.py [pairs [distance]] addr=192.168.1.255
./eyes.py [pairs [distance] 'addr=[("192.168.1.255", ), ("localhost", 7000)]'
./eyes.py [pairs [distance] 'addr=[("192.168.1.255", 6454), ("localhost", 7000)]'
"""

if __name__ == "__main__":
    pairs = 5
    distance = 2
    if (len(sys.argv) >= 2):
        pairs = int( sys.argv[1] )
    if (len(sys.argv) >= 3):
        distance = int( sys.argv[2] )

    e = Eyes(Strip2D(10, 10), pairs, distance)
    e.run()


