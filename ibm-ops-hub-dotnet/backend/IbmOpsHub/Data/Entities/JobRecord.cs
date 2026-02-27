using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace IbmOpsHub.Data.Entities;

[Table("job_records")]
public class JobRecord
{
    [Key]
    [Column("id")]
    public int Id { get; set; }

    [Column("external_id")]
    [MaxLength(512)]
    public string ExternalId { get; set; } = string.Empty;

    [Column("name")]
    [MaxLength(512)]
    public string Name { get; set; } = string.Empty;

    [Column("component")]
    [MaxLength(64)]
    public string Component { get; set; } = string.Empty;

    [Column("status")]
    [MaxLength(64)]
    public string Status { get; set; } = string.Empty;

    [Column("started_at")]
    public DateTime? StartedAt { get; set; }

    [Column("finished_at")]
    public DateTime? FinishedAt { get; set; }

    [Column("polled_at")]
    public DateTime PolledAt { get; set; } = DateTime.UtcNow;

    [Column("details", TypeName = "jsonb")]
    public string Details { get; set; } = "{}";
}
