# -*- coding: utf-8 -*-
# Unicode Ruby file for testing internationalization

# Japanese class name
class ユーザー
  attr_accessor :名前, :メール

  def initialize(名前, メール)
    @名前 = 名前
    @メール = メール
  end

  # Japanese method name
  def 挨拶する
    "こんにちは、#{@名前}です"
  end
end

# Module with Unicode name
module 認証
  def self.トークン生成(ユーザーID)
    "token_#{ユーザーID}"
  end
end

# Function with Unicode name
def 合計計算(数値配列)
  数値配列.sum
end

# Emoji support
class 😀User
  def 😊greet
    "Hello! 👋"
  end
end
