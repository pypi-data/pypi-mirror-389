# Sample Ruby file for testing symbol extraction

# Module definition
module Authentication
  # Constant
  TOKEN_EXPIRY = 3600

  # Module method
  def self.generate_token(user_id)
    "token_#{user_id}_#{Time.now.to_i}"
  end
end

# Class definition
class User
  # Class variable
  @@user_count = 0

  # attr_accessor creates getter/setter methods
  attr_accessor :name, :email
  attr_reader :id

  # Initialize method (constructor)
  def initialize(name, email)
    @name = name
    @email = email
    @id = @@user_count += 1
  end

  # Instance method
  def greet
    "Hello, I'm #{@name}"
  end

  # Class method
  def self.count
    @@user_count
  end

  # Private methods
  private

  def validate_email
    @email.include?('@')
  end
end

# Inheritance
class AdminUser < User
  def initialize(name, email, permissions)
    super(name, email)
    @permissions = permissions
  end

  def admin?
    true
  end
end

# Mixin module
module Timestampable
  def created_at
    @created_at ||= Time.now
  end

  def updated_at
    @updated_at ||= Time.now
  end
end

# Class with mixin
class Post
  include Timestampable

  attr_accessor :title, :content

  def initialize(title, content)
    @title = title
    @content = content
  end

  def summary
    @content[0..100]
  end
end

# Standalone function (method)
def calculate_total(items)
  items.sum(&:price)
end

# Method with block
def process_items(items, &block)
  items.each(&block)
end

# Lambda
sum_lambda = ->(a, b) { a + b }

# Proc
multiply_proc = Proc.new { |a, b| a * b }
