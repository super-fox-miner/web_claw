Write-Host "=============================================================" -ForegroundColor Green
Write-Host "Project Startup Script" -ForegroundColor Green
Write-Host "=============================================================" -ForegroundColor Green

# Function: Find suitable Python executable in the system
function Find-SuitablePython {
    # Try using py launcher (most reliable, lists all registered versions)
    try {
        $pyOutput = py --list 2>$null
        if ($LASTEXITCODE -eq 0) {
            $versions = @()
            foreach ($line in $pyOutput) {
                if ($line -match '-V:(\d+\.\d+)') {
                    $ver = [version]$matches[1]
                    if ($ver -ge [version]"3.11") {
                        $versions += $ver
                    }
                }
            }
            if ($versions.Count -gt 0) {
                $best = ($versions | Sort-Object -Descending | Select-Object -First 1).ToString()
                Write-Host "Found suitable Python $best (via py launcher)" -ForegroundColor Green
                # Return command array: @('py', '-3.11')
                return ,@('py', "-$best")
            }
        }
    } catch {
        Write-Host "py launcher unavailable or parsing failed: $_" -ForegroundColor Yellow
    }

    # Try to find all python executables from PATH
    try {
        $pythonPaths = Get-Command python* -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandType -eq 'Application' -and $_.Name -match '^python(\d+(\.\d+)?)?\.exe$' } |
            Select-Object -ExpandProperty Source
        foreach ($path in $pythonPaths) {
            $verOutput = & $path --version 2>&1
            if ($verOutput -match 'Python (\d+\.\d+\.\d+)') {
                $ver = [version]$matches[1]
                if ($ver -ge [version]"3.11.0") {
                    Write-Host "Found suitable Python $ver at $path" -ForegroundColor Green
                    return $path
                }
            }
        }
    } catch {
        Write-Host "Error searching Python in PATH: $_" -ForegroundColor Yellow
    }

    # Try searching common Python installation directories
    $searchPaths = @(
        "C:\Python3*",
        "C:\Program Files\Python3*",
        "C:\Program Files (x86)\Python3*",
        "$env:LOCALAPPDATA\Programs\Python\Python3*",
        "$env:APPDATA\Local\Programs\Python\Python3*"
    )
    foreach ($pattern in $searchPaths) {
        $directories = Get-ChildItem -Path $pattern -Directory -ErrorAction SilentlyContinue
        foreach ($dir in $directories) {
            $pythonExe = Join-Path $dir.FullName "python.exe"
            if (Test-Path $pythonExe) {
                $verOutput = & $pythonExe --version 2>&1
                if ($verOutput -match 'Python (\d+\.\d+\.\d+)') {
                    $ver = [version]$matches[1]
                    if ($ver -ge [version]"3.11.0") {
                        Write-Host "Found suitable Python $ver at $pythonExe" -ForegroundColor Green
                        return $pythonExe
                    }
                }
            }
        }
    }

    # No suitable Python found
    return $null
}

# Find suitable Python
$pythonCmd = Find-SuitablePython

if (-not $pythonCmd) {
    Write-Host "Python 3.11 or higher not found, installing Python 3.13.12..." -ForegroundColor Yellow
    try {
        $installer = "python-3.13.12-amd64.exe"
        Write-Host "Downloading installer..." -ForegroundColor Cyan
        Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.13.12/$installer" -OutFile $installer
        Write-Host "Installing Python 3.13.12 (silent install for all users)..." -ForegroundColor Cyan
        Start-Process -FilePath ".\$installer" -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
        Remove-Item $installer -Force -ErrorAction SilentlyContinue

        # Get newly installed Python path (via registry or default location)
        $regPath = Get-ItemProperty -Path "HKLM:\SOFTWARE\Python\PythonCore\3.13\InstallPath" -ErrorAction SilentlyContinue
        if (-not $regPath) {
            $regPath = Get-ItemProperty -Path "HKCU:\SOFTWARE\Python\PythonCore\3.13\InstallPath" -ErrorAction SilentlyContinue
        }
        if ($regPath -and $regPath.ExecutablePath) {
            $pythonCmd = $regPath.ExecutablePath
        } else {
            # Fallback to default installation path
            $pythonCmd = "C:\Program Files\Python313\python.exe"
        }
        Write-Host "Python 3.13.12 installed: $pythonCmd" -ForegroundColor Green
    } catch {
        Write-Host "Failed to install Python: $($_.Exception.Message)" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "Using Python: $pythonCmd" -ForegroundColor Green
}

# Check virtual environment
Write-Host "Checking virtual environment..." -ForegroundColor Cyan
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    try {
        if ($pythonCmd -is [array]) {
            # $pythonCmd is in @('py', '-3.11') format
            & $pythonCmd[0] $pythonCmd[1] -m venv venv
        } else {
            & $pythonCmd -m venv venv
        }
        Write-Host "Virtual environment created successfully" -ForegroundColor Green
    } catch {
        Write-Host "Failed to create virtual environment: $($_.Exception.Message)" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "Virtual environment already exists" -ForegroundColor Green
}

# Set Python path in virtual environment
$venvPython = "venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Virtual environment Python not found, recreating..." -ForegroundColor Yellow
    Remove-Item "venv" -Recurse -Force -ErrorAction SilentlyContinue
    if ($pythonCmd -is [array]) {
        & $pythonCmd[0] $pythonCmd[1] -m venv venv
    } else {
        & $pythonCmd -m venv venv
    }
}

