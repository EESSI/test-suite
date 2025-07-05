#
#  BLIS    
#  An object-based framework for developing high-performance BLAS-like
#  libraries.
#
#  Copyright (C) 2014, The University of Texas at Austin
#  Copyright (C) 2018, Advanced Micro Devices, Inc.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#   - Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   - Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   - Neither the name(s) of the copyright holder(s) nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
#  A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
#  HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#  SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#  LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#  DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#  THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Makefile
#
# Field G. Van Zee
#
# Makefile for standalone BLIS test drivers.
#
# Makefile adapted for FlexiBLAS by Samuel Moors (Vrije Universiteit Brussel)
#

REQUIRED_VARS = EBROOTBLIS EBROOTFLEXIBLAS CFLAGS

$(foreach var_name,$(REQUIRED_VARS),\
	$(if $(value $(var_name)),,\
		$(error variable '$(var_name)' must be set)\
	)\
)

.PHONY: all all-st all-mt all-blis all-flexiblas flexiblas-st flexiblas-mt blis-st blis-mt clean

LIB_PATH   := $(EBROOTBLIS)/lib
INC_PATH   := $(EBROOTBLIS)/include/blis

LIBBLIS_LINK := $(LIB_PATH)/libblis.a
LDFLAGS += -lm -lpthread -fopenmp -lrt

FLEXIBLAS_LIB := $(EBROOTFLEXIBLAS)/lib/libflexiblas.so

TEST_SRC_PATH  := .
TEST_OBJ_PATH  := .

