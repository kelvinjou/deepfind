#!/bin/bash
supabase start &
./backend/run_backend.sh &
./frontend/run_frontend.sh