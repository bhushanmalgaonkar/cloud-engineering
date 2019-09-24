CC           = g++
CFLAGS       = -O2

#set the following variables for custom libraries and/or other objects
EXTOBJS      =
LIBS         = -lm -lcurl
LIBPATHS     = 
INCLUDEPATHS = 

PROGRAMS     = server
all: $(PROGRAMS)

$(PROGRAMS): %: %.o
	$(CC) -o $@ $< $(LIBPATHS) $(CFLAGS) $(EXTOBJS) $(LIBS)

.c.o:
	$(CC) $(CFLAGS) $(TUNEFLAGS) $(INCLUDEPATHS) -c $<

clean:
	rm -f $(PROGRAMS) *.o *~