using System.Text.Json;
using IbmOpsHub.Services.Interfaces;
using StackExchange.Redis;

namespace IbmOpsHub.Services;

public class CacheService(IConnectionMultiplexer redis) : ICacheService
{
    private readonly IDatabase _db = redis.GetDatabase();

    public async Task<T?> GetAsync<T>(string key)
    {
        var value = await _db.StringGetAsync(key);
        return value.IsNullOrEmpty ? default : JsonSerializer.Deserialize<T>(value!);
    }

    public async Task SetAsync<T>(string key, T value, TimeSpan? expiry = null)
    {
        var json = JsonSerializer.Serialize(value);
        await _db.StringSetAsync(key, json, expiry);
    }

    public async Task<string?> GetStringAsync(string key)
    {
        var v = await _db.StringGetAsync(key);
        return v.IsNullOrEmpty ? null : v.ToString();
    }

    public async Task SetStringAsync(string key, string value, TimeSpan? expiry = null)
        => await _db.StringSetAsync(key, value, expiry);

    public async Task DeleteAsync(string key)
        => await _db.KeyDeleteAsync(key);

    public async Task<Dictionary<string, string>> GetHashAsync(string key)
    {
        var entries = await _db.HashGetAllAsync(key);
        return entries.ToDictionary(e => e.Name.ToString(), e => e.Value.ToString());
    }

    public async Task SetHashAsync(string key, Dictionary<string, string> fields)
    {
        var entries = fields.Select(kv => new HashEntry(kv.Key, kv.Value)).ToArray();
        await _db.HashSetAsync(key, entries);
    }
}
