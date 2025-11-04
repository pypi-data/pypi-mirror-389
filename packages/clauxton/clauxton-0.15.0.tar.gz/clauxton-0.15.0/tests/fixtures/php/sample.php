<?php

namespace App\Models;

/**
 * User model class
 */
class User
{
    private $name;
    private $email;

    /**
     * Constructor
     */
    public function __construct(string $name, string $email)
    {
        $this->name = $name;
        $this->email = $email;
    }

    /**
     * Get user name
     */
    public function getName(): string
    {
        return $this->name;
    }

    /**
     * Set user name
     */
    public function setName(string $name): void
    {
        $this->name = $name;
    }

    /**
     * Static method example
     */
    public static function create(string $name, string $email): self
    {
        return new self($name, $email);
    }
}

/**
 * Loggable interface
 */
interface Loggable
{
    public function log(string $message): void;
}

/**
 * Timestampable trait
 */
trait Timestampable
{
    private $createdAt;
    private $updatedAt;

    public function touch(): void
    {
        $this->updatedAt = time();
    }
}

/**
 * Standalone function
 */
function calculateTotal(array $items): float
{
    return array_sum($items);
}

/**
 * Another function
 */
function formatCurrency(float $amount): string
{
    return '$' . number_format($amount, 2);
}
