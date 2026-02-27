using IbmOpsHub.Models;

namespace IbmOpsHub.Services.Interfaces;

public interface IJobService
{
    string Component { get; }
    Task<List<NormalizedJob>> PollAsync(CancellationToken ct = default);
    Task<List<NormalizedJob>> GetCachedAsync();
}
