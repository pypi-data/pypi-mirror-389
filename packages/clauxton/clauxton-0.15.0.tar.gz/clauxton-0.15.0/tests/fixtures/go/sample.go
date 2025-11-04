// Sample Go file for testing symbol extraction.
package main

import "fmt"

// User represents a user in the system
type User struct {
	Name string
	Age  int
}

// Reader defines the Read interface
type Reader interface {
	Read(p []byte) (n int, err error)
	Close() error
}

// Status represents operation status
type Status string

// Add adds two integers
func Add(a, b int) int {
	return a + b
}

// Multiply multiplies two integers
func Multiply(a, b int) int {
	return a * b
}

// GetName returns the user's name
func (u *User) GetName() string {
	return u.Name
}

// SetName sets the user's name
func (u *User) SetName(name string) {
	u.Name = name
}

// Generic function (Go 1.18+)
func Identity[T any](x T) T {
	return x
}
