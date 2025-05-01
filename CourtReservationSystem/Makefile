
CXX?=g++
CXXFLAGS=-std=c++20 -Wall -Wextra -pedantic -Iinclude
SRC=$(wildcard src/*.cpp)
OBJ=$(SRC:.cpp=.o)
TARGET=reservation_system

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CXX) $(CXXFLAGS) -o $@ $^

clean:
	rm -f $(OBJ) $(TARGET)
