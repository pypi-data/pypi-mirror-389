CC := g++
CCFLAGS_COMMON := -Wall -Wextra -MMD -fopenmp
CCFLAGS_RELEASE := -O2
CCFLAGS_DEBUG := -g -O0 -DDEBUG
CCFLAGS_ASAN := -g -O1 -DDEBUG -fsanitize=address -fno-omit-frame-pointer
CCFLAGS := ${CCFLAGS_COMMON} ${CCFLAGS_RELEASE}
LDFLAGS := ${LDFLAGS} -fopenmp
LDFLAGS_ASAN := ${LDFLAGS} -fsanitize=address

OBJDIR := build
DNNDIR := dnn
BINDIR := bin
TARGET := $(BINDIR)/run_export
DEBUG_OBJDIR := build_debug
DEBUG_TARGET := $(BINDIR)/run_export_debug
ASAN_OBJDIR := build_asan
ASAN_TARGET := $(BINDIR)/run_export_asan

# Export Params
AIDGE_CMP := false		# Compare fmaps with Aidge ref
SAVE_OUTPUTS := false	# Store fmaps into files

ifeq ($(AIDGE_CMP), true)
	PRMFLAGS := ${PRMFLAGS} -DAIDGE_CMP
endif

ifeq ($(SAVE_OUTPUTS), true)
	PRMFLAGS := ${PRMFLAGS} -DSAVE_OUTPUTS
endif

INCLUDE_DIRS :=-I. -I./${DNNDIR} -I./${DNNDIR}/include -I./${DNNDIR}/layers -I./${DNNDIR}/parameters
CC_SRCS := $(shell find . -iname "*.cpp")
CC_OBJS := $(patsubst %.cpp, ${OBJDIR}/%.o, ${CC_SRCS})
DEBUG_OBJS := $(patsubst %.cpp, ${DEBUG_OBJDIR}/%.o, ${CC_SRCS})
ASAN_OBJS := $(patsubst %.cpp, ${ASAN_OBJDIR}/%.o, ${CC_SRCS})
DEPENDENCIES := $(patsubst %.o, %.d, ${CC_OBJS})
DEBUG_DEPENDENCIES := $(patsubst %.o, %.d, ${DEBUG_OBJS})
ASAN_DEPENDENCIES := $(patsubst %.o, %.d, ${ASAN_OBJS})

.PHONY: all build debug asan clean

all: build

build: ${CC_OBJS}
	@mkdir -p $(dir ${TARGET})
	${CC} ${CC_OBJS} ${LDFLAGS} -o ${TARGET}

debug: CCFLAGS := ${CCFLAGS_COMMON} ${CCFLAGS_DEBUG}
debug: ${DEBUG_OBJS}
	@mkdir -p $(dir ${DEBUG_TARGET})
	${CC} ${DEBUG_OBJS} ${LDFLAGS} -o ${DEBUG_TARGET}

asan: CCFLAGS := ${CCFLAGS_COMMON} ${CCFLAGS_ASAN}
asan: ${ASAN_OBJS}
	@mkdir -p $(dir ${ASAN_TARGET})
	${CC} ${ASAN_OBJS} ${LDFLAGS_ASAN} -o ${ASAN_TARGET}

${OBJDIR}/%.o: %.cpp
	@mkdir -p $(dir $@)
	${CC} ${CCFLAGS} ${PRMFLAGS} ${INCLUDE_DIRS} -c $< -o $@ 

${DEBUG_OBJDIR}/%.o: %.cpp
	@mkdir -p $(dir $@)
	${CC} ${CCFLAGS} ${PRMFLAGS} ${INCLUDE_DIRS} -c $< -o $@ 

${ASAN_OBJDIR}/%.o: %.cpp
	@mkdir -p $(dir $@)
	${CC} ${CCFLAGS} ${PRMFLAGS} ${INCLUDE_DIRS} -c $< -o $@ 

clean:
	if [ -d "$(OBJDIR)" ]; then rm -rf $(OBJDIR); fi
	if [ -d "$(DEBUG_OBJDIR)" ]; then rm -rf $(DEBUG_OBJDIR); fi
	if [ -d "$(ASAN_OBJDIR)" ]; then rm -rf $(ASAN_OBJDIR); fi
	if [ -d "$(BINDIR)" ]; then rm -rf $(BINDIR); fi


-include $(DEPENDENCIES)
-include $(DEBUG_DEPENDENCIES)
-include $(ASAN_DEPENDENCIES)
