namespace IbmOpsHub.Services.Interfaces;

public interface ICacheService
{
    Task<T?> GetAsync<T>(string key);
    Task SetAsync<T>(string key, T value, TimeSpan? expiry = null);
    Task<string?> GetStringAsync(string key);
    Task SetStringAsync(string key, string value, TimeSpan? expiry = null);
    Task DeleteAsync(string key);
    Task<Dictionary<string, string>> GetHashAsync(string key);
    Task SetHashAsync(string key, Dictionary<string, string> fields);
}
