using IbmOpsHub.Background;
using IbmOpsHub.Configuration;
using IbmOpsHub.Data;
using IbmOpsHub.Hubs;
using IbmOpsHub.Services;
using IbmOpsHub.Services.Interfaces;
using Microsoft.EntityFrameworkCore;
using Serilog;
using StackExchange.Redis;

var builder = WebApplication.CreateBuilder(args);

// ── Logging ────────────────────────────────────────────────────────────────
Log.Logger = new LoggerConfiguration()
    .ReadFrom.Configuration(builder.Configuration)
    .CreateLogger();
builder.Host.UseSerilog();

// ── Configuration ──────────────────────────────────────────────────────────
builder.Services.Configure<AppSettings>(
    builder.Configuration.GetSection("AppSettings"));

// ── Database ───────────────────────────────────────────────────────────────
builder.Services.AddDbContext<AppDbContext>(opts =>
    opts.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection")));

// ── Redis ──────────────────────────────────────────────────────────────────
var redisConn = builder.Configuration.GetConnectionString("Redis") ?? "localhost:6379";
builder.Services.AddSingleton<IConnectionMultiplexer>(_ => ConnectionMultiplexer.Connect(redisConn));
builder.Services.AddSingleton<ICacheService, CacheService>();

// ── HttpClient factory ─────────────────────────────────────────────────────
builder.Services.AddHttpClient("ibm", c =>
{
    c.Timeout = TimeSpan.FromSeconds(30);
    c.DefaultRequestHeaders.Add("Accept", "application/json");
});
builder.Services.AddHttpClient("auth", c =>
{
    c.Timeout = TimeSpan.FromSeconds(15);
});

// ── Application services ───────────────────────────────────────────────────
builder.Services.AddSingleton<AuthService>();
builder.Services.AddSingleton<SparkService>();
builder.Services.AddSingleton<DataStageService>();
builder.Services.AddSingleton<FlinkService>();
builder.Services.AddSingleton<EventProcessingService>();
builder.Services.AddSingleton<ApicService>();
builder.Services.AddSingleton<DashboardService>();
builder.Services.AddSingleton<SettingsStore>();

// ── Background polling workers ─────────────────────────────────────────────
builder.Services.AddHostedService<SparkPollingWorker>();
builder.Services.AddHostedService<DataStagePollingWorker>();
builder.Services.AddHostedService<FlinkPollingWorker>();
builder.Services.AddHostedService<EventProcessingPollingWorker>();
builder.Services.AddHostedService<ApicPollingWorker>();

// ── ASP.NET Core ───────────────────────────────────────────────────────────
builder.Services.AddControllers()
    .AddJsonOptions(o => o.JsonSerializerOptions.PropertyNamingPolicy = System.Text.Json.JsonNamingPolicy.SnakeCaseLower);

builder.Services.AddSignalR();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c => c.SwaggerDoc("v1", new() { Title = "IBM Ops Hub API", Version = "v1" }));

builder.Services.AddCors(o => o.AddPolicy("Angular", p =>
    p.WithOrigins(
        "http://localhost:4200",   // ng serve
        "http://localhost:80",     // IIS production
        "http://localhost"
    )
    .AllowAnyHeader()
    .AllowAnyMethod()
    .AllowCredentials()));         // required for SignalR

var app = builder.Build();

// ── Database migration on startup ──────────────────────────────────────────
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    await db.Database.MigrateAsync();
}

// ── Restore persisted settings overrides ──────────────────────────────────
var settingsStore = app.Services.GetRequiredService<SettingsStore>();
await settingsStore.LoadOverridesOnStartupAsync();

// ── Middleware pipeline ────────────────────────────────────────────────────
app.UseSwagger();
app.UseSwaggerUI(c => c.SwaggerEndpoint("/swagger/v1/swagger.json", "IBM Ops Hub v1"));

app.UseCors("Angular");
app.UseRouting();

app.MapControllers();
app.MapHub<OpsHub>("/hubs/ops");

// Health endpoint
app.MapGet("/health", () => Results.Ok(new { status = "healthy", timestamp = DateTime.UtcNow }));

Log.Information("IBM Ops Hub (.NET) starting on {Urls}", builder.Configuration["ASPNETCORE_URLS"] ?? "http://localhost:5000");
app.Run();
