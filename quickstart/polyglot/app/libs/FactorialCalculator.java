/**
 * FactorialCalculator - A simple Java class for the Polyglot demo.
 * 
 * This class provides methods to calculate factorial of numbers and is called from
 * Python code using JPype to demonstrate polyglot programming (cross-language integration).
 */
public class FactorialCalculator {
    
    /**
     * Calculate the factorial of a given number.
     * 
     * @param n The number to calculate factorial for
     * @return The factorial of n as a long
     * @throws IllegalArgumentException if n is negative
     */
    public static long calculateFactorial(int n) {
        if (n < 0) {
            throw new IllegalArgumentException("Number must be non-negative. Got: " + n);
        }
        
        if (n == 0 || n == 1) {
            return 1;
        }
        
        // Check for overflow potential (factorial of 21 exceeds long max)
        if (n > 20) {
            throw new IllegalArgumentException(
                "Number too large. Maximum supported value is 20 to prevent overflow. Got: " + n
            );
        }
        
        long result = 1;
        for (int i = 2; i <= n; i++) {
            result *= i;
        }
        
        return result;
    }
    
    /**
     * Get the version of this calculator.
     * 
     * @return Version string
     */
    public static String getVersion() {
        return "1.0.0";
    }
    
    /**
     * Get a description of this calculator.
     * 
     * @return Description string
     */
    public static String getDescription() {
        return "Simple Factorial Calculator for Polyglot Demo";
    }
    
    /**
     * Main method for testing the calculator independently.
     * 
     * @param args Command line arguments
     */
    public static void main(String[] args) {
        System.out.println("Factorial Calculator v" + getVersion());
        System.out.println(getDescription());
        System.out.println();
        
        // Test some factorial calculations
        int[] testNumbers = {0, 1, 5, 10, 15, 20};
        
        for (int n : testNumbers) {
            try {
                long result = calculateFactorial(n);
                System.out.println("Factorial of " + n + " = " + result);
            } catch (IllegalArgumentException e) {
                System.out.println("Error for " + n + ": " + e.getMessage());
            }
        }
    }
}

