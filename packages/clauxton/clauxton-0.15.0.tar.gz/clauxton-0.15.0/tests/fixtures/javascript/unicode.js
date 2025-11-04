/**
 * Unicode test file (日本語)
 */

// Function with Japanese comments
function こんにちは(名前) {
  return `こんにちは、${名前}さん！`;
}

// Class with emoji
class 😀Emoji {
  constructor(message) {
    this.message = message;
  }

  greet() {
    return `${this.message} 🎉`;
  }
}

export { こんにちは, 😀Emoji };