# Upgrade pip (try multiple mirrors)
Write-Host "Upgrading pip..." -ForegroundColor Cyan
$pipMirrors = @(
    "https://mirrors.aliyun.com/pypi/simple",
    "https://pypi.tuna.tsinghua.edu.cn/simple",
    "https://pypi.mirrors.ustc.edu.cn/simple",
    "https://pypi.doubanio.com/simple",
    "https://pypi.org/simple"
)
$pipUpgraded = $false
foreach ($mirror in $pipMirrors) {
    try {
        Write-Host "Trying mirror: $mirror" -ForegroundColor Cyan
        $hostName = ([System.Uri]$mirror).Host
        & $venvPython -m pip install --upgrade pip -i $mirror --trusted-host $hostName
        $pipUpgraded = $true
        Write-Host "pip upgraded successfully" -ForegroundColor Green
        break
    } catch {
        Write-Host "Mirror $mirror failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}
if (-not $pipUpgraded) {
    Write-Host "Failed to upgrade pip, will continue with existing version" -ForegroundColor Yellow
}

# Check and install dependencies
Write-Host "Checking dependencies..." -ForegroundColor Cyan
try {
    $deps = Get-Content "requirements.txt" | Where-Object { $_ -notmatch '^#' -and $_ -notmatch '^$' }
    $allInstalled = $true
    foreach ($dep in $deps) {
        $depName = $dep.Split('=')[0].Split('>')[0].Split('<')[0].Trim()
        $result = & $venvPython -m pip show $depName 2>&1
        if ($LASTEXITCODE -ne 0) {
            $allInstalled = $false
            break
        }
    }
    if (-not $allInstalled) {
        Write-Host "Installing dependencies..." -ForegroundColor Cyan
        $depMirrors = @(
            "https://pypi.tuna.tsinghua.edu.cn/simple",
            "https://mirrors.aliyun.com/pypi/simple",
            "https://pypi.mirrors.ustc.edu.cn/simple",
            "https://pypi.doubanio.com/simple",
            "https://pypi.org/simple"
        )
        $depsInstalled = $false
        foreach ($mirror in $depMirrors) {
            try {
                Write-Host "Trying mirror: $mirror" -ForegroundColor Cyan
                $hostName = ([System.Uri]$mirror).Host
                & $venvPython -m pip install -r requirements.txt -i $mirror --trusted-host $hostName
                $depsInstalled = $true
                Write-Host "Dependencies installed successfully" -ForegroundColor Green
                break
            } catch {
                Write-Host "Mirror $mirror failed: $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
        if (-not $depsInstalled) {
            Write-Host "Failed to install dependencies, please check network or install manually" -ForegroundColor Red
        }
    } else {
        Write-Host "All dependencies are already installed" -ForegroundColor Green
    }
} catch {
    Write-Host "Error checking dependencies: $($_.Exception.Message)" -ForegroundColor Yellow
    # Try to install dependencies directly on error
    Write-Host "Trying to install dependencies directly..." -ForegroundColor Cyan
    $depMirrors = @(
        "https://pypi.tuna.tsinghua.edu.cn/simple",
        "https://mirrors.aliyun.com/pypi/simple",
        "https://pypi.mirrors.ustc.edu.cn/simple",
        "https://pypi.doubanio.com/simple",
        "https://pypi.org/simple"
    )
    $depsInstalled = $false
    foreach ($mirror in $depMirrors) {
        try {
            $hostName = ([System.Uri]$mirror).Host
            & $venvPython -m pip install -r requirements.txt -i $mirror --trusted-host $hostName
            $depsInstalled = $true
            Write-Host "Dependencies installed successfully" -ForegroundColor Green
            break
        } catch {
            Write-Host "Mirror $mirror failed: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
    if (-not $depsInstalled) {
        Write-Host "Failed to install dependencies, please check network or install manually" -ForegroundColor Red
    }
}

# Start application
Write-Host "Starting application..." -ForegroundColor Cyan
try {
    & $venvPython main.py
} catch {
    Write-Host "Failed to start application: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Application started" -ForegroundColor Green
Read-Host "Press Enter to exit"