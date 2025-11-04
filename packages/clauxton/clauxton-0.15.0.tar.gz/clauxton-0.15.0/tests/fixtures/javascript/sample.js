/**
 * Sample JavaScript file for testing symbol extraction.
 */

// ES6 Class
class Calculator {
  constructor(name) {
    this.name = name;
  }

  add(a, b) {
    return a + b;
  }

  multiply(a, b) {
    return a * b;
  }
}

// Regular function
function factorial(n) {
  if (n <= 1) return 1;
  return n * factorial(n - 1);
}

// Arrow function (const)
const square = (x) => x * x;

// Arrow function (let)
let double = (x) => x * 2;

// Async function
async function fetchData(url) {
  const response = await fetch(url);
  return response.json();
}

// Function expression
const greet = function(name) {
  return `Hello, ${name}!`;
};

// Export
export { Calculator, factorial, square };
