#!/bin/bash

# Autospook Authentication Key Generator
# This script generates secure authentication keys for the OSINT system

set -e

KEYS_FILE="auth_keys.txt"
KEYS_DIR="."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to generate a secure key
generate_key() {
    # Generate a 32-character key using alphanumeric characters
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-32
}

# Function to print usage
usage() {
    echo -e "${BLUE}Autospook Key Generator${NC}"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -g, --generate [EMAIL]    Generate a new key (optionally for specific email)"
    echo "  -l, --list               List all active keys"
    echo "  -r, --revoke KEY         Revoke a specific key"
    echo "  -h, --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -g                                    # Generate anonymous key"
    echo "  $0 -g john.doe@company.com              # Generate key for specific email"
    echo "  $0 -l                                    # List all keys"
    echo "  $0 -r abc123def456ghi789jkl012mno345    # Revoke specific key"
    echo ""
}

# Function to generate and save a key
generate_and_save_key() {
    local email="$1"
    local key=$(generate_key)
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Create keys file if it doesn't exist
    touch "$KEYS_FILE"
    
    # Add key to file
    if [ -n "$email" ]; then
        echo "$key|$email|$timestamp|active" >> "$KEYS_FILE"
        echo -e "${GREEN}✓ Generated key for $email:${NC}"
    else
        echo "$key|anonymous|$timestamp|active" >> "$KEYS_FILE"
        echo -e "${GREEN}✓ Generated anonymous key:${NC}"
    fi
    
    echo -e "${YELLOW}$key${NC}"
    echo ""
    echo -e "${BLUE}Email template:${NC}"
    echo "----------------------------------------"
    echo "Subject: Autospook OSINT Access Key"
    echo ""
    echo "Hello,"
    echo ""
    echo "You have been granted access to the Autospook OSINT research system."
    echo ""
    echo "Your access key is: $key"
    echo ""
    echo "To use the system:"
    echo "1. Visit the Autospook application"
    echo "2. Enter your access key in the authentication field"
    echo "3. Begin your OSINT investigations"
    echo ""
    echo "Please keep this key secure and do not share it with others."
    echo ""
    echo "Best regards,"
    echo "Autospook Admin"
    echo "----------------------------------------"
}

# Function to list all keys
list_keys() {
    if [ ! -f "$KEYS_FILE" ]; then
        echo -e "${YELLOW}No keys file found. Use -g to generate the first key.${NC}"
        return
    fi
    
    echo -e "${BLUE}Active Authentication Keys:${NC}"
    echo "----------------------------------------"
    
    local count=0
    while IFS='|' read -r key email timestamp status; do
        if [ "$status" = "active" ]; then
            count=$((count + 1))
            echo -e "${GREEN}$count.${NC} Key: ${YELLOW}$key${NC}"
            echo "   Email: $email"
            echo "   Created: $timestamp"
            echo ""
        fi
    done < "$KEYS_FILE"
    
    if [ $count -eq 0 ]; then
        echo -e "${YELLOW}No active keys found.${NC}"
    else
        echo -e "${GREEN}Total active keys: $count${NC}"
    fi
}

# Function to revoke a key
revoke_key() {
    local target_key="$1"
    
    if [ ! -f "$KEYS_FILE" ]; then
        echo -e "${RED}✗ No keys file found.${NC}"
        return 1
    fi
    
    # Check if key exists and is active
    local key_found=false
    while IFS='|' read -r key email timestamp status; do
        if [ "$key" = "$target_key" ] && [ "$status" = "active" ]; then
            key_found=true
            break
        fi
    done < "$KEYS_FILE"
    
    if [ "$key_found" = false ]; then
        echo -e "${RED}✗ Key not found or already revoked.${NC}"
        return 1
    fi
    
    # Create backup
    cp "$KEYS_FILE" "${KEYS_FILE}.backup"
    
    # Revoke the key (mark as revoked instead of deleting)
    local temp_file=$(mktemp)
    while IFS='|' read -r key email timestamp status; do
        if [ "$key" = "$target_key" ]; then
            echo "$key|$email|$timestamp|revoked" >> "$temp_file"
        else
            echo "$key|$email|$timestamp|$status" >> "$temp_file"
        fi
    done < "$KEYS_FILE"
    
    mv "$temp_file" "$KEYS_FILE"
    echo -e "${GREEN}✓ Key revoked successfully.${NC}"
}

# Main script logic
case "${1:-}" in
    -g|--generate)
        generate_and_save_key "$2"
        ;;
    -l|--list)
        list_keys
        ;;
    -r|--revoke)
        if [ -z "$2" ]; then
            echo -e "${RED}✗ Please provide a key to revoke.${NC}"
            echo "Usage: $0 -r KEY"
            exit 1
        fi
        revoke_key "$2"
        ;;
    -h|--help|"")
        usage
        ;;
    *)
        echo -e "${RED}✗ Invalid option: $1${NC}"
        usage
        exit 1
        ;;
esac