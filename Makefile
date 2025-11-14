# Makefile for toy compiler
.PHONY: help build-docker build run clean test

# Docker image name
IMAGE_NAME = toy-compiler

# Default target
help:
	@echo "Toy Compiler - Makefile Commands"
	@echo "================================="
	@echo ""
	@echo "Setup:"
	@echo "  make build-docker    Build the Docker image with NASM and ld"
	@echo ""
	@echo "Build & Run:"
	@echo "  make build          Compile example in Docker (examples/arithmetic.toy)"
	@echo "  make run            Run the compiled program in Docker"
	@echo "  make compile FILE=<path> NAME=<name>"
	@echo "                      Compile specific toy file"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          Remove build artifacts"
	@echo ""
	@echo "Examples:"
	@echo "  make compile FILE=examples/hello.toy NAME=hello"
	@echo "  make run NAME=hello"

# Build Docker image
build-docker:
	@echo "Building Docker image: $(IMAGE_NAME)..."
	docker build -t $(IMAGE_NAME) .
	@echo "Done! Image '$(IMAGE_NAME)' is ready."

# Default compile target (arithmetic example)
build: build-docker
	@echo "Compiling examples/arithmetic.toy..."
	docker run --rm -v "$$(pwd):/workspace" $(IMAGE_NAME) sh -c "./compile.sh examples/arithmetic.toy arithmetic"

# Compile specific file
compile: build-docker
	@if [ -z "$(FILE)" ]; then \
		echo "Error: FILE not specified. Usage: make compile FILE=path/to/file.toy NAME=output"; \
		exit 1; \
	fi
	@NAME=$${NAME:-program}; \
	echo "Compiling $(FILE) -> build/$$NAME..."; \
	docker run --rm -v "$$(pwd):/workspace" $(IMAGE_NAME) sh -c "./compile.sh $(FILE) $$NAME"

# Run compiled program (default: arithmetic)
run:
	@NAME=$${NAME:-arithmetic}; \
	echo "Running build/$$NAME..."; \
	docker run --rm -v "$$(pwd):/workspace" $(IMAGE_NAME) build/$$NAME; \
	echo "Exit code: $$?"

# Run program and check exit code
test: build
	@echo "Testing compiled program..."
	@docker run --rm -v "$$(pwd):/workspace" $(IMAGE_NAME) build/arithmetic; \
	EXIT_CODE=$$?; \
	echo "Exit code: $$EXIT_CODE"; \
	if [ $$EXIT_CODE -eq 0 ]; then \
		echo "Test passed!"; \
	else \
		echo "Test failed!"; \
		exit 1; \
	fi

# Clean build artifacts
clean:
	@echo "Cleaning build directory..."
	rm -rf build/*.asm build/*.o build/arithmetic build/hello build/program
	@echo "Clean complete."

# Interactive Docker shell for debugging
shell: build-docker
	docker run --rm -it -v "$$(pwd):/workspace" $(IMAGE_NAME) /bin/sh