# Gather all local object files.
TEST_OBJS      := $(sort $(patsubst $(TEST_SRC_PATH)/%.c, \
                                    $(TEST_OBJ_PATH)/%.o, \
                                    $(wildcard $(TEST_SRC_PATH)/*.c)))

# Override the value of CINCFLAGS so that the value of CFLAGS returned by
# get-user-cflags-for() is not cluttered up with include paths needed only
# while building BLIS.
CINCFLAGS      := -I$(INC_PATH)

# Add local header paths to CFLAGS.
CFLAGS         += -I$(TEST_SRC_PATH)

# Which library?
DEF_BLI  := -DBLIS
DEF_BLA  := -DBLAS

# Implementation string.
STR_BLI  := -DIMPL_STR=\"blis\"
STR_FBL  := -DIMPL_STR=\"flexiblas\"

# Single or multithreaded string.
STR_ST   := -DTHR_STR=\"st\"
STR_MT   := -DTHR_STR=\"mt\"

# Targets/rules
all:      all-st all-mt

all-st:   blis-st flexiblas-st
all-mt:   blis-mt flexiblas-mt

all-blis:     blis-st blis-mt
all-flexiblas: flexiblas-st flexiblas-mt

# Define the datatypes, operations, and implementations.
OPS    := gemm hemm herk trmm trsm
BIMPLS := blis flexiblas

# Define a function to construct object filenames from the operations
# given an implementation.
get-st-objs = $(foreach op,$(OPS),test_$(op)_$(1)_st.o)
get-mt-objs = $(foreach op,$(OPS),test_$(op)_$(1)_mt.o)

# Construct object and binary names for single-threaded and multithreaded
# files for BLIS, OpenBLAS, Eigen, and a vendor library (e.g. MKL).
BLIS_ST_OBJS     := $(call get-st-objs,blis)
BLIS_ST_BINS     := $(patsubst %.o,%.x,$(BLIS_ST_OBJS))

BLIS_MT_OBJS     := $(call get-mt-objs,blis)
BLIS_MT_BINS     := $(patsubst %.o,%.x,$(BLIS_MT_OBJS))

FLEXIBLAS_ST_OBJS := $(call get-st-objs,flexiblas)
FLEXIBLAS_ST_BINS := $(patsubst %.o,%.x,$(FLEXIBLAS_ST_OBJS))

FLEXIBLAS_MT_OBJS := $(call get-mt-objs,flexiblas)
FLEXIBLAS_MT_BINS := $(patsubst %.o,%.x,$(FLEXIBLAS_MT_OBJS))

# List other miscellaneous object files
UTIL_OBJS        := test_utils.o
UTIL_HDRS        := test_utils.h

# Define some targets associated with the above object/binary files.
blis-st:     $(BLIS_ST_BINS)
blis-mt:     $(BLIS_MT_BINS)
flexiblas-st: $(FLEXIBLAS_ST_BINS)
flexiblas-mt: $(FLEXIBLAS_MT_BINS)

# Mark the object files as intermediate so that make will remove them
# automatically after building the binaries on which they depend.
.INTERMEDIATE: $(BLIS_ST_OBJS)     $(BLIS_MT_OBJS)
.INTERMEDIATE: $(FLEXIBLAS_ST_OBJS) $(FLEXIBLAS_MT_OBJS)
.INTERMEDIATE: $(UTIL_OBJS)

# -- Object file rules --

# A function to return other cpp macros that help the test driver
# identify the implementation.
get-bl-cpp = $(strip \
             $(if $(findstring     blis,$(1)),$(STR_BLI) $(DEF_BLI),\
             $(if $(findstring flexiblas,$(1)),$(STR_FBL) $(DEF_BLA),\
             $(if $(and $(findstring eigen,$(1)),\
                        $(findstring  gemm,$(2))),\
                                              $(STR_EIG) $(DEF_EIG),\
             $(if       $(findstring eigen,$(1)),\
                                              $(STR_EIG) $(DEF_BLA),\
                                              $(STR_VEN) $(DEF_BLA))))))

# Rules for miscellaneous files.
test_utils.o: test_utils.c test_utils.h
	$(CC) $(CFLAGS) -c $< -o $@

# Rules for BLIS and BLAS libraries.
define make-st-rule
test_$(1)_$(2)_st.o: test_$(op).c Makefile
	$(CC) $(CFLAGS) $(call get-bl-cpp,$(2),$(1)) $(STR_ST) -c $$< -o $$@
endef

define make-mt-rule
test_$(1)_$(2)_mt.o: test_$(op).c Makefile
	$(CC) $(CFLAGS) $(call get-bl-cpp,$(2),$(1)) $(STR_MT) -c $$< -o $$@
endef

$(foreach op,$(OPS), \
$(foreach im,$(BIMPLS),$(eval $(call make-st-rule,$(op),$(im)))))

$(foreach op,$(OPS), \
$(foreach im,$(BIMPLS),$(eval $(call make-mt-rule,$(op),$(im)))))

# -- Executable file rules --

# NOTE: For the BLAS test drivers, we place the BLAS libraries before BLIS
# on the link command line in case BLIS was configured with the BLAS
# compatibility layer. This prevents BLIS from inadvertently getting called
# for the BLAS routines we are trying to test with.

# Combine the miscellaneous objects with libblis for conciseness (since all
# driver binaries depend on these objects).
COMMON_OBJS := $(UTIL_OBJS) $(LIBBLIS_LINK)

test_%_blis_st.x:     test_%_blis_st.o     $(COMMON_OBJS)
	$(CC) $(strip $<                    $(COMMON_OBJS) $(LDFLAGS) -o $@)

test_%_blis_mt.x:     test_%_blis_mt.o     $(COMMON_OBJS)
	$(CC) $(strip $<                    $(COMMON_OBJS) $(LDFLAGS) -o $@)

test_%_flexiblas_st.x: test_%_flexiblas_st.o $(COMMON_OBJS)
	$(CC) $(strip $<   $(FLEXIBLAS_LIB)  $(COMMON_OBJS) $(LDFLAGS) -o $@)

test_%_flexiblas_mt.x: test_%_flexiblas_mt.o $(COMMON_OBJS)
	$(CC) $(strip $<   $(FLEXIBLAS_LIB) $(COMMON_OBJS) $(LDFLAGS) -o $@)

clean:
	- rm -f *.o *.x

