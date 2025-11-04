import Foundation

/// ユーザークラス (User class in Japanese)
class ユーザー {
    var 名前: String

    init(名前: String) {
        self.名前 = 名前
    }

    func 挨拶() -> String {
        return "こんにちは、\(名前)さん！"
    }
}

/// 計算関数 (Calculation function)
func 計算(数値: Int) -> Int {
    return 数値 * 2
}
