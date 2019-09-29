CC           = g++
CFLAGS       = -O2 

#set the following variables for custom libraries and/or other objects
LIBS         = -lm -pthread -lstdc++fs

all: 
	$(CC) -o Server *.cpp *.h $(CFLAGS) $(LIBS)

clean:
	rm -f Server 