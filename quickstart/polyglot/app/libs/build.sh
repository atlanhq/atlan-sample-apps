#!/bin/bash

# Build script for FactorialCalculator Java class
# This script compiles the Java source code and packages it into a JAR file

set -e  # Exit on error

echo "======================================"
echo "Building Factorial Calculator JAR"
echo "======================================"

# Check if Java is installed
if ! command -v javac &> /dev/null; then
    echo "Error: javac not found. Please install Java JDK 11 or higher."
    exit 1
fi

# Display Java version
echo "Using Java version:"
java -version
echo ""

# Clean previous builds
echo "Cleaning previous builds..."
rm -f *.class
rm -f *.jar
echo "Done."
echo ""

# Compile Java source
echo "Compiling FactorialCalculator.java..."
javac FactorialCalculator.java
echo "Compilation successful."
echo ""

# Create JAR file
echo "Creating JAR file..."
jar cvf factorial-calculator.jar FactorialCalculator.class
echo "JAR created successfully."
echo ""

# Clean up class files
echo "Cleaning up class files..."
rm -f *.class
echo "Done."
echo ""

echo "======================================"
echo "Build completed successfully!"
echo "JAR location: $(pwd)/factorial-calculator.jar"
echo "======================================"

# Test the JAR
echo ""
echo "Testing the JAR file..."
java -cp factorial-calculator.jar FactorialCalculator
echo ""
echo "Test completed successfully!"

