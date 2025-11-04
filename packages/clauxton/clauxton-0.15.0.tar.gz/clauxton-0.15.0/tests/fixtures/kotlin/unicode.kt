package com.example.unicode

/**
 * ユーザークラス (User class in Japanese)
 */
data class ユーザー(
    val 名前: String,
    val メール: String
) {
    fun 挨拶(): String {
        return "こんにちは、${名前}さん！"
    }
}

/**
 * 計算関数 (Calculation function in Japanese)
 */
fun 計算(数値: Int): Int {
    return 数値 * 2
}

/**
 * Emoji class name
 */
class 😀Emoji {
    fun smile(): String = "😀"
}
