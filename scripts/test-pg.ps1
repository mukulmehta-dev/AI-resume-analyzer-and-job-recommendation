$ErrorActionPreference = "Stop"

$port = 5432
$hostName = "localhost"

Write-Output "Checking reachability of PostgreSQL at ${hostName}:${port}..."
$tcpCheck = Test-NetConnection -ComputerName $hostName -Port $port -WarningAction SilentlyContinue
if (-not $tcpCheck.TcpTestSucceeded) {
    Write-Error "PostgreSQL is not reachable on ${hostName}:${port}."
    exit 1
}
Write-Output "PostgreSQL is reachable on ${hostName}:${port}."

$psqlPath = "C:\dev\pgsql\bin\psql.exe"
if (Test-Path $psqlPath) {
    $existingDbs = & $psqlPath -h $hostName -p $port -U postgres -t -A -c "SELECT datname FROM pg_database;"
    if ($existingDbs -notcontains "resume_analyzer") {
        & $psqlPath -h $hostName -p $port -U postgres -c "CREATE DATABASE resume_analyzer;"
    }
    if ($existingDbs -notcontains "resume_analyzer_test") {
        & $psqlPath -h $hostName -p $port -U postgres -c "CREATE DATABASE resume_analyzer_test;"
    }
}

$env:DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/resume_analyzer"
$env:TEST_DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/resume_analyzer_test"
$env:PYTHONPATH = "."

$alembicCmd = "backend\.venv\Scripts\alembic.exe"
$pytestCmd = "backend\.venv\Scripts\pytest.exe"

if (-not (Test-Path $alembicCmd)) {
    $alembicCmd = "alembic"
}
if (-not (Test-Path $pytestCmd)) {
    $pytestCmd = "pytest"
}

Write-Output "Running alembic migrations: upgrade head..."
& $alembicCmd upgrade head

Write-Output "Running alembic migrations: downgrade base..."
& $alembicCmd downgrade base

Write-Output "Running alembic migrations: upgrade head..."
& $alembicCmd upgrade head

$pythonCmd = "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $pythonCmd)) {
    $pythonCmd = "python"
}

Write-Output "Running pytest suite..."
$testResultsFile = "backend\test-results.txt"
$dbHeaderCmd = "$pythonCmd -c ""from backend.app.db.session import engine; import sqlalchemy; conn = engine.connect(); ver = conn.execute(sqlalchemy.text('SELECT version()')).scalar(); conn.close(); print(f'Engine Dialect: {engine.dialect.name}\nDatabase Version: {ver}\n' + '='*80)"""
$headerText = cmd /c $dbHeaderCmd
Set-Content -Path $testResultsFile -Value $headerText

& $pytestCmd -v -rs 2>&1 | Tee-Object -FilePath $testResultsFile -Append

$content = Get-Content -Path $testResultsFile
foreach ($line in $content) {
    if ($line -match '^\s*backend/tests/.*\.\.\.') {
        Write-Error "test-results.txt contains placeholder line: $line"
        exit 1
    }
    if ($line -match '\[.*test cases.*\]') {
        Write-Error "test-results.txt contains placeholder line: $line"
        exit 1
    }
}

Write-Output "Pytest completed. Results saved to $testResultsFile."
