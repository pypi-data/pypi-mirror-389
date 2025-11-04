// Unicode test file (日本語)
package main

// こんにちは greets with Japanese
func こんにちは(名前 string) string {
	return "こんにちは、" + 名前 + "さん！"
}

// 😀Emoji represents an emoji interface
type 😀Emoji interface {
	Greet() string
}

// 🎉Celebration implements Emoji
type 🎉Celebration struct {
	Message string
}

func (c *🎉Celebration) Greet() string {
	return c.Message + " 🎉"
}
