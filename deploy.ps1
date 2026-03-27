# Deployment Script for Cloud Run

Write-Host "Deploying Rig Builder ADK Agent to Google Cloud Run..."
Write-Host "Please ensure you have gcloud installed and authenticated (gcloud auth login)."
Write-Host "You also need to provide your GEMINI_API_KEY."

# API Key is hardcoded below

# Deploy to Cloud Run using source deployment
gcloud run deploy rig-builder-agent `
    --source . `
    --region us-central1 `
    --allow-unauthenticated `
    --set-env-vars="GEMINI_API_KEY=AIzaSyC7tgE2Skf45SuerjDy02su1CEALL9y07g"

Write-Host "Deployment completed!"
