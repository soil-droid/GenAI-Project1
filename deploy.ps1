# Deployment Script for Cloud Run

Write-Host "Deploying Rig Builder ADK Agent to Google Cloud Run..."
Write-Host "Please ensure you have gcloud installed and authenticated (gcloud auth login)."
Write-Host "You also need to provide your GEMINI_API_KEY."

$GeminiApiKey = Read-Host -Prompt "Enter your Gemini API Key"

if ([string]::IsNullOrWhiteSpace($GeminiApiKey)) {
    Write-Host "API Key is required to deploy. Exiting."
    exit
}

# Deploy to Cloud Run using source deployment
gcloud run deploy rig-builder-agent `
    --source . `
    --region us-central1 `
    --allow-unauthenticated `
    --set-env-vars="GEMINI_API_KEY=$GeminiApiKey"

Write-Host "Deployment completed!"
