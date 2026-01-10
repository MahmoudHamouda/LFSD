# Deploy Admin & Frontend to Cloud Run

$PROJECT_ID = "lfsd-backend-692544481281" # Inferred from backend URL, likely project ID or requires checking
$REGION = "us-central1"
$FRONTEND_SERVICE = "lfsd-frontend"
$BACKEND_SERVICE = "lfsd-backend"

Write-Host "Starting Deployment Process..." -ForegroundColor Green

# 1. Check gcloud auth
$auth = gcloud auth list --filter=status:ACTIVE --format="value(account)"
if (-not $auth) {
    Write-Host "Error: Not authenticated with gcloud. Run 'gcloud auth login' first." -ForegroundColor Red
    exit 1
}
Write-Host "Authenticated as: $auth" -ForegroundColor Cyan

# 2. Get Project ID (if not hardcoded correctly above, this helps)
$current_project = gcloud config get-value project
Write-Host "Current Project: $current_project" -ForegroundColor Cyan

# 3. Deploy Frontend (Admin Panel is part of this)
Write-Host "Building and Deploying Frontend..." -ForegroundColor Yellow
# Note: Using Cloud Build to avoid local Docker issues
gcloud builds submit --tag "gcr.io/$current_project/lfsd-frontend" frontend/

if ($LASTEXITCODE -eq 0) {
    gcloud run deploy $FRONTEND_SERVICE `
        --image "gcr.io/$current_project/lfsd-frontend" `
        --platform managed `
        --region $REGION `
        --allow-unauthenticated `
        --port 8080
} else {
    Write-Host "Frontend Build Failed!" -ForegroundColor Red
    exit 1
}

# 4. Deploy Backend (Update with new Security & Admin Routes)
Write-Host "Building and Deploying Backend..." -ForegroundColor Yellow
gcloud builds submit --tag "gcr.io/$current_project/lfsd-backend" .

if ($LASTEXITCODE -eq 0) {
    gcloud run deploy $BACKEND_SERVICE `
        --image "gcr.io/$current_project/lfsd-backend" `
        --platform managed `
        --region $REGION `
        --allow-unauthenticated
        # Note: 'allow-unauthenticated' is needed for public API, but internal routes are secured via Application Auth (JWT + Role)
} else {
    Write-Host "Backend Build Failed!" -ForegroundColor Red
    exit 1
}

Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "Admin Panel accessible at: https://<frontend-url>/admin"
