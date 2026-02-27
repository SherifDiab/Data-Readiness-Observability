using IbmOpsHub.Data.Entities;
using Microsoft.EntityFrameworkCore;

namespace IbmOpsHub.Data;

public class AppDbContext(DbContextOptions<AppDbContext> options) : DbContext(options)
{
    public DbSet<JobRecord> JobRecords { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<JobRecord>(e =>
        {
            e.HasIndex(r => new { r.Component, r.PolledAt });
            e.HasIndex(r => r.ExternalId);
        });
    }
}
