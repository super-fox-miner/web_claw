Write-Host "=============================================================" -ForegroundColor Green
Write-Host "Project Startup Script" -ForegroundColor Green
Write-Host "=============================================================" -ForegroundColor Green

# Function: Find suitable Python executable in the system (prefer 3.11+, accept 3.8+)
function Find-SuitablePython {
    # Try using py launcher (most reliable, lists all registered versions)
    try {
        $pyOutput = py --list 2>$null
        if ($LASTEXITCODE -eq 0) {
            $availableVersions = @()
            foreach ($line in $pyOutput) {
                if ($line -match '-V:(\d+\.\d+)') {
                    $ver = [version]$matches[1]
                    if ($ver.Major -eq 3 -and $ver.Minor -ge 8) {
                        $availableVersions += $ver
                    }
                }
            }
            
            # Sort versions and pick the highest compatible version
            if ($availableVersions.Count -gt 0) {
                $sortedVersions = $availableVersions | Sort-Object -Descending
                $bestVersion = $sortedVersions[0]
                Write-Host "Found Python $bestVersion (via py launcher)" -ForegroundColor Green
                # Return command array: @('py', '-3.x')
                return ,@('py', "-V:$bestVersion")
            }
        }
    } catch {
        Write-Host "py launcher unavailable or parsing failed: $_" -ForegroundColor Yellow
    }

    # Try to find Python executables from PATH (3.8+)
    try {
        $pythonPaths = Get-Command python* -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandType -eq 'Application' -and $_.Name -match '^python(\d+(\.\d+)?)?\.exe$' } |
            Select-Object -ExpandProperty Source
        
        $availableVersions = @()
        foreach ($path in $pythonPaths) {
            $verOutput = & $path --version 2>&1
            if ($verOutput -match 'Python (\d+\.\d+\.\d+)') {
                $ver = [version]$matches[1]
                if ($ver.Major -eq 3 -and $ver.Minor -ge 8) {
                    $availableVersions += @{Version = $ver; Path = $path}
                }
            }
        }
        
        # Sort versions and pick the highest compatible version
        if ($availableVersions.Count -gt 0) {
            $sortedVersions = $availableVersions | Sort-Object { $_.Version } -Descending
            $bestVersion = $sortedVersions[0].Version
            $bestPath = $sortedVersions[0].Path
            Write-Host "Found Python $bestVersion at $bestPath" -ForegroundColor Green
            return $bestPath
        }
    } catch {
        Write-Host "Error searching Python in PATH: $_" -ForegroundColor Yellow
    }

    # Try searching common Python installation directories (3.8+)
    $searchPaths = @(
        "C:\Python311", "C:\Python310", "C:\Python39", "C:\Python38",
        "C:\Python313", "C:\Python312",
        "C:\Program Files\Python311", "C:\Program Files\Python310", 
        "C:\Program Files\Python39", "C:\Program Files\Python38",
        "C:\Program Files\Python313", "C:\Program Files\Python312",
        "C:\Program Files (x86)\Python311", "C:\Program Files (x86)\Python310",
        "C:\Program Files (x86)\Python39", "C:\Program Files (x86)\Python38",
        "C:\Program Files (x86)\Python313", "C:\Program Files (x86)\Python312",
        "$env:LOCALAPPDATA\Programs\Python\Python311",
        "$env:LOCALAPPDATA\Programs\Python\Python310",
        "$env:LOCALAPPDATA\Programs\Python\Python39",
        "$env:LOCALAPPDATA\Programs\Python\Python38",
        "$env:LOCALAPPDATA\Programs\Python\Python313",
        "$env:LOCALAPPDATA\Programs\Python\Python312",
        "$env:APPDATA\Local\Programs\Python\Python311",
        "$env:APPDATA\Local\Programs\Python\Python310",
        "$env:APPDATA\Local\Programs\Python\Python39",
        "$env:APPDATA\Local\Programs\Python\Python38",
        "$env:APPDATA\Local\Programs\Python\Python313",
        "$env:APPDATA\Local\Programs\Python\Python312"
    )
    
    $availableVersions = @()
    foreach ($path in $searchPaths) {
        if (Test-Path $path) {
            $pythonExe = Join-Path $path "python.exe"
            if (Test-Path $pythonExe) {
                $verOutput = & $pythonExe --version 2>&1
                if ($verOutput -match 'Python (\d+\.\d+\.\d+)') {
                    $ver = [version]$matches[1]
                    if ($ver.Major -eq 3 -and $ver.Minor -ge 8) {
                        $availableVersions += @{Version = $ver; Path = $pythonExe}
                    }
                }
            }
        }
    }
    
    # Sort versions and pick the highest compatible version
    if ($availableVersions.Count -gt 0) {
        $sortedVersions = $availableVersions | Sort-Object { $_.Version } -Descending
        $bestVersion = $sortedVersions[0].Version
        $bestPath = $sortedVersions[0].Path
        Write-Host "Found Python $bestVersion at $bestPath" -ForegroundColor Green
        return $bestPath
    }

    # No suitable Python found
    return $null
}

