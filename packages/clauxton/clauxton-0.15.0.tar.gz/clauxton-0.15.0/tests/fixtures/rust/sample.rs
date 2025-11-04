// Sample Rust file for testing symbol extraction

/// User struct with name and age
pub struct User {
    pub name: String,
    pub age: u32,
}

/// Status enum
pub enum Status {
    Ok,
    Error(String),
    Pending,
}

/// Display trait
pub trait Display {
    fn fmt(&self) -> String;
}

/// Type alias for Result
pub type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;

/// Add two numbers
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}

/// Multiply two numbers with generics
pub fn multiply<T: std::ops::Mul<Output = T> + Copy>(a: T, b: T) -> T {
    a * b
}

/// User implementation
impl User {
    /// Create a new user
    pub fn new(name: String, age: u32) -> Self {
        User { name, age }
    }

    /// Get user name (immutable reference)
    pub fn get_name(&self) -> &str {
        &self.name
    }

    /// Set user name (mutable reference)
    pub fn set_name(&mut self, name: String) {
        self.name = name;
    }

    /// Consume user and return name (move self)
    pub fn into_name(self) -> String {
        self.name
    }
}

/// Display implementation for User
impl Display for User {
    fn fmt(&self) -> String {
        format!("{} ({})", self.name, self.age)
    }
}
