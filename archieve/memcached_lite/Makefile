CC           = g++
CFLAGS       = -O2 -std=c++11

#set the following variables for custom libraries and/or other objects
LIBS         = -lm -pthread 

all: 
	$(CC) -o Server *.cpp *.h $(CFLAGS) $(LIBS)

clean:
	rm -f Server 