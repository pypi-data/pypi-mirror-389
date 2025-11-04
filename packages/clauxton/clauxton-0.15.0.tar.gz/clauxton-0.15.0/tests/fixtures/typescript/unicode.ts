/**
 * Unicode test file (日本語)
 */

// Function with Japanese name
function こんにちは(名前: string): string {
  return `こんにちは、${名前}さん！`;
}

// Interface with emoji
interface 😀Emoji {
  message: string;
  greet(): string;
}

// Class with emoji
class 🎉Celebration implements 😀Emoji {
  constructor(public message: string) {}

  greet(): string {
    return `${this.message} 🎉`;
  }
}

export { こんにちは, 😀Emoji, 🎉Celebration };
