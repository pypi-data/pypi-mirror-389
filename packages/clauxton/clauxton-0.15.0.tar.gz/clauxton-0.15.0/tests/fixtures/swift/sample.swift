import Foundation

/// User model representing a user in the system
class User {
    var name: String
    var email: String

    init(name: String, email: String) {
        self.name = name
        self.email = email
    }

    func greet() -> String {
        return "Hello, \(name)!"
    }

    static func create(name: String, email: String) -> User {
        return User(name: name, email: email)
    }
}

/// Point structure for 2D coordinates
struct Point {
    var x: Int
    var y: Int

    func distance(to other: Point) -> Double {
        let dx = Double(x - other.x)
        let dy = Double(y - other.y)
        return sqrt(dx * dx + dy * dy)
    }
}

/// Direction enumeration
enum Direction {
    case north
    case south
    case east
    case west
}

/// Greetable protocol for objects that can greet
protocol Greetable {
    func greet() -> String
}

/// Extension adding Greetable conformance to User
extension User: Greetable {}

/// Helper function for text processing
func formatText(text: String) -> String {
    return text.uppercased()
}

/// Calculate sum of two numbers
func calculateSum(a: Int, b: Int) -> Int {
    return a + b
}
