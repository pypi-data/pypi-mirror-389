// Sample Java file for testing symbol extraction

package com.example;

import java.util.List;
import java.util.ArrayList;

/**
 * User class representing a user entity.
 */
public class User {
    private String name;
    private int age;

    /**
     * Constructor for User.
     * @param name The user's name
     * @param age The user's age
     */
    public User(String name, int age) {
        this.name = name;
        this.age = age;
    }

    /**
     * Get the user's name.
     * @return The name
     */
    public String getName() {
        return name;
    }

    /**
     * Set the user's name.
     * @param name The new name
     */
    public void setName(String name) {
        this.name = name;
    }

    public int getAge() {
        return age;
    }
}

/**
 * UserRepository interface for data access.
 */
public interface UserRepository {
    User findById(int id);
    List<User> findAll();
    void save(User user);
}

/**
 * Status enum for user status.
 */
public enum Status {
    ACTIVE,
    INACTIVE,
    SUSPENDED
}

/**
 * Generic container class.
 */
public class Container<T> {
    private T item;

    public Container(T item) {
        this.item = item;
    }

    public T getItem() {
        return item;
    }
}
