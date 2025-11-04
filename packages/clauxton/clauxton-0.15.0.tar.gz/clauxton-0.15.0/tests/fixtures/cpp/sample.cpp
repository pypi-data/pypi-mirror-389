// Sample C++ file for testing symbol extraction

#include <string>
#include <iostream>

/// User class
class User {
public:
    User(std::string name) : name_(name) {}
    ~User() {}

    std::string getName() const {
        return name_;
    }

    void setName(std::string name) {
        name_ = name;
    }

private:
    std::string name_;
};

/// Point struct
struct Point {
    int x;
    int y;
};

/// Utility namespace
namespace utils {
    /// Add two integers
    int add(int a, int b) {
        return a + b;
    }

    /// Max template function
    template<typename T>
    T max(T a, T b) {
        return a > b ? a : b;
    }
}

/// Global function
int multiply(int a, int b) {
    return a * b;
}
