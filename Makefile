UNAME_S := $(shell uname -s)

pathInc = -I./src
Libs = `sdl2-config --cflags`
DLibs = `sdl2-config --libs`

ifeq ($(UNAME_S), Darwin)
    Libs += -D_MACOSX
endif

ifeq ($(UNAME_S), Linux)
    Libs += -DLINUX
    pathInc += -I/usr/include/directfb/direct -I/usr/include/directfb
endif

ifeq ($(UNAME_S), FreeBSD)
    Libs += -DFREEBSD
endif
 
CC = g++ -c -Wall $(pathInc) $(Libs)
LD = g++ obj/*.o $(DLibs)

all : obj_dir vic sid graphics castle main creep

obj_dir:
	mkdir -p obj

vic:
	$(CC) src/vic-ii/bitmapMulticolor.cpp src/vic-ii/screen.cpp src/vic-ii/sprite.cpp
	mv *.o obj/

sid:
	$(CC) src/sound/sound.cpp src/resid-0.16/*.cpp
	mv *.o obj/

graphics :
	$(CC) src/graphics/screenSurface.cpp src/graphics/window.cpp
	mv *.o obj/

castle :
	$(CC) src/castle/castle.cpp  src/castle/room.cpp src/castle/objects/*.cpp 
	mv *.o obj/

main :
	$(CC) src/castleManager.cpp src/stdafx.cpp src/creep.cpp src/d64.cpp src/debug.cpp src/builder.cpp src/playerInput.cpp src/Event.cpp src/Menu.cpp src/Steam.cpp
	mv *.o obj/

creep :
	$(LD) -o run/creep

clean :
	rm -rf obj/
	rm -f run/creep
