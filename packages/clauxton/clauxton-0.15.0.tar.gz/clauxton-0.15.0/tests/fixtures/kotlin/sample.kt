package com.example.sample

import kotlin.math.sqrt

/**
 * User data class representing a user in the system
 */
data class User(
    val name: String,
    val email: String,
    val age: Int
) {
    fun greet(): String {
        return "Hello, $name!"
    }

    companion object {
        fun create(name: String, email: String): User {
            return User(name, email, 0)
        }
    }
}

/**
 * Point structure for 2D coordinates
 */
data class Point(val x: Int, val y: Int) {
    fun distanceTo(other: Point): Double {
        val dx = (x - other.x).toDouble()
        val dy = (y - other.y).toDouble()
        return sqrt(dx * dx + dy * dy)
    }
}

/**
 * Direction enum
 */
enum class Direction {
    NORTH, SOUTH, EAST, WEST
}

/**
 * Greetable interface
 */
interface Greetable {
    fun greet(): String
}

/**
 * Admin class extending User and implementing Greetable
 */
class Admin(name: String, email: String) : User(name, email, 0), Greetable {
    var permissions: List<String> = emptyList()

    override fun greet(): String {
        return "Hello Admin, $name!"
    }
}

/**
 * Sealed class for API response
 */
sealed class ApiResponse {
    data class Success(val data: String) : ApiResponse()
    data class Error(val message: String) : ApiResponse()
    object Loading : ApiResponse()
}

/**
 * Generic Box class
 */
class Box<T>(val value: T) {
    fun get(): T = value
}

/**
 * Singleton object
 */
object Logger {
    fun log(message: String) {
        println(message)
    }
}

/**
 * Extension function for String
 */
fun String.isEmail(): Boolean {
    return this.contains("@")
}

/**
 * Top-level function
 */
fun formatText(text: String): String {
    return text.uppercase()
}

/**
 * Suspend function (coroutine)
 */
suspend fun fetchData(): String {
    return "data"
}

/**
 * Function with default parameters
 */
fun greet(name: String, greeting: String = "Hello"): String {
    return "$greeting, $name!"
}

/**
 * Infix function
 */
infix fun Int.times(str: String): String = str.repeat(this)

/**
 * Property with getter and setter
 */
var counter: Int = 0
    get() = field
    set(value) {
        field = value.coerceAtLeast(0)
    }
