param(
    [string]$Root = "data/raw",
    [string]$Out = $null,
    [switch]$NoFollow
)

Write-Host "Tailing JSONL files in $Root" -ForegroundColor Cyan

if ($Out) {
    py -3 -m src.consumer.file_tail --root $Root --out $Out $(if ($NoFollow) { "--no-follow" })
} else {
    py -3 -m src.consumer.file_tail --root $Root $(if ($NoFollow) { "--no-follow" })
}
