# scripts/export_env.ps1
# Usage: . ./scripts/export_env.ps1

if (Test-Path ".env") {
    Get-Content .env | ForEach-Object {
        if ($_ -match "^(?<name>[^#\s=]+)\s*=\s*(?<value>.*)$") {
            $name = $Matches['name'].Trim()
            $value = $Matches['value'].Trim().Trim('"').Trim("'")
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
            Write-Host "Exported $name" -ForegroundColor Green
        }
    }
} else {
    Write-Host ".env file not found" -ForegroundColor Red
}
