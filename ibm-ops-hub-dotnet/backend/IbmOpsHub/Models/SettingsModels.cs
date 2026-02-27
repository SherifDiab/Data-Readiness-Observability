namespace IbmOpsHub.Models;

public class SettingFieldDef
{
    public string Key { get; set; } = string.Empty;
    public string Label { get; set; } = string.Empty;
    public string Type { get; set; } = "text"; // text, url, password, boolean, number, tags
    public bool Required { get; set; }
    public bool Sensitive { get; set; }
    public string? Hint { get; set; }
    public int? Min { get; set; }
    public int? Max { get; set; }
}

public class SettingsResponse
{
    public Dictionary<string, List<SettingFieldDef>> Schema { get; set; } = [];
    public Dictionary<string, object?> Values { get; set; } = [];
    public List<string> Overrides { get; set; } = [];
}

public class SettingsUpdateRequest
{
    public Dictionary<string, object?> Changes { get; set; } = [];
}

public class SettingsUpdateResult
{
    public string Status { get; set; } = "ok";
    public List<string> Applied { get; set; } = [];
    public List<string> Skipped { get; set; } = [];
}
