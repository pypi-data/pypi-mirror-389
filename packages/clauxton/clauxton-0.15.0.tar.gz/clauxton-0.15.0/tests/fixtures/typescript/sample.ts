/**
 * Sample TypeScript file for testing symbol extraction.
 */

// Interface
interface Calculator {
  add(a: number, b: number): number;
  multiply(a: number, b: number): number;
}

// Type alias
type Operation = 'add' | 'subtract' | 'multiply' | 'divide';

// Class with types
class MathService implements Calculator {
  constructor(private precision: number = 2) {}

  add(a: number, b: number): number {
    return a + b;
  }

  multiply(a: number, b: number): number {
    return a * b;
  }

  async calculate(op: Operation, a: number, b: number): Promise<number> {
    switch (op) {
      case 'add': return this.add(a, b);
      case 'multiply': return this.multiply(a, b);
      default: throw new Error('Unsupported');
    }
  }
}

// Regular function with types
function factorial(n: number): number {
  if (n <= 1) return 1;
  return n * factorial(n - 1);
}

// Arrow function with types
const square = (x: number): number => x * x;

// Generic function
function identity<T>(arg: T): T {
  return arg;
}

// Export
export { MathService, factorial, Calculator };
