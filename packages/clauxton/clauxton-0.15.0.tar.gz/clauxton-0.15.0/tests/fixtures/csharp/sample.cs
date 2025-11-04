using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace MyApp
{
    /// <summary>
    /// User class representing a user entity
    /// </summary>
    public class User
    {
        private string name;
        private int age;

        public string Name { get; set; }
        public int Age { get; private set; }

        public User(string name, int age)
        {
            this.name = name;
            this.age = age;
        }

        public void UpdateName(string newName)
        {
            this.name = newName;
        }

        public async Task<string> FetchDataAsync()
        {
            return await Task.FromResult("data");
        }
    }

    public interface IRunnable
    {
        void Run();
        Task RunAsync();
    }

    public enum Status
    {
        Ok,
        Error,
        Pending
    }

    public delegate void EventHandler(object sender, EventArgs e);

    public class Container<T>
    {
        private T item;

        public Container(T item)
        {
            this.item = item;
        }

        public T GetItem()
        {
            return item;
        }
    }
}

namespace MyApp.Utils
{
    public static class Helper
    {
        public static int Add(int a, int b)
        {
            return a + b;
        }
    }
}
