using Microsoft.EntityFrameworkCore.Migrations;
using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;

#nullable disable

namespace IbmOpsHub.Data.Migrations;

public partial class InitialCreate : Migration
{
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.CreateTable(
            name: "job_records",
            columns: table => new
            {
                id         = table.Column<int>(nullable: false)
                                  .Annotation("Npgsql:ValueGenerationStrategy",
                                              NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                external_id = table.Column<string>(maxLength: 512, nullable: false),
                name        = table.Column<string>(maxLength: 512, nullable: false),
                component   = table.Column<string>(maxLength: 64,  nullable: false),
                status      = table.Column<string>(maxLength: 64,  nullable: false),
                started_at  = table.Column<DateTime>(nullable: true),
                finished_at = table.Column<DateTime>(nullable: true),
                polled_at   = table.Column<DateTime>(nullable: false),
                details     = table.Column<string>(type: "jsonb", nullable: false, defaultValue: "{}")
            },
            constraints: table => table.PrimaryKey("PK_job_records", x => x.id));

        migrationBuilder.CreateIndex(
            name: "IX_job_records_component_polled_at",
            table: "job_records",
            columns: ["component", "polled_at"]);

        migrationBuilder.CreateIndex(
            name: "IX_job_records_external_id",
            table: "job_records",
            column: "external_id");
    }

    protected override void Down(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.DropTable(name: "job_records");
    }
}