# Find suitable Python
$pythonCmd = Find-SuitablePython

if (-not $pythonCmd) {
    Write-Host "No suitable Python found, installing latest Python 3.11+ version..." -ForegroundColor Yellow
    
    # Get latest Python 3.11+ version from Python official website
    try {
        Write-Host "Getting latest Python version information..." -ForegroundColor Cyan
        $releasesPage = Invoke-WebRequest -Uri "https://www.python.org/downloads/windows/" -UseBasicParsing
        
        # Extract latest stable version (3.11+)
        if ($releasesPage.Content -match 'Latest Python 3 Release: Python (\d+\.\d+\.\d+)') {
            $latestVersion = $matches[1]
            Write-Host "Latest Python version found: $latestVersion" -ForegroundColor Green
        } else {
            # Fallback to a known stable version
            $latestVersion = "3.11.10"
            Write-Host "Using fallback version: $latestVersion" -ForegroundColor Yellow
        }
        
        $installer = "python-$latestVersion-amd64.exe"
        Write-Host "Downloading Python $latestVersion installer..." -ForegroundColor Cyan
        
        # Try multiple download mirrors
        $downloadUrls = @(
            "https://www.python.org/ftp/python/$latestVersion/$installer",
            "https://npm.taobao.org/mirrors/python/$latestVersion/$installer"
        )
        
        $downloadSuccess = $false
        foreach ($url in $downloadUrls) {
            try {
                Write-Host "Trying download from: $url" -ForegroundColor Cyan
                Invoke-WebRequest -Uri $url -OutFile $installer -TimeoutSec 60
                $downloadSuccess = $true
                Write-Host "Download successful" -ForegroundColor Green
                break
            } catch {
                Write-Host "Download failed: $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
        
        if (-not $downloadSuccess) {
            throw "All download attempts failed"
        }
        
        Write-Host "Installing Python $latestVersion..." -ForegroundColor Cyan
        
        # Check if we have admin privileges for system-wide installation
        $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
        
        if ($isAdmin) {
            Write-Host "Installing for all users (admin privileges detected)..." -ForegroundColor Cyan
            Start-Process -FilePath ".\$installer" -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
        } else {
            Write-Host "Installing for current user only..." -ForegroundColor Cyan
            Start-Process -FilePath ".\$installer" -ArgumentList "/quiet PrependPath=1" -Wait
        }
        
        Remove-Item $installer -Force -ErrorAction SilentlyContinue

        # Get newly installed Python path
        $majorMinor = $latestVersion.Substring(0, $latestVersion.LastIndexOf('.'))
        $regPath = Get-ItemProperty -Path "HKLM:\SOFTWARE\Python\PythonCore\$majorMinor\InstallPath" -ErrorAction SilentlyContinue
        if (-not $regPath) {
            $regPath = Get-ItemProperty -Path "HKCU:\SOFTWARE\Python\PythonCore\$majorMinor\InstallPath" -ErrorAction SilentlyContinue
        }
        
        if ($regPath -and $regPath.ExecutablePath) {
            $pythonCmd = $regPath.ExecutablePath
        } else {
            # Fallback to default installation paths
            if ($isAdmin) {
                $pythonCmd = "C:\Program Files\Python$majorMinor\python.exe"
            } else {
                $pythonCmd = "$env:LOCALAPPDATA\Programs\Python\Python$majorMinor\python.exe"
            }
        }
        
        Write-Host "Python $latestVersion installed: $pythonCmd" -ForegroundColor Green
        
        # Wait a moment for system PATH to update
        Start-Sleep -Seconds 2
        
    } catch {
        Write-Host "Failed to install Python: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Please install Python 3.8 or later manually from https://www.python.org/downloads/" -ForegroundColor Yellow
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
    # Get all dependencies from requirements.txt
    $deps = Get-Content "requirements.txt" | Where-Object { $_ -notmatch '^#' -and $_ -notmatch '^$' }
    
    if ($deps.Count -gt 0) {
        # Get all installed packages at once (much faster than checking individually)
        $installedPackages = & $venvPython -m pip list --format=freeze 2>$null
        $installedPackagesHash = @{}
        foreach ($pkg in $installedPackages) {
            if ($pkg -match '^([^=]+)=') {
                $installedPackagesHash[$matches[1].ToLower()] = $true
            }
        }
        
        # Check if all dependencies are installed
        $allInstalled = $true
        foreach ($dep in $deps) {
            $depName = $dep.Split('=')[0].Split('>')[0].Split('<')[0].Trim().ToLower()
            if (-not $installedPackagesHash.ContainsKey($depName)) {
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
    } else {
        Write-Host "No dependencies found in requirements.txt" -ForegroundColor Green
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

# Check and download model
Write-Host "Checking model files..." -ForegroundColor Cyan
try {
    $modelName = "paraphrase-multilingual-MiniLM-L12-v2"
    $modelPath = Join-Path "models" $modelName
    
    if (-not (Test-Path $modelPath)) {
        Write-Host "Model $modelName not found, downloading..." -ForegroundColor Cyan
        
        # Create models directory if it doesn't exist
        if (-not (Test-Path "models")) {
            New-Item -ItemType Directory -Path "models" -Force | Out-Null
            Write-Host "Created models directory" -ForegroundColor Green
        }
        
        # Install modelscope
        Write-Host "Installing modelscope..." -ForegroundColor Cyan
        $hostName = ([System.Uri]"https://pypi.tuna.tsinghua.edu.cn/simple").Host
        & $venvPython -m pip install modelscope -i "https://pypi.tuna.tsinghua.edu.cn/simple" --trusted-host $hostName
        
        # Download model
        Write-Host "Downloading model $modelName..." -ForegroundColor Cyan
        & $venvPython -c "from modelscope import snapshot_download; snapshot_download('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', cache_dir='models')"
        
        # Rename the downloaded directory to match expected name
        $downloadedDir = Get-ChildItem -Path "models" -Directory | Where-Object { $_.Name -match 'paraphrase-multilingual-MiniLM-L12-v2' }
        if ($downloadedDir) {
            $downloadedPath = $downloadedDir.FullName
            if ($downloadedPath -ne $modelPath) {
                Move-Item -Path $downloadedPath -Destination $modelPath -Force
                Write-Host "Renamed downloaded model directory to $modelName" -ForegroundColor Green
            }
        }
        
        Write-Host "Model $modelName downloaded successfully" -ForegroundColor Green
    } else {
        Write-Host "Model $modelName already exists" -ForegroundColor Green
    }
} catch {
    Write-Host "Error checking or downloading model: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "Continuing with application startup..." -ForegroundColor Cyan
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