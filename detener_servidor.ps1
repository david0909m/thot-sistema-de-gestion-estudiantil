Write-Host "=== DETENIENDO SERVIDOR THOT EN EL PUERTO 8000 ===" -ForegroundColor Yellow
$proc = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($proc) {
    Stop-Process -Id $proc.OwningProcess -Force
    Write-Host "[OK] Servidor detenido correctamente (PID $($proc.OwningProcess))." -ForegroundColor Green
} else {
    Write-Host "[INFO] No hay ningún servidor ejecutándose en el puerto 8000." -ForegroundColor Cyan
}
