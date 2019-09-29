CC           = g++
CFLAGS       = -O2 

#set the following variables for custom libraries and/or other objects
EXTOBJS      =
LIBS         = -lm -pthread
LIBPATHS     = 
INCLUDEPATHS = 

PROGRAMS     = Server.cpp MemcacheExchange.h MemcacheExchange.cpp
all: $(PROGRAMS)

$(PROGRAMS): %: %.o
	$(CC) -o $@ $< $(LIBPATHS) $(CFLAGS) $(EXTOBJS) $(LIBS)

.cpp.o:
	$(CC) $(CFLAGS) $(TUNEFLAGS) $(INCLUDEPATHS) -c $<

clean:
	rm -f *.o 