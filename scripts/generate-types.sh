#!/bin/bash

# Script to generate TypeScript types from Supabase database
# This uses the PAT token stored in the .env file

# Load environment variables from .env file
if [ -f .env ]; then
  export $(cat .env | grep SUPABASE_PAT_TOKEN | xargs)
fi

# Check if PAT token is available
if [ -z "$SUPABASE_PAT_TOKEN" ]; then
  echo "Error: SUPABASE_PAT_TOKEN not found in .env file"
  exit 1
fi

# Set the access token for Supabase CLI
export SUPABASE_ACCESS_TOKEN=$SUPABASE_PAT_TOKEN

# Project details
PROJECT_ID="leozlogjxlzsnoijodez"
OUTPUT_FILE="../webapp-frontend/types/database.types.ts"

echo "Generating TypeScript types from Supabase..."
echo "Project ID: $PROJECT_ID"
echo "Output file: $OUTPUT_FILE"

# Generate types
npx supabase gen types typescript --project-id $PROJECT_ID --schema public > $OUTPUT_FILE

if [ $? -eq 0 ]; then
  echo "✅ Types generated successfully!"
  echo "Location: $OUTPUT_FILE"

  # Also copy to backend for reference if needed
  cp $OUTPUT_FILE ./types/database.types.ts 2>/dev/null || mkdir -p ./types && cp $OUTPUT_FILE ./types/database.types.ts
  echo "✅ Types also copied to backend/types directory"
else
  echo "❌ Failed to generate types"
  exit 1
fi
